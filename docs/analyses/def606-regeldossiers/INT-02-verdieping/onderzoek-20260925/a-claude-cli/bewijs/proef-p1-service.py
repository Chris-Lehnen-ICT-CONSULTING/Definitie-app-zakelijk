"""Proef P1 (onderzoekslijn A, INT-02): ModularValidationService rechtstreeks.

Offline, synthetisch, geen modelcalls. Uitvoeren vanuit de repo-root:
    PYTHONPATH=src .venv/bin/python <dit bestand>
Schrijft invoer en uitkomsten naast dit script.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

HIER = Path(__file__).resolve().parent
BUREN = ["INT-01", "INT-10", "ARAI-04", "ARAI-04SUB1", "STR-06", "INT-08", "ESS-04", "ESS-05"]
CTX = {
    "organisatorische_context": ["Dienst Justis"],
    "juridische_context": ["bestuursrecht"],
    "wettelijke_basis": ["Algemene wet bestuursrecht"],
}

CASUSSEN = [
    ("INT02-C01", "transitie-eis", "transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken.", {}),
    ("INT02-C02", "transitie-eis", "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken.", {}),
    ("INT02-C03", "aanvraag", "Aanvraag die wordt afgewezen indien een bijlage ontbreekt.", {}),
    ("INT02-C04", "even getal", "Getal dat even is indien het zonder rest door twee deelbaar is.", {}),
    ("INT02-C05", "even getal", "Geheel getal dat zonder rest door twee deelbaar is.", {}),
    ("INT02-C06", "leeg", "", {}),
    ("INT02-C10", "stelselmatige dader", "persoon die in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld.", {}),
    ("INT02-C11", "stelselmatige dader", "persoon die als stelselmatige dader geldt indien hij in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld.", {}),
    ("INT02-C12", "weigering", "besluit waarmee de bevoegde autoriteit een aanvraag afwijst, tenzij zij van oordeel is dat de aanvrager daardoor onevenredig zou worden benadeeld.", {}),
    ("INT02-C13", "vervallenverklaring", "besluit waarmee de bevoegde autoriteit een vergunning intrekt wanneer zij dat na afweging van de belangen van de houder evenredig acht.", {}),
    ("INT02-C14", "aangifte", "verklaring die een getuige van een strafbaar feit moet afleggen bij de politie.", {}),
    ("INT02-C15", "aanvraag", "verzoek dat de behandelaar binnen zes weken beoordeelt en bij een ontbrekende bijlage afwijst.", {}),
    ("INT02-C16", "verzuimboete", "bestuurlijke boete die wordt opgelegd wanneer een aangifte niet tijdig is gedaan.", {}),
    ("INT02-C17", "stemgerechtigd lid", "Een lid is stemgerechtigd indien ingeschreven vóór 1 januari.", {}),
    ("INT02-C18", "stemgerechtigd lid", "lid dat vóór 1 januari van het lopende verenigingsjaar is ingeschreven.", {}),
    ("INT02-C19", "gewaarmerkt document", "Een document geldt als gewaarmerkt mits voorzien van handtekening en datum.", {}),
    ("INT02-C20", "eigen risico", "deel van de zorgkosten dat een verzekerde zelf draagt voor zover die kosten onder de basisverzekering vallen.", {}),
    ("INT02-C21", "tenzij-clausule", "contractbepaling die een uitzondering op een hoofdregel formuleert.", {}),
    ("INT02-C22", "tijdige aangifte", "aangifte die binnen vijf werkdagen na het feit is gedaan.", {}),
    ("INT02-C23", "toegang", "Toegang:", {}),
    ("INT02-C24", "toegang", "Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld.", {}),
    ("INT02-C25", "korting", "korting: verlaging indien tijdig betaald", {}),
    ("INT02-C26", "identificatieplichtige", "Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart", {}),
    ("INT02-C27", "leeftijd", "aantal volledige jaren tussen de geboortedatum van een persoon en de peildatum.", {}),
    ("INT02-C29", "aanvraag", "Aanvraag die wordt afgewezen indien een bijlage ontbreekt.", CTX),
]


async def draai():
    svc = ModularValidationService(get_toetsregel_manager(), None, None)
    uit = []
    for cid, begrip, tekst, ctx in CASUSSEN:
        res = await svc.validate_definition(
            begrip=begrip, text=tekst, ontologische_categorie=None, context=dict(ctx)
        )
        review = {r.get("rule_id"): r for r in res.get("review_required") or []}
        statussen = res.get("rule_statuses") or {}
        viol = sorted({str(v.get("code") or v.get("rule_id")) for v in res.get("violations") or []})
        r02 = review.get("INT-02") or {}
        uit.append(
            {
                "id": cid,
                "begrip": begrip,
                "tekst": tekst,
                "context": ctx,
                "int02_status": statussen.get("INT-02"),
                "int02_in_review_required": "INT-02" in review,
                "int02_in_passed": "INT-02" in (res.get("passed_rules") or []),
                "int02_violation": "INT-02" in viol,
                "int02_reason": r02.get("reason"),
                "int02_signals": list(r02.get("signals") or []),
                "buur_statussen": {c: statussen.get(c) for c in BUREN},
                "violations": viol,
                "overall_score": res.get("overall_score"),
                "is_acceptable": res.get("is_acceptable"),
            }
        )
    return uit


def main():
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    (HIER / "p1-invoer.json").write_text(
        json.dumps([{"id": c, "begrip": b, "tekst": t, "context": x} for c, b, t, x in CASUSSEN], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    uitkomsten = asyncio.run(draai())
    (HIER / "p1-uitkomsten.json").write_text(
        json.dumps({"commit": commit, "python": sys.version, "uitkomsten": uitkomsten}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for u in uitkomsten:
        print(u["id"], u["int02_status"], u["int02_signals"], "viol=", u["violations"])


if __name__ == "__main__":
    main()
