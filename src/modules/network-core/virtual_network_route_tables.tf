#----------------------------------------------------------------------------------------------------------------------
# AZURE ROUTE TABLES
#-------------------
# Schema Path: platform.network.virtual_networks.<network>.route_tables
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         route_tables:
#           <route_table_ref_key>:
#             enabled:
#             display_name:
#             disable_bgp_route_propagation:
#             tags:
#             routes:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __route_tables_processed_config = flatten(
    [
      for vnet_config in local.virtual_networks : [
        for route_table_ref_key, route_table_config in vnet_config.route_tables : [
          {
            resource_id = join("_", [vnet_config.resource_id, route_table_ref_key])
            ref_key     = route_table_ref_key

            name = lower("${local.prefix}-${local.region.short_name}-${local.env}-rt-${route_table_config.display_name}")

            region                        = vnet_config.region
            resource_group_name           = vnet_config.resource_group_name
            disable_bgp_route_propagation = try(route_table_config.disable_bgp_route_propagation, false)
            tags                          = merge(local.tags, try(route_table_config.tags, {}))

            # Pass-through objects
            # These objects are not processed here. 
            # They are only defined for the respective resources to process.
            routes = try(route_table_config.routes, {})
          }
        ] if try(route_table_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]
    ]
  )

  route_tables = { for config in local.__route_tables_processed_config : config.resource_id => config }
}

resource "azurerm_route_table" "this" {
  for_each = local.route_tables

  name                          = each.value.name
  location                      = each.value.region
  resource_group_name           = each.value.resource_group_name
  disable_bgp_route_propagation = each.value.disable_bgp_route_propagation
  tags                          = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE ROUTE TABLES -> ROUTES
#-----------------------------
# Schema Path: platform.network.virtual_networks.<network>.route_tables.<route_table>.routes
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         route_tables:
#           <route_table_ref_key>:
#             routes:
#               <route_ref_key>:
#                 enabled:
#                 display_name:
#                 address_prefix:
#                 next_hop_type:
#                 next_hop_in_ip_address:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __routes_processed_config = flatten(
    [
      for route_table_resource_id, route_table_config in local.route_tables : [
        for route_ref_key, route_config in try(route_table_config.routes, {}) : [
          {
            route_table_resource_id = route_table_resource_id

            # The resource_id is the uniquely id that will be assigned to each Terraform resource.
            # Example: azurerm_subnet.this[resource_id]
            resource_id = md5(join("", [route_table_resource_id, route_ref_key]))

            # The ref_key provides a mechanism to define resource relationships in the YAML files.
            # All module outputs are using the ref_key as resource identifier when exporting values.
            ref_key = route_ref_key

            name                   = route_config.display_name
            address_prefix         = route_config.address_prefix
            next_hop_type          = route_config.next_hop_type
            next_hop_in_ip_address = try(route_config.next_hop_in_ip_address, null)
          }
        ] if try(route_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]
    ]
  )


  routes = { for config in local.__routes_processed_config : config.resource_id => config }
}

resource "azurerm_route" "this" {
  for_each = local.routes

  name                   = each.value.name
  resource_group_name    = azurerm_route_table.this[each.value.route_table_resource_id].resource_group_name
  route_table_name       = azurerm_route_table.this[each.value.route_table_resource_id].name
  address_prefix         = each.value.address_prefix
  next_hop_type          = each.value.next_hop_type
  next_hop_in_ip_address = each.value.next_hop_in_ip_address
}
