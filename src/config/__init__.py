"""Configuration module voor DefinitieAgent."""

# Import legacy config functionaliteit
from .config_loader import laad_toetsregels, laad_verboden_woorden

# Export voor backward compatibility
__all__ = ["laad_toetsregels", "laad_verboden_woorden"]
