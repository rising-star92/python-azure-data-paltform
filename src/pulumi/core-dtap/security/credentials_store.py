import pulumi
import pulumi_azure_native as azure_native
from pulumi.resource import ResourceOptions

from config import platform as p
from config import helpers as h
from config import azure_client

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
        azure_native.keyvault.IPRuleArgs(value=ip_address)

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT
# ----------------------------------------------------------------------------------------------------------------------
key_vault_config = p.config_object["security"]["credentials_store"]
key_vault_name = p.generate_name("key_vault", "cred")

key_vault = azure_native.keyvault.Vault(
    resource_name=key_vault_name,
    vault_name=key_vault_name,
    resource_group_name=resource_groups.security.name,
    location=p.region_long_name,
    properties=azure_native.keyvault.VaultPropertiesArgs(
        enable_rbac_authorization=True,
        network_acls=(
            azure_native.keyvault.NetworkRuleSetArgs(
                bypass="AzureServices",
                default_action="Deny",
                i_rules=(
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
            else h.key_vault_default_network_acl
        ),
        tenant_id=azure_client.tenant_id,
        sku=azure_native.keyvault.SkuArgs(family="A", name="standard"),
    ),
    tags=p.tags,
)

# ----------------------------------------------------------------------------------------------------------------------
# KEY VAULT -> PRIVATE ENDPOINT
# ----------------------------------------------------------------------------------------------------------------------

# PRIVATE ENDPOINT
private_endpoint_name = p.generate_name("private_endpoint", "for-cred-store")
private_endpoint = azure_native.network.PrivateEndpoint(
    resource_name=private_endpoint_name,
    private_endpoint_name=private_endpoint_name,
    location=p.region_long_name,
    private_link_service_connections=[
        azure_native.network.PrivateLinkServiceConnectionArgs(
            name=vnet.vnet.name,
            group_ids=["vault"],
            private_link_service_id=key_vault.id,
            request_message="none",
        )
    ],
    resource_group_name=resource_groups.infra.name,
    custom_dns_configs=[],
    subnet=azure_native.network.SubnetArgs(id=vnet.privatelink_subnet.id),
)

# PRIVATE DNS ZONE GROUP
private_endpoint_dns_zone_group_name = p.generate_name(
    "private_dns_zone", "for-cred-store")
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
    resource_group_name=resource_groups.infra.name,
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
        azure_native.authorization.RoleAssignment(
            # Hash the resource_name to guarantee uniqueness
            resource_name=p.generate_hash(
                assignment["user_group_ref_key"], assignment["role_definition_name"], key_vault_name),
            principal_id=user_groups[assignment["user_group_ref_key"]].get(
                "object_id"),
            principal_type="Group",
            role_definition_id=p.azure_iam_role_definitions[
                assignment["role_definition_name"]
            ],
            scope=key_vault.id,
            opts=ResourceOptions(delete_before_replace=True)
        )

# Grant access to the Automation Service Principal to manage the key vault.
# We are going to be creating secrets in the key vault later on, so we need the access.
iam_role_assignment_grant_admin_access_to_automation_sp = (
    azure_native.authorization.RoleAssignment(
        # We use a generated name for the service principal,
        # plus the main key vault id to base our md5 hash on.
        # This guarantees uniqueness of the resource name
        # accross the stack.
        resource_name=p.generate_hash(
            "automation-service-principal", key_vault_name),
        principal_id=azure_client.object_id,
        principal_type="ServicePrincipal",
        role_definition_id=p.azure_iam_role_definitions["Key Vault Administrator"],
        scope=key_vault.id,
        opts=ResourceOptions(delete_before_replace=True)
    )
)
