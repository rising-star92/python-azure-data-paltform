import os
import pulumi_azure_native as azure_native
from pulumi import ResourceOptions
from pulumi_databricks import Provider as DatabricksProvider
from pulumi_databricks import ProviderArgs as DatabricksProviderArgs
from pulumi_databricks import databricks
from config import platform as p
from config import azure_client
from management import resource_groups, user_groups
from network import vnet

# ----------------------------------------------------------------------------------------------------------------------
# ANALYTICS DATABRICKS WORKSPACE
# ----------------------------------------------------------------------------------------------------------------------
workspace_config = p.config_object["analytics_services"]["databricks"]["workspaces"]["analytics"]
workspace_short_name = "analytics"
workspace_name = p.generate_name("databricks_workspace", workspace_short_name)
workspace_managed_resource_group_name = f"/subscriptions/{azure_client.subscription_id}/resourceGroups/{p.generate_name('resource_group', f'dbw-{workspace_short_name}')}"

workspace = azure_native.databricks.Workspace(
    resource_name=workspace_name,
    workspace_name=workspace_name,
    location=p.region_long_name,
    managed_resource_group_id=workspace_managed_resource_group_name,
    parameters=azure_native.databricks.WorkspaceCustomParametersArgs(
        custom_private_subnet_name=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.dbw_analytics_containers_subnet.name,
        ),
        custom_public_subnet_name=azure_native.databricks.WorkspaceCustomStringParameterArgs(
            value=vnet.dbw_analytics_hosts_subnet.name,
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
# ANALYTICS DATABRICKS WORKSPACE -> IAM ROLE ASSIGNMENTS
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
# ANALYTICS DATABRICKS WORKSPACE -> GENERAL CONFIG
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
# ANALYTICS DATABRICKS WORKSPACE -> CLUSTERS
# ----------------------------------------------------------------------------------------------------------------------

# If no clusters are defined in the YAML files, we'll not attempt to create any.
try:
    cluster_definitions = workspace_config["clusters"]
except:
    cluster_definitions = {}

clusters = {}
for ref_key in cluster_definitions:
    cluster_config = cluster_definitions[ref_key]
    cluster_resource_name = p.generate_name(
        "databricks_cluster", f'{workspace_short_name}-{ref_key}')

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
