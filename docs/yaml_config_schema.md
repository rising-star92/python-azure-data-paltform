# YAML Configuration Schema

- [YAML Configuration Schema](#yaml-configuration-schema)
  - [Global Keys](#global-keys)
  - [General Section](#general-section)
  - [Management Section](#management-section)
  - [Network Section](#network-section)
  - [Storage Section](#storage-section)
  - [Data Tools Section](#data-tools-section)

## Global Keys

We use the keys below as logical sections where the specific component configurations reside.

| Key          | Type | Description                                         |
| ------------ | ---- | --------------------------------------------------- |
| `general`    | dict | General configs such as Region, Prefixes, Tags etc. |
| `management` | dict | Management resources and components.                |
| `network`    | dict | Network resources and components.                   |
| `storage`    | dict | Storage resources and components.                   |
| `data_tools` | dict | Data tools and services components.                 |

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
    platform: # <- resource_group_key_name
      display_name: "platform"
```

## Network Section

| Key                | Type | Component                 | Description |
| ------------------ | ---- | ------------------------- | ----------- |
| `virtual_networks` | dict | [Azure Virtual Network]() |             |

```yml
# Example
network:
  virtual_networks:
    platform: # <- virtual_network_key_name
      resource_group_key_name: "platform"
      address_space: "10.10.0.0/16"
      #...
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
      resource_group_key_name: "platform"
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
      resource_group_key_name: "platform"
      #...
  azure_databricks_worckspaces:
    data_analytics: # <- azure_databricks_workspace_key_name
      resource_group_key_name: "platform"
      #...
    data_processing:
      resource_group_key_name: "platform"
      #...
```
