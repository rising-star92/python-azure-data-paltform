# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3.9"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# User vscode needs sudoers access to all users without password.
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode

# PULUMI
# Install pulumi as vscode to allow read/write to .pulumi.
ARG PULUMI_VERSION="3.9.1"
RUN cd /tmp && su vscode -c "curl -fsSL https://get.pulumi.com | sh -s -- --silent" \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.bashrc \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.zshrc

# AZURE CLI
RUN apt-get install ca-certificates curl apt-transport-https lsb-release gnupg \
    && curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | \
    tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null \
    && echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" | \
    tee /etc/apt/sources.list.d/azure-cli.list \
    && apt-get update && apt-get install azure-cli

# PIP REQUIREMENTS
# Our pip requirements rarely change, so its best to keep them in the image to make use of the layer caching.
COPY ./src/pulumi/requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
   && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>

# [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1