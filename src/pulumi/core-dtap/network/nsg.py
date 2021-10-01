import pulumi
import pulumi_azure_native as azure_native
from ingenii_azure_data_platform.utils import generate_resource_name
from project_config import platform_config, platform_outputs
from management import resource_groups

outputs = platform_outputs["network"]["network_security_groups"] = {}

# TODO: Remove duplication. Use a for loop or another method to create the NSGs.

# ----------------------------------------------------------------------------------------------------------------------
# DATABRICKS NSG for ENGINEERING SUBNETS
# ----------------------------------------------------------------------------------------------------------------------
databricks_engineering_resource_name = generate_resource_name(
    resource_type="network_security_group",
    resource_name="databricks-eng",
    platform_config=platform_config,
)
databricks_engineering = azure_native.network.NetworkSecurityGroup(
    resource_name=databricks_engineering_resource_name,
    network_security_group_name=databricks_engineering_resource_name,
    resource_group_name=resource_groups["infra"].name,
    tags=platform_config.tags,
    # Tags are added in the ignore_changes list because of:
    # https://github.com/ingenii-solutions/azure-data-platform/issues/71
    opts=pulumi.ResourceOptions(ignore_changes=["security_rules", "tags"]),
)

# Export NSG metadata
outputs["databricks_engineering"] = {
    "name": databricks_engineering.name,
    "id": databricks_engineering.id,
}

# ----------------------------------------------------------------------------------------------------------------------
# DATABRICKS NSG for ANALYTICS SUBNETS
# ----------------------------------------------------------------------------------------------------------------------
databricks_analytics_resource_name = generate_resource_name(
    resource_type="network_security_group",
    resource_name="databricks-atc",
    platform_config=platform_config,
)
databricks_analytics = azure_native.network.NetworkSecurityGroup(
    resource_name=databricks_analytics_resource_name,
    network_security_group_name=databricks_analytics_resource_name,
    resource_group_name=resource_groups["infra"].name,
    tags=platform_config.tags,
    # Tags are added in the ignore_changes list because of:
    # https://github.com/ingenii-solutions/azure-data-platform/issues/71
    opts=pulumi.ResourceOptions(ignore_changes=["security_rules", "tags"]),
)

# Export NSG metadata
outputs["databricks_analytics"] = {
    "name": databricks_analytics.name,
    "id": databricks_analytics.id,
}
