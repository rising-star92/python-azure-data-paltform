# Init the platform outputs
from project_config import platform_outputs

platform_outputs["storage"] = {}

from . import databricks
from . import datalake

storage_accounts = {
    "databricks": databricks.databricks_storage_account_details,
    "datalake": datalake.datalake_details,
}
