from os import getcwd, environ
import pulumi_azuread as azuread
from pulumi import ResourceOptions, Output
from pulumi_azure_native import network, containerservice
from pulumi_kubernetes import helm
import pulumi_random

from ingenii_azure_data_platform.utils import generate_resource_name

from analytics.quantum.workspace import outputs as quantum_outputs
from platform_shared import (
    shared_kubernetes_provider,
    shared_platform_config,
    shared_services_provider,
)
from project_config import azure_client, DTAP_ROOT, ingenii_workspace_dns_provider, \
    platform_config, platform_outputs, SHARED_OUTPUTS

jupyterlab_config = shared_platform_config["analytics_services"]["jupyterlab"]

if jupyterlab_config["enabled"]:

    outputs = platform_outputs["analytics"]["jupyterlab"] = {}

    resource_name = f"jupyterlab-{platform_config.stack}"
    kubernetes_node_resource_group_name = SHARED_OUTPUTS.get(
        "analytics",
        "shared_kubernetes_cluster",
        "node_resource_group_name",
        preview="Preview-Kubernetes-Resource-Group-Name",
    )

    #----------------------------------------------------------------------------------------------------------------------
    # JUPYTERLAB -> IP ADDRESS AND HTTPS
    #----------------------------------------------------------------------------------------------------------------------

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

    https_settings = platform_config["analytics_services"].get("jupyterlab", {}).get("https", {})
    # HTTPS is on by default
    if https_settings.get("custom_hostname"):
        # Client has provided custom hostname details
        hostname = https_settings["custom_hostname"].strip("/")
        contact_email = https_settings["contact_email"]
        record_set = None
    else:
        # Ingenii provides the hostname
        relative_name = f"{platform_config.unique_id}-{platform_config.prefix}-{platform_config.stack}"
        zone_name = "workspace.ingenii.io"
        record_set = network.RecordSet(
            generate_resource_name(
                resource_type="dns_zone",
                resource_name=zone_name,
                platform_config=platform_config,
            ),
            a_records=[network.ARecordArgs(
                ipv4_address=hub_public_ip.ip_address,
            )],
            metadata={
                "env": platform_config.stack,
                "prefix": platform_config.prefix,
                "unique_id": platform_config.unique_id,
            },
            record_type="A",
            relative_record_set_name=relative_name,
            resource_group_name=environ["WORKSPACE_DNS_RESOURCE_GROUP_NAME"],
            ttl=3600,
            zone_name=zone_name,
            opts=ResourceOptions(provider=ingenii_workspace_dns_provider),
        )
        hostname = f"{relative_name}.{zone_name}"
        contact_email = "support@ingenii.dev"
    callback_url = f"https://{hostname}/hub/oauth_callback"

    if not https_settings.get("enabled", True):
        # Client has turned off HTTPS
        # If Ingenii provided, record set will still be created
        hostname, contact_email, record_set = None, None, None
        callback_url = hub_public_ip.ip_address.apply(
            lambda ip: f"http://{ip}/hub/oauth_callback")

    #----------------------------------------------------------------------------------------------------------------------
    # JUPYTERLAB -> AUTHENTICATION -> APPLICATION
    #----------------------------------------------------------------------------------------------------------------------

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

    #----------------------------------------------------------------------------------------------------------------------
    # JUPYTERLAB -> AUTHENTICATION -> ENCRYPTION 
    #----------------------------------------------------------------------------------------------------------------------

    # Encryption key to persis the auth state
    encryption_key = pulumi_random.RandomString(
        resource_name=generate_resource_name(
            resource_type="random_string",
            resource_name="jupyterhub_encryption_key",
            platform_config=platform_config,
        ),
        length=32
    )
    encryption_key_hex = encryption_key.result.apply(
        lambda rstring: rstring.encode("utf-8").hex()
    )

    #----------------------------------------------------------------------------------------------------------------------
    # JUPYTERLAB -> CHART AND DEPLOYMENT
    #----------------------------------------------------------------------------------------------------------------------

    # Get the extra configurations
    with open(DTAP_ROOT + "/analytics/jupyterlab/configs/token_passing_authenticator.py") as auth_conf:
        authentication_config = auth_conf.read()

    def create_chart_values(kwargs):
        node_selector = {"OS": containerservice.OSType.LINUX}
        values = {
            "hub": {
                "config": {
                    "Authenticator": {
                        "auto_login": True,
                    },
                    "AzureAdTokenOAuthenticator": {
                        "client_id": auth_application.application_id,
                        "client_secret": auth_service_principal_password.value,
                        "oauth_callback_url": kwargs["callback_url"],
                        "scope": ["User.Read", "offline_access"],
                        "tenant_id": azure_client.tenant_id,
                    },
                },
                "extraConfig":{
                    "add-jupyterlab": "c.Spawner.cmd=['jupyter-labhub']",
                    "authentication": authentication_config,
                },
                "extraEnv": {
                    "JUPYTERHUB_CRYPT_KEY": kwargs["encryption_key"],
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
                    "loadBalancerIP": kwargs["public_ip"]
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
                "nodeSelector": node_selector
            },
        }
        quantum_workspace_name = kwargs["quantum_workspace_name"]
        if quantum_workspace_name:
            values["singleuser"]["extraEnv"] = {
                "WORKSPACE_SUBSCRIPTION_ID": azure_client.subscription_id,
                "WORKSPACE_RESOURCE_GROUP": quantum_outputs["workspace"]["resource_group_name"],
                "WORKSPACE_LOCATION": quantum_outputs["workspace"]["location"],
                "WORKSPACE_NAME": quantum_workspace_name,
            }
            values["singleuser"]["image"] = {"name": "ingeniisolutions/jupyterhub-singleuser"}
        if hostname:
            values["proxy"]["https"] = {
                "enabled": True,
                "hosts": [hostname],
                "letsencrypt": {"contactEmail": contact_email,},
            }

        return values

    chart_values = Output.all(
        callback_url=callback_url, public_ip=hub_public_ip.ip_address,
        record_set=record_set, encryption_key=encryption_key_hex,
        quantum_workspace_name=quantum_outputs.get("workspace", {}).get("name"),
    ).apply(create_chart_values)
    jupyterlab = helm.v3.Release(
        resource_name=resource_name,
        chart=f"{getcwd()}/../../helm_charts/jupyterhub",
        create_namespace=True,
        namespace=resource_name,
        timeout=600,
        values=chart_values,
        version=jupyterlab_config["version"],
        opts=ResourceOptions(provider=shared_kubernetes_provider)
    )
    #     chart="jupyterhub",
    #     repository_opts=helm.v3.RepositoryOptsArgs(repo="https://jupyterhub.github.io/helm-chart/"),

    outputs.update({
        "id": jupyterlab.id,
        "name": jupyterlab.name,
        "namespace": jupyterlab.namespace,
        "url": hostname or hub_public_ip.ip_address
    })
