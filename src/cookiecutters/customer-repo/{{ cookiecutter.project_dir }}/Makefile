SHELL := /bin/bash

PULUMI_ORGANIZATION :=	ingenii

PROJECT_ROOT 	:= $(realpath .)
CONFIGS_DIR 	:= ${PROJECT_ROOT}/configs
VENV_DIR 		:= ${PROJECT_ROOT}/venv
SOURCE_DIR 		:= ${PROJECT_ROOT}/source
RUNTIME_DIR 	:= ${PROJECT_ROOT}/runtime

# This variable is intentionally left empty.
EXTRA_ARGS 		:=

include platform.cfg

#--------------------------------------------------------------------------------------------------------------------
# SETUP
#--------------------------------------------------------------------------------------------------------------------
clone-repo:
	@if test -d ${SOURCE_DIR}; then echo "The Ingenii Azure Data Platform repo has been cloned already. Run 'make clean' and try again."; exit 1; fi
	@if test -z "${PLATFORM_VERSION}"; then echo "PLATFORM_VERSION not set."; exit 1; fi
	@git clone \
	--depth 1 -b ${PLATFORM_VERSION} https://github.com/ingenii-solutions/azure-data-platform.git ${SOURCE_DIR}

clone-repo-using-ssh:
	@if test -d ${SOURCE_DIR}; then echo "The Ingenii Azure Data Platform repo has been cloned already. Run 'make clean' and try again."; exit 1; fi
	@if test -z "${PLATFORM_VERSION}"; then echo "PLATFORM_VERSION not set."; exit 1; fi
	@git clone \
	--depth 1 -b ${PLATFORM_VERSION} git@github.com:ingenii-solutions/azure-data-platform.git ${SOURCE_DIR}

set-platform-version:
	@if test -z "${VERSION}"; then echo "VERSION variable not set. Try make update-platform-version VERSION=xxx"; exit 1; fi
	@sed -i 's/PLATFORM_VERSION=.*/PLATFORM_VERSION=${VERSION}/g' ${PROJECT_ROOT}/platform.cfg
	@sed -i 's/azure-data-platform-iac-runtime:.*/azure-data-platform-iac-runtime:${VERSION}/g' ${PROJECT_ROOT}/.github/workflows/ingenii_data_platform_ci.yml
	@sed -i 's/azure-data-platform-iac-runtime:.*/azure-data-platform-iac-runtime:${VERSION}/g' ${PROJECT_ROOT}/.devcontainer/devcontainer.json

#--------------------------------------------------------------------------------------------------------------------
# STACKS
#--------------------------------------------------------------------------------------------------------------------
# SHARED (Shared Services)
CORE_SHARED_DIR := ${RUNTIME_DIR}/core-shared
init-core-shared:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_SHARED_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-shared -C ${CORE_SHARED_DIR} -n ${CUSTOMER_CODE}-iadp-core-shared -g -y > /dev/null

preview-core-shared:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi preview -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --diff ${EXTRA_ARGS}

apply-core-shared:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi up -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} -p 3 --color always --diff ${EXTRA_ARGS} 

destroy-core-shared:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi destroy -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always ${EXTRA_ARGS}

# DTAP (Dev, Test, Acceptance, Prod)
CORE_DTAP_DIR := ${RUNTIME_DIR}/core-dtap
init-core-dtap:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_DTAP_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-dtap -C ${CORE_DTAP_DIR} -n ${CUSTOMER_CODE}-iadp-core-dtap -g -y > /dev/null

preview-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi preview -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --diff ${EXTRA_ARGS}

apply-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi up -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} -p 3 --color always --diff ${EXTRA_ARGS} 

destroy-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi destroy -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always ${EXTRA_ARGS}

upload-notebooks:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@az login --service-principal -t ${ARM_TENANT_ID} -u ${ARM_CLIENT_ID} -p ${ARM_CLIENT_SECRET} > /dev/null
	@$(eval DATABRICKS_AAD_TOKEN=$(shell az account get-access-token --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d | jq '.accessToken' --raw-output))

	@$(eval ANALYTICS_HOST=$(shell pulumi stack output -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --json | jq '.root.analytics.databricks.workspaces.analytics.url' | sed 's/"//g'))
	@DATABRICKS_AAD_TOKEN=${DATABRICKS_AAD_TOKEN} databricks configure --aad-token --host https://${ANALYTICS_HOST}
	@databricks workspace mkdirs '/Shared/Ingenii Engineering'
	@ls ${SOURCE_DIR}/src/notebooks/analytics | awk -F '.' '{ print $$1 }' | xargs -I {} databricks workspace import -l PYTHON ${SOURCE_DIR}/src/notebooks/analytics/{}.py '/Shared/Ingenii Engineering/{}' --overwrite

	@$(eval ENGINEERING_HOST=$(shell pulumi stack output -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --json | jq '.root.analytics.databricks.workspaces.engineering.url' | sed 's/"//g'))
	@DATABRICKS_AAD_TOKEN=${DATABRICKS_AAD_TOKEN} databricks configure --aad-token --host https://${ENGINEERING_HOST}
	@databricks workspace mkdirs '/Shared/Ingenii Engineering'
	@ls ${SOURCE_DIR}/src/notebooks/engineering | awk -F '.' '{ print $$1 }' | xargs -I {} databricks workspace import -l PYTHON ${SOURCE_DIR}/src/notebooks/engineering/{}.py '/Shared/Ingenii Engineering/{}' --overwrite

# PACKAGES (Additional Packages)
CORE_PACKAGES_DIR := ${RUNTIME_DIR}/core-packages
init-core-packages:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_PACKAGES_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-packages -C ${CORE_PACKAGES_DIR} -n ${CUSTOMER_CODE}-iadp-core-packages -g -y > /dev/null

preview-core-packages:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi preview -C ${CORE_PACKAGES_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --diff ${EXTRA_ARGS}

apply-core-packages:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi up -C ${CORE_PACKAGES_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} -p 3 --color always --diff ${EXTRA_ARGS} 

destroy-core-packages:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi destroy -C ${CORE_PACKAGES_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always ${EXTRA_ARGS}
#--------------------------------------------------------------------------------------------------------------------
# CLEANUP
#--------------------------------------------------------------------------------------------------------------------
clean-source:
	@rm -rf ${PROJECT_ROOT}/source

clean-runtime:
	@rm -rf ${PROJECT_ROOT}/runtime

#--------------------------------------------------------------------------------------------------------------------
# GENERAL API
#--------------------------------------------------------------------------------------------------------------------
init-shared: init-core-shared
preview-shared: preview-core-shared
apply-shared: apply-core-shared
destroy-shared: destroy-core-shared

init-dtap: init-core-dtap
preview-dtap: preview-core-dtap
apply-dtap: apply-core-dtap
destroy-dtap: destroy-core-dtap

init-packages: init-core-packages
preview-packages: preview-core-packages
apply-packages: apply-core-packages
destroy-packages: destroy-core-packages

init: init-shared init-dtap init-packages
preview: preview-shared preview-dtap preview-packages
apply: apply-shared apply-dtap apply-packages

clean: clean-source clean-runtime