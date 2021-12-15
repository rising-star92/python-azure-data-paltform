import pulumi
from os import getcwd, getenv
from pulumi_azure_native.authorization import get_client_config
from ingenii_azure_data_platform.config import PlatformConfiguration

# Load the config files.
platform_config = PlatformConfiguration(
    stack=pulumi.get_stack(),
    config_schema_file_path=getenv(
        "ADP_CONFIG_SCHEMA_FILE_PATH", "../../platform-config/schema.yml"
    ),
    default_config_file_path=getenv(
        "ADP_DEFAULT_CONFIG_FILE_PATH", "../../platform-config/defaults.yml"
    ),
    custom_config_file_path=getenv("ADP_CUSTOM_CONFIGS_FILE_PATH"),
)

# Load the current Azure auth session metadata
azure_client = get_client_config()

PULUMI_ORG_NAME = "ingenii"
CURRENT_STACK_NAME = pulumi.get_stack()
CURRENT_PROJECT_NAME = pulumi.get_project()

SHARED_OUTPUTS = pulumi.StackReference(
    "/".join(
        [PULUMI_ORG_NAME, CURRENT_PROJECT_NAME.replace("dtap", "shared"), "shared"]
    )
).get_output("root")

DTAP_ROOT = getcwd()

# Outputs
platform_outputs = {}

pulumi.export("root", platform_outputs)
