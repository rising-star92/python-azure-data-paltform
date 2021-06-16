########################################################################################################################
# OUTPUTS
########################################################################################################################
output "groups" {
  value = try(
    {
      for group_id, group_config in local.azure_resource_groups :
      group_id => {
        name = azurerm_resource_group.this["${group_id}"].name
        id   = azurerm_resource_group.this["${group_id}"].id
      }
    },
    {}
  )
}
