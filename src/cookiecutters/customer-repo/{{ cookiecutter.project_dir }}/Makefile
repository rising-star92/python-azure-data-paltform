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
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-shared -C ${CORE_SHARED_DIR} -n ${CUSTOMER_CODE}-iadp-core-shared -g --yes --non-interactive > /dev/null

init-core-shared-stack:
	@pulumi -C ${CORE_SHARED_DIR} stack select ${PULUMI_ORGANIZATION}/shared --create --color always --non-interactive

preview-core-shared: init-core-shared-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi preview -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/shared --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-shared: init-core-shared-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi refresh -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/shared --color always --yes --non-interactive ${EXTRA_ARGS}

apply-core-shared: init-core-shared-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi up -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/shared -p 3 --color always --diff --yes --non-interactive ${EXTRA_ARGS} 

destroy-core-shared:
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi destroy -C ${CORE_SHARED_DIR} --stack ${PULUMI_ORGANIZATION}/shared --color always --yes --non-interactive ${EXTRA_ARGS}

# DTAP (Dev, Test, Acceptance, Prod)
CORE_DTAP_DIR := ${RUNTIME_DIR}/core-dtap
init-core-dtap:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_DTAP_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-dtap -C ${CORE_DTAP_DIR} -n ${CUSTOMER_CODE}-iadp-core-dtap -g --yes --non-interactive > /dev/null

init-core-dtap-stack:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@pulumi -C ${CORE_DTAP_DIR} stack select ${PULUMI_ORGANIZATION}/${STACK} --create --color always --non-interactive

preview-core-dtap: init-core-dtap-stack
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi preview -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-dtap: init-core-dtap-stack
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi refresh -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --yes --non-interactive ${EXTRA_ARGS}

apply-core-dtap: init-core-dtap-stack
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi up -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} -p 3 --color always --diff --yes --non-interactive ${EXTRA_ARGS} 

destroy-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi destroy -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --yes --non-interactive ${EXTRA_ARGS}

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

# EXTENSIONS
CORE_EXTENSIONS_DIR := ${RUNTIME_DIR}/core-extensions
init-core-extensions:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_EXTENSIONS_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-extensions -C ${CORE_EXTENSIONS_DIR} -n ${CUSTOMER_CODE}-iadp-core-extensions -g --yes --non-interactive > /dev/null

init-core-extensions-stack:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@pulumi -C ${CORE_EXTENSIONS_DIR} stack select ${PULUMI_ORGANIZATION}/${STACK} --create --color always --non-interactive

preview-core-extensions: init-core-extensions-stack
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi preview -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-extensions: init-core-extensions-stack
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi refresh -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --yes --non-interactive ${EXTRA_ARGS}

apply-core-extensions: init-core-extensions-stack
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi up -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} -p 3 --color always --diff --yes --non-interactive ${EXTRA_ARGS} 

destroy-core-extensions: 
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi destroy -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --yes --non-interactive ${EXTRA_ARGS}

init-core-shared-extensions:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_EXTENSIONS_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-extensions -C ${CORE_EXTENSIONS_DIR} -n ${CUSTOMER_CODE}-iadp-core-extensions -g --yes --non-interactive > /dev/null

init-core-shared-extensions-stack:
	@pulumi -C ${CORE_EXTENSIONS_DIR} stack select ${PULUMI_ORGANIZATION}/shared --create --color always --non-interactive

preview-core-shared-extensions: init-core-shared-extensions-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi preview -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/shared --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-shared-extensions: init-core-shared-extensions-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi refresh -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/shared --color always --yes --non-interactive ${EXTRA_ARGS}

apply-core-shared-extensions: init-core-shared-extensions-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi up -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/shared -p 3 --color always --diff --yes --non-interactive ${EXTRA_ARGS} 

destroy-core-shared-extensions: init-core-shared-extensions-stack
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/platform-config/schema.yml \
	ADP_DEFAULT_CONFIG_FILE_PATH=${SOURCE_DIR}/src/platform-config/defaults.shared.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/shared.yml \
	pulumi destroy -C ${CORE_EXTENSIONS_DIR} --stack ${PULUMI_ORGANIZATION}/shared --color always --yes --non-interactive ${EXTRA_ARGS}
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
init-shared: init-core-shared init-core-shared-extensions
preview-shared: preview-core-shared preview-core-shared-extensions
refresh-shared: refresh-core-shared refresh-core-shared-extensions
apply-shared: apply-core-shared apply-core-shared-extensions
destroy-shared: destroy-core-shared destroy-core-shared-extensions

init-dtap: init-core-dtap init-core-extensions
preview-dtap: preview-core-dtap preview-core-extensions
refresh-dtap: refresh-core-dtap refresh-core-extensions
apply-dtap: apply-core-dtap	apply-core-extensions
destroy-dtap: destroy-core-dtap	destroy-core-extensions

clean: clean-source clean-runtime