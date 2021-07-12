# YAML Configuration Schema <!-- omit in toc -->

- [**Global**](#global)
- [**Platform**](#platform)
- [**General**](#general)
- [**General: Region**](#general-region)
- [**Management**](#management)
- [**Management: User Groups**](#management-user-groups)
- [**Management: Resource Groups**](#management-resource-groups)
- [**Network**](#network)
- [**Network: Virtual Network**](#network-virtual-network)
- [**Network: Route Tables**](#network-route-tables)
- [**Network: Network Security Groups**](#network-network-security-groups)
- [**Network: NAT Gateway**](#network-nat-gateway)
- [**Terraform Configuration**](#terraform-configuration)

> Please make sure to read the [**documentation**][yaml_config_design_doc] on how the platform gets configured using various YAML files.

---

## **Global**

We support only two config attributes at the root scope of the YAML config file.

### **Examples** <!-- omit in toc -->

```yml
platform: #...
terraform: #...
```

### **Attributes** <!-- omit in toc -->

- `platform` - [**PlatformConfig Object**](#platform-configuration)
- `terraform` - [**TerraformConfig Object**](#terraform-configuration)

## **Platform**

### **Examples** <!-- omit in toc -->

```yml
platform:
  general: #...
  management: #...
  network: #...
#...
```

### **Scope** <!-- omit in toc -->

`platform`

### **Attributes** <!-- omit in toc -->

- `general` - [**GeneralConfig Object**](#general)
- `management` - [**ManagementConfig Object**](#management)
- `network` - [**NetworkConfig Object**](#network)

---

## **General**

### **Examples** <!-- omit in toc -->

```yml
platform:
  general:
    region: #...
    prefix: "adp"
    tags:
      ResourceManagedWith: "Terraform"
#...
```

### **Scope** <!-- omit in toc -->

`platform.general`

### **Attributes** <!-- omit in toc -->

- `region` - (_Required_) [**RegionConfig Object**](#general-region)
- `prefix` - (_Required_) **string** - The resource prefix used for the deployment.
- `tags` - (_Optional_) **map[string:string]** - Key value pairs of tags to be assigned to all resources.

---

## **General: Region**

### **Examples** <!-- omit in toc -->

```yml
platform:
  general:
    region:
      long_name: "EastUS"
      short_name: "eus"
#...
```

### **Scope** <!-- omit in toc -->

`platform.general.region`

### **Attributes** <!-- omit in toc -->

- `long_name` - (_Required_) **string** - The full name of the Azure region. e.g. EastUS, UKSouth, UKWest
- `short_name` - (_Required_) **string** - The short name of the Azure region. e.g. eus, uks, ukw

---

## **Management**

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    user_groups: #...
    resource_groups: #...
#...
```

### **Scope** <!-- omit in toc -->

`platform.management`

### **Attributes** <!-- omit in toc -->

- `user_groups` - [**UserGroupsConfig Object**](#management-user-groups) - Providing Module: `management-core`
- `resource_groups` - [**ResourceGroupsConfig Object**](#management-resource-groups) - Providing Module: `management-core`

---

## **Management: User Groups**

The user groups config maps represent Azure AD groups.

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    user_groups:
      engineers: # <- user_group_ref_key
        display_name: "engineers"
      admins: # <- user_group_ref_key
        display_name: "admins"
#...
```

### **Scope** <!-- omit in toc -->

`platform.management.user_groups`

### **Attributes** <!-- omit in toc -->

- `display_name` - (_Required_) **string** - The name of the User Group. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].

### **Reference Key** <!-- omit in toc -->

`user_group_ref_key`

---

## **Management: Resource Groups**

The user groups config maps represent Azure AD groups.

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    resource_groups:
      infra: # <- resource_group_ref_key
        display_name: "infra"
        tags:
          Owner: "Infra Team"
        iam:
          role_assignments:
            - user_group_ref_key: "engineers" # <- ref: management.user_groups.user_group_ref_key
              role_definition_name: "Contributor" # The name of a built-in Azure Role.
#...
```

### **Scope** <!-- omit in toc -->

`platform.management.resource_groups`

### **Attributes** <!-- omit in toc -->

- `display_name` - (_Required_) **string** - The name of the Resource Group. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].
- `iam` - (_Optional_) **object** - Identity and access management object (below).
- `tags` - (_Optional_) **map[string:string]** - Map of key/value tags which are resource specific.

---

The `iam` object has the following attributes:

- `role_assignments` - (_Optional_) **list[object]** - A list of `role_assignment` objects (below).

---

The `role_assignment` object has the following attributes:

- `user_group_ref_key` - (_Required_) **string** - The [**user group**](#management-user-groups) reference key name.
- `role_definition_name` - (_Optional_) **string** - The name of the built-in Azure Role. Conflicts with `role_definition_id`.
- `role_definition_id` - (_Optional_) **string** - The Scoped-ID of the role definition.

### **Reference Key** <!-- omit in toc -->

`resource_group_ref_key`

---

## **Network**

### **Examples** <!-- omit in toc -->

```yml
platform:
  network:
    virtual_network: #...
    route_tables: #...
    network_security_groups: #...
    nat_gateway: #...
    public_ip_addresses: #...
#...
```

### **Scope** <!-- omit in toc -->

`platform.network`

### **Attributes** <!-- omit in toc -->

- `virtual_network` - [**VirtualNetworkConfig Object**](#network-virtual-network) - Providing Module: `network-core`
- `route_tables` - [**RouteTablesConfig Object**](#network-route-tables) - Providing Module: `network-core`
- `network_security_groups` - [**NetworkSecurityGroupsConfig Object**](#network-network-security-groups) - Providing Module: `network-core`
- `nat_gateway` - [**NatGatewayConfig Object**](#network-nat-gateway)
- `public_ip_addresses` - [**PublicIpAddressesConfig Object**](#network-public-ip-addresses)

---

## **Network: Virtual Network**

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    resource_groups:
      infra: # <- resource_group_ref_key
    user_groups:
      engineers: # <- user_group_ref_key
        display_name: "engineers"
  network:
    nat_gateway:
      enabled: true
      display_name: main
      resource_group_ref_key: infra
    route_tables:
      private: # <- route_table_ref_key
        display_name: "private"
        resource_group_ref_key: "infra"
    network_security_groups:
      databricks: # <- network_security_group_ref_key
        display_name: "databricks"
        resource_group_ref_key: "infra"
   virtual_network:
      display_name: main
      resource_group_ref_key: infra
      address_space: 10.110.0.0/16
      subnet_network_size: 6
      subnets:
        databricks_private:
          display_name: dbw-private
          network_number: 0
          route_table_ref_key: private
          network_security_group_ref_key: databricks
          is_associated_to_nat_gateway: true
          service_endpoints:
            - Microsoft.Storage
            - Microsoft.KeyVault
          delegations:
            databricks:
              display_name: "databricks"
              service_delegation:
                name: "Microsoft.Databricks/workspaces"
                actions:
                  - "Microsoft.Network/virtualNetworks/subnets/join/action"
                  - "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action"
                  - "Microsoft.Network/virtualNetworks/subnets/unprepareNetworkPolicies/action"
#...
```

### **Scope** <!-- omit in toc -->

`platform.network.virtual_network`

### **Attributes** <!-- omit in toc -->

- `display_name` (_Required_) **string** - The name of the Virtual Network. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].
- `iam` (_Optional_) **object** - The identity and access management object. As described below.
- `resource_group_ref_key` (_Required_) **string** - The [**resource group**](#management-resource-groups) reference key name.
- `address_space` (_Required_) **string** - The virtual network network range. e.g. 10.10.0.0/16
- `subnet_network_size` - (_Optional_) **[number]** - A number of additional bits added to the _address_space_ when generating the subnet prefixes. e.g. _address_space_ = 10.10.0.0/16, _subnet_network_size_ = 6, the first subnet prefix to be generated will be _10.10.0.0/22_, next _10.10.4.0/22_, and so on. Defaults to: `6`
- `dns_servers` (_Optional_) **list[string]** - A list of IP addresses of DNS servers.
- `bgp_community` (_Optional_) **string** - BGP community attribute in the following format: `<as-number>:<community-value>`
- `subnets` (_Optional_) **map[string:object]** - A map of `subnet_ref_key`:`subnet_object` (below) elements.
- `tags` (_Optional_) **map[string:string]** - Map of key/value tags which are resource specific.

---

The `iam` object has the following attributes:

- `role_assignments` - (_Optional_) **list[object]** - A list of `role_assignment` objects (below).

---

The `role_assignment` object has the following attributes:

- `user_group_ref_key` - (_Required_) **string** - The [**user group**](#management-user-groups) reference key name.
- `role_definition_name` - (_Optional_) **string** - The name of the built-in Azure Role. Conflicts with `role_definition_id`.
- `role_definition_id` - (_Optional_) **string** - The Scoped-ID of the role definition.

---

The `subnet` object has the following attributes:

- `display_name` (_Required_) **string** - The name of the Subnet. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].
- `network_number` (_Required_) **number** - The network number of the subnet. It is based on the VNET _address_space_, VNET _subnet_network_size_ plus the SUBNET _network_number_. e.g. _address_space_ = 10.10.0.0/16, _subnet_network_size_ = 6, _network_number_ = 0 will result in subnet prefix of _10.10.0.0/22_; _network_number_ = 1 will result in subnet prefix of _10.10.4.0/22_
- `network_security_group_ref_key` (_Optional_) **string** - The ref key of the NSG we want attached to this subnet.
- `route_table_ref_key` (_Optional_) **string** - The ref key of the Route Table we want to attach this subnet.
- `is_associated_to_nat_gateway` (_Optional_) **bool** - It only works if the NAT gateway is enabled. Defaults to `true`.
- `delegations` (_Optional_) **map[string:object]** - A map of `delegation_ref_key`:`delegation_object` (below) elements.
- `enforce_private_link_endpoint_network_policies` (_Optional_) **bool** - Enable or Disable network policies for the private link endpoint on the subnet. Default value is `false`. Conflicts with `enforce_private_link_service_network_policies`.
- `enforce_private_link_service_network_policies` (_Optional_) **bool** - Enable or Disable network policies for the private link service on the subnet. Default value is `false`. Conflicts with `enforce_private_link_endpoint_network_policies`.
- `service_endpoints` (_Optional_) **list[string]** - The list of Service endpoints to associate with the subnet.
- `service_endpoint_policy_ids` (_Optional_) **list[string]** - The list of IDs of Service Endpoint Policies to associate with the subnet.

---

The `delegation` object has the following attributes:

- `display_name` (_Required_) **string** - The name of the delegation.
- `service_delegation` (_Required_) **object** - As described below.

---

The `service_delegation` object has the following attributes:

- `name` (_Required_) **string** - The name of service to delegate to.
- `actions` (_Optional_) **list[string]** - A list of Actions which should be delegated. This list is specific to the service to delegate to.

### **Reference Key** <!-- omit in toc -->

`n/a`

## **Network: Route Tables**

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    resource_groups:
      infra: # <- resource_group_ref_key
  user_groups:
    engineers: # <- user_group_ref_key
      display_name: "engineers"
  network:
    route_tables:
      private: # <- route_table_ref_key
        display_name: "private"
        iam:
          role_assignments:
            - user_group_ref_key: "engineers"
              role_definition_name: "Contributor" # <- The name of a built-in Azure Role.
        resource_group_ref_key: "infra"
        routes:
          dns_via_internet: # <- route_ref_key
            display_name: "dns-via-internet"
            address_prefix: "1.1.1.1/32"
            next_hop_type: "internet"
        tags:
          ManagedBy: "Network Team"
#...
```

### **Scope** <!-- omit in toc -->

`platform.network.route_tables`

### **Attributes** <!-- omit in toc -->

- `display_name` (_Required_) **string** - The name of the Route Table. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].
- `iam` (_Optional_) **object** - The identity and access management object. As described below.
- `resource_group_ref_key` (_Required_) **string** - The [**resource group**](#management-resource-groups) reference key name.
- `disable_bgp_route_propagation` (_Optional_) **bool** - Enable or Disable BGP route propagation. Defaults to `false`.
- `routes` (_Optional_) **map[string:object]** - A map of `route_ref_key`:`route_object` (below) elements.
- `tags` (_Optional_) **map[string:string]** - Map of key/value tags which are resource specific.

---

The `iam` object has the following attributes:

- `role_assignments` - (_Optional_) **list[object]** - A list of `role_assignment` objects (below).

---

The `role_assignment` object has the following attributes:

- `user_group_ref_key` - (_Required_) **string** - The [**user group**](#management-user-groups) reference key name.
- `role_definition_name` - (_Optional_) **string** - The name of the built-in Azure Role. Conflicts with `role_definition_id`.
- `role_definition_id` - (_Optional_) **string** - The Scoped-ID of the role definition.

---

The `route` object has the following attributes:

- `display_name` (_Required_) **string** - The name of the route.
- `address_prefix` (_Required_) **string** - The address prefix. (e.g. 1.1.1.1/32)
- `next_hop_type` (_Required_) **string** - The type of Azure hop the packet should be sent to. Possible values are `VirtualNetworkGateway`, `VnetLocal`, `Internet`, `VirtualAppliance` and `None`
- `next_hop_in_ip_address` (_Optional_) **string** - Contains the IP address packets should be forwarded to. Next hop values are only allowed in routes where the next hop type is `VirtualAppliance`.

### **Reference Key** <!-- omit in toc -->

`route_table_ref_key`

## **Network: Network Security Groups**

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    resource_groups:
      infra: # <- resource_group_ref_key
  user_groups:
    engineers: # <- user_group_ref_key
      display_name: "engineers"
  network:
    network_security_groups:
      inbound_filter: # <- network_security_group_ref_key
        display_name: "inbound-filter"
        iam:
          role_assignments:
            - user_group_ref_key: "engineers"
              role_definition_name: "Contributor" # The name of a built-in Azure Role.
        resource_group_ref_key: "infra"
        rules:
          allow_rdp_from_office: # <- network_security_rule_ref_key
            display_name: "AllowRDPFromOffice"
            description: "Allowing RDP connections from the office location."
            priority: 100
            direction: Inbound
            access: Allow
            protocol: Tcp
            source_port_range: "*"
            destination_port_range: "3389"
            source_address_prefix: "72.72.73.73/32"
            destination_address_prefix: "*"
#...
```

### **Scope** <!-- omit in toc -->

`platform.network.network_security_groups`

### **Attributes** <!-- omit in toc -->

- `display_name` (_Required_) **string** - The name of the Network Security Group. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].
- `iam` (_Optional_) **object** - The identity and access management object. As described below.
- `resource_group_ref_key` (_Required_) **string** - The [**resource group**](#management-resource-groups) reference key name.
- `rules` (_Optional_) **map[string:object]** - A map of `rule_ref_key`:`rule_object` (below) elements.
- `tags` (_Optional_) **map[string:string]** - Map of key/value tags which are resource specific.

---

The `iam` object has the following attributes:

- `role_assignments` - (_Optional_) **list[object]** - A list of `role_assignment` objects (below).

---

The `role_assignment` object has the following attributes:

- `user_group_ref_key` - (_Required_) **string** - The [**user group**](#management-user-groups) reference key name.
- `role_definition_name` - (_Optional_) **string** - The name of the built-in Azure Role. Conflicts with `role_definition_id`.
- `role_definition_id` - (_Optional_) **string** - The Scoped-ID of the role definition.

---

The `rule` object has the following attributes:

- `display_name` (_Required_) **string** - The name of the rule. It must be unique across rules.
- `description` (_Optional_) **string** - A description for the rule. Restricted to 140 characters.
- `priority` (_Required_) **number** - Specifies the priority of the rule. The value can be between `100` and `4096`. The priority number must be unique for each rule in the collection. The lower the priority number, the higher the priority of the rule.
- `direction` - (_Required_) **string** - The direction specifies if rule will be evaluated on incoming or outgoing traffic. Possible values are `Inbound` and `Outbound`
- `access` (_Required_) **string** - Specifies whether network traffic is allowed or denied. Possible values are `Allow` and `Deny`.
- `protocol` (_Required_) **string** - Network protocol this rule applies to. Possible values include `Tcp`, `Udp`, `Icmp`, `Esp`, `Ah` or `*` (which matches all).
- `source_port_range` (_Optional_) **string** - Source Port or Range. Integer or range between `0` and `65535` or `*` to match any. This is required if `source_port_ranges` is not specified.
- `source_port_ranges` (_Optional_) **list[string]** - List of source ports or port ranges. This is required if `source_port_range` is not specified.
- `source_address_prefix` (_Optional_) **string** - CIDR or source IP range or `*` to match any IP. Tags such as ‘VirtualNetwork’, ‘AzureLoadBalancer’ and ‘Internet’ can also be used. This is required if `source_address_prefixes` is not specified.
- `source_address_prefixes` (_Optional_) **list[string]** - List of source address prefixes. Tags may not be used. This is required if `source_address_prefix` is not specified.
- `destination_port_range` (_Optional_) **string** - Destination Port or Range. Integer or range between `0` and `65535` or `*` to match any. This is required if `destination_port_ranges` is not specified.
- `destination_port_ranges` (_Optional_) **list[string]** - List of destination ports or port ranges. This is required if `destination_port_range` is not specified.
- `destination_address_prefix` (_Optional_) **string** - CIDR or destination IP range or `*` to match any IP. Tags such as ‘VirtualNetwork’, ‘AzureLoadBalancer’ and ‘Internet’ can also be used. Besides, it also supports all available Service Tags like ‘Sql.WestEurope‘, ‘Storage.EastUS‘, etc. You can list the available service tags with the cli: `az network list-service-tags --location westcentralus`.
- `destination_address_prefixes` (_Optional_) **list[string]** - List of destination address prefixes. Tags may not be used. This is required if `destination_address_prefix` is not specified.

### **Reference Key** <!-- omit in toc -->

`network_security_group_ref_key`

## **Network: NAT Gateway**

### **Examples** <!-- omit in toc -->

```yml
platform:
  management:
    resource_groups:
      infra: # <- resource_group_ref_key
  user_groups:
    engineers: # <- user_group_ref_key
      display_name: "engineers"
  network:
    nat_gateway:
      enabled: true
      display_name: "main"
      resource_group_ref_key: "infra"
#...
```

### **Scope** <!-- omit in toc -->

`platform.network.nat_gateway`

### **Attributes** <!-- omit in toc -->

- `enabled` - (_Required_) **bool** - Enable or disable the NAT gateway. Defaults to `true`.
- `display_name` (_Required_) **string** - The name of the NAT gateway. The platform is following an opinionated naming convention. Please check our [**naming conventions document**][naming_conventions_doc].
- `resource_group_ref_key` (_Required_) **string** - The [**resource group**](#management-resource-groups) reference key name.
- `tags` (_Optional_) **map[string:string]** - Map of key/value tags which are resource specific.

### **Reference Key** <!-- omit in toc -->

`n/a`

## **Terraform Configuration**

TODO

[//]: # "-------------------------"
[//]: # "INSERT LINK LABELS BELOW"
[//]: # "-------------------------"
[yaml_config_design_doc]: https://github.com/ingenii-solutions/azure-data-platform/blob/main/docs/yaml_config_design.md
[platform_design_doc]: https://github.com/ingenii-solutions/azure-data-platform/blob/main/docs/platform_design.md
[naming_conventions_doc]: https://github.com/ingenii-solutions/azure-data-platform/blob/main/docs/naming_conventions.md
