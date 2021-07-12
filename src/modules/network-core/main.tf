#----------------------------------------------------------------------------------------------------------------------
# SHORTCUTS
#
# Using fully qualified naming can result in very long lines of code.
# In this section, we assign specific values, especially dependencies, to much shorter local variable names.
#----------------------------------------------------------------------------------------------------------------------
locals {
  config = jsondecode(var.config)
  env    = local.config.env
  prefix = local.config.platform.general.prefix
  region = local.config.platform.general.region
  tags   = local.config.platform.general.tags

  # Dependencies
  dependencies = jsondecode(var.dependencies)

  user_groups     = local.dependencies.management.user_groups
  resource_groups = local.dependencies.management.resource_groups
}
