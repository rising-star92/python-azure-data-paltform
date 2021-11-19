SHELL := /bin/bash

PULUMI_ORGANIZATION	:= ingenii
PULUMI_PARALLELISM	:= 2

PROJECT_ROOT 	:= $(realpath .)
CONFIGS_DIR 	:= ${PROJECT_ROOT}/configs
VENV_DIR 		:= ${PROJECT_ROOT}/venv
SOURCE_DIR 		:= ${PROJECT_ROOT}/src
RUNTIME_DIR 	:= ${PROJECT_ROOT}/runtime

PULUMI_CORE_SHARED_SRC_DIR 		:= ${SOURCE_DIR}/pulumi/core-shared
PULUMI_CORE_DTAP_SRC_DIR 		:= ${SOURCE_DIR}/pulumi/core-dtap
PULUMI_CORE_EXTENSIONS_SRC_DIR 	:= ${SOURCE_DIR}/pulumi/core-extensions

PLATFORM_CONF_SCHEMA_FILE			:= ${SOURCE_DIR}/platform-config/schema.yml
PLATFORM_CONF_DEFAULTS_FILE 		:= ${SOURCE_DIR}/platform-config/defaults.yml
PLATFORM_CONF_SHARED_DEFAULTS_FILE 	:= ${SOURCE_DIR}/platform-config/defaults.shared.yml

# This variable is intentionally left empty.
EXTRA_ARGS 		:=

#####################################################################################################################
# Imports
#####################################################################################################################
-include .env	# Optional way to set credentials
include platform.cfg	# Import platform config

#####################################################################################################################
# Functions
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

#####################################################################################################################
# Stacks
#####################################################################################################################

# Shared Stack
CORE_SHARED_STACK	:= ${PULUMI_ORGANIZATION}/shared
init-core-shared:
	@$(call pulumi_init,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS})

preview-core-shared: init-core-shared
	@$(call pulumi_preview,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

refresh-core-shared: init-core-shared
	@$(call pulumi_refresh,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

apply-core-shared: init-core-shared
	@$(call pulumi_apply,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

destroy-core-shared: init-core-shared
	@$(call pulumi_destroy,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS})

CORE_SHARED_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.shared.json
export-stack-core-shared: init-core-shared
	@$(info Exporting stack to ${CORE_SHARED_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${CORE_SHARED_STACK_OUTPUT_FILE})

import-stack-core-shared: init-core-shared
	@$(info Importing stack file ${CORE_SHARED_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_SHARED_SRC_DIR},${CORE_SHARED_STACK},${EXTRA_ARGS},${CORE_SHARED_STACK_OUTPUT_FILE})

# Shared Stack Extensions
CORE_SHARED_EXTENSIONS_STACK	:= ${PULUMI_ORGANIZATION}/shared
init-core-shared-extensions:
	@$(call pulumi_init,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS})

preview-core-shared-extensions: init-core-shared-extensions
	@$(call pulumi_preview,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

refresh-core-shared-extensions: init-core-shared-extensions
	@$(call pulumi_refresh,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

apply-core-shared-extensions: init-core-shared-extensions
	@$(call pulumi_apply,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${PLATFORM_CONF_SHARED_DEFAULTS_FILE},${CONFIGS_DIR}/shared.yml)

destroy-core-shared-extensions: init-core-shared-extensions
	@$(call pulumi_destroy,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS})

CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.shared.extensions.json
export-stack-core-shared-extensions: init-core-shared-extensions
	@$(info Exporting stack to ${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})

import-stack-core-shared-extensions: init-core-shared-extensions
	@$(info Importing stack file ${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${CORE_SHARED_EXTENSIONS_STACK},${EXTRA_ARGS},${CORE_SHARED_EXTENSIONS_STACK_OUTPUT_FILE})

# DTAP Stack
_check-for-stack-var:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi

init-core-dtap: _check-for-stack-var
	@$(call pulumi_init,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

preview-core-dtap: init-core-dtap
	@$(call pulumi_preview,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

refresh-core-dtap: init-core-dtap
	@$(call pulumi_refresh,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

apply-core-dtap: init-core-dtap
	@$(call pulumi_apply,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

destroy-core-dtap: init-core-dtap
	@$(call pulumi_destroy,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

CORE_DTAP_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.dtap.json
export-stack-core-dtap: init-core-dtap
	@$(info Exporting stack to ${CORE_DTAP_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_STACK_OUTPUT_FILE})

import-stack-core-dtap: init-core-dtap
	@$(info Importing stack file ${CORE_DTAP_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_DTAP_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_STACK_OUTPUT_FILE})

# DTAP Stack Extensions
init-core-dtap-extensions: _check-for-stack-var
	@$(call pulumi_init,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

preview-core-dtap-extensions: init-core-dtap-extensions
	@$(call pulumi_preview,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

refresh-core-dtap-extensions: init-core-dtap-extensions
	@$(call pulumi_refresh,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

apply-core-dtap-extensions: init-core-dtap-extensions
	@$(call pulumi_apply,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${PLATFORM_CONF_DEFAULTS_FILE},${CONFIGS_DIR}/${STACK}.yml)

destroy-core-dtap-extensions: init-core-dtap-extensions
	@$(call pulumi_destroy,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS})

CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE := ${PROJECT_ROOT}/pulumi.stack.core.dtap.extensions.json
export-stack-core-dtap-extensions: init-core-dtap-extensions
	@$(info Exporting stack to ${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_export_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})

import-stack-core-dtap-extensions: init-core-dtap-extensions
	@$(info Importing stack file ${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})
	@$(call pulumi_import_stack,${PULUMI_CORE_EXTENSIONS_SRC_DIR},${PULUMI_ORGANIZATION}/${STACK},${EXTRA_ARGS},${CORE_DTAP_EXTENSIONS_STACK_OUTPUT_FILE})

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
	@sed -i 's/azure-data-platform-iac-runtime:.*/azure-data-platform-iac-runtime:${VERSION}/g' ${PROJECT_ROOT}/.github/workflows/ingenii_data_platform_ci.yml
	@sed -i 's/azure-data-platform-iac-runtime:.*/azure-data-platform-iac-runtime:${VERSION}/g' ${PROJECT_ROOT}/.devcontainer/devcontainer.json

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
	@(info You need to run 'make destroy-shared' after you have destroyed all DTAP environments.)