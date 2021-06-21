########################################################################################################################
# OUTPUTS
########################################################################################################################
output "data_lakes" {
  value = try(
    {
      for data_lake_id, data_lake_config in local.azure_storage_gen_2_data_lakes :
      data_lake_id => {
        name = data_lake_config.name
        storage_account = {
          id   = module.azure_storage_gen_2_data_lake[data_lake_id].storage_account_id
          name = module.azure_storage_gen_2_data_lake[data_lake_id].storage_account_name
          endpoints = {
            dfs = module.azure_storage_gen_2_data_lake[data_lake_id].storage_account_dfs_endpoint
          }
        }

        iam = {
          role_definitions = data_lake_config.iam.role_definitions
        }

        storage_containers = {
          for container_id, container_config in module.azure_storage_gen_2_data_lake[data_lake_id].data_lake_containers :
          container_id => {
            name        = container_config.name
            id          = container_config.id
            resource_id = "${module.azure_storage_gen_2_data_lake[data_lake_id].storage_account_id}/blobServices/default/containers/${container_config.name}"
          }
        }
      }
    },
    {}
  )
}