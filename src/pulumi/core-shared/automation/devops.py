import pulumi_azuredevops as ado

from ingenii_azure_data_platform.utils import generate_resource_name
from project_config import platform_config

ado_configs = platform_config.from_yml["automation"]["devops"]

# Azure DevOps Project
PROJECT_FEATURES = ["boards", "repositories", "pipelines", "testplans", "artifacts"]

ado_project = ado.Project(
    resource_name=generate_resource_name(
        resource_type="devops_project",
        resource_name="data-platform",
        platform_config=platform_config,
    ),
    name=ado_configs["project"]["name"],
    description=ado_configs["project"]["description"],
    features={
        feature: "disabled"
        for feature in PROJECT_FEATURES
        if feature not in ado_configs["project"]["features"]
    },
    version_control=ado_configs["project"]["version_control"],
    visibility=ado_configs["project"]["visibility"],
    work_item_template=ado_configs["project"]["work_item_template"],
)

# Azure DevOps Repositories
ado_repo_configs = ado_configs.get("repositories", [])
ado_repos = {}

for repo in ado_repo_configs:
    ado_repos[repo["name"]] = ado.Git(
        resource_name=generate_resource_name(
            resource_type="devops_repo",
            resource_name=repo["name"],
            platform_config=platform_config,
        ),
        name=repo["name"],
        project_id=ado_project.id,
        initialization=ado.GitInitializationArgs(
            init_type="Import",
            source_type="Git",
            source_url=repo["import_url"],
        )
        if repo.get("import_url") is not None
        else ado.GitInitializationArgs(init_type="Clean"),
    )

    if repo.get("pipeline") is not None:
        ado.BuildDefinition(
            resource_name=generate_resource_name(
                resource_type="devops_pipeline",
                resource_name=repo["name"],
                platform_config=platform_config,
            ),
            name=repo["name"],
            project_id=ado_project.id,
            ci_trigger=ado.BuildDefinitionCiTriggerArgs(
                use_yaml=repo["pipeline"].get("use_yml", True),
            ),
            repository=ado.BuildDefinitionRepositoryArgs(
                repo_type="TfsGit",
                repo_id=ado_repos[repo["name"]].id,
                branch_name=repo["pipeline"].get("branch_name", "main"),
                yml_path=repo["pipeline"].get("yml_path", "azure-pipelines.yml"),
            ),
        )