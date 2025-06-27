from ai_toetser.core import toets_VER_03

# fout: vervoegd
assert toets_VER_03("beoordeelt", regel_VER_03).startswith("❌ VER-03")
# goed: infinitief
assert toets_VER_03("beoordelen", regel_VER_03).startswith("✔️ VER-03")
# grootste fallback
assert toets_VER_03("toezicht houden", regel_VER_03).startswith("✔️ VER-03")
