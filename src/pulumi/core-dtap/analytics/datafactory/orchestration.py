import pulumi_azure_native as azure_native
from config import platform as p
from management import resource_groups
from analytics.databricks.workspaces import engineering as databricks_engineering
from storage.datalake import datalake, datalake_name

# ----------------------------------------------------------------------------------------------------------------------
# ORCHESTRATION DATA FACTORY
# ----------------------------------------------------------------------------------------------------------------------
datafactory_config = p.config_object["analytics_services"]["datafactory"]["factories"]["orchestration"]
datafactory_name = p.generate_name(
    "datafactory", datafactory_config["display_name"])

datafactory = azure_native.datafactory.Factory(
    resource_name=datafactory_name,
    factory_name=datafactory_name,
    location=p.region_long_name,
    resource_group_name=resource_groups.infra.name,
    identity=azure_native.datafactory.FactoryIdentityArgs(
        type=azure_native.datafactory.FactoryIdentityType.SYSTEM_ASSIGNED)
)

# ----------------------------------------------------------------------------------------------------------------------
# LINKED SERVICES
# ----------------------------------------------------------------------------------------------------------------------

# DATALAKE
datafactory_access_to_datalake = azure_native.authorization.RoleAssignment(
    resource_name=p.generate_hash(
        datafactory_name, datalake_name, p.azure_iam_role_definitions["Storage Blob Data Contributor"]),
    principal_id=datafactory.identity.principal_id,
    principal_type="ServicePrincipal",
    role_definition_id=p.azure_iam_role_definitions["Storage Blob Data Contributor"],
    scope=datalake.id
)

datalake_linked_service = azure_native.datafactory.LinkedService(
    resource_name=f"{datafactory_name}-link-to-datalake",
    factory_name=datafactory.name,
    linked_service_name="DataLake",
    properties=azure_native.datafactory.AzureBlobFSLinkedServiceArgs(
        url=datalake.primary_endpoints.dfs,
        description="Managed by Ingenii Data Platform",
        type="AzureBlobFS"
    ),
    resource_group_name=resource_groups.infra.name
)

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
        type="AzureDatabricksDeltaLake"
    ),
    resource_group_name=resource_groups.infra.name
)


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
        type="AzureDatabricks"
    ),
    resource_group_name=resource_groups.infra.name
)
