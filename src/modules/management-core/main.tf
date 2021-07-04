#----------------------------------------------------------------------------------------------------------------------
# SHORTCUTS
#
# Using fully qualified naming can result in very long lines of code.
# In this section, we assign specific resources, especially dependencies, to much shorter local variable names.
#----------------------------------------------------------------------------------------------------------------------
locals {
  config       = jsondecode(var.config)
  dependencies = jsondecode(var.dependencies)
  env          = local.config.env
  prefix       = local.config.platform.general.prefix
  region       = local.config.platform.general.region
  tags         = local.config.platform.general.tags
}


#----------------------------------------------------------------------------------------------------------------------
# AZURE AD GROUPS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing virtual network configuration.
  azuread_groups_config = try(local.config.platform.management.user_groups, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azuread_groups = {
    for user_group_ref_key, user_group_config in local.azuread_groups_config :
    user_group_ref_key => {
      user_group_ref_key = user_group_ref_key

      name                    = "${upper(local.prefix)}-${title(local.env)}-${title(user_group_config.display_name)}"
      description             = try(user_group_config.description, "")
      prevent_duplicate_names = try(user_group_config.prevent_duplicate_names, true)
    }
  }
}

resource "azuread_group" "this" {
  for_each = local.azuread_groups

  display_name            = each.value.name
  description             = each.value.description
  prevent_duplicate_names = each.value.prevent_duplicate_names
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE RESOURCE GROUPS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing virtual network configuration.
  azure_resource_groups_config = try(local.config.platform.management.resource_groups, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azure_resource_groups = {
    for resource_group_ref_key, resource_group_config in local.azure_resource_groups_config :
    resource_group_ref_key => {
      resource_group_ref_key = resource_group_ref_key

      name   = lower("${local.prefix}-${local.region.short_name}-${local.env}-${resource_group_config.display_name}")
      tags   = merge(local.tags, try(resource_group_config.tags, {}))
      region = local.region.long_name
    }
  }
}

resource "azurerm_resource_group" "this" {
  for_each = local.azure_resource_groups

  location = each.value.region
  name     = each.value.name
  tags     = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE RESOURCE GROUPS -> IAM ROLE ASSIGNMENTS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Create a list with all role assignments for every resource group.
  # Example:
  # [
  #   {
  #     resource_group_ref_key     = "infra"
  #     resource_group_display_name = "Infrastructure"
  #     role_definition_name                   = "Owner"
  #     user_group_ref_key         = "engineers"
  #   }
  # ]
  azure_resource_groups_iam_role_assignments = flatten(
    [
      for resource_group_ref_key, resource_group_config in local.azure_resource_groups_config : [
        for role_assignment in try(resource_group_config.iam.role_assignments, {}) : [
          {
            resource_group_ref_key      = resource_group_ref_key
            resource_group_display_name = resource_group_config.display_name
            role_definition_name        = try(role_assignment.role_definition_name, null)
            role_definition_id          = try(role_assignment.role_definition_id, null)
            user_group_ref_key          = try(role_assignment.user_group_ref_key, "")
          }
        ]
      ]
    ]
  )

  # We use the list from above (azure_resource_groups_iam_role_assignments) to create a hashed map. Each map key is 
  # an MD5 hash and each key-value is an element from the list above. This way we can guarantee uniqueness for our
  # map keys.
  # Example:
  # {
  #   8d0ac51ba41f4c42f78217e595850394 = { resource_group_ref_key = "...", resource_group_display_name = "...", ... }
  #   2f2daec5d6be0646fdadb67909b95841 = { resource_group_ref_key = "...", resource_group_display_name = "...", ... }
  #   f24ebbc47df5382a129d5b54a9b17499 = { resource_group_ref_key = "...", resource_group_display_name = "...", ... }
  # }
  azure_resource_groups_iam_role_assignments_hashed_map = {
    for assignment in local.azure_resource_groups_iam_role_assignments : md5(
      join("",
        [
          assignment.resource_group_ref_key,
          assignment.resource_group_display_name,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_ref_key
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_resource_group" {
  for_each = local.azure_resource_groups_iam_role_assignments_hashed_map

  scope                = azurerm_resource_group.this[each.value.resource_group_ref_key].id
  principal_id         = azuread_group.this[each.value.user_group_ref_key].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}
