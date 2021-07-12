#----------------------------------------------------------------------------------------------------------------------
# DNS - PRIVATE ZONES
#----------------------
# Schema Path: platform.network.dns.private_zones
# Schema Example:
# ---
# platform:
#   network:
#     dns:
#       private_zones:
#         <private_dns_zone_ref_key>:
#           enabled:
#           name:
#           resource_group_ref_key:
#           tags:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __private_dns_zones_raw_config = try(local.config.platform.network.dns.private_zones, {})

  __private_dns_zones_processed_config = {
    for dns_zone_ref_key, dns_zone_config in local.__private_dns_zones_raw_config :
    dns_zone_ref_key => {
      resource_id = dns_zone_ref_key
      ref_key     = dns_zone_ref_key

      name                = dns_zone_config.name
      resource_group_name = local.resource_groups[dns_zone_config.resource_group_ref_key].name
      tags                = merge(local.tags, try(dns_zone_config.tags, {}))
    } if try(dns_zone_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
  }

  private_dns_zones = { for config in local.__private_dns_zones_processed_config : config.resource_id => config }

}
resource "azurerm_private_dns_zone" "this" {
  for_each = local.private_dns_zones

  name                = each.value.name
  resource_group_name = each.value.resource_group_name
  tags                = each.value.tags
}