import pulumi_azure_native as azure_native
from pulumi.resource import ResourceOptions
from config import platform as p
from management import resource_groups

# ----------------------------------------------------------------------------------------------------------------------
# DATABRICKS NSG for ENGINEERING SUBNETS
# ----------------------------------------------------------------------------------------------------------------------
databricks_engineering_resource_name = p.generate_name(
    "network_security_group", "databricks-eng")
databricks_engineering = azure_native.network.NetworkSecurityGroup(
    resource_name=databricks_engineering_resource_name,
    network_security_group_name=databricks_engineering_resource_name,
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
    opts=ResourceOptions(ignore_changes=["security_rules"])
)

# ----------------------------------------------------------------------------------------------------------------------
# DATABRICKS NSG for ANALYTICS SUBNETS
# ----------------------------------------------------------------------------------------------------------------------
databricks_analytics_resource_name = p.generate_name(
    "network_security_group", "databricks-atc")
databricks_analytics = azure_native.network.NetworkSecurityGroup(
    resource_name=databricks_analytics_resource_name,
    network_security_group_name=databricks_analytics_resource_name,
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
    opts=ResourceOptions(ignore_changes=["security_rules"])
)
