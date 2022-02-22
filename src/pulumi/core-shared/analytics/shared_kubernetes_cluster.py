import platform
from pulumi import ResourceOptions
import pulumi_random
from pulumi_azure_native import containerservice

from ingenii_azure_data_platform.iam import GroupRoleAssignment
from ingenii_azure_data_platform.utils import generate_resource_name, lock_resource

from management import resource_groups, resource_group_outputs, user_groups
from network.vnet import hosted_services_subnet
from project_config import azure_client, platform_config, platform_outputs

# ----------------------------------------------------------------------------------------------------------------------
# SHARED KUBERNETES CLUSTER -> BASE CONFIGURATIONS
# ----------------------------------------------------------------------------------------------------------------------

cluster_resource_name = "shared_cluster"
cluster_resource_group_name = resource_groups["infra"].name
configs = [
    {
        "config": platform_config["analytics_services"]["datafactory"]["integrated_self_hosted_runtime"],
        "os": containerservice.OSType.WINDOWS,
    },
    {
        "config": platform_config["analytics_services"]["jupyterlab"],
        "os": containerservice.OSType.LINUX,
    },
]
outputs = platform_outputs["analytics"]["shared_kubernetes_cluster"] = {}

# Only create if a system requires it
if any(config["config"]["enabled"] for config in configs):
    
    # ----------------------------------------------------------------------------------------------------------------------
    # SHARED KUBERNETES CLUSTER -> NODE RESOURCE GROUP NAME
    # ----------------------------------------------------------------------------------------------------------------------

    # Resource group for Kubernetes nodes, otherwise Azure will create one
    resource_group_config = platform_config["shared_kubernetes_cluster"]["resource_group"]
    node_resource_group_name = generate_resource_name(
            resource_type="resource_group",
            resource_name=resource_group_config["display_name"],
            platform_config=platform_config,
        )

    # ----------------------------------------------------------------------------------------------------------------------
    # SHARED KUBERNETES CLUSTER -> CLUSTER
    # ----------------------------------------------------------------------------------------------------------------------

    windows_admin_password = pulumi_random.RandomPassword(
        resource_name=generate_resource_name(
            resource_type="random_password",
            resource_name=cluster_resource_name,
            platform_config=platform_config,
        ),
        length=32,
        min_lower=1,
        min_numeric=1,
        min_special=1,
        min_upper=1,
        override_special="_%@",
    )

    kubernetes_cluster = containerservice.ManagedCluster(
        resource_name=generate_resource_name(
            resource_type="kubernetes_cluster",
            resource_name=cluster_resource_name,
            platform_config=platform_config,
        ),
        aad_profile=containerservice.ManagedClusterAADProfileArgs(
            admin_group_object_ids=[user_groups["admins"]["object_id"]],
            enable_azure_rbac=True,
            managed=True,
        ),
        agent_pool_profiles=[
            # At minimum, the cluster requires a system Linux pool
            containerservice.ManagedClusterAgentPoolProfileArgs(
                availability_zones=["1"],
                count=1,
                enable_auto_scaling=True,
                max_count=1,
                min_count=1,
                mode=containerservice.AgentPoolMode.SYSTEM,
                name="systempool",
                node_labels={"OS": containerservice.OSType.LINUX},
                os_type=containerservice.OSType.LINUX,
                type=containerservice.AgentPoolType.VIRTUAL_MACHINE_SCALE_SETS,
                vm_size="Standard_B2ms",
                vnet_subnet_id=hosted_services_subnet.id,
            ),
        ],
        auto_upgrade_profile=containerservice.ManagedClusterAutoUpgradeProfileArgs(
            upgrade_channel=containerservice.UpgradeChannel.STABLE
        ),
        disable_local_accounts=False,
        dns_prefix=cluster_resource_name.replace("_", ""),
        enable_rbac=True,
        identity=containerservice.ManagedClusterIdentityArgs(
            type=containerservice.ResourceIdentityType.SYSTEM_ASSIGNED
        ),
        location=platform_config.region.long_name,
        network_profile=containerservice.ContainerServiceNetworkProfileArgs(
            network_mode=containerservice.NetworkMode.TRANSPARENT,
            network_plugin=containerservice.NetworkPlugin.AZURE,
            network_policy=containerservice.NetworkPolicy.AZURE,
        ),
        node_resource_group=node_resource_group_name,
        opts=ResourceOptions(delete_before_replace=True),
        resource_group_name=cluster_resource_group_name,
        sku=containerservice.ManagedClusterSKUArgs(
            name=containerservice.ManagedClusterSKUName.BASIC,
            tier=containerservice.ManagedClusterSKUTier.FREE,
        ),
        tags=platform_config.tags,
        windows_profile=containerservice.ManagedClusterWindowsProfileArgs(
            admin_password=windows_admin_password.result,
            admin_username="runtimeclusteradmin",
        ),
    )
    if platform_config.resource_protection:
        lock_resource("shared_kubernetes_cluster", kubernetes_cluster.id)

    # TODO: Potentially implement
    #    identity_profile: Optional[Mapping[str, ManagedClusterPropertiesIdentityProfileArgs]] = None,
    #    private_link_resources: Optional[Sequence[PrivateLinkResourceArgs]] = None,

    outputs.update({
        "cluster_resource_group_name": cluster_resource_group_name.apply(lambda name: name),
        "fqdn": kubernetes_cluster.fqdn,
        "id": kubernetes_cluster.id,
        "name": kubernetes_cluster.name,
        "node_resource_group_name": node_resource_group_name,
        "principal_id": kubernetes_cluster.identity.principal_id,
    })

    # ----------------------------------------------------------------------------------------------------------------------
    # SHARED KUBERNETES CLUSTER -> ROLE ASSIGNMENTS
    # ----------------------------------------------------------------------------------------------------------------------

    for assignment in platform_config["shared_kubernetes_cluster"]["cluster"]["iam"]["role_assignments"]:
        # User Group Assignment
        user_group_ref_key = assignment.get("user_group_ref_key")
        if user_group_ref_key is not None:
            GroupRoleAssignment(
                principal_id=user_groups[user_group_ref_key]["object_id"],
                principal_name=user_group_ref_key,
                role_name=assignment["role_definition_name"],
                scope=kubernetes_cluster.id,
                scope_description="kubernetes-cluster",
            )

    # ----------------------------------------------------------------------------------------------------------------------
    # SHARED KUBERNETES CLUSTER -> NODE RESOURCE GROUP ASSIGNMENTS
    # ----------------------------------------------------------------------------------------------------------------------

    node_resource_group_id = kubernetes_cluster.node_resource_group.apply(
        lambda rg_name: f"/subscriptions/{azure_client.subscription_id}/resourceGroups/{rg_name}"
    )

    # Export resource group metadata
    resource_group_outputs["kubernetes"] = {
        "name": node_resource_group_name,
        "location": kubernetes_cluster.location,
        "id": node_resource_group_id,
    }
    for assignment in resource_group_config["iam"]["role_assignments"]:
        # User Group Assignment
        user_group_ref_key = assignment.get("user_group_ref_key")
        if user_group_ref_key is not None:
            GroupRoleAssignment(
                principal_id=user_groups[user_group_ref_key]["object_id"],
                principal_name=user_group_ref_key,
                role_name=assignment["role_definition_name"],
                scope=node_resource_group_id,
                scope_description="kubernetes-cluster-node-resource-group",
            )

    # ----------------------------------------------------------------------------------------------------------------------
    # SHARED KUBERNETES CLUSTER -> AGENT POOLS
    # ----------------------------------------------------------------------------------------------------------------------

    for idx, pool in enumerate(platform_config["shared_kubernetes_cluster"]["cluster"].get("linux_agent_pools", [])):
        agent_pool_name = pool.get("name", f"linux{idx}")
        containerservice.AgentPool(
            resource_name=generate_resource_name(
                resource_type="kubernetes_agent_pool",
                resource_name=agent_pool_name,
                platform_config=platform_config,
            ),
            agent_pool_name=agent_pool_name,
            availability_zones=pool.get("availability_zones", ["1"]),
            count=pool.get("count", 1),
            enable_auto_scaling=pool.get("auto_scaling", True),
            max_count=pool.get("max_count", 1),
            min_count=pool.get("min_count", 1),
            mode=containerservice.AgentPoolMode.USER,
            node_labels={
                **pool.get("labels", {}),
                "OS": containerservice.OSType.LINUX,
            },
            os_type=containerservice.OSType.LINUX,
            resource_group_name=cluster_resource_group_name,
            resource_name_=kubernetes_cluster.name,
            tags=platform_config.tags,
            type=containerservice.AgentPoolType.VIRTUAL_MACHINE_SCALE_SETS,
            vm_size=pool.get("vm_size", "Standard_B2ms"),
            vnet_subnet_id=hosted_services_subnet.id,
        )

    # Check if any of the enabled features need Windows machines
    need_windows = any(
        config["config"]["enabled"] and config["os"] == containerservice.OSType.WINDOWS
        for config in configs
    )
    windows_pools = platform_config["shared_kubernetes_cluster"]["cluster"].get("windows_agent_pools", [])
    if need_windows and not windows_pools:
        windows_pools = [{
            "labels": {"addedBy": "platform"},
            "name": "win1"
        }]

    for idx, pool in enumerate(windows_pools):
        # Note: Windows pool names must be 6 characters or fewer: https://docs.microsoft.com/en-us/azure/aks/windows-container-cli#limitations
        agent_pool_name = pool.get("name", f"win{idx}")
        containerservice.AgentPool(
            resource_name=generate_resource_name(
                resource_type="kubernetes_agent_pool",
                resource_name=agent_pool_name,
                platform_config=platform_config,
            ),
            agent_pool_name=agent_pool_name,
            availability_zones=pool.get("availability_zones", ["1"]),
            count=pool.get("count", 1),
            enable_auto_scaling=pool.get("auto_scaling", True),
            max_count=pool.get("max_count", 1),
            min_count=pool.get("min_count", 1),
            mode=containerservice.AgentPoolMode.USER,
            node_labels={
                **pool.get("labels", {}),
                "OS": containerservice.OSType.WINDOWS,
            },
            os_type=containerservice.OSType.WINDOWS,
            resource_group_name=cluster_resource_group_name,
            resource_name_=kubernetes_cluster.name,
            tags=platform_config.tags,
            type=containerservice.AgentPoolType.VIRTUAL_MACHINE_SCALE_SETS,
            vm_size=pool.get("vm_size", "Standard_B2ms"),
            vnet_subnet_id=hosted_services_subnet.id,
        )
