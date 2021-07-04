locals {
  #--------------------------------------------------------------------------------------------------------------------
  # ENVIRONMENT
  # Extract the environment name and set the environment type. 
  # Dev, Test, Prod environments will be considered of DTAP type.
  #--------------------------------------------------------------------------------------------------------------------
  env      = lower(get_env("DP_ENV_NAME"))
  env_type = local.env == "shared" ? "shared" : "dtap"

  #--------------------------------------------------------------------------------------------------------------------
  # PATHS
  # Set useful paths to be reused in the downstream components.
  #--------------------------------------------------------------------------------------------------------------------
  root_dir    = chomp(run_cmd("--terragrunt-quiet", "git", "rev-parse", "--show-toplevel"))
  configs_dir = "${local.root_dir}/configs"
  src_dir     = "${local.root_dir}/src"
  modules_dir = "${local.src_dir}/modules"
  env_dir     = "${local.src_dir}/env"

  #--------------------------------------------------------------------------------------------------------------------
  # CONFIG FILE PATHS
  # All important config files and their paths.
  #--------------------------------------------------------------------------------------------------------------------
  env_yml_file_path      = "${local.configs_dir}/${local.env}.yml"
  globals_yml_file_path  = "${local.configs_dir}/globals.yml"
  defaults_yml_file_path = "${local.env_dir}/${local.env_type}/defaults.yml"
  dummy_yml_file_path    = "${local.env_dir}/${local.env_type}/dummy.yml"

  #--------------------------------------------------------------------------------------------------------------------
  # YAML CONFIG
  # Merge and decode the YAML config. We are merging Defaults <- Globals <- Env YAML files, where Defaults is 
  # overwritten by Globals and the result of that is overwritten by the Env YAML file. The result of the merge
  # operation is then decoded and passed down to each component.
  #--------------------------------------------------------------------------------------------------------------------
  yaml_config = [
    # TODO docs
    can(run_cmd("--terragrunt-quiet", "touch", "${local.dummy_yml_file_path}")),

    # TODO: yq docs on merging yml files: https://mikefarah.gitbook.io/yq/operators/reduce
    yamldecode(
      run_cmd(
        "--terragrunt-quiet",
        "yq", "eval-all", ". as $item ireduce ({}; . *+ $item )",
        "${local.env_dir}/${local.env_type}/defaults.yml",
        fileexists(local.globals_yml_file_path) ? local.globals_yml_file_path : local.dummy_yml_file_path,
        fileexists(local.env_yml_file_path) ? local.env_yml_file_path : local.dummy_yml_file_path
      )
    )
  ][1]

  #--------------------------------------------------------------------------------------------------------------------
  # REMOTE STATE BACKEND CONFIG
  # We expect the terraform remote state backend type to be configured via the YAML files or using environment vars.
  # If the backend state config credentials are different than the current environment's service principal creds, we
  # allow backend specific credentials to be passed on via environment variables.
  #--------------------------------------------------------------------------------------------------------------------
  remote_state_backend_type = try(
    local.yaml_config.terraform.remote_state_backend.type,
    get_env("DP_TF_REMOTE_STATE_BACKEND_TYPE", "azurerm")
  )

  remote_state_backend_types = {
    # Azure Backend Type
    azurerm = {
      resource_group_name = try(
        local.yaml_config.terraform.remote_state_backend.azurerm.resource_group_name,
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_RESOURCE_GROUP_NAME")
      )

      storage_account_name = try(
        local.yaml_config.terraform.remote_state_backend.azurerm.storage_account_name,
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_STORAGE_ACCOUNT_NAME")
      )

      container_name = try(
        local.yaml_config.terraform.remote_state_backend.azurerm.container_name,
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_CONTAINER_NAME")
      )

      # This is the base of the key. Inside the env.hcl file, we'll construct the final key path.
      key = "ingenii/azure-data-platform/${local.env}"

      # Environment
      environment = try(
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_ENVIRONMENT"),
        get_env("ARM_ENVIRONMENT", "public"),
      )

      # Authentication Details
      client_id = try(
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_CLIENT_ID"),
        get_env("ARM_CLIENT_ID")
      )

      tenant_id = try(
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_TENANT_ID"),
        get_env("ARM_TENANT_ID"),
      )

      subscription_id = try(
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_SUBSCRIPTION_ID"),
        get_env("ARM_SUBSCRIPTION_ID"),
      )

      client_secret = try(
        get_env("DP_TF_REMOTE_STATE_BACKEND_AZURERM_CLIENT_SECRET"),
        get_env("ARM_CLIENT_SECRET"),
      )
    }
  }

  remote_state_config = {
    type   = local.remote_state_backend_type
    config = local.remote_state_backend_types[local.remote_state_backend_type]
  }

  #--------------------------------------------------------------------------------------------------------------------
  # EXPORTS
  # We are wrapping all the data that needs to be used by the downstream Terragrunt files in a single "exports" object 
  # for an easy import.
  #--------------------------------------------------------------------------------------------------------------------
  exports = {
    # Platform Config
    # Contains merged and decoded YAML file + additional configs.
    platform_config = merge(
      local.yaml_config,
      {
        env      = local.env
        env_type = local.env_type
      }
    )

    # Remote State Config
    remote_state_config = local.remote_state_config

    # Directories
    root_dir    = local.root_dir
    configs_dir = local.configs_dir
    src_dir     = local.src_dir
    modules_dir = local.modules_dir
    env_dir     = local.env_dir
  }
}
