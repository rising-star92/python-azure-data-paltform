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
# AZURE VNET
#----------------------------------------------------------------------------------------------------------------------
locals {
  azure_virtual_networks_config = try(local.config.platform.network.virtual_networks, {})

  azure_virtual_networks = {
    for id, config in local.azure_virtual_networks_config :
    id => {
      name                = lower("${local.prefix}-${local.env}-${config.display_name}")
      tags                = merge(local.tags, try(config.tags, {}))
      region              = local.region
      resource_group_name = local.dependencies.resource_groups[config.resource_group_key_name].name
      address_space       = [config.address_space]
      dns_servers         = try(config.dns_servers, [])
    }
  }
}

resource "azurerm_virtual_network" "this" {
  for_each = local.azure_virtual_networks

  name                = each.value.name
  location            = each.value.region
  resource_group_name = each.value.resource_group_name
  address_space       = each.value.address_space
  dns_servers         = each.value.dns_servers
  tags                = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE ROUTE TABLES
#----------------------------------------------------------------------------------------------------------------------
locals {
  azure_route_tables_config = try(local.config.platform.network.route_tables, {})

  azure_route_tables = {
    for id, config in local.azure_route_tables_config :
    id => {
      name                          = lower("${local.prefix}-${local.env}-${config.display_name}")
      region                        = local.region
      resource_group_name           = local.dependencies.resource_groups[config.resource_group_key_name].name
      disable_bgp_route_propagation = try(config.disable_bgp_route_propagation, false)
      tags                          = merge(local.tags, try(config.tags, {}))
    }
  }
}

resource "azurerm_route_table" "this" {
  for_each = local.azure_route_tables

  name                          = each.value.name
  location                      = each.value.region
  resource_group_name           = each.value.resource_group_name
  disable_bgp_route_propagation = each.value.disable_bgp_route_propagation
  tags                          = each.value.tags
}

# #----------------------------------------------------------------------------------------------------------------------
# # AZURE ROUTES
# #----------------------------------------------------------------------------------------------------------------------
# locals {
#   azure_routes = flatten(
#     [
#       for id, config in local.azure_route_tables_config: [
#         for route_id, route_config in try(config.routes, {}): [
#           {
#             route_table_key_name = id
#           }
#         ]
#       ]
#     ]
#   )
#     routes = {
#       for id, config in try(config.routes, {}) :
#       id => {
#         name                   = config.display_name
#         address_prefix         = config.address_prefix
#         next_hop_type          = config.next_hop_type
#         next_hop_in_ip_address = try(config.next_hop_in_ip_address, null)
#       }
#     }
#   }
# }

# resource "azurerm_route" "example" {
#   name                = "acceptanceTestRoute1"
#   resource_group_name = azurerm_resource_group.example.name
#   route_table_name    = azurerm_route_table.example.name
#   address_prefix      = "10.1.0.0/16"
#   next_hop_type       = "vnetlocal"
# }