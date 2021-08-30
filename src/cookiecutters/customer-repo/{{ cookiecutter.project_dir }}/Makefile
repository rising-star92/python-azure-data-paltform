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

#--------------------------------------------------------------------------------------------------------------------
# STACKS
#--------------------------------------------------------------------------------------------------------------------
# DTAP (Dev, Test, Acceptance, Prod)
CORE_DTAP_DIR := ${RUNTIME_DIR}/core-dtap
init-core-dtap:
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${CORE_DTAP_DIR}
	@pulumi new ${SOURCE_DIR}/src/pulumi/core-dtap -C ${CORE_DTAP_DIR} -n ${CUSTOMER_CODE}-iadp-core-dtap -g -y > /dev/null

preview-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/schemas/platform-config/schema.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi preview -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always --diff ${EXTRA_ARGS}

apply-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/schemas/platform-config/schema.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi up -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} -p 3 --color always --diff ${EXTRA_ARGS} 

destroy-core-dtap:
	@if test -z "${STACK}"; then echo "STACK variable not set. Try 'make <your command> STACK=<stack-name>'"; exit 1; fi
	@ADP_CONFIG_SCHEMA_FILE_PATH=${SOURCE_DIR}/src/schemas/platform-config/schema.yml \
	ADP_CUSTOM_CONFIGS_FILE_PATH=${CONFIGS_DIR}/${STACK}.yml \
	pulumi destroy -C ${CORE_DTAP_DIR} --stack ${PULUMI_ORGANIZATION}/${STACK} --color always ${EXTRA_ARGS}

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
init: init-core-dtap

preview-dtap: preview-core-dtap

apply-dtap: apply-core-dtap

destroy-dtap: destroy-core-dtap

clean: clean-source clean-runtime