from pulumi.resource import ResourceOptions
from pulumi_azure_native import containerregistry as cr

from ingenii_azure_data_platform.defaults import CONTAINER_REGISTRY_DEFAULT_FIREWALL
from ingenii_azure_data_platform.iam import GroupRoleAssignment
from ingenii_azure_data_platform.utils import generate_resource_name

from management.resource_groups import resource_groups
from management.user_groups import user_groups
from project_config import platform_config, platform_outputs

outputs = platform_outputs["storage"]["container_registry"] = {}

resource_group_name = resource_groups["data"].name

registry_config = platform_config.from_yml.get("storage", {}).get(
    "container_registry", {}
)

sku_map = {sku.value.lower(): sku.value for sku in cr.SkuName}

registries = {}

for ref_key, config in registry_config.items():

    # Generate a resource name complying with our naming conventions.
    resource_name = generate_resource_name(
        resource_type="container_registry",
        resource_name=config["display_name"],
        platform_config=platform_config,
    )

    firewall_config = config.get("network", {}).get("firewall", {})
    firewall_enabled = firewall_config.get("enabled", False)

    if firewall_enabled:
        network_rule_set = cr.NetworkRuleSetArgs(
            default_action=cr.DefaultAction.DENY,
            ip_rules=[
                cr.IPRuleArgs(i_p_address_or_range=ip, action="Allow")
                for ip in firewall_config.get("ip_access_list", [])
            ],
        )
    else:
        network_rule_set = CONTAINER_REGISTRY_DEFAULT_FIREWALL

    registry = cr.Registry(
        resource_name=resource_name,
        location=platform_config.region.long_name,
        registry_name=config["display_name"],
        resource_group_name=resource_group_name,
        admin_user_enabled=config.get("admin_user_enabled", False),
        network_rule_set=network_rule_set,
        sku=cr.SkuArgs(name=sku_map[config.get("sku", "standard")]),
        tags=platform_config.tags | config.get("tags", {}),
        opts=ResourceOptions(
            protect=platform_config.resource_protection,
            ignore_changes=[
                "policies"  # Policy management will be implemented as needed.
            ],
        ),
    )

    registries[ref_key] = registry

    # IAM Role Assignments
    # Create role assignments defined in the YAML files
    for assignment in config.get("iam", {}).get("role_assignments", []):
        # User Group Assignment
        user_group_ref_key = assignment.get("user_group_ref_key")
        if user_group_ref_key is not None:
            GroupRoleAssignment(
                principal_name=user_group_ref_key,
                principal_id=user_groups[user_group_ref_key]["object_id"],
                role_name=assignment["role_definition_name"],
                scope=registry.id,
                scope_description="container-registry",
            )

    # Export outputs
    outputs[ref_key] = {
        "id": registry.id,
        "url": registry.login_server,
        "display_name": config["display_name"],
        "resource_group_name": resource_group_name.apply(lambda name: name),
    }