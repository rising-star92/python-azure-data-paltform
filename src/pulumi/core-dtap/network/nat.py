import pulumi_azure_native as azure_native

from config import platform as p

from management import resource_groups

# ----------------------------------------------------------------------------------------------------------------------
# NAT GATEWAY
# ----------------------------------------------------------------------------------------------------------------------
gateway_config = p.config_object["network"]["nat_gateway"]


def create_gateway_public_ip(
    resource_name: str,
    display_name: str,
    resource_group_name: str
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
    resource_group_name: str,
    public_ip_address_id: str
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


if gateway_config.get("enabled"):

    gateway_public_ip_resource_name = p.generate_name(
        "public_ip", "for-ngw-main")
    gateway_public_ip = create_gateway_public_ip(
        resource_name=gateway_public_ip_resource_name,
        display_name=gateway_public_ip_resource_name,
        resource_group_name=resource_groups.infra.name
    )

    gateway_resource_name = p.generate_name("nat_gateway", "main")
    gateway = create_gateway(
        resource_name=gateway_resource_name,
        display_name=gateway_resource_name,
        resource_group_name=resource_groups.infra.name,
        public_ip_address_id=gateway_public_ip.id
    )

gateway_id = azure_native.network.SubResourceArgs(
    id=gateway.id) if gateway_config.get("enabled") else None
