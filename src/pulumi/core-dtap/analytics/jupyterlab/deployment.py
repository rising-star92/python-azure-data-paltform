import pulumi_azuread as azuread
from pulumi import ResourceOptions, Output
from pulumi_azure_native import network, containerservice
from pulumi_kubernetes import core, helm

from ingenii_azure_data_platform.utils import generate_resource_name

from platform_shared import (
    shared_kubernetes_cluster_configs,
    shared_kubernetes_provider,
    shared_services_provider,
)
from project_config import azure_client, platform_config, platform_outputs, \
    SHARED_OUTPUTS

jupyterlab_config = shared_kubernetes_cluster_configs["jupyterlab"]

if jupyterlab_config["enabled"]:

    outputs = platform_outputs["analytics"]["jupyterlab"] = {}

    resource_name = f"jupyterlab-{platform_config.stack}"
    kubernetes_node_resource_group_name = SHARED_OUTPUTS.get(
        "analytics",
        "shared_kubernetes_cluster",
        "node_resource_group_name",
        preview="Preview-Kubernetes-Resource-Group-Name",
    )

    hub_public_ip = network.PublicIPAddress(
        resource_name=generate_resource_name(
            resource_type="public_ip",
            resource_name=resource_name,
            platform_config=platform_config,
        ),
        public_ip_address_version=network.IPVersion.I_PV4,
        public_ip_allocation_method=network.IPAllocationMethod.STATIC,
        resource_group_name=kubernetes_node_resource_group_name,
        sku=network.PublicIPAddressSkuArgs(
            name=network.PublicIPAddressSkuName.STANDARD,
            tier=network.PublicIPAddressSkuTier.REGIONAL,
        ),
        tags=platform_config.tags,
        opts=ResourceOptions(provider=shared_services_provider),
    )

    callback_url = hub_public_ip.ip_address.apply(
        lambda ip: f"http://{ip}/hub/oauth_callback")

    auth_application = azuread.Application(
        resource_name=resource_name,
        display_name=f"Ingenii Azure Data Platform JupyterHub Authentication - {platform_config.stack}",
        feature_tags=[azuread.ApplicationFeatureTagArgs(enterprise=True)],
        owners=[azure_client.object_id],
        required_resource_accesses=[
            azuread.ApplicationRequiredResourceAccessArgs(
                resource_accesses=[azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                    id="e1fe6dd8-ba31-4d61-89e7-88639da4683d",
                    type="Scope",
                )],
                resource_app_id="00000003-0000-0000-c000-000000000000",
            )
        ],
        web=azuread.ApplicationWebArgs(redirect_uris=[callback_url]),
    )
    auth_service_principal = azuread.ServicePrincipal(
        resource_name=resource_name,
        application_id=auth_application.application_id,
        app_role_assignment_required=jupyterlab_config.get("require_assignment", True),
    )
    auth_service_principal_password = azuread.ServicePrincipalPassword(
        resource_name=resource_name,
        service_principal_id=auth_service_principal.object_id,
    )

    node_selector = {"OS": containerservice.OSType.LINUX}
    chart_values = Output.all(
        callback_url=callback_url, public_ip=hub_public_ip.ip_address
    ).apply(
        lambda args: {
        "hub": {
            "config": {
                "Authenticator": {
                    "auto_login": True
                },
                "AzureAdOAuthenticator": {
                    "client_id": auth_application.application_id,
                    "client_secret": auth_service_principal_password.value,
                    "oauth_callback_url": args["callback_url"],
                    "tenant_id": azure_client.tenant_id,
                },
                "JupyterHub": {
                    "authenticator_class": "azuread"
                }
            },
            "extraConfig":{
                "add-jupyterlab": "c.Spawner.cmd=['jupyter-labhub']"
            },
            "nodeSelector": node_selector
        },
        "prePuller": {
            "hook": {
                "nodeSelector": node_selector
            }
        },
        "proxy": {
            "chp": {
                "nodeSelector": node_selector
            },
            "service": {
                "loadBalancerIP": args["public_ip"]
            },
            "traefik": {
                "nodeSelector": node_selector
            }
        },
        "scheduling": {
            "userScheduler": {
                "nodeSelector": node_selector
            }
        },
        "singleuser": {
            "nodeSelector": node_selector,
            "storage": {
                "dynamic": {
                    "storageClass": "azurefile"
                }
            }
        },
    })
    jupyterlab = helm.v3.Release(
        resource_name=resource_name,
        chart="jupyterhub",
        create_namespace=True,
        namespace=resource_name,
        repository_opts=helm.v3.RepositoryOptsArgs(repo="https://jupyterhub.github.io/helm-chart/"),
        timeout=600,
        values=chart_values,
        version=jupyterlab_config["version"],
        opts=ResourceOptions(provider=shared_kubernetes_provider)
    )

    outputs.update({
        "id": jupyterlab.id,
        "name": jupyterlab.name,
        "namespace": jupyterlab.namespace,
        "public_ip": hub_public_ip.ip_address.apply(lambda ip: ip)
    })
