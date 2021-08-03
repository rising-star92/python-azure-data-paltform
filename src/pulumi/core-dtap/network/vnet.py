from pulumi.resource import ResourceOptions
import pulumi_azure_native as azure_native

from config import platform as p
from config import helpers as h

from management import resource_groups

from . import nat
from . import routing
from . import nsg

# ----------------------------------------------------------------------------------------------------------------------
# VNET
# ----------------------------------------------------------------------------------------------------------------------
vnet_config = p.config_object["network"]["virtual_network"]
vnet_address_space = vnet_config["address_space"]
vnet_name = p.generate_name("virtual_network", "main")

vnet = azure_native.network.VirtualNetwork(
    resource_name=vnet_name,
    virtual_network_name=vnet_name,
    resource_group_name=resource_groups.infra.name,
    location=p.region_long_name,
    address_space=azure_native.network.AddressSpaceArgs(
        address_prefixes=[vnet_address_space]),
    tags=p.tags,
    opts=ResourceOptions(ignore_changes=["subnets"])
)

# ----------------------------------------------------------------------------------------------------------------------
# VNET -> SUBNETS
# ----------------------------------------------------------------------------------------------------------------------

# GATEWAY SUBNET
gateway_subnet = azure_native.network.Subnet(
    resource_name=p.generate_name("subnet", "gateway"),
    subnet_name=p.generate_name("gateway_subnet", "Gateway"),
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=h.cidrsubnet(vnet_address_space, 24, 0),
    route_table=azure_native.network.RouteTableArgs(
        id=routing.main_route_table.id),
)

# PRIVATELINK SUBNET
privatelink_subnet_name = p.generate_name("subnet", "privatelink")
privatelink_subnet = azure_native.network.Subnet(
    resource_name=privatelink_subnet_name,
    subnet_name=privatelink_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=h.cidrsubnet(vnet_address_space, 24, 1),
    private_endpoint_network_policies=azure_native.network.VirtualNetworkPrivateEndpointNetworkPolicies.DISABLED,
    route_table=azure_native.network.RouteTableArgs(
        id=routing.main_route_table.id),
    opts=ResourceOptions(depends_on=[gateway_subnet]),
)

# DATABRICKS ENGINEERING HOSTS SUBNET
dbw_engineering_hosts_subnet_name = p.generate_name(
    "subnet", "dbw-eng-hosts")
dbw_engineering_hosts_subnet = azure_native.network.Subnet(
    resource_name=dbw_engineering_hosts_subnet_name,
    subnet_name=dbw_engineering_hosts_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=h.cidrsubnet(vnet_address_space, 22, 1),
    route_table=azure_native.network.RouteTableArgs(
        id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_engineering.id),
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
    opts=ResourceOptions(depends_on=[privatelink_subnet]),
)

# DATABRICKS ENGINEERING CONTAINERS SUBNET
dbw_engineering_containers_subnet_name = p.generate_name(
    "subnet", "dbw-eng-cont")
dbw_engineering_containers_subnet = azure_native.network.Subnet(
    resource_name=dbw_engineering_containers_subnet_name,
    subnet_name=dbw_engineering_containers_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=h.cidrsubnet(vnet_address_space, 22, 2),
    route_table=azure_native.network.RouteTableArgs(
        id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_engineering.id),
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
    opts=ResourceOptions(depends_on=[dbw_engineering_hosts_subnet]),
)

# DATABRICKS ANALYTICS HOSTS SUBNET
dbw_analytics_hosts_subnet_name = p.generate_name(
    "subnet", "dbw-atc-hosts")
dbw_analytics_hosts_subnet = azure_native.network.Subnet(
    resource_name=dbw_analytics_hosts_subnet_name,
    subnet_name=dbw_analytics_hosts_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=h.cidrsubnet(vnet_address_space, 22, 3),
    route_table=azure_native.network.RouteTableArgs(
        id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_analytics.id),
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
    opts=ResourceOptions(
        depends_on=[dbw_engineering_containers_subnet]),
)

# DATABRICKS ANALYTICS CONTAINERS SUBNET
dbw_analytics_containers_subnet_name = p.generate_name(
    "subnet", "dbw-atc-cont")
dbw_analytics_containers_subnet = azure_native.network.Subnet(
    resource_name=dbw_analytics_containers_subnet_name,
    subnet_name=dbw_analytics_containers_subnet_name,
    resource_group_name=resource_groups.infra.name,
    virtual_network_name=vnet.name,
    address_prefix=h.cidrsubnet(vnet_address_space, 22, 4),
    route_table=azure_native.network.RouteTableArgs(
        id=routing.main_route_table.id),
    network_security_group=azure_native.network.NetworkSecurityGroupArgs(
        id=nsg.databricks_analytics.id),
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
    opts=ResourceOptions(depends_on=[dbw_analytics_hosts_subnet]),
)
