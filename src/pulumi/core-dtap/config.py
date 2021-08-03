from pulumi import get_stack
from pulumi_azure_native.authorization import get_client_config
from ingenii_azure_data_platform.general import ConfigParser, PlatformConfiguration
from ingenii_azure_data_platform import helpers

# Load the config files.
config_object = ConfigParser(
    schema_path="./schema.yml",
    default_config_path="./defaults.yml",
    customer_config_path=f"**/configs/{get_stack()}.yml").validate_schema().load_as_dynaconf()
)

# The platform configuration object.
# It holds all config data needed from the rest of the resources.
platform = PlatformConfiguration(
    stack=get_stack(), config_object=config_object)

# Helper functions
helpers = helpers

# Metadata about the current Azure environment.
# subscription_id, client_id, tenant_id etc...
azure_client = get_client_config()
