from pulumi import ResourceOptions, log, Output
from pulumi_azure_native import network as net

from ingenii_azure_data_platform.iam import ServicePrincipalRoleAssignment
from ingenii_azure_data_platform.network import get_private_endpoint_ip_addr_and_fqdn
from ingenii_azure_data_platform.utils import generate_resource_name, lock_resource

from management.resource_groups import resource_groups
from network.vnet import vnet, privatelink_subnet
from network.dns import container_registry_dns_zone
from project_config import platform_config, azure_client
from platform_shared import (
    SHARED_OUTPUTS,
    container_registry_configs,
    container_registry_private_endpoint_configs,
    shared_services_provider,
)

# ----------------------------------------------------------------------------------------------------------------------
# CONTAINER REGISTRY PRIVATE ENDPOINTS
# ----------------------------------------------------------------------------------------------------------------------

for ref_key, config in container_registry_private_endpoint_configs.items():

    registry_name = container_registry_configs[ref_key]["display_name"]
    registry_sku = container_registry_configs[ref_key]["sku"]

    # Check the registry SKU. Create an endpoint for "premium" SKUs only.
    if registry_sku != "premium":
        log.warn(
            f"Unable to create PrivateLink endpoint for the container registry {registry_name}. "
            f"Only 'premium' SKU suppots PrivateLink. The current registry SKU is '{registry_sku}'."
        )
        continue

    container_registry_resource_id = SHARED_OUTPUTS.get(
        "storage",
        "container_registry",
        ref_key,
        "id",
        preview="Preview Container Registry ID",
    )

    container_registry_role_definition_id = SHARED_OUTPUTS.get(
        "iam",
        "role_definitions",
        "container_registry_private_endpoint_connection_approver",
        "id",
        preview="/subscriptions/preview-only/providers/Microsoft.Authorization/roleDefinitions/preview-only",
    )

    role_assignment = ServicePrincipalRoleAssignment(
        principal_id=azure_client.client_id,
        principal_name=f"{platform_config.stack_short_name}-provider",
        role_id=container_registry_role_definition_id,
        scope=container_registry_resource_id,
        scope_description=f"container-registry-{ref_key}",
        opts=ResourceOptions(provider=shared_services_provider),
    )

    resource_group_name = resource_groups["infra"].name

    endpoint_name = generate_resource_name(
        resource_type="private_endpoint",
        resource_name=f"for-container-registry-{ref_key}",
        platform_config=platform_config,
    )

    endpoint = net.PrivateEndpoint(
        resource_name=endpoint_name,
        private_endpoint_name=endpoint_name,
        location=platform_config.region.long_name,
        private_link_service_connections=[
            net.PrivateLinkServiceConnectionArgs(
                group_ids=["registry"],
                name=vnet.name,
                private_link_service_id=container_registry_resource_id,
                request_message="none",
            )
        ],
        resource_group_name=resource_group_name,
        subnet=net.SubnetArgs(id=privatelink_subnet.id),
        tags=platform_config.tags,
        opts=ResourceOptions(depends_on=[role_assignment]),
    )
    if platform_config.resource_protection:
        lock_resource(endpoint_name, endpoint.id)

    endpoint_ip_and_fqdn = Output.all(
        resource_group_name=resource_group_name, endpoint=endpoint
    ).apply(
        lambda args: get_private_endpoint_ip_addr_and_fqdn(
            args["endpoint"], args["resource_group_name"]
        )
    )

    def create_record_sets(record_sets):
        for entry in record_sets:
            net.PrivateRecordSet(
                resource_name=f"{entry['fqdn'].replace('.','-')}-{ref_key}",
                a_records=[net.ARecordArgs(ipv4_address=entry["ip_address"])],
                relative_record_set_name=entry["fqdn"].split(".azurecr.io")[0],
                record_type="A",
                ttl=3600,
                private_zone_name=container_registry_dns_zone.name,
                resource_group_name=resource_group_name,
            )

    endpoint_ip_and_fqdn.apply(create_record_sets)
