ARG VARIANT="hirsute"
FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}

ARG PYTHON_VERSION=3.10.1
ARG PULUMI_VERSION=3.20.0

# User vscode needs sudoers access to all users without password.
RUN echo "vscode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/vscode
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Install Python
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends build-essential \ 
    zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev \
    libffi-dev libsqlite3-dev wget libbz2-dev \
    && wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \
    && tar -xf Python-${PYTHON_VERSION}.tgz \
    && cd Python-${PYTHON_VERSION} \
    && ./configure --enable-optimizations \
    && make -j $(nproc) \
    && make install \
    && ln -s /usr/local/bin/python3 /usr/local/bin/python \
    && ln -s /usr/local/bin/pip3 /usr/local/bin/pip \
    && cd .. \ 
    && rm -rf Python-${PYTHON_VERSION}*

# Essential Python Packages
RUN su vscode -c "pip install --disable-pip-version-check --no-cache-dir --upgrade \ 
    pip \
    cruft \
    azure-cli"

# Pulumi
# Install pulumi as vscode to allow read/write to .pulumi.
RUN cd /tmp && su vscode -c "curl -fsSL https://get.pulumi.com | sh -s -- --silent" \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.bashrc \
    && echo "export PULUMI_SKIP_UPDATE_CHECK=false" >> /home/vscode/.zshrc
ENV PATH="/home/vscode/.pulumi/bin:${PATH}"

# Pulumi Plugins (Temporary, until we migrate away from v0.0.6)
RUN su vscode -c "/home/vscode/.pulumi/bin/pulumi plugin install resource databricks 0.0.6 --server https://github.com/ingenii-solutions/pulumi-databricks/releases/download/v0.0.6"

# Copy the platform source code to the container
COPY --chown=vscode:vscode src /platform/src

# Install all platform Python packages
RUN cd /platform/src && pip install -r requirements.txt

USER vscode