# Solution Security

## Exposed Services

All of the Ingenii Data Engineering deployed resources are available through your cloud platform portal. The top level security 

Azure Data Platform exposes the following additional end points:

* Databricks Workspaces - accessible via a web interface, each workspace will have its own URL and access to which 
* Azure Data Factory
* Data Lake - DataBricks connects via private link, but ADF goes via a public link (Microsoft limitation, until it the ADF private links)
  * Trusted Services 
* Azure DevOps - own URL


## User Accounts

All user controls are done through Azure AD and role assignments. There are three roles that the Azure Data Platform solution requires:

| role | usage |
| --- | --- |
| admin | overall admin rights to all of the platform |
| engineer | who will be managing the data connectors, pipelines and storage |
| analyst | who will effectively be working with the anlytics workspaces, tools and notebooks |

You can assign any Azure AD user to one or more of these roles. 


## Service Accounts

<TO DO>

## Data Movement

<TO DO>
