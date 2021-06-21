########################################################################################################################
# OUTPUTS
########################################################################################################################
output "groups" {
  value = try(
    {
      for group_id, group_config in local.azure_network_security_groups :
      group_id => {
        name = azurerm_network_security_group.this["${group_id}"].name
        id   = azurerm_network_security_group.this["${group_id}"].id
      }
    },
    {}
  )
}