#--------------------------------------------------------------------------------------------------------------------
# LOAD ROOT CONFIG
#--------------------------------------------------------------------------------------------------------------------
locals {
  root_hcl_config = read_terragrunt_config(find_in_parent_folders("root.hcl"))["locals"]["exports"]
}

#--------------------------------------------------------------------------------------------------------------------
# REMOTE STATE CONFIG
# This is where the remote_state block is configured. All downstream components will inherit this block to set their
# backend config.
#--------------------------------------------------------------------------------------------------------------------
remote_state {
  backend = local.root_hcl_config.remote_state_config.type
  config = merge(
    local.root_hcl_config.remote_state_config.config,
    {
      # The final key path is a combination of a base key config (defined in root.hcl) plus the additional config
      # defined below. The decision to keep the config definition split is because how (path_relative_to_include())
      # works. To get the correct behavior, we need to keep the function call in the (env.hcl) file as that is 
      # "included" by the downstream components.
      key = format(
        "%s/%s",
        local.root_hcl_config.remote_state_config.config.key,
        "${path_relative_to_include()}/terraform.tfstate"
      )
    }
  )

  generate = {
    path      = "_generated_remote_state_backend.tf"
    if_exists = "overwrite"
  }
}

#--------------------------------------------------------------------------------------------------------------------
# PROVIDER CONFIG
#--------------------------------------------------------------------------------------------------------------------
generate "azurerm_provider" {
  path      = "_generated_azurerm_provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
provider "azurerm" {
  features {}
  # Credentials are passed via Environment Variables.
}
EOF
}

generate "azuread_provider" {
  path      = "_generated_azuread_provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
provider "azuread" {
  # Credentials are passed via Environment Variables.
}
EOF
}

#--------------------------------------------------------------------------------------------------------------------
# GLOBAL INPUTS
# All downstream components will have the "config" object passed to them.
#--------------------------------------------------------------------------------------------------------------------
inputs = {
  config       = local.root_hcl_config.platform_config
  dependencies = {}
}
