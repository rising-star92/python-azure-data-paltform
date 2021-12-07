import pulumi_azure_native as azure_native
import pulumi_azure as azure_classic
from pulumi import ResourceOptions, Output

from ingenii_azure_data_platform.defaults import STORAGE_ACCOUNT_DEFAULT_FIREWALL

from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    UserAssignedIdentityRoleAssignment,
)
from ingenii_azure_data_platform.logs import (
    log_diagnostic_settings,
    log_network_interfaces,
)
from ingenii_azure_data_platform.utils import generate_resource_name

from logs import log_analytics_workspace
from project_config import platform_config, platform_outputs
from platform_shared import (
    shared_services_provider,
    get_devops_principal_id,
    get_devops_config_registry,
    get_devops_config_registry_resource_group,
)
from management import resource_groups
from management.user_groups import user_groups
from network import vnet, dns
from security import credentials_store

outputs = platform_outputs["storage"]["datalake"] = {}

# ----------------------------------------------------------------------------------------------------------------------
# FIREWALL IP ACCESS LIST
# This is the global firewall access list and applies to all resources such as key vaults, storage accounts etc.
# ----------------------------------------------------------------------------------------------------------------------
firewall = platform_config.from_yml["network"]["firewall"]
firewall_ip_access_list = [
    azure_native.storage.IPRuleArgs(i_p_address_or_range=ip_address)
    for ip_address in firewall.get("ip_access_list", [])
]

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE
# ----------------------------------------------------------------------------------------------------------------------
datalake_config = platform_config.from_yml["storage"]["datalake"]
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
    resource_group_name=resource_groups["data"].name,
    sku=azure_native.storage.SkuArgs(
        name="Standard_GRS",
    ),
    tags=platform_config.tags,
)

outputs["id"] = datalake.id
outputs["name"] = datalake.name

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
    resource_group_name=resource_groups["infra"].name,
    subnet=azure_native.network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

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
    resource_group_name=resource_groups["infra"].name,
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
    resource_group_name=resource_groups["infra"].name,
    custom_dns_configs=[],
    subnet=azure_native.network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

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
    resource_group_name=resource_groups["infra"].name,
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
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=datalake.id,
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
    datalake_containers[ref_key] = azure_native.storage.BlobContainer(
        resource_name=datalake_container_name,
        account_name=datalake.name,
        container_name=container_config["display_name"],
        resource_group_name=resource_groups["data"].name,
        opts=ResourceOptions(
            ignore_changes=[
                "public_access",
                "default_encryption_scope",
                "deny_encryption_scope_override",
            ]
        ),
    )
    # Container Role Assignments
    role_assignments = container_config.get("iam", {}).get("role_assignments", [])
    for assignment in role_assignments:
        # User Group Role Assignment
        if assignment.get("user_group_ref_key") is not None:
            user_group_ref_key = assignment.get("user_group_ref_key")
            GroupRoleAssignment(
                role_name=assignment["role_definition_name"],
                group_object_id=user_groups[user_group_ref_key]["object_id"],
                scope=datalake_containers[ref_key].id,
            )

# ----------------------------------------------------------------------------------------------------------------------
# DATA LAKE -> TABLES
# ----------------------------------------------------------------------------------------------------------------------

# This dict will keep all table resources.
datalake_tables = {}

# If no containers are defined in the YAML files, we'll not attempt to create any.
for ref_key, table_config in datalake_config.get("tables", {}).items():

    table_name = table_config["display_name"]

    datalake_tables[ref_key] = azure_native.storage.Table(
        resource_name=f"{datalake_name}-{table_config['display_name']}".lower(),
        resource_group_name=resource_groups["data"].name,
        account_name=datalake.name,
        table_name=table_name,
    )

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
    lambda account_name: azure_native.storage.list_storage_account_sas(
        account_name=account_name,
        protocols=azure_native.storage.HttpProtocol.HTTPS,
        resource_types=azure_native.storage.SignedResourceTypes.O,
        services=azure_native.storage.Services.T,
        shared_access_start_time="2021-08-31T00:00:00Z",
        shared_access_expiry_time="2041-08-31T00:00:00Z",
        permissions="".join(
            [
                azure_native.storage.Permissions.R,
                azure_native.storage.Permissions.W,
                azure_native.storage.Permissions.D,
                azure_native.storage.Permissions.L,
                azure_native.storage.Permissions.A,
                azure_native.storage.Permissions.C,
                azure_native.storage.Permissions.U,
            ]
        ),
        resource_group_name=resource_groups["data"].name,
    )
)

# Save to Key Vault
azure_native.keyvault.Secret(
    resource_name="datalake-table-storage-sas-uri-secret",
    resource_group_name=resource_groups["security"].name,
    vault_name=credentials_store.key_vault.name,
    secret_name="datalake-table-storage-sas-uri",
    properties=azure_native.keyvault.SecretPropertiesArgs(
        value=Output.concat(
            datalake.primary_endpoints.table, "?", table_storage_sas.account_sas_token
        ),
    ),
)

# ----------------------------------------------------------------------------------------------------------------------
# DEVOPS ASSIGNMENT
# ----------------------------------------------------------------------------------------------------------------------

devops_principal_id = get_devops_principal_id()
for container in ["dbt", "utilities"]:
    UserAssignedIdentityRoleAssignment(
        role_name="Storage Blob Data Contributor",
        principal_id=devops_principal_id,
        scope=datalake_containers[container].id,
    )

azure_native.keyvault.Secret(
    resource_name="devops-datalake-name",
    resource_group_name=get_devops_config_registry_resource_group(),
    vault_name=get_devops_config_registry()["key_vault_name"],
    secret_name=f"data-lake-name-{platform_config.stack}",
    properties=azure_native.keyvault.SecretPropertiesArgs(value=datalake.name),
    opts=ResourceOptions(provider=shared_services_provider),
)

# Required while the Azure CLI command 'sync' does not support MSI authentication
# https://docs.microsoft.com/en-us/cli/azure/storage/blob?view=azure-cli-latest#az_storage_blob_sync
UserAssignedIdentityRoleAssignment(
    role_name="Reader and Data Access",
    principal_id=devops_principal_id,
    scope=datalake.id,
)
