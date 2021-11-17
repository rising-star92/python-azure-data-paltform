from os import getenv

from pulumi_azure_native import Provider

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
