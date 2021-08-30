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
        # General
        "Owner": "/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635",
        "Contributor": "/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
        "Reader": "/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7",
        # Key Vault
        "Key Vault Administrator": "/providers/Microsoft.Authorization/roleDefinitions/00482a5a-887f-4fb3-b363-3b7fe8e74483",
        "Key Vault Secrets Reader": "/providers/Microsoft.Authorization/roleDefinitions/4633458b-17de-408a-b874-0445c86b69e6",
        # Storage
        "Storage Blob Data Owner": "/providers/Microsoft.Authorization/roleDefinitions/b7e6dc6d-f1e8-4753-8033-0f276bb0955b",
        "Storage Blob Data Contributor": "/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe",
        "Storage Blob Data Reader": "/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
        "Storage Blob Delegator": "/providers/Microsoft.Authorization/roleDefinitions/db58b8e5-c6ad-4a2a-8342-4190687cbf4a",
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
