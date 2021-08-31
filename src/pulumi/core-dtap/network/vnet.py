import pulumi
import pulumi_azure_native as azure_native
from ingenii_azure_data_platform.utils import generate_resource_name, generate_cidr

from config import platform_config
from management import resource_groups

from . import nat
from . import routing
from . import nsg

# ----------------------------------------------------------------------------------------------------------------------
# VNET
# ----------------------------------------------------------------------------------------------------------------------
vnet_config = platform_config.yml_config["network"]["virtual_network"]
vnet_address_space = vnet_config["address_space"]
vnet_name = generate_resource_name(
    resource_type="virtual_network",
    resource_name="main",
    platform_config=platform_config,
)

vnet = azure_native.network.VirtualNetwork(
    resource_name=vnet_name,
    virtual_network_name=vnet_name,
    resource_group_name=resource_groups.infra.name,
    location=platform_config.region.long_name,
    address_space=azure_native.network.AddressSpaceArgs(
        address_prefixes=[vnet_address_space]
    ),
    tags=platform_config.tags,
    # Tags are added in the ignore_changes list because of:
    # https://github.com/ingenii-solutions/azure-data-platform/issues/71
    opts=pulumi.ResourceOptions(ignore_changes=["subnets", "tags"]),
)

# ----------------------------------------------------------------------------------------------------------------------
# VNET -> SUBNETS
# ----------------------------------------------------------------------------------------------------------------------

# GATEWAY SUBNET
gateway_subnet = azure_native.network.Subnet(
    resource_name=generate_resource_name(
        resource_type="subnet", resource_name="gateway", platform_config=platform_config
    ),
    subnet_name="Gateway",  # Microsoft requires the Gateway subnet to be called "Gateway"
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 24, 0),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
)

# PRIVATELINK SUBNET
privatelink_subnet_name = generate_resource_name(
    resource_type="subnet", resource_name="privatelink", platform_config=platform_config
)
privatelink_subnet = azure_native.network.Subnet(
    resource_name=privatelink_subnet_name,
    subnet_name=privatelink_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 24, 1),
    private_endpoint_network_policies=azure_native.network.VirtualNetworkPrivateEndpointNetworkPolicies.DISABLED,
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    opts=pulumi.ResourceOptions(depends_on=[gateway_subnet]),
)

# HOSTED SERVICES SUBNET
hosted_services_subnet_name = generate_resource_name(
    resource_type="subnet",
    resource_name="hosted-services",
    platform_config=platform_config,
)
hosted_services_subnet = azure_native.network.Subnet(
    resource_name=privatelink_subnet_name,
    subnet_name=privatelink_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 24, 2),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    nat_gateway=nat.gateway_id,
    service_endpoints=[
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.Storage",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.KeyVault",
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=[privatelink_subnet]),
)

# DATABRICKS ENGINEERING HOSTS SUBNET
dbw_engineering_hosts_subnet_name = generate_resource_name(
    resource_type="subnet",
    resource_name="dbw-eng-hosts",
    platform_config=platform_config,
)
dbw_engineering_hosts_subnet = azure_native.network.Subnet(
    resource_name=dbw_engineering_hosts_subnet_name,
    subnet_name=dbw_engineering_hosts_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 22, 1),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_engineering.id
    ),
    nat_gateway=nat.gateway_id,
    service_endpoints=[
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.Storage",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.KeyVault",
        ),
    ],
    delegations=[
        azure_native.network.DelegationArgs(
            name="databricks", service_name="Microsoft.Databricks/workspaces"
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[hosted_services_subnet]),
)

# DATABRICKS ENGINEERING CONTAINERS SUBNET
dbw_engineering_containers_subnet_name = generate_resource_name(
    resource_type="subnet",
    resource_name="dbw-eng-cont",
    platform_config=platform_config,
)
dbw_engineering_containers_subnet = azure_native.network.Subnet(
    resource_name=dbw_engineering_containers_subnet_name,
    subnet_name=dbw_engineering_containers_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 22, 2),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_engineering.id
    ),
    nat_gateway=nat.gateway_id,
    service_endpoints=[
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.Storage",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.KeyVault",
        ),
    ],
    delegations=[
        azure_native.network.DelegationArgs(
            name="databricks", service_name="Microsoft.Databricks/workspaces"
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[dbw_engineering_hosts_subnet]),
)

# DATABRICKS ANALYTICS HOSTS SUBNET
dbw_analytics_hosts_subnet_name = generate_resource_name(
    resource_type="subnet",
    resource_name="dbw-atc-hosts",
    platform_config=platform_config,
)
dbw_analytics_hosts_subnet = azure_native.network.Subnet(
    resource_name=dbw_analytics_hosts_subnet_name,
    subnet_name=dbw_analytics_hosts_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 22, 3),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_analytics.id
    ),
    nat_gateway=nat.gateway_id,
    service_endpoints=[
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.Storage",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.KeyVault",
        ),
    ],
    delegations=[
        azure_native.network.DelegationArgs(
            name="databricks", service_name="Microsoft.Databricks/workspaces"
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[dbw_engineering_containers_subnet]),
)

# DATABRICKS ANALYTICS CONTAINERS SUBNET
dbw_analytics_containers_subnet_name = generate_resource_name(
    resource_type="subnet",
    resource_name="dbw-atc-cont",
    platform_config=platform_config,
)
dbw_analytics_containers_subnet = azure_native.network.Subnet(
    resource_name=dbw_analytics_containers_subnet_name,
    subnet_name=dbw_analytics_containers_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 22, 4),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_analytics.id
    ),
    nat_gateway=nat.gateway_id,
    service_endpoints=[
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.Storage",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.KeyVault",
        ),
    ],
    delegations=[
        azure_native.network.DelegationArgs(
            name="databricks", service_name="Microsoft.Databricks/workspaces"
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[dbw_analytics_hosts_subnet]),
)
