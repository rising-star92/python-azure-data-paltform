"""
This script is used to parse and upload specific Pulumi outputs to an Azure
table that will be read and processed by the Ingenii UI.
"""
import argparse
import json
from typing import Dict, Any

from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceNotFoundError

parser = argparse.ArgumentParser(
    description="Utility tool that helps to parse out certain output values from the Pulumi stack outputs and then push them to Azure table storage."
)

parser.add_argument(
    "--outputs-file",
    type=str,
    nargs="?",
    help="A JSON formatted file that contains the data platform pulumi outputs.",
    required=True,
)

parser.add_argument(
    "--connection-string",
    type=str,
    nargs="?",
    help="The connection string of the Azure storage account.",
    required=True,
)

parser.add_argument(
    "--table-name",
    type=str,
    nargs="?",
    help="The name of the table in the Azure storage account.",
    required=True,
)

parser.add_argument(
    "--env-name",
    type=str,
    nargs="?",
    help="The name of the platform environment. (dev, test, prod or shared)",
    required=True,
)

args = parser.parse_args()


class OutputExporter:
    def __init__(self, connection_string: str, table_name: str):
        table_service = TableServiceClient.from_connection_string(connection_string)
        self._client = table_service.get_table_client(table_name)

    def _parse_outputs(self, file: str, env_name: str) -> Dict[Any, Any]:
        with open(file, "r") as f:
            outputs = json.loads(f.read())["root"]

        parsed = {
            "org_id": outputs["metadata"]["org_id"],
            "project_id": outputs["metadata"]["project_id"],
            "payload": {},
        }

        payload = parsed["payload"]

        if env_name in ["dev", "test", "prod"]:
            databricks = outputs["analytics"]["databricks"]["workspaces"]
            datafactory = outputs["analytics"]["datafactory"]["factories"]
            datalake = outputs["storage"]["datalake"]
            dbt = outputs["analytics"]["dbt"]["documentation"]

            payload[env_name] = {
                "databricks_eng_workspace_url": databricks["engineering"].get("url"),
                "databricks_atc_workspace_url": databricks["analytics"].get("url"),
                "datafactory_data_studio_url": datafactory["data"].get("url"),
                "datalake_containers_view_url": datalake.get("containers_view_url"),
                "dbt_docs_url": dbt.get("url"),
            }
        elif env_name == "shared":
            payload[env_name] = {
                "devops_project_url": outputs["devops"]["project"].get("url")
            }

        return parsed

    def save(self, outputs_file: str, env_name: str) -> None:
        parsed = self._parse_outputs(outputs_file, env_name)

        new_entity = {
            "PartitionKey": parsed["org_id"],
            "RowKey": parsed["project_id"],
            "payload": parsed["payload"],
        }

        # If there is an existing record (row) in Azure Table storage,
        # let's pull it in and merge our outputs to it.
        try:
            existing_entity = self._client.get_entity(
                new_entity["PartitionKey"], new_entity["RowKey"]
            )

            existing_payload = json.loads(existing_entity["payload"])

            # Merge the new payload (urls) with whatever is already existing on the Azure table storage.
            # The new payload will overwrite existing data.
            new_entity["payload"] = existing_payload | new_entity["payload"]
        except ResourceNotFoundError:
            # The table row has not been found, but that's ok.
            # We'll upsert the payload which will result in the row being created.
            pass
        except KeyError:
            # A KeyError can be generated if the "payload" column is empty or does not exist for that row.
            # We can safely ignore the error and let the upsert function create a new row.
            pass

        new_entity["payload"] = json.dumps(new_entity["payload"])

        # Write to Azure table storage
        self._client.upsert_entity(new_entity)


# Main
exporter = OutputExporter(args.connection_string, args.table_name)
exporter.save(args.outputs_file, str(args.env_name).lower())
