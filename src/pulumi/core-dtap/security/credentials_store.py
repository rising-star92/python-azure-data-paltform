from pulumi import ResourceOptions
from pulumi_azure_native import keyvault, network
from ingenii_azure_data_platform.defaults import KEY_VAULT_DEFAULT_FIREWALL
from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    ServicePrincipalRoleAssignment,
    UserAssignedIdentityRoleAssignment,
)
from ingenii_azure_data_platform.logs import log_diagnostic_settings, log_network_interfaces
from ingenii_azure_data_platform.utils import generate_resource_name

from logs import log_analytics_workspace
from project_config import platform_config, azure_client, platform_outputs
from platform_shared import add_config_registry_secret, get_devops_principal_id, shared_services_provider, SHARED_OUTPUTS
from management import resource_groups
from management.user_groups import user_groups
from network import vnet, dns

outputs = platform_outputs["security"]["credentials_store"] = {}

# ----------------------------------------------------------------------------------------------------------------------
# FIREWALL IP ACCESS LIST
# This is the global firewall access list and applies to all resources such as key vaults, storage accounts etc.
# ----------------------------------------------------------------------------------------------------------------------
firewall = platform_config.from_yml["network"]["firewall"]
firewall_ip_access_list = [
    keyvault.IPRuleArgs(value=ip_address)
    for ip_address in firewall.get("ip_access_list", [])
]

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT
# ----------------------------------------------------------------------------------------------------------------------
key_vault_config = platform_config.from_yml["security"]["credentials_store"]
key_vault_name = generate_resource_name(
    resource_type="key_vault", resource_name="cred", platform_config=platform_config
)

key_vault = keyvault.Vault(
    resource_name=key_vault_name,
    vault_name=key_vault_name,
    resource_group_name=resource_groups["security"].name,
    location=platform_config.region.long_name,
    properties=keyvault.VaultPropertiesArgs(
        enable_rbac_authorization=True,
        network_acls=(
            keyvault.NetworkRuleSetArgs(
                bypass="AzureServices",
                default_action="Deny",
                ip_rules=(
                    firewall_ip_access_list
                    if len(firewall_ip_access_list) > 0
                    else None
                ),
                virtual_network_rules=[
                    keyvault.VirtualNetworkRuleArgs(id=subnet.id)
                    for subnet in (
                        vnet.dbw_engineering_hosts_subnet,
                        vnet.dbw_engineering_containers_subnet,
                        vnet.dbw_analytics_hosts_subnet,
                        vnet.dbw_analytics_containers_subnet,
                    )
                ],
            )
            if key_vault_config["network"]["firewall"]["enabled"] == True
            else KEY_VAULT_DEFAULT_FIREWALL
        ),
        tenant_id=azure_client.tenant_id,
        sku=keyvault.SkuArgs(
            family="A", name=keyvault.SkuName("standard")
        ),
    ),
    tags=platform_config.tags,
)

outputs["key_vault_id"] = key_vault.id
outputs["key_vault_name"] = key_vault.name


# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT -> PRIVATE ENDPOINT
# ----------------------------------------------------------------------------------------------------------------------

# PRIVATE ENDPOINT
private_endpoint_name = generate_resource_name(
    resource_type="private_endpoint",
    resource_name="for-cred-store",
    platform_config=platform_config,
)
private_endpoint = network.PrivateEndpoint(
    resource_name=private_endpoint_name,
    private_endpoint_name=private_endpoint_name,
    location=platform_config.region.long_name,
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["vault"],
            private_link_service_id=key_vault.id,
            request_message="none",
        )
    ],
    resource_group_name=resource_groups["infra"].name,
    custom_dns_configs=[],
    subnet=network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

# To Log Analytics Workspace
private_endpoint_logs_and_metrics = key_vault_config.get("network", {}) \
                                                    .get("private_endpoint", {})
log_network_interfaces(
    platform_config, log_analytics_workspace.id,
    private_endpoint_name, private_endpoint.network_interfaces,
    logs_config=private_endpoint_logs_and_metrics.get("logs", {}),
    metrics_config=private_endpoint_logs_and_metrics.get("metrics", {})
)

# PRIVATE DNS ZONE GROUP
private_endpoint_dns_zone_group_name = generate_resource_name(
    resource_type="private_dns_zone",
    resource_name="for-cred-store",
    platform_config=platform_config,
)
private_endpoint_dns_zone_group = network.PrivateDnsZoneGroup(
    resource_name=private_endpoint_dns_zone_group_name,
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name=private_endpoint_name,
            private_dns_zone_id=dns.key_vault_private_dns_zone.id,
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=private_endpoint.name,
    resource_group_name=resource_groups["infra"].name,
)

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT -> PRIVATE ENDPOINT FOR DEVOPS
# ----------------------------------------------------------------------------------------------------------------------

shared_vnet = SHARED_OUTPUTS["network"]["virtual_network"]

# PRIVATE ENDPOINT
private_endpoint_name_devops = generate_resource_name(
    resource_type="private_endpoint",
    resource_name="for-cred-store-devops",
    platform_config=platform_config,
)
private_endpoint_devops = network.PrivateEndpoint(
    resource_name=private_endpoint_name_devops,
    private_endpoint_name=private_endpoint_name_devops,
    location=shared_vnet["location"],
    private_link_service_connections=[
        network.PrivateLinkServiceConnectionArgs(
            name=shared_vnet["name"],
            group_ids=["vault"],
            private_link_service_id=key_vault.id,
            request_message="none",
        )
    ],
    resource_group_name=resource_groups["infra"].name,
    custom_dns_configs=[],
    subnet=network.SubnetArgs(
        id=shared_vnet["subnets"]["privatelink"]["id"]
    ),
    opts=ResourceOptions(provider=shared_services_provider)
)

# To Log Analytics Workspace
private_endpoint_logs_and_metrics = key_vault_config.get("network", {}) \
                                                    .get("private_endpoint", {})
log_network_interfaces(
    platform_config, log_analytics_workspace.id,
    private_endpoint_name_devops, private_endpoint_devops.network_interfaces,
    logs_config=private_endpoint_logs_and_metrics.get("logs", {}),
    metrics_config=private_endpoint_logs_and_metrics.get("metrics", {})
)

# PRIVATE DNS ZONE GROUP
private_endpoint_dns_zone_group_name_devops = generate_resource_name(
    resource_type="private_dns_zone",
    resource_name="for-cred-store-devops",
    platform_config=platform_config,
)
private_endpoint_dns_zone_group_devops = network.PrivateDnsZoneGroup(
    resource_name=private_endpoint_dns_zone_group_name_devops,
    private_dns_zone_configs=[
        network.PrivateDnsZoneConfigArgs(
            name=private_endpoint_name_devops,
            private_dns_zone_id=SHARED_OUTPUTS["network"]["dns"]["private_zones"]["key_vault"]["id"],
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=private_endpoint_devops.name,
    resource_group_name=resource_groups["infra"].name,
    opts=ResourceOptions(provider=shared_services_provider)
)

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT -> IAM -> ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------

# Create role assignments defined in the YAML files
for assignment in key_vault_config.get("iam", {}).get("role_assignments", []):
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=key_vault.id,
        )

# Grant access to the Automation Service Principal to manage the key vault.
# We are going to be creating secrets in the key vault later on, so we need the access.
ServicePrincipalRoleAssignment(
    service_principal_object_id=azure_client.object_id,
    role_name="Key Vault Administrator",
    scope=key_vault.id,
)

UserAssignedIdentityRoleAssignment(
    principal_id=get_devops_principal_id(),
    role_name="Key Vault Secrets User",
    scope=key_vault.id,
)

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT -> LOGGING
# ----------------------------------------------------------------------------------------------------------------------

log_diagnostic_settings(
    platform_config, log_analytics_workspace.id,
    key_vault.type, key_vault.id, key_vault_name,
    logs_config=key_vault_config.get("logs", {}),
    metrics_config=key_vault_config.get("metrics", {})
)

# ----------------------------------------------------------------------------------------------------------------------
# DEVOPS ACCESS
# ----------------------------------------------------------------------------------------------------------------------

add_config_registry_secret("credential-key-vault-name", key_vault_name)
