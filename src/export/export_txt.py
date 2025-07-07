import os
from datetime import datetime

# ✅ Exportfunctie voor begrijpelijke tekstbestanden (.txt)
# ✅ Geschikt voor export van één begrip (definitie, metadata, toetsresultaten, bronnen)

def exporteer_naar_txt(gegevens: dict, exportpad: str = "exports") -> str:
    """
    ✅ Exporteert alle relevante gegevens van één begrip naar een leesbaar .txt-bestand
    """
    if not os.path.exists(exportpad):
        os.makedirs(exportpad)

    begrip = gegevens.get("begrip", "onbekend")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bestandsnaam = f"{begrip}_{timestamp}.txt"
    pad = os.path.join(exportpad, bestandsnaam)

    regels = []

    # ✅ Begrip en definitie
    regels.append(f"📘 Begrip: {begrip}")
    regels.append(f"✏️ Definitie (gecorrigeerd): {gegevens.get('definitie_gecorrigeerd', '—')}")
    regels.append("")

    # ✅ Toetsresultaten
    regels.append("📊 Toetsresultaten:")
    toetsresultaten = gegevens.get("toetsresultaten", {})
    for toets, resultaat in toetsresultaten.items():
        status = "✅" if resultaat.get("resultaat") else "❌"
        toelichting = resultaat.get("toelichting", "")
        regels.append(f"- {toets}: {status} {toelichting}")
    regels.append("")

    # ✅ Gebruikte bronnen
    regels.append("📚 Gebruikte bronnen:")
    bronnen = gegevens.get("bronnen", [])
    if bronnen:
        for bron in bronnen:
            regels.append(f"- {bron}")
    else:
        regels.append("- Geen")
    regels.append("")

    # ✅ Metadata
    regels.append("🧾 Metadata:")
    metadata = gegevens.get("metadata", {})
    for k, v in metadata.items():
        regels.append(f"- {k}: {v}")
    regels.append("")

    # ✅ Schrijf naar bestand
    with open(pad, "w", encoding="utf-8") as f:
        f.write("\n".join(regels))

    return pad  # ✅ Geeft pad terug voor bevestiging of downloadlink