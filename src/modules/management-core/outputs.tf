#######################################################################################################################
# !!! IMPORTANT !!!
#
# The structure of the outputs is highly dependent on by other modules. Making changes on the structure will result in
# failures and potentially catastrophic side effects. (e.g. destruction of data resources)
# 
# The outputs are considered contracts and should be treated with caution.
#
# If you need to make changes of the output structure, consider the following:
# - Leave any existing attributes in place. If you need to expose the same data in a different way, 
#   just create a new (alias) attribute. This will guarantee backward compatibility.
# - Make sure to test your changes by running a full platform deployment.
# - Make sure to run terraform plan on the customer environments before applying the changes.
#######################################################################################################################


#----------------------------------------------------------------------------------------------------------------------
# OUTPUTS
#----------------------------------------------------------------------------------------------------------------------

# User Groups
output "user_groups" {
  value = {
    for group_config in local.user_groups :
    group_config.ref_key => {
      object_id = azuread_group.this[group_config.resource_id].object_id
      name      = azuread_group.this[group_config.resource_id].name
    }
  }
}

# Resource Groups
output "resource_groups" {
  value = {
    for group_config in local.resource_groups :
    group_config.ref_key => {
      id   = azurerm_resource_group.this[group_config.resource_id].id
      name = azurerm_resource_group.this[group_config.resource_id].name
    }
  }
}
