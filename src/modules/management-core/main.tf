#----------------------------------------------------------------------------------------------------------------------
# LOCAL VALUES
#----------------------------------------------------------------------------------------------------------------------
locals {
  config       = jsondecode(var.config)
  dependencies = jsondecode(var.dependencies)
  env          = local.config.env
  prefix       = local.config.general.prefix
  region       = local.config.general.region
  tags         = local.config.general.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE AD GROUPS
#----------------------------------------------------------------------------------------------------------------------
locals {
  azuread_groups_config = try(local.config.platform.management.user_groups, {})

  azuread_groups = {
    for id, config in local.azuread_groups_config :
    id => {
      name                    = "${upper(local.prefix)}-${title(local.env)}-${title(config.display_name)}"
      description             = try(config.description, "")
      prevent_duplicate_names = try(config.prevent_duplicate_names, true)
    }
  }
}

resource "azuread_group" "this" {
  for_each                = local.azuread_groups
  display_name            = each.value.name
  description             = each.value.description
  prevent_duplicate_names = each.value.prevent_duplicate_names
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE RESOURCE GROUPS
#----------------------------------------------------------------------------------------------------------------------
locals {
  azure_resource_groups_config = try(local.config.platform.management.resource_groups, {})
}

# Resource Groups
locals {
  azure_resource_groups = {
    for id, config in local.azure_resource_groups_config :
    id => {
      name   = lower("${local.prefix}-${local.env}-${config.display_name}")
      tags   = merge(local.tags, try(config.tags, {}))
      region = local.region
    }
  }
}

resource "azurerm_resource_group" "this" {
  for_each = local.azure_resource_groups
  location = each.value.region
  name     = each.value.name
  tags     = each.value.tags
}

# Resource Groups -> IAM Role Assignments
locals {
  # Create a list with all role assignments for every resource group.
  # Example:
  # [
  #   {
  #     resource_group_key_name     = "infra"
  #     resource_group_display_name = "Infrastructure"
  #     role_definition_name                   = "Owner"
  #     user_group_key_name         = "engineers"
  #   }
  # ]
  azure_resource_groups_iam_role_assignments = flatten(
    [
      for id, config in local.azure_resource_groups_config : [
        for role_assignment in try(config.iam.role_assignments, {}) : [
          {
            resource_group_key_name     = id
            resource_group_display_name = config.display_name
            role_definition_name        = try(role_assignment.role_definition_name, null)
            role_definition_id          = try(role_assignment.role_definition_id, null)
            user_group_key_name         = try(role_assignment.user_group_key_name, "")
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
  #   8d0ac51ba41f4c42f78217e595850394 = { resource_group_key_name = "...", resource_group_display_name = "...", ... }
  #   2f2daec5d6be0646fdadb67909b95841 = { resource_group_key_name = "...", resource_group_display_name = "...", ... }
  #   f24ebbc47df5382a129d5b54a9b17499 = { resource_group_key_name = "...", resource_group_display_name = "...", ... }
  # }
  azure_resource_groups_iam_role_assignments_hashed_map = {
    for assignment in local.azure_resource_groups_iam_role_assignments : md5(
      join("",
        [
          assignment.resource_group_key_name,
          assignment.resource_group_display_name,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_key_name
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_resource_group" {
  for_each             = local.azure_resource_groups_iam_role_assignments_hashed_map
  scope                = azurerm_resource_group.this[each.value.resource_group_key_name].id
  principal_id         = azuread_group.this[each.value.user_group_key_name].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}