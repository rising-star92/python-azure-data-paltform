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
  ip_access_list = try(
    local.component_config.ip_access_list != null ? local.component_config.ip_access_list : [],
    []
  )

  subnet_access_list = try(
    local.component_config.subnet_access_list != null ? local.component_config.subnet_access_list : [],
    []
  )
}
