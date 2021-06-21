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
  azure_network_security_groups = {
    for group_id, group_config in try(local.component_config, {}) :
    group_id => {
      name                = lower("${local.resource_prefix}-${local.env}-${group_config.display_name}")
      resource_group_name = local.dependencies.azure_resource_group[group_config.resource_group_key_name].name
      region              = local.region
      tags                = merge(local.tags, try(group_config.tags, {}))
    }
  }
}

resource "azurerm_network_security_group" "this" {
  for_each = local.azure_network_security_groups

  name                = each.value.name
  tags                = each.value.tags
  resource_group_name = each.value.resource_group_name
  location            = each.value.region
}
