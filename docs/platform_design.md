# Ingenii Azure Data Platform Design <!-- omit in toc -->

**Table of Contents**

- [Overview](#overview)
- [Definitions and Acronyms](#definitions-and-acronyms)
- [Architectural Design](#architectural-design)
- [Data Flow](#data-flow)
- [Network Flow](#network-flow)
- [Infrastructure Environments](#infrastructure-environments)
  - [Data Sharing (Shared -> DTAP)](#data-sharing-shared---dtap)
  - [Data Sharing (Same Environment)](#data-sharing-same-environment)
- [Network](#network)
  - [Network Flow](#network-flow-1)
- [Infrastructure As Code](#infrastructure-as-code)
  - [Code Structure](#code-structure)
- [Cloud Costs](#cloud-costs)
  - [Network](#network-1)

## Overview

![Platform Overview](./assets/adp-design-overview.png)

## Definitions and Acronyms

TBD

## Architectural Design

![Platform High Level Architecture](./assets/adp-design-architecture.png)

## Data Flow

## Network Flow

![](assets/adp-design-network-flow.png)

## Infrastructure Environments

![](assets/adp-design-infra-environments.png)

### Data Sharing (Shared -> DTAP)

![](assets/adp-sharing-data-between-environments.png)

### Data Sharing (Same Environment)

![](assets/adp-sharing-data-within-the-same-environment.png)

## Network

### Network Flow

## Infrastructure As Code

### Code Structure

```shell
├── Makefile                  # Helper functions
├── README.md                 # Main README file
├── configs                   # Client specific configs
│   ├── dev.yml               # Development environment-specific configs
│   ├── globals.yml           # Global configs (applying to DTAP/Shared environments)
│   ├── prod.yml              # Production environment-specific configs
│   ├── shared.yml            # Shared environment-specific configs
│   └── test.yml              # Test environment-specific configs
├── docs                      # Platform documentation
│   └── assets                # Documentation assets such as images, files etc
└── src                       # Platform source code
    ├── env                   # All environment configs
    │   ├── dtap              # DTAP environment configs
    │   │   ├── defaults.yml  # Default values for the DTAP environments
    │   │   ├── env.hcl       # Environment (DTAP) specific Terragrunt configs
    │   ├── root.hcl          # Global Terragrunt configs. (DTAP/Shared)
    │   └── shared            # Shared environment configs
    │       ├── defaults.yml  # Default values for the Shared environment
    │       └── env.hcl       # Environment (Shared) specific Terragrunt configs
    ├── modules               # Pure Terraform code
    └── terragrunt.hcl        # Base Terragrunt file
```

## Cloud Costs

### Network

- [Azure Bandwidth Pricing](https://azure.microsoft.com/en-us/pricing/details/bandwidth/)
- [Azure Virtual Network Pricing](https://azure.microsoft.com/en-gb/pricing/details/virtual-network/)
