# Ingenii Azure Data Platform

## Getting Started

### Initialize The Platform Repository

```shell
# Set your GitHub personal access token
export GITHUB_TOKNEN=""

# Set the platform version to initialize
export PLATFORM_VERSION=""

# Create a directory for your repo
mkdir ingenii-azure-data-platform && cd ingenii-azure-data-platform

wget --header="Authorization: token ${GITHUB_TOKEN}" -O - https://raw.githubusercontent.com/ingenii-solutions/azure-data-platform/main/src/utils/scripts/init-platform.sh | bash
```
