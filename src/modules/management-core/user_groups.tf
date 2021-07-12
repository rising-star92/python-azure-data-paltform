#----------------------------------------------------------------------------------------------------------------------
# AZURE AD GROUPS
#----------------
# Schema Path: platform.management.user_groups
# Schema Example:
# ---
# platform:
#   management:
#     user_groups:
#       <user_group_ref_key>:
#         enabled:
#         display_name:
#         description:
#         prevent_duplicate_names:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __user_groups_raw_configs = try(local.config.platform.management.user_groups, {})

  __user_groups_processed_config = {
    for user_group_ref_key, user_group_config in local.__user_groups_raw_configs :
    user_group_ref_key => {
      resource_id = user_group_ref_key
      ref_key     = user_group_ref_key

      name                    = "${upper(local.prefix)}-${title(local.env)}-${title(user_group_config.display_name)}"
      description             = try(user_group_config.description, "")
      prevent_duplicate_names = try(user_group_config.prevent_duplicate_names, true)

    } if try(user_group_config.enabled, true)
  }

  user_groups = { for config in local.__user_groups_processed_config : config.resource_id => config }
}

resource "azuread_group" "this" {
  for_each = local.user_groups

  display_name            = each.value.name
  description             = each.value.description
  prevent_duplicate_names = each.value.prevent_duplicate_names
}
