.PHONY: setup setup-env-file setup-dev-dir setup-venv clean init preview apply destroy
.PHONY: init-core-shared preview-core-shared apply-core-shared destroy-core-shared
.PHONY: init-core-dtap preview-core-dtap apply-core-dtap destroy-core-dtap
.PHONY: init-core-extensions preview-core-extensions apply-core-extensions destroy-core-extensions
.PHONY: import-stack-core-shared export-stack-core-shared import-stack-core-dtap export-stack-core-dtap import-stack-core-extensions export-stack-core-extensions

SHELL := /bin/bash

PULUMI_ORGANIZATION :=	ingenii
PULUMI_PARALLELISM  := 	3 	# Increasing this number will speed up deployments but you are likely to encounter race conditions.

PROJECT_ROOT 					:= $(realpath .)
SOURCE_DIR 						:= ${PROJECT_ROOT}/src
PULUMI_SOURCE_DIR 				:= ${PROJECT_ROOT}/src/pulumi
PULUMI_PRJ_CONF_TEMPLATES_DIR 	:= ${PULUMI_SOURCE_DIR}/templates/pulumi-project-conf
DEV_DIR							:= ${PROJECT_ROOT}/dev

CORE_DEFAULT_SHARED_PLATFORM_CONF   := ${DEV_DIR}/platform-config/defaults.shared.yml
CORE_DEFAULT_PLATFORM_CONF 			:= ${DEV_DIR}/platform-config/defaults.yml
PLATFORM_CONF_SCHEMA				:= ${DEV_DIR}/platform-config/schema.yml

CORE_SHARED_SOURCE_DIR 		:= ${PULUMI_SOURCE_DIR}/core-shared
CORE_DTAP_SOURCE_DIR 		:= ${PULUMI_SOURCE_DIR}/core-dtap
CORE_EXTENSIONS_SOURCE_DIR 	:= ${PULUMI_SOURCE_DIR}/core-extensions

VENV_DIR	:= ${PROJECT_ROOT}/venv
RANDOM_STR  := $(shell python -c "import random, string; print(''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(3)))")

# This variable is intentionally left empty.
EXTRA_ARGS 		:=

-include .env

#--------------------------------------------------------------------------------------------------------------------
# SETUP
#--------------------------------------------------------------------------------------------------------------------
setup-env-file:
	$(info [INFO] Setting up the .env file)
	@if test -f ".env"; then echo "[INFO] .env file already exist. Skipping .env-dist setup."; else cp .env-dist .env; fi

setup-dev-dir:
	$(info [INFO] Setting up the dev directory at ${DEV_DIR})
	@mkdir ${DEV_DIR}
	@cp -r ${SOURCE_DIR}/platform-config ${DEV_DIR}
	@find ${DEV_DIR}/platform-config -type f -name 'defaults*.yml' -exec sed -i 's/prefix:.*/prefix: ${RANDOM_STR}/g' {} +
	@find ${DEV_DIR}/platform-config -type f -name 'defaults*.yml' -exec sed -i 's/name: Ingenii Data Platform.*/name: Ingenii Data Platform ${RANDOM_STR}/g' {} +
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-shared/Pulumi.yaml ${CORE_SHARED_SOURCE_DIR}/Pulumi.yaml
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-dtap/Pulumi.yaml ${CORE_DTAP_SOURCE_DIR}/Pulumi.yaml
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-extensions/Pulumi.yaml ${CORE_EXTENSIONS_SOURCE_DIR}/Pulumi.yaml
	@sed -i 's/ingenii-.*/${RANDOM_STR}-adp-core-shared/g' ${CORE_SHARED_SOURCE_DIR}/Pulumi.yaml
	@sed -i 's/ingenii-.*/${RANDOM_STR}-adp-core-dtap/g' ${CORE_DTAP_SOURCE_DIR}/Pulumi.yaml
	@sed -i 's/ingenii-.*/${RANDOM_STR}-adp-core-extensions/g' ${CORE_EXTENSIONS_SOURCE_DIR}/Pulumi.yaml

setup-venv:
	$(info [INFO] Setting up the virtual environment at ${VENV_DIR})
	@python3 -m venv ${VENV_DIR}
	@source ${VENV_DIR}/bin/activate && cd ${SOURCE_DIR} && pip install -r requirements-dev.txt

setup: setup-env-file setup-dev-dir setup-venv
	@$(info ##############################################)
	@$(info You need to complete the following steps to complete the setup:)
	@$(info 	1. Populate the .env file with your credentials.)
	@$(info 	2. Activate the virtual environment by running > source ${VENV_DIR}/bin/activate)
	@$(info ##############################################)

reset:
	@rm -rf ${DEV_DIR}
	@rm -rf ${CORE_SHARED_SOURCE_DIR}/Pulumi.yaml
	@rm -rf ${CORE_DTAP_SOURCE_DIR}/Pulumi.yaml
	@rm -rf ${CORE_EXTENSIONS_SOURCE_DIR}/Pulumi.yaml

clean: reset
	@rm -rf ${VENV_DIR}

#--------------------------------------------------------------------------------------------------------------------
# STACKS
#--------------------------------------------------------------------------------------------------------------------

# SHARED (Shared Services)
CORE_SHARED_STACK 	   	:= ${PULUMI_ORGANIZATION}/shared
init-core-shared:
	@pulumi -C ${CORE_SHARED_SOURCE_DIR} stack select ${CORE_SHARED_STACK} --create --color always --non-interactive ${EXTRA_ARGS}

preview-core-shared: init-core-shared
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_SHARED_PLATFORM_CONF} \
	pulumi -C ${CORE_SHARED_SOURCE_DIR} preview --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-shared: init-core-shared
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_SHARED_PLATFORM_CONF} \
	pulumi -C ${CORE_SHARED_SOURCE_DIR} refresh --color always --non-interactive --yes --diff --skip-preview ${EXTRA_ARGS}

apply-core-shared: init-core-shared
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_SHARED_PLATFORM_CONF} \
	pulumi -C ${CORE_SHARED_SOURCE_DIR} up --parallel ${PULUMI_PARALLELISM} --color always --non-interactive --yes --diff --skip-preview ${EXTRA_ARGS}

destroy-core-shared: init-core-shared
	@pulumi destroy -C ${CORE_SHARED_SOURCE_DIR}  --parallel ${PULUMI_PARALLELISM} --color always ${EXTRA_ARGS}
	@pulumi stack rm -C ${CORE_SHARED_SOURCE_DIR} --stack ${CORE_SHARED_STACK} --non-interactive --yes ${EXTRA_ARGS}

export-stack-core-shared: init-core-shared
	@$(info Exporting stack to ${DEV_DIR}/core-shared.pulumi.stack.json)
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_SHARED_PLATFORM_CONF} \
	pulumi -C ${CORE_SHARED_SOURCE_DIR} stack export --file ${DEV_DIR}/core-shared.pulumi.stack.json ${EXTRA_ARGS}

import-stack-core-shared: init-core-shared
	@$(info Importing stack file ${DEV_DIR}/core-shared.pulumi.stack.json)
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_SHARED_PLATFORM_CONF} \
	pulumi -C ${CORE_SHARED_SOURCE_DIR} stack import --file ${DEV_DIR}/core-shared.pulumi.stack.json ${EXTRA_ARGS}


# DTAP (Dev, Test, Prod)
init-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@pulumi -C ${CORE_DTAP_SOURCE_DIR} stack select ${PULUMI_ORGANIZATION}/${STACK} --create --color always --non-interactive ${EXTRA_ARGS}

preview-core-dtap: init-core-dtap
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_DTAP_SOURCE_DIR} preview --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-dtap: init-core-dtap
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_DTAP_SOURCE_DIR} refresh --color always --diff --non-interactive --yes --skip-preview ${EXTRA_ARGS}

apply-core-dtap: init-core-dtap
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_DTAP_SOURCE_DIR} up --parallel ${PULUMI_PARALLELISM}  --color always --diff --non-interactive --yes --skip-preview ${EXTRA_ARGS}

destroy-core-dtap: init-core-dtap
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@pulumi destroy -C ${CORE_DTAP_SOURCE_DIR} --parallel ${PULUMI_PARALLELISM} --color always --non-interactive --yes --skip-preview ${EXTRA_ARGS}
	@pulumi stack rm -C ${CORE_DTAP_SOURCE_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --non-interactive --yes ${EXTRA_ARGS}

export-stack-core-dtap: init-core-dtap
	@$(info Exporting stack to ${DEV_DIR}/core-dtap.pulumi.stack.json)
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_DTAP_SOURCE_DIR} stack export --file ${DEV_DIR}/core-dtap.pulumi.stack.json ${EXTRA_ARGS}

import-stack-core-dtap: init-core-dtap
	@$(info Importing stack file ${DEV_DIR}/core-dtap.pulumi.stack.json)
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_DTAP_SOURCE_DIR} stack import --file ${DEV_DIR}/core-dtap.pulumi.stack.json ${EXTRA_ARGS}


# EXTENSIONS
init-core-extensions:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@pulumi -C ${CORE_EXTENSIONS_SOURCE_DIR} stack select ${PULUMI_ORGANIZATION}/${STACK} --create --color always --non-interactive ${EXTRA_ARGS}

preview-core-extensions: init-core-extensions
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_EXTENSIONS_SOURCE_DIR} preview --color always --diff --non-interactive ${EXTRA_ARGS}

refresh-core-extensions: init-core-extensions
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_EXTENSIONS_SOURCE_DIR} refresh --color always --diff --non-interactive --yes --skip-preview ${EXTRA_ARGS}

apply-core-extensions: init-core-extensions
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_EXTENSIONS_SOURCE_DIR} up --parallel ${PULUMI_PARALLELISM}  --color always --diff --non-interactive --yes --skip-preview ${EXTRA_ARGS}

destroy-core-extensions: init-core-extensions
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@pulumi destroy -C ${CORE_EXTENSIONS_SOURCE_DIR} --parallel ${PULUMI_PARALLELISM} --color always --non-interactive --yes --skip-preview ${EXTRA_ARGS}
	@pulumi stack rm -C ${CORE_EXTENSIONS_SOURCE_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --non-interactive --yes ${EXTRA_ARGS}

export-stack-core-extensions: init-core-extensions
	@$(info Exporting stack to ${DEV_DIR}/core-extensions.pulumi.stack.json)
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_EXTENSIONS_SOURCE_DIR} stack export --file ${DEV_DIR}/core-extensions.pulumi.stack.json ${EXTRA_ARGS}

import-stack-core-extensions: init-core-extensions
	@$(info Importing stack file ${DEV_DIR}/core-extensions.pulumi.stack.json)
	@ADP_CONFIG_SCHEMA_FILE_PATH=${PLATFORM_CONF_SCHEMA} \
	ADP_DEFAULT_CONFIG_FILE_PATH=${CORE_DEFAULT_PLATFORM_CONF} \
	pulumi -C ${CORE_EXTENSIONS_SOURCE_DIR} stack import --file ${DEV_DIR}/core-extensions.pulumi.stack.json ${EXTRA_ARGS}