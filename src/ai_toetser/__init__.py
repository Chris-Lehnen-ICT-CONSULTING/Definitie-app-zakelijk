"""
ai_toetser package

Publieke API:
    Toetser         – OO-wrapper met `.is_verboden()`
    toets_definitie – functiebasis voor definitie-toetsing

The package now uses a modular architecture but maintains backward compatibility.
The old monolithic core.py is still available, but the new modular_toetser.py
provides the same API with better maintainability.
"""

from .toetser import Toetser  # noqa: F401

# Import from new modular architecture while maintaining compatibility
try:
    from .modular_toetser import toets_definitie, ModularToetser  # noqa: F401
except ImportError:
    # Fallback to old implementation if modular version fails
    from .core import toets_definitie  # noqa: F401
    ModularToetser = None

__all__ = ["Toetser", "toets_definitie", "ModularToetser"]
