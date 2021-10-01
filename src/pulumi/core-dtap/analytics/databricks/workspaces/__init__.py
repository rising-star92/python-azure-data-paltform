# Init the platform outputs
from project_config import platform_outputs

platform_outputs["analytics"]["databricks"]["workspaces"] = {}

from . import engineering
from . import analytics
