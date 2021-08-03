import pulumi
import pulumi_azuread as azuread

from config import platform as p

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
user_group_definitions = p.config_object["management"]["user_groups"]
user_groups = {}

for ref_key in user_group_definitions:
    group_config = user_group_definitions[ref_key]
    group_name = p.generate_name(
        "user_group", group_config["display_name"])
    outputs = {"display_name": group_name}

    # If no group object is provided we will go ahead and create the Azure AD group.
    if group_config.get("object_id") is None:
        group_resource = azuread.Group(
            group_name.lower(), display_name=group_name)
        outputs["object_id"] = group_resource.object_id
    # If an object_id key has been set, we will pass that as an output.
    # It means the Azure AD groups have been created beforehand.
    else:
        outputs["object_id"] = group_config["object_id"]

    # Save the current user group metadata in the user_groups dictionary.
    user_groups[ref_key] = outputs

pulumi.export("user_groups", user_groups)
