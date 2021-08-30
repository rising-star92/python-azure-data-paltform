import pulumi_azure_native as azure_native
from pulumi.output import Output
from ingenii_azure_data_platform.utils import generate_resource_name

from config import platform_config
from management import resource_groups

# ----------------------------------------------------------------------------------------------------------------------
# NAT GATEWAY
# ----------------------------------------------------------------------------------------------------------------------
gateway_config = platform_config.yml_config["network"]["nat_gateway"]


def create_gateway_public_ip(
    resource_name: str, display_name: str, resource_group_name: Output[str]
):
    return azure_native.network.PublicIPAddress(
        resource_name,
        idle_timeout_in_minutes=10,
        public_ip_address_name=display_name,
        public_ip_address_version="IPv4",
        public_ip_allocation_method="Static",
        resource_group_name=resource_group_name,
        sku=azure_native.network.PublicIPAddressSkuArgs(name="Standard"),
    )


def create_gateway(
    resource_name: str,
    display_name: str,
    resource_group_name: Output[str],
    public_ip_address_id: Output[str],
):
    return azure_native.network.NatGateway(
        resource_name,
        nat_gateway_name=display_name,
        public_ip_addresses=[
            azure_native.network.SubResourceArgs(
                id=public_ip_address_id,
            )
        ],
        resource_group_name=resource_group_name,
        sku=azure_native.network.NatGatewaySkuArgs(
            name="Standard",
        ),
    )


gateway_id = None

if gateway_config.get("enabled"):

    gateway_public_ip_resource_name = generate_resource_name(
        resource_type="public_ip",
        resource_name="for-ngw-main",
        platform_config=platform_config,
    )
    gateway_public_ip = create_gateway_public_ip(
        resource_name=gateway_public_ip_resource_name,
        display_name=gateway_public_ip_resource_name,
        resource_group_name=resource_groups.infra.name,
    )

    gateway_resource_name = generate_resource_name(
        resource_type="nat_gateway",
        resource_name="main",
        platform_config=platform_config,
    )
    gateway = create_gateway(
        resource_name=gateway_resource_name,
        display_name=gateway_resource_name,
        resource_group_name=resource_groups.infra.name,
        public_ip_address_id=gateway_public_ip.id,
    )

    gateway_id = azure_native.network.SubResourceArgs(id=gateway.id)

else:
    gateway_id = None
