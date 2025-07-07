import os
from datetime import datetime

def exporteer_naar_txt(gegevens: dict) -> str:
    begrip = gegevens.get("begrip", "")
    definitie = gegevens.get("definitie_gecorrigeerd", "")
    definitie_orig = gegevens.get("definitie_origineel", "")
    metadata = gegevens.get("metadata", {})
    context_dict = gegevens.get("context_dict", {})
    toetsresultaten = gegevens.get("toetsresultaten", {})
    bronnen = gegevens.get("bronnen", [])

    voorbeeld_zinnen = gegevens.get("voorbeeld_zinnen") or []
    praktijkvoorbeelden = gegevens.get("praktijkvoorbeelden") or []
    tegenvoorbeelden = gegevens.get("tegenvoorbeelden") or []
    toelichting = gegevens.get("toelichting") or ""
    synoniemen = gegevens.get("synoniemen") or ""
    voorkeursterm = gegevens.get("voorkeursterm", "")
    antoniemen = gegevens.get("antoniemen") or ""

    tijdstempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    bestandsnaam = f"definitie_{begrip.replace(' ', '_').lower()}_{tijdstempel}.txt"
    pad = os.path.join("exports", bestandsnaam)

    regels = []
    regels.append(f"\U0001F4D8 Begrip: {begrip}\n")
    regels.append(f"\u270F\uFE0F Definitie (gecorrigeerd): {definitie}\n")
    regels.append(f"\U0001F4CE Oorspronkelijke definitie: {definitie_orig}\n")

    regels.append("\U0001F9FE Metadata:")
    regels += [f"- {k}: {v}" for k, v in metadata.items()] or ["- geen"]

    regels.append("\n\U0001F3E9 Contexten:")
    for ctx_type, waarden in context_dict.items():
        lijst = ", ".join(waarden) if waarden else "geen"
        regels.append(f"- {ctx_type.capitalize()}: {lijst}")

    regels.append("\n\U0001F4CA Toetsresultaten:")
    if isinstance(toetsresultaten, list):
        regels += [f"- {r}" for r in toetsresultaten]
    elif isinstance(toetsresultaten, dict):
        regels += [f"- {k}: {v}" for k, v in toetsresultaten.items()]
    else:
        regels.append("- geen")

    regels.append("\n\U0001F4DA Gebruikte bronnen:")
    regels += [f"- {b}" for b in bronnen if b.strip()] or ["- geen"]

    regels.append("\n\U0001F4A1 Toelichting:")
    regels.append(toelichting.strip() or "- geen")

    regels.append("\n\U0001F9E2 Voorbeeldzinnen:")
    regels += [f"- {z.strip()}" for z in voorbeeld_zinnen if z.strip()] or ["- geen"]

    regels.append("\n\U0001F9E2 Praktijkvoorbeelden:")
    regels += [f"- {z.strip()}" for z in praktijkvoorbeelden if z.strip()] or ["- geen"]

    regels.append("\n\U0001F6AB Tegenvoorbeelden:")
    regels += [f"- {z.strip()}" for z in tegenvoorbeelden if z.strip()] or ["- geen"]

    regels.append("\n\U0001F501 Synoniemen:")
    regels += [f"- {s.strip()}" for s in synoniemen.splitlines() if s.strip()] or ["- geen"]

    regels.append("\n🏷️ Voorkeursterm:")
    regels.append(f"- {voorkeursterm or 'geen'}")

    regels.append("\n\U0001F504 Antoniemen:")
    regels += [f"- {a.strip()}" for a in antoniemen.splitlines() if a.strip()] or ["- geen"]

    os.makedirs("exports", exist_ok=True)
    with open(pad, "w", encoding="utf-8") as f:
        f.write("\n".join(regels))

    return pad