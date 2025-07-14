import os  # Operating system interface voor bestandsoperaties
from datetime import datetime  # Datum en tijd functionaliteit voor timestamps

def exporteer_naar_txt(gegevens: dict) -> str:
    """Exporteert definitie gegevens naar een geformatteerd TXT bestand."""
    # Haal alle benodigde gegevens op uit de data dictionary
    begrip = gegevens.get("begrip", "")  # Het gedefinieerde begrip
    definitie = gegevens.get("definitie_gecorrigeerd", "")  # Finale gecorrigeerde definitie
    definitie_orig = gegevens.get("definitie_origineel", "")  # Oorspronkelijke AI-gegenereerde definitie
    metadata = gegevens.get("metadata", {})  # Extra metadata informatie
    context_dict = gegevens.get("context_dict", {})  # Context categorieën en waarden
    toetsresultaten = gegevens.get("toetsresultaten", {})  # Resultaten van kwaliteitstoetsen
    bronnen = gegevens.get("bronnen", [])  # Gebruikte bronnen voor de definitie

    # Haal optionele voorbeelden en aanvullende informatie op
    voorbeeld_zinnen = gegevens.get("voorbeeld_zinnen") or []  # Voorbeeldzinnen met het begrip
    praktijkvoorbeelden = gegevens.get("praktijkvoorbeelden") or []  # Praktische gebruiksvoorbeelden
    tegenvoorbeelden = gegevens.get("tegenvoorbeelden") or []  # Tegenvoorbeelden ter verduidelijking
    toelichting = gegevens.get("toelichting") or ""  # Uitgebreide toelichting
    synoniemen = gegevens.get("synoniemen") or ""  # Synoniemen van het begrip
    voorkeursterm = gegevens.get("voorkeursterm", "")  # Voorkeursterm indien anders
    antoniemen = gegevens.get("antoniemen") or ""  # Antoniemen van het begrip

    # Genereer unieke bestandsnaam met timestamp
    tijdstempel = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    bestandsnaam = f"definitie_{begrip.replace(' ', '_').lower()}_{tijdstempel}.txt"  # Normaliseer begrip voor bestandsnaam
    pad = os.path.join("exports", bestandsnaam)  # Volledig pad naar export bestand

    regels = []
    regels.append(f"\U0001F4D8 Begrip: {begrip}\n")
    regels.append(f"\u270F\uFE0F Definitie (gecorrigeerd): {definitie}\n")
    regels.append(f"\U0001F4CE Oorspronkelijke definitie: {definitie_orig}\n")

    regels.append("\U0001F9FE Metadata:")
    for k, v in metadata.items():
        if k == "ketenpartners" and isinstance(v, list):
            regels.append(f"- {k}: {', '.join(v) if v else 'geen'}")
        elif k == "datum_voorstel" and v:
            regels.append(f"- {k}: {v.strftime('%d-%m-%Y') if hasattr(v, 'strftime') else str(v)}")
        elif v:
            regels.append(f"- {k}: {v}")
        else:
            regels.append(f"- {k}: geen")

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