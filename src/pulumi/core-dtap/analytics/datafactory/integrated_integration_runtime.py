from base64 import b64decode, b64encode
from pulumi import InvokeOptions, ResourceOptions
from pulumi_azure_native import containerservice
from pulumi_azure import datafactory as adf
from pulumi_kubernetes import Provider, apps, core, meta

from analytics.datafactory.datafactories import data_datafactories, datafactory_resource_group
from platform_shared import (
    SHARED_OUTPUTS,
    shared_services_provider,
    shared_platform_config,
)
from project_config import platform_config, platform_outputs

# ----------------------------------------------------------------------------------------------------------------------
# DATA FACTORY -> INTEGRATED INTEGRATION RUNTIME
# ----------------------------------------------------------------------------------------------------------------------

runtime_config = shared_platform_config["analytics_services"]["datafactory"]["integrated_self_hosted_runtime"]

if runtime_config["enabled"]:

    overall_outputs = platform_outputs["analytics"]["datafactory"]["integrated_integration_runtime"] = {}

    # ----------------------------------------------------------------------------------------------------------------------
    # DATA FACTORY RUNTIME -> ACCESS
    # ----------------------------------------------------------------------------------------------------------------------

    # Use the admin credential as it's static
    # TODO: Don't do this - add Pulumi service principal as Azure Kubernetes Service RBAC Cluster Admin

    def get_credentials(cluster_details):
        if cluster_details is None:
            return "Preview Kubernetes Config"
        return b64decode(
            containerservice.list_managed_cluster_admin_credentials(
                resource_group_name=cluster_details["resource_group_name"],
                resource_name=cluster_details["name"],
                opts=InvokeOptions(provider=shared_services_provider)
            ).kubeconfigs[0].value
        ).decode()

    kube_config = SHARED_OUTPUTS.get(
        "analytics", "shared_kubernetes_cluster").apply(get_credentials)

    kubernetes_provider = Provider(
        "datafactory_kubernetes_provider", kubeconfig=kube_config
    )

    # ----------------------------------------------------------------------------------------------------------------------
    # DATA FACTORY RUNTIME -> NAMESPACE
    # ----------------------------------------------------------------------------------------------------------------------

    namespace = core.v1.Namespace(
        resource_name=f"datafactory-runtime-{platform_config.stack}",
        metadata={},
        opts=ResourceOptions(provider=kubernetes_provider)
    )
    overall_outputs["namespace"] = namespace.metadata.name


    # A container per Data Factory
    for ref_key, datafactory in data_datafactories.items():

        outputs = overall_outputs[ref_key] = {}

        integrated_integration_runtime = adf.IntegrationRuntimeSelfHosted(
            resource_name=f"datafactory_integrated_runtime_{platform_config.stack}",
            data_factory_id=datafactory["obj"].id,
            name="IntegratedIntegrationRuntime",
            description="Integrated integration runtime provided by Ingenii",
            resource_group_name=datafactory_resource_group.name,
        )

        labels = {
            "data_factory": datafactory["name"],
            "type": "DataFactorySelfHostedIntegrationRuntime",
            "system": "IngeniiDataPlatform"
        }

        # ----------------------------------------------------------------------------------------------------------------------
        # DATA FACTORY RUNTIME -> SECRET -> AUTH KEY
        # ----------------------------------------------------------------------------------------------------------------------

        auth_key_secret_name = f"data-factory-runtime-auth-key-{ref_key}-{platform_config.stack}"
        auth_key_secret = core.v1.Secret(
            resource_name=auth_key_secret_name,
            data={
                auth_key_secret_name: integrated_integration_runtime.auth_key1.apply(
                    lambda key: b64encode(key.encode()).decode()
                ),
            },
            metadata=meta.v1.ObjectMetaArgs(
                labels=labels, 
                namespace=namespace.id
            ),
            opts=ResourceOptions(provider=kubernetes_provider, ignore_changes=["data"])
        )

        # ----------------------------------------------------------------------------------------------------------------------
        # DATA FACTORY RUNTIME -> RUNTIME CONTAINER
        # ----------------------------------------------------------------------------------------------------------------------

        deployment = apps.v1.Deployment(
            resource_name=f"datafactory-runtime-deployment-{ref_key}-{platform_config.stack}",
            metadata=meta.v1.ObjectMetaArgs(
                labels=labels,
                namespace=namespace.id
            ),
            spec=apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=meta.v1.LabelSelectorArgs(
                    match_labels=labels,
                ),
                template=core.v1.PodTemplateSpecArgs(
                    metadata=meta.v1.ObjectMetaArgs(
                        labels=labels,
                    ),
                    spec=core.v1.PodSpecArgs(
                        containers=[core.v1.ContainerArgs(
                            name=f"datafactory-runtime-{ref_key}-{platform_config.stack}",
                            image=runtime_config["image"],
                            env=[
                                core.v1.EnvVarArgs(
                                    name="NODE_NAME", 
                                    value=f"kubernetes_node_{ref_key}_{platform_config.stack}"
                                ),
                                core.v1.EnvVarArgs(
                                    name="AUTH_KEY",
                                    value_from=core.v1.EnvVarSourceArgs(
                                        secret_key_ref=core.v1.SecretKeySelectorArgs(
                                            key=auth_key_secret_name,
                                            name=auth_key_secret.metadata.name,
                                        )
                                    )
                                ),
                                core.v1.EnvVarArgs(name="ENABLE_HA", value="true"),
                            ],
                            ports=[
                                core.v1.ContainerPortArgs(container_port=port)
                                for port in (80, 8060)
                            ],
                        )],
                        node_selector={"OS": "Windows"},
                    ),
                ),
            ),
            opts=ResourceOptions(provider=kubernetes_provider, depends_on=[auth_key_secret])
        )

        outputs["deployment"] = deployment.metadata.name