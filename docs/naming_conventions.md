# Ingenii Azure Data Platform: Naming Conventions

For illustration purposes, we'll assume the following values are set for:

- prefix = "adp"
- env = "dev"

| Resource Type        | Naming Convention                      | Examples                              |
| -------------------- | -------------------------------------- | ------------------------------------- |
| Azure AD Group       | `<PREFIX>-<Env>-<GroupName>`           | ADP-Dev-Engineers <br> ADP-Dev-Admins |
| Azure Resource Group | `<prefix>-<env>-<resource_group_name>` | adp-dev-infra <br> adp-dev-data       |
| A3                   | B3                                     | C3                                    |
