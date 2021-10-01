# CHANGELOG

## 0.1.17 (2021-10-02)

### Bug Fixes

- [general] - Bugfixes around the make file and the first package to deploy.

## 0.1.16 (2021-10-02)

### Improvements

- [general] - Migrating the defaults into a centralized location.

## 0.1.15 (2021-10-02)

### Improvements

- [github-workflows] - Adding a check to make sure the Changelog has been updated.
- [general] - Exporting outputs from the platform
- [packages] - Getting a very rough packaging system in place.
- [packages] - Preview of ADP SQL Results Server package.
- [cookiecutters] - Updating the cookiecutter templates.

### Bug Fixes

- [datalake] - Update Table storage permissions
- [datafactory] - Fix ingestion pipeline parameters

## 0.1.14 (2021-09-22)

### Improvements

- [datalake] - Update the name of the Table storage SAS token when stored in Azure Key Vault.
- [datalake] - Append the Data Lake Table storage endpoint to the SAS token when stored in the Azure Key Vault.

## 0.1.13 (2021-09-22)

### New Features

- [datafactory] - Create self-hosted integration runtimes using the YAML config.

## 0.1.12 (2021-09-16)

### Improvements

- [general] - Update to Pulumi version 3.12.0
- [datafactory] - Adding 'Data Factory Contributor' access for the 'Engineers' group.

### Bug Fixes

- [general] - Creating a relationship for Storage Tables and Entities. Without the relationship deployments had to be retried multiple times as entities were to be created before tha storage table to exist.

## 0.1.11 (2021-09-14)

### Improvements

- [general] - Improving naming conventions.
- [general] - Add the ability to register Azure Resource Providers.
- [data engineering] - Add table storage to keep track of sftp file ingestion.

### Bug Fixes

- [general] - Improving naming convetions.
- [general] - Add the ability to register Azure Resource Providers.
- [data engineering] - Add table storage to keep track of sftp file ingestion.

### Bug Fixes

- [general] - Fix Databricks linked services for Data Factory.

## 0.1.6

### Improvements

- [databricks] - Making sure all storage mounts are done using the default clusters for Engineering and Analytics workspaces.

## 0.1.5

### Improvements

- [databricks] - Mounting the 'utilities' container in the Analytics workspace.
- [development] - Improving the .devcontainer experience

## 0.1.4

### Improvements

- [databricks] - Provide additional environment variables to the Engineering and Analytics cluster.
- [databricks] - Add default cluster docker image for the Engineering cluster.
- [databricks] - Make sure the "users" group has "CAN_ATTACH_TO" access to the Databricks clusters.

## 0.1.3

### Improvements

- [databricks] - Add the DBT token to the Databricks 'main' secret scope.
