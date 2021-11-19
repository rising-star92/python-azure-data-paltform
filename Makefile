SHELL := /bin/bash

REGION := EastUS

TEMP_DIR		:= /tmp
PROJECT_ROOT	:= $(realpath .)

VENV_DIR 			:= ${PROJECT_ROOT}/venv
SOURCE_DIR			:= ${PROJECT_ROOT}/src
PULUMI_SOURCE_DIR	:= ${PROJECT_ROOT}/src/pulumi

DEV_DIR_NAME	:= dev
DEV_DIR 		:= ${PROJECT_ROOT}/${DEV_DIR_NAME}

RANDOM_STR			:= $(shell python -c "import random, string; print(''.join(random.SystemRandom().choice(string.ascii_lowercase) for _ in range(10)))")
RANDOM_STR_LEN_3	:= $(shell python -c "print('${RANDOM_STR}'[:3])")
RANDOM_STR_LEN_4	:= $(shell python -c "print('${RANDOM_STR}'[:4])")

#####################################################################################################################
# Helper Targets
# Please only use these targets if really necessary. Scroll down to the API section for the list of targets to use.
#####################################################################################################################
COOKIECUTTER_CUSTOMER_REPO_DIR				:= ${SOURCE_DIR}/cookiecutters/customer-repo
COOKIECUTTER_CUSTOMER_REPO_CONFIG_TPL_FILE	:= ${COOKIECUTTER_CUSTOMER_REPO_DIR}/cookiecutter.tpl
setup-cruft-config:
	$(info [INFO] Configuring the Cookiecutter template...)
	@cp ${COOKIECUTTER_CUSTOMER_REPO_CONFIG_TPL_FILE} ${TEMP_DIR}/${RANDOM_STR}.yml
	@sed -i 's|customer_code_replace_me.*|${RANDOM_STR_LEN_3}|g' ${TEMP_DIR}/${RANDOM_STR}.yml;
	@sed -i 's|region_replace_me.*|${REGION}|g' ${TEMP_DIR}/${RANDOM_STR}.yml;
	@sed -i 's|resource_prefix_replace_me.*|${RANDOM_STR_LEN_3}|g' ${TEMP_DIR}/${RANDOM_STR}.yml;
	@sed -i 's|unique_id_replace_me.*|${RANDOM_STR_LEN_4}|g' ${TEMP_DIR}/${RANDOM_STR}.yml;
	@sed -i 's|platform_version_replace_me.*|development|g' ${TEMP_DIR}/${RANDOM_STR}.yml;
	@sed -i 's|project_dir_replace_me.*|${DEV_DIR_NAME}|g' ${TEMP_DIR}/${RANDOM_STR}.yml;

setup-cruft-project:
	$(info [INFO] Setting up the Cookiecutter project in ${DEV_DIR})
	@cruft create ${PROJECT_ROOT} --directory src/cookiecutters/customer-repo --config-file ${TEMP_DIR}/${RANDOM_STR}.yml --no-input \

setup-dir-links:
	@ln -s ${SOURCE_DIR} ${DEV_DIR}/src

setup-env-file:
	$(info [INFO] Setting up the .env file)
	@if [ ! -f ${DEV_DIR}/.env ]; then cp ${DEV_DIR}/.env-dist ${DEV_DIR}/.env ; else echo "[INFO] '${DEV_DIR}/.env' file already exist. Skipping env file setup."; fi

PULUMI_PRJ_CONF_TEMPLATES_DIR	:= ${PULUMI_SOURCE_DIR}/templates/pulumi-project-conf
setup-pulumi-project-configs:
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-shared/Pulumi.yaml		${PULUMI_SOURCE_DIR}/core-shared/Pulumi.yaml
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-dtap/Pulumi.yaml			${PULUMI_SOURCE_DIR}/core-dtap/Pulumi.yaml
	@cp ${PULUMI_PRJ_CONF_TEMPLATES_DIR}/core-extensions/Pulumi.yaml	${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml
	@sed -i 's|ingenii-|${RANDOM_STR_LEN_4}-|g'	${PULUMI_SOURCE_DIR}/core-shared/Pulumi.yaml
	@sed -i 's|ingenii-|${RANDOM_STR_LEN_4}-|g'	${PULUMI_SOURCE_DIR}/core-dtap/Pulumi.yaml
	@sed -i 's|ingenii-|${RANDOM_STR_LEN_4}-|g'	${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml

setup-python-venv:
	$(info [INFO] Setting up the Python virtual environment at ${VENV_DIR})
	@python3 -m venv ${VENV_DIR}
	@source ${VENV_DIR}/bin/activate && cd ${SOURCE_DIR} && pip install -r requirements-dev.txt

show-setup-banner:
	@$(info ####################################################################################)
	@$(info	Success! A new development environment has been created at ${PROJECT_ROOT}/${DEV_DIR_NAME})
	@$(info )
	@$(info Step 1 -> Populate the ${PROJECT_ROOT}/${DEV_DIR_NAME}/.env file with your credentials)
	@$(info ------------------------------------------------------------------------------------)
	@$(info )
	@$(info Step 2 -> Activate the virtual environment by running the command below:)
	@$(info source ${VENV_DIR}/bin/activate)
	@$(info ------------------------------------------------------------------------------------)
	@$(info )
	@$(info Important)
	@$(info ------------------------------------------------------------------------------------)
	@$(info Please note that the ${PROJECT_ROOT}/src directory is linked to the)
	@$(info ${PROJECT_ROOT}/${DEV_DIR_NAME}/src directory.)
	@$(info ####################################################################################)

show-reset-banner:
	@$(info ####################################################################################)
	@$(info PLEASE READ CAREFULLY)
	@$(info ####################################################################################)

remove-dev-dir:
	$(info Removing the Development directory at: ${DEV_DIR})
	$(info Please make a copy of your .env file if you wish to retain your credentials.)
	@rm -r -I ${DEV_DIR}

remove-venv-dir:
	$(info Removing the Python Virtual Environment directory at: ${VENV_DIR})
	@rm -r -I ${VENV_DIR}

remove-pulumi-project-configs:
	$(info Removing the Pulumi project configuration files)
	@rm  ${PULUMI_SOURCE_DIR}/core-shared/Pulumi.yaml
	@rm  ${PULUMI_SOURCE_DIR}/core-dtap/Pulumi.yaml
	@rm  ${PULUMI_SOURCE_DIR}/core-extensions/Pulumi.yaml

set-pulumi-version:
	@if test -z "${VERSION}"; then echo "VERSION variable not set. Try 'make set-pulumi-version VERSION=<pulumi version>'"; exit 1; fi
	$(info Setting the Pulumi version to ${VERSION})
	@sed -i 's|pulumi==.*|pulumi==${VERSION}|g'	${SOURCE_DIR}/requirements-common.txt
	@sed -i 's|PULUMI_VERSION=.*|PULUMI_VERSION=\"${VERSION}\"|g'	${SOURCE_DIR}/docker-images/iac-runtime/Dockerfile
	@sed -i 's|\"PULUMI_VERSION\".*|\"PULUMI_VERSION\": \"${VERSION}\"|g'	${PROJECT_ROOT}/.devcontainer/devcontainer.json
	$(info Rebuild the VSCode dev container for the changes to take an effect.)

set-python-version:
	@if test -z "${VERSION}"; then echo "VERSION variable not set. Try 'make set-pulumi-version VERSION=<pulumi version>'"; exit 1; fi
	$(info Setting the Python version to ${VERSION})
	@sed -i 's|\"VARIANT\".*|\"VARIANT\": \"${VERSION}\",|g'	${PROJECT_ROOT}/.devcontainer/devcontainer.json
	@sed -i 's|python:.*|python:${VERSION}|g'	${SOURCE_DIR}/docker-images/iac-runtime/Dockerfile
	$(info Rebuild the VSCode dev container for the changes to take an effect.)


#####################################################################################################################
# API
#####################################################################################################################
setup: setup-cruft-config setup-cruft-project setup-dir-links setup-env-file setup-pulumi-project-configs setup-python-venv show-setup-banner

project-reset: show-reset-banner remove-dev-dir remove-pulumi-project-configs

reset: project-reset remove-venv-dir