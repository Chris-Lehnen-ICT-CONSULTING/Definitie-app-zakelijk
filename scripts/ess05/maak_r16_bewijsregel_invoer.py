"""DEF-768 R16 — invoer van de mechanismeproef bewijsregels (A/B/C).

Opdracht Chris 28-09 ("ga hier mee verder",
`logs/def768/bewijsregels-gebruikersopdracht-v1.json`) en het startmandaat
`logs/def768/bewijsregels-start-en-mandaat-v1.md`: een minimale, echte
mechanismeproef van `ess05-bewijsregels/3`
(`docs/technisch/ess05-bewijsregels-contract-v3.md`). Per geval één
broninterpretatie en ten hoogste drie geïsoleerde controles; vaste code
bepaalt de uitkomst.

- **A** — het R13-geval H3 ongewijzigd (gepinde bron): doel tijdelijk en
  kosteloos, buur verhuur tijdelijk, over de kosten van verhuur zegt het
  volledig gebonden materiaal niets. Verwacht: `review_required` (buur open),
  4 aanroepen.
- **B** — SYNTHETISCH, GEEN MODELUITVOER: exact het materiaal van A; alleen
  markeert de app de bron als uittreksel (`onvolledig`). Een `onbesproken`
  over dat materiaal is dan geen vastgesteld informatiegebrek. Verwacht:
  `error` (`dekking_ontbreekt`) na de interpretatie, zonder controle:
  1 aanroep. Dit toetst de vaste dekkingsgrens, geen modelprestatie.
- **C** — SYNTHETISCH, GEEN MODELUITVOER: A met een permanente verhuur. De
  verhuurzin van de bron en de verhuurdefinitie noemen permanent in plaats van
  tijdelijk (zonder teruggave). Verwacht: `pass` (buur onderscheiden op duur),
  4 aanroepen.

Verwachtingen (uitkomst, fout, buuroordeel, aanroepen) staan per item buiten
de modelpayload. De inhoudelijke oracle (`--oracle`) is voor de
onafhankelijke inhoudsreview en gaat nooit naar het model.

    .venv/bin/python scripts/ess05/maak_r16_bewijsregel_invoer.py [--doel P] [--oracle P]

Doelen worden nooit overschreven; alle bronnen worden alleen gelezen.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import maak_r10_verificatie_invoer as mk10
import migreer_r7_naar_v2 as mig
import proefinvoer as pi
from maak_r10_verificatie_invoer import MakerfoutError

__all__ = [
    "INVOERSCHEMA",
    "MakerfoutError",
    "maak_bewijsregel_invoer",
    "main",
    "oracletekst",
]

INVOERSCHEMA = "def768-ess05-bewijsregel-invoer/1"
LOGS = PROJECT_ROOT / "logs" / "def768"
R13_GEVALLEN = (
    PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R13" / "herkenbare-gevallen-v1.json"
)
R13_GEVALLEN_SHA256 = "b212b826ef51dce8c20b5a587e57389b13e3d24ab6d590e5dcfec7e60493841b"
BRONNEN = {
    "gebruikersopdracht": (
        LOGS / "bewijsregels-gebruikersopdracht-v1.json",
        "a2776c37c15116cd3e9c4f5c8502fe9f16b75c4fa76bbfd601461d50f309dfc5",
    ),
    "startmandaat": (
        LOGS / "bewijsregels-start-en-mandaat-v1.md",
        "cfefb581c1ca1a31a9c712bad69a106679f275178794ab97653c3893c7968f67",
    ),
    "implementatieopdracht": (
        LOGS / "bewijsregels-implementatie-opdracht-v1.md",
        "c051d0090c94163b1fc7511014850b95549cdcb21579ec7ff704d0478eddde03",
    ),
    "correctieopdracht": (
        LOGS / "bewijsregels-contractcorrecties-opdracht-v1.md",
        "730836a183d0bcbbfd0165dad1bb0c6796c998a0db088b1b656d4cecc0f83689",
    ),
    "k4_correctieopdracht": (
        LOGS / "bewijsregels-k4-correctie-opdracht-v1.md",
        "a28b1a4fa883a63013e5f82b4826cba9a5e055b43435afbf19a143726090d463",
    ),
}
DOEL = (
    PROJECT_ROOT / "reports" / "DEF-768-AI-20260928-R16" / "bewijsregel-invoer-v1.json"
)
ORACLE = LOGS / "ronde16-bewijsregels-oracle-invoer-v1.md"
AUTEUR = mk10.AUTEUR
LABEL = "SYNTHETISCH, GEEN MODELUITVOER"
#: Alleen deze velden gaan via de modelprojectie naar het model.
_MODELVELDEN = (
    "begrip",
    "tekst",
    "toelichting",
    "categorie",
    "context",
    "bronnen",
    "buren",
)

#: C: de twee vervangingen in H3 (bronzin en buurdefinitie), elk exact eenmaal.
C_BRON = (
    (
        "Verhuur: de servicedesk stelt apparatuur tijdelijk ter beschikking aan een "
        "medewerker; de medewerker geeft de apparatuur daarna terug."
    ),
    "Verhuur: de servicedesk stelt apparatuur permanent ter beschikking aan een medewerker.",
)
C_BUUR = (
    (
        "tijdelijk ter beschikking stellen van apparatuur aan een medewerker, die de "
        "apparatuur daarna teruggeeft"
    ),
    "permanent ter beschikking stellen van apparatuur aan een medewerker",
)


def _h3() -> dict[str, Any]:
    data = json.loads(mk10._gepind(R13_GEVALLEN, R13_GEVALLEN_SHA256, "R13-gevallen"))
    (h3,) = [g for g in data["gevallen"] if g.get("id") == "H3"]
    return h3


def _vervang_eenmaal(tekst: str, oud: str, nieuw: str, naam: str) -> str:
    if tekst.count(oud) != 1:
        msg = f"{naam}: {oud!r} staat niet precies eenmaal in de H3-tekst"
        raise MakerfoutError(msg)
    return tekst.replace(oud, nieuw)


def _geval_c(a: Mapping[str, Any]) -> dict[str, Any]:
    c = copy.deepcopy(dict(a))
    c["id"] = "R16-C"
    (bron,) = c["bronnen"]
    bron["snippet"] = _vervang_eenmaal(bron["snippet"], *C_BRON, "C-bron")
    (buur,) = c["buren"]
    buur["definitie"] = _vervang_eenmaal(buur["definitie"], *C_BUUR, "C-buur")
    return c


def _item(
    naam: str,
    geval: Mapping[str, Any],
    *,
    variant: str,
    synthetisch: bool,
    onvolledig: Sequence[str],
    verwacht: Mapping[str, Any],
    herkomst: Mapping[str, Any],
) -> dict[str, Any]:
    from domain.ess05 import bewijsregels as br
    from services.validation.ess05_bewijsregel_service import bouw_interpretatieprompt
    from services.validation.ess05_verification_service import prompthash

    materiaal, buren, _ = mig.verificatiemateriaal(geval)
    if len(buren) != 1:
        msg = f"{naam}: precies één buur vereist"
        raise MakerfoutError(msg)
    invoer = br.Vergelijkingsinvoer(
        term=geval["begrip"],
        materiaal=materiaal,
        buren=tuple((b.id, b.term) for b in buren),
        onvolledig=frozenset(onvolledig),
    )
    system, user = bouw_interpretatieprompt(invoer)
    return {
        "id": naam,
        "variant": variant,
        "synthetisch": synthetisch,
        "label": LABEL if synthetisch else "ongewijzigd uit gepinde bron",
        "geval": dict(geval),
        "geval_sha256": pi.sha_json(dict(geval)),
        "materiaal_sha256": {m: mk10._sha(t) for m, t in materiaal.items()},
        "buren": [[b.id, b.term] for b in buren],
        "onvolledig": list(onvolledig),
        "prompt_sha256": prompthash(system, user),
        "verwacht": dict(verwacht),
        "herkomst": dict(herkomst),
    }


def maak_bewijsregel_invoer() -> dict[str, Any]:
    """A/B/C uit het gepinde H3; afwijking in een bron is een makerfout."""
    from services.validation.ess05_bewijsregel_service import Ess05BewijsregelService

    bronnen = {}
    for naam, (pad, sha) in BRONNEN.items():
        mk10._gepind(pad, sha, naam)
        bronnen[naam] = {"pad": mk10._rel(pad), "sha256": sha}
    h3 = _h3()
    a = {"id": "R16-A", **{k: copy.deepcopy(h3[k]) for k in _MODELVELDEN}}
    h3_herkomst = {
        "bron": mk10._rel(R13_GEVALLEN),
        "sha256": R13_GEVALLEN_SHA256,
        "geval": "H3",
    }
    materiaal_a, _, _ = mig.verificatiemateriaal(a)
    bron_ids = [m for m in materiaal_a if m.startswith("source:")]
    if len(bron_ids) != 1:
        msg = f"A: precies één bron verwacht, kreeg {bron_ids}"
        raise MakerfoutError(msg)
    items = [
        _item(
            "A",
            a,
            variant="doel tijdelijk+kosteloos, buur tijdelijk, kosten van verhuur "
            "onbesproken in volledig gebonden materiaal",
            synthetisch=False,
            onvolledig=[],
            verwacht={
                "uitkomst": "review_required",
                "fout_soort": None,
                "buur_oordeel": "open",
                "aanroepen": 4,
            },
            herkomst={**h3_herkomst, "bewerking": "alleen de modelvelden, ongewijzigd"},
        ),
        _item(
            "B",
            a,
            variant="A met de bron als uittreksel gemarkeerd: noodzakelijke dekking "
            "ontbreekt",
            synthetisch=True,
            onvolledig=bron_ids,
            verwacht={
                "uitkomst": "error",
                "fout_soort": "dekking_ontbreekt",
                "buur_oordeel": None,
                "aanroepen": 1,
            },
            herkomst={
                **h3_herkomst,
                "bewerking": "materiaal gelijk aan A; alleen de app-markering onvolledig "
                f"voor {bron_ids[0]}",
            },
        ),
        _item(
            "C",
            _geval_c(a),
            variant="A met permanente verhuur: afgrenzing op duur, kosten onbekend",
            synthetisch=True,
            onvolledig=[],
            verwacht={
                "uitkomst": "pass",
                "fout_soort": None,
                "buur_oordeel": "onderscheiden",
                "aanroepen": 4,
            },
            herkomst={
                **h3_herkomst,
                "bewerking": "verhuurzin van de bron en verhuurdefinitie: tijdelijk "
                "(met teruggave) vervangen door permanent (zonder teruggave)",
                "vervangingen": {"bron": list(C_BRON), "buurdefinitie": list(C_BUUR)},
            },
        ),
    ]
    return {
        "schema": INVOERSCHEMA,
        "status": (
            "vooraf vastgelegd vóór elke R16-aanroep; B en C zijn "
            f"{LABEL}; verwachtingen buiten de modelpayload"
        ),
        "contract": Ess05BewijsregelService.contractidentiteit(),
        "herkomst": {
            "bronnen": bronnen,
            "regels": "scripts/ess05/maak_r16_bewijsregel_invoer.py (moduledocstring)",
            "contractnotitie": "docs/technisch/ess05-bewijsregels-contract-v3.md",
            "auteur": AUTEUR,
        },
        "items": items,
    }


def oracletekst(invoer: Mapping[str, Any]) -> str:
    """Invoer voor de onafhankelijke inhoudelijke oraclecontrole (geen modelpayload)."""
    from domain.ess05 import bewijsregels as br
    from services.validation.ess05_bewijsregel_service import bouw_interpretatieprompt

    delen = [
        "# DEF-768 R16 — invoer voor de oraclecontrole van de bewijsregelproef",
        "",
        (
            "Per geval: wat het model ziet (de interpretatieprompt), de vooraf "
            "vastgelegde verwachting en de grond. Vragen: (1) is de verwachte "
            "uitkomst juist volgens `ess05-bewijsregels/3` als het model het "
            "materiaal juist interpreteert; (2) welke juiste interpretaties zijn er, "
            "en geven die allemaal dezelfde uitkomst; (3) is B werkelijk een "
            "dekkingsgebrek en geen informatiegebrek; (4) is de synthetische "
            "C-wijziging minimaal en ondubbelzinnig?"
        ),
        "",
        "Grond per geval (vaste regels, contract v3 §3–§4):",
        "",
        (
            "- **A**: kern = tijdelijk, kosteloos, ontvanger een medewerker, teruggave. "
            "Verhuur is volgens bron en buurdefinitie tijdelijk, aan een medewerker, "
            "met teruggave; over kosten zegt het volledig gebonden materiaal niets "
            "(`onbesproken`). Kosten is dan onbekend: geen afgrenzing en geen "
            "tegengeval bewezen → buur `open` → `review_required`. Aanroepen: "
            "interpretatie plus kern-, doel- en buurcontrole = 4."
        ),
        (
            "- **B**: hetzelfde materiaal, maar de app markeert de bron als "
            "uittreksel. Elk `onbesproken` over dat materiaal is `dekking_ontbreekt` "
            "(contract §3 punt 7) → `error` vóór elke controle: 1 aanroep. Geeft het "
            "model voor de verhuurkosten iets anders dan `onbesproken` (bijvoorbeeld "
            "`ontkend`), dan is dat een interpretatiefout en een andere uitkomst."
        ),
        (
            "- **C**: verhuur is permanent (niet tijdelijk). De hele buur is op het "
            "vereiste kernkenmerk duur `ontkend` → `onderscheiden` → `pass`. Kosten "
            "blijven onbekend en teruggave onbesproken of ontkend; dat verandert de "
            "uitkomst niet. Aanroepen: 4."
        ),
        "",
        (
            "Niet in scope van deze oracle: de formulering van de weergave, de "
            "kenmerklabels van het model en of een controle `supported` zegt; een "
            "afgewezen controle is een geldige `error`-uitkomst en geen fout van de "
            "regels."
        ),
        "",
    ]
    for item in invoer["items"]:
        materiaal, buren, _ = mig.verificatiemateriaal(item["geval"])
        vergelijking = br.Vergelijkingsinvoer(
            term=item["geval"]["begrip"],
            materiaal=materiaal,
            buren=tuple((b.id, b.term) for b in buren),
            onvolledig=frozenset(item["onvolledig"]),
        )
        _, user = bouw_interpretatieprompt(vergelijking)
        delen += [
            f"## {item['id']} — {item['variant']}",
            "",
            f"- label: {item['label']}",
            f"- verwacht: `{json.dumps(item['verwacht'], ensure_ascii=False)}`",
            f"- onvolledig: `{item['onvolledig']}`",
            f"- prompt_sha256 `{item['prompt_sha256']}`, geval_sha256 `{item['geval_sha256']}`",
            "",
            (
                "Gebruikersprompt van de interpretatie (exact de modelpayload, naast de "
                "vaste systeemprompt):"
            ),
            "",
            "```text",
            user,
            "```",
            "",
            "Herkomst (buiten de payload):",
            "",
            "```json",
            json.dumps(item["herkomst"], ensure_ascii=False, indent=1),
            "```",
            "",
        ]
    return "\n".join(delen)


def _schrijf(doel: Path, tekst: str) -> None:
    if doel.exists():
        msg = f"doel bestaat al: {doel}"
        raise FileExistsError(msg)
    doel.parent.mkdir(parents=True, exist_ok=True)
    with doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    sys.stdout.write(f"{doel} sha256={mk10._sha(tekst)}\n")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doel", type=Path, default=DOEL)
    p.add_argument("--oracle", type=Path, default=None)
    args = p.parse_args(argv)
    invoer = maak_bewijsregel_invoer()
    _schrijf(args.doel, json.dumps(invoer, ensure_ascii=False, indent=2) + "\n")
    if args.oracle is not None:
        _schrijf(args.oracle, oracletekst(invoer))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
