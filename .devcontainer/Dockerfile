# Python Version
ARG VARIANT="3.10"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# User vscode needs sudoers access to all users without password.
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode

# Essential Python Packages
RUN su vscode -c "pip install --disable-pip-version-check --no-cache-dir --upgrade \ 
    pip \
    cruft \
    azure-cli"

# Pulumi
# Install pulumi as vscode to allow read/write to .pulumi.
ARG PULUMI_VERSION="3.17.1"
RUN cd /tmp && su vscode -c "curl -fsSL https://get.pulumi.com | sh -s -- --silent" \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.bashrc \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.zshrc