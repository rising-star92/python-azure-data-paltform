ARG BASE_IMAGE
FROM ${BASE_IMAGE}

RUN pip install azure-cli

COPY ingenii_azure_quantum-0.1.0-py3-none-any.whl /tmp/
RUN pip install /tmp/ingenii_azure_quantum-0.1.0-py3-none-any.whl
