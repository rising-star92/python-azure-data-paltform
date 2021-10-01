import pulumi_azure_native as azure_native
from ingenii_azure_data_platform.utils import generate_resource_name
from ingenii_azure_data_platform.defaults import KEY_VAULT_DEFAULT_FIREWALL
from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    ServicePrincipalRoleAssignment,
)
from pulumi_azure_native import keyvault
from pulumi_azure_native.keyvault import key

from project_config import platform_config, azure_client, platform_outputs
from management import resource_groups
from management.user_groups import user_groups

from network import vnet, dns

outputs = platform_outputs["security"]["credentials_store"] = {}

# ----------------------------------------------------------------------------------------------------------------------
# FIREWALL IP ACCESS LIST
# This is the global firewall access list and applies to all resources such as key vaults, storage accounts etc.
# ----------------------------------------------------------------------------------------------------------------------
firewall = platform_config.from_yml["network"]["firewall"]
firewall_ip_access_list = []
if firewall.get("ip_access_list") is not None:
    for ip_address in firewall.get("ip_access_list"):
        firewall_ip_access_list.append(
            azure_native.keyvault.IPRuleArgs(value=ip_address)
        )

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT
# ----------------------------------------------------------------------------------------------------------------------
key_vault_config = platform_config.from_yml["security"]["credentials_store"]
key_vault_name = generate_resource_name(
    resource_type="key_vault", resource_name="cred", platform_config=platform_config
)

key_vault = azure_native.keyvault.Vault(
    resource_name=key_vault_name,
    vault_name=key_vault_name,
    resource_group_name=resource_groups["security"].name,
    location=platform_config.region.long_name,
    properties=azure_native.keyvault.VaultPropertiesArgs(
        enable_rbac_authorization=True,
        network_acls=(
            azure_native.keyvault.NetworkRuleSetArgs(
                bypass="AzureServices",
                default_action="Deny",
                ip_rules=(
                    firewall_ip_access_list
                    if len(firewall_ip_access_list) > 0
                    else None
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
            if key_vault_config["network"]["firewall"]["enabled"] == True
            else KEY_VAULT_DEFAULT_FIREWALL
        ),
        tenant_id=azure_client.tenant_id,
        sku=azure_native.keyvault.SkuArgs(
            family="A", name=azure_native.keyvault.SkuName("standard")
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
private_endpoint = azure_native.network.PrivateEndpoint(
    resource_name=private_endpoint_name,
    private_endpoint_name=private_endpoint_name,
    location=platform_config.region.long_name,
    private_link_service_connections=[
        azure_native.network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["vault"],
            private_link_service_id=key_vault.id,
            request_message="none",
        )
    ],
    resource_group_name=resource_groups["infra"].name,
    custom_dns_configs=[],
    subnet=azure_native.network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

# PRIVATE DNS ZONE GROUP
private_endpoint_dns_zone_group_name = generate_resource_name(
    resource_type="private_dns_zone",
    resource_name="for-cred-store",
    platform_config=platform_config,
)
private_endpoint_dns_zone_group = azure_native.network.PrivateDnsZoneGroup(
    resource_name=private_endpoint_dns_zone_group_name,
    private_dns_zone_configs=[
        azure_native.network.PrivateDnsZoneConfigArgs(
            name=private_endpoint_name,
            private_dns_zone_id=dns.key_vault_private_dns_zone.id,
        )
    ],
    private_dns_zone_group_name="privatelink",
    private_endpoint_name=private_endpoint.name,
    resource_group_name=resource_groups["infra"].name,
)

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT -> IAM -> ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------
try:
    iam_role_assignments = key_vault_config["iam"]["role_assignments"]
except:
    iam_role_assignments = {}

# Create role assignments defined in the YAML files
for assignment in iam_role_assignments:
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
