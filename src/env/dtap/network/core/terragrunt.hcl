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
  root_hcl_config = include.locals.root_hcl_config
  env_hcl_config  = include.locals
}

#--------------------------------------------------------------------------------------------------------------------
# DEPENDENCIES
#--------------------------------------------------------------------------------------------------------------------
dependency "management_core" {
  config_path = "..//..//management//core"

  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]

  mock_outputs = {

    user_groups = {
      for id, config in try(local.root_hcl_config.platform_config.platform.management.user_groups, {}) :
      id => {
        name      = uuid()
        object_id = uuid()
      }
    }

    resource_groups = {
      for id, config in try(local.root_hcl_config.platform_config.platform.management.resource_groups, {}) :
      id => {
        id   = "/subscriptions/${uuid()}/resourceGroups/${uuid()}"
        name = uuid()
      }
    }
  }
}

#--------------------------------------------------------------------------------------------------------------------
# TERRAFORM SOURCE
#--------------------------------------------------------------------------------------------------------------------
terraform {
  source = "${local.root_hcl_config.modules_dir}//network-core"
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
  }
}
