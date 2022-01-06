from pulumi import ResourceOptions
from pulumi_azure_native import datafactory as adf

from analytics.datafactory.orchestration import datafactory, datafactory_name
from analytics.datafactory.orchestration_datasets import data_lake_folder
from analytics.datafactory.orchestration_linked_services import databricks_analytics_compute_linked_service, \
    databricks_engineering_compute_linked_service, datalake_linked_service
from management import resource_groups
from storage.datalake import datalake

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
            depends_on=[],
            base_parameters={
                "file_path": {
                    "value": "@pipeline().parameters.filePath",
                    "type": "Expression",
                },
                "file_name": {
                    "value": "@pipeline().parameters.fileName",
                    "type": "Expression",
                },
                "increment": "0",
            },
            policy=adf.ActivityPolicyArgs(
                timeout="0.00:20:00",
                retry=0,
                retry_interval_in_seconds=30,
                secure_output=False,
                secure_input=False,
            ),
            user_properties=[],
        )
    ],
    policy=adf.PipelinePolicyArgs(),
    annotations=["Created by Ingenii"],
    opts=ResourceOptions(ignore_changes=["annotations"]),
    resource_group_name=resource_groups["infra"].name,
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
        annotations=["Created by Ingenii"],
    ),
    opts=ResourceOptions(ignore_changes=["properties.annotations"]),
    resource_group_name=resource_groups["infra"].name,
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> WORKSPACE SYNCING
# ----------------------------------------------------------------------------------------------------------------------

containers = ["models", "snapshots", "source"]

default_policy = adf.ActivityPolicyArgs(
    timeout="0.00:01:00",
    retry=3,
    retry_interval_in_seconds=30,
    secure_output=False,
    secure_input=False,
)

def per_container_activities(container_name):
    return [
        adf.GetMetadataActivityArgs(
            type="GetMetadata",
            name=f"Get {container_name} top-level folders",
            description=None,
            dataset=adf.DatasetReferenceArgs(
                reference_name=data_lake_folder.name,
                type="DatasetReference",
                parameters={"Container": container_name, "Folder": "/"}
            ),
            field_list=["childItems"],
            format_settings=adf.BinaryReadSettingsArgs(
                type="BinaryReadSettings"
            ),
            policy=default_policy,
            store_settings=adf.AzureBlobFSReadSettingsArgs(
                type="AzureBlobFSReadSettings",
                enable_partition_discovery=False
            )
        ),
        adf.ForEachActivityArgs(
            name=f"Find new {container_name} table folders",
            type="ForEach",
            depends_on=[adf.ActivityDependencyArgs(
                activity=f"Get {container_name} top-level folders",
                dependency_conditions=[adf.DependencyCondition.SUCCEEDED]
            )],
            items=adf.ExpressionArgs(
                type="Expression",
                value=f"@activity('Get {container_name} top-level folders').output.childItems"
            ),
            activities=[
                adf.GetMetadataActivityArgs(
                    type="GetMetadata",
                    name=f"List {container_name} table folders",
                    description=None,
                    dataset=adf.DatasetReferenceArgs(
                        reference_name=data_lake_folder.name,
                        type="DatasetReference",
                        parameters={
                            "Container": container_name,
                            "Folder": adf.ExpressionArgs(
                                type="Expression",
                                value="@item().name"
                            )
                        }
                    ),
                    field_list=["childItems"],
                    format_settings=adf.BinaryReadSettingsArgs(
                        type="BinaryReadSettings"
                    ),
                    linked_service_name=datalake_linked_service.name,
                    policy=default_policy,
                    store_settings=adf.AzureBlobFSReadSettingsArgs(
                        type="AzureBlobFSReadSettings",
                        enable_partition_discovery=False,
                        modified_datetime_start=adf.ExpressionArgs(
                                type="Expression",
                                value="@addToTime(utcNow(), -3, 'Day')"
                        )
                    )
                ),
                adf.FilterActivityArgs(
                    type="Filter",
                    name=f"Find only {container_name} table folders",
                    description=None,
                    depends_on=[adf.ActivityDependencyArgs(
                        activity=f"List {container_name} table folders",
                        dependency_conditions=[adf.DependencyCondition.SUCCEEDED]
                    )],
                    items=adf.ExpressionArgs(
                        type="Expression",
                        value=f"@activity('List {container_name} table folders').output.childItems"
                    ),
                    condition=adf.ExpressionArgs(
                        type="Expression",
                        value="@equals(item().type, 'Folder')"
                    )
                ),
                adf.IfConditionActivityArgs(
                    type="IfCondition",
                    name=f"If new {container_name} tables",
                    description=None,
                    depends_on=[adf.ActivityDependencyArgs(
                        activity=f"Find only {container_name} table folders",
                        dependency_conditions=[adf.DependencyCondition.SUCCEEDED]
                    )],
                    expression=adf.ExpressionArgs(
                        type="Expression",
                        value=f"@greater(length(activity('Find only {container_name} table folders').output.Value), 0)"
                    ),
                    if_true_activities=[
                        adf.SetVariableActivityArgs(
                            type="SetVariable",
                            name=f"Set found {container_name} folders",
                            description=None,
                            variable_name=f"{container_name}Tables",
                            value=adf.ExpressionArgs(
                                type="Expression",
                                value=f"@activity('Find only {container_name} table folders').output.Value"
                            )
                        )
                    ]
                )
            ]
        )
    ]

databricks_workspace_syncing_pipeline = adf.Pipeline(
    resource_name=f"{datafactory_name}-databricks-workspace-syncing",
    factory_name=datafactory.name,
    pipeline_name="Sync workspaces for new tables",
    description="Managed by Ingenii Data Platform",
    concurrency=1,
    activities=[
        per_container_activity
        for container in containers
        for per_container_activity in per_container_activities(container)
    ] + [
        adf.IfConditionActivityArgs(
            type="IfCondition",
            name="If new tables",
            description=None,
            depends_on=[
                adf.ActivityDependencyArgs(
                    activity=f"Find new {container} table folders",
                    dependency_conditions=[adf.DependencyCondition.SUCCEEDED]
                )
                for container in containers
            ],
            expression=adf.ExpressionArgs(
                type="Expression",
                value="@greater(length(union(" + 
                      ", ".join([
                          f"variables('{container}Tables')"
                          for container in containers
                          ]) + 
                      ")), 0)"
            ),
            if_true_activities=[
                adf.DatabricksNotebookActivityArgs(
                    name="Sync tables to Analytics workspace",
                    notebook_path="/Shared/Ingenii Engineering/mount_tables",
                    type="DatabricksNotebook",
                    linked_service_name=adf.LinkedServiceReferenceArgs(
                        reference_name=databricks_analytics_compute_linked_service.name,
                        type="LinkedServiceReference",
                    ),
                    policy=adf.ActivityPolicyArgs(
                        timeout="0.00:20:00",
                        retry=0,
                        retry_interval_in_seconds=30,
                        secure_output=False,
                        secure_input=False,
                    ),
                )
            ]
        ),
    ],
    variables={
        f"{container}Tables": adf.VariableSpecificationArgs(
            type=adf.VariableType.ARRAY
        )
        for container in containers
    },
    policy=adf.PipelinePolicyArgs(),
    annotations=["Created by Ingenii"],
    opts=ResourceOptions(ignore_changes=["annotations"]),
    resource_group_name=resource_groups["infra"].name,
)

databricks_sync_workspaces_trigger = adf.Trigger(
    resource_name=f"{datafactory_name}-databricks-workspace-syncing",
    factory_name=datafactory.name,
    trigger_name="Daily sync",
    properties=adf.ScheduleTriggerArgs(
        type="ScheduleTrigger",
        description=None,
        recurrence=adf.ScheduleTriggerRecurrenceArgs(
            frequency=adf.RecurrenceFrequency.DAY,
            interval=1,
            time_zone="UTC",
            start_time="2021-01-01T00:00:00Z",
            schedule=adf.RecurrenceScheduleArgs(hours=[0], minutes=[0])
        ),
        pipelines=[
            adf.TriggerPipelineReferenceArgs(
                pipeline_reference=adf.PipelineReferenceArgs(
                    reference_name=databricks_workspace_syncing_pipeline.name,
                    type="PipelineReference",
                ),
            )
        ],
        annotations=["Created by Ingenii"],
    ),
    opts=ResourceOptions(ignore_changes=["properties.annotations"]),
    resource_group_name=resource_groups["infra"].name,
)