import os
import pulumi_azure_native as azure_native
import pulumi_azuread as azuread
from pulumi import ResourceOptions
from pulumi_databricks import Provider as DatabricksProvider
from pulumi_databricks import ProviderArgs as DatabricksProviderArgs
from pulumi_databricks import databricks
from config import platform as p
from config import azure_client
from management import resource_groups, user_groups
from network import vnet
from security import credentials_store
from storage.datalake import datalake

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE
# ----------------------------------------------------------------------------------------------------------------------
workspace_config = p.config_object["analytics_services"]["databricks"]["workspaces"]["engineering"]
workspace_short_name = "engineering"
workspace_name = p.generate_name("databricks_workspace", workspace_short_name)
workspace_managed_resource_group_name = f"/subscriptions/{azure_client.subscription_id}/resourceGroups/{p.generate_name('resource_group', f'dbw-{workspace_short_name}')}"

workspace = azure_native.databricks.Workspace(
    resource_name=workspace_name,
    workspace_name=workspace_name,
    location=p.region_long_name,
    managed_resource_group_id=workspace_managed_resource_group_name,
    parameters=azure_native.databricks.WorkspaceCustomParametersArgs(
        custom_private_subnet_name=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.dbw_engineering_containers_subnet.name,
        ),
        custom_public_subnet_name=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.dbw_engineering_hosts_subnet.name,
        ),
        custom_virtual_network_id=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.vnet.id,
        ),
        enable_no_public_ip=azure_native.databricks.WorkspaceCustomBooleanParameterArgs(
            value=True),
    ),
    sku=azure_native.databricks.SkuArgs(name="Premium"),
    resource_group_name=resource_groups.infra.name,
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> IAM ROLE ASSIGNMENTS
# ----------------------------------------------------------------------------------------------------------------------
try:
    iam_role_assignments = workspace_config["iam"]["role_assignments"]
except:
    iam_role_assignments = {}

# TODO: Create a function that takes care of the role assignments. Replace all role assignments using the function.
# Create role assignments defined in the YAML files
for assignment in iam_role_assignments:
    # User Group Assignment
    user_group_ref_key = assignment.get("user_group_ref_key")
    if user_group_ref_key is not None:
        azure_native.authorization.RoleAssignment(
            # Hash the resource_name to guarantee uniqueness
            resource_name=p.generate_hash(
                assignment["user_group_ref_key"], assignment["role_definition_name"], workspace_name),
            principal_id=user_groups[assignment["user_group_ref_key"]].get(
                "object_id"),
            principal_type="Group",
            role_definition_id=p.azure_iam_role_definitions[
                assignment["role_definition_name"]
            ],
            scope=workspace.id,
            opts=ResourceOptions(delete_before_replace=True)
        )

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> PROVIDER
# ----------------------------------------------------------------------------------------------------------------------
databricks_provider = DatabricksProvider(
    resource_name=workspace_name,
    args=DatabricksProviderArgs(
        azure_client_id=os.getenv("ARM_CLIENT_ID") or azure_client.client_id,
        azure_client_secret=os.getenv("ARM_CLIENT_SECRET"),
        azure_subscription_id=os.getenv(
            "ARM_SUBSCRIPTION_ID") or azure_client.subscription_id,
        azure_tenant_id=os.getenv("ARM_TENANT_ID") or azure_client.tenant_id,
        azure_workspace_resource_id=workspace.id
    )
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> GENERAL CONFIG
# ----------------------------------------------------------------------------------------------------------------------
databricks.WorkspaceConf(
    resource_name=workspace_name,
    custom_config={
        "enableDcs": workspace_config["config"].get("enable_container_services") or "false",
        "enableIpAccessLists": workspace_config["config"].get("enable_ip_access_lists") or "false"
    },
    opts=ResourceOptions(provider=databricks_provider)
)
# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> SECRETS & TOKENS
# ----------------------------------------------------------------------------------------------------------------------

# SECRET SCOPE
secret_scope = databricks.SecretScope(
    resource_name=f"{workspace_name}-secret-scope-main",
    name="main",
    opts=ResourceOptions(provider=databricks_provider))

# DBT TOKEN
dbt_token = databricks.Token(
    resource_name=f"{workspace_name}-token-for-dbt",
    comment="Data Build Tool Token - Used for DBT automation",
    opts=ResourceOptions(provider=databricks_provider))

dbt_token_as_key_vault_secret = azure_native.keyvault.Secret(
    resource_name=f"{workspace_name}-token-for-dbt",
    properties=azure_native.keyvault.SecretPropertiesArgs(
        value=dbt_token.token_value,
    ),
    resource_group_name=resource_groups.security.name,
    secret_name=f'{workspace_name}-token-for-dbt',
    vault_name=credentials_store.key_vault.name
)

# DATAFACTORY TOKEN
datafactory_token = databricks.Token(
    resource_name=f"{workspace_name}-token-for-datafactory",
    comment="Data Factory Token - Used for Data Factory integration",
    opts=ResourceOptions(provider=databricks_provider))

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> STORAGE MOUNTS
# ----------------------------------------------------------------------------------------------------------------------

# AZURE AD SERVICE PRINCIPAL USED FOR STORAGE MOUNTING
storage_mounts_sp_name = p.generate_name("service_principal", "dbw-eng-mounts")
storage_mounts_sp_app = azuread.Application(
    resource_name=storage_mounts_sp_name,
    display_name=storage_mounts_sp_name,
    identifier_uris=[f"api://{storage_mounts_sp_name}"],
    owners=[azure_client.object_id],
)

storage_mounts_sp = azuread.ServicePrincipal(
    resource_name=storage_mounts_sp_name,
    application_id=storage_mounts_sp_app.application_id,
    app_role_assignment_required=False
)

storage_mounts_sp_password = azuread.ServicePrincipalPassword(
    resource_name=storage_mounts_sp_name,
    service_principal_id=storage_mounts_sp.object_id
)

storage_mounts_dbw_password = databricks.Secret(
    resource_name=storage_mounts_sp_name,
    scope=secret_scope.id,
    string_value=storage_mounts_sp_password.value,
    key=storage_mounts_sp_name,
    opts=ResourceOptions(provider=databricks_provider)
)

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> STORAGE MOUNTS -> ADLS GEN 2
# ----------------------------------------------------------------------------------------------------------------------

# IAM ROLE ASSIGNMENT
# Allow the Storage Mounts service principal to access the Datalake.
storage_mounts_datalake_role_assignment = azure_native.authorization.RoleAssignment(
    resource_name=p.generate_hash(storage_mounts_sp_name),
    principal_id=storage_mounts_sp.object_id,
    principal_type="ServicePrincipal",
    role_definition_id=p.azure_iam_role_definitions["Storage Blob Data Contributor"],
    scope=datalake.id
)

# CONTAINER MOUNTS
# If no storage mounts are defined in the YAML files, we'll not attempt to create any.
try:
    storage_mount_definitions = workspace_config["storage_mounts"]
except:
    storage_mount_definitions = []

for definition in storage_mount_definitions:
    resource = databricks.AzureAdlsGen2Mount(
        resource_name=f'{workspace_name}-{definition["mount_name"]}',
        client_id=storage_mounts_sp.application_id,
        client_secret_key=storage_mounts_dbw_password.key,
        tenant_id=azure_client.tenant_id,
        client_secret_scope=secret_scope.name,
        storage_account_name=datalake.name,
        initialize_file_system=False,
        container_name=definition["container_name"],
        mount_name=definition["mount_name"],
        opts=ResourceOptions(provider=databricks_provider)
    )

# ----------------------------------------------------------------------------------------------------------------------
# ENGINEERING DATABRICKS WORKSPACE -> CLUSTERS
# ----------------------------------------------------------------------------------------------------------------------

# If no clusters are defined in the YAML files, we'll not attempt to create any.
try:
    cluster_definitions = workspace_config["clusters"]
except:
    cluster_definitions = {}

clusters = {}
for ref_key in cluster_definitions:
    cluster_config = cluster_definitions[ref_key]
    cluster_resource_name = p.generate_name("databricks_cluster", f'{workspace_short_name}-{ref_key}')

    # Cluster Libraries
    cluster_libraries = []
    try:
        # PyPi
        for lib in cluster_config["libraries"]["pypi"]:
            cluster_libraries.append(
                databricks.ClusterLibraryArgs(
                    pypi=databricks.ClusterLibraryPypiArgs(
                        package=lib["package"])
                )
            )
    except:
        pass

    # Single Node Cluster Type
    if cluster_config["type"] == "single_node":
        clusters[ref_key] = databricks.Cluster(
            resource_name=cluster_resource_name,
            cluster_name=cluster_config["display_name"],

            spark_version=cluster_config["spark_version"],

            node_type_id=cluster_config["node_type_id"],

            autotermination_minutes=cluster_config["autotermination_minutes"],

            docker_image=databricks.ClusterDockerImageArgs(
                url=cluster_config["docker_image_url"]
            ) if cluster_config.get("docker_image_url") else None,

            libraries=cluster_libraries or None,

            spark_env_vars={
                "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
            } | (cluster_config.get("spark_env_vars") or {}),

            spark_conf={
                "spark.databricks.cluster.profile": "singleNode",
                "spark.master": "local[*]",
                "spark.databricks.delta.preview.enabled": "true"
            } | (cluster_config.get("spark_conf") or {}),

            custom_tags={
                "ResourceClass": "SingleNode"
            } | p.tags,

            opts=ResourceOptions(provider=databricks_provider)
        )
    # High Concurrency Cluster Type
    elif cluster_config["type"] == "high_concurrency":
        clusters[ref_key] = databricks.Cluster(
            resource_name=cluster_resource_name,
            cluster_name=cluster_config["display_name"],

            spark_version=cluster_config["spark_version"],

            node_type_id=cluster_config["node_type_id"],

            autotermination_minutes=cluster_config["autotermination_minutes"],

            docker_image=databricks.ClusterDockerImageArgs(
                url=cluster_config["docker_image_url"]
            ) if cluster_config.get("docker_image_url") else None,

            autoscale=databricks.ClusterAutoscaleArgs(
                min_workers=cluster_config["auto_scale_min_workers"],
                max_workers=cluster_config["auto_scale_max_workers"]
            ),

            azure_attributes=databricks.ClusterAzureAttributesArgs(
                availability="SPOT_WITH_FALLBACK_AZURE",
                first_on_demand=1,
                spot_bid_max_price=100
            ),

            libraries=cluster_libraries or None,

            spark_env_vars={
                "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
            } | (cluster_config.get("spark_env_vars") or {}),

            spark_conf={
                "spark.databricks.cluster.profile": "serverless",
                "spark.databricks.repl.allowedLanguages": "python,sql",
                "spark.databricks.passthrough.enabled": "true",
                "spark.databricks.pyspark.enableProcessIsolation": "true",
                "spark.databricks.delta.preview.enabled": "true"
            } | (cluster_config.get("spark_conf") or {}),

            custom_tags={
                "ResourceClass": "Serverless"
            } | p.tags,

            opts=ResourceOptions(provider=databricks_provider)
        )
