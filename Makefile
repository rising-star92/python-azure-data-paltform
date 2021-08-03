#--------------------------------------------------------------------------------------------------------------------
# VARIABLES
#--------------------------------------------------------------------------------------------------------------------
PLATFORM_VERSION := change/pulumi
CUSTOMER_CODE :=
STACK :=

#--------------------------------------------------------------------------------------------------------------------
# PREP
#--------------------------------------------------------------------------------------------------------------------
clone-repo:
	@if test -z "${PLATFORM_VERSION}"; then echo "PLATFORM_VERSION not set"; exit 1; fi
	$(info Cloning the Ingenii Azure Data Platform repository...)
	@git clone --depth 1 -b ${PLATFORM_VERSION} https://github.com/ingenii-solutions/azure-data-platform.git source

#--------------------------------------------------------------------------------------------------------------------
# COMPONENTS - MANAGEMENT
#--------------------------------------------------------------------------------------------------------------------
init-management:: DIR := runtime/management 
init-management:: PROJECT_NAME := iadp-management
init-management::
	@if test -z "${CUSTOMER_CODE}"; then echo "CUSTOMER_CODE not set"; exit 1; fi
	@mkdir -p ${DIR}
	@pulumi new ../../source/src/pulumi/components/management -C ${DIR} -n ${PROJECT_NAME}-${CUSTOMER_CODE} -g -y > /dev/null
	@cd ${DIR} && python3 -m venv venv && source venv/bin/activate \
	&& pip install ../../source/src/python/packages/ingenii_data_platform --use-feature=in-tree-build

preview-management:
	@if test -z "${STACK}"; then echo "STACK not set"; exit 1; fi
	@cd runtime/management && pulumi preview --stack ${STACK}

apply-management:
	@if test -z "${STACK}"; then echo "STACK not set"; exit 1; fi
	@cd runtime/management && pulumi up --stack ${STACK}

destroy-management:
	@if test -z "${STACK}"; then echo "STACK not set"; exit 1; fi
	@cd runtime/management && pulumi destroy -y --stack ${STACK}

#--------------------------------------------------------------------------------------------------------------------
# API
#--------------------------------------------------------------------------------------------------------------------
prep: clone-repo

init: init-management

preview: preview-management

apply: apply-management

destroy: destroy-management

#--------------------------------------------------------------------------------------------------------------------
# CLEANUP
#--------------------------------------------------------------------------------------------------------------------
clean-source:
	@rm -rf source

clean-runtime:
	@rm -rf runtime

clean: clean-source clean-runtime
