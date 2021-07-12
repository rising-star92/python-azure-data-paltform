#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2 -> CONTAINERS
#--------------------------------------------
# Schema Path: platform.storage.data_lakes.<data_lake_ref_key>.containers
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         containers:
#           <container_ref_key>:
#             enabled:
#             display_name:
#             iam: 
#             paths:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __data_lake_containers_processed_config = flatten(
    [
      for data_lake_config in local.data_lakes :
      [
        for container_ref_key, container_config in data_lake_config.containers :
        [
          {
            data_lake_resource_id = data_lake_config.resource_id

            resource_id = join("_", [data_lake_config.resource_id, container_ref_key])
            ref_key     = container_ref_key

            name  = container_config.display_name
            iam   = try(container_config.iam, {})
            paths = try(container_config.paths, [])
          }
        ] if try(container_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
      ]

    ]
  )

  data_lake_containers = { for config in local.__data_lake_containers_processed_config : config.resource_id => config }
}

resource "azurerm_storage_data_lake_gen2_filesystem" "data_lake" {
  for_each = local.data_lake_containers

  name               = each.value.name
  storage_account_id = azurerm_storage_account.data_lake[each.value.data_lake_resource_id].id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2 -> CONTAINERS -> IAM ROLE ASSIGNMENTS
#--------------------------------------------------------------------
# Schema Path: platform.storage.data_lakes.<data_lake_ref_key>.containers.iam.role_assignments
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         containers:
#           <container_ref_key>:
#             enabled:
#             display_name:
#             iam:
#               role_assignments:
#                 - user_group_ref_key:
#                   role_definition_name:
#                   principal_id:         # conflicts with user_group_ref_key
#                   role_definition_id:   # conflicts with role_definition_name
#----------------------------------------------------------------------------------------------------------------------
locals {
  __data_lakes_containers_iam_role_assignments_processed_config = flatten(
    [
      for data_lake_container_config in local.data_lake_containers :
      [
        for assignment in try(data_lake_container_config.iam.role_assignments, []) :
        [
          {
            data_lake_resource_id           = data_lake_container_config.data_lake_resource_id
            data_lake_container_resource_id = data_lake_container_config.resource_id
            data_lake_container_name        = data_lake_container_config.name

            # Generate a unique resource_id.
            # We won't need to refer to this resource_id anywhere else in the code.
            # That's why we are turning it into MD5 hash to guarantee its uniqueness
            # and character length.
            resource_id = md5(
              join("",
                [
                  data_lake_container_config.resource_id,
                  try(assignment.user_group_ref_key, ""),
                  try(assignment.role_definition_name, ""),
                  try(assignment.role_definition_id, "")
                ]
              )
            )

            user_group_resource_id = try(assignment.user_group_ref_key, null)
            principal_id           = try(assignment.principal_id, null)
            role_definition_name   = try(assignment.role_definition_name, null)
            role_definition_id     = try(assignment.role_definition_id, null)
          }
        ]
      ]
    ]
  )

  data_lakes_containers_iam_role_assignments = {
    for config in local.__data_lakes_containers_iam_role_assignments_processed_config : config.resource_id => config
  }
}

resource "azurerm_role_assignment" "data_lake_containers" {
  for_each = local.data_lakes_containers_iam_role_assignments

  scope = (
    "${
      azurerm_storage_account.data_lake[each.value.data_lake_resource_id].id
    }/blobServices/default/containers/${each.value.data_lake_container_name}"
  )

  # We evaluate the principal_id in the following order:
  principal_id = try(
    # 1. Check if the role assignment is about a user_group we have created.
    local.user_groups[each.value.user_group_resource_id].object_id,
    # 2. Check if the role assignment is about a principal id that is external to our deployment.
    each.value.principal_id
    # 3. If no matches, error out.
  )

  role_definition_name = each.value.role_definition_name
  role_definition_id   = each.value.role_definition_id
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2 -> CONTAINERS -> PATHS
#-----------------------------------------------------
# Schema Path: platform.storage.data_lakes.<data_lake_ref_key>.containers.paths
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         containers:
#           <container_ref_key>:
#             paths:
#               - path_name:
#                 resource_type
#                 owner:
#                 group:
#----------------------------------------------------------------------------------------------------------------------
locals {

  __data_lakes_containers_paths_processed_config = flatten(
    [
      for data_lake_container_config in local.data_lake_containers :
      [
        for path in try(data_lake_container_config.paths, []) :
        [
          {
            data_lake_resource_id           = data_lake_container_config.data_lake_resource_id
            data_lake_container_resource_id = data_lake_container_config.resource_id

            # Generate a unique resource_id.
            # We won't need to refer to this resource_id anywhere else in the code.
            # That's why we are turning it into MD5 hash to guarantee its uniqueness
            # and character length.
            resource_id = md5(
              join("",
                [
                  data_lake_container_config.resource_id,
                  path.path_name
                ]
              )
            )

            path_name        = path.path_name
            path_resource    = try(path.resource_type, "directory")
            path_owner       = try(path.owner, null)
            path_group_owner = try(path.group, null)
          }
        ]
      ]
    ]
  )

  data_lakes_containers_paths = {
    for config in local.__data_lakes_containers_paths_processed_config : config.resource_id => config
  }
}

resource "azurerm_storage_data_lake_gen2_path" "data_lake" {
  for_each = local.data_lakes_containers_paths

  storage_account_id = azurerm_storage_account.data_lake[each.value.data_lake_resource_id].id
  path               = each.value.path_name
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.data_lake[each.value.data_lake_container_resource_id].name
  resource           = each.value.path_resource
  owner              = each.value.path_owner
  group              = each.value.path_group_owner
}