locals {
  ######################################################################################################################
  # ENVIRONMENT
  ######################################################################################################################
  env      = lower(get_env("DP_ENV_NAME"))
  env_type = local.env == "shared" ? "shared" : "dtap"

  ######################################################################################################################
  # PATHS
  ######################################################################################################################
  paths = {
    root_dir    = chomp(run_cmd("--terragrunt-quiet", "git", "rev-parse", "--show-toplevel"))
    configs_dir = "${run_cmd("--terragrunt-quiet", "git", "rev-parse", "--show-toplevel")}/configs"
    src_dir     = "${run_cmd("--terragrunt-quiet", "git", "rev-parse", "--show-toplevel")}/src"
  }

  config_file_paths = {
    globals  = "${local.paths.configs_dir}/globals.yml"
    defaults = "${local.paths.src_dir}/defaults.${local.env_type}_env.yml"
    env      = "${local.paths.configs_dir}/${local.env}.yml"
    versions = "${local.paths.src_dir}/versions.yml"
    dummy    = "${local.paths.src_dir}/dummy.yml"
  }

  ######################################################################################################################
  # YAML CONFIG
  ######################################################################################################################
  yaml_config_files = {
    globals = fileexists(
      "${local.paths.configs_dir}/globals.yml"
    ) ? "${local.config_file_paths.globals}" : "${local.config_file_paths.dummy}"

    env = fileexists(
      "${local.config_file_paths.env}"
    ) ? "${local.config_file_paths.env}" : "${local.config_file_paths.dummy}"

    defaults = "${local.paths.src_dir}/defaults.${local.env_type}_env.yml"
  }

  yaml_config = [
    # Create a dummy yml file to be used in place of possible missing optional yml files.
    can(run_cmd("--terragrunt-quiet", "touch", "${local.config_file_paths.dummy}")),

    # yq docs on merging yml files: https://mikefarah.gitbook.io/yq/operators/reduce
    yamldecode(
      run_cmd(
        "--terragrunt-quiet",
        "yq", "eval-all", ". as $item ireduce ({}; . *+ $item )",
        "${local.yaml_config_files.defaults}",
        "${local.yaml_config_files.globals}",
        "${local.yaml_config_files.env}"
      )
    )
  ][1]

  ######################################################################################################################
  # REMOTE STATE CONFIG
  ######################################################################################################################
  remote_state_backend_type = try(
    local.yaml_config.terraform.remote_state_backend.type,
    get_env("DP_TF_RS_BACKEND_TYPE", "azurerm")
  )

  remote_state_backend_types = {

    # Azure Backend Type
    azurerm = {
      resource_group_name = try(
        local.yaml_config.terraform.remote_state_backend.azurerm.resource_group_name,
        get_env("DP_TF_RS_BACKEND_AZURERM_RESOURCE_GROUP_NAME", "")
      )

      storage_account_name = try(
        local.yaml_config.terraform.remote_state_backend.azurerm.storage_account_name,
        get_env("DP_TF_RS_BACKEND_AZURERM_STORAGE_ACCOUNT_NAME", "")
      )

      container_name = try(
        local.yaml_config.terraform.remote_state_backend.azurerm.container_name,
        get_env("DP_TF_RS_BACKEND_AZURERM_CONTAINER_NAME", "")
      )

      key = "ingenii/azure-data-platform/${local.env}/${path_relative_to_include()}/terraform.tfstate"

      # Environment
      environment = try(
        get_env("DP_TF_RS_BACKEND_AZURERM_ENVIRONMENT"),
        get_env("ARM_ENVIRONMENT", "public"),
      )

      # Authentication Details
      client_id = try(
        get_env("DP_TF_RS_BACKEND_AZURERM_CLIENT_ID"),
        get_env("DP_TF_AUTH_AZURERM_CLIENT_ID"),
        get_env("DP_TF_AUTH_CLIENT_ID"),
        get_env("ARM_CLIENT_ID")
      )

      tenant_id = try(
        get_env("DP_TF_RS_BACKEND_AZURERM_TENANT_ID"),
        get_env("DP_TF_AUTH_AZURERM_TENANT_ID"),
        get_env("DP_TF_AUTH_TENANT_ID"),
        get_env("ARM_TENANT_ID"),
      )

      subscription_id = try(
        get_env("DP_TF_RS_BACKEND_AZURERM_SUBSCRIPTION_ID"),
        get_env("DP_TF_AUTH_AZURERM_SUBSCRIPTION_ID"),
        get_env("DP_TF_AUTH_SUBSCRIPTION_ID"),
        get_env("ARM_SUBSCRIPTION_ID"),
      )

      client_secret = try(
        get_env("DP_TF_RS_BACKEND_AZURERM_CLIENT_SECRET"),
        get_env("DP_TF_AUTH_AZURERM_CLIENT_SECRET"),
        get_env("DP_TF_AUTH_CLIENT_SECRET"),
        get_env("ARM_CLIENT_SECRET"),
      )
    }
  }

  ######################################################################################################################
  # TERRAFORM VERSION CONFIG
  # Terraform core and provider version definitions.
  ######################################################################################################################
  versions = yamldecode(file(local.config_file_paths.versions))

  terraform_version_config = {
    path      = "_generated_terraform_versions.tf"
    if_exists = "overwrite"
    contents  = <<EOF
terraform {
  required_version = "${local.versions.terraform.required_version}"
  required_providers {
    azurerm = {
      source  = "${local.versions.terraform.required_providers.azurerm.source}"
      version = "${local.versions.terraform.required_providers.azurerm.version}"
    }
    azuread = {
      source = "${local.versions.terraform.required_providers.azuread.source}"
      version = "${local.versions.terraform.required_providers.azuread.version}"
    }
  }
}
EOF
  }

  ######################################################################################################################
  # TERRAFORM PROVIDER CONFIG
  # Platform-wide Terraform providers that any component can use.
  # Additional providers can be registered under the 'terraform_provider_config' map.
  ######################################################################################################################
  terraform_provider_config = {

    # Azure RM
    azurerm = {
      path      = "_generated_azurerm_provider.tf"
      if_exists = "overwrite"
      contents = <<EOF
provider "azurerm" {
  features {}
  client_id = "${
      try(
        get_env("DP_TF_AUTH_AZURERM_CLIENT_ID"),
        get_env("DP_TF_AUTH_CLIENT_ID"),
        get_env("ARM_CLIENT_ID")
      )
      }"
  tenant_id = "${
      try(
        get_env("DP_TF_AUTH_AZURERM_TENANT_ID"),
        get_env("DP_TF_AUTH_TENANT_ID"),
        get_env("ARM_TENANT_ID")
      )
      }"
  subscription_id = "${
      try(
        get_env("DP_TF_AUTH_AZURERM_SUBSCRIPTION_ID"),
        get_env("DP_TF_AUTH_SUBSCRIPTION_ID"),
        get_env("ARM_SUBSCRIPTION_ID")
      )
      }"
  client_secret = "${
      try(
        get_env("DP_TF_AUTH_AZURERM_CLIENT_SECRET"),
        get_env("DP_TF_AUTH_CLIENT_SECRET"),
        get_env("ARM_CLIENT_SECRET")
      )
    }"
}
EOF
  }

  # Azure AD
  azuread = {
    path      = "_generated_azuread_provider.tf"
    if_exists = "overwrite"
    contents = <<EOF
provider "azuread" {
  client_id = "${
    try(
      get_env("DP_TF_AUTH_AZUREAD_CLIENT_ID"),
      get_env("DP_TF_AUTH_CLIENT_ID"),
      get_env("ARM_CLIENT_ID")
    )
    }"
  tenant_id = "${
    try(
      get_env("DP_TF_AUTH_AZUREAD_TENANT_ID"),
      get_env("DP_TF_AUTH_TENANT_ID"),
      get_env("ARM_TENANT_ID")
    )
    }"
  client_secret = "${
    try(
      get_env("DP_TF_AUTH_AZUREAD_CLIENT_SECRET"),
      get_env("DP_TF_AUTH_CLIENT_SECRET"),
      get_env("ARM_CLIENT_SECRET")
    )
  }"
}
EOF
}
}
}

######################################################################################################################
# INPUTS
# All child components will inherit these inputs.
######################################################################################################################
inputs = {
  env             = local.env
  resource_prefix = local.yaml_config.general.resource_prefix
  region          = local.yaml_config.general.region
  tags            = local.yaml_config.general.tags
}

######################################################################################################################
# REMOTE STATE
# All child components will inherit the remote state config.
######################################################################################################################
remote_state {
  backend = local.remote_state_backend_type
  config  = local.remote_state_backend_types[local.remote_state_backend_type]

  generate = {
    path      = "_generated_remote_state_backend.tf"
    if_exists = "overwrite"
  }
}
