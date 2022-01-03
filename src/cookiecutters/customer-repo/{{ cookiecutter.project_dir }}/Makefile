SHELL := /bin/bash

PULUMI_ORGANIZATION := ingenii
PULUMI_PARALLELISM  := 2

SOURCE_DIR      := /platform/src
PROJECT_ROOR    := $(realpath .)
CONFIGS_DIR     := ${PROJECT_ROOT}/configs
VENV_DIR        := ${PROJECT_ROOT}/venv
RUNTIME_DIR     := ${PROJECT_ROOT}/runtime

PULUMI_SOURCE_DIR               := ${SOURCE_DIR}/pulumi
PULUMI_CORE_SHARED_SRC_DIR      := ${PULUMI_SOURCE_DIR}/core-shared
PULUMI_CORE_DTAP_SRC_DIR        := ${PULUMI_SOURCE_DIR}/core-dtap
PULUMI_CORE_EXTENSIONS_SRC_DIR  := ${PULUMI_SOURCE_DIR}/core-extensions
PULUMI_PRJ_CONF_TEMPLATES_DIR   := ${PULUMI_SOURCE_DIR}/templates/pulumi-project-conf

PLATFORM_CONF_SCHEMA_FILE           := ${SOURCE_DIR}/platform-config/schema.yml
PLATFORM_CONF_DEFAULTS_FILE         := ${SOURCE_DIR}/platform-config/defaults.yml
PLATFORM_CONF_SHARED_DEFAULTS_FILE  := ${SOURCE_DIR}/platform-config/defaults.shared.yml

# This variable is intentionally left empty.
EXTRA_ARGS :=

#####################################################################################################################
# Imports
#####################################################################################################################
-include .env	# Optional way to set credentials
include platform.cfg	# Import platform config

#####################################################################################################################
# Functions and Helpers
#####################################################################################################################
define pulumi_init
	@pulumi --cwd $(1) stack select $(2) --create --color always --non-interactive $(3)
endef

define pulumi_preview
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA_FILE} \
	ADP_DEFAULT_CONFIG_FILE_PATH=$(4) \
	ADP_CUSTOM_CONFIGS_FILE_PATH=$(5) \
	pulumi --cwd $(1) preview --stack $(2) --color always --diff --non-interactive $(3)
endef

define pulumi_refresh
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA_FILE} \
	ADP_DEFAULT_CONFIG_FILE_PATH=$(4) \
	ADP_CUSTOM_CONFIGS_FILE_PATH=$(5) \
	pulumi --cwd $(1) refresh --stack $(2) --color always --diff --skip-preview --non-interactive --yes $(3)
endef

define pulumi_apply
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA_FILE} \
	ADP_DEFAULT_CONFIG_FILE_PATH=$(4) \
	ADP_CUSTOM_CONFIGS_FILE_PATH=$(5) \
	pulumi --cwd $(1) up --stack $(2) --parallel ${PULUMI_PARALLELISM} --color always --diff --skip-preview --non-interactive --yes $(3)
endef

define pulumi_destroy
	@pulumi destroy --cwd $(1) --stack $(2) --parallel ${PULUMI_PARALLELISM} --color always $(3)
	@pulumi stack rm --cwd $(1) --stack $(2) --non-interactive --yes $(3)
endef

define pulumi_export_stack
	@pulumi --cwd $(1) stack export --stack $(2) --file $(4) $(3) 
endef

define pulumi_import_stack
	@pulumi --cwd $(1) stack import --stack $(2) --file $(4) $(3) 
endef

define pulumi_destroy_role_assignments
	$(shell ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA_FILE} \
	ADP_DEFAULT_CONFIG_FILE_PATH=$(4) \
	ADP_CUSTOM_CONFIGS_FILE_PATH=$(5) \
	pulumi --cwd $(1) preview --stack $(2) --json --non-interactive $(3) > output.json)
	$(shell python scripts/filter_resources.py output.json delete "azure-native:authorization:RoleAssignment" > output.filtered)
	pulumi --cwd $(1) destroy --stack $(2) $(shell cat output.filtered)
	$(shell rm -rf output.json output.filtered)
endef

_check-for-stack-var:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi

_check-for-cust-code-var:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE variable not set. Check if platform.cfg exist in the current directory."; exit 1; fi

#####################################################################################################################
# Post-Deployment
#####################################################################################################################

az_login:
	@az login --service-principal -t ${ARM_TENANT_ID} -u ${ARM_CLIENT_ID} -p ${ARM_CLIENT_SECRET} > /dev/null

define upload_notebooks
	@$(eval DATABRICKS_AAD_TOKEN=$(shell az account get-access-token  --subscription ${ARM_SUBSCRIPTION_ID} --resource 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d | jq '.accessToken' --raw-output))

	@$(eval ANALYTICS_HOST=$(shell pulumi stack output --cwd $(1) --stack $(2) --json $(3) | jq '.root.analytics.databricks.workspaces.analytics.url' | sed 's/"//g'))
	@DATABRICKS_AAD_TOKEN=${DATABRICKS_AAD_TOKEN} databricks configure --aad-token --host https://${ANALYTICS_HOST}
	@databricks workspace mkdirs '/Shared/Ingenii Engineering'
	@ls ${SOURCE_DIR}/notebooks/analytics | awk -F '.' '{ print $$1 }' | xargs -I {} databricks workspace import -l PYTHON ${SOURCE_DIR}/notebooks/analytics/{}.py '/Shared/Ingenii Engineering/{}' --overwrite

	@$(eval ENGINEERING_HOST=$(shell pulumi stack output --cwd $(1) --stack $(2) --json $(3) | jq '.root.analytics.databricks.workspaces.engineering.url' | sed 's/"//g'))
	@DATABRICKS_AAD_TOKEN=${DATABRICKS_AAD_TOKEN} databricks configure --aad-token --host https://${ENGINEERING_HOST}
	@databricks workspace mkdirs '/Shared/Ingenii Engineering'
	@ls ${SOURCE_DIR}/notebooks/engineering | awk -F '.' '{ print $$1 }' | xargs -I {} databricks workspace import -l PYTHON ${SOURCE_DIR}/notebooks/engineering/{}.py '/Shared/Ingenii Engineering/{}' --overwrite
endef

define enable_trigger
	@$(eval DATAFACTORY_ID=$(shell pulumi stack output --cwd $(1) --stack $(2) --json $(3) | jq '.root.analytics.datafactory.factories.orchestration.id' | sed 's/"//g'))
	@az datafactory trigger start --ids "${DATAFACTORY_ID}/triggers/Raw file created"
endef

#####################################################################################################################
# Stacks
#####################################################################################################################

# Shared Stack
CORE_SHARED_STACK := ${PULUMI_ORGANIZATION}/shared
init-core-shared: _check-for-cust-code-var
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-shared/Pulumi.yaml	${PULUMI_SOURCE_DIR}/core-shared/Pulumi.yaml
	@sed -i 's|ingenii-|${CUSTOMER_CODE}-|g'		${PULUMI_SOURCE_DIR}/core-shared/Pulumi.yaml
	@$(call pulumi_init,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS})

preview-core-shared:
	@$(call pulumi_preview,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

refresh-core-shared: 
	@$(call pulumi_refresh,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

apply-core-shared: 
	@$(call pulumi_apply,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

destroy-core-shared: 
	@$(call pulumi_destroy,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS})

CORE_SHARED_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.shared.json
export-stack-core-shared: 
	@$(info Exporting stack to ${CORE_SHARED_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${CORE_SHARED_STACK_OUTPUT_FILE})

import-stack-core-shared: 
	@$(info Importing stack file ${CORE_SHARED_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${CORE_SHARED_STACK_OUTPUT_FILE})

destroy-tainted-role-assignments-core-shared:
	@$(info Deleting all role assignments for ${CORE_SHARED_STACK})
	@$(call pulumi_destroy_role_assignments,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

# Shared Stack Extensions
CORE_SHARED_EXTENSIONS_STACK := ${PULUMI_ORGANIZATION}/shared
init-core-shared-extensions: _check-for-cust-code-var
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-extensions/Pulumi.yaml ${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml
	@sed -i 's|ingenii-|${CUSTOMER_CODE}-|g' ${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml
	@$(call pulumi_init,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS})

preview-core-shared-extensions: 
	@$(call pulumi_preview,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

refresh-core-shared-extensions: 
	@$(call pulumi_refresh,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

apply-core-shared-extensions: 
	@$(call pulumi_apply,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

destroy-core-shared-extensions: 
	@$(call pulumi_destroy,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS})

CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.shared.extensions.json
export-stack-core-shared-extensions: 
	@$(info Exporting stack to ${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})

import-stack-core-shared-extensions: 
	@$(info Importing stack file ${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})

destroy-tainted-role-assignments-core-shared-extensions: _check-for-stack-var
	@$(info Deleting all role assignments for ${CORE_SHARED_EXTENSIONS_STACK})
	@$(call pulumi_destroy_role_assignments,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

# DTAP Stack
init-core-dtap: _check-for-stack-var _check-for-cust-code-var
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-dtap/Pulumi.yaml ${PULUMI_SOURCE_DIR}/core-dtap/Pulumi.yaml
	@sed -i 's|ingenii-|${CUSTOMER_CODE}-|g' ${PULUMI_SOURCE_DIR}/core-dtap/Pulumi.yaml
	@$(call pulumi_init,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

preview-core-dtap: 
	@$(call pulumi_preview,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

refresh-core-dtap: 
	@$(call pulumi_refresh,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

apply-core-dtap: 
	@$(call pulumi_apply,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

post-deploy-core-dtap: az_login
	@$(call upload_notebooks,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})
	@$(call enable_trigger,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

destroy-core-dtap: 
	@$(call pulumi_destroy,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

CORE_DTAP_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.dtap.json
export-stack-core-dtap: 
	@$(info Exporting stack to ${CORE_DTAP_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_STACK_OUTPUT_FILE})

import-stack-core-dtap: 
	@$(info Importing stack file ${CORE_DTAP_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_STACK_OUTPUT_FILE})

destroy-tainted-role-assignments-core-dtap: _check-for-stack-var
	@$(info Deleting all role assignments for ${PULUMI_ORGANIZATION}/${STACK})
	@$(call pulumi_destroy_role_assignments,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

# DTAP Stack Extensions
init-core-dtap-extensions: _check-for-stack-var _check-for-cust-code-var
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-extensions/Pulumi.yaml ${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml
	@sed -i 's|ingenii-|${CUSTOMER_CODE}-|g' ${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml
	@$(call pulumi_init,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

preview-core-dtap-extensions: 
	@$(call pulumi_preview,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

refresh-core-dtap-extensions: 
	@$(call pulumi_refresh,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

apply-core-dtap-extensions: 
	@$(call pulumi_apply,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

destroy-core-dtap-extensions: 
	@$(call pulumi_destroy,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.dtap.extensions.json
export-stack-core-dtap-extensions: 
	@$(info Exporting stack to ${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})

import-stack-core-dtap-extensions: 
	@$(info Importing stack file ${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})

destroy-tainted-role-assignments-core-dtap-extensions: _check-for-stack-var
	@$(info Deleting all role assignments for ${PULUMI_ORGANIZATION}/${STACK})
	@$(call pulumi_destroy_role_assignments,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

#####################################################################################################################
# SETUP
#####################################################################################################################
.PHONY: clone-repo
clone-repo:
	@if test -d ${SOURCE_DIR}; then echo "The Ingenii Azure Data Platform repo has been cloned already. Run 'make clean' and try again."; exit 1; fi
	@if test -z "${PLATFORM_VERSION}"; then echo "PLATFORM_VERSION not set."; exit 1; fi
	@git clone \
	--depth 1 -b ${PLATFORM_VERSION} https://github.com/ingenii-solutions/azure-data-platform.git temp_clone \
	&& mv temp_clone/src ${PROJECT_ROOT} \
	&& rm -rf temp_clone

.PHONY: clone-repo-using-ssh
clone-repo-using-ssh:
	@if test -d ${SOURCE_DIR}; then echo "The Ingenii Azure Data Platform repo has been cloned already. Run 'make clean' and try again."; exit 1; fi
	@if test -z "${PLATFORM_VERSION}"; then echo "PLATFORM_VERSION not set."; exit 1; fi
	@git clone \
	--depth 1 -b ${PLATFORM_VERSION} git@github.com:ingenii-solutions/azure-data-platform.git temp_clone \
	&& mv temp_clone/src ${PROJECT_ROOT} \
	&& rm -rf temp_clone

.PHONY: set-platform-version
set-platform-version:
	@if test -z "${VERSION}"; then echo "VERSION variable not set. Try make update-platform-version VERSION=xxx"; exit 1; fi
	@sed -i 's/PLATFORM_VERSION=.*/PLATFORM_VERSION=${VERSION}/g' ${PROJECT_ROOT}/platform.cfg
	@sed -i 's/azure-data-platform-iac-runtime:.*/azure-data-platform-iac-runtime:${VERSION}/g' ${PROJECT_ROOT}/.github/workflows/*.yml
	@sed -i 's/azure-data-platform-iac-runtime:.*/azure-data-platform-iac-runtime:${VERSION}",/g' ${PROJECT_ROOT}/.devcontainer/devcontainer.json

.PHONY: clean
clean:
	@rm -rf ${SOURCE_DIR}
	@rm -rf ${PROJECT_ROOT}/temp_clone

#####################################################################################################################
# API
#####################################################################################################################
init-shared: init-core-shared
preview-shared: preview-core-shared
refresh-shared: refresh-core-shared
apply-shared: apply-core-shared
destroy-shared: destroy-core-shared

init-shared-extensions: init-core-shared-extensions
preview-shared-extensions: preview-core-shared-extensions
refresh-shared-extensions: refresh-core-shared-extensions
apply-shared-extensions: apply-core-shared-extensions
destroy-shared-extensions: destroy-core-shared-extensions

init-dtap: init-core-dtap
preview-dtap: preview-core-dtap
refresh-dtap: refresh-core-dtap
apply-dtap: apply-core-dtap
post-deploy-dtap: post-deploy-core-dtap
destroy-dtap: destroy-core-dtap

init-dtap-extensions: init-core-dtap-extensions
preview-dtap-extensions: preview-core-dtap-extensions
refresh-dtap-extensions: refresh-core-dtap-extensions
apply-dtap-extensions: apply-core-dtap-extensions
destroy-dtap-extensions: destroy-core-dtap-extensions

init-extensions: init-core-dtap-extensions init-core-shared-extensions
preview-extensions: preview-core-dtap-extensions preview-core-shared-extensions
refresh-extensions: refresh-core-dtap-extensions refresh-core-shared-extensions
apply-extensions: apply-core-dtap-extensions apply-core-shared-extensions
destroy-extensions: destroy-core-dtap-extensions destroy-core-shared-extensions

init: _check-for-stack-var init-shared init-dtap init-extensions
preview: _check-for-stack-var preview-shared preview-dtap preview-extensions
refresh: _check-for-stack-var refresh-shared refresh-dtap refresh-extensions
apply: _check-for-stack-var apply-shared apply-dtap apply-extensions
destroy: _check-for-stack-var destroy-extensions destroy-dtap
	@($info You need to run 'make destroy-shared' after you have destroyed all DTAP environments.)
