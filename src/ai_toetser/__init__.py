# ✅ maakt het pakket importeerbaar
# ✅ maakt het pakket importeerbaar
from .core import laad_toetsregels, toets_definitie  # noqa: F401
# 💚 Exporteert publieksfuncties
# ↪︎ Compat: korte import voor tests
from .core import Toetser  # noqa: F401
