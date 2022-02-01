from pulumi import ResourceOptions, Output
from pulumi_azure_native import datafactory as adf, insights

from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    ServicePrincipalRoleAssignment,
)
from ingenii_azure_data_platform.logs import log_diagnostic_settings
from ingenii_azure_data_platform.orchestration import AdfSelfHostedIntegrationRuntime
from ingenii_azure_data_platform.utils import generate_resource_name

from logs import log_analytics_workspace
from management import action_groups, resource_groups, user_groups

from project_config import platform_config, platform_outputs, azure_client
from platform_shared import get_devops_principal_id

from storage.datalake import datalake

outputs = platform_outputs["analytics"]["datafactory"]["factories"][
    "orchestration"
] = {}

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY
# ----------------------------------------------------------------------------------------------------------------------
datafactory_config = platform_config.from_yml["analytics_services"]["datafactory"][
    "factories"
]["orchestration"]

datafactory_name = generate_resource_name(
    resource_type="datafactory",
    resource_name=datafactory_config["display_name"],
    platform_config=platform_config,
)
datafactory_resource_group = resource_groups["infra"].name

datafactory = adf.Factory(
    resource_name=datafactory_name,
    factory_name=datafactory_name,
    location=platform_config.region.long_name,
    resource_group_name=datafactory_resource_group,
    identity=adf.FactoryIdentityArgs(type=adf.FactoryIdentityType.SYSTEM_ASSIGNED),
    global_parameters={
        "DataLakeName": adf.GlobalParameterSpecificationArgs(
            type="String", value=datalake.name
        )
    },
    opts=ResourceOptions(
        protect=platform_config.resource_protection,
        ignore_changes=["repo_configuration"],
    ),
)

outputs["id"] = datafactory.id
outputs["name"] = datafactory.name
outputs["url"] = Output.all(datafactory_resource_group, datafactory.name).apply(
    lambda args: f"https://adf.azure.com/en-us/home?factory=%2Fsubscriptions%2F{azure_client.subscription_id}%2FresourceGroups%2F{args[0]}%2Fproviders%2FMicrosoft.DataFactory%2Ffactories%2F{args[1]}"
)
# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> IAM -> ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------

# Create role assignments defined in the YAML files
for assignment in datafactory_config["iam"].get("role_assignments", []):
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            principal_id=user_groups[user_group_ref_key]["object_id"],
            principal_name=user_group_ref_key,
            role_name=assignment["role_definition_name"],
            scope=datafactory.id,
            scope_description="orchestration-datafactory",
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> INTEGRATION RUNTIMES
# ----------------------------------------------------------------------------------------------------------------------
for config in datafactory_config.get("integration_runtimes", []):
    if config["type"] == "self-hosted":
        runtime = AdfSelfHostedIntegrationRuntime(
            name=config["name"],
            description=config.get(
                "description",
                "Managed by the Ingenii's deployment process. Manual changes are discouraged as they will be overridden.",
            ),
            factory_name=datafactory.name,
            resource_group_name=datafactory_resource_group,
            platform_config=platform_config,
        )

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> DEVOPS ASSIGNMENT
# ----------------------------------------------------------------------------------------------------------------------

ServicePrincipalRoleAssignment(
    principal_name="deployment-user-identity",
    principal_id=get_devops_principal_id(),
    role_name="Data Factory Contributor",
    scope=datafactory.id,
    scope_description="orchestration-datafactory",
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> PIPELINE FAILURE ALERT RULE
# ----------------------------------------------------------------------------------------------------------------------
if datafactory_config.get("pipeline_failure_action_groups"):
    insights.MetricAlert(
        resource_name=generate_resource_name(
            resource_type="metric_alert",
            resource_name="datafactory_orchestration_pipeline_failure",
            platform_config=platform_config,
        ),
        actions=[
            insights.MetricAlertActionArgs(action_group_id=action_groups[pfac])
            for pfac in datafactory_config.get("pipeline_failure_action_groups", [])
        ],
        auto_mitigate=False,
        criteria=insights.MetricAlertMultipleResourceMultipleMetricCriteriaArgs(
            odata_type="Microsoft.Azure.Monitor.MultipleResourceMultipleMetricCriteria",
            all_of=[insights.MetricCriteriaArgs(
                criterion_type="StaticThresholdCriterion",
                metric_name="PipelineFailedRuns",
                name="Pipeline failure",
                operator=insights.ConditionalOperator.GREATER_THAN_OR_EQUAL,
                threshold=0,
                time_aggregation=insights.AggregationTypeEnum.TOTAL,
            )],
        ),
        description="Alerts on pipeline failures",
        enabled=True,
        evaluation_frequency="PT15M",
        location="global",
        resource_group_name=datafactory_resource_group,
        rule_name="Pipeline Failures - orchestration",
        scopes=[datafactory.id],
        severity=1,
        tags=platform_config.tags,
        window_size="PT15M"
    )

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> LOGGING
# ----------------------------------------------------------------------------------------------------------------------

log_diagnostic_settings(
    platform_config,
    log_analytics_workspace.id,
    datafactory.type,
    datafactory.id,
    datafactory_name,
    logs_config=datafactory_config.get("logs", {}),
    metrics_config=datafactory_config.get("metrics", {}),
)
