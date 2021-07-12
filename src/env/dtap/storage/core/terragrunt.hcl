#--------------------------------------------------------------------------------------------------------------------
# LOAD ENV CONFIG
#--------------------------------------------------------------------------------------------------------------------
include {
  path   = find_in_parent_folders("env.hcl")
  expose = true
}

#--------------------------------------------------------------------------------------------------------------------
# PREPARE LOCAL VALUES
#--------------------------------------------------------------------------------------------------------------------
locals {
  root_hcl_exports = include.locals.root_hcl_exports

  config = local.root_hcl_exports.platform_config
}

#--------------------------------------------------------------------------------------------------------------------
# DEPENDENCIES
#--------------------------------------------------------------------------------------------------------------------
dependency "management_core" {
  config_path = "..//..//management//core"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]

  mock_outputs = {

    user_groups = {
      for id, config in try(local.config.platform.management.user_groups, {}) :
      id => {
        name      = uuid()
        object_id = uuid()
      }
    }

    resource_groups = {
      for id, config in try(local.config.platform.management.resource_groups, {}) :
      id => {
        id   = "/subscriptions/${uuid()}/resourceGroups/${uuid()}"
        name = uuid()
      }
    }
  }
}

dependency "network_core" {
  config_path = "..//..//network//core"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]

  mock_outputs = {
    virtual_networks = {
      for vnet_ref_key, vnet_config in try(local.config.platform.network.virtual_networks, {}) :
      vnet_ref_key => {
        subnets = {
          for subnet_ref_key, subnet_config in try(vnet_config.subnets, {}) :
          subnet_ref_key => {
            id   = "/subscriptions/${uuid()}/resourceGroups/${uuid()}/providers/Microsoft.Network/virtualNetworks/${uuid()}/subnets/${uuid()}"
            name = "mock-${uuid()}"
          }
        }
      }
    }
    dns = {
      private_zones = {
        for dns_zone_ref_key, dns_zone_config in try(local.config.platform.network.dns.private_zones, {}) :
        dns_zone_ref_key => {
          id = "/subscriptions/${uuid()}/resourceGroups/${uuid()}/providers/Microsoft.Network/privateDnsZones/${uuid()}"
        }
      }
    }
  }
}

#--------------------------------------------------------------------------------------------------------------------
# TERRAFORM SOURCE
#--------------------------------------------------------------------------------------------------------------------
terraform {
  source = "${local.root_hcl_exports.modules_dir}//storage-core"
}

#--------------------------------------------------------------------------------------------------------------------
# INPUTS
#--------------------------------------------------------------------------------------------------------------------
inputs = {
  # The global inputs from (env.hcl) file are automatically passed here.

  # Define additional inputs that are not already included from the global inputs.
  dependencies = {
    management = {
      user_groups     = dependency.management_core.outputs.user_groups
      resource_groups = dependency.management_core.outputs.resource_groups
    }

    network = {
      virtual_networks = dependency.network_core.outputs.virtual_networks
      dns              = dependency.network_core.outputs.dns
    }
  }
}
