from typing import Dict, List, Union

from pulumi import Output
from pulumi_azure_native.network import PrivateEndpoint, get_network_interface


class PlatformFirewall:
    def __init__(
        self,
        enabled: bool = False,
        ip_access_list: List[str] = [],
        vnet_access_list: List[str] = [],
        resource_access_list: List[Dict[str, str]] = [],
        default_action: str = "Deny",
        trust_azure_services: bool = False,
    ):
        self._enabled = enabled
        self._ip_access_list = sorted(list(set(ip_access_list)))
        self._vnet_access_list = sorted(list(set(vnet_access_list)))
        self._resource_access_list = sorted(resource_access_list)
        self._default_action = default_action
        self._trust_azure_services = trust_azure_services

    def __str__(self):
        return str(
            {
                "enabled": self._enabled,
                "ip_access_list": self._ip_access_list,
                "vnet_access_list": self._vnet_access_list,
                "resource_access_list": self._resource_access_list,
                "default_action": self._default_action,
                "trust_azure_services": self._trust_azure_services,
            }
        )

    def __add__(self, other):
        if self._enabled:
            ip_access_list = list(set(self._ip_access_list + other._ip_access_list))
            vnet_access_list = list(
                set(self._vnet_access_list + other._vnet_access_list)
            )
            resource_access_list = list(
                set(self._resource_access_list + other._resource_access_list)
            )

        else:
            ip_access_list = other._ip_access_list
            vnet_access_list = other._vnet_access_list
            resource_access_list = other._resource_access_list

        return PlatformFirewall(
            enabled=other._enabled,
            ip_access_list=ip_access_list,
            vnet_access_list=vnet_access_list,
            resource_access_list=resource_access_list,
            default_action=other._default_action,
            trust_azure_services=other._trust_azure_services,
        )

    @property
    def enabled(self):
        return self._enabled

    @property
    def ip_access_list(self) -> List[str]:
        return self._ip_access_list

    @property
    def vnet_access_list(self) -> List[str]:
        return self._vnet_access_list

    @property
    def resource_access_list(self) -> List[Dict[str, str]]:
        return self._resource_access_list

    @property
    def default_action(self) -> str:
        return self._default_action

    @property
    def bypass_services(self) -> Union[str, None]:
        if self._trust_azure_services:
            return "AzureServices"
        return None


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
