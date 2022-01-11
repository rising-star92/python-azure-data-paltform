# Init the platform outputs
from project_config import platform_outputs

platform_outputs["analytics"]["datafactory"] = {"factories": {}}

from . import datafactories
from . import integrated_integration_runtime
from . import orchestration
from . import orchestration_linked_services
from . import orchestration_datasets
from . import orchestration_pipelines
