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
    local.yaml_config.management.user_groups == null ? {} : local.yaml_config.management.user_groups,
    {}
  )

  # If the component config is missing from the YAML files, we are skipping the deployment of this component.
  skip_deployment = try(!contains(keys(local.yaml_config.management), "user_groups"), true)
}

skip = local.skip_deployment

########################################################################################################################
# TERRAFORM VERSIONS AND PROVIDERS
# Import any platform-wide versions and providers or define component-specific providers and versions. Or both.
########################################################################################################################
generate = {

  # Generate a 'terraform{}' block with core terraform and provider version definitions.
  terraform_version_config = include.locals.terraform_version_config

  # Generate an Azure AD provider block. This provider is platform-wide, and the majority of the resources are using it.
  terraform_provider_config_azuread = include.locals.terraform_provider_config.azuread

  #... Additional providers can be defined here.
}

########################################################################################################################
# DEPENDENCIES
########################################################################################################################

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
  dependencies = {}
}
