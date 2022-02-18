from pulumi_azure_native import authorization as auth

from storage import container_registry as cr
from project_config import platform_outputs

outputs = platform_outputs["iam"]["role_definitions"] = {}

if cr.registries.items():
    container_registry_role_def = auth.RoleDefinition(
        "container-registry-private-endpoint-connection-creator",
        role_name="ContainerRegistryPrivateEndpointConnectionCreator",
        permissions=[
            auth.PermissionArgs(
                actions=[
                    "Microsoft.ContainerRegistry/registries/privateEndpointConnections/write",
                    "Microsoft.ContainerRegistry/registries/privateEndpointConnections/delete",
                    "Microsoft.ContainerRegistry/registries/privateEndpointConnections/read"
                ]
            )
        ],
        assignable_scopes=[cr.resource_group.id],
        scope=cr.resource_group.id,
    )
    outputs["container_registry_private_endpoint_connection_creator"] = {
        "id": container_registry_role_def.id,
        "name": container_registry_role_def.role_name,
    }
