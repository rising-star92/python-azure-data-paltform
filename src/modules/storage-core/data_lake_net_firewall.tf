#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2 -> NETWORK -> FIREWALL
#---------------------------------------------------
# Schema Path: platform.storage.data_lakes.<data_lake_ref_key>.private_endpoints
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         network:
#           firewall:
#             enabled:
#             default_action:
#             bypass:
#             ip_rules:
#             virtual_network_subnet_ids: []
#             virtual_network_subnet_ref_objects:
#               - vnet_ref_key:
#                 subnet_ref_key:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __data_lake_firewalls_processed_config = flatten(
    [
      for data_lake_config in local.data_lakes :
      [
        {
          data_lake_resource_id = data_lake_config.resource_id

          resource_id         = data_lake_config.ref_key
          resource_group_name = data_lake_config.resource_group_name

          default_action = data_lake_config.network.firewall.default_action
          ip_rules       = try(data_lake_config.network.firewall.ip_rules, [])
          bypass         = try(data_lake_config.network.firewall.bypass, [])

          virtual_network_subnet_ids = flatten(
            [
              try(data_lake_config.network.firewall.virtual_network_subnet_ids, []),
              try(
                [
                  for obj in data_lake_config.network.firewall.virtual_network_subnet_ref_objects :
                  local.virtual_networks[obj.vnet_ref_key].subnets[obj.subnet_ref_key].id
                ]
                ,
                []
              )
            ]
          )
        }
      ] if try(data_lake_config.network.firewall.enabled, true)
    ]
  )

  data_lake_firewalls = { for config in local.__data_lake_firewalls_processed_config : config.resource_id => config }
}
resource "azurerm_storage_account_network_rules" "data_lake" {
  for_each = local.data_lake_firewalls

  resource_group_name  = each.value.resource_group_name
  storage_account_name = azurerm_storage_account.data_lake[each.value.data_lake_resource_id].name

  default_action             = each.value.default_action
  ip_rules                   = each.value.ip_rules
  virtual_network_subnet_ids = each.value.virtual_network_subnet_ids
  bypass                     = each.value.bypass
}