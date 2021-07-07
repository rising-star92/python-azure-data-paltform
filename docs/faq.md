# Frequently Asked Questions

## Are VPNs required to connect to the data platform?

VPNs are neither a necessity nor recommended to work with the Ingenii Data Platform.

## Our Azure AD is not really used, we federate from on-premise AD. How do we work with the prerequisites?

TODO

## Can the Azure deployment be run in a separate tennat?

Yes it could, but it is not our recommended set up. The Azure Ingenii Data Platform is deployed in separate subscriptions and that is sufficient for the separation of environments.

## We have a third party providing support for our cloud environments, what would they be responsible for?

See the [Requirements](./docs/platform_requirements.md) for the prerequisities that are required from a third party outsourced support or managed service provider (MSP). As a summary the support that the third party would have to provide is:
* General vendor management of Microsoft for any escalations
* Ensuring the [Requirements](./docs/platform_requirements.md) for the prerequisities are available on an ongoing basis
* Troubleshooting any issues with the prerequisities such as:
  * Subscription
  * Azure Principals and Azure AD permissions

## What are the security settings of the platform?

TODO

