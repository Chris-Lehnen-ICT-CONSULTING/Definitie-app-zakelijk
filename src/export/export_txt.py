import os  # Operating system interface voor bestandsoperaties
from datetime import UTC, datetime  # Datum en tijd functionaliteit voor timestamps
from typing import Any

from domain.int01.opslag import exportregels

#: Leesbare namen van de drie CON-02-onderdelen (kerncontract C §2).
_ONDERDEELNAMEN = {
    "source_authority": "brongezag/toepasselijkheid",
    "semantic_support": "betekenissteun",
    "reference_quality": "verwijskwaliteit",
}
_STATUSNAMEN = {
    "pass": "voldoet",
    "fail": "voldoet niet",
    "review_required": "nog te beoordelen",
    "error": "technische fout",
}
_BEWIJSSTATUS = {
    "present": "bronbewijs aanwezig",
    "reference_only": "alleen korte bronverwijzing: onvolledig bewijs",
    "absent": "geen bronbewijs opgeslagen",
    "invalid": "opgeslagen bronbewijs is misvormd (ongeldig)",
}
_REVIEWTYPEN = {
    "reference_exception": "verwijzingsuitzondering (bron zonder bruikbare hyperlink)",
    "no_appropriate_source": "uitzondering: geen passende bron na gedocumenteerd zoeken",
    "part_correction": "correctie van één AI-onderdeel door de deskundige",
}


def _tekst(waarde: Any) -> str:
    return str(waarde).strip() if waarde is not None else ""


def _statusregels(bronbewijs: dict[str, Any], status: str) -> list[str]:
    """Bewijsstatus, actualiteit, korte verwijzing en peildatum."""
    regels: list[str] = []
    regels.append(f"- Status: {_BEWIJSSTATUS.get(status, status)}")
    if status == "present":
        actueel = bronbewijs.get("current")
        if actueel:
            regels.append("- Actualiteit: bewijs hoort bij de actuele tekst en context")
        else:
            reden = _tekst(bronbewijs.get("reason"))
            regels.append(
                "- Actualiteit: NIET ACTUEEL (historisch bewijs)"
                + (f" — {reden}" if reden else "")
            )
    if bronbewijs.get("source_reference"):
        regels.append(f"- Korte verwijzing: {bronbewijs['source_reference']}")
    if bronbewijs.get("peildatum"):
        regels.append(f"- Peildatum: {bronbewijs['peildatum']}")
    return regels


def _bronregel(nr: int, bron: dict[str, Any]) -> list[str]:
    """Eén aangeleverde bron: kop met details, passage en coördinaten."""
    regels: list[str] = []
    titel = _tekst(bron.get("title") or bron.get("filename")) or "onbekende bron"
    kop = f"  {nr}. {titel}"
    details = []
    if bron.get("provider"):
        details.append(f"route {bron['provider']}")
    if bron.get("citation_label"):
        details.append(f"vindplaats {bron['citation_label']}")
    if bron.get("url"):
        details.append(str(bron["url"]))
    if bron.get("used_in_prompt") is not None:
        details.append(
            "gebruikt in prompt" if bron.get("used_in_prompt") else "niet in prompt"
        )
    if bron.get("omitted_reason"):
        details.append(f"weggelaten: {bron['omitted_reason']}")
    if details:
        kop += " (" + "; ".join(details) + ")"
    regels.append(kop)
    passage = _tekst(bron.get("prompt_content") or bron.get("snippet"))
    if passage:
        regels.append(f"     passage: {passage}")
    coords = (bron.get("metadata") or {}).get("coordinates")
    if isinstance(coords, dict) and coords:
        regels.append(
            "     coördinaten: " + ", ".join(f"{k}={v}" for k, v in coords.items())
        )
    return regels


def _bronregels(bronbewijs: dict[str, Any]) -> list[str]:
    """De aangeleverde bronnen (alleen dict-records), genummerd."""
    regels: list[str] = []
    bronnen = [b for b in (bronbewijs.get("sources") or []) if isinstance(b, dict)]
    if bronnen:
        regels.append("- Aangeleverde bronnen:")
        for nr, bron in enumerate(bronnen, start=1):
            regels.extend(_bronregel(nr, bron))
    return regels


def _replay_deelregels(deel: dict[str, Any]) -> list[str]:
    """Eén onderdeel van de actuele CON-02-uitkomst (replay)."""
    regels: list[str] = []
    naam = _ONDERDEELNAMEN.get(_tekst(deel.get("id")), _tekst(deel.get("id")))
    oordeel = _STATUSNAMEN.get(
        _tekst(deel.get("status")), _tekst(deel.get("status")) or "onbekend"
    )
    herkomst = _tekst(deel.get("field"))
    regels.append(
        f"  * {naam}: {oordeel}"
        + (f" (basis: {herkomst})" if herkomst else " (geen basis)")
    )
    if _tekst(deel.get("reason")):
        regels.append(f"     reden: {deel['reason']}")
    if _tekst(deel.get("evidence")):
        regels.append(f"     bewijs: {deel['evidence']}")
    return regels


def _replay_reviewregels(
    con02: dict[str, Any], toepasbaarheid: dict[str, Any]
) -> list[str]:
    """Toepasbaarheid van de AI-beoordeling, geaccepteerde uitzondering, correctie."""
    regels: list[str] = []
    samenvatting = (con02.get("review") or {}).get("assessment") or {}
    if samenvatting.get("applied") is not True:
        regels.append(
            "  AI-beoordeling niet toepasbaar op dit record: "
            f"{_tekst(samenvatting.get('reason')) or _tekst(toepasbaarheid.get('reason')) or 'onbekende reden'}"
        )
    review_sv = con02.get("review") or {}
    if review_sv.get("accepted_exception"):
        regels.append(
            f"  geaccepteerde uitzondering: {review_sv['accepted_exception']} "
            "(blijft uitzondering, geen gewone pass)"
        )
    correctie = review_sv.get("applied_correction")
    if isinstance(correctie, dict):
        origineel = correctie.get("original") or {}
        naam = _ONDERDEELNAMEN.get(
            _tekst(correctie.get("part_id")), _tekst(correctie.get("part_id"))
        )
        regels.append(
            f"  toegepaste deskundige correctie: {naam} → "
            f"{_STATUSNAMEN.get(_tekst(correctie.get('status')), _tekst(correctie.get('status')))} "
            f"door {_tekst(correctie.get('actor')) or 'onbekend'}; oorspronkelijk "
            f"AI-oordeel: {_STATUSNAMEN.get(_tekst(origineel.get('status')), _tekst(origineel.get('status')) or 'onbekend')}"
        )
    return regels


def _replayregels(
    bronbewijs: dict[str, Any], status: str, toepasbaarheid: dict[str, Any]
) -> list[str]:
    """Actuele CON-02-uitkomst: de kernreplay bindt beoordeling en uitzondering
    aan precies dit record. Dit is het enige "huidige" oordeel; de ruwe
    opgeslagen beoordeling daarna is bewijs, geen actuele uitkomst."""
    regels: list[str] = []
    con02 = bronbewijs.get("con02")
    if isinstance(con02, dict):
        regels.append(
            "- Actuele CON-02-uitkomst (replay op dit record): "
            f"{_STATUSNAMEN.get(_tekst(con02.get('status')), _tekst(con02.get('status')) or 'onbekend')}"
        )
        for deel in con02.get("parts") or []:
            if not isinstance(deel, dict):
                continue
            regels.extend(_replay_deelregels(deel))
        regels.extend(_replay_reviewregels(con02, toepasbaarheid))
    elif status == "present":
        regels.append(
            "- Actuele CON-02-uitkomst: niet bepaald — "
            f"{_tekst(toepasbaarheid.get('reason')) or 'geen replay beschikbaar'}"
        )
    return regels


def _beoordeling_deelregels(onderdeel: Any, deel: dict[str, Any]) -> list[str]:
    """Eén onderdeel van de opgeslagen AI-bronbeoordeling met citaten en onzekerheid."""
    regels: list[str] = []
    naam = _ONDERDEELNAMEN.get(str(onderdeel), str(onderdeel))
    oordeel = _STATUSNAMEN.get(
        _tekst(deel.get("status")), _tekst(deel.get("status")) or "onbekend"
    )
    regels.append(f"  * {naam}: {oordeel}")
    if _tekst(deel.get("reason")):
        regels.append(f"     reden: {deel['reason']}")
    for bewijs in deel.get("evidence") or []:
        if isinstance(bewijs, dict) and _tekst(bewijs.get("quote")):
            vindplaats = _tekst(bewijs.get("locator"))
            regels.append(
                f"     citaat [{_tekst(bewijs.get('source_id'))}"
                + (f", {vindplaats}" if vindplaats else "")
                + f"]: \"{bewijs['quote']}\""
            )
    if _tekst(deel.get("uncertainty")):
        regels.append(f"     onzekerheid: {deel['uncertainty']}")
    return regels


def _beoordelingsregels(
    bronbewijs: dict[str, Any], status: str, toepasbaarheid: dict[str, Any]
) -> list[str]:
    """De opgeslagen AI-bronbeoordeling (historisch bewijs) met toepasbaarheidslabel."""
    regels: list[str] = []
    beoordeling = bronbewijs.get("source_assessment")
    if isinstance(beoordeling, dict):
        toepasbaar = toepasbaarheid.get("applicable") is True
        regels.append(
            "- Opgeslagen AI-bronbeoordeling (herkomst: AI, geen vaststelling; "
            + (
                "toepasbaar op dit record"
                if toepasbaar
                else "historisch — niet toepasbaar op dit record"
            )
            + "):"
        )
        attributie = beoordeling.get("attribution") or {}
        herkomst = ", ".join(f"{k}={v}" for k, v in attributie.items() if v is not None)
        regels.append(
            f"  status: {_tekst(beoordeling.get('status')) or 'onbekend'}"
            + (f"; {herkomst}" if herkomst else "")
        )
        fout = beoordeling.get("error")
        if isinstance(fout, dict) and fout:
            regels.append(
                f"  technische fout: {_tekst(fout.get('type'))}: {_tekst(fout.get('message'))}"
            )
        delen = beoordeling.get("parts")
        if isinstance(delen, dict):
            for onderdeel, deel in delen.items():
                if not isinstance(deel, dict):
                    continue
                regels.extend(_beoordeling_deelregels(onderdeel, deel))
        afgewezen = beoordeling.get("rejected") or []
        for item in afgewezen:
            if isinstance(item, dict):
                regels.append(
                    f"  afgewezen bewijs ({_tekst(item.get('part'))}): "
                    f"{_tekst(item.get('reason'))}"
                    + (f" — {item['detail']}" if _tekst(item.get("detail")) else "")
                )
    elif status == "present":
        regels.append("- AI-bronbeoordeling: nog niet uitgevoerd")
    return regels


def _reviewdetailregels(review: dict[str, Any], soort: str) -> list[str]:
    """De type-specifieke details van de deskundigenuitzondering/-correctie."""
    regels: list[str] = []
    if soort == "reference_exception":
        regels.append(
            f"  bron-id: {_tekst(review.get('source_id'))}; vindplaats: "
            f"{_tekst(review.get('locator'))}; bronversie: "
            f"{_tekst(review.get('source_version')) or 'onbekend'}"
        )
    elif soort == "part_correction":
        regels.append(
            f"  onderdeel: {_ONDERDEELNAMEN.get(_tekst(review.get('part_id')), _tekst(review.get('part_id')))}; "
            f"oordeel deskundige: {_STATUSNAMEN.get(_tekst(review.get('status')), _tekst(review.get('status')))}"
        )
        for claim in review.get("evidence") or []:
            if isinstance(claim, dict) and _tekst(claim.get("quote")):
                regels.append(
                    f"     bewijs [{_tekst(claim.get('source_id'))}"
                    + (f", {claim['locator']}" if _tekst(claim.get("locator")) else "")
                    + f"]: \"{claim['quote']}\""
                )
    elif soort == "no_appropriate_source":
        zoeken = review.get("search") or {}
        if isinstance(zoeken, dict):
            regels.append(
                "  gedocumenteerd zoeken: zoekvragen "
                f"{', '.join(map(str, zoeken.get('queries') or []))}; "
                f"geraadpleegd {', '.join(map(str, zoeken.get('consulted') or []))}; "
                f"conclusie: {_tekst(zoeken.get('conclusion'))}"
            )
    return regels


def _reviewregels(bronbewijs: dict[str, Any]) -> list[str]:
    """De deskundigenuitzondering, herkenbaar als uitzondering (nooit gewone pass)."""
    regels: list[str] = []
    review = bronbewijs.get("source_review")
    reviewstatus = bronbewijs.get("source_review_status") or {}
    if isinstance(review, dict):
        soort = _tekst(review.get("type"))
        regels.append(
            f"- Deskundigenuitzondering: {_REVIEWTYPEN.get(soort, soort or 'onbekend')}"
        )
        regels.append(
            f"  beoordelaar: {_tekst(review.get('actor')) or 'onbekend'}; "
            f"geaccepteerd: {'ja' if review.get('accepted') is True else 'nee'}; "
            f"vastgelegd: {_tekst(review.get('reviewed_at')) or 'onbekend'}"
        )
        if _tekst(review.get("rationale")):
            regels.append(f"  motivering: {review['rationale']}")
        regels.extend(_reviewdetailregels(review, soort))
        rs = _tekst(reviewstatus.get("status"))
        if rs and rs != "present":
            regels.append(
                f"  status uitzondering: {rs}"
                + (
                    f" — {reviewstatus['reason']}"
                    if _tekst(reviewstatus.get("reason"))
                    else ""
                )
            )
        regels.append(
            "  (een uitzondering is geen gewone positieve beoordeling; overige "
            "onderdelen blijven beoordeeld)"
        )
    elif _tekst(reviewstatus.get("status")) == "invalid":
        regels.append(
            "- Deskundigenuitzondering: ONGELDIG — "
            f"{_tekst(reviewstatus.get('reason'))}"
        )
    return regels


def _reviewhistorieregels(bronbewijs: dict[str, Any]) -> list[str]:
    """Eerdere (vervangen/verwijderde) deskundigenbeoordelingen."""
    regels: list[str] = []
    reviewhistorie = bronbewijs.get("review_history") or []
    if reviewhistorie:
        regels.append(f"- Eerdere deskundigenbeoordelingen: {len(reviewhistorie)}")
        for g in reviewhistorie:
            if not isinstance(g, dict):
                continue
            vorige = g.get("previous_review")
            soort = (
                _tekst(vorige.get("type"))
                if isinstance(vorige, dict)
                else "meerdere/misvormd"
            )
            regels.append(
                f"  * {_tekst(g.get('event'))} op {_tekst(g.get('at'))} door "
                f"{_tekst(g.get('actor')) or 'onbekend'} (versie "
                f"{_tekst(g.get('version_number'))}, vorige: "
                f"{_REVIEWTYPEN.get(soort, soort or 'onbekend')}, status "
                f"{_tekst(g.get('previous_status'))})"
            )
    return regels


def _bewijshistorie_en_voorstelregels(bronbewijs: dict[str, Any]) -> list[str]:
    """Eerdere bewijsversies en herstelvoorstellen."""
    regels: list[str] = []
    historie = bronbewijs.get("history") or []
    if historie:
        regels.append(f"- Eerdere bewijsversies: {len(historie)}")
        for h in historie:
            if isinstance(h, dict):
                regels.append(
                    f"  * {_tekst(h.get('origin'))} op versie "
                    f"{_tekst(h.get('version_number'))}, vervangen "
                    f"{_tekst(h.get('superseded_at'))}"
                )
    voorstellen = bronbewijs.get("proposals") or []
    for v in voorstellen:
        if isinstance(v, dict):
            regels.append(
                f"- Herstelvoorstel {_tekst(v.get('proposal_id'))[:8]}: status "
                f"{_tekst(v.get('status'))} ({_tekst(v.get('actor'))})"
            )
    return regels


def bronbewijs_regels(bronbewijs: dict[str, Any] | None) -> list[str]:
    """Leesbare regels van het opgeslagen bronbewijs (DEF-743), zonder cijfer.

    Toont per bron titel, route, vindplaats/URL en de volledige aangeleverde
    passage; per CON-02-onderdeel het oordeel met geverifieerde citaten,
    onzekerheid en afgewezen bewijs; technische fouten; de deskundigen-
    uitzondering herkenbaar als uitzondering; en of het bewijs nog bij de
    actuele tekst/context hoort. Er is geen score en die wordt ook niet
    verzonnen. De secties staan in vaste volgorde (helpers per sectie).
    """
    if not isinstance(bronbewijs, dict):
        return ["- geen"]
    status = _tekst(bronbewijs.get("status")) or "absent"
    toepasbaarheid = bronbewijs.get("source_assessment_status") or {}
    regels: list[str] = [
        *_statusregels(bronbewijs, status),
        *_bronregels(bronbewijs),
        *_replayregels(bronbewijs, status, toepasbaarheid),
        *_beoordelingsregels(bronbewijs, status, toepasbaarheid),
        *_reviewregels(bronbewijs),
        *_reviewhistorieregels(bronbewijs),
        *_bewijshistorie_en_voorstelregels(bronbewijs),
    ]
    return regels or ["- geen"]


def _bronsecties(gegevens: dict) -> list[str]:
    """De secties "Gebruikte bronnen" en "Bronbeoordeling (CON-02)" (zelfde tekst)."""
    bronnen = gegevens.get("bronnen", [])  # Gebruikte bronnen voor de definitie
    regels: list[str] = []
    regels.append("\n\U0001f4da Gebruikte bronnen:")
    regels += [f"- {b}" for b in bronnen if b.strip()] or ["- geen"]

    regels.append("\n\U0001f50e Bronbeoordeling (CON-02):")
    regels += bronbewijs_regels(gegevens.get("bronbewijs"))  # DEF-743
    return regels


def _int01sectie(gegevens: dict) -> list[str]:
    """De opgeslagen INT-01-deeluitkomst (DEF-770); afwezig = zichtbaar niet beoordeeld."""
    regels = ["\n\U0001f9ed Zinsgrenzen (INT-01):"]
    uitkomst = exportregels(gegevens.get("int01_beoordeling"))
    if not uitkomst:
        return [*regels, "- geen opgeslagen INT-01-uitkomst: niet beoordeeld"]
    return [*regels, f"- {uitkomst[0]}", *uitkomst[1:]]


def exporteer_naar_txt(gegevens: dict) -> str:
    """Exporteert definitie gegevens naar een geformatteerd TXT bestand."""
    # Haal alle benodigde gegevens op uit de data dictionary
    begrip = gegevens.get("begrip", "")  # Het gedefinieerde begrip
    definitie = gegevens.get(
        "definitie_gecorrigeerd", ""
    )  # Finale gecorrigeerde definitie
    definitie_orig = gegevens.get(
        "definitie_origineel", ""
    )  # Oorspronkelijke AI-gegenereerde definitie
    metadata = gegevens.get("metadata", {})  # Extra metadata informatie
    context_dict = gegevens.get("context_dict", {})  # Context categorieën en waarden
    toetsresultaten = gegevens.get(
        "toetsresultaten", {}
    )  # Resultaten van kwaliteitstoetsen

    # Haal optionele voorbeelden en aanvullende informatie op
    voorbeeld_zinnen = (
        gegevens.get("voorbeeld_zinnen") or []
    )  # Voorbeeldzinnen met het begrip
    praktijkvoorbeelden = (
        gegevens.get("praktijkvoorbeelden") or []
    )  # Praktische gebruiksvoorbeelden
    tegenvoorbeelden = (
        gegevens.get("tegenvoorbeelden") or []
    )  # Tegenvoorbeelden ter verduidelijking
    toelichting = gegevens.get("toelichting") or ""  # Uitgebreide toelichting
    synoniemen = gegevens.get("synoniemen") or ""  # Synoniemen van het begrip
    voorkeursterm = gegevens.get("voorkeursterm", "")  # Voorkeursterm indien anders
    antoniemen = gegevens.get("antoniemen") or ""  # Antoniemen van het begrip

    # Genereer unieke bestandsnaam met timestamp
    tijdstempel = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
    bestandsnaam = f"definitie_{begrip.replace(' ', '_').lower()}_{tijdstempel}.txt"  # Normaliseer begrip voor bestandsnaam
    pad = os.path.join("exports", bestandsnaam)  # Volledig pad naar export bestand

    regels = []
    regels.append(f"\U0001f4d8 Begrip: {begrip}\n")
    regels.append(f"\u270f\ufe0f Definitie (gecorrigeerd): {definitie}\n")
    regels.append(f"\U0001f4ce Oorspronkelijke definitie: {definitie_orig}\n")

    regels.append("\U0001f9fe Metadata:")
    for k, v in metadata.items():
        if k == "ketenpartners" and isinstance(v, list):
            regels.append(f"- {k}: {', '.join(v) if v else 'geen'}")
        elif k == "datum_voorstel" and v:
            regels.append(
                f"- {k}: {v.strftime('%d-%m-%Y') if hasattr(v, 'strftime') else str(v)}"
            )
        elif v:
            regels.append(f"- {k}: {v}")
        else:
            regels.append(f"- {k}: geen")

    regels.append("\n\U0001f3e9 Contexten:")
    for ctx_type, waarden in context_dict.items():
        lijst = ", ".join(waarden) if waarden else "geen"
        regels.append(f"- {ctx_type.capitalize()}: {lijst}")

    regels.append("\n\U0001f4ca Toetsresultaten:")
    if isinstance(toetsresultaten, list):
        regels += [f"- {r}" for r in toetsresultaten]
    elif isinstance(toetsresultaten, dict):
        regels += [f"- {k}: {v}" for k, v in toetsresultaten.items()]
    else:
        regels.append("- geen")

    regels += _int01sectie(gegevens)
    regels += _bronsecties(gegevens)

    regels.append("\n\U0001f4a1 Toelichting:")
    regels.append(toelichting.strip() or "- geen")

    regels.append("\n\U0001f9e2 Voorbeeldzinnen:")
    regels += [f"- {z.strip()}" for z in voorbeeld_zinnen if z.strip()] or ["- geen"]

    regels.append("\n\U0001f9e2 Praktijkvoorbeelden:")
    regels += [f"- {z.strip()}" for z in praktijkvoorbeelden if z.strip()] or ["- geen"]

    regels.append("\n\U0001f6ab Tegenvoorbeelden:")
    regels += [f"- {z.strip()}" for z in tegenvoorbeelden if z.strip()] or ["- geen"]

    regels.append("\n\U0001f501 Synoniemen:")
    regels += [f"- {s.strip()}" for s in synoniemen.splitlines() if s.strip()] or [
        "- geen"
    ]

    regels.append("\n🏷️ Voorkeursterm:")
    regels.append(f"- {voorkeursterm or 'geen'}")

    regels.append("\n\U0001f504 Antoniemen:")
    regels += [f"- {a.strip()}" for a in antoniemen.splitlines() if a.strip()] or [
        "- geen"
    ]

    os.makedirs("exports", exist_ok=True)
    with open(pad, "w", encoding="utf-8") as f:
        f.write("\n".join(regels))

    return pad
