ARG IMAGE_VERSION
FROM jupyterhub/k8s-singleuser-sample:${IMAGE_VERSION}

RUN pip install azure-cli

ARG PACKAGE_VERSION

COPY files/ingenii_azure_quantum-${PACKAGE_VERSION}-py3-none-any.whl /packages/
RUN pip install /packages/ingenii_azure_quantum-${PACKAGE_VERSION}-py3-none-any.whl
