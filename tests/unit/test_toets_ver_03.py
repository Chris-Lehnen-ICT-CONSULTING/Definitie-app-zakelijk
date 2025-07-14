from ai_toetser.core import toets_VER_03
from config.config_loader import laad_toetsregels

toetsregels = laad_toetsregels()
regel_VER_03 = next(r for r in toetsregels if r["id"] == "VER-03")

# fout: vervoegd
assert toets_VER_03("beoordeelt", regel_VER_03).startswith("❌ VER-03")
# goed: infinitief
assert toets_VER_03("beoordelen", regel_VER_03).startswith("✔️ VER-03")
# grootste fallback
assert toets_VER_03("toezicht houden", regel_VER_03).startswith("✔️ VER-03")
