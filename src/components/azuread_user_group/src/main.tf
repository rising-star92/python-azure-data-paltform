########################################################################################################################
# LOCAL VALUES
########################################################################################################################
locals {
  component_config = jsondecode(var.component_config)
  dependencies     = jsondecode(var.dependencies)

  env             = var.env
  resource_prefix = var.resource_prefix
  region          = var.region
  tags            = jsondecode(var.tags)
}

########################################################################################################################
# MAIN
########################################################################################################################
locals {
  azuread_groups = {
    for group_id, group_config in try(local.component_config, {}) :
    group_id => {
      name                    = "${upper(local.resource_prefix)}-${title(local.env)}-${title(group_config.display_name)}"
      description             = try(group_config.description, "This group provides access to specific resources in the ${lower(local.env)} environment.")
      prevent_duplicate_names = try(group_config.prevent_duplicate_names, true)
    } if !contains(try(group_config.attributes.excluded_from_env, []), local.env)
  }
}

resource "azuread_group" "this" {
  for_each                = local.azuread_groups
  display_name            = each.value.name
  description             = each.value.description
  prevent_duplicate_names = each.value.prevent_duplicate_names
}

