#----------------------------------------------------------------------------------------------------------------------
# AZURE RESOURCE GROUPS
#----------------------
# Schema Path: platform.management.resource_groups
# Schema Example:
# ---
# platform:
#   management:
#     resource_groups:
#       <resource_group_ref_key>:
#         enabled:
#         display_name: 
#         iam: 
#         tags: 
#----------------------------------------------------------------------------------------------------------------------
locals {
  __resource_groups_raw_configs = try(local.config.platform.management.resource_groups, {})

  __resource_groups_processed_configs = {
    for resource_group_ref_key, resource_group_config in local.__resource_groups_raw_configs :
    resource_group_ref_key => {
      resource_id = resource_group_ref_key
      ref_key     = resource_group_ref_key

      name   = lower("${local.prefix}-${local.region.short_name}-${local.env}-${resource_group_config.display_name}")
      tags   = merge(local.tags, try(resource_group_config.tags, {}))
      region = local.region.long_name

      iam = try(resource_group_config.iam, {})

    } if try(resource_group_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
  }

  resource_groups = { for config in local.__resource_groups_processed_configs : config.resource_id => config }
}

resource "azurerm_resource_group" "this" {
  for_each = local.resource_groups

  location = each.value.region
  name     = each.value.name
  tags     = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE RESOURCE GROUPS -> IAM ROLE ASSIGNMENTS
#----------------------------------------------
# Schema Path: platform.management.resource_groups.<resource_group_ref_key>.iam.role_assignments
# Schema Example:
# ---
# platform:
#   management:
#     resource_groups:
#       <resource_group_ref_key>:
#         iam:
#           role_assignments:
#             - user_group_ref_key:
#               role_definition_name:
#               principal_id:         # conflicts with user_group_ref_key
#               role_definition_id:   # conflicts with role_definition_name
#----------------------------------------------------------------------------------------------------------------------
locals {
  __resource_groups_iam_role_assignments_processed_configs = flatten(
    [
      for resource_group_ref_key, resource_group_config in local.resource_groups :
      [
        for assignment in try(resource_group_config.iam.role_assignments, {}) :
        [
          {
            # Generate a unique resource_id.
            # We won't need to refer to this resource_id anywhere else in the code.
            # That's why we are turning it into MD5 hash to guarantee its uniqueness
            # and character length.
            resource_id = md5(
              join("",
                [
                  resource_group_config.resource_id,
                  try(assignment.user_group_ref_key, ""),
                  try(assignment.principal_id, ""),
                  try(assignment.role_definition_name, ""),
                  try(assignment.role_definition_id, "")
                ]
              )
            )
            resource_group_id    = resource_group_config.resource_id
            user_group_ref_key   = try(assignment.user_group_ref_key, null)
            principal_id         = try(assignment.principal_id, null)
            role_definition_name = try(assignment.role_definition_name, null)
            role_definition_id   = try(assignment.role_definition_id, null)
          }
        ]
      ]
    ]
  )

  resource_groups_iam_role_assignments = {
    for config in local.__resource_groups_iam_role_assignments_processed_configs : config.resource_id => config
  }
}

resource "azurerm_role_assignment" "resource_group" {
  for_each = local.resource_groups_iam_role_assignments

  scope = azurerm_resource_group.this[each.value.resource_group_id].id

  # We evaluate the principal_id in the following order:
  principal_id = try(
    # 1. Check if the role assignment is about a user_group we have created.
    azuread_group.this[each.value.user_group_ref_key].object_id,
    # 2. Check if the role assignment is about a principal id that is external to our deployment.
    each.value.principal_id
    # 3. If no matches, error out.
  )
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}
