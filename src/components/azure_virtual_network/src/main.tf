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
  azure_virtual_networks = {
    for network_id, network_config in try(local.component_config, {}) :
    network_id => {
      name                = lower("${local.resource_prefix}-${local.env}-${network_config.display_name}")
      tags                = merge(local.tags, try(network_config.tags, {}))
      region              = local.region
      resource_group_name = local.dependencies.azure_resource_group[network_config.resource_group_key_name].name
      address_space       = [network_config.address_space]
      route_tables = {
        for route_table_id, route_table_config in network_config.route_tables :
        route_table_id => {
          name = lower("${local.resource_prefix}-${local.env}-${network_config.display_name}-${route_table_config.display_name}")
        }
      }
      subnets = {
        for subnet_id, subnet_config in network_config.subnets :
        subnet_id => {
          name                      = lower("${local.resource_prefix}-${local.env}-${network_config.display_name}-${subnet_config.display_name}")
          address_prefixes          = [subnet_config.address_prefix]
          route_table_id            = subnet_config.route_table_key_name
          network_security_group_id = local.dependencies.azure_network_security_group[subnet_config.network_security_group_key_name].id
          service_endpoints         = subnet_config.service_endpoints
          delegations = {
            for delegation_id in subnet_config.delegations : delegation_id => network_config.subnet_delegations[delegation_id]
          }
        }
      }
    }
  }
}

module "azure_virtual_network" {
  for_each = local.azure_virtual_networks

  source  = "ingenii-solutions/vnet/azurerm"
  version = "0.0.2"

  name                = each.value.name
  tags                = each.value.tags
  resource_group_name = each.value.resource_group_name
  region              = each.value.region

  address_space = each.value.address_space
  route_tables  = each.value.route_tables
  subnets       = each.value.subnets
}
