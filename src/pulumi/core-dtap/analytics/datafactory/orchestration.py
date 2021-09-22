from pulumi import resource
from pulumi_azure_native import datafactory as adf

from ingenii_azure_data_platform.iam import (
    ServicePrincipalRoleAssignment,
    GroupRoleAssignment,
)

from ingenii_azure_data_platform.utils import generate_resource_name
from ingenii_azure_data_platform.orchestration import AdfSelfHostedIntegrationRuntime

from config import platform_config
from management import resource_groups
from management.user_groups import user_groups
from storage.datalake import datalake
from security import credentials_store
from analytics.databricks.workspaces import engineering as databricks_engineering

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY
# ----------------------------------------------------------------------------------------------------------------------
datafactory_config = platform_config.yml_config["analytics_services"]["datafactory"][
    "factories"
]["orchestration"]

datafactory_name = generate_resource_name(
    resource_type="datafactory",
    resource_name=datafactory_config["display_name"],
    platform_config=platform_config,
)

datafactory = adf.Factory(
    resource_name=datafactory_name,
    factory_name=datafactory_name,
    location=platform_config.region.long_name,
    resource_group_name=resource_groups.infra.name,
    identity=adf.FactoryIdentityArgs(type=adf.FactoryIdentityType.SYSTEM_ASSIGNED),
    global_parameters={
        "DataLakeName": adf.GlobalParameterSpecificationArgs(
            type="String", value=datalake.name
        )
    },
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> IAM -> ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------
iam_role_assignments = datafactory_config["iam"].get("role_assignments", {})

# Create role assignments defined in the YAML files
for assignment in iam_role_assignments:
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=datafactory.id,
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> INTEGRATION RUNTIMES
# ----------------------------------------------------------------------------------------------------------------------
integration_runtimes_config = datafactory_config.get("integration_runtimes", [])

for config in integration_runtimes_config:
    if config["type"] == "self-hosted":
        runtime = AdfSelfHostedIntegrationRuntime(
            name=config["name"],
            description=config.get(
                "description",
                "Managed by the Ingenii's deployment process. Manual changes are discouraged as they will be overridden.",
            ),
            factory_name=datafactory.name,
            resource_group_name=resource_groups.infra.name,
            platform_config=platform_config,
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> LINKED SERVICES
# ----------------------------------------------------------------------------------------------------------------------

# DATALAKE
# Datafactory Access to Data Lake
datafactory_acccess_to_datalake = ServicePrincipalRoleAssignment(
    role_name="Storage Blob Data Contributor",
    service_principal_object_id=datafactory.identity.principal_id,
    scope=datalake.id,
)

datalake_linked_service = adf.LinkedService(
    resource_name=f"{datafactory_name}-link-to-datalake",
    factory_name=datafactory.name,
    linked_service_name="DataLake",
    properties=adf.AzureBlobFSLinkedServiceArgs(
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

credentials_store_linked_service = adf.LinkedService(
    resource_name=f"{datafactory_name}-link-to-credentials-store",
    factory_name=datafactory.name,
    linked_service_name="Credentials Store",
    properties=adf.AzureKeyVaultLinkedServiceArgs(
        base_url=f"https://{credentials_store.key_vault_name}.vault.azure.net",
        description="Managed by Ingenii Data Platform",
        type="AzureKeyVault",
    ),
    resource_group_name=resource_groups.infra.name,
)  # type: ignore

# DATABRICKS ENGINEERING - DELTA LAKE
databricks_engineering_delta_linked_service = adf.LinkedService(
    resource_name=f"{datafactory_name}-link-to-databricks-engineering-delta",
    factory_name=datafactory.name,
    linked_service_name="Databricks Engineering Delta",
    properties=adf.AzureDatabricksDeltaLakeLinkedServiceArgs(
        domain=databricks_engineering.workspace.workspace_url.apply(
            lambda url: f"https://{url}"
        ),
        access_token=databricks_engineering.datafactory_token.token_value,  # type: ignore
        cluster_id=databricks_engineering.clusters["default"].id,
        description="Managed by Ingenii Data Platform",
        type="AzureDatabricksDeltaLake",
    ),
    resource_group_name=resource_groups.infra.name,
)  # type: ignore


# DATABRICKS ENGINEERING - COMPUTE
databricks_engineering_compute_linked_service = adf.LinkedService(
    resource_name=f"{datafactory_name}-link-to-databricks-engineering-compute",
    factory_name=datafactory.name,
    linked_service_name="Databricks Engineering Compute",
    properties=adf.AzureDatabricksLinkedServiceArgs(
        domain=databricks_engineering.workspace.workspace_url.apply(
            lambda url: f"https://{url}"
        ),
        access_token=databricks_engineering.datafactory_token.token_value,  # type: ignore
        existing_cluster_id=databricks_engineering.clusters["default"].id,
        workspace_resource_id=databricks_engineering.workspace.id,
        description="Managed by Ingenii Data Platform",
        type="AzureDatabricks",
    ),
    resource_group_name=resource_groups.infra.name,
)  # type: ignore

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> INGESTION PIPELINE AND TRIGGER
# ----------------------------------------------------------------------------------------------------------------------
databricks_file_ingestion_pipeline = adf.Pipeline(
    resource_name=f"{datafactory_name}-raw-databricks-file-ingestion",
    factory_name=datafactory.name,
    pipeline_name="Trigger ingest file notebook",
    description="Managed by Ingenii Data Platform",
    concurrency=1,
    parameters={
        "fileName": adf.ParameterSpecificationArgs(type="String"),
        "filePath": adf.ParameterSpecificationArgs(type="String"),
    },
    activities=[
        adf.DatabricksNotebookActivityArgs(
            name="Trigger ingest file notebook",
            notebook_path="/Shared/Ingenii Engineering/data_pipeline",
            type="DatabricksNotebook",
            linked_service_name=adf.LinkedServiceReferenceArgs(
                reference_name=databricks_engineering_compute_linked_service.name,
                type="LinkedServiceReference",
            ),
            base_parameters={
                "file_path": {
                    "value": "@pipeline().parameters.filePath",
                    "type": "Expression",
                },
                "file_name": {
                    "value": "@pipeline().parameters.fileName",
                    "type": "Expression",
                },
                "increment": 0,
            },
            policy=adf.ActivityPolicyArgs(
                timeout="0.00:10:00",
                retry=0,
                retry_interval_in_seconds=30,
                secure_output=False,
                secure_input=False,
            ),
        )
    ],
    resource_group_name=resource_groups.infra.name,
)

databricks_file_ingestion_trigger = adf.Trigger(
    resource_name=f"{datafactory_name}-raw-databricks-file-ingestion",
    factory_name=datafactory.name,
    trigger_name="Raw file created",
    properties=adf.BlobEventsTriggerArgs(
        type="BlobEventsTrigger",
        scope=datalake.id,
        events=[adf.BlobEventTypes.MICROSOFT_STORAGE_BLOB_CREATED],
        blob_path_begins_with="/raw/blobs/",
        ignore_empty_blobs=True,
        pipelines=[
            adf.TriggerPipelineReferenceArgs(
                pipeline_reference=adf.PipelineReferenceArgs(
                    reference_name=databricks_file_ingestion_pipeline.name,
                    type="PipelineReference",
                ),
                parameters={
                    "fileName": "@trigger().outputs.body.fileName",
                    "filePath": "@trigger().outputs.body.folderPath",
                },
            )
        ],
    ),
    resource_group_name=resource_groups.infra.name,
)
