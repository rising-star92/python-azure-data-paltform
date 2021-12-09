import os
import pulumi
import pulumi_azure_native as azure_native
import pulumi_azuread as azuread

from pulumi_databricks import Provider as DatabricksProvider
from pulumi_databricks import ProviderArgs as DatabricksProviderArgs
from pulumi_databricks import databricks

from ingenii_azure_data_platform.iam import (
    GroupRoleAssignment,
    ServicePrincipalRoleAssignment,
)
from ingenii_azure_data_platform.logs import log_diagnostic_settings
from ingenii_azure_data_platform.utils import generate_hash, generate_resource_name

from project_config import azure_client, platform_config, platform_outputs, DTAP_ROOT
from platform_shared import add_config_registry_secret
from logs import log_analytics_workspace
from management import resource_groups
from management.user_groups import user_groups
from security import credentials_store
from network import vnet
from storage.datalake import datalake, datalake_containers

outputs = platform_outputs["analytics"]["databricks"]["workspaces"]["engineering"] = {}

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE
# ----------------------------------------------------------------------------------------------------------------------
workspace_config = platform_config.from_yml["analytics_services"]["databricks"][
    "workspaces"
]["engineering"]
workspace_short_name = "engineering"
workspace_name = generate_resource_name(
    resource_type="databricks_workspace",
    resource_name=workspace_short_name,
    platform_config=platform_config,
)

workspace_managed_resource_group_short_name = generate_resource_name(
    resource_type="resource_group",
    resource_name=f"dbw-{workspace_short_name}",
    platform_config=platform_config,
)

workspace_managed_resource_group_name = f"/subscriptions/{azure_client.subscription_id}/resourceGroups/{workspace_managed_resource_group_short_name}"

workspace = azure_native.databricks.Workspace(
    resource_name=workspace_name,
    workspace_name=workspace_name,
    location=platform_config.region.long_name,
    managed_resource_group_id=workspace_managed_resource_group_name,
    parameters=azure_native.databricks.WorkspaceCustomParametersArgs(
        custom_private_subnet_name=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.dbw_engineering_containers_subnet.name,  # type: ignore
        ),
        custom_public_subnet_name=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.dbw_engineering_hosts_subnet.name,  # type: ignore
        ),
        custom_virtual_network_id=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.vnet.id,
        ),
        enable_no_public_ip=azure_native.databricks.WorkspaceCustomBooleanParameterArgs(
            value=True
        ),
    ),
    sku=azure_native.databricks.SkuArgs(name="Premium"),
    resource_group_name=resource_groups["infra"].name,
)

outputs["name"] = workspace.name
outputs["id"] = workspace.workspace_id
outputs["url"] = workspace.workspace_url

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> LOGGING
# ----------------------------------------------------------------------------------------------------------------------

log_diagnostic_settings(
    platform_config,
    log_analytics_workspace.id,
    workspace.type,
    workspace.id,
    workspace_name,
    logs_config=workspace_config.get("logs", {}),
    metrics_config=workspace_config.get("metrics", {}),
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> IAM ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------

# TODO: Create a function that takes care of the role assignments. Replace all role assignments using the function.
# Create role assignments defined in the YAML files
for assignment in workspace_config.get("iam", {}).get("role_assignments", []):
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        GroupRoleAssignment(
            role_name=assignment["role_definition_name"],
            group_object_id=user_groups[user_group_ref_key]["object_id"],
            scope=workspace.id,
        )

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> PROVIDER
# ----------------------------------------------------------------------------------------------------------------------
databricks_provider = DatabricksProvider(
    resource_name=workspace_name,
    args=DatabricksProviderArgs(
        azure_client_id=os.getenv("ARM_CLIENT_ID", azure_client.client_id),
        azure_client_secret=os.getenv("ARM_CLIENT_SECRET"),
        azure_subscription_id=os.getenv("ARM_SUBSCRIPTION_ID", azure_client.subscription_id),
        azure_tenant_id=os.getenv("ARM_TENANT_ID", azure_client.tenant_id),
        azure_workspace_resource_id=workspace.id,
    ),
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> GENERAL CONFIG
# ----------------------------------------------------------------------------------------------------------------------
databricks.WorkspaceConf(
    resource_name=workspace_name,
    custom_config={
        "enableDcs": workspace_config["config"].get("enable_container_services", "false"),
        "enableIpAccessLists": workspace_config["config"].get("enable_ip_access_lists", "false"),
    },
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)
# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> SECRETS & TOKENS
# ----------------------------------------------------------------------------------------------------------------------

# SECRET SCOPE
secret_scope_name = "main"
secret_scope = databricks.SecretScope(
    resource_name=f"{workspace_name}-secret-scope-main",
    name=secret_scope_name,
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)

# DBT TOKEN
dbt_token_name = f"{workspace_short_name}-token-for-dbt"
dbt_token_resource_name = f"{workspace_name}-token-for-dbt"

# Also used to generate the DBT documentation by the DevOps pipeline
dbt_token = databricks.Token(
    resource_name=dbt_token_resource_name,
    comment="Data Build Tool Token - Used for DBT automation",
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)

dbt_token_as_scope_secret = databricks.Secret(
    resource_name=dbt_token_resource_name,
    scope=secret_scope.id,
    string_value=dbt_token.token_value,
    key=dbt_token_name,
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)

dbt_token_as_key_vault_secret = azure_native.keyvault.Secret(
    resource_name=dbt_token_resource_name,
    properties=azure_native.keyvault.SecretPropertiesArgs(
        value=dbt_token.token_value,
    ),
    resource_group_name=resource_groups["security"].name,
    secret_name=dbt_token_name,
    vault_name=credentials_store.key_vault.name,
)

# DATAFACTORY TOKEN
datafactory_token = databricks.Token(
    resource_name=f"{workspace_name}-token-for-datafactory",
    comment="Data Factory Token - Used for Data Factory integration",
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> CLUSTER TAGS
# ----------------------------------------------------------------------------------------------------------------------

# https://docs.microsoft.com/en-us/azure/databricks/administration-guide/account-settings/usage-detail-tags-azure#tag-conflict-resolution
cluster_default_tags = {"x_" + k: v for k, v in platform_config.tags.items()}

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> CLUSTERS -> SYSTEM CLUSTER
# ----------------------------------------------------------------------------------------------------------------------

system_cluster_config = workspace_config["clusters"]["system"]
system_cluster_resource_name = generate_resource_name(
    resource_type="databricks_cluster",
    resource_name=f"{workspace_short_name}-system",
    platform_config=platform_config,
)

system_cluster = databricks.Cluster(
    resource_name=system_cluster_resource_name,
    cluster_name=system_cluster_config["display_name"],
    spark_version=system_cluster_config["spark_version"],
    node_type_id=system_cluster_config["node_type_id"],
    is_pinned=system_cluster_config["is_pinned"],
    autotermination_minutes=system_cluster_config["autotermination_minutes"],
    spark_conf={
        "spark.databricks.cluster.profile": "singleNode",
        "spark.master": "local[*]",
        "spark.databricks.delta.preview.enabled": "true",
        **system_cluster_config.get("spark_conf", {}),
    },
    custom_tags={"ResourceClass": "SingleNode", **cluster_default_tags},
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)
# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> STORAGE MOUNTS
# ----------------------------------------------------------------------------------------------------------------------

# AZURE AD SERVICE PRINCIPAL USED FOR STORAGE MOUNTING
storage_mounts_sp_name = generate_resource_name(
    resource_type="service_principal",
    resource_name="dbw-eng-mounts",
    platform_config=platform_config,
)
storage_mounts_sp_app = azuread.Application(
    resource_name=storage_mounts_sp_name,
    display_name=storage_mounts_sp_name,
    identifier_uris=[f"api://{storage_mounts_sp_name}"],
    owners=[azure_client.object_id],
)

storage_mounts_sp = azuread.ServicePrincipal(
    resource_name=storage_mounts_sp_name,
    application_id=storage_mounts_sp_app.application_id,
    app_role_assignment_required=False,
)

storage_mounts_sp_password = azuread.ServicePrincipalPassword(
    resource_name=storage_mounts_sp_name,
    service_principal_id=storage_mounts_sp.object_id,
)

storage_mounts_dbw_password = databricks.Secret(
    resource_name=storage_mounts_sp_name,
    scope=secret_scope.id,
    string_value=storage_mounts_sp_password.value,
    key=storage_mounts_sp_name,
    opts=pulumi.ResourceOptions(provider=databricks_provider),
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> STORAGE MOUNTS -> ADLS GEN 2
# ----------------------------------------------------------------------------------------------------------------------

# IAM ROLE ASSIGNMENT
# Allow the Storage Mounts service principal to access the Datalake.
storage_mounts_datalake_role_assignment = ServicePrincipalRoleAssignment(
    role_name="Storage Blob Data Contributor",
    service_principal_object_id=storage_mounts_sp.object_id,
    scope=datalake.id,
)

# STORAGE MOUNTS
# If no storage mounts are defined in the YAML files, we'll not attempt to create any.
storage_mounts = {}
for definition in workspace_config.get("storage_mounts", []):
    storage_mounts[definition["mount_name"]] = databricks.AzureAdlsGen2Mount(
        resource_name=f'{workspace_name}-{definition["mount_name"]}',
        client_id=storage_mounts_sp.application_id,
        client_secret_key=storage_mounts_dbw_password.key,
        tenant_id=azure_client.tenant_id,
        client_secret_scope=secret_scope.name,
        storage_account_name=datalake.name,
        initialize_file_system=False,
        container_name=definition["container_name"],
        mount_name=definition["mount_name"],
        cluster_id=system_cluster.id,
        opts=pulumi.ResourceOptions(
            provider=databricks_provider,
            delete_before_replace=True,
        ),
    )

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> PRE-PROCESSING PACKAGE
# ----------------------------------------------------------------------------------------------------------------------

blob_name = "pre_process-1.0.0-py3-none-any.whl"
pre_processing_package = pulumi.FileAsset(f"{DTAP_ROOT}/assets/{blob_name}")
pre_processing_blob = azure_native.storage.Blob(
    resource_name=f"{workspace_name}-pre_processing_package",
    account_name=datalake.name,
    blob_name="pre_process/" + blob_name,
    container_name=datalake_containers["utilities"].name,
    resource_group_name=resource_groups["data"].name,
    source=pre_processing_package,
    opts=pulumi.ResourceOptions(
        ignore_changes=["content_md5"], depends_on=[storage_mounts["utilities"]]
    ),
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> CLUSTERS
# ----------------------------------------------------------------------------------------------------------------------

# A dict of all clusters that are deployed.
clusters = {}

# If no clusters are defined in the YAML files, we'll not attempt to create any.
for ref_key, cluster_config in workspace_config.get("clusters", {}).items():
    if ref_key == "system":
        continue

    cluster_resource_name = generate_resource_name(
        resource_type="databricks_cluster",
        resource_name=f"{workspace_short_name}-{ref_key}",
        platform_config=platform_config,
    )

    # Cluster Libraries
    libraries = cluster_config.get("libraries", {})
    pypi_libraries = [
        databricks.ClusterLibraryArgs(
            pypi=databricks.ClusterLibraryPypiArgs(
                package=lib.get("package"), repo=lib.get("repo")
            )
        )
        for lib in libraries.get("pypi", [])
    ]
    whl_libraries_str = libraries.get("whl", [])
    
    if ref_key == "default":
        whl_libraries_str.append("dbfs:/mnt/utilities/pre_process/pre_process-1.0.0-py3-none-any.whl")
    
    whl_libraries = [
        databricks.ClusterLibraryArgs(whl=lib)
        for lib in set(whl_libraries_str)
    ]

    cluster_libraries = pypi_libraries + whl_libraries

    base_cluster_configuration = {
        "resource_name": cluster_resource_name,
        "cluster_name": cluster_config["display_name"],
        "spark_version": cluster_config["spark_version"],
        "node_type_id": cluster_config["node_type_id"],
        "is_pinned": cluster_config["is_pinned"],
        "autotermination_minutes": cluster_config["autotermination_minutes"],
        "libraries": cluster_libraries or None,
        "spark_env_vars": {
            "PYSPARK_PYTHON": "/databricks/python3/bin/python3",
            "DATABRICKS_WORKSPACE_HOSTNAME": workspace.workspace_url,
            "DATABRICKS_CLUSTER_NAME": cluster_config["display_name"],
            "DBT_TOKEN_SCOPE": secret_scope_name,
            "DBT_TOKEN_NAME": dbt_token_name,
            "DBT_ROOT_FOLDER": "/dbfs/mnt/dbt",
            "DBT_LOGS_FOLDER": "/dbfs/mnt/dbt-logs",
            **cluster_config.get("spark_env_vars", {}),
        },
        "opts": pulumi.ResourceOptions(
            provider=databricks_provider, depends_on=[pre_processing_blob]
        ),
    }

    if cluster_config.get("docker_image_url"):
        base_cluster_configuration["docker_image"] = databricks.ClusterDockerImageArgs(
            url=cluster_config["docker_image_url"]
        )

    # Single Node Cluster Type
    if cluster_config["type"] == "single_node":
        clusters[ref_key] = databricks.Cluster(
            **base_cluster_configuration,
            spark_conf={
                "spark.databricks.cluster.profile": "singleNode",
                "spark.master": "local[*]",
                "spark.databricks.delta.preview.enabled": "true",
                **cluster_config.get("spark_conf", {}),
            },
            custom_tags={"ResourceClass": "SingleNode", **cluster_default_tags},
        )
    # High Concurrency Cluster Type
    elif cluster_config["type"] == "high_concurrency":
        clusters[ref_key] = databricks.Cluster(
            **base_cluster_configuration,
            autoscale=databricks.ClusterAutoscaleArgs(
                min_workers=cluster_config["auto_scale_min_workers"],
                max_workers=cluster_config["auto_scale_max_workers"],
            ),
            azure_attributes=databricks.ClusterAzureAttributesArgs(
                availability="SPOT_WITH_FALLBACK_AZURE"
                if cluster_config.get("use_spot_instances")
                else "ON_DEMAND_AZURE",
                first_on_demand=1,
                spot_bid_max_price=100,
            ),
            spark_conf={
                "spark.databricks.cluster.profile": "serverless",
                "spark.databricks.repl.allowedLanguages": "python,sql",
                "spark.databricks.passthrough.enabled": "true",
                "spark.databricks.pyspark.enableProcessIsolation": "true",
                "spark.databricks.delta.preview.enabled": "true",
                **cluster_config.get("spark_conf", {}),
            },
            custom_tags={"ResourceClass": "Serverless", **cluster_default_tags},
        )

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> CLUSTERS -> PERMISSIONS
# ----------------------------------------------------------------------------------------------------------------------

# Allow all users to be able to attach to the clusters
for ref_key, cluster_config in clusters.items():
    databricks.Permissions(
        resource_name=generate_hash(workspace_short_name, ref_key, "users"),
        cluster_id=clusters[ref_key].cluster_id,
        access_controls=[
            databricks.PermissionsAccessControlArgs(
                permission_level="CAN_ATTACH_TO", group_name="users"
            )
        ],
        opts=pulumi.ResourceOptions(provider=databricks_provider),
    )

# ----------------------------------------------------------------------------------------------------------------------
# DEVOPS ASSIGNMENT
# ----------------------------------------------------------------------------------------------------------------------

add_config_registry_secret(
    "databricks-engineering-workspace-hostname", workspace.workspace_url)
add_config_registry_secret(
    "databricks-engineering-cluster-name", clusters["default"].cluster_name)
