import pulumi
from pulumi import output
from config import platform_config
from ingenii_azure_data_platform.management import UserGroup
from ingenii_azure_data_platform.utils import generate_resource_name

# ----------------------------------------------------------------------------------------------------------------------
# USER GROUPS
# Schema path: management.user_groups.<user_group_ref_key>
# Example:
# ---
# management:
#   user_groups:
#     <user_group_ref_key>:
#       display_name:
#       object_id:
# ----------------------------------------------------------------------------------------------------------------------
user_group_definitions = platform_config.yml_config["management"]["user_groups"]
user_groups = {}

for ref_key, group_config in user_group_definitions.items():
    outputs = {}

    # If no group object is provided we will go ahead and create the Azure AD group.
    if group_config.get("object_id") is None:
        group_resource = UserGroup(
            group_name=group_config["display_name"], platform_config=platform_config
        )
        outputs["display_name"] = group_resource.display_name
        outputs["object_id"] = group_resource.object_id
    # If an object_id key has been set, we will pass that as an output.
    # It means the Azure AD groups have been created beforehand.
    else:
        outputs["display_name"] = generate_resource_name(
            resource_type="user_group",
            resource_name=group_config["display_name"],
            platform_config=platform_config,
        )
        outputs["object_id"] = group_config["object_id"]

    # Save the current user group metadata in the user_groups dictionary.
    user_groups[ref_key] = outputs

pulumi.export("user_groups", user_groups)
