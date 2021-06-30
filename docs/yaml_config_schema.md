# YAML Configuration Schema

- [YAML Configuration Schema](#yaml-configuration-schema)
  - [Global Keys](#global-keys)
  - [General Section](#general-section)
  - [Management Section](#management-section)
    - [User Groups](#user-groups)
    - [Resource Groups](#resource-groups)

## Global Keys

We use the keys below as logical sections where the specific component configurations reside.

| Key          | Type | Description                                         |
| ------------ | ---- | --------------------------------------------------- |
| `general`    | dict | General configs such as Region, Prefixes, Tags etc. |
| `management` | dict | Management resources and components.                |
| `network`    | dict | Network resources and components.                   |
| `storage`    | dict | Storage resources and components.                   |
| `data_tools` | dict | Data tools and services components.                 |
| `terraform`  | dict | Terraform specific configurations.                  |

```yml
# Example
general:
management:
network:
storage:
data_tools:
```

## General Section

| Key      | Type   | Rules and Recommendations         | Description |
| -------- | ------ | --------------------------------- | ----------- |
| `region` | string | `none`                            |             |
| `prefix` | string | `lowercase`, `4 characters limit` |             |
| `tags`   | dict   | `none`                            |             |

```yml
# Example
general:
  region: "UKWest"
  prefix: "adp01"
  tags:
    ResourceManagedWith: Terraform
```

## Management Section

| Key               | Type | Component         | Description |
| ----------------- | ---- | ----------------- | ----------- |
| `user_groups`     | dict | `management-core` |             |
| `resource_groups` | dict | `management-core` |             |

```yml
# Example
management:
  # User Groups
  user_groups:
    engineers:
      display_name: "engineers"
    analysts:
      display_name: "analysts"

  # Resource Groups
  resource_groups:
    infra:
      display_name: "infra"
      iam:
        role_assignments:
          - user_group_key_name: "engineers"
            role_definition_name: "Contributor"
```

### User Groups

The user groups represent Azure AD Groups.

```yml
# Example
management:
  # User Groups
  user_groups:
    engineers: # <- user_group_key_name
      display_name: "engineers"
    analysts: # <- user_group_key_name
      display_name: "analysts"
```

Namespace: `management`

Key: `user_groups`

Attributes:

- `display_name` - (Required) [**string**] The name of the User Group. End result: `<PREFIX>-<Env>-<DisplayName>`

### Resource Groups

The resource groups are standard Azure RM Resource Groups.

```yml
management:
  # Resource Groups
  resource_groups:
    infra: # <- resource_group_key_name
      display_name: "infra"
      tags:
        Owner: "Infra Team"
      iam:
        role_assignments:
          - user_group_key_name: "engineers" # <- ref: user_groups.user_group_key_name
            role_definition_name: "Contributor" # The name of a built-in Azure Role.
```

Namespace: `management`

Key: `resource_groups`

Attributes:

- `display_name` - (Required) [**string**] The name of the Resource Group. End result: `<prefix>-<env>-<display_name>`
- `iam` - (Optional) [**dict**] Identity and access management
  - `role_assignments` - (Optional) [**list**] A list of role assignments
    - `user_group_key_name` - (Required) [**string**] The [**user group**](#user-groups) key name.
    - `role_definition_name` - (Optional) [**string**] The name of the built-in Azure Role. Conflicts with `role_definition_id`.
    - `role_definition_id` - (Optional) [**string**] The Scoped-ID of the role definition.
- `tags` - (Optional) [**dict**] Map of key/value tags which are resource specific.

<!-- ## Network Section

| Key                       | Type | Component                        | Description |
| ------------------------- | ---- | -------------------------------- | ----------- |
| `firewall`                | dict | [Network Firewall]()             |             |
| `virtual_networks`        | dict | [Azure Virtual Network]()        |             |
| `network_security_groups` | dict | [Azure Network Security Group]() |             |

```yml
# Example
network:
  # Firewall
  firewall:
    ip_access_list:
      - "1.1.1.1"
    subnet_access_list:

  # Virtual Networks
  virtual_networks:
    main: # <- virtual_network_key_name
      display_name: "main"
      resource_group_key_name: "infra"
      address_space: "10.50.0.0/16"
      route_tables:
        private: # <- route_table_key_name
          display_name: "private"
      subnets:
        data_processing_private: # <- subnet_key_name
          display_name: "data-processing-private"
          address_prefix: "10.50.16.0/20"
          route_table_key_name: "private"
          network_security_group_key_name: "databricks"
          service_endpoints:
            - "Microsoft.Storage"
            - "Microsoft.KeyVault"
          delegations:
            - "databricks"
        data_analytics_private:
          display_name: "data-analytics-private"
          address_prefix: "10.50.48.0/20"
          route_table_key_name: "private"
          network_security_group_key_name: "databricks"
          service_endpoints:
            - "Microsoft.Storage"
          delegations:
            - "databricks"
      subnet_delegations:
        databricks:
          name: "Databricks"
          service_delegation:
            name: "Microsoft.Databricks/workspaces"
            actions:
              - "Microsoft.Network/virtualNetworks/subnets/join/action"

  # Network Security Groups
  network_security_groups:
    databricks: # <- network_security_group_key_name
      display_name: "databricks"
      resource_group_key_name: "infra"
```

## Storage Section

| Key          | Type | Component                        | Description |
| ------------ | ---- | -------------------------------- | ----------- |
| `data_lakes` | dict | [Azure Storage Gen2 Data Lake]() |             |

```yml
# Example
storage:
  data_lakes:
    main: # <- data_lake_key_name
      display_name: "datalake"
      resource_group_key_name: "data"
      iam:
        role_definitions:
          read_write: "Storage Blob Data Contributor"
          read_only: "Storage Blob Data Reader"
      network:
        firewall:
          default_action: "Deny"
          bypass_services:
            - "AzureServices"
            - "Logging"
          subnet_access_list:
            - "platform:data_processing_public" # <- Ref: "virtual_network_key_name : subnet_key_name"
      storage_containers:
        raw:
          display_name: "raw"
          iam:
            role_assignments:
              read_write:
                - "engineers" # <- Ref: user_group_key_name
        orchestration:
          display_name: "orchestration"
          iam:
            role_assignments:
              read_write:
                - "engineers" # <- Ref: user_group_key_name
              read_only:
                - "analysts" # <- Ref: user_group_key_name
        utilities:
          display_name: "utilities"
          iam:
            role_assignments:
              read_only:
                - "analysts" # <- Ref: user_group_key_name
                - "engineers" # <- Ref: user_group_key_name
        data-structure:
          display_name: "data-structure"
          iam:
            role_assignments:
              read_only:
                - "analysts" # <- Ref: user_group_key_name
                - "engineers" # <- Ref: user_group_key_name
      #...
```

## Data Tools Section

| Key                          | Type | Component                      | Description |
| ---------------------------- | ---- | ------------------------------ | ----------- |
| `azure_data_factories`       | dict | [Azure Data Factory]()         |             |
| `azure_dataricks_workspaces` | dict | [Azure Databricks Workspace]() |             |

```yml
# Example
data_tools:
  azure_data_factories:
    data_orchestration: # azure_data_factory_key_name
      resource_group_key_name: "infra"
      #...
  azure_databricks_worckspaces:
    data_analytics: # <- azure_databricks_workspace_key_name
      resource_group_key_name: "infra"
      #...
    data_processing:
      resource_group_key_name: "infra"
      #...
```

## Terraform Section

| Key                    | Type | Component | Description |
| ---------------------- | ---- | --------- | ----------- |
| `remote_state_backend` | dict |           |             |

```yml
# Example
terraform:
  remote_state_backend:
    type: "azurerm"
    azurerm:
      resource_group_name: "ingneii"
      storage_account_name: "ingenii"
      container_name: "terraform-state"
``` -->
