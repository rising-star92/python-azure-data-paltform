#----------------------------------------------------------------------------------------------------------------------
# AZURE NAT GATEWAYS
#-------------------
# Schema Path: platform.network.virtual_networks.<network>.nat_gateway
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         nat_gateway:
#           enabled:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __nat_gateways_processed_config = flatten(
    [
      for vnet_config in local.virtual_networks : [
        {
          resource_id = vnet_config.resource_id

          name = (
            lower("${local.prefix}-${local.region.short_name}-${local.env}-ngw-${vnet_config.nat_gateway.display_name}")
          )
          resource_group_name = vnet_config.resource_group_name
          sku_name            = try(vnet_config.nat_gateway.sku_name, "Standard")
          tags                = merge(local.tags, try(vnet_config.nat_gateway.tags, {}))
          region              = local.region.long_name

          public_ip_address_name = (
            lower("${local.prefix}-${local.region.short_name}-${local.env}-pip-ngw-${vnet_config.nat_gateway.display_name}")
          )
          public_ip_address_allocation_method = "Static"
          public_ip_address_sku_name          = "Standard"
          public_ip_address_ip_version        = "IPv4"
        }
      ] if try(vnet_config.nat_gateway.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
    ]
  )

  nat_gateways = { for config in local.__nat_gateways_processed_config : config.resource_id => config }
}

resource "azurerm_nat_gateway" "this" {
  for_each = local.nat_gateways

  name                = each.value.name
  location            = each.value.region
  resource_group_name = each.value.resource_group_name
  sku_name            = each.value.sku_name
  tags                = each.value.tags
}

resource "azurerm_public_ip" "nat_gateway" {
  for_each = local.nat_gateways

  name                = each.value.public_ip_address_name
  resource_group_name = each.value.resource_group_name
  allocation_method   = each.value.public_ip_address_allocation_method
  sku                 = each.value.public_ip_address_sku_name
  ip_version          = each.value.public_ip_address_ip_version
  location            = each.value.region
  tags                = each.value.tags
}

resource "azurerm_nat_gateway_public_ip_association" "this" {
  for_each = local.nat_gateways

  nat_gateway_id       = azurerm_nat_gateway.this[each.key].id
  public_ip_address_id = azurerm_public_ip.nat_gateway[each.key].id
}