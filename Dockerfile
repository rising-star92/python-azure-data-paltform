ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

ARG PULUMI_VERSION=3.20.0

# User vscode needs sudoers access to all users without password.
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode
ENV PATH="/home/vscode/.local/bin:${PATH}"

USER vscode

# Pulumi
# Install pulumi as vscode to allow read/write to .pulumi.
RUN cd /tmp && curl -fsSL https://get.pulumi.com | sh -s -- --silent \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.bashrc \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.zshrc
ENV PATH="/home/vscode/.pulumi/bin:${PATH}"

# Pulumi Plugins (Temporary, until we migrate away from v0.0.6)
RUN /home/vscode/.pulumi/bin/pulumi plugin install resource databricks 0.0.6 --server https://github.com/ingenii-solutions/pulumi-databricks/releases/download/v0.0.6
RUN /home/vscode/.pulumi/bin/pulumi plugin install resource databricks 0.0.8 --server https://github.com/ingenii-solutions/pulumi-databricks/releases/download/v0.0.8

# Copy the platform source code to the container
COPY --chown=vscode:vscode src /platform/src

# Install all platform Python packages
RUN cd /platform/src && pip install -r requirements.txt