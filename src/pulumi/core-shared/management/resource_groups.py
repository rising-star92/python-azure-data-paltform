from project_config import platform_config, platform_outputs
from ingenii_azure_data_platform.management import ResourceGroup
from ingenii_azure_data_platform.iam import GroupRoleAssignment

from .user_groups import user_groups

resource_groups_config = platform_config.from_yml["management"]["resource_groups"]

outputs = platform_outputs["management"]["resource_groups"] = {}

resource_groups = {}

for ref_key, config in resource_groups_config.items():
    resource = ResourceGroup(config["display_name"], platform_config)
    resource_groups[ref_key] = resource

    # Export resource group metadata
    outputs[ref_key] = {
        "name": resource.name,
        "location": resource.location,
        "id": resource.id,
    }

    # IAM role assignments
    role_assignments = config.get("iam", {}).get("role_assignments", {})

    for assignment in role_assignments:
        # User group role assignment
        user_group_ref_key = assignment.get("user_group_ref_key")

        if user_group_ref_key is not None:
            GroupRoleAssignment(
                role_name=assignment["role_definition_name"],
                group_object_id=user_groups[user_group_ref_key]["object_id"],
                scope=resource_groups[ref_key].id,
            )