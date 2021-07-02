# YAML Configuration Schema <!-- omit in toc -->

- [Global](#global)
- [Platform](#platform)
  - [General](#general)
  - [Management](#management)
  - [Management: User Groups](#management-user-groups)
  - [Management: Resource Groups](#management-resource-groups)
  - [Network](#network)
- [Terraform Configuration](#terraform-configuration)

> Please make sure to read the [documentation][yaml_config_design_doc] on how the platform gets configured using various YAML files.

## Global

We support only two config keys at the root namespace of the YAML config file.

| Key         | Type                                               |
| ----------- | -------------------------------------------------- |
| `platform`  | [PlatformConfig](#platform-configuration) object   |
| `terraform` | [TerraformConfig](#terraform-configuration) object |

`example.yml`

```yml
platform: #...
terraform: #...
```

## Platform

| Key          | Type                                   |
| ------------ | -------------------------------------- |
| `general`    | [GeneralConfig](#general) object       |
| `management` | [ManagementConfig](#management) object |
| `network`    | [NetworkConfig](#network) object       |

`example.yml`

```yml
platform:
  general: #...
  management: #...
  network: #...
#...
```

### General

| Key                 | Type   |
| ------------------- | ------ |
| `region`            | string |
| `region_short_name` | string |
| `prefix`            | string |
| `tags`              | map    |

`example.yml`

```yml
platform:
  general:
    region: "EastUS"
    region_short_name: "eus"
    prefix: "adp"
    tags:
      ResourceManagedWith: "Terraform"
#...
```

**Namespace**: `platform`

**Key**: `general`

**Attributes**:

- `region` - (Required) [**string**] The name of the Azure region.
- `prefix` - (Required) [**string**] The resource prefix used for the deployment.
- `tags`- (Optional) [**map**] A map of key (name) and value tags that will be assigned to all resources in the deployment.

### Management

| Key               | Type                                                    | Providing Module  |
| ----------------- | ------------------------------------------------------- | ----------------- |
| `user_groups`     | [UserGroupsConfig](#management-user-groups) map         | `management-core` |
| `resource_groups` | [ResourceGroupsConfig](#management-resource-groups) map | `management-core` |

`example.yml`

```yml
platform:
  management:
    user_groups: #...
    resource_groups: #...
#...
```

### Management: User Groups

The user groups config objects represent Azure AD groups.

`example.yml`

```yml
platform:
  management:
    user_groups:
      engineers: # <- user_group_key_name
        display_name: "engineers"
      admins: # <- user_group_key_name
        display_name: "admins"
#...
```

**Namespace**: `platform.management`

**Key**: `user_groups`

**Attributes**:

- `display_name` - (Required) [**string**] The name of the User Group. The platform is following an opinionated naming convention. Please check our [naming conventions document][naming_conventions_doc].

**Referred By**:
This is merely a convention. There is no code in the current module that exposes this value. The convention is for other modules when they need to refer to instances of the current module.

- `user_group_key_name` - Other modules/components referring to User Groups should use `user_group_key_name` in their definitions.

### Management: Resource Groups

The user groups config objects represent Azure AD groups.

`example.yml`

```yml
platform:
  management:
    resource_groups:
      infra: # <- resource_group_key_name
        display_name: "infra"
        tags:
          Owner: "Infra Team"
        iam:
          role_assignments:
            - user_group_key_name: "engineers" # <- ref: management.user_groups.user_group_key_name
              role_definition_name: "Contributor" # The name of a built-in Azure Role.
#...
```

**Namespace**: `platform.management`

**Key**: `resource_groups`

**Attributes**:

- `display_name` - (Required) [**string**] The name of the Resource Group. The platform is following an opinionated naming convention. Please check our [naming conventions document][naming_conventions_doc].
- `iam` - (Optional) [**map**] Identity and access management
  - `role_assignments` - (Optional) [**list**] A list of role assignments
    - `user_group_key_name` - (Required) [**string**] The [**user group**](#management-user-groups) key name.
    - `role_definition_name` - (Optional) [**string**] The name of the built-in Azure Role. Conflicts with `role_definition_id`.
    - `role_definition_id` - (Optional) [**string**] The Scoped-ID of the role definition.
- `tags` - (Optional) [**map**] Map of key/value tags which are resource specific.

**Referred By**:
This is merely a convention. There is no code in the current module that exposes this value. The convention is for other modules when they need to refer to instances of the current module.

- `resource_group_key_name` - Other modules/components referring to Resource Groups should use `resource_group_key_name` in their definitions.

### Network

TODO

## Terraform Configuration

TODO

[//]: # "-------------------------"
[//]: # "INSERT LINK LABELS BELOW"
[//]: # "-------------------------"
[yaml_config_design_doc]: https://github.com/ingenii-solutions/azure-data-platform/blob/main/docs/yaml_config_design.md
[platform_design_doc]: https://github.com/ingenii-solutions/azure-data-platform/blob/main/docs/platform_design.md
[naming_conventions_doc]: https://github.com/ingenii-solutions/azure-data-platform/blob/main/docs/naming_conventions.md
