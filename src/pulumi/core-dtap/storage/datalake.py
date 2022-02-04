import pulumi_azure as azure_classic
from pulumi import Output, ResourceOptions
from pulumi_azure_native import keyvault, network, storage

from ingenii_azure_data_platform.defaults import STORAGE_ACCOUNT_DEFAULT_FIREWALL
from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    UserAssignedIdentityRoleAssignment,
)
from ingenii_azure_data_platform.logs import (
    log_diagnostic_settings,
    log_network_interfaces,
)
from ingenii_azure_data_platform.network import PlatformFirewall
from ingenii_azure_data_platform.utils import generate_resource_name, lock_resource

from logs import log_analytics_workspace
from management import resource_groups
from management.user_groups import user_groups
from network import dns, vnet
from platform_shared import (
    add_config_registry_secret,
    get_devops_principal_id,
)
from project_config import platform_config, platform_outputs, azure_client
from security import credentials_store

outputs = platform_outputs["storage"]["datalake"] = {}

# ----------------------------------------------------------------------------------------------------------------------
# FIREWALL IP ACCESS LIST
# This is the global firewall access list and applies to all resources such as key vaults, storage accounts etc.
# ----------------------------------------------------------------------------------------------------------------------
firewall = platform_config.from_yml["network"]["firewall"]
firewall_ip_access_list = [
    storage.IPRuleArgs(i_p_address_or_range=ip_address)
    for ip_address in firewall.get("ip_access_list", [])
]

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE
# ----------------------------------------------------------------------------------------------------------------------
datalake_config = platform_config.from_yml["storage"]["datalake"]
datalake_firewall_config = datalake_config.get("network", {}).get("firewall", {})

datalake_name = generate_resource_name(
    resource_type="storage_account",
    resource_name="datalake",
    platform_config=platform_config,
)
datalake_resource_group_name = resource_groups["data"].name

if datalake_firewall_config.get("enabled"):
    firewall = platform_config.global_firewall + PlatformFirewall(
        enabled=True,
        ip_access_list=datalake_firewall_config.get("ip_access_list", []),
        vnet_access_list=datalake_firewall_config.get("vnet_access_list", []),
        resource_access_list=datalake_firewall_config.get("resource_access_list", []),
        trust_azure_services=datalake_firewall_config.get(
            "trust_azure_services", False
        ),
    )

    trusted_subnet_ids = [
        subnet.id
        for subnet in (
            vnet.dbw_engineering_hosts_subnet,
            vnet.dbw_engineering_containers_subnet,
            vnet.dbw_analytics_hosts_subnet,
            vnet.dbw_analytics_containers_subnet,
        )
    ]

    network_rule_set = storage.NetworkRuleSetArgs(
        bypass=firewall.bypass_services,
        default_action=firewall.default_action,
        ip_rules=[
            storage.IPRuleArgs(i_p_address_or_range=ip_add)
            for ip_add in firewall.ip_access_list
        ],
        virtual_network_rules=[
            storage.VirtualNetworkRuleArgs(
                virtual_network_resource_id=subnet_id,
            )
            for subnet_id in set(trusted_subnet_ids + firewall.vnet_access_list)
        ],
    )
else:
    network_rule_set = STORAGE_ACCOUNT_DEFAULT_FIREWALL

datalake = storage.StorageAccount(
    resource_name=datalake_name,
    account_name=datalake_name,
    allow_blob_public_access=False,
    network_rule_set=network_rule_set,
    is_hns_enabled=True,
    kind=storage.Kind.STORAGE_V2,
    location=platform_config.region.long_name,
    minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
    resource_group_name=datalake_resource_group_name,
    sku=storage.SkuArgs(name=storage.SkuName.STANDARD_GRS),
    tags=platform_config.tags,
    opts=ResourceOptions(
        protect=platform_config.resource_protection,
    ),
)
if platform_config.resource_protection:
    lock_resource(datalake_name, datalake.id)

outputs["id"] = datalake.id
outputs["name"] = datalake.name
outputs["containers_view_url"] = Output.all(
    datalake_resource_group_name, datalake.name
).apply(
    lambda args: f"https://portal.azure.com/#@/resource/subscriptions/{azure_client.subscription_id}/resourceGroups/{args[0]}/providers/Microsoft.Storage/storageAccounts/{args[1]}/containersList"
)


# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> LOGGING
# ----------------------------------------------------------------------------------------------------------------------

log_diagnostic_settings(
    platform_config,
    log_analytics_workspace.id,
    datalake.type,
    datalake.id,
    datalake_name,
    logs_config=datalake_config.get("logs", {}),
    metrics_config=datalake_config.get("metrics", {}),
)

blob_logs_and_metrics = datalake_config.get("storage_type_logging", {}).get("blob", {})
log_diagnostic_settings(
    platform_config,
    log_analytics_workspace.id,
    datalake.type,
    datalake.id.apply(lambda dl_id: f"{dl_id}/blobservices/default"),
    f"{datalake_name}-blob",
    logs_config=blob_logs_and_metrics.get("logs", {}),
    metrics_config=blob_logs_and_metrics.get("metrics", {}),
)

table_logs_and_metrics = datalake_config.get("storage_type_logging", {}).get(
    "table", {}
)
log_diagnostic_settings(
    platform_config,
    log_analytics_workspace.id,
    datalake.type,
    datalake.id.apply(lambda dl_id: f"{dl_id}/tableservices/default"),
    f"{datalake_name}-table",
    logs_config=table_logs_and_metrics.get("logs", {}),
    metrics_config=table_logs_and_metrics.get("metrics", {}),
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
blob_private_endpoint = network.PrivateEndpoint(
    resource_name=blob_private_endpoint_name,
    location=platform_config.region.long_name,
    private_endpoint_name=blob_private_endpoint_name,
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["blob"],
            private_link_service_id=datalake.id,
            request_message="none",
        )
    ],
    custom_dns_configs=[],
    resource_group_name=resource_groups["infra"].name,
    subnet=network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

if platform_config.resource_protection:
    lock_resource(blob_private_endpoint_name, blob_private_endpoint.id)

# To Log Analytics Workspace
blob_private_endpoint_details = (
    datalake_config.get("network", {}).get("private_endpoint", {}).get("blob", {})
)
log_network_interfaces(
    platform_config,
    log_analytics_workspace.id,
    blob_private_endpoint_name,
    blob_private_endpoint.network_interfaces,
    logs_config=blob_private_endpoint_details.get("logs", {}),
    metrics_config=blob_private_endpoint_details.get("metrics", {}),
)

# BLOB PRIVATE DNS ZONE GROUP
blob_private_endpoint_dns_zone_group_name = (
    f"{blob_private_endpoint_name}-dns-zone-group"
)

blob_private_endpoint_dns_zone_group = network.PrivateDnsZoneGroup(
    resource_name=blob_private_endpoint_dns_zone_group_name,
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name=blob_private_endpoint_name,
            private_dns_zone_id=dns.storage_blob_private_dns_zone.id,
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=blob_private_endpoint.name,
    resource_group_name=resource_groups["infra"].name,
)
if platform_config.resource_protection:
    lock_resource(
        blob_private_endpoint_dns_zone_group_name,
        blob_private_endpoint_dns_zone_group.id,
    )

# DFS PRIVATE ENDPOINT
dfs_private_endpoint_name = generate_resource_name(
    resource_type="private_endpoint",
    resource_name="for-datalake-dfs",
    platform_config=platform_config,
)

dfs_private_endpoint = network.PrivateEndpoint(
    resource_name=dfs_private_endpoint_name,
    location=platform_config.region.long_name,
    private_endpoint_name=dfs_private_endpoint_name,
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["dfs"],
            private_link_service_id=datalake.id,
            request_message="none",
        )
    ],
    resource_group_name=resource_groups["infra"].name,
    custom_dns_configs=[],
    subnet=network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

if platform_config.resource_protection:
    lock_resource(dfs_private_endpoint_name, dfs_private_endpoint.id)

# To Log Analytics Workspace
dfs_private_endpoint_details = (
    datalake_config.get("network", {}).get("private_endpoint", {}).get("dfs", {})
)
log_network_interfaces(
    platform_config,
    log_analytics_workspace.id,
    dfs_private_endpoint_name,
    dfs_private_endpoint.network_interfaces,
    logs_config=dfs_private_endpoint_details.get("logs", {}),
    metrics_config=dfs_private_endpoint_details.get("metrics", {}),
)

# DFS PRIVATE DNS ZONE GROUP
dfs_private_endpoint_dns_zone_group_name = f"{dfs_private_endpoint_name}-dns-zone-group"
dfs_private_endpoint_dns_zone_group = network.PrivateDnsZoneGroup(
    resource_name=dfs_private_endpoint_dns_zone_group_name,
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name=dfs_private_endpoint_name,
            private_dns_zone_id=dns.storage_dfs_private_dns_zone.id,
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=dfs_private_endpoint.name,
    resource_group_name=resource_groups["infra"].name,
)

if platform_config.resource_protection:
    lock_resource(
        dfs_private_endpoint_dns_zone_group_name, dfs_private_endpoint_dns_zone_group.id
    )

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> IAM -> ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------

# Create role assignments defined in the YAML files
for assignment in datalake_config["iam"].get("role_assignments", {}):
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            principal_id=user_groups[user_group_ref_key]["object_id"],
            principal_name=user_group_ref_key,
            role_name=assignment["role_definition_name"],
            scope=datalake.id,
            scope_description="datalake",
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> CONTAINERS
# ----------------------------------------------------------------------------------------------------------------------

# This dict will keep all container resources.
datalake_containers = {}

# If no containers are defined in the YAML files, we'll not attempt to create any.
for ref_key, container_config in datalake_config.get("containers", {}).items():
    datalake_container_name = generate_resource_name(
        resource_type="storage_blob_container",
        resource_name=ref_key,
        platform_config=platform_config,
    )
    datalake_containers[ref_key] = storage.BlobContainer(
        resource_name=datalake_container_name,
        account_name=datalake.name,
        container_name=container_config["display_name"],
        resource_group_name=datalake_resource_group_name,
        opts=ResourceOptions(
            protect=platform_config.resource_protection,
            ignore_changes=[
                "public_access",
                "default_encryption_scope",
                "deny_encryption_scope_override",
            ],
        ),
    )
    if platform_config.resource_protection:
        lock_resource(datalake_container_name, datalake_containers[ref_key].id)

    # Container Role Assignments
    role_assignments = container_config.get("iam", {}).get("role_assignments", [])
    for assignment in role_assignments:
        # User Group Role Assignment
        if assignment.get("user_group_ref_key") is not None:
            user_group_ref_key = assignment.get("user_group_ref_key")
            GroupRoleAssignment(
                principal_id=user_groups[user_group_ref_key]["object_id"],
                principal_name=user_group_ref_key,
                role_name=assignment["role_definition_name"],
                scope=datalake_containers[ref_key].id,
                scope_description=f"datalake-container-{ref_key}",
            )

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> TABLES
# ----------------------------------------------------------------------------------------------------------------------

# This dict will keep all table resources.
datalake_tables = {}

# If no containers are defined in the YAML files, we'll not attempt to create any.
for ref_key, table_config in datalake_config.get("tables", {}).items():

    table_name = table_config["display_name"]

    datalake_table_resource_name = (
        f"{datalake_name}-{table_config['display_name']}".lower()
    )
    datalake_tables[ref_key] = storage.Table(
        resource_name=datalake_table_resource_name,
        resource_group_name=datalake_resource_group_name,
        account_name=datalake.name,
        table_name=table_name,
    )
    if platform_config.resource_protection:
        lock_resource(datalake_table_resource_name, datalake_tables[ref_key].id)

    entities = table_config.get("entities", {})

    for entity_ref_key, entity_config in entities.items():
        azure_classic.storage.TableEntity(
            resource_name=f"{datalake_name}-{table_name}-{entity_ref_key}".lower(),
            storage_account_name=datalake.name,
            table_name=datalake_tables[ref_key].name,
            partition_key=entity_config.get("partition_key"),
            row_key=entity_config.get("row_key"),
            entity=entity_config.get("entity", {}),
        )


# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> TABLES -> SAS
# ----------------------------------------------------------------------------------------------------------------------

table_storage_sas = datalake.name.apply(
    lambda account_name: storage.list_storage_account_sas(
        account_name=account_name,
        protocols=storage.HttpProtocol.HTTPS,
        resource_types=storage.SignedResourceTypes.O,
        services=storage.Services.T,
        shared_access_start_time="2021-08-31T00:00:00Z",
        shared_access_expiry_time="2041-08-31T00:00:00Z",
        permissions="".join(
            [
                storage.Permissions.R,
                storage.Permissions.W,
                storage.Permissions.D,
                storage.Permissions.L,
                storage.Permissions.A,
                storage.Permissions.C,
                storage.Permissions.U,
            ]
        ),
        resource_group_name=datalake_resource_group_name,
    )
)

# Save to Key Vault
keyvault.Secret(
    resource_name="datalake-table-storage-sas-uri-secret",
    resource_group_name=resource_groups["security"].name,
    vault_name=credentials_store.key_vault.name,
    secret_name="datalake-table-storage-sas-uri",
    properties=keyvault.SecretPropertiesArgs(
        value=Output.concat(
            datalake.primary_endpoints.table, "?", table_storage_sas.account_sas_token
        ),
    ),
)

# ----------------------------------------------------------------------------------------------------------------------
# DEVOPS ASSIGNMENT
# ----------------------------------------------------------------------------------------------------------------------

devops_principal_id = get_devops_principal_id()
devops_principal_name = "deployment-user-identity"
for container in ["dbt", "preprocess"]:
    UserAssignedIdentityRoleAssignment(
        principal_id=devops_principal_id,
        principal_name=devops_principal_name,
        role_name="Storage Blob Data Contributor",
        scope=datalake_containers[container].id,
        scope_description=f"datalake-container-{container}",
    )

add_config_registry_secret(
    "data-lake-name", datalake.name, infrastructure_identifier=True
)

# Required while the Azure CLI command 'sync' does not support MSI authentication
# https://docs.microsoft.com/en-us/cli/azure/storage/blob?view=azure-cli-latest#az_storage_blob_sync
UserAssignedIdentityRoleAssignment(
    principal_id=devops_principal_id,
    principal_name=devops_principal_name,
    role_name="Reader and Data Access",
    scope=datalake.id,
    scope_description="datalake",
)
