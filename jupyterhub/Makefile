# include .env
# export

$(eval INGENII_AZURE_QUANTUM_VERSION=$(shell grep '^Ingenii Azure Quantum Version:' README.md | awk -F ':' '{print $$2}' | sed 's/ //g'))
$(eval SINGLEUSER_VERSION=$(shell grep '^JupyterHub Single User Image Version:' README.md | awk -F ':' '{print $$2}' | sed 's/ //g'))

# Docker

SINGLEUSER_IMAGE_NAME=ingeniisolutions/jupyterhub-singleuser

build-singleuser-image:
	docker build . \
		--build-arg IMAGE_VERSION=$(SINGLEUSER_VERSION) \
		--build-arg PACKAGE_VERSION=$(INGENII_AZURE_QUANTUM_VERSION) \
		-f docker/jupyterhub-singleuser.Dockerfile \
		-t ${SINGLEUSER_IMAGE_NAME}:${SINGLEUSER_VERSION}

push-singleuser-image:
	docker push ${SINGLEUSER_IMAGE_NAME}:${SINGLEUSER_VERSION}
