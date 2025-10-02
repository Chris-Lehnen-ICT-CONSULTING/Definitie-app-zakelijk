"""UI Components package voor DefinitieAgent.

Bevat herbruikbare Streamlit componenten. Deze module exporteert een
lichte aggregator-klasse voor backwards compatibiliteit met tests die
``from ui.components import UIComponents`` verwachten.
"""


class UIComponents:  # Backwards-compatibele aggregator
    """Placeholder/aggregator voor UI componenten.

    In de huidige architectuur worden componenten direct uit de
    submodules geïmporteerd. Deze klasse bestaat voor testcompatibiliteit
    en kan later uitgebreid worden met helpers.
    """


__all__ = ["UIComponents"]
