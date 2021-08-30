# ---------------------------------------------------------------------------------------------------------------------
# PLEASE READ
#
# Please use the accompanying Makefile to build this image. e.g. 'make build'
# Running 'docker build' directly will not work. 
#
# The Makefile makes sure all dependencies are in place for the docker image to be built.
# ---------------------------------------------------------------------------------------------------------------------
FROM python:3.9

ARG PULUMI_VERSION="3.11.0"

# Install Pulumi
RUN cd /tmp && curl -fsSL https://get.pulumi.com | sh -s -- --silent --version ${PULUMI_VERSION}
ENV PATH="/root/.pulumi/bin:${PATH}"

# Install Python Dependencies
COPY tmp /tmp/build

RUN pip install --upgrade pip \
    && cd /tmp/build \ 
    && pip --disable-pip-version-check --no-cache-dir install \
    -r /tmp/build/requirements.txt \
    && rm -rf /tmp/build