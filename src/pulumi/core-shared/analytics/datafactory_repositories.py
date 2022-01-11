from pulumi import ResourceOptions
import pulumi_azuredevops as ado

from ingenii_azure_data_platform.utils import generate_resource_name

from automation.devops import ado_project
from platform_dtap import dtap_configs
from project_config import platform_config, platform_outputs

repositories_needed = set()

for env, config in dtap_configs.items():
    factory_configs = config["analytics_services"]["datafactory"]["factories"]
    for factory_ref_key, factory_confg in factory_configs.items():
        if factory_ref_key == "orchestration":
            continue

        if factory_confg.get("repository", {}).get("devops_integrated"):
            repositories_needed.add(factory_ref_key)

outputs = platform_outputs["analytics"]["datafactory_repositories"] = {}

datafactory_repositories = {}
for repository_name in repositories_needed:
    git_repository = ado.Git(
        resource_name=generate_resource_name(
            resource_type="devops_repo",
            resource_name=f"datafactory-{repository_name}",
            platform_config=platform_config,
        ),
        name=f"Data Factory - {repository_name}",
        project_id=ado_project.id,
        default_branch="refs/heads/main",
        initialization = ado.GitInitializationArgs(
            init_type="Import",
            source_type="Git",
            source_url="https://github.com/ingenii-solutions/azure-data-factory-initial-repository.git",
        ),
        opts=ResourceOptions(protect=platform_config.resource_protection),
    )

    datafactory_repositories[repository_name] = git_repository
    outputs[repository_name] = {
        "id": git_repository.id,
        "name": git_repository.name,
        "web_url": git_repository.web_url
    }
