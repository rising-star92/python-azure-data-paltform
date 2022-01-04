from base64 import b64decode
import hiyapyco as hco
from pulumi import ResourceOptions
from pulumi_azure_native import containerservice
import pulumi_random
from pulumi_kubernetes import Provider, core

from ingenii_azure_data_platform.iam import GroupRoleAssignment
from ingenii_azure_data_platform.utils import generate_resource_name

from management import resource_groups, user_groups
from network.vnet import hosted_services_subnet
from project_config import platform_config, platform_outputs

runtime_config = platform_config["analytics_services"]["datafactory"]["integrated_self_hosted_runtime"]

# ----------------------------------------------------------------------------------------------------------------------
# SHARED KUBERNETES CLUSTER
# ----------------------------------------------------------------------------------------------------------------------

cluster_resource_name = "shared_cluster"
resource_group_name = resource_groups["infra"].name

if runtime_config["enabled"]:
    outputs = platform_outputs["analytics"]["shared_kubernetes_cluster"] = {}

    admin_password = pulumi_random.RandomPassword(
        resource_name=generate_resource_name(
            resource_type="random_password",
            resource_name=cluster_resource_name,
            platform_config=platform_config,
        ),
        length=16,
        special=True,
        override_special="_%@",
    )

    # Note: Windows pool names must be 6 characters or fewer: https://docs.microsoft.com/en-us/azure/aks/windows-container-cli#limitations
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
            containerservice.ManagedClusterAgentPoolProfileArgs(
                availability_zones=["1"],
                count=1,
                enable_auto_scaling=True,
                max_count=1,
                min_count=1,
                mode="System",
                name="systempool",
                node_labels={"OS": "Linux"},
                os_type=containerservice.OSType.LINUX,
                type="VirtualMachineScaleSets",
                vm_size="Standard_B2ms",
                vnet_subnet_id=hosted_services_subnet.id
            ),
            containerservice.ManagedClusterAgentPoolProfileArgs(
                availability_zones=["1"],
                count=1,
                enable_auto_scaling=True,
                max_count=1,
                min_count=1,
                mode="User",
                name="win1",
                node_labels={"OS": "Windows"},
                os_type=containerservice.OSType.WINDOWS,
                type="VirtualMachineScaleSets",
                vm_size="Standard_B2ms",
                vnet_subnet_id=hosted_services_subnet.id
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
            network_policy=containerservice.NetworkPolicy.AZURE
        ),
        resource_group_name=resource_group_name,
        sku=containerservice.ManagedClusterSKUArgs(
            name=containerservice.ManagedClusterSKUName.BASIC,
            tier=containerservice.ManagedClusterSKUTier.FREE,
        ),
        tags=platform_config.tags,
        windows_profile=containerservice.ManagedClusterWindowsProfileArgs(
            admin_password=admin_password.result,
            admin_username="runtimeclusteradmin",
        ),
    )

    # TODO: Potentially implement
    #    identity_profile: Optional[Mapping[str, ManagedClusterPropertiesIdentityProfileArgs]] = None,
    #    private_link_resources: Optional[Sequence[PrivateLinkResourceArgs]] = None,

    for attr in ["fqdn", "id", "name"]:
        outputs[attr] = getattr(kubernetes_cluster, attr)
    outputs["resource_group_name"] = resource_group_name.apply(lambda name: name)

    # ----------------------------------------------------------------------------------------------------------------------
    # SHARED KUBERNETES CLUSTER -> ROLE ASSIGNMENTS
    # ----------------------------------------------------------------------------------------------------------------------

    for assignment in runtime_config.get("iam", {}).get("role_assignments", []):
        # User Group Assignment
        user_group_ref_key = assignment.get("user_group_ref_key")
        if user_group_ref_key is not None:
            GroupRoleAssignment(
                principal_id=user_groups[user_group_ref_key]["object_id"],
                principal_name=user_group_ref_key,
                role_name=assignment["role_definition_name"],
                scope=kubernetes_cluster.id,
                scope_description="kubernetes-cluster"
            )
