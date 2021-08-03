import pulumi
from pulumi.resource import ResourceOptions
import pulumi_azure_native as azure_native

from config import platform as p
from config import helpers as h

from management import resource_groups, user_groups
from network import vnet, dns

# ----------------------------------------------------------------------------------------------------------------------
# FIREWALL IP ACCESS LIST
# This is the global firewall access list and applies to all resources such as key vaults, storage accounts etc.
# ----------------------------------------------------------------------------------------------------------------------
firewall = p.config_object["network"]["firewall"]
firewall_ip_access_list = []
if firewall.get("ip_access_list") is not None:
    for ip_address in firewall.get("ip_access_list"):
        azure_native.storage.IPRuleArgs(i_p_address_or_range=ip_address)

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE
# ----------------------------------------------------------------------------------------------------------------------
datalake_config = p.config_object["storage"]["datalake"]
datalake_name = p.generate_name("storage_account", "datalake")

datalake = azure_native.storage.StorageAccount(
    resource_name=datalake_name,
    account_name=datalake_name,
    allow_blob_public_access=False,
    network_rule_set=(
        azure_native.storage.NetworkRuleSetArgs(
            bypass="AzureServices",
            default_action="Deny",
            ip_rules=(
                firewall_ip_access_list if len(
                    firewall_ip_access_list) > 0 else None
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
        if False
        else h.storage_default_network_acl
    ),
    is_hns_enabled=True,
    kind="StorageV2",
    location=p.region_long_name,
    minimum_tls_version="TLS1_2",
    resource_group_name=resource_groups.data.name,
    sku=azure_native.storage.SkuArgs(
        name="Standard_GRS",
    ),
    tags=p.tags
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> PRIVATE ENDPOINTS
# ----------------------------------------------------------------------------------------------------------------------

# BLOB PRIVATE ENDPOINT
blob_private_endpoint_name = p.generate_name(
    "private_endpoint", "for-datalake-blob")
blob_private_endpoint = azure_native.network.PrivateEndpoint(
    resource_name=blob_private_endpoint_name,
    location=p.region_long_name,
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
dfs_private_endpoint_name = p.generate_name(
    "private_endpoint", "for-datalake-dfs")

dfs_private_endpoint = azure_native.network.PrivateEndpoint(
    resource_name=dfs_private_endpoint_name,
    location=p.region_long_name,
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
        azure_native.authorization.RoleAssignment(
            # Hash the resource_name to guarantee uniqueness
            resource_name=p.generate_hash(
                assignment["user_group_ref_key"], assignment["role_definition_name"], datalake_name),
            principal_id=user_groups[assignment["user_group_ref_key"]].get(
                "object_id"),
            principal_type="Group",
            role_definition_id=p.azure_iam_role_definitions[
                assignment["role_definition_name"]
            ],
            scope=datalake.id,
            opts=ResourceOptions(delete_before_replace=True)
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

for ref_key in datalake_container_definitions:
    container_config = datalake_container_definitions[ref_key]
    datalake_container_name = p.generate_name(
        "storage_blob_container", ref_key)
    datalake_containers[ref_key] = azure_native.storage.BlobContainer(
        resource_name=datalake_container_name,
        account_name=datalake.name,
        container_name=container_config["display_name"],
        resource_group_name=resource_groups.data.name
    )
    # Container Role Assignments
    try:
        role_assignments = container_config["iam"]["role_assignments"]
        for assignment in role_assignments:
            # User Group Role Assignment
            if assignment.get("user_group_ref_key") is not None:
                user_group_ref_key = assignment.get("user_group_ref_key")
                role_definition_name = assignment.get("role_definition_name")
                principal_id = user_groups[user_group_ref_key].get("object_id")
                role_definition_id = p.azure_iam_role_definitions[role_definition_name]
            azure_native.authorization.RoleAssignment(
                resource_name=p.generate_hash(
                    user_group_ref_key, role_definition_name, ref_key),
                principal_id=principal_id,
                principal_type="Group",
                role_definition_id=role_definition_id,
                scope=datalake_containers[ref_key].id
            )
    except:
        # No role assignments are found. Evaluate the next container.
        continue
