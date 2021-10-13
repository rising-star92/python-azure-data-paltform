import pulumi
import pulumi_azure_native as azure_native
from ingenii_azure_data_platform.utils import generate_resource_name, generate_cidr

from project_config import platform_config, platform_outputs
from management import resource_groups

from . import nat
from . import routing
from . import nsg

outputs = platform_outputs["network"]

# ----------------------------------------------------------------------------------------------------------------------
# VNET
# ----------------------------------------------------------------------------------------------------------------------
vnet_config = platform_config.from_yml["network"]["virtual_network"]
vnet_address_space = vnet_config["address_space"]
vnet_name = generate_resource_name(
    resource_type="virtual_network",
    resource_name="main",
    platform_config=platform_config,
)

vnet = azure_native.network.VirtualNetwork(
    resource_name=vnet_name,
    virtual_network_name=vnet_name,
    resource_group_name=resource_groups["infra"].name,
    location=platform_config.region.long_name,
    address_space=azure_native.network.AddressSpaceArgs(
        address_prefixes=[vnet_address_space]
    ),
    tags=platform_config.tags,
    # Tags are added in the ignore_changes list because of:
    # https://github.com/ingenii-solutions/azure-data-platform/issues/71
    opts=pulumi.ResourceOptions(ignore_changes=["subnets", "tags"]),
)

# Export VNET metadata
outputs["virtual_network"] = {
    "name": vnet.name,
    "address_space": vnet.address_space,
    "id": vnet.id,
}

# ----------------------------------------------------------------------------------------------------------------------
# VNET -> SUBNETS
# ----------------------------------------------------------------------------------------------------------------------

# TODO: Remove duplication. Keep it DRY.

subnet_outputs = outputs["virtual_network"]["subnets"] = {}

# GATEWAY SUBNET
gateway_subnet = azure_native.network.Subnet(
    resource_name=generate_resource_name(
        resource_type="subnet", resource_name="gateway", platform_config=platform_config
    ),
    subnet_name="Gateway",  # Microsoft requires the Gateway subnet to be called "Gateway"
    resource_group_name=resource_groups["infra"].name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 24, 0),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
)

# Export subnet metadata
subnet_outputs["gateway"] = {
    "name": gateway_subnet.name,
    "id": gateway_subnet.id,
    "address_prefix": gateway_subnet.address_prefix,
}

# PRIVATELINK SUBNET
privatelink_subnet_name = generate_resource_name(
    resource_type="subnet", resource_name="privatelink", platform_config=platform_config
)
privatelink_subnet = azure_native.network.Subnet(
    resource_name=privatelink_subnet_name,
    subnet_name=privatelink_subnet_name,
    resource_group_name=resource_groups["infra"].name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 24, 1),
    private_endpoint_network_policies=azure_native.network.VirtualNetworkPrivateEndpointNetworkPolicies.DISABLED,
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    opts=pulumi.ResourceOptions(depends_on=[gateway_subnet]),
)

# Export subnet metadata
subnet_outputs["privatelink"] = {
    "name": privatelink_subnet.name,
    "id": privatelink_subnet.id,
    "address_prefix": privatelink_subnet.address_prefix,
}

# HOSTED SERVICES SUBNET
hosted_services_subnet_name = generate_resource_name(
    resource_type="subnet",
    resource_name="hosted-services",
    platform_config=platform_config,
)
hosted_services_subnet = azure_native.network.Subnet(
    resource_name=hosted_services_subnet_name,
    subnet_name=hosted_services_subnet_name,
    resource_group_name=resource_groups["infra"].name,
    virtual_network_name=vnet.name,
    address_prefix=generate_cidr(vnet_address_space, 24, 2),
    route_table=azure_native.network.RouteTableArgs(id=routing.main_route_table.id),
    nat_gateway=azure_native.network.SubResourceArgs(id=nat.gateway.id),
    service_endpoints=[
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.Storage",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.KeyVault",
        ),
        azure_native.network.ServiceEndpointPropertiesFormatArgs(
            service="Microsoft.SQL",
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=[privatelink_subnet]),
)

# Export subnet metadata
subnet_outputs["hosted_services"] = {
    "name": hosted_services_subnet.name,
    "id": hosted_services_subnet.id,
    "address_prefix": hosted_services_subnet.address_prefix,
}