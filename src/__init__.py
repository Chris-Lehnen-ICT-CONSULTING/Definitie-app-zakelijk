"""
DefinitieAgent source package.

Main source package voor alle DefinitieAgent modules.
Configureert Python path voor correcte import resolutie.
"""

import sys
import os

# Voeg root directory toe aan Python path voor toegang tot logs module
# Dit zorgt ervoor dat imports van logs.application.log_definitie werken
_root_dir = os.path.dirname(os.path.dirname(__file__))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)