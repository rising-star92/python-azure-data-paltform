from pulumi_azure_native import containerregistry as acr

from ingenii_azure_data_platform.contracts.packages import PackageInputArgs


def init(args: PackageInputArgs) -> None:
    STACK = args.platform_config.stack
    REGION = args.platform_config.region
    PREFIX = args.platform_config.prefix
    UNIQUE_ID = args.platform_config.unique_id

    # Package Config Inputs
    _registry_name = args.package_config.get("registry_name", "adpcr")
    _sku = args.package_config.get("sku", "Standard")
    _resource_group_name = args.package_config.get("resource_group_name", "data")
    _admin_user_enabled = args.package_config.get("admin_user_enabled", False)
    _region = args.package_config.get("region", REGION.long_name)

    resource_group_name = args.shared_outputs.apply(
        lambda outputs: outputs["management"]["resource_groups"][_resource_group_name][
            "name"
        ]
    )

    registry = acr.Registry(
        resource_name=f"{args.namespace}-{server_name}-admin-creds",
        admin_user_enabled=True,
        location=_region,
        registry_name="myRegistry",
        resource_group_name=resource_group_name,
        sku=acr.SkuArgs(
            name=_sku,
        ),
        tags={
            "key": "value",
        },
    )
