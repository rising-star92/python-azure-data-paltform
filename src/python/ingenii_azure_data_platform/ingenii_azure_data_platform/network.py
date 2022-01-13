from typing import Dict, List, Union

from pulumi import Output
from pulumi_azure_native.network import PrivateEndpoint, get_network_interface


def get_private_endpoint_ip_addr_and_fqdn(
    endpoint: PrivateEndpoint, resource_group_name: Union[str, Output[str]]
) -> List[Dict[str, str]]:
    # Get the private endpoint underlying NIC name
    nic_name = endpoint.network_interfaces[0].id.apply(lambda id: id.split("/")[-1])

    # Get NIC data
    nic = get_network_interface(
        network_interface_name=nic_name, resource_group_name=resource_group_name
    )

    # Grab the first (default) FQDN and map it to the NIC IP address
    return [
        {
            "ip_address": ip_config.private_ip_address,
            "fqdn": ip_config.private_link_connection_properties["fqdns"][0],
        }
        for ip_config in nic.ip_configurations
    ]
