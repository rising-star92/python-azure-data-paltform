#----------------------------------------------------------------------------------------------------------------------
# OUTPUTS
#----------------------------------------------------------------------------------------------------------------------
output "user_groups" {
  value = try(
    {
      for id, config in local.azuread_groups :
      id => {
        name      = azuread_group.this["${id}"].name
        object_id = azuread_group.this["${id}"].object_id
      }
    },
    {}
  )
}

output "resource_groups" {
  value = try(
    {
      for id, configs in local.azure_resource_groups :
      id => {
        name = azurerm_resource_group.this["${id}"].name
        id   = azurerm_resource_group.this["${id}"].id
      }
    },
    {}
  )
}
