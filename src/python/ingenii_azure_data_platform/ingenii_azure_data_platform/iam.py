import pulumi
from pulumi.output import Output
from typing import Union
import pulumi_azure_native as azure_native
from ingenii_azure_data_platform.utils import generate_hash


class RoleAssignment(azure_native.authorization.RoleAssignment):
    """
    #TODO
    """

    _role_definitions = {
        k: f"/providers/Microsoft.Authorization/roleDefinitions/{v}"
        for k, v in {
            # General
            "Owner": "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
            "Contributor": "b24988ac-6180-42a0-ab88-20f7382dd24c",
            "Reader": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
            # Key Vault
            "Key Vault Administrator": "00482a5a-887f-4fb3-b363-3b7fe8e74483",
            "Key Vault Contributor": "f25e0fa2-a7c8-4377-a976-54943a77a395",
            "Key Vault Secrets Officer": "b86a8fe4-44ce-4948-aee5-eccb2c155cd7",
            "Key Vault Secrets User": "4633458b-17de-408a-b874-0445c86b69e6",
            # Storage
            "Reader and Data Access": "c12c1c16-33a1-487b-954d-41c89c60f349",
            "Storage Account Key Operator Service Role": "81a9662b-bebf-436f-a333-f67b29880f12",
            "Storage Blob Data Owner": "b7e6dc6d-f1e8-4753-8033-0f276bb0955b",
            "Storage Blob Data Contributor": "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
            "Storage Blob Data Reader": "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
            "Storage Blob Delegator": "db58b8e5-c6ad-4a2a-8342-4190687cbf4a",
            # Data Factory
            "Data Factory Contributor": "673868aa-7521-48a0-acc6-0f60742d39f5",
            # Container Registry
            "Container Registry Delete": "c2f4ef07-c644-48eb-af81-4b1b4947fb11",
            "Container Registry Image Signer": "6cef56e8-d556-48e5-a04f-b8e64114680f",
            "Container Registry Pull": "7f951dda-4ed3-4680-a7ca-43fe172d538d",
            "Container Registry Push": "8311e382-0749-4cb8-b61a-304f252e45ec",
            "Container Registry Quarantine Reader": "cdda3590-29a3-44f6-95f2-9f980659eb04",
            "Container Registry Quarantine Writer": "c8d4ff99-41c3-41a8-9f60-21dfdad59608",
            # Kubernetes
            "Azure Kubernetes Service Cluster Admin Role": "0ab0b1a8-8aac-4efd-b8c2-3ee1fb270be8",
            "Azure Kubernetes Service Cluster User Role": "4abbcc35-e782-43d8-92c5-2d3f1bd2253f",
            "Azure Kubernetes Service Contributor Role": "ed7f3fbd-7b88-4dd4-9017-9adb7ce333f8",
            "Azure Kubernetes Service RBAC Admin": "3498e952-d568-435e-9b2c-8d77e338d7f7",
            "Azure Kubernetes Service RBAC Cluster Admin": "b1ff04bb-8a4e-4dc4-8eb5-8693973ce19b",
            "Azure Kubernetes Service RBAC Reader": "7f6c6a51-bcf8-42ba-9220-52d62157d7db",
            "Azure Kubernetes Service RBAC Writer": "a7ffa36f-339b-4b5c-8bdf-e2c188b2c0eb",
        }.items()
    }

    def __init__(
        self,
        principal_name: str,
        principal_type: str,
        principal_id: Union[str, Output[str]],
        role_name: str,
        scope: Union[str, Output[str]],
        scope_description: str,
    ) -> None:

        if role_name not in self._role_definitions:
            raise ValueError(
                f"The role name {role_name} is not yet supported by this class or not a valid Azure role name."
            )

        resource_name = "-".join([
            f"{title}-[{name}]"
            for title, name in
            (
                ("principal", principal_name),
                ("type", principal_type),
                ("role", role_name),
                ("to", scope_description)
            )
        ]).lower().replace(" ", "-")

        super().__init__(
            resource_name=resource_name,
            principal_id=principal_id,
            scope=scope,
            role_definition_id=self._role_definitions[role_name],
            principal_type=principal_type,
            opts=pulumi.ResourceOptions(delete_before_replace=True),
        )


class UserRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        scope: Union[str, Output[str]],
        scope_description: str,
        principal_name: str,
        principal_id: Union[str, Output[str]],
    ) -> None:
        super().__init__(
            principal_name=principal_name,
            principal_id=principal_id,
            principal_type="User",
            role_name=role_name,
            scope=scope,
            scope_description=scope_description,
        )


class GroupRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        principal_name: str,
        principal_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
        scope_description: str,
    ) -> None:
        super().__init__(
            principal_id=principal_id,
            principal_name=principal_name,
            principal_type="Group",
            role_name=role_name,
            scope=scope,
            scope_description=scope_description,
        )


class ServicePrincipalRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        principal_name: str,
        principal_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
        scope_description: str,
    ) -> None:
        super().__init__(
            principal_name=principal_name,
            principal_id=principal_id,
            principal_type="ServicePrincipal",
            role_name=role_name,
            scope=scope,
            scope_description=scope_description,
        )


class UserAssignedIdentityRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        principal_name: str,
        principal_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
        scope_description: str,
    ) -> None:
        super().__init__(
            role_name=role_name,
            principal_name=principal_name,
            principal_id=principal_id,
            principal_type="ServicePrincipal",
            scope=scope,
            scope_description=scope_description,
        )
