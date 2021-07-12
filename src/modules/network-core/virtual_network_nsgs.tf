#----------------------------------------------------------------------------------------------------------------------
# AZURE NETWORK SECURITY GROUPS
#------------------------------
# Schema Path: platform.network.virtual_networks.<network>.network_security_groups
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         network_security_groups:
#           <network_security_group_ref_key>:
#             enabled:
#             display_name:
#             tags:
#             rules:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __network_security_groups_processed_config = flatten(
    [
      for vnet_config in local.virtual_networks : [
        for nsg_ref_key, nsg_config in try(vnet_config.network_security_groups, {}) : [
          {
            vnet_resource_id = vnet_config.resource_id

            # The resource_id is the uniquely id that will be assigned to each Terraform resource.
            # Example: azurerm_subnet.this[resource_id]
            resource_id = join("_", [vnet_config.resource_id, nsg_ref_key])

            # The ref_key provides a mechanism to define resource relationships in the YAML files.
            # All module outputs are using the ref_key as resource identifier when exporting values.
            ref_key = nsg_ref_key

            name = lower(
              "${local.prefix}-${local.region.short_name}-${local.env}-nsg-${nsg_config.display_name}"
            )
            region              = local.region.long_name
            resource_group_name = vnet_config.resource_group_name
            tags                = merge(local.tags, try(nsg_config.tags, {}))

            rules = try(nsg_config.rules, {})
          }
        ] if try(nsg_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]
    ]
  )

  network_security_groups = { for config in local.__network_security_groups_processed_config : config.resource_id => config }
}

resource "azurerm_network_security_group" "this" {
  for_each = local.network_security_groups

  name                = each.value.name
  location            = each.value.region
  resource_group_name = each.value.resource_group_name
  tags                = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NETWORK SECURITY GROUPS -> RULES
#---------------------------------------
# Schema Path: platform.network.virtual_networks.<network>.network_security_groups.<group>.rules
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         network_security_groups:
#           <network_security_group_ref_key>:
#             rules:
#               <rules_ref_key>:
#                 enabled:
#                 display_name:
#                 description:
#                 priority:
#                 direction:
#                 access:
#                 protocol:
#                 source_port_range:
#                 source_port_ranges:
#                 source_address_prefix:
#                 source_address_prefixes:
#                 destination_port_range:
#                 destination_port_ranges:
#                 destination_address_prefix:
#                 destination_address_prefixes:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __network_security_rules_processed_config = flatten(
    [
      for nsg_config in local.network_security_groups : [

        for rule_ref_key, rule_config in nsg_config.rules :
        {
          network_security_group_resource_id = nsg_config.resource_id

          resource_id = md5(join("", [nsg_config.resource_id, rule_ref_key]))
          ref_key     = rule_ref_key

          name                         = rule_config.display_name
          description                  = try(rule_config.description, null)
          priority                     = rule_config.priority
          direction                    = rule_config.direction
          access                       = rule_config.access
          protocol                     = rule_config.protocol
          source_port_range            = try(rule_config.source_port_range, null)
          source_port_ranges           = try(rule_config.source_port_ranges, null)
          source_address_prefix        = try(rule_config.source_address_prefix, null)
          source_address_prefixes      = try(rule_config.source_address_prefixes, null)
          destination_port_range       = try(rule_config.destination_port_range, null)
          destination_port_ranges      = try(rule_config.destination_port_ranges, null)
          destination_address_prefix   = try(rule_config.destination_address_prefix, null)
          destination_address_prefixes = try(rule_config.destination_address_prefixes, null)

        } if try(rule_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]
    ]
  )

  network_security_rules = { for config in local.__network_security_rules_processed_config : config.resource_id => config }
}



resource "azurerm_network_security_rule" "this" {
  for_each = local.network_security_rules

  name                         = each.value.name
  description                  = each.value.description
  priority                     = each.value.priority
  direction                    = each.value.direction
  access                       = each.value.access
  protocol                     = each.value.protocol
  source_port_range            = each.value.source_port_range
  source_port_ranges           = each.value.source_port_ranges
  source_address_prefix        = each.value.source_address_prefix
  source_address_prefixes      = each.value.source_address_prefixes
  destination_port_range       = each.value.destination_port_range
  destination_port_ranges      = each.value.destination_port_ranges
  destination_address_prefix   = each.value.destination_address_prefix
  destination_address_prefixes = each.value.destination_address_prefixes
  resource_group_name = (
    azurerm_network_security_group.this[each.value.network_security_group_resource_id].resource_group_name
  )
  network_security_group_name = (
    azurerm_network_security_group.this[each.value.network_security_group_resource_id].name
  )
}
