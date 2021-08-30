import pulumi_azure_native as azure_native

from ingenii_azure_data_platform.utils import generate_resource_name
from ingenii_azure_data_platform.defaults import STORAGE_ACCOUNT_DEFAULT_FIREWALL
from ingenii_azure_data_platform.iam import GroupRoleAssignment

from config import platform_config
from management import resource_groups
from management.user_groups import user_groups
from network import vnet, dns

# ----------------------------------------------------------------------------------------------------------------------
# FIREWALL IP ACCESS LIST
# This is the global firewall access list and applies to all resources such as key vaults, storage accounts etc.
# ----------------------------------------------------------------------------------------------------------------------
firewall = platform_config.yml_config["network"]["firewall"]
firewall_ip_access_list = []
if firewall.get("ip_access_list") is not None:
    for ip_address in firewall.get("ip_access_list"):
        azure_native.storage.IPRuleArgs(i_p_address_or_range=ip_address)

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE
# ----------------------------------------------------------------------------------------------------------------------
datalake_config = platform_config.yml_config["storage"]["datalake"]
datalake_name = generate_resource_name(
    resource_type="storage_account",
    resource_name="datalake",
    platform_config=platform_config,
)

datalake = azure_native.storage.StorageAccount(
    resource_name=datalake_name,
    account_name=datalake_name,
    allow_blob_public_access=False,
    network_rule_set=(
        azure_native.storage.NetworkRuleSetArgs(
            bypass="AzureServices",
            default_action="Deny",
            ip_rules=(
                firewall_ip_access_list if len(firewall_ip_access_list) > 0 else None
            ),
            virtual_network_rules=[
                azure_native.keyvault.VirtualNetworkRuleArgs(
                    id=vnet.dbw_engineering_hosts_subnet.id,
                ),
                azure_native.keyvault.VirtualNetworkRuleArgs(
                    id=vnet.dbw_engineering_containers_subnet.id,
                ),
                azure_native.keyvault.VirtualNetworkRuleArgs(
                    id=vnet.dbw_analytics_hosts_subnet.id,
                ),
                azure_native.keyvault.VirtualNetworkRuleArgs(
                    id=vnet.dbw_analytics_containers_subnet.id,
                ),
            ],
        )
        if datalake_config["network"]["firewall"]["enabled"] == True
        else STORAGE_ACCOUNT_DEFAULT_FIREWALL
    ),
    is_hns_enabled=True,
    kind="StorageV2",
    location=platform_config.region.long_name,
    minimum_tls_version="TLS1_2",
    resource_group_name=resource_groups.data.name,
    sku=azure_native.storage.SkuArgs(
        name="Standard_GRS",
    ),
    tags=platform_config.tags,
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> PRIVATE ENDPOINTS
# ----------------------------------------------------------------------------------------------------------------------

# BLOB PRIVATE ENDPOINT
blob_private_endpoint_name = generate_resource_name(
    resource_type="private_endpoint",
    resource_name="for-datalake-blob",
    platform_config=platform_config,
)
blob_private_endpoint = azure_native.network.PrivateEndpoint(
    resource_name=blob_private_endpoint_name,
    location=platform_config.region.long_name,
    private_endpoint_name=blob_private_endpoint_name,
    private_link_service_connections=[
        azure_native.network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["blob"],
            private_link_service_id=datalake.id,
            request_message="none",
        )
    ],
    custom_dns_configs=[],
    resource_group_name=resource_groups.infra.name,
    subnet=azure_native.network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

# BLOB PRIVATE DNS ZONE GROUP
blob_private_endpoint_dns_zone_group = azure_native.network.PrivateDnsZoneGroup(
    resource_name=f"{blob_private_endpoint_name}-dns-zone-group",
    private_dns_zone_configs=[
        azure_native.network.PrivateDnsZoneConfigArgs(
            name=blob_private_endpoint_name,
            private_dns_zone_id=dns.storage_blob_private_dns_zone.id,
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=blob_private_endpoint.name,
    resource_group_name=resource_groups.infra.name,
)

# DFS PRIVATE ENDPOINT
dfs_private_endpoint_name = generate_resource_name(
    resource_type="private_endpoint",
    resource_name="for-datalake-dfs",
    platform_config=platform_config,
)

dfs_private_endpoint = azure_native.network.PrivateEndpoint(
    resource_name=dfs_private_endpoint_name,
    location=platform_config.region.long_name,
    private_endpoint_name=dfs_private_endpoint_name,
    private_link_service_connections=[
        azure_native.network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["dfs"],
            private_link_service_id=datalake.id,
            request_message="none",
        )
    ],
    resource_group_name=resource_groups.infra.name,
    custom_dns_configs=[],
    subnet=azure_native.network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

# DFS PRIVATE DNS ZONE GROUP
dfs_private_endpoint_dns_zone_group = azure_native.network.PrivateDnsZoneGroup(
    resource_name=f"{dfs_private_endpoint_name}-dns-zone-group",
    private_dns_zone_configs=[
        azure_native.network.PrivateDnsZoneConfigArgs(
            name=dfs_private_endpoint_name,
            private_dns_zone_id=dns.storage_dfs_private_dns_zone.id,
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=dfs_private_endpoint.name,
    resource_group_name=resource_groups.infra.name,
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> IAM -> ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------
try:
    iam_role_assignments = datalake_config["iam"]["role_assignments"]
except:
    iam_role_assignments = {}

# TODO: Create a function that takes care of the role assignments. Replace all role assignments using the function.
# Create role assignments defined in the YAML files
for assignment in iam_role_assignments:
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=datalake.id,
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> CONTAINERS
# ----------------------------------------------------------------------------------------------------------------------

# If no containers are defined in the YAML files, we'll not attempt to create any.
try:
    datalake_container_definitions = datalake_config["containers"]
except:
    datalake_container_definitions = {}

# This dict will keep all container resources.
datalake_containers = {}

for ref_key, container_config in datalake_container_definitions.items():
    datalake_container_name = generate_resource_name(
        resource_type="storage_blob_container",
        resource_name=ref_key,
        platform_config=platform_config,
    )
    datalake_containers[ref_key] = azure_native.storage.BlobContainer(
        resource_name=datalake_container_name,
        account_name=datalake.name,
        container_name=container_config["display_name"],
        resource_group_name=resource_groups.data.name,
    )
    # Container Role Assignments
    try:
        role_assignments = container_config["iam"]["role_assignments"]
        for assignment in role_assignments:
            # User Group Role Assignment
            if assignment.get("user_group_ref_key") is not None:
                user_group_ref_key = assignment.get("user_group_ref_key")
                GroupRoleAssignment(
                    role_name=assignment["role_definition_name"],
                    group_object_id=user_groups[user_group_ref_key]["object_id"],
                    scope=datalake_containers[ref_key].id,
                )
    except KeyError:
        # No role assignments are found. Evaluate the next container.
        continue
