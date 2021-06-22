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
    local.yaml_config.network.virtual_networks == null ? {} : local.yaml_config.network.virtual_networks,
    {}
  )

  # If the component config is missing from the YAML files, we are skipping the deployment of this component.
  skip_deployment = try(!contains(keys(local.yaml_config.network), "virtual_networks"), true)
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

  # Mock outputs are useful when Terraform plan is ran across all components, before they have been applied yet.
  # Since no outputs will be generated from each dependency, the mock outputs are used instead.

  # Mock outputs should never be used during Terraform apply.
  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]

  # Example output:
  # groups = {
  #   engineers = {
  #     id        = "engineers"
  #     object_id = "9b0feca7-121a-4f90-bfd9-b0e96f2e1ba7"
  #   }
  # }
  mock_outputs = {
    groups = {
      for id, config in try(local.yaml_config.management.user_groups, {}) : id => {
        name      = config.display_name
        object_id = uuid()
      }
    }
  }
}

# Azure Resource Groups
dependency "azure_resource_group" {
  config_path = "..//azure_resource_group"

  # Mock outputs are useful when Terraform plan is ran across all components, before they have been applied yet.
  # Since no outputs will be generated from each dependency, the mock outputs are used instead.

  # Mock outputs should never be used during Terraform apply.
  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]

  # Example output:
  # groups = {
  #   infra = {
  #     id = "infra"
  #   }
  # }
  mock_outputs = {
    groups = {
      for id, config in try(local.yaml_config.management.resource_groups, {}) : id => {
        name = config.display_name
      }
    }
  }
}


# Azure Network Security Groups
dependency "azure_network_security_group" {
  config_path = "..//azure_network_security_group"

  # Mock outputs are useful when Terraform plan is ran across all components, before they have been applied yet.
  # Since no outputs will be generated from each dependency, the mock outputs are used instead.

  # Mock outputs should never be used during Terraform apply.
  mock_outputs_allowed_terraform_commands = ["init", "validate", "plan"]

  # Example output:
  # groups = {
  #   databricks = {
  #     id = "/subscriptions/df0ed18d-6999-4c80-9474-d8b7d0b9c472/resourceGroups/temp/providers/Microsoft.Network/networkSecurityGroups/databricks"
  #   }
  # }
  mock_outputs = {
    groups = {
      for id, config in try(local.yaml_config.network.network_security_groups, {}) : id => {
        id = "/subscriptions/${uuid()}/resourceGroups/temp/providers/Microsoft.Network/networkSecurityGroups/${id}"
      }
    }
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
    azuread_user_group           = dependency.azuread_user_group.outputs.groups
    azure_resource_group         = dependency.azure_resource_group.outputs.groups
    azure_network_security_group = dependency.azure_network_security_group.outputs.groups
  }
}
