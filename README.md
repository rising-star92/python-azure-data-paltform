# Ingenii Azure Data Platform

## Getting Started

### Initialize The Platform Repo1sitory

```shell
# Set your GitHub personal access token
export GITHUB_TOKEN=""

# Set the platform version to initialize
export PLATFORM_VERSION=""

# Run Init Script
sh -c "$(wget --header="Authorization: token ${GITHUB_TOKEN}" -O - \
https://raw.githubusercontent.com/ingenii-solutions/azure-data-platform/main/src/utils/scripts/init-platform.sh)"
```

### Update The Platform Version

```shell
# Set your GitHub personal access token
export GITHUB_TOKEN=""

# Set the platform version to initialize
export PLATFORM_VERSION=""

# Run Update Script
sh -c "$(wget --header="Authorization: token ${GITHUB_TOKEN}" -O - \
https://raw.githubusercontent.com/ingenii-solutions/azure-data-platform/main/src/utils/scripts/update-platform.sh)"
```

## Configuration Schema

Our config schema can be found here:
[YAML Configuration Schema](./docs/yaml_config_schema.md)
