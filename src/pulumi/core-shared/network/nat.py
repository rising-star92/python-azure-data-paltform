import pulumi_azure_native as azure_native
from pulumi.resource import ResourceOptions
from ingenii_azure_data_platform.logs import log_diagnostic_settings
from ingenii_azure_data_platform.utils import generate_resource_name

from logs import log_analytics_workspace
from project_config import platform_config, platform_outputs
from management import resource_groups

gateway_config = platform_config.from_yml["network"]["nat_gateway"]

outputs = platform_outputs["network"]["nat"] = {}

is_gateway_enabled = gateway_config.get("enabled", False)

if is_gateway_enabled:

    gateway_public_ip_resource_name = generate_resource_name(
        resource_type="public_ip",
        resource_name="for-ngw-main",
        platform_config=platform_config,
    )

    gateway_public_ip = azure_native.network.PublicIPAddress(
        gateway_public_ip_resource_name,
        idle_timeout_in_minutes=10,
        public_ip_address_name=gateway_public_ip_resource_name,
        public_ip_address_version="IPv4",
        public_ip_allocation_method="Static",
        resource_group_name=resource_groups["infra"].name,
        sku=azure_native.network.PublicIPAddressSkuArgs(name="Standard"),
        opts=ResourceOptions(
            protect=platform_config.resource_protection,
            ignore_changes=["nat_gateway"],
        ),
    )

    # Send diagnostic logs to Log Analytics Workspace
    public_ip_details = gateway_config.get("public_ip", {})
    log_diagnostic_settings(
        platform_config,
        log_analytics_workspace.id,
        gateway_public_ip.type,
        gateway_public_ip.id,
        gateway_public_ip_resource_name,
        logs_config=public_ip_details.get("logs", {}),
        metrics_config=public_ip_details.get("metrics", {}),
    )

    outputs["public_ip_address"] = gateway_public_ip.ip_address

    gateway_resource_name = generate_resource_name(
        resource_type="nat_gateway",
        resource_name="main",
        platform_config=platform_config,
    )

    gateway = azure_native.network.NatGateway(
        gateway_resource_name,
        nat_gateway_name=gateway_resource_name,
        public_ip_addresses=[
            azure_native.network.SubResourceArgs(
                id=gateway_public_ip.id,
            )
        ],
        resource_group_name=resource_groups["infra"].name,
        sku=azure_native.network.NatGatewaySkuArgs(
            name="Standard",
        ),
    )

    outputs["gateway"] = {"id": gateway.id, "name": gateway.name}

outputs["is_gateway_enabled"] = is_gateway_enabled
