########################################################################################################################
# CONFIGURATION
########################################################################################################################
# Inherit the global configuration as defined in the parent terragrunt.hcl file.
include {
  path = find_in_parent_folders()
}

locals {
  # The global config object. It contains all local values and configurations defined in the parent terragrunt.hcl file.
  config_obj = read_terragrunt_config(find_in_parent_folders("terragrunt.hcl"))["locals"]

  # The YAML config represents a merge between the defaults.<env_type>_env.yml and configs/<env>.yml files.
  yaml_config = local.config_obj.yaml_config

  # Get the config required for this component.
  component_config = try(
    local.yaml_config.management.resource_groups == null ? {} : local.yaml_config.management.resource_groups,
    {}
  )
}

########################################################################################################################
# TERRAFORM VERSIONS AND PROVIDERS
# Import any platform-wide versions and providers or define component-specific providers and versions. Or both.
########################################################################################################################
generate = {

  # Generate a 'terraform{}' block with core terraform and provider version definitions.
  terraform_version_config = local.config_obj.terraform_version_config

  # Generate an Azure RM provider block. This provider is platform-wide, and the majority of the resources are using it.
  terraform_provider_config_azurerm = local.config_obj.terraform_provider_config.azurerm

  #... Additional providers can be defined here.
}

########################################################################################################################
# DEPENDENCIES
########################################################################################################################
# Azure AD Groups
dependency "azuread_user_groups" {
  config_path = "..//azuread_user_group"

  mock_outputs = {
    groups = {}
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
  dependencies = {
    azuread_user_groups = dependency.azuread_user_groups.outputs.groups
  }
}
