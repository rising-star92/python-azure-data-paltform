#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2 -> NETWORK -> PRIVATE ENDPOINTS
#---------------------------------------------------
# Schema Path: platform.storage.data_lakes.<data_lake_ref_key>.private_endpoints
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         network:
#           private_endpoints:
#             <private_endpoint_ref_key>:
#               enabled:
#               resource_group_ref_key:
#               vnet_ref_key:
#               subnet_ref_key:
#               dns_zone_group_name:
#               private_dns_zone_ref_key:
#               subresource_names:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __data_lake_private_endpoints_processed_config = flatten(
    [
      for data_lake_config in local.data_lakes :
      [
        for private_endpoint_ref_key, private_endpoint_config in try(data_lake_config.network.private_endpoints, {}) :
        [
          {
            data_lake_resource_id = data_lake_config.resource_id
            data_lake_name        = data_lake_config.name

            resource_id = join("_", [data_lake_config.resource_id, private_endpoint_ref_key])
            name        = join("_", [data_lake_config.name, private_endpoint_ref_key])

            region               = data_lake_config.region
            resource_group_name  = local.resource_groups[private_endpoint_config.resource_group_ref_key].name
            subresource_names    = private_endpoint_config.subresource_names
            dns_zone_group_name  = private_endpoint_config.dns_zone_group_name
            is_manual_connection = try(private_endpoint_config.is_manual_connection, false)

            private_dns_zone_ids = [
              local.dns.private_zones[private_endpoint_config.private_dns_zone_ref_key].id
            ]

            subnet_id = (
              local.virtual_networks[private_endpoint_config.vnet_ref_key].subnets[private_endpoint_config.subnet_ref_key].id
            )

            tags = merge(local.tags, try(private_endpoint_config.tags, {}))
          }
        ] if try(private_endpoint_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]
    ]
  )

  data_lake_private_endpoints = {
    for config in local.__data_lake_private_endpoints_processed_config : config.resource_id => config
  }
}

resource "azurerm_private_endpoint" "this" {
  for_each = local.data_lake_private_endpoints

  name                = each.value.name
  location            = each.value.region
  resource_group_name = each.value.resource_group_name
  subnet_id           = each.value.subnet_id
  tags                = each.value.tags

  private_dns_zone_group {
    name                 = each.value.dns_zone_group_name
    private_dns_zone_ids = each.value.private_dns_zone_ids
  }

  private_service_connection {
    name                           = each.value.data_lake_name
    is_manual_connection           = each.value.is_manual_connection
    private_connection_resource_id = azurerm_storage_account.data_lake[each.value.data_lake_resource_id].id
    subresource_names              = each.value.subresource_names
  }
}
