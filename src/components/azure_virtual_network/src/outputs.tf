########################################################################################################################
# OUTPUTS
########################################################################################################################
output "virtual_networks" {
  value = try(
    {
      for network_id, network_config in module.azure_virtual_network :
      network_id => {
        name          = network_config.vnet_name
        id            = network_config.vnet_id
        address_space = network_config.vnet_address_space
        subnets = {
          for subnet_id, subnet_config in network_config.subnet :
          subnet_id => {
            name             = subnet_config.name
            id               = subnet_config.id
            address_prefix   = subnet_config.address_prefix
            address_prefixes = subnet_config.address_prefixes
          }
        }
        route_tables = {
          for route_table_id, route_table_config in network_config.route_table :
          route_table_id => {
            name = route_table_config.name
            id   = route_table_config.id
          }
        }
      }
    },
    {}
  )
}
