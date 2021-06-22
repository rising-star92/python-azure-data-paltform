########################################################################################################################
# LOCAL VALUES
########################################################################################################################
locals {
  component_config = jsondecode(var.component_config)
  dependencies     = jsondecode(var.dependencies)

  env             = var.env
  resource_prefix = var.resource_prefix
  region          = var.region
  tags            = jsondecode(var.tags)
}

########################################################################################################################
# MAIN
########################################################################################################################
locals {
  azure_storage_gen_2_data_lakes = {
    for data_lake_id, data_lake_config in try(local.component_config, {}) :
    data_lake_id => {
      name                = lower("${local.resource_prefix}${local.env}${data_lake_config.display_name}${random_string.this.result}")
      resource_group_name = local.dependencies.azure_resource_group[data_lake_config.resource_group_key_name].name
      iam = {
        role_definitions = data_lake_config.iam.role_definitions
      }
      network_acls = {
        default_action = try(data_lake_config.network.firewall.default_action, "Allow")
        bypass         = try(data_lake_config.network.firewall.bypass_services, [])
        ip_rules = distinct(
          flatten(
            [
              try(data_lake_config.network.firewall.ip_access_list, []),
              local.dependencies.network_firewall.access_lists.ip_access_list
            ]
          )
        )
        virtual_network_subnet_ids = [
          for subnet_acl in distinct(
            flatten(
              [
                try(data_lake_config.network.firewall.subnet_access_list, []),
                local.dependencies.network_firewall.access_lists.subnet_access_list
              ]
            )
          ) : local.dependencies.azure_virtual_network[split(":", subnet_acl)[0]].subnets[split(":", subnet_acl)[1]].id
        ]
      }
      storage_containers = try(data_lake_config.storage_containers, {})
      storage_container_names = [
        for container_config in data_lake_config.storage_containers : container_config.display_name
      ]
      storage_container_paths = flatten(
        [
          for container_config in try(data_lake_config.storage_containers, {}) :
          [
            for path in try(container_config.paths, []) :
            { container_name = container_config.display_name, path_name = path }
          ]
        ]
      )
      region = local.region
      tags   = local.tags
    }
  }

  # Example output:
  #
  # [{scope = "xxx", principal_id="xxx", role_definition_name="xxx"}]
  azure_storage_gen_2_data_lakes_containers_iam_role_assignments = flatten(
    [
      for data_lake_id, data_lake_config in local.azure_storage_gen_2_data_lakes : [
        for container_id, container_config in data_lake_config.storage_containers : [
          for role_definition_id, user_groups in container_config.iam.role_assignments : [
            for group_id in user_groups : [
              {
                role_definition_name   = data_lake_config.iam.role_definitions[role_definition_id]
                principal_id           = local.dependencies.azuread_user_group[group_id].object_id
                storage_container_name = container_config.display_name
                data_lake_id           = data_lake_id
              }
            ]
          ]
        ]
      ]
    ]
  )

  # Example output:
  #
  # {
  #  "8c80c0ffa801ba24e38886bad9ec1d1e" = {scope = "xxx", principal_id="xxx", role_definition_name="xxx"}
  #  "a4be8f29fa3a6b7d9c81a59a33d2f79c" = {scope = "xxx", principal_id="xxx", role_definition_name="xxx"}
  # }
  azure_storage_gen_2_data_lakes_containers_iam_role_assignments_hashed_map = {
    for assignment in local.azure_storage_gen_2_data_lakes_containers_iam_role_assignments :
    md5(
      join("",
        [
          assignment.data_lake_id,
          assignment.storage_container_name,
          assignment.principal_id,
          assignment.role_definition_name
        ]
      )
    ) => assignment
  }
}

resource "random_string" "this" {
  length = 4

  lower   = true
  number  = true
  upper   = false
  special = false
}

module "azure_storage_gen_2_data_lake" {
  for_each = local.azure_storage_gen_2_data_lakes

  source  = "ingenii-solutions/data-lake-gen2/azurerm"
  version = "0.0.1"

  region               = each.value.region
  resource_group_name  = each.value.resource_group_name
  storage_account_name = each.value.name
  tags                 = each.value.tags

  data_lake_containers         = each.value.storage_container_names
  data_lake_container_paths    = each.value.storage_container_paths
  storage_account_network_acls = each.value.network_acls
}

resource "azurerm_role_assignment" "azure_storage_gen_2_data_lake" {
  for_each             = local.azure_storage_gen_2_data_lakes_containers_iam_role_assignments_hashed_map
  scope                = "${module.azure_storage_gen_2_data_lake[each.value.data_lake_id].storage_account_id}/blobServices/default/containers/${each.value.storage_container_name}"
  principal_id         = each.value.principal_id
  role_definition_name = each.value.role_definition_name
}