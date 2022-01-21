from pulumi import ResourceOptions
from pulumi_azure_native import datafactory as adf

from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    ServicePrincipalRoleAssignment,
)
from ingenii_azure_data_platform.logs import log_diagnostic_settings
from ingenii_azure_data_platform.orchestration import AdfSelfHostedIntegrationRuntime
from ingenii_azure_data_platform.utils import generate_resource_name

from logs import log_analytics_workspace
from management import resource_groups
from management.user_groups import user_groups
from platform_shared import get_devops_principal_id
from project_config import platform_config, platform_outputs
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
