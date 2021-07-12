#######################################################################################################################
# !!! IMPORTANT !!!
#
# The structure of the outputs is highly dependent on by other modules. Making changes on the structure will result in
# failures and potentially catastrophic side effects. (e.g. destruction of data resources)
# 
# The outputs are considered contracts and should be treated with caution.
#
# If you need to make changes of the output structure, consider the following:
# - Leave any existing attributes in place. If you need to expose the same data in a different way, 
#   just create a new (alias) attribute. This will guarantee backward compatibility.
# - Make sure to test your changes by running a full platform deployment.
# - Make sure to run terraform plan on the customer environments before applying the changes.
#######################################################################################################################

#----------------------------------------------------------------------------------------------------------------------
# OUTPUTS
#----------------------------------------------------------------------------------------------------------------------
output "virtual_networks" {
  value = {
    for vnet_config in local.virtual_networks :
    vnet_config.ref_key => {
      # Virtual Network
      id   = azurerm_virtual_network.this[vnet_config.resource_id].id
      name = azurerm_virtual_network.this[vnet_config.resource_id].name

      # Subnets
      subnets = {
        for subnet_config in local.subnets :
        subnet_config.ref_key => {
          id                           = azurerm_subnet.this[subnet_config.resource_id].id
          name                         = azurerm_subnet.this[subnet_config.resource_id].name
          address_prefixes             = azurerm_subnet.this[subnet_config.resource_id].address_prefixes
          is_nat_gateway_enabled       = local.subnets[subnet_config.resource_id].is_nat_gateway_enabled
          is_associated_to_nat_gateway = local.subnets[subnet_config.resource_id].is_associated_to_nat_gateway
        }
      }

      # Route Tables
      route_tables = {
        for route_table_config in local.route_tables :
        route_table_config.ref_key => {
          id   = azurerm_route_table.this[route_table_config.resource_id].id
          name = azurerm_route_table.this[route_table_config.resource_id].name
        }
      }

      # Network Security Groups
      network_security_groups = {
        for nsg_config in local.network_security_groups :
        nsg_config.ref_key => {
          id   = azurerm_network_security_group.this[nsg_config.resource_id].id
          name = azurerm_network_security_group.this[nsg_config.resource_id].name
        }
      }

      # NAT Gateway
      nat_gateway = {
        is_enabled = try(vnet_config.nat_gateway.enabled, false)
      }
    }
  }
}

output "dns" {
  value = {
    private_zones = {
      for dns_zone_config in local.private_dns_zones :
      dns_zone_config.ref_key => {
        id = azurerm_private_dns_zone.this[dns_zone_config.resource_id].id
      }
    }
  }
}