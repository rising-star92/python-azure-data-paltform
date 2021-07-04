#----------------------------------------------------------------------------------------------------------------------
# SHORTCUTS
#
# Using fully qualified naming can result in very long lines of code.
# In this section, we assign specific resources, especially dependencies, to much shorter local variable names.
#----------------------------------------------------------------------------------------------------------------------
locals {
  config       = jsondecode(var.config)
  dependencies = jsondecode(var.dependencies)
  env          = local.config.env
  prefix       = local.config.platform.general.prefix
  region       = local.config.platform.general.region
  tags         = local.config.platform.general.tags

  resource_groups = local.dependencies.management.resource_groups
  user_groups     = local.dependencies.management.user_groups
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing virtual network configuration.
  azure_virtual_networks_config = try(local.config.platform.network.virtual_networks, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azure_virtual_networks = {
    for vnet_ref_key, vnet_config in local.azure_virtual_networks_config :

    vnet_ref_key => {
      vnet_ref_key = vnet_ref_key

      name                = lower("${local.prefix}-${local.region.short_name}-${local.env}-vnet-${vnet_config.display_name}")
      region              = local.region.long_name
      resource_group_name = local.resource_groups[vnet_config.resource_group_ref_key].name
      address_space       = vnet_config.address_space
      tags                = merge(local.tags, try(vnet_config.tags, {}))
      bgp_community       = try(vnet_config.bgp_community, null)
      dns_servers         = try(vnet_config.dns_servers, [])
    }
  }
}

resource "azurerm_virtual_network" "this" {
  for_each = local.azure_virtual_networks

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
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Create a list with all role assignments for every virtual network.
  # Example:
  # [
  #   {
  #     vnet_ref_key          = "main"
  #     role_definition_name  = "Owner"
  #     user_group_ref_key    = "engineers"
  #   }
  # ]
  azure_virtual_networks_iam_role_assignments = flatten(
    [
      for vnet_ref_key, vnet_config in local.azure_virtual_networks_config : [
        for role_assignment in try(vnet_config.iam.role_assignments, {}) : [
          {
            vnet_ref_key         = vnet_ref_key
            role_definition_name = try(role_assignment.role_definition_name, null)
            role_definition_id   = try(role_assignment.role_definition_id, null)
            user_group_ref_key   = try(role_assignment.user_group_ref_key, "")
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # azure_virtual_networks_iam_role_assignments_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { vnet_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { vnet_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  # }
  azure_virtual_networks_iam_role_assignments_hashed = {
    for assignment in local.azure_virtual_networks_iam_role_assignments :
    md5(
      join("",
        [
          assignment.vnet_ref_key,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_ref_key
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_virtual_network" {
  for_each = local.azure_virtual_networks_iam_role_assignments_hashed

  scope                = azurerm_virtual_network.this[each.value.vnet_ref_key].id
  principal_id         = local.user_groups[each.value.user_group_ref_key].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS
#----------------------------------------------------------------------------------------------------------------------
locals {

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.

  # We are creating a list of subnet config objects for every subnet that has been defined in the YAML file.
  # The object has enough information to identify which VNET the subnet belongs to.
  azure_subnets_config = flatten(
    [
      for vnet_ref_key, vnet_config in local.azure_virtual_networks_config : [

        # Check for existing subnet configuration.
        for subnet_ref_key, subnet_config in try(vnet_config.subnets, {}) : [
          {
            subnet_ref_key = subnet_ref_key

            name                           = lower("${local.prefix}-${local.region.short_name}-${local.env}-snet-${subnet_config.display_name}")
            address_prefixes               = subnet_config.address_prefixes
            resource_group_name            = azurerm_virtual_network.this[vnet_ref_key].resource_group_name
            virtual_network_name           = azurerm_virtual_network.this[vnet_ref_key].name
            delegations                    = try(subnet_config.delegations, {})
            service_endpoints              = try(subnet_config.service_endpoints, null)
            service_endpoint_policy_ids    = try(subnet_config.service_endpoint_policy_ids, null)
            network_security_group_ref_key = try(subnet_config.network_security_group_ref_key, "")
            route_table_ref_key            = try(subnet_config.route_table_ref_key, "")
            nat_gateway_ref_key            = try(subnet_config.nat_gateway_ref_key, "")
            enforce_private_link_endpoint_network_policies = try(
              subnet_config.enforce_private_link_endpoint_network_policies, false
            )
            enforce_private_link_service_network_policies = try(
              subnet_config.enforce_private_link_service_network_policies, false
            )
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # azure_subnets_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { name = "xxxx", resource_group_name = "xxxx", etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { name = "xxxx", resource_group_name = "xxxx", etc...}
  # }
  azure_subnets_hashed = {
    for subnet_config in local.azure_subnets_config :
    md5(
      join("",
        [
          subnet_config.subnet_ref_key,
          subnet_config.name,
          subnet_config.virtual_network_name
        ]
      )
    ) => subnet_config
  }
}

resource "azurerm_subnet" "this" {
  for_each = local.azure_subnets_hashed

  name                                           = each.value.name
  resource_group_name                            = each.value.resource_group_name
  virtual_network_name                           = each.value.virtual_network_name
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
        actions = d.value.service_delegation.actions
      }
    }
  }
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS -> ROUTE TABLE ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # xxxx_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { subnet_id = "xxxx", route_table_id = "xxxx" }
  #   "1fc0ea929d277af17375256a9410c478" = { subnet_id = "xxxx", route_table_id = "xxxx" }
  # }
  azure_subnets_route_table_associations_hashed = {
    for subnet_ref_key_hashed, subnet_config in local.azure_subnets_hashed :
    md5(
      join("",
        [
          subnet_ref_key_hashed,
          subnet_config.route_table_ref_key
        ]
      )
      ) => {
      subnet_id      = azurerm_subnet.this[subnet_ref_key_hashed].id
      route_table_id = azurerm_route_table.this[subnet_config.route_table_ref_key].id
    } if subnet_config.route_table_ref_key != ""
  }
}

resource "azurerm_subnet_route_table_association" "this" {
  for_each = local.azure_subnets_route_table_associations_hashed

  subnet_id      = each.value.subnet_id
  route_table_id = each.value.route_table_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS -> NETWORK SECURITY GROUP ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # xxxx_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { subnet_id = "xxxx", network_security_group_id = "xxxx" }
  #   "1fc0ea929d277af17375256a9410c478" = { subnet_id = "xxxx", network_security_group_id = "xxxx" }
  # }
  azure_subnets_network_security_group_associations_hashed = {
    for subnet_ref_key_hashed, subnet_config in local.azure_subnets_hashed :
    md5(
      join("",
        [
          subnet_ref_key_hashed,
          subnet_config.network_security_group_ref_key
        ]
      )
      ) => {
      subnet_id                 = azurerm_subnet.this[subnet_ref_key_hashed].id
      network_security_group_id = azurerm_network_security_group.this[subnet_config.network_security_group_ref_key].id
    } if subnet_config.network_security_group_ref_key != ""
  }
}

resource "azurerm_subnet_network_security_group_association" "this" {
  for_each = local.azure_subnets_network_security_group_associations_hashed

  subnet_id                 = each.value.subnet_id
  network_security_group_id = each.value.network_security_group_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE VIRTUAL NETWORKS -> SUBNETS -> NAT GATEWAY ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # xxxx_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { subnet_id = "xxxx", nat_gateway_id = "xxxx" }
  #   "1fc0ea929d277af17375256a9410c478" = { subnet_id = "xxxx", nat_gateway_id = "xxxx" }
  # }
  azure_subnets_nat_gateway_associations_hashed = {
    for subnet_ref_key_hashed, subnet_config in local.azure_subnets_hashed :
    md5(
      join("",
        [
          subnet_ref_key_hashed,
          subnet_config.nat_gateway_ref_key
        ]
      )
      ) => {
      subnet_id      = azurerm_subnet.this[subnet_ref_key_hashed].id
      nat_gateway_id = azurerm_nat_gateway.this[subnet_config.nat_gateway_ref_key].id
    } if subnet_config.nat_gateway_ref_key != ""
  }
}

resource "azurerm_subnet_nat_gateway_association" "this" {
  for_each = local.azure_subnets_nat_gateway_associations_hashed

  subnet_id      = each.value.subnet_id
  nat_gateway_id = each.value.nat_gateway_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE ROUTE TABLES
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing route table configuration.
  azure_route_tables_config = try(local.config.platform.network.route_tables, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azure_route_tables = {
    for route_table_ref_key, route_table_config in local.azure_route_tables_config :

    route_table_ref_key => {
      route_table_ref_key = route_table_ref_key

      name = lower(
        "${local.prefix}-${local.region.short_name}-${local.env}-rt-${route_table_config.display_name}"
      )
      region                        = local.region.long_name
      resource_group_name           = local.resource_groups[route_table_config.resource_group_ref_key].name
      disable_bgp_route_propagation = try(route_table_config.disable_bgp_route_propagation, false)
      tags                          = merge(local.tags, try(route_table_config.tags, {}))
    }
  }
}

resource "azurerm_route_table" "this" {
  for_each = local.azure_route_tables

  name                          = each.value.name
  location                      = each.value.region
  resource_group_name           = each.value.resource_group_name
  disable_bgp_route_propagation = each.value.disable_bgp_route_propagation
  tags                          = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE ROUTE TABLES -> IAM ROLE ASSIGNMENTS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Create a list with all role assignments for every route table.
  # Example:
  # [
  #   {
  #     route_table_ref_key   = "main"
  #     role_definition_name  = "Owner"
  #     user_group_ref_key    = "engineers"
  #   }
  # ]
  azure_route_tables_iam_role_assignments = flatten(
    [
      for route_table_ref_key, route_table_config in local.azure_route_tables_config : [
        for role_assignment in try(route_table_config.iam.role_assignments, {}) : [
          {
            route_table_ref_key  = route_table_ref_key
            role_definition_name = try(role_assignment.role_definition_name, null)
            role_definition_id   = try(role_assignment.role_definition_id, null)
            user_group_ref_key   = try(role_assignment.user_group_ref_key, "")
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # azure_route_tables_iam_role_assignments_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { route_table_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { route_table_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  # }
  azure_route_tables_iam_role_assignments_hashed = {
    for assignment in local.azure_route_tables_iam_role_assignments :
    md5(
      join("",
        [
          assignment.route_table_ref_key,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_ref_key
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_route_table" {
  for_each = local.azure_route_tables_iam_role_assignments_hashed

  scope                = azurerm_route_table.this[each.value.route_table_ref_key].id
  principal_id         = local.user_groups[each.value.user_group_ref_key].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE ROUTE TABLES -> ROUTES
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing routes configuration.
  azure_routes_config = flatten(
    [
      for route_table_ref_key, route_table_config in local.azure_route_tables_config : [
        for route_ref_key, route_config in try(route_table_config.routes, {}) : [
          {
            route_ref_key       = route_ref_key
            route_table_ref_key = route_table_ref_key

            name                   = route_config.display_name
            address_prefix         = route_config.address_prefix
            next_hop_type          = route_config.next_hop_type
            next_hop_in_ip_address = try(route_config.next_hop_in_ip_address, null)
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # xxxx_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { route_ref_key = "xxxx", name = "xxxx" etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { route_ref_key = "xxxx", name = "xxxx" etc...}
  # }
  azure_routes_hashed = {
    for route_config in local.azure_routes_config : md5(
      join("",
        [
          route_config.route_ref_key,
          route_config.route_table_ref_key,
          route_config.name,
          route_config.address_prefix
        ]
      )
    ) => route_config
  }
}

resource "azurerm_route" "this" {
  for_each = local.azure_routes_hashed

  name                   = each.value.name
  resource_group_name    = azurerm_route_table.this[each.value.route_table_ref_key].resource_group_name
  route_table_name       = azurerm_route_table.this[each.value.route_table_ref_key].name
  address_prefix         = each.value.address_prefix
  next_hop_type          = each.value.next_hop_type
  next_hop_in_ip_address = each.value.next_hop_in_ip_address
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NETWORK SECURITY GROUPS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing network security groups configuration.
  azure_network_security_groups_config = try(local.config.platform.network.network_security_groups, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azure_network_security_groups = {
    for network_security_group_ref_key, network_security_group_config in local.azure_network_security_groups_config :

    network_security_group_ref_key => {
      network_security_group_ref_key = network_security_group_ref_key

      name = lower(
        "${local.prefix}-${local.region.short_name}-${local.env}-nsg-${network_security_group_config.display_name}"
      )
      region              = local.region.long_name
      resource_group_name = local.resource_groups[network_security_group_config.resource_group_ref_key].name
      tags                = merge(local.tags, try(network_security_group_config.tags, {}))
      rules               = try(network_security_group_config.rules, {})
    }
  }
}

resource "azurerm_network_security_group" "this" {
  for_each = local.azure_network_security_groups

  name                = each.value.name
  location            = each.value.region
  resource_group_name = each.value.resource_group_name
  tags                = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NETWORK SECURITY GROUPS -> IAM ROLE ASSIGNMENTS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Create a list with all role assignments for every route table.
  # Example:
  # [
  #   {
  #     network_security_group_ref_key    = "main"
  #     role_definition_name              = "Owner"
  #     user_group_ref_key                = "engineers"
  #   }
  # ]
  azure_network_security_groups_iam_role_assignments = flatten(
    [
      for network_security_group_ref_key, network_security_group_config in local.azure_network_security_groups_config : [
        for role_assignment in try(network_security_group_config.iam.role_assignments, {}) : [
          {
            network_security_group_ref_key = network_security_group_ref_key
            role_definition_name           = try(role_assignment.role_definition_name, null)
            role_definition_id             = try(role_assignment.role_definition_id, null)
            user_group_ref_key             = try(role_assignment.user_group_ref_key, "")
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # azure_network_security_groups_iam_role_assignments_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { network_security_group_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { network_security_group_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  # }
  azure_network_security_groups_iam_role_assignments_hashed = {
    for assignment in local.azure_network_security_groups_iam_role_assignments :
    md5(
      join("",
        [
          assignment.network_security_group_ref_key,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_ref_key
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_network_security_group" {
  for_each = local.azure_network_security_groups_iam_role_assignments_hashed

  scope                = azurerm_network_security_group.this[each.value.network_security_group_ref_key].id
  principal_id         = local.user_groups[each.value.user_group_ref_key].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NETWORK SECURITY GROUPS -> RULES
#----------------------------------------------------------------------------------------------------------------------
locals {
  azure_network_security_rules_config = flatten(
    [
      for network_security_group_ref_key, network_security_group_config in local.azure_network_security_groups : [

        # Check for existing network security groups configuration.
        for network_security_rule_ref_key, network_security_rule_config in network_security_group_config.rules :
        {
          network_security_group_ref_key = network_security_group_ref_key
          network_security_rule_ref_key  = network_security_rule_ref_key

          name                         = network_security_rule_config.display_name
          description                  = network_security_rule_config.description
          priority                     = network_security_rule_config.priority
          direction                    = network_security_rule_config.direction
          access                       = network_security_rule_config.access
          protocol                     = network_security_rule_config.protocol
          source_port_range            = try(network_security_rule_config.source_port_range, null)
          source_port_ranges           = try(network_security_rule_config.source_port_ranges, null)
          source_address_prefix        = try(network_security_rule_config.source_address_prefix, null)
          source_address_prefixes      = try(network_security_rule_config.source_address_prefixes, null)
          destination_port_range       = try(network_security_rule_config.destination_port_range, null)
          destination_port_ranges      = try(network_security_rule_config.destination_port_ranges, null)
          destination_address_prefix   = try(network_security_rule_config.destination_address_prefix, null)
          destination_address_prefixes = try(network_security_rule_config.destination_address_prefixes, null)
          resource_group_name          = network_security_group_config.resource_group_name
          network_security_group_name  = azurerm_network_security_group.this[network_security_group_ref_key].name
        }
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # xxxx_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { network_security_rule_ref_key = "xxxx", name = "xxxx" etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { network_security_rule_ref_key = "xxxx", name = "xxxx" etc...}
  # }
  azure_network_security_rules_hashed = {
    for rule_config in local.azure_network_security_rules_config :
    md5(
      join("",
        [
          rule_config.network_security_group_ref_key,
          rule_config.network_security_rule_ref_key,
          rule_config.name
        ]
      )
    ) => rule_config
  }
}

resource "azurerm_network_security_rule" "this" {
  for_each = local.azure_network_security_rules_hashed

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
  resource_group_name          = each.value.resource_group_name
  network_security_group_name  = each.value.network_security_group_name
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE PUBLIC IP ADDRESSES
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing public ip configuration.
  azure_public_ip_addresses_config = try(local.config.platform.network.public_ip_addresses, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azure_public_ip_addresses = {
    for public_ip_address_ref_key, public_ip_config in local.azure_public_ip_addresses_config :

    public_ip_address_ref_key => {
      public_ip_address_ref_key = public_ip_address_ref_key

      name = lower(
        "${local.prefix}-${local.region.short_name}-${local.env}-pip-${public_ip_config.display_name}"
      )
      resource_group_name     = local.resource_groups[public_ip_config.resource_group_ref_key].name
      sku                     = try(public_ip_config.sku_name, "Standard")
      allocation_method       = try(public_ip_config.allocation_method, "Static")
      availability_zone       = try(public_ip_config.availability_zone, null)
      ip_version              = try(public_ip_config.ip_version, "IPv4")
      idle_timeout_in_minutes = try(public_ip_config.idle_timeout_in_minutes, null)
      domain_name_label       = try(public_ip_config.domain_name_label, null)
      reverse_fqdn            = try(public_ip_config.reverse_fqdn, null)
      region                  = local.region.long_name
      tags                    = merge(local.tags, try(public_ip_config.tags, {}))
    }
  }
}

resource "azurerm_public_ip" "this" {
  for_each = local.azure_public_ip_addresses

  name                    = each.value.name
  location                = each.value.region
  resource_group_name     = each.value.resource_group_name
  allocation_method       = each.value.allocation_method
  sku                     = each.value.sku
  availability_zone       = each.value.availability_zone
  ip_version              = each.value.ip_version
  idle_timeout_in_minutes = each.value.idle_timeout_in_minutes
  domain_name_label       = each.value.domain_name_label
  reverse_fqdn            = each.value.reverse_fqdn
  tags                    = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE PUBLIC IP ADDRESSES -> IAM ROLE ASSIGNMENTS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Create a list with all role assignments for every route table.
  # Example:
  # [
  #   {
  #     public_ip_address_ref_key     = "main"
  #     role_definition_name          = "Owner"
  #     user_group_ref_key            = "engineers"
  #   }
  # ]
  azure_public_ip_addresses_iam_role_assignments = flatten(
    [
      for public_ip_address_ref_key, public_ip_address_config in local.azure_public_ip_addresses_config : [
        for role_assignment in try(public_ip_address_config.iam.role_assignments, {}) : [
          {
            public_ip_address_ref_key = public_ip_address_ref_key
            role_definition_name      = try(role_assignment.role_definition_name, null)
            role_definition_id        = try(role_assignment.role_definition_id, null)
            user_group_ref_key        = try(role_assignment.user_group_ref_key, "")
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # azure_public_ip_addresses_iam_role_assignments_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { public_ip_address_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { public_ip_address_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  # }
  azure_public_ip_addresses_iam_role_assignments_hashed = {
    for assignment in local.azure_public_ip_addresses_iam_role_assignments :
    md5(
      join("",
        [
          assignment.public_ip_address_ref_key,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_ref_key
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_public_ip_address" {
  for_each = local.azure_public_ip_addresses_iam_role_assignments_hashed

  scope                = azurerm_public_ip.this[each.value.public_ip_address_ref_key].id
  principal_id         = local.user_groups[each.value.user_group_ref_key].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NAT GATEWAYS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Check for existing NAT gateway configuration.
  azure_nat_gateways_config = try(local.config.platform.network.nat_gateways, {})

  # Process and prepare the config before passing it to the Terraform resource.
  # Any processing or data lookups should be done as we construct the configuration map, not at resource level.
  # Please consult with the YAML schema documentation to see full list of attributes for this resource.
  azure_nat_gateways = {
    for nat_gateway_ref_key, nat_gateway_config in local.azure_nat_gateways_config :

    nat_gateway_ref_key => {
      nat_gateway_ref_key = nat_gateway_ref_key

      name = lower(
        "${local.prefix}-${local.region.short_name}-${local.env}-ngw-${nat_gateway_config.display_name}"
      )
      idle_timeout_in_minutes   = try(nat_gateway_config.idle_timeout_in_minutes, 4)
      public_ip_address_ref_key = nat_gateway_config.public_ip_address_ref_key
      resource_group_name       = local.resource_groups[nat_gateway_config.resource_group_ref_key].name
      sku_name                  = try(nat_gateway_config.sku_name, "Standard")
      tags                      = merge(local.tags, try(nat_gateway_config.tags, {}))
      zones                     = try(nat_gateway_config.availability_zones, null)
      region                    = local.region.long_name
    }
  }

}

resource "azurerm_nat_gateway" "this" {
  for_each = local.azure_nat_gateways

  name                    = each.value.name
  location                = each.value.region
  resource_group_name     = each.value.resource_group_name
  sku_name                = each.value.sku_name
  idle_timeout_in_minutes = each.value.idle_timeout_in_minutes
  zones                   = each.value.zones
  tags                    = each.value.tags
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NAT GATEWAYS -> IAM ROLE ASSIGNMENTS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # Create a list with all role assignments for every route table.
  # Example:
  # [
  #   {
  #     nat_gateway_ref_key       = "main"
  #     role_definition_name      = "Owner"
  #     user_group_ref_key        = "engineers"
  #   }
  # ]
  azure_nat_gateways_iam_role_assignments = flatten(
    [
      for nat_gateway_ref_key, nat_gateway_config in local.azure_nat_gateways_config : [
        for role_assignment in try(nat_gateway_config.iam.role_assignments, {}) : [
          {
            nat_gateway_ref_key  = nat_gateway_ref_key
            role_definition_name = try(role_assignment.role_definition_name, null)
            role_definition_id   = try(role_assignment.role_definition_id, null)
            user_group_ref_key   = try(role_assignment.user_group_ref_key, "")
          }
        ]
      ]
    ]
  )

  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # azure_nat_gateways_iam_role_assignments_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { nat_gateway_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { nat_gateway_ref_key = "xxxx", user_group_ref_key = "xxxx", etc...}
  # }
  azure_nat_gateways_iam_role_assignments_hashed = {
    for assignment in local.azure_nat_gateways_iam_role_assignments :
    md5(
      join("",
        [
          assignment.nat_gateway_ref_key,
          assignment.role_definition_name == null ? assignment.role_definition_id : assignment.role_definition_name,
          assignment.role_definition_id == null ? assignment.role_definition_name : assignment.role_definition_id,
          assignment.user_group_ref_key
        ]
      )
    ) => assignment
  }
}

resource "azurerm_role_assignment" "azure_nat_gateway" {
  for_each = local.azure_nat_gateways_iam_role_assignments_hashed

  scope                = azurerm_nat_gateway.this[each.value.nat_gateway_ref_key].id
  principal_id         = local.user_groups[each.value.user_group_ref_key].object_id
  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE NAT GATEWAYS -> PUBLIC IP ADDRESS ASSOCIATIONS
#----------------------------------------------------------------------------------------------------------------------
locals {
  # To ensure key uniqueness, we generate MD5 hashes based on certain attributes of the config objects.
  # The MD5 hashes are then used as map keys, that have config objects assigned as values.
  # 
  # Examples:
  #
  # xxxx_hashed = {
  #   "71f6ac3385ce284152a64208521c592b" = { nat_gateway_id = "xxxx", public_ip_address_id = "xxxx" etc...}
  #   "1fc0ea929d277af17375256a9410c478" = { nat_gateway_id = "xxxx", public_ip_address_id = "xxxx" etc...}
  # }
  azure_nat_gateways_public_ip_associations_hashed = {
    for nat_gateway_ref_key, nat_gateway_config in local.azure_nat_gateways :
    md5(
      join("",
        [
          nat_gateway_ref_key,
          nat_gateway_config.public_ip_address_ref_key
        ]
      )
      ) => {
      nat_gateway_id       = azurerm_nat_gateway.this[nat_gateway_ref_key].id
      public_ip_address_id = azurerm_public_ip.this[nat_gateway_config.public_ip_address_ref_key].id
    }
  }
}

resource "azurerm_nat_gateway_public_ip_association" "this" {
  for_each = local.azure_nat_gateways_public_ip_associations_hashed

  nat_gateway_id       = each.value.nat_gateway_id
  public_ip_address_id = each.value.public_ip_address_id
}
