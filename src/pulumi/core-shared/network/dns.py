import pulumi_azure_native as azure_native

from project_config import platform_config
from management import resource_groups

from .vnet import vnet

# ----------------------------------------------------------------------------------------------------------------------
# KEYVAULT PRIVATE DNS ZONE
# ----------------------------------------------------------------------------------------------------------------------
key_vault_private_dns_zone = azure_native.network.PrivateZone(
    resource_name="privatelink-vaultcore-azure-net",
    location="Global",
    private_zone_name="privatelink.vaultcore.azure.net",
    resource_group_name=resource_groups["infra"].name,
    tags=platform_config.tags,
)

key_vault_private_dns_zone_link = azure_native.network.VirtualNetworkLink(
    resource_name="privatelink-vaultcore-azure-net",
    virtual_network_link_name=vnet.name,
    location="Global",
    private_zone_name=key_vault_private_dns_zone.name,
    registration_enabled=False,
    resource_group_name=resource_groups["infra"].name,
    tags=platform_config.tags,
    virtual_network=azure_native.network.SubResourceArgs(
        id=vnet.id,
    ),
)
