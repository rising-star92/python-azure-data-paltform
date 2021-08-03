import pulumi_azure_native as azure_native

from config import platform as p

from management import resource_groups

from . import vnet

# ----------------------------------------------------------------------------------------------------------------------
# STORAGE BLOB PRIVATE DNS ZONE
# ----------------------------------------------------------------------------------------------------------------------
storage_blob_private_dns_zone = azure_native.network.PrivateZone(
    resource_name="privatelink-blob-core-windows-net",
    location="Global",
    private_zone_name="privatelink.blob.core.windows.net",
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
)

storage_blob_private_dns_zone_link = azure_native.network.VirtualNetworkLink(
    resource_name="privatelink-blob-core-windows-net",
    virtual_network_link_name=vnet.vnet.name,
    location="Global",
    private_zone_name=storage_blob_private_dns_zone.name,
    registration_enabled=False,
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
    virtual_network=azure_native.network.SubResourceArgs(
        id=vnet.vnet.id,
    ),
)

# ----------------------------------------------------------------------------------------------------------------------
# STORAGE DFS PRIVATE DNS ZONE
# ----------------------------------------------------------------------------------------------------------------------
storage_dfs_private_dns_zone = azure_native.network.PrivateZone(
    resource_name="privatelink-dfs-core-windows-net",
    location="Global",
    private_zone_name="privatelink.dfs.core.windows.net",
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
)

storage_dfs_private_dns_zone_link = azure_native.network.VirtualNetworkLink(
    resource_name="privatelink-dfs-core-windows-net",
    virtual_network_link_name=vnet.vnet.name,
    location="Global",
    private_zone_name=storage_dfs_private_dns_zone.name,
    registration_enabled=False,
    resource_group_name=resource_groups.infra.name,
    virtual_network=azure_native.network.SubResourceArgs(
        id=vnet.vnet.id,
    ),
    tags=p.tags,
)

# ----------------------------------------------------------------------------------------------------------------------
# KEYVAULT PRIVATE DNS ZONE
# ----------------------------------------------------------------------------------------------------------------------
key_vault_private_dns_zone = azure_native.network.PrivateZone(
    resource_name="privatelink-vaultcore-azure-net",
    location="Global",
    private_zone_name="privatelink.vaultcore.azure.net",
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
)

key_vault_private_dns_zone_link = azure_native.network.VirtualNetworkLink(
    resource_name="privatelink-vaultcore-azure-net",
    virtual_network_link_name=vnet.vnet.name,
    location="Global",
    private_zone_name=key_vault_private_dns_zone.name,
    registration_enabled=False,
    resource_group_name=resource_groups.infra.name,
    tags=p.tags,
    virtual_network=azure_native.network.SubResourceArgs(
        id=vnet.vnet.id,
    )
)
