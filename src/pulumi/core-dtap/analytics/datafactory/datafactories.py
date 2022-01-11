from os import getenv
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
from platform_shared import SHARED_OUTPUTS
from project_config import platform_config, platform_outputs
from security.credentials_store import key_vault
from storage.datalake import datalake

factory_outputs = platform_outputs["analytics"]["datafactory"]["factories"]

datafactory_resource_group = resource_groups["infra"].name
devops_organization_name = getenv("AZDO_ORG_SERVICE_URL").strip(" /").split("/")[-1]

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORIES
# ----------------------------------------------------------------------------------------------------------------------
datafactory_configs = platform_config.from_yml["analytics_services"]["datafactory"]["factories"]
datafactory_repositories = SHARED_OUTPUTS["analytics"]["datafactory_repositories"]
devops_project = SHARED_OUTPUTS["devops"]["project"]

data_datafactories = {}

for ref_key, datafactory_config in datafactory_configs.items():
    if ref_key == "orchestration":
        continue

    datafactory_name = generate_resource_name(
        resource_type="datafactory",
        resource_name=datafactory_config["display_name"],
        platform_config=platform_config,
    )

    outputs = factory_outputs[ref_key] = {}

    # ----------------------------------------------------------------------------------------------------------------------
    # DATA FACTORY -> DEVOPS REPOSITORY
    # ----------------------------------------------------------------------------------------------------------------------

    datafactory_repository = datafactory_config.get("repository", {})
    if datafactory_repository.get("devops_integrated"):
        global_parameters = {}
        repo_configuration = adf.FactoryVSTSConfigurationArgs(
            account_name=devops_organization_name,
            collaboration_branch=datafactory_repository.get("collaboration_branch", "main"),
            project_name=devops_project["name"],
            repository_name=datafactory_repositories[ref_key]["name"],
            root_folder=datafactory_repository.get("root_folder", "/"),
            type="FactoryVSTSConfiguration"
        )
    else:
        global_parameters = {
            "CredentialStoreName": adf.GlobalParameterSpecificationArgs(
                type="String", value=key_vault.name
            ),
            "DataLakeName": adf.GlobalParameterSpecificationArgs(
                type="String", value=datalake.name
            )
        }
        repo_configuration = None

    # ----------------------------------------------------------------------------------------------------------------------
    # DATA FACTORY -> FACTORY
    # ----------------------------------------------------------------------------------------------------------------------
    datafactory = adf.Factory(
        resource_name=datafactory_name,
        factory_name=datafactory_name,
        location=platform_config.region.long_name,
        resource_group_name=datafactory_resource_group,
        identity=adf.FactoryIdentityArgs(type=adf.FactoryIdentityType.SYSTEM_ASSIGNED),
        repo_configuration=repo_configuration,
        global_parameters=global_parameters,
        opts=ResourceOptions(protect=platform_config.resource_protection),
    )

    data_datafactories[ref_key] = datafactory

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
                scope_description=f"{ref_key}-datafactory",
            )

    # ----------------------------------------------------------------------------------------------------------------------
    # DATA FACTORY -> INTEGRATION RUNTIMES
    # ----------------------------------------------------------------------------------------------------------------------
    for config in datafactory_config.get("integration_runtimes", []):
        if config["type"] == "self-hosted":
            runtime = AdfSelfHostedIntegrationRuntime(
                name=config["name"],
                description=config.get("description"),
                factory_name=datafactory.name,
                resource_group_name=datafactory_resource_group,
                platform_config=platform_config,
            )
    
    # ----------------------------------------------------------------------------------------------------------------------
    # DATA FACTORY -> DATA LAKE ACCESS
    # ----------------------------------------------------------------------------------------------------------------------
    ServicePrincipalRoleAssignment(
        principal_id=datafactory.identity.principal_id,
        principal_name=f"{ref_key}-datafactory-identity",
        role_name="Storage Blob Data Contributor",
        scope=datalake.id,
        scope_description="datalake",
    )

    ServicePrincipalRoleAssignment(
        principal_id=datafactory.identity.principal_id,
        principal_name=f"{ref_key}-datafactory-identity",
        role_name="Key Vault Secrets User",
        scope=key_vault.id,
        scope_description="cred-store",
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
