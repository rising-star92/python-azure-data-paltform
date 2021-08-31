import pulumi_azure_native as azure_native

from ingenii_azure_data_platform.iam import ServicePrincipalRoleAssignment
from ingenii_azure_data_platform.utils import generate_resource_name

from config import platform_config
from management import resource_groups
from storage.datalake import datalake
from security import credentials_store
from analytics.databricks.workspaces import engineering as databricks_engineering

# ----------------------------------------------------------------------------------------------------------------------
# ORCHESTRATION DATA FACTORY
# ----------------------------------------------------------------------------------------------------------------------
datafactory_config = platform_config.yml_config["analytics_services"]["datafactory"][
    "factories"
]["orchestration"]

datafactory_name = generate_resource_name(
    resource_type="datafactory",
    resource_name=datafactory_config["display_name"],
    platform_config=platform_config,
)

datafactory = azure_native.datafactory.Factory(
    resource_name=datafactory_name,
    factory_name=datafactory_name,
    location=platform_config.region.long_name,
    resource_group_name=resource_groups.infra.name,
    identity=azure_native.datafactory.FactoryIdentityArgs(
        type=azure_native.datafactory.FactoryIdentityType.SYSTEM_ASSIGNED
    ),
)

# ----------------------------------------------------------------------------------------------------------------------
# LINKED SERVICES
# ----------------------------------------------------------------------------------------------------------------------

# DATALAKE
# Datafactory Access to Data Lake
datafactory_acccess_to_datalake = ServicePrincipalRoleAssignment(
    role_name="Storage Blob Data Contributor",
    service_principal_object_id=datafactory.identity.principal_id,
    scope=datalake.id,
)

datalake_linked_service = azure_native.datafactory.LinkedService(
    resource_name=f"{datafactory_name}-link-to-datalake",
    factory_name=datafactory.name,
    linked_service_name="DataLake",
    properties=azure_native.datafactory.AzureBlobFSLinkedServiceArgs(
        url=datalake.primary_endpoints.dfs,
        description="Managed by Ingenii Data Platform",
        type="AzureBlobFS",
    ),
    resource_group_name=resource_groups.infra.name,
)

# CREDENTIALS STORE
# Datafactory Access to Credentials Store (Key Vault)
datafactory_acccess_to_credentials_store = ServicePrincipalRoleAssignment(
    role_name="Key Vault Secrets Reader",
    service_principal_object_id=datafactory.identity.principal_id,
    scope=credentials_store.key_vault.id,
)

credentials_store_linked_service = azure_native.datafactory.LinkedService(
    resource_name=f"{datafactory_name}-link-to-credentials-store",
    factory_name=datafactory.name,
    linked_service_name="Credentials Store",
    properties=azure_native.datafactory.AzureKeyVaultLinkedServiceArgs(
        base_url=f"https://{credentials_store.key_vault_name}.vault.azure.net",
        description="Managed by Ingenii Data Platform",
        type="AzureKeyVault",
    ),
    resource_group_name=resource_groups.infra.name,
)  # type: ignore

# DATABRICKS ENGINEERING - DELTA LAKE
databricks_engineering_delta_linked_service = azure_native.datafactory.LinkedService(
    resource_name=f"{datafactory_name}-link-to-databricks-engineering-delta",
    factory_name=datafactory.name,
    linked_service_name="Databricks Engineering Delta",
    properties=azure_native.datafactory.AzureDatabricksDeltaLakeLinkedServiceArgs(
        domain=databricks_engineering.workspace.workspace_url,
        access_token=databricks_engineering.datafactory_token.token_value,
        cluster_id=databricks_engineering.clusters["default"].id,
        description="Managed by Ingenii Data Platform",
        type="AzureDatabricksDeltaLake",
    ),
    resource_group_name=resource_groups.infra.name,
)  # type: ignore


# DATABRICKS ENGINEERING - COMPUTE
databricks_engineering_compute_linked_service = azure_native.datafactory.LinkedService(
    resource_name=f"{datafactory_name}-link-to-databricks-engineering-compute",
    factory_name=datafactory.name,
    linked_service_name="Databricks Engineering Compute",
    properties=azure_native.datafactory.AzureDatabricksLinkedServiceArgs(
        domain=databricks_engineering.workspace.workspace_url,
        access_token=databricks_engineering.datafactory_token.token_value,
        existing_cluster_id=databricks_engineering.clusters["default"].id,
        workspace_resource_id=databricks_engineering.workspace.id,
        description="Managed by Ingenii Data Platform",
        type="AzureDatabricks",
    ),
    resource_group_name=resource_groups.infra.name,
)  # type: ignore
