"""
ai_toetser package

Publieke API:
    Toetser         – OO-wrapper met `.is_verboden()`
    toets_definitie – functiebasis voor definitie-toetsing
"""

from .toetser import Toetser  # noqa: F401
from .core import toets_definitie  # noqa: F401

__all__ = ["Toetser", "toets_definitie"]
