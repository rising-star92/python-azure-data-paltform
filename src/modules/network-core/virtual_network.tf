#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS
#----------------------
# Schema Path: platform.network.virtual_networks
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         enabled:
#         display_name:
#         resource_group_ref_key:
#         address_space:
#         subnet_range_size:
#         dns_servers:
#         bgp_community:
#         tag:
#         iam:
#         subnets:
#         route_tables:
#         network_security_groups:
#         nat_gateway:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __virtual_networks_raw_config = try(local.config.platform.network.virtual_networks, {})

  __virtual_networks_processed_config = {
    for vnet_ref_key, vnet_config in local.__virtual_networks_raw_config :
    vnet_ref_key => {
      resource_id = vnet_ref_key
      ref_key     = vnet_ref_key

      name = (
        lower("${local.prefix}-${local.region.short_name}-${local.env}-vnet-${vnet_config.display_name}")
      )

      region              = local.region.long_name
      resource_group_name = local.resource_groups[vnet_config.resource_group_ref_key].name
      address_space       = [vnet_config.address_space]
      subnet_range_size   = try(vnet_config.subnet_range_size, 6)
      dns_servers         = try(vnet_config.dns_servers, null)
      bgp_community       = try(vnet_config.bgp_community, null)
      tags                = merge(local.tags, try(vnet_config.tags, {}))

      iam                     = try(vnet_config.iam, {})
      subnets                 = try(vnet_config.subnets, {})
      route_tables            = try(vnet_config.route_tables, {})
      network_security_groups = try(vnet_config.network_security_groups, {})
      nat_gateway             = try(vnet_config.nat_gateway, {})

    } if try(vnet_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
  }

  virtual_networks = { for config in local.__virtual_networks_processed_config : config.resource_id => config }

}

resource "azurerm_virtual_network" "this" {
  for_each = local.virtual_networks

  name                = each.value.name
  location            = each.value.region
  resource_group_name = each.value.resource_group_name
  address_space       = each.value.address_space
  dns_servers         = each.value.dns_servers
  bgp_community       = each.value.bgp_community
  tags                = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> IAM ROLE ASSIGNMENTS
#-----------------------------------------------
# Schema Path: platform.network.virtual_networks.<network>.iam.role_assignments
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         iam:
#           role_assignments:
#             - user_group_ref_key:
#               role_definition_name:
#               principal_id:         # conflicts with user_group_ref_key
#               role_definition_id:   # conflicts with role_definition_name
#----------------------------------------------------------------------------------------------------------------------
locals {
  __virtual_networks_iam_role_assignments_processed_configs = flatten(
    [
      for vnet_config in local.virtual_networks :
      [
        for assignment in try(vnet_config.iam.role_assignments, []) :
        [
          {
            # Generate a unique resource_id.
            # We won't need to refer to this resource_id anywhere else in the code.
            # That's why we are turning it into MD5 hash to guarantee its uniqueness
            # and character length.
            resource_id = md5(
              join("",
                [
                  vnet_config.resource_id,
                  try(assignment.user_group_ref_key, ""),
                  try(assignment.role_definition_name, ""),
                  try(assignment.role_definition_id, "")
                ]
              )
            )

            vnet_resource_id       = vnet_config.resource_id
            user_group_resource_id = try(assignment.user_group_ref_key, null)
            principal_id           = try(assignment.principal_id, null)
            role_definition_name   = try(assignment.role_definition_name, null)
            role_definition_id     = try(assignment.role_definition_id, null)
          }
        ]
      ]
    ]
  )

  virtual_networks_iam_role_assignments = {
    for config in local.__virtual_networks_iam_role_assignments_processed_configs : config.resource_id => config
  }
}

resource "azurerm_role_assignment" "azure_virtual_network" {
  for_each = local.virtual_networks_iam_role_assignments

  scope = azurerm_virtual_network.this[each.value.vnet_resource_id].id

  # We evaluate the principal_id in the following order:
  principal_id = try(
    # 1. Check if the role assignment is about a user_group we have created.
    local.user_groups[each.value.user_group_resource_id].object_id,
    # 2. Check if the role assignment is about a principal id that is external to our deployment.
    each.value.principal_id
    # 3. If no matches, error out.
  )

  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}
