########################################################################################################################
# OUTPUTS
########################################################################################################################
output "access_lists" {
  value = {
    ip_access_list     = local.ip_access_list
    subnet_access_list = local.subnet_access_list
  }
}