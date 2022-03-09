from pulumi_azure_native import containerservice

from project_config import platform_config

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

# Only create if a system requires it
cluster_required = any(config["config"]["enabled"] for config in configs)
cluster_windows_required = any(
    config["config"]["enabled"] and config["os"] == containerservice.OSType.WINDOWS
    for config in configs
)
