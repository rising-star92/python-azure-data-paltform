# Azure Data Platform: Infra as Code Runtime

## Overview

The runtime consists of all Python (and other) requirements needed for the infrastructure deployment.

## Usage

> Make sure to always use `make` when building or publishing image versions.  
> The Makefile takes care of all dependencies required by the Docker image.

### Build Image

```shell
make build
```

### Publish Image
```
make publish # to publish 'latest' version
```

```shell
make publish TAG_NAME=1.2.0 # to publish `1.2.0` version
```

### Use Image

```shell
docker pull ingeniisolutions/azure-data-platform-iac-runtime
```

## Why Is This Docker Image Needed

We use this image in our CICD pipelines that drive our client deployments. 
The image dramatically saves time to set up the right environment needed to run the deployments.

## Challenges

### Image Versioning and Rebuilds

At the moment, we release a docker image every time there is:
- new push to any branch -> latest-dev tag
- new push to the main branch -> latest tag
- new release -> release-version tag

This seems a bit inefficient as the Docker image does not change as often as the main platform does.  
However, keeping the docker image version the same as the platform version makes it a lot easier to construct the CICD
pipelines for the customer repos.

At the expense of extra build time, we gain the benefit of simpler CICD pipelines.