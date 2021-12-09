from os import getenv
from pulumi import ResourceOptions
from pulumi_azure_native import Provider, keyvault

from project_config import platform_config, SHARED_OUTPUTS

shared_services_provider = Provider(
    resource_name="shared-services",
    client_id=getenv("SHARED_ARM_CLIENT_ID"),
    client_secret=getenv("SHARED_ARM_CLIENT_SECRET"),
    tenant_id=getenv("SHARED_ARM_TENANT_ID"),
    subscription_id=getenv("SHARED_ARM_SUBSCRIPTION_ID"),
)


def get_devops_principal_id():
    return SHARED_OUTPUTS["automation"]["deployment_user_assigned_identities"][
        platform_config.stack
    ]


def get_devops_config_registry():
    return SHARED_OUTPUTS["security"]["config_registry"]


def get_devops_config_registry_resource_group():
    return get_devops_config_registry()["key_vault_id"].apply(
        lambda id_str: id_str.split("/")[4]
    )


def add_config_registry_secret(secret_name, secret_value, resource_name=None):
    keyvault.Secret(
        resource_name=resource_name or f"devops-{secret_name}",
        resource_group_name=get_devops_config_registry_resource_group(),
        vault_name=get_devops_config_registry()["key_vault_name"],
        secret_name=f"{secret_name}-{platform_config.stack}",
        properties=keyvault.SecretPropertiesArgs(value=secret_value),
        opts=ResourceOptions(provider=shared_services_provider),
    )
