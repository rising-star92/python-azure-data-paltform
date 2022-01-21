# Init the platform outputs
from project_config import platform_outputs

platform_outputs["analytics"] = {"datafactory": {}}

# Load sub-modules
from . import datafactory_repositories
from . import datafactory_shared
from . import shared_kubernetes_cluster
