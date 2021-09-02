from config import platform_config
from management.user_groups import user_groups
from ingenii_azure_data_platform.management import ResourceGroup
from ingenii_azure_data_platform.iam import GroupRoleAssignment

resource_groups_config = platform_config.yml_config["management"]["resource_groups"]

# ----------------------------------------------------------------------------------------------------------------------
# INFRA RESOURCE GROUP
# ----------------------------------------------------------------------------------------------------------------------
infra = ResourceGroup("infra", platform_config)

infra_iam_role_assignments = resource_groups_config["infra"]["iam"]["role_assignments"]

for assignment in infra_iam_role_assignments:
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=infra.id,
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA RESOURCE GROUP
# ----------------------------------------------------------------------------------------------------------------------
data = ResourceGroup("data", platform_config)

data_iam_role_assignments = resource_groups_config["data"]["iam"]["role_assignments"]

for assignment in data_iam_role_assignments:
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=data.id,
        )

# ----------------------------------------------------------------------------------------------------------------------
# SECURITY RESOURCE GROUP
# ----------------------------------------------------------------------------------------------------------------------
security = ResourceGroup("security", platform_config)

security_iam_role_assignments = resource_groups_config["security"]["iam"][
    "role_assignments"
]

for assignment in security_iam_role_assignments:
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=security.id,
        )
