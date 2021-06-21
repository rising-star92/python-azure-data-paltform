########################################################################################################################
# CONFIGURATION
########################################################################################################################
# Inherit the global configuration as defined in the parent terragrunt.hcl file.
include {
  path   = find_in_parent_folders()
  expose = true
}

locals {
  # The YAML config represents a merge between the defaults.<env_type>_env.yml and configs/<env>.yml files.
  yaml_config = include.locals.yaml_config

  # Get the config required for this component.
  component_config = try(
    local.yaml_config.storage.data_lakes == null ? {} : local.yaml_config.storage.data_lakes,
    {}
  )

  # If the component config is missing from the YAML files, we are skipping the deployment of this component.
  skip_deployment = try(!contains(keys(local.yaml_config.storage), "data_lakes"), true)
}

skip = local.skip_deployment

########################################################################################################################
# TERRAFORM VERSIONS AND PROVIDERS
# Import any platform-wide versions and providers or define component-specific providers and versions. Or both.
########################################################################################################################
generate = {

  # Generate a 'terraform{}' block with core terraform and provider version definitions.
  terraform_version_config = include.locals.terraform_version_config

  # Generate an Azure RM provider block. This provider is platform-wide, and the majority of the resources are using it.
  terraform_provider_config_azurerm = include.locals.terraform_provider_config.azurerm

  #... Additional providers can be defined here.
}

########################################################################################################################
# DEPENDENCIES
########################################################################################################################
# Azure AD Groups
dependency "azuread_user_group" {
  config_path = "..//azuread_user_group"

  mock_outputs = {
    groups = {}
  }
}

# Azure Resource Groups
dependency "azure_resource_group" {
  config_path = "..//azure_resource_group"

  mock_outputs = {
    groups = {}
  }
}

# Azure Virtual Networks
dependency "azure_virtual_network" {
  config_path = "..//azure_virtual_network"

  mock_outputs = {
    virtual_networks = {}
  }
}

# Network Firewall
dependency "network_firewall" {
  config_path = "..//network_firewall"

  mock_outputs = {
    access_lists = {}
  }
}

########################################################################################################################
# MAIN
########################################################################################################################
terraform {
  source = ".//src"
}

inputs = {
  # Global inputs are also passed as defined in the parent terragrunt.hcl file.

  component_config = local.component_config

  # Component dependencies
  dependencies = {
    azuread_user_group    = dependency.azuread_user_group.outputs.groups
    azure_resource_group  = dependency.azure_resource_group.outputs.groups
    azure_virtual_network = dependency.azure_virtual_network.outputs.virtual_networks
    network_firewall      = dependency.network_firewall.outputs
  }
}
