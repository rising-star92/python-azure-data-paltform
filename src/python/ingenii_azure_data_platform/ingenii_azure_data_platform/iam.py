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
        }.items()
    }

    def __init__(
        self,
        role_name: str,
        principal_type: str,
        principal_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
    ) -> None:

        if role_name not in self._role_definitions:
            raise ValueError(
                f"The role name {role_name} is not yet supported by this class or not a valid Azure role name."
            )

        super_init = super().__init__

        Output.all(principal_id, scope, role_name).apply(
            lambda args: super_init(
                resource_name=generate_hash(*args),
                principal_id=args[0],
                scope=args[1],
                role_definition_id=self._role_definitions[args[2]],
                principal_type=principal_type,
                opts=pulumi.ResourceOptions(delete_before_replace=True),
            )
        )


class UserRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        user_object_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
    ) -> None:
        super().__init__(
            role_name=role_name,
            principal_id=user_object_id,
            scope=scope,
            principal_type="User",
        )


class GroupRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        group_object_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
    ) -> None:
        super().__init__(
            role_name=role_name,
            principal_id=group_object_id,
            scope=scope,
            principal_type="Group",
        )


class ServicePrincipalRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        service_principal_object_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
    ) -> None:
        super().__init__(
            role_name=role_name,
            principal_id=service_principal_object_id,
            scope=scope,
            principal_type="ServicePrincipal",
        )


class UserAssignedIdentityRoleAssignment(RoleAssignment):
    """
    #TODO
    """

    def __init__(
        self,
        role_name: str,
        principal_id: Union[str, Output[str]],
        scope: Union[str, Output[str]],
    ) -> None:
        super().__init__(
            role_name=role_name,
            principal_id=principal_id,
            scope=scope,
            principal_type="ServicePrincipal",
        )
