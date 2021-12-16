# Init the platform outputs
from project_config import platform_outputs

platform_outputs["analytics"]["datafactory"] = {"factories": {}}

from . import integrated_integration_runtime
from . import orchestration
