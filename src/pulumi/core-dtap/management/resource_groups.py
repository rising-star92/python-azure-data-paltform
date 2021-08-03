from pulumi import resource
import pulumi_azure_native as azure_native
from config import platform as p

# ----------------------------------------------------------------------------------------------------------------------
# INFRA RESOURCE GROUP
# ----------------------------------------------------------------------------------------------------------------------
infra_name = p.generate_name("resource_group", "infra")
infra = azure_native.resources.ResourceGroup(
    resource_name=infra_name,
    resource_group_name=infra_name,
    location=p.region_long_name,
    tags=p.tags,
)

# ----------------------------------------------------------------------------------------------------------------------
# DATA RESOURCE GROUP
# ----------------------------------------------------------------------------------------------------------------------
data_name = p.generate_name("resource_group", "data")
data = azure_native.resources.ResourceGroup(
    resource_name=data_name,
    resource_group_name=data_name,
    location=p.region_long_name,
    tags=p.tags,
)

# ----------------------------------------------------------------------------------------------------------------------
# SECURITY RESOURCE GROUP
# ----------------------------------------------------------------------------------------------------------------------
security_name = p.generate_name("resource_group", "security")
security = azure_native.resources.ResourceGroup(
    resource_name=security_name,
    resource_group_name=security_name,
    location=p.region_long_name,
    tags=p.tags,
)
