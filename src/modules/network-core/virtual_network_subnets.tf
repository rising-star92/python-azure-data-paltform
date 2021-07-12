#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS
#----------------------------------
# Schema Path: platform.network.virtual_networks.<network>.subnets
# Schema Example:
# ---
# platform:
#   network:
#     virtual_networks:
#       <virtual_network_ref_key>:
#         subnets:
#           <subnet_ref_key>:
#             enabled:
#             display_name:
#             type:
#             route_table_ref_key:
#             network_security_group_ref_key:
#             subnet_range_size:
#             subnet_network_id:
#             is_associated_to_nat_gateway:
#             enforce_private_link_endpoint_network_policies:
#             enforce_private_link_service_network_policies:
#             tags:
#----------------------------------------------------------------------------------------------------------------------
locals {

  __subnets_processed_config = flatten(
    [
      for vnet_config in local.virtual_networks : [
        for subnet_ref_key, subnet_config in vnet_config.subnets : [
          {
            vnet_resource_id = vnet_config.resource_id

            resource_id = join("_", [vnet_config.resource_id, subnet_ref_key])
            ref_key     = subnet_ref_key

            route_table_id = try(join("_", [vnet_config.resource_id, subnet_config.route_table_ref_key]), "")
            network_security_group_id = try(
              join("_", [vnet_config.resource_id, subnet_config.network_security_group_ref_key]),
              ""
            )

            # If the subnet type is set to 'gateway-subnet', we'll create a subnet named GatewaySubnet as required by Azure.
            name = try(subnet_config.type, "") == "gateway-subnet" ? (
              "GatewaySubnet"
              ) : (
              # Example: adp-uks-dev-snet-dbw-engineering-hosts
              lower("${local.prefix}-${local.region.short_name}-${local.env}-snet-${subnet_config.display_name}")
            )

            # The address prefix is a combination of the VNET address space, the configured subnet range size and the 
            # network id for this subnet as defined in the YAML file.
            address_prefixes = [
              cidrsubnet(vnet_config.address_space[0],
                try(subnet_config.subnet_range_size, vnet_config.subnet_range_size),
                subnet_config.subnet_network_id
              )
            ]

            # This attribute is added for convenience.
            is_nat_gateway_enabled = try(vnet_config.nat_gateway.enabled, false)

            # The subnet can be associated to a NAT gateway if:
            # - is_associated_to_nat_gateway attrib is set to true, and,
            # - the NAT gateway is enabled, and,
            # - the subnet is not a Gateway subnet
            is_associated_to_nat_gateway = (
              try(subnet_config.is_associated_to_nat_gateway, true)
              ) && (
              try(vnet_config.nat_gateway.enabled, false)
              ) && (
              try(subnet_config.type, "") != "gateway-subnet"
            )

            enforce_private_link_endpoint_network_policies = try(
              subnet_config.enforce_private_link_endpoint_network_policies,
              false
            )
            enforce_private_link_service_network_policies = try(
              subnet_config.enforce_private_link_service_network_policies,
              false
            )

            delegations                 = try(subnet_config.delegations, {})
            service_endpoints           = try(subnet_config.service_endpoints, null)
            service_endpoint_policy_ids = try(subnet_config.service_endpoint_policy_ids, null)
          }
        ] if try(subnet_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]
    ]
  )

  subnets = { for config in local.__subnets_processed_config : config.resource_id => config }
}


resource "azurerm_subnet" "this" {
  for_each = local.subnets

  name = each.value.name

  resource_group_name = (
    azurerm_virtual_network.this[each.value.vnet_resource_id].resource_group_name
  )
  virtual_network_name = (
    azurerm_virtual_network.this[each.value.vnet_resource_id].name
  )
  address_prefixes                               = each.value.address_prefixes
  enforce_private_link_endpoint_network_policies = each.value.enforce_private_link_endpoint_network_policies
  enforce_private_link_service_network_policies  = each.value.enforce_private_link_service_network_policies
  service_endpoints                              = each.value.service_endpoints
  service_endpoint_policy_ids                    = each.value.service_endpoint_policy_ids

  dynamic "delegation" {
    for_each = each.value.delegations
    iterator = d
    content {
      name = d.value.display_name
      service_delegation {
        name    = d.value.service_delegation.name
        actions = try(d.value.service_delegation.actions, [])
      }
    }
  }
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS -> ROUTE TABLE ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  subnets_route_table_associations = {
    for subnet_config in local.subnets :
    # Generate a unique resource_id.
    # We won't need to refer to this resource_id anywhere else in the code.
    # That's why we are turning it into MD5 hash to guarantee its uniqueness
    # and character length.
    md5(
      join("",
        [
          subnet_config.resource_id,
          subnet_config.route_table_id
        ]
      )
      ) => {
      subnet_id      = azurerm_subnet.this[subnet_config.resource_id].id
      route_table_id = azurerm_route_table.this[subnet_config.route_table_id].id
    } if subnet_config.route_table_id != "" # Consider only subnets with route table associations.
  }
}

resource "azurerm_subnet_route_table_association" "this" {
  for_each = local.subnets_route_table_associations

  subnet_id      = each.value.subnet_id
  route_table_id = each.value.route_table_id

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
    read   = "5m"
  }
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS -> NETWORK SECURITY GROUP ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  subnets_network_security_group_associations = {
    for subnet_config in local.subnets :
    # Generate a unique resource_id.
    # We won't need to refer to this resource_id anywhere else in the code.
    # That's why we are turning it into MD5 hash to guarantee its uniqueness
    # and character length.
    md5(
      join("",
        [
          subnet_config.resource_id,
          subnet_config.network_security_group_id
        ]
      )
      ) => {
      subnet_id                 = azurerm_subnet.this[subnet_config.resource_id].id
      network_security_group_id = azurerm_network_security_group.this[subnet_config.network_security_group_id].id
    } if subnet_config.network_security_group_id != "" # Consider only subnets with nsg associations.
  }
}

resource "azurerm_subnet_network_security_group_association" "this" {
  for_each = local.subnets_network_security_group_associations

  subnet_id                 = each.value.subnet_id
  network_security_group_id = each.value.network_security_group_id

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
    read   = "5m"
  }
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS -> NAT GATEWAY ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  subnets_nat_gateway_associations = {
    for subnet_config in local.subnets :
    # Generate a unique resource_id.
    # We won't need to refer to this resource_id anywhere else in the code.
    # That's why we are turning it into MD5 hash to guarantee its uniqueness
    # and character length.
    md5(subnet_config.resource_id) => {
      subnet_id      = azurerm_subnet.this[subnet_config.resource_id].id
      nat_gateway_id = azurerm_nat_gateway.this[subnet_config.vnet_resource_id].id
    } if subnet_config.is_associated_to_nat_gateway && subnet_config.is_nat_gateway_enabled
  }
}

resource "azurerm_subnet_nat_gateway_association" "this" {
  for_each = local.subnets_nat_gateway_associations

  subnet_id      = each.value.subnet_id
  nat_gateway_id = each.value.nat_gateway_id

  timeouts {
    create = "5m"
    update = "5m"
    delete = "5m"
    read   = "5m"
  }
}
