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
  # If the current environment is excluded via "excluded_from_env" attribute, we should ignore the resource group.
  azure_resource_groups = {
    for group_id, group_config in try(local.component_config, {}) :
    group_id => {
      name   = lower("${local.resource_prefix}-${local.env}-${group_config.display_name}")
      tags   = merge(local.tags, try(group_config.tags, {}))
      region = local.region
    } if !contains(try(group_config.attributes.excluded_from_env, []), local.env)
  }
}

resource "azurerm_resource_group" "this" {
  for_each = local.azure_resource_groups
  location = each.value.region
  name     = each.value.name
  tags     = each.value.tags
}


