import os
from ipaddress import ip_network
from hashlib import md5
from typing import Any
from ingenii_azure_data_platform.config import PlatformConfiguration


def generate_resource_name(
    resource_type: str, resource_name: str, platform_config: PlatformConfiguration
) -> str:
    """
    Generate a resource names based on consistent naming conventions.

    Parameters
    ----------
    resource_type: str
        The Azure resource type, e.g. 'resource_group', 'route_table'.

        Possible options are: resource_group, virtual_network, subnet, route_table,
        network_security_group, nat_gateway, public_ip, private_endpoint, service_principal,
        storage_blob_container,dns_zone, private_dns_zone, datafactory, databricks_workspace,
        databricks_cluster

    resource_name: str
        The name of the resource for which we are generating a consistent name.

    Returns
    -------
    str
        The generated resource name.
    """
    resource_names = {
        "resource_group": "rg",
        "virtual_network": "vnet",
        "subnet": "snet",
        "route_table": "rt",
        "network_security_group": "nsg",
        "nat_gateway": "ngw",
        "public_ip": "pip",
        "private_endpoint": "pe",
        "databricks_workspace": "dbw",
        "databricks_cluster": "dbwc",
        "service_principal": "sp",
        "storage_blob_container": "sbc",
        "dns_zone": "dz",
        "private_dns_zone": "prdz",
    }

    resource_type = resource_type.lower()
    prefix = platform_config.prefix
    stack = platform_config.stack
    region_short_name = platform_config.region.short_name
    unique_id = platform_config.unique_id
    use_legacy_naming = platform_config.use_legacy_naming

    # User Groups (Azure AD Groups)
    if resource_type == "user_group":
        # Example
        # ADP-Dev-Engineers
        return f"{prefix.upper()}-{stack.title()}-{resource_name.title()}"

    # Gateway Subnet
    elif resource_type == "gateway_subnet":
        return "Gateway"

    # Key Vault
    elif resource_type == "key_vault":
        # Example:
        # adp-tst-eus-kv-cred-ixk1
        return f"{prefix}-{stack}-{region_short_name}-kv-{resource_name}-{unique_id}"

    # Data Factory
    elif resource_type == "datafactory":
        if use_legacy_naming:
            return f"{prefix}-{stack}-{region_short_name}-adf-{resource_name.lower()}"

        return f"{prefix}-{stack}-{region_short_name}-adf-{resource_name}-{unique_id}"

    # Data Factory: Self Hosted Integration Runtime
    elif resource_type == "adf_integration_runtime":
        return f"{prefix}-{stack}-{resource_name}-{unique_id}"

    # Storage Account
    elif resource_type == "storage_account":
        return f"{prefix}{stack}{resource_name}{unique_id}"

    # Other Resources
    elif resource_type in resource_names:
        return f"{prefix}-{stack}-{region_short_name}-{resource_names[resource_type]}-{resource_name.lower()}"

    else:
        raise Exception(f"Resource type {resource_type} not recognised.")


def generate_hash(*args: str) -> str:
    """
    This function takes arbitrary number of string arguments, joins them together and returns and MD5 hash
    based on the joined string.

    Parameters
    ----------
    *args: str
        Arbitrary number of strings.

    Returns
    -------
    str
        An MD5 hash based on the provided strings.
    """
    concat = "".join(args).encode("utf-8")
    return md5(concat).hexdigest()


def generate_cidr(cidr_subnet: str, new_prefix: int, network_number: int) -> Any:
    """
    Calculates a new subnet number based on the inputs provided.
    # TODO
    """
    return list(ip_network(cidr_subnet).subnets(new_prefix=new_prefix))[
        network_number
    ].exploded


def get_os_root_path() -> str:
    """
    Returns the root path of the current operating system.
    Unix/MacOS = "/"
    Windows = "c:"
    # TODO
    """
    return os.path.abspath(os.sep)


def ensure_type(value, types):
    """
    This function checks if a value is of certain type.
    # TODO
    """
    if isinstance(value, types):
        return value
    else:
        raise TypeError(f"Value {value} is {type(value),}, but should be {types}!")