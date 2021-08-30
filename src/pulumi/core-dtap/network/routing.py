import pulumi_azure_native as azure_native
from ingenii_azure_data_platform.utils import generate_resource_name
from config import platform_config
from management import resource_groups

# ----------------------------------------------------------------------------------------------------------------------
# MAIN ROUTE TABLE
# ----------------------------------------------------------------------------------------------------------------------
main_route_table_resource_name = generate_resource_name(
    resource_type="route_table", resource_name="main", platform_config=platform_config
)
main_route_table = azure_native.network.RouteTable(
    resource_name=main_route_table_resource_name,
    route_table_name=main_route_table_resource_name,
    resource_group_name=resource_groups.infra.name,
    disable_bgp_route_propagation=True,
    tags=platform_config.tags,
)
