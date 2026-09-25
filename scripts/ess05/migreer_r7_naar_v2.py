"""DEF-768 R8 — migratie van zes R7-antwoorden (/1) naar conceptoordelen (/2).

Invoer voor de verifier-only-fase (livevervolg-proefvoorstel-technisch-v1 §3,
met de leidende rootcorrecties). Zes letterlijke R7-bronantwoorden: drie met
een bekende fout (V-N1..V-N3) en drie zonder (V-P1..V-P3). Eén migratieregel
voor alle zes; het label bestaat alleen in `BRONNEN`, niet in `migreer`.

Migratieregels (fail-closed, geen reparatie):

- **bewijs** — E1..En: de volledige tekst van elk niet-leeg materiaal (kern,
  context, betekenis, bronnen, buurbeschrijvingen), in materiaalvolgorde;
  daarna de kernfragmenten (bovenbegrip, kenmerk, onderscheidend citaat).
  Offsets en `material_sha256` berekent de code; een zelfde plaats krijgt
  één ID. Verfijning van §3.2: niet alleen de kern maar elk materiaal is
  één volledige bewijsplaats, zodat een claim nooit een ongeciteerde
  vindplaats nodig heeft;
- **claims** — C1..Cn, letterlijk en ongesplitst, rol `material`, bewijs =
  alle volledige materiaalplaatsen, geen premissen. Volgorde: de algemene
  `reason`, dan per buur `reason`, `missing_feature`, `uncertainty`;
- **bovenbegrip** — uit de algemene reason (`bovenbegrip '…'`). Heeft de
  kern een kenmerk (`lacks_differentia` onwaar), dan begint de kern met het
  bovenbegrip plus spatie en is de rest één kenmerk F1; anders is de
  kenmerkenlijst leeg en is het bovenbegrip alleen bewijs als het precies
  één keer in de kern staat;
- **buren** — `distinguished`: het citaat staat precies één keer in de kern;
  `missing_feature` en `uncertainty` worden claims; labels ongewijzigd;
- **vraag** — `{"text": vraag, "claims": []}`; voorstellen worden niet
  gemigreerd (geen van de zes heeft er een; anders een harde fout).

De foutdragende items van V-N1..V-N3 zijn een voorstel voor de trouwreview
(`controlelijst`), geen vastgesteld oordeel.

    .venv/bin/python scripts/ess05/migreer_r7_naar_v2.py [--doel P] [--controlelijst P]

Doel en controlelijst worden nooit overschreven; de R7-bestanden alleen gelezen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import proefinvoer as pi

from domain.ess05.bewijs import CONCEPTSCHEMA, verplichte_controles
from domain.ess05.contract import Buur, beoordelingsmateriaal, valideer_concept

R7_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R7"
R8_MAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R8"
R7_EINDSET = "onafhankelijke-eindset-v1.json"
R7_EINDSET_SHA256 = "9b239e2c1b462f1e2235f9085ff85b82b5957506389d7db2f9b8b841692ee31b"
DOEL = R8_MAP / "verificatie-invoer-v1.json"
CONTROLELIJST = R8_MAP / "migratie-controlelijst-v1.md"
INVOERSCHEMA = "def768-r8-verificatie-invoer/1"
AUTEUR = "Claude Code CLI-uitvoerder, sessie 6d273f41-0afb-480a-9034-1c87b1ecba58"
_T_EIND = "t_eind-20260925T084536204991Z/calls"
_T_HERH = "t_herhaling-20260925T084842767646Z/calls"

#: De zes bronantwoorden (letterlijk, R7) met hun voorgestelde foutdragende
#: items: `claims_met` = tekstfragmenten die precies één claim aanwijzen,
#: `items` = letterlijke verplichte controles.
BRONNEN: tuple[dict[str, Any], ...] = (
    {
        "id": "V-N1",
        "soort": "fout",
        "sleutel": "t_eind|R705|1",
        "seq": 14,
        "callrecord": f"{_T_EIND}/014-t_eind-R705.json",
        "ruw_sha256": "3d5599bce6c528518e884e96db5c6d27e69d70d2566a23c7c1371c326e40e8d8",
        "foutdragend": {
            "claims_met": ["Dat kenmerk draagt geen enkel exemplaar van draaihaak"],
            "items": ["neighbour:gebruiker:c9527b09e446"],
        },
    },
    {
        "id": "V-N2",
        "soort": "fout",
        "sleutel": "t_eind|R712|1",
        "seq": 21,
        "callrecord": f"{_T_EIND}/021-t_eind-R712.json",
        "ruw_sha256": "0123e4bfb901fb4fbb4d81813c731edc59f129a0aa701069adb2d0d67a6a2325",
        "foutdragend": {"claims_met": [], "items": ["core_features", "feature:F1"]},
    },
    {
        "id": "V-N3",
        "soort": "fout",
        "sleutel": "t_herhaling|R719|herhaling-1",
        "seq": 34,
        "callrecord": f"{_T_HERH}/034-t_herhaling-R719.json",
        "ruw_sha256": "72107f2b14e984a4f2e98a97e519c8c67314fcbe7dee2a91b2ecb43fa989057e",
        "foutdragend": {
            "claims_met": [
                (
                    "de vastlegging van het tijdstip is volgens de bron een attribuut "
                    "en geen afzonderlijk begrip"
                )
            ],
            "items": [],
        },
    },
    {
        "id": "V-P1",
        "soort": "goed",
        "sleutel": "t_herhaling|R705|herhaling-1",
        "seq": 32,
        "callrecord": f"{_T_HERH}/032-t_herhaling-R705.json",
        "ruw_sha256": "36892093bd77d2024838de562e6c9089f39fe72366198a60fab797bd15af80a6",
        "foutdragend": None,
    },
    {
        "id": "V-P2",
        "soort": "goed",
        "sleutel": "t_eind|R709|1",
        "seq": 18,
        "callrecord": f"{_T_EIND}/018-t_eind-R709.json",
        "ruw_sha256": "7a10a84b6909259f2e45fb9e5298f47a913b0aa1b69b0980f0a40571859f7e7f",
        "foutdragend": None,
    },
    {
        "id": "V-P3",
        "soort": "goed",
        "sleutel": "t_eind|R719|1",
        "seq": 28,
        "callrecord": f"{_T_EIND}/028-t_eind-R719.json",
        "ruw_sha256": "d03b375b51a6e6ed1b798ceea0a27b6ebf8bb43d6702241bf396d6cf14fc09b1",
        "foutdragend": None,
    },
)

_OORDEELVELDEN = frozenset(
    {"lacks_differentia", "reason", "neighbours", "proposed_neighbours", "question"}
)
_BUURVELDEN = frozenset(
    {
        "neighbour_id",
        "distinction",
        "distinguishing_feature_quote",
        "missing_feature",
        "reason",
        "uncertainty",
    }
)
_BOVENBEGRIP = re.compile(r"bovenbegrip '([^']+)'")


class MigratiefoutError(RuntimeError):
    """Bron of migratie voldoet niet (fail-closed, niets geschreven)."""


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def verificatiemateriaal(
    geval: Mapping[str, Any], norm: Mapping[str, str] | None = None
) -> tuple[dict[str, str], tuple[Buur, ...], str]:
    """(materiaal, buren, materiaalregels) zoals `Ess05AssessmentService` ze bouwt.

    Dezelfde projectie en canonisering als de T-stap (`pi.bouw_t_prompt`),
    zodat de verificatie-invoer gelijk is aan die in de productieketen.
    """
    from services.validation.ess05_assessment_service import (
        _invoerregels,
        laad_ess05_norm,
    )

    projectie = pi.modelprojectie(geval)
    prompt = pi.bouw_t_prompt(
        projectie, norm if norm is not None else laad_ess05_norm()
    )
    contexten = projectie.get("context") or {}
    intentie = pi.intentie(projectie)
    materiaal = beoordelingsmateriaal(
        projectie["begrip"],
        projectie["tekst"],
        prompt.bronnen,
        prompt.buren,
        contexten=contexten,
        intentie=intentie,
    )
    regels = _invoerregels(
        projectie["begrip"],
        projectie["tekst"],
        contexten,
        prompt.bronnen,
        buren=prompt.buren,
        intentie=intentie,
    )
    return materiaal, prompt.buren, "\n".join(regels)


class _Bewijs:
    """Bewijsplaatsen met neutrale, doorlopende ID's; één ID per plaats."""

    def __init__(self, materiaal: Mapping[str, str]) -> None:
        self._materiaal = materiaal
        self.items: list[dict[str, Any]] = []
        self._per_plaats: dict[tuple[str, int, int], str] = {}

    def plaats(self, materiaal_id: str, start: int, eind: int) -> str:
        sleutel = (materiaal_id, start, eind)
        if sleutel not in self._per_plaats:
            tekst = self._materiaal[materiaal_id]
            ref = f"E{len(self.items) + 1}"
            self._per_plaats[sleutel] = ref
            self.items.append(
                {
                    "id": ref,
                    "material_id": materiaal_id,
                    "material_sha256": _sha(tekst),
                    "start": start,
                    "end": eind,
                    "quote": tekst[start:eind],
                }
            )
        return self._per_plaats[sleutel]

    def uniek_in_kern(self, fragment: str, wat: str) -> str:
        kern = self._materiaal["definition"]
        if not fragment or kern.count(fragment) != 1:
            msg = f"{wat} {fragment!r} staat niet precies één keer in de kern"
            raise MigratiefoutError(msg)
        start = kern.index(fragment)
        return self.plaats("definition", start, start + len(fragment))


def _controleer_vorm(oordeel: Mapping[str, Any]) -> None:
    if not isinstance(oordeel, Mapping) or set(oordeel) != _OORDEELVELDEN:
        msg = "R7-oordeel heeft niet exact de /1-velden"
        raise MigratiefoutError(msg)
    if oordeel["proposed_neighbours"]:
        msg = "voorstellen worden niet gemigreerd (geen vastgelegde regel)"
        raise MigratiefoutError(msg)
    for buur in oordeel["neighbours"]:
        if not isinstance(buur, Mapping) or set(buur) != _BUURVELDEN:
            msg = "R7-buuroordeel heeft niet exact de /1-velden"
            raise MigratiefoutError(msg)


def _kern_en_bovenbegrip(
    oordeel: Mapping[str, Any], bewijs: _Bewijs, kern: str
) -> tuple[str | None, list[dict[str, str]]]:
    """(genus_evidence, core_features) volgens de migratieregel."""
    treffer = _BOVENBEGRIP.search(oordeel["reason"])
    if treffer is None:
        msg = "geen bovenbegrip '…' in de algemene reason"
        raise MigratiefoutError(msg)
    genus = treffer.group(1)
    if oordeel["lacks_differentia"]:
        genus_ref = (
            bewijs.uniek_in_kern(genus, "bovenbegrip")
            if kern.count(genus) == 1
            else None
        )
        return genus_ref, []
    if not kern.startswith(genus + " ") or not kern[len(genus) + 1 :].strip():
        msg = f"de kern begint niet met bovenbegrip {genus!r} plus een kenmerk"
        raise MigratiefoutError(msg)
    genus_ref = bewijs.plaats("definition", 0, len(genus))
    kenmerk = bewijs.plaats("definition", len(genus) + 1, len(kern))
    return genus_ref, [{"id": "F1", "evidence": kenmerk}]


def migreer(
    oordeel: Mapping[str, Any],
    materiaal: Mapping[str, str],
    buren: Sequence[Buur],
) -> dict[str, Any]:
    """Het /2-conceptoordeel bij één letterlijk /1-oordeel (zie moduledocstring)."""
    _controleer_vorm(oordeel)
    bewijs = _Bewijs(materiaal)
    volledig = [bewijs.plaats(m, 0, len(t)) for m, t in materiaal.items() if t]
    claims: list[dict[str, Any]] = []

    def claim(tekst: Any) -> str | None:
        if tekst is None:
            return None
        if not isinstance(tekst, str) or not tekst.strip():
            msg = "een claimtekst is leeg of geen tekst"
            raise MigratiefoutError(msg)
        ref = f"C{len(claims) + 1}"
        claims.append(
            {
                "id": ref,
                "role": "material",
                "text": tekst,
                "evidence": list(volledig),
                "premises": [],
            }
        )
        return ref

    reden = claim(oordeel["reason"])
    genus_ref, kenmerken = _kern_en_bovenbegrip(
        oordeel, bewijs, materiaal.get("definition", "")
    )
    buurconcepten = []
    for buur in oordeel["neighbours"]:
        onderscheid = buur["distinction"]
        citaat = buur["distinguishing_feature_quote"]
        if onderscheid == "distinguished" and buur["missing_feature"] is not None:
            msg = f"{buur['neighbour_id']}: distinguished met missing_feature"
            raise MigratiefoutError(msg)
        if onderscheid != "distinguished" and citaat is not None:
            msg = f"{buur['neighbour_id']}: citaat bij {onderscheid}"
            raise MigratiefoutError(msg)
        buurconcepten.append(
            {
                "neighbour_id": buur["neighbour_id"],
                "distinction": onderscheid,
                "feature_evidence": (
                    bewijs.uniek_in_kern(citaat, "onderscheidend citaat")
                    if onderscheid == "distinguished"
                    else None
                ),
                "reason_claims": [claim(buur["reason"])],
                "missing_feature_claim": claim(buur["missing_feature"]),
                "uncertainty_claim": claim(buur["uncertainty"]),
            }
        )
    vraag = oordeel["question"]
    concept = {
        "schema_version": CONCEPTSCHEMA,
        "genus_evidence": genus_ref,
        "core_features": kenmerken,
        "evidence": bewijs.items,
        "claims": claims,
        "reason_claims": [reden],
        "neighbours": buurconcepten,
        "proposals": [],
        "question": None if vraag is None else {"text": vraag, "claims": []},
    }
    gevalideerd, fouten = valideer_concept(concept, materiaal, buren)
    if gevalideerd is None:
        msg = f"gemigreerd concept voldoet niet aan {CONCEPTSCHEMA}: {fouten}"
        raise MigratiefoutError(msg)
    return concept


def foutdragende_items(
    concept: Mapping[str, Any], spec: Mapping[str, Any]
) -> list[str]:
    """De voorgestelde foutdragende verplichte controles bij een fout item."""
    items: list[str] = []
    for fragment in spec["claims_met"]:
        treffers = [c["id"] for c in concept["claims"] if fragment in c["text"]]
        if len(treffers) != 1:
            msg = f"fragment {fragment!r} wijst niet precies één claim aan: {treffers}"
            raise MigratiefoutError(msg)
        items.append(f"claim:{treffers[0]}")
    items.extend(spec["items"])
    from domain.ess05.bewijs import Ess05Concept

    verplicht = set(verplichte_controles(Ess05Concept(concept)))
    vreemd = [i for i in items if i not in verplicht]
    if vreemd or not items:
        msg = f"foutdragend item(s) {vreemd or items} is geen verplichte controle"
        raise MigratiefoutError(msg)
    return items


def _lees_bron(r7_map: Path, bron: Mapping[str, Any]) -> dict[str, Any]:
    pad = Path(r7_map) / bron["callrecord"]
    record = json.loads(pad.read_text(encoding="utf-8"))
    ruw = record.get("ruw_antwoord")
    if not isinstance(ruw, str) or _sha(ruw) != bron["ruw_sha256"]:
        msg = f"{bron['id']}: ruw antwoord wijkt af van de vastgelegde hash"
        raise MigratiefoutError(msg)
    if (record.get("sleutel"), record.get("seq")) != (bron["sleutel"], bron["seq"]):
        msg = f"{bron['id']}: sleutel of seq wijkt af"
        raise MigratiefoutError(msg)
    return {"record": record, "ruw": ruw, "bestand_sha256": _sha(pad.read_bytes())}


def _verificatieprompt(
    concept: Mapping[str, Any], regels: str, norm: Mapping[str, str]
) -> tuple[str, str]:
    from domain.ess05.bewijs import Ess05Concept
    from services.validation.ess05_assessment_service import _TOETSINSTRUCTIE
    from services.validation.ess05_verification_service import bouw_verificatieprompt

    return bouw_verificatieprompt(
        regels, Ess05Concept(concept), norm=norm, toetsinstructie=_TOETSINSTRUCTIE
    )


def invoeritem(
    item_id: str,
    soort: str,
    geval: Mapping[str, Any],
    concept: Mapping[str, Any],
    foutdragend: Sequence[str],
    bron: Mapping[str, Any],
    norm: Mapping[str, str],
) -> dict[str, Any]:
    """Eén verifier-only-item met geval-, materiaal-, concept- en promptbinding."""
    from domain.ess05.bewijs import Ess05Concept

    materiaal, buren, regels = verificatiemateriaal(geval, norm)
    gevalideerd, fouten = valideer_concept(dict(concept), materiaal, buren)
    if gevalideerd is None:
        msg = f"{item_id}: concept voldoet niet aan {CONCEPTSCHEMA}: {fouten}"
        raise MigratiefoutError(msg)
    system, user = _verificatieprompt(concept, regels, norm)
    return {
        "id": item_id,
        "soort": soort,
        "bron": dict(bron),
        "geval": dict(geval),
        "geval_sha256": pi.sha_json(geval),
        "materiaal_sha256": {m: _sha(t) for m, t in materiaal.items()},
        "concept": dict(concept),
        "concept_hash": Ess05Concept(dict(concept)).hash,
        "verplichte_controles": list(verplichte_controles(gevalideerd)),
        "foutdragende_items": list(foutdragend),
        "verificatieprompt_sha256": _sha(system + "\n␞\n" + user),
    }


def maak_verificatie_invoer(r7_map: Path = R7_MAP) -> dict[str, Any]:
    """De bevroren verifier-only-invoer: zes items met bron-, geval- en conceptbinding."""
    from services.validation.ess05_assessment_service import laad_ess05_norm

    eindset_bytes = (Path(r7_map) / R7_EINDSET).read_bytes()
    if _sha(eindset_bytes) != R7_EINDSET_SHA256:
        msg = "R7-eindset wijkt af van de vastgelegde hash"
        raise MigratiefoutError(msg)
    gevallen = {g["id"]: g for g in json.loads(eindset_bytes)["gevallen"]}
    norm = laad_ess05_norm()
    items = []
    for bron in BRONNEN:
        gelezen = _lees_bron(r7_map, bron)
        record = gelezen["record"]
        geval = gevallen[record["geval_id"]]
        if pi.sha_json(geval) != record.get("geval_sha256"):
            msg = f"{bron['id']}: geval {geval['id']} wijkt af van het callrecord"
            raise MigratiefoutError(msg)
        materiaal, buren, _ = verificatiemateriaal(geval, norm)
        concept = migreer(json.loads(gelezen["ruw"]), materiaal, buren)
        items.append(
            invoeritem(
                bron["id"],
                bron["soort"],
                geval,
                concept,
                (
                    foutdragende_items(concept, bron["foutdragend"])
                    if bron["foutdragend"]
                    else []
                ),
                {
                    "callrecord": f"reports/{Path(r7_map).name}/{bron['callrecord']}",
                    "callrecord_sha256": gelezen["bestand_sha256"],
                    "sleutel": bron["sleutel"],
                    "seq": bron["seq"],
                    "ruw_antwoord": gelezen["ruw"],
                    "ruw_antwoord_sha256": bron["ruw_sha256"],
                },
                norm,
            )
        )
    return {
        "schema": INVOERSCHEMA,
        "status": (
            "migratiebewijs voor de verifier-only-fase; foutdragende items zijn een "
            "voorstel voor de trouwreview, geen vastgesteld oordeel"
        ),
        "herkomst": {
            "r7_eindset": {
                "pad": f"reports/{Path(r7_map).name}/{R7_EINDSET}",
                "sha256": R7_EINDSET_SHA256,
            },
            "migratieregels": "scripts/ess05/migreer_r7_naar_v2.py (moduledocstring)",
            "auteur": AUTEUR,
        },
        "items": items,
    }


def controlelijst(invoer: Mapping[str, Any]) -> str:
    """Markdown voor de trouwreview: bron, gemigreerde claims en foutdragers."""
    regels = [
        "# DEF-768 R8 — controlelijst migratie /1 → /2 (trouwreview)",
        "",
        (
            f"Invoerschema `{invoer['schema']}`; R7-eindset "
            f"`{invoer['herkomst']['r7_eindset']['sha256']}`."
        ),
        "",
        "Te toetsen per item (alle vakjes nodig vóór bevriezing):",
        "",
        "- [ ] elke claimtekst is letterlijk en ongesplitst uit het R7-antwoord;",
        "- [ ] bovenbegrip, kenmerk en citaat zijn de bedoelde kernfragmenten;",
        "- [ ] labels (distinction, lacks_differentia) zijn ongewijzigd;",
        (
            "- [ ] bij V-N: de foutdragende items dragen de bekende fout; bij V-P: "
            "geen bekende fout;"
        ),
        "- [ ] goede en foute items volgen dezelfde regels (geen extra informatie).",
        "",
    ]
    for item in invoer["items"]:
        concept = item["concept"]
        bewijs = {e["id"]: e for e in concept["evidence"]}
        regels += [
            f"## {item['id']} ({item['soort']}) — {item['bron']['sleutel']}",
            "",
            (
                f"- callrecord `{item['bron']['callrecord']}` "
                f"(sha256 `{item['bron']['callrecord_sha256']}`)"
            ),
            f"- ruw antwoord sha256 `{item['bron']['ruw_antwoord_sha256']}`",
            f"- concepthash `{item['concept_hash']}`",
            f"- verificatieprompt sha256 `{item['verificatieprompt_sha256']}`",
            f"- foutdragend (voorstel): {item['foutdragende_items'] or 'geen'}",
            "",
            "Kernfragmenten:",
            "",
        ]
        fragmenten = [("genus_evidence", concept["genus_evidence"])]
        fragmenten += [
            (f"feature:{k['id']}", k["evidence"]) for k in concept["core_features"]
        ]
        fragmenten += [
            (f"neighbour:{b['neighbour_id']}", b["feature_evidence"])
            for b in concept["neighbours"]
        ]
        for naam, ref in fragmenten:
            if ref is None:
                regels.append(f"- {naam}: geen")
                continue
            e = bewijs[ref]
            regels.append(
                f"- {naam}: {ref} = definition[{e['start']}:{e['end']}] “{e['quote']}”"
            )
        regels += ["", "Claims (letterlijk):", ""]
        regels += [f"- {c['id']}: {c['text']}" for c in concept["claims"]]
        vraag = concept["question"]
        regels += [
            "",
            (
                "Buurlabels: "
                + ", ".join(
                    f"{b['neighbour_id']}={b['distinction']}"
                    for b in concept["neighbours"]
                )
                if concept["neighbours"]
                else "Buurlabels: geen buren"
            ),
            f"Vraag (letterlijk): {vraag['text']}" if vraag else "Vraag: geen",
            "",
            "- [ ] trouw bevestigd door: ______",
            "",
        ]
    return "\n".join(regels)


def _schrijf(doel: Path, tekst: str) -> str:
    doel.parent.mkdir(parents=True, exist_ok=True)
    with doel.open("x", encoding="utf-8") as f:
        f.write(tekst)
    return _sha(tekst)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--doel", type=Path, default=DOEL)
    p.add_argument("--controlelijst", type=Path, default=CONTROLELIJST)
    p.add_argument(
        "--alleen-controlelijst",
        action="store_true",
        help="lees de bestaande invoer (--doel) en schrijf alleen een nieuwe controlelijst",
    )
    args = p.parse_args(argv)
    if args.alleen_controlelijst:
        if args.controlelijst.exists():
            msg = f"doel bestaat al: {args.controlelijst}"
            raise FileExistsError(msg)
        invoer = json.loads(args.doel.read_text(encoding="utf-8"))
        lijst_sha = _schrijf(args.controlelijst, controlelijst(invoer) + "\n")
        sys.stdout.write(f"{args.controlelijst} sha256={lijst_sha}\n")
        return 0
    for pad in (args.doel, args.controlelijst):
        if pad.exists():
            msg = f"doel bestaat al: {pad}"
            raise FileExistsError(msg)
    invoer = maak_verificatie_invoer()
    sha = _schrijf(args.doel, json.dumps(invoer, ensure_ascii=False, indent=2) + "\n")
    lijst_sha = _schrijf(args.controlelijst, controlelijst(invoer) + "\n")
    sys.stdout.write(f"{args.doel} sha256={sha}\n")
    sys.stdout.write(f"{args.controlelijst} sha256={lijst_sha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
