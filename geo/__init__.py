import os
import sys

# Extend geo package path so that both legacy flat imports (`from geo.boundary_service import ...`)
# and new modular imports (`from geo.services.boundary_service import ...`) work seamlessly.
_base_dir = os.path.dirname(__file__)
for sub in ["services", "analysis", "layers", "boundaries"]:
    sub_path = os.path.join(_base_dir, sub)
    if os.path.exists(sub_path) and sub_path not in __path__:
        __path__.append(sub_path)
