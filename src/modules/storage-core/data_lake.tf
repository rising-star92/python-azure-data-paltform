#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2
#------------------------------
# Schema Path: platform.storage.data_lakes
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         enabled:
#         display_name:
#         resource_group_ref_key:
#         tags:
#         data_management:
#           data_protection:
#             enable_soft_delete_for_containers:
#           data_lifecycle: TODO
#         storage_account:
#           access_tier:
#           replication_type:
#           tier:
#           kind:
#           allow_blob_public_access:
#           min_tls_version:
#           enable_https_traffic_only:
#           is_hns_enabled:
#         network:
#           private_endpoints:
#         iam:
#         containers:
#----------------------------------------------------------------------------------------------------------------------
locals {
  __data_lakes_raw_config = try(local.config.platform.storage.data_lakes, {})

  __data_lakes_processed_config = {
    for data_lake_ref_key, data_lake_config in local.__data_lakes_raw_config :
    data_lake_ref_key => {
      resource_id = data_lake_ref_key
      ref_key     = data_lake_ref_key

      name = (
        lower(
          "${local.prefix}${local.env}${data_lake_config.display_name}${random_string.data_lake[data_lake_ref_key].result}"
        )
      )

      resource_group_name                       = local.resource_groups[data_lake_config.resource_group_ref_key].name
      storage_account_access_tier               = try(data_lake_config.storage_account.access_tier, "Hot")
      storage_account_replication_type          = try(data_lake_config.storage_account.replication_type, "RAGRS")
      storage_account_tier                      = try(data_lake_config.storage_account.tier, "Standard")
      storage_account_kind                      = try(data_lake_config.storage_account.kind, "StorageV2")
      storage_account_allow_blob_public_access  = try(data_lake_config.storage_account.allow_blob_public_access, false)
      storage_account_min_tls_version           = try(data_lake_config.storage_account.min_tls_version, "TLS1_2")
      storage_account_enable_https_traffic_only = try(data_lake_config.storage_account.enable_https_traffic_only, true)
      storage_account_is_hns_enabled            = try(data_lake_config.storage_account.is_hns_enabled, "true")
      region                                    = local.region.long_name
      tags                                      = merge(local.tags, try(data_lake_config.tags, {}))

      network    = try(data_lake_config.network, {})
      iam        = try(data_lake_config.iam, {})
      containers = try(data_lake_config.containers, {})
    } if try(data_lake_config.enabled, true) # Consider objects with attrib 'enabled' set to 'true' or not set at all.
  }

  data_lakes = { for config in local.__data_lakes_processed_config : config.resource_id => config }
}

resource "azurerm_storage_account" "data_lake" {
  for_each = local.data_lakes

  location                  = each.value.region
  resource_group_name       = each.value.resource_group_name
  tags                      = each.value.tags
  name                      = each.value.name
  access_tier               = each.value.storage_account_access_tier
  account_replication_type  = each.value.storage_account_replication_type
  account_tier              = each.value.storage_account_tier
  account_kind              = each.value.storage_account_kind
  allow_blob_public_access  = each.value.storage_account_allow_blob_public_access
  is_hns_enabled            = each.value.storage_account_is_hns_enabled
  min_tls_version           = each.value.storage_account_min_tls_version
  enable_https_traffic_only = each.value.storage_account_enable_https_traffic_only
}

# This random string is used to help generate the name of the Azure Storage Account 
# that will be used as Data Lake Storage.
locals {
  data_lakes_ref_keys_only = {
    for data_lake_ref_key, data_lake_config in local.__data_lakes_raw_config :
    data_lake_ref_key => {}
  }
}

resource "random_string" "data_lake" {
  for_each = local.data_lakes_ref_keys_only

  length  = 4
  lower   = false
  number  = true
  upper   = false
  special = false
}

#----------------------------------------------------------------------------------------------------------------------
# AZURE DATA LAKE STORAGE GEN 2 -> IAM ROLE ASSIGNMENTS
#------------------------------------------------------
# Schema Path: platform.storage.data_lakes.<data_lake>.iam.role_assignments
# Sample Schema: 
# --
# platform:
#   storage:
#     data_lakes:
#       <data_lake_ref_key>:
#         iam:
#           role_assignments:
#             - user_group_ref_key:
#               role_definition_name:
#               principal_id:         # conflicts with user_group_ref_key
#               role_definition_id:   # conflicts with role_definition_name
#----------------------------------------------------------------------------------------------------------------------
locals {
  __data_lakes_iam_role_assignments_processed_config = flatten(
    [
      for data_lake_config in local.data_lakes :
      [
        for assignment in try(data_lake_config.iam.role_assignments, []) :
        [
          {
            # Generate a unique resource_id.
            # We won't need to refer to this resource_id anywhere else in the code.
            # That's why we are turning it into MD5 hash to guarantee its uniqueness
            # and character length.
            resource_id = md5(
              join("",
                [
                  data_lake_config.resource_id,
                  try(assignment.user_group_ref_key, ""),
                  try(assignment.role_definition_name, ""),
                  try(assignment.role_definition_id, "")
                ]
              )
            )

            data_lake_resource_id  = data_lake_config.resource_id
            user_group_resource_id = try(assignment.user_group_ref_key, null)
            principal_id           = try(assignment.principal_id, null)
            role_definition_name   = try(assignment.role_definition_name, null)
            role_definition_id     = try(assignment.role_definition_id, null)
          }
        ]
      ]
    ]
  )

  data_lakes_iam_role_assignments = {
    for assignment in local.__data_lakes_iam_role_assignments_processed_config : assignment.resource_id => assignment
  }
}

resource "azurerm_role_assignment" "data_lake" {
  for_each = local.data_lakes_iam_role_assignments

  scope = azurerm_storage_account.data_lake[each.value.data_lake_resource_id].id

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

