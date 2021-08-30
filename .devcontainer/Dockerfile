# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3.9"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# User vscode needs sudoers access to all users without password.
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode

# Python Packages
# Make sure pip operations are done in venv with correct file permissions so vscode can use it later, then
# update pip, install both app and pulumi requirements.
COPY ./src/requirements*.txt /tmp/pip-tmp/
# Doing this as vscode to load as many libraries in the base Docker image. Default pip install dir for vscode
# will be under /home/vscode/.local/
RUN pip install --upgrade pip \
    && sudo -u vscode pip --disable-pip-version-check --no-cache-dir install \
    -r /tmp/pip-tmp/requirements-common.txt \
    && rm -rf /tmp/pip-tmp

# Pulumi
# Install pulumi as vscode to allow read/write to .pulumi.
ARG PULUMI_VERSION="3.9.1"
RUN cd /tmp && su vscode -c "curl -fsSL https://get.pulumi.com | sh -s -- --silent" \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.bashrc \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.zshrc

# Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash