# Init the platform outputs
from project_config import platform_outputs

platform_outputs["analytics"] = {}

# Load sub-modules
from . import shared_kubernetes_cluster
