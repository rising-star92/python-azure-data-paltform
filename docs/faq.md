# Frequently Asked Questions <!-- omit in toc -->

- [Security](#security)
  - [Is the data encrypted at rest?](#is-the-data-encrypted-at-rest)
  - [Is the data encrypted in transit?](#is-the-data-encrypted-in-transit)
  - [Are VPNs required to connect ot the platform?](#are-vpns-required-to-connect-ot-the-platform)
  - [What are the security settings of the platform?](#what-are-the-security-settings-of-the-platform)
  - [Is access to the data monitored?](#is-access-to-the-data-monitored)
  - [Is our data safe from outside access and/or other customers?](#is-our-data-safe-from-outside-access-andor-other-customers)
- [Authentication and Permissions](#authentication-and-permissions)
  - [How do users or administrators authenticate?](#how-do-users-or-administrators-authenticate)
  - [Is Multifactor Authentication enabled?](#is-multifactor-authentication-enabled)
  - [How is access controlled to the environment?](#how-is-access-controlled-to-the-environment)
  - [How are permissions managed in the platform?](#how-are-permissions-managed-in-the-platform)
  - [Our Azure AD is not really used, we federate from on-premise AD. How do we work with the prerequisites?](#our-azure-ad-is-not-really-used-we-federate-from-on-premise-ad-how-do-we-work-with-the-prerequisites)
  - [How do you manage access credentials? Are they rotated frequently?](#how-do-you-manage-access-credentials-are-they-rotated-frequently)
- [Deployment](#deployment)
  - [Can the Azure deployment be run in a separate tenant from our Azure AD?](#can-the-azure-deployment-be-run-in-a-separate-tenant-from-our-azure-ad)
- [Support](#support)
  - [We have a third party providing support for our cloud environments, what would they be responsible for?](#we-have-a-third-party-providing-support-for-our-cloud-environments-what-would-they-be-responsible-for)

## Security

---

### Is the data encrypted at rest?

- Yes, all data stored via the Ingenii Platform is encrypted at rest.

### Is the data encrypted in transit?

- Yes. Data traversing within platform is not leaving the customer isolated network.
- Data leaving the platform is only possible via secure protocols such as HTTPS/TLS.

### Are VPNs required to connect ot the platform?

- No. VPNs are not necessary or recommended. All user access is protected by standard Microsoft authentication mechanisms used in services such as Office 365.
- All access to the platform is possible only via secure protocols such as HTTPS/TLS.

### What are the security settings of the platform?

TODO

### Is access to the data monitored?

TODO

### Is our data safe from outside access and/or other customers?

- Your data is your data. No other customers have access to it.
- Our deployment of the platform is done in a sandboxed container (subscription/account) that only YOU have access to.

## Authentication and Permissions

---

### How do users or administrators authenticate?

- All users (admins included) are authenticated via Azure Active Directory (AAD).

### Is Multifactor Authentication enabled?

- MFA can be enabled via Azure Active Directory.

### How is access controlled to the environment?

- Access is controlled via Roles (RBAC).
- Additionally, we recommend our customers to make use of Azure Conditional Access policies to further control how is access granted.

### How are permissions managed in the platform?

- Permissions are granted using Role Based Access control.

### Our Azure AD is not really used, we federate from on-premise AD. How do we work with the prerequisites?

- We do require cloud identities to be synced from on-premise AD to Azure AD in order for Role Based Access Control to work.
- Alternatively, separate cloud identities can be created for the platform access.

### How do you manage access credentials? Are they rotated frequently?

- We do not manage access credentials to the platform. All authentication is handled by Azure AD and follow your password rotation policy.

## Deployment

---

### Can the Azure deployment be run in a separate tenant from our Azure AD?

- No. At present, we only support deployments in the same AAD tenant.
- The Azure Ingenii Data Platform is deployed in separate subscriptions and that is sufficient for the separation of environments.

## Support

---

### We have a third party providing support for our cloud environments, what would they be responsible for?

See the [Requirements](./docs/platform_requirements.md) for the prerequisities that are required from a third party outsourced support or managed service provider (MSP). As a summary the support that the third party would have to provide is:

- General vendor management of Microsoft for any escalations
- Ensuring the [Requirements](./docs/platform_requirements.md) for the prerequisities are available on an ongoing basis
- Troubleshooting any issues with the prerequisities such as:
  - Subscription
  - Azure Principals and Azure AD permissions
