# YAML Configuration Schema

- [YAML Configuration Schema](#yaml-configuration-schema)
  - [Global Keys](#global-keys)
  - [General Section](#general-section)
  - [Management Section](#management-section)
  - [Network Section](#network-section)
  - [Storage Section](#storage-section)
  - [Data Tools Section](#data-tools-section)
  - [Terraform Section](#terraform-section)

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

| Key               | Type   | Rules and Recommendations     | Description |
| ----------------- | ------ | ----------------------------- | ----------- |
| `region`          | string | `none`                        |             |
| `resource_prefix` | string | lowercase, 4 characters limit |             |
| `tags`            | dict   | `none`                        |             |

```yml
# Example
general:
  region: "UKWest"
  resource_prefix: "adp01"
  tags:
    key: value
```

## Management Section

| Key               | Type | Component                | Description |
| ----------------- | ---- | ------------------------ | ----------- |
| `user_groups`     | dict | [AzureAD Group]()        |
| `resource_groups` | dict | [Azure Resource Group]() |

```yml
# Example
management:
  # User Groups
  user_groups:
    engineers: # <- user_group_key_name
      display_name: "engineers"
    analysts:
      display_name: "analysts"
  # Resource Groups
  resource_groups:
    infra: # <- resource_group_key_name
      display_name: "infra"
```

## Network Section

| Key                       | Type | Component                        | Description |
| ------------------------- | ---- | -------------------------------- | ----------- |
| `virtual_networks`        | dict | [Azure Virtual Network]()        |             |
| `network_security_groups` | dict | [Azure Network Security Group]() |             |

```yml
# Example
network:
  # Virtual Networks
  virtual_networks:
    main: # <- virtual_network_key_name
      display_name: "main"
      resource_group_key_name: "infra"
      address_space: "10.50.0.0/16"
      route_tables:
        private:
          display_name: "private"
      subnets:
        data_processing_private:
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
    platform: # <- data_lake_key_name
      resource_group_key_name: "infra"
      display_name: "platform"
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
```
