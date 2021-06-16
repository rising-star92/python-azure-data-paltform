########################################################################################################################
# OUTPUTS
########################################################################################################################
output "groups" {
  value = try(
    {
      for group_id, group_config in local.azuread_groups :
      group_id => {
        name      = azuread_group.this["${group_id}"].name
        object_id = azuread_group.this["${group_id}"].object_id
      }
    },
    {}
  )
}
