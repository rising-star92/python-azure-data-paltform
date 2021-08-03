import pulumi_azure_native as azure_native

from config import platform as p

from management import resource_groups

# ----------------------------------------------------------------------------------------------------------------------
# MAIN ROUTE TABLE
# ----------------------------------------------------------------------------------------------------------------------
main_route_table_resource_name = p.generate_name("route_table", "main")
main_route_table = azure_native.network.RouteTable(
    resource_name=main_route_table_resource_name,
    route_table_name=main_route_table_resource_name,
    resource_group_name=resource_groups.infra.name,
    disable_bgp_route_propagation=True,
    tags=p.tags,
)
