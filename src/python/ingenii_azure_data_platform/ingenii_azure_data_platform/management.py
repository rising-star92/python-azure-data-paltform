import pulumi_azure_native as azure_native
import pulumi_azuread as azuread
from ingenii_azure_data_platform.config import PlatformConfiguration
from ingenii_azure_data_platform.utils import generate_resource_name


class ResourceGroup(azure_native.resources.ResourceGroup):
    """
    #TODO
    """

    def __init__(
        self, resource_group_name: str, platform_config: PlatformConfiguration
    ):
        name = generate_resource_name(
            resource_type="resource_group",
            resource_name=resource_group_name,
            platform_config=platform_config,
        )
        super().__init__(
            resource_name=name,
            resource_group_name=name,
            location=platform_config.region.long_name,
            tags=platform_config.tags,
        )


class UserGroup(azuread.Group):
    """
    #TODO
    """

    def __init__(
        self,
        group_name: str,
        platform_config: PlatformConfiguration,
        description: str = None,
    ):
        name = generate_resource_name(
            resource_type="user_group",
            resource_name=group_name,
            platform_config=platform_config,
        )
        super().__init__(
            resource_name=name.lower(), display_name=name, description=description
        )
