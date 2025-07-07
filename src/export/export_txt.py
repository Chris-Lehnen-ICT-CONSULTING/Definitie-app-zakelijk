import os
from datetime import datetime

def exporteer_naar_txt(gegevens: dict) -> str:
    """
    Exporteert de definitie en contextuele gegevens naar een TXT-bestand.
    Alle velden worden netjes weergegeven in tekstformaat.
    """

    begrip = gegevens.get("begrip", "")
    definitie = gegevens.get("definitie_gecorrigeerd", "")
    definitie_orig = gegevens.get("definitie_origineel", "")
    metadata = gegevens.get("metadata", {})
    context_dict = gegevens.get("context_dict", {})
    toetsresultaten = gegevens.get("toetsresultaten", {})
    bronnen = gegevens.get("bronnen", [])

    tijdstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    bestandsnaam = f"_definitie_export_{tijdstempel}.txt"
    pad = os.path.join("log", bestandsnaam)

    regels = []
    regels.append(f"📘 Begrip: {begrip}")
    regels.append(f"\n✏️ Definitie (gecorrigeerd): {definitie}")
    regels.append(f"\n📎 Oorspronkelijke definitie: {definitie_orig}")

    # Metadata tonen
    regels.append("\n🧾 Metadata:")
    for sleutel, waarde in metadata.items():
        regels.append(f"- {sleutel}: {waarde}")

    # Contexten
    regels.append("\n🏛️ Contexten:")
    for ctx_type, ctx_waarden in context_dict.items():
        waarden = ", ".join(ctx_waarden) if ctx_waarden else "geen"
        regels.append(f"- {ctx_type.capitalize()}: {waarden}")

    # Toetsresultaten
    regels.append("\n📊 Toetsresultaten:")
    if toetsresultaten:
        if isinstance(toetsresultaten, dict):
            for k, v in toetsresultaten.items():
                regels.append(f"- {k}: {v}")
        elif isinstance(toetsresultaten, list):
            for regel in toetsresultaten:
                regels.append(f"- {regel}")
    else:
        regels.append("- Geen toetsresultaten beschikbaar.")

    # Bronnen
    regels.append("\n📚 Gebruikte bronnen:")
    if bronnen:
        for bron in bronnen:
            regels.append(f"- {bron}")
    else:
        regels.append("- Geen")

    # Schrijven naar bestand
    os.makedirs("log", exist_ok=True)
    with open(pad, "w", encoding="utf-8") as f:
        f.write("\n".join(regels))

    return pad