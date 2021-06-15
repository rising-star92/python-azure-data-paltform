#!/usr/bin/env bash
# This script is used to initialize the Azure Data Platform repository on the client's side.

# Exit immediately if a command exits with a non-zero status.
set -e

readonly PLATFORM_REPO_URL="https://github.com/ingenii-solutions/azure-data-platform"

# These are the files and directories that will be included in the client repo
# Other directories and files not matched will be discarded.
readonly INCLUDED_ASSETS="*/src */configs */docs */README.md */.gitignore"

function log {
    local readonly type="$1"
    local readonly message="$2"
    local readonly timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    >&2 echo -e "${timestamp} [${type}] ${message}"
}

function check_env_variables {
    log "INFO" "Checking if environment variables are set..."

    # Check if GITHUB_TOKEN environment variable is set
    if [ -z "$GITHUB_TOKEN" ]; then
        echo
        echo "Please enter your GITHUB_TOKEN:"
        read -s GITHUB_TOKEN
    fi
    
    # Check if the PLATFORM_VERSION environment variable is set up:
    if [ -z "$PLATFORM_VERSION" ]; then
        echo
        echo "Please enter the platform version to initialize:"
        read PLATFORM_VERSION
    fi
}

function download_platform_source {
    local readonly header="Authorization: token ${GITHUB_TOKEN}"
    local readonly url="${PLATFORM_REPO_URL}/archive/refs/tags/${PLATFORM_VERSION}.tar.gz"

    log "INFO" "Downloading the platform source..."    
    wget --header="$header" -O - $url | \
    tar -xzv --strip-components 1 --wildcards $INCLUDED_ASSETS
}

function init_git_repo {
    log "INFO" "Checking if the current directory is a Git repository."
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        git init
    else
        log "INFO" "The current directory is a Git repository. Do not re-initialize."
    fi
}

function setup_github_workflows {
    log "INFO" "Setting up GitHub workflows"

    if [ -d ".github" ]; then    
        echo
        echo "The .github directory will be overwritten. Any custom changes will be removed."
        read -p "Are you sure (y/n)? " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .github
        else
            log "INFO" "GitHub workflows NOT installed."
            exit 0
        fi
    fi

    # Copy the workflows from the platform resources
    cp -r ./src/utils/ci/.github .
}


function write_to_platform_version_file {
    echo "${PLATFORM_VERSION}" > .platform-version
}

# Main
clear

echo    "##############################################"
echo    "# Ingenii Azure Data Platform Initialization #"
echo    "##############################################"
echo

check_env_variables
download_platform_source
init_git_repo
setup_github_workflows
write_to_platform_version_file

log "INFO" "Done"