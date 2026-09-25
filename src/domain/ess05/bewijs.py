"""ESS-05 `/2` — gesloten bewijscontract en verificatiedekking (DEF-768, ADR-003).

Pure domeinlogica, zonder Streamlit, database of AI-client. Specificatie:
`docs/adr/ADR-003-ess05-gestructureerde-bewijscontrole-v1.md` (optie C).

Een beoordeling verloopt in twee stappen:

1. Het model levert een **conceptoordeel** in een gesloten structuur:
   kernkenmerken, bewijsplaatsen (materiaal-ID, materiaalhash, begin/eind,
   citaat), claims met een rol, buuroordelen, voorstellen en hoogstens één
   vraag. `valideer_concept` controleert wat vaste code kan controleren:
   schema, unieke ID's, verwijzingen, claimrollen, exacte bewijsplaatsen en de
   bestaande labelregels. `lacks_differentia` levert het model niet meer; het
   volgt uit de kenmerkenlijst (leeg → true).
2. Een afzonderlijke verifier geeft per verplicht controle-item
   `supported`/`unsupported`/`undetermined`. `toets_verificatie` eist exact de
   verplichte, unieke dekking en de juiste kandidaat-hash; alleen alles
   `supported` geeft vrijgave.

Het model levert het concept als **antwoord** (`ANTWOORDSCHEMA`): dezelfde
gesloten structuur, maar per bewijsplaats alleen materiaal-ID, materiaalhash
en het exacte citaat. `valideer_antwoord` leidt begin en eind af, uitsluitend
bij precies één letterlijke treffer in het aangewezen materiaal (R8-offset-
herstel: tekens tellen door het model is geen betrouwbare basis). Het
resultaat is een gewoon `CONCEPTSCHEMA`-concept; een antwoord in een ander
schema, met posities, of met een niet-letterlijk, dubbelzinnig of aan ander
materiaal ontleend citaat wordt geweigerd, nooit gerepareerd.

Grens: een bestaand citaat bewijst geen dragende gevolgtrekking. Deze module
claimt geen semantische juistheid; dat oordeel ligt bij de verifier.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from html import unescape
from typing import Any

__all__ = [
    "ANTWOORDSCHEMA",
    "CONCEPTSCHEMA",
    "RENDERERVERSIE",
    "ROLLEN",
    "UITKOMSTEN",
    "VERIFICATIESCHEMA",
    "Ess05Concept",
    "Verificatieuitkomst",
    "concepthash",
    "toets_verificatie",
    "valideer_antwoord",
    "valideer_concept",
    "verplichte_controles",
]

#: Versie van het gesloten conceptschema (eerste stap).
CONCEPTSCHEMA = "ess05-concept/1"
#: Versie van het modelantwoord van de eerste stap: bewijsplaatsen zonder
#: posities; de app leidt ze af (`valideer_antwoord`).
ANTWOORDSCHEMA = "ess05-answer/1"
#: Versie van het gesloten verificatieschema (tweede stap).
VERIFICATIESCHEMA = "ess05-verification/1"
#: Versie van de vaste weergave van gecontroleerde claims.
RENDERERVERSIE = "ess05-render/1"

ROL_MATERIAAL = "material"
ROL_GEVOLGTREKKING = "inference"
ROL_AFWEZIGHEID = "absence_in_supplied_material"
ROLLEN: tuple[str, ...] = (ROL_MATERIAAL, ROL_GEVOLGTREKKING, ROL_AFWEZIGHEID)

UITKOMSTEN: tuple[str, ...] = ("supported", "unsupported", "undetermined")
_ONDERSCHEIDINGEN = ("distinguished", "not_distinguished", "unclear")

_DEFINITIE = "definition"
_BRONPREFIX = "source:"
_BUURPREFIX = "neighbour:"

_CONCEPTVELDEN = frozenset(
    {
        "schema_version",
        "genus_evidence",
        "core_features",
        "evidence",
        "claims",
        "reason_claims",
        "neighbours",
        "proposals",
        "question",
    }
)
_BEWIJSVELDEN = frozenset(
    {"id", "material_id", "material_sha256", "start", "end", "quote"}
)
_ANTWOORDBEWIJSVELDEN = frozenset({"id", "material_id", "material_sha256", "quote"})
_KENMERKVELDEN = frozenset({"id", "evidence"})
_CLAIMVELDEN = frozenset({"id", "role", "text", "evidence", "premises"})
_BUURVELDEN = frozenset(
    {
        "neighbour_id",
        "distinction",
        "feature_evidence",
        "reason_claims",
        "missing_feature_claim",
        "uncertainty_claim",
    }
)
_VOORSTELVELDEN = frozenset({"id", "term", "source_evidence", "reason_claims"})
_VRAAGVELDEN = frozenset({"text", "claims"})
_VERIFICATIEVELDEN = frozenset({"schema_version", "candidate_hash", "checks"})
_CONTROLEVELDEN = frozenset({"item", "outcome", "finding"})

_LABELS = {
    _DEFINITIE: "definitie",
    "context": "context",
    "meaning": "bedoelde betekenis",
}


def _tekst(waarde: Any) -> str:
    return waarde.strip() if isinstance(waarde, str) else ""


def _sha256(tekst: str) -> str:
    return hashlib.sha256(str(tekst).encode("utf-8")).hexdigest()


def concepthash(ruw: Any) -> str:
    """Canonieke sha256 van een conceptoordeel (sleutelvolgorde telt niet)."""
    return _sha256(
        json.dumps(ruw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _is_een_gerichte_vraag(waarde: Any) -> bool:
    vraag = _tekst(waarde)
    return bool(vraag) and vraag.endswith("?") and vraag.count("?") == 1


def _is_positie(waarde: Any) -> bool:
    return isinstance(waarde, int) and not isinstance(waarde, bool)


def _is_idlijst(waarde: Any) -> bool:
    return isinstance(waarde, list) and all(_tekst(v) for v in waarde)


def _optioneel_id(waarde: Any) -> bool:
    return waarde is None or bool(_tekst(waarde))


def _exacte_velden(item: Any, velden: frozenset[str], pad: str) -> str | None:
    if not isinstance(item, Mapping):
        return f"{pad} is geen object"
    if set(item) != velden:
        onbekend = sorted(set(item) - velden)
        ontbrekend = sorted(velden - set(item))
        return (
            f"{pad} heeft niet exact de afgesproken velden "
            f"(onbekend: {onbekend}, ontbrekend: {ontbrekend})"
        )
    return None


def _eerste(fouten: Iterable[tuple[Callable[[], bool], str]]) -> str | None:
    for faalt, melding in fouten:
        if faalt():
            return melding
    return None


def _lijstfout(
    items: Any,
    velden: frozenset[str],
    pad: str,
    veldfout: Callable[[Any, str], str | None],
) -> str | None:
    if not isinstance(items, list):
        return f"{pad} moet een lijst zijn"
    for index, item in enumerate(items):
        eigen = f"{pad}[{index}]"
        fout = _exacte_velden(item, velden, eigen) or veldfout(item, eigen)
        if fout:
            return fout
    return None


# --- veldtypen per onderdeel -----------------------------------------------------------


def _bewijsveldfout(item: Mapping[str, Any], pad: str) -> str | None:
    return _eerste(
        (
            (lambda: not _tekst(item["id"]), f"{pad}.id ontbreekt"),
            (lambda: not _tekst(item["material_id"]), f"{pad}.material_id ontbreekt"),
            (
                lambda: not _tekst(item["material_sha256"]),
                f"{pad}.material_sha256 ontbreekt",
            ),
            (
                lambda: not _is_positie(item["start"]) or not _is_positie(item["end"]),
                f"{pad}: start en end zijn gehele getallen",
            ),
            (
                lambda: not isinstance(item["quote"], str) or not item["quote"],
                f"{pad}.quote ontbreekt",
            ),
        )
    )


def _kenmerkveldfout(item: Mapping[str, Any], pad: str) -> str | None:
    if not _tekst(item["id"]) or not _tekst(item["evidence"]):
        return f"{pad}: id en evidence zijn verplicht"
    return None


def _claimveldfout(item: Mapping[str, Any], pad: str) -> str | None:
    return _eerste(
        (
            (lambda: not _tekst(item["id"]), f"{pad}.id ontbreekt"),
            (
                lambda: item["role"] not in ROLLEN,
                f"{pad}: onbekende role {item['role']!r}",
            ),
            (lambda: not _tekst(item["text"]), f"{pad}.text ontbreekt"),
            (
                lambda: not _is_idlijst(item["evidence"])
                or not _is_idlijst(item["premises"]),
                f"{pad}: evidence en premises zijn lijsten van ID's",
            ),
        )
    )


def _buurveldfout(item: Mapping[str, Any], pad: str) -> str | None:
    return _eerste(
        (
            (lambda: not _tekst(item["neighbour_id"]), f"{pad}.neighbour_id ontbreekt"),
            (
                lambda: item["distinction"] not in _ONDERSCHEIDINGEN,
                f"{pad}: onbekende distinction {item['distinction']!r}",
            ),
            (
                lambda: not _is_idlijst(item["reason_claims"])
                or not item["reason_claims"],
                f"{pad}: reason_claims is een niet-lege lijst van claim-ID's",
            ),
            (
                lambda: not all(
                    _optioneel_id(item[v])
                    for v in (
                        "feature_evidence",
                        "missing_feature_claim",
                        "uncertainty_claim",
                    )
                ),
                (
                    f"{pad}: feature_evidence, missing_feature_claim en "
                    "uncertainty_claim zijn een ID of null"
                ),
            ),
        )
    )


def _voorstelveldfout(item: Mapping[str, Any], pad: str) -> str | None:
    return _eerste(
        (
            (lambda: not _tekst(item["id"]), f"{pad}.id ontbreekt"),
            (lambda: not _tekst(item["term"]), f"{pad}.term ontbreekt"),
            (
                lambda: not _optioneel_id(item["source_evidence"]),
                f"{pad}.source_evidence is een ID of null",
            ),
            (
                lambda: not _is_idlijst(item["reason_claims"])
                or not item["reason_claims"],
                f"{pad}: reason_claims is een niet-lege lijst van claim-ID's",
            ),
        )
    )


def _vraagfout(vraag: Any) -> str | None:
    if vraag is None:
        return None
    return _exacte_velden(vraag, _VRAAGVELDEN, "question") or _eerste(
        (
            (
                lambda: not _is_een_gerichte_vraag(vraag["text"]),
                "question.text is precies één gerichte vraag",
            ),
            (
                lambda: not _is_idlijst(vraag["claims"]),
                "question.claims is een lijst van claim-ID's",
            ),
        )
    )


def _vormfout(ruw: Any) -> str | None:
    """Schema, typen en gesloten velden, nog zonder onderlinge verwijzingen."""
    fout = _exacte_velden(ruw, _CONCEPTVELDEN, "concept")
    if fout:
        return fout
    return (
        _eerste(
            (
                (
                    lambda: ruw["schema_version"] != CONCEPTSCHEMA,
                    f"schema_version moet {CONCEPTSCHEMA!r} zijn",
                ),
                (
                    lambda: not _optioneel_id(ruw["genus_evidence"]),
                    "genus_evidence is een ID of null",
                ),
                (
                    lambda: not _is_idlijst(ruw["reason_claims"])
                    or not ruw["reason_claims"],
                    "reason_claims is een niet-lege lijst van claim-ID's",
                ),
            )
        )
        or _lijstfout(ruw["evidence"], _BEWIJSVELDEN, "evidence", _bewijsveldfout)
        or _lijstfout(ruw["claims"], _CLAIMVELDEN, "claims", _claimveldfout)
        or _lijstfout(
            ruw["core_features"], _KENMERKVELDEN, "core_features", _kenmerkveldfout
        )
        or _lijstfout(ruw["neighbours"], _BUURVELDEN, "neighbours", _buurveldfout)
        or _lijstfout(ruw["proposals"], _VOORSTELVELDEN, "proposals", _voorstelveldfout)
        or _vraagfout(ruw["question"])
    )


# --- onderlinge verwijzingen -----------------------------------------------------------


@dataclass(frozen=True)
class _Index:
    bewijs: Mapping[str, Mapping[str, Any]]
    claims: Mapping[str, Mapping[str, Any]]
    claimvolgorde: Mapping[str, int]


def _index(ruw: Mapping[str, Any]) -> tuple[_Index | None, str | None]:
    ids = (
        [e["id"] for e in ruw["evidence"]]
        + [c["id"] for c in ruw["claims"]]
        + [k["id"] for k in ruw["core_features"]]
        + [p["id"] for p in ruw["proposals"]]
    )
    if len(ids) != len(set(ids)):
        return None, "ID's van bewijs, claims, kenmerken en voorstellen zijn niet uniek"
    return (
        _Index(
            bewijs={e["id"]: e for e in ruw["evidence"]},
            claims={c["id"]: c for c in ruw["claims"]},
            claimvolgorde={c["id"]: i for i, c in enumerate(ruw["claims"])},
        ),
        None,
    )


def _bewijsref(index: _Index, ref: Any, pad: str, prefix: str | None) -> str | None:
    """Verwijzing naar bestaand bewijs, desgewenst uit een bepaalde materiaalsoort."""
    if ref is None:
        return None
    if ref not in index.bewijs:
        return f"{pad}: onbekende bewijsplaats {ref!r}"
    locatie = index.bewijs[ref]["material_id"]
    if prefix == _DEFINITIE and locatie != _DEFINITIE:
        return f"{pad}: bewijsplaats {ref!r} komt niet uit de definitiekern"
    if prefix == _BRONPREFIX and not str(locatie).startswith(_BRONPREFIX):
        return f"{pad}: bewijsplaats {ref!r} komt niet uit een aangeleverde bron"
    return None


def _claimrefs(index: _Index, refs: Iterable[Any], pad: str) -> str | None:
    for ref in refs:
        if ref not in index.claims:
            return f"{pad}: onbekende claim {ref!r}"
    return None


def _claimrolfout(index: _Index, claim: Mapping[str, Any]) -> str | None:
    pad = f"claim {claim['id']!r}"
    rol, bewijs, premissen = claim["role"], claim["evidence"], claim["premises"]
    for ref in bewijs:
        fout = _bewijsref(index, ref, pad, None)
        if fout:
            return fout
    if rol == ROL_MATERIAAL:
        if not bewijs or premissen:
            return f"{pad}: een materiaalclaim verwijst naar bewijs, zonder premissen"
        return None
    if rol == ROL_GEVOLGTREKKING:
        eigen = index.claimvolgorde[claim["id"]]
        if bewijs or not premissen:
            return f"{pad}: een gevolgtrekking heeft premissen en geen eigen citaat"
        for ref in premissen:
            if index.claimvolgorde.get(ref, eigen) >= eigen:
                return f"{pad}: premisse {ref!r} is geen eerdere claim"
        return None
    if bewijs or premissen:
        return (
            f"{pad}: een afwezigheidsclaim verwijst naar het volledige materiaal, "
            "zonder citaat of premissen"
        )
    return None


def _buurlabelfout(
    item: Mapping[str, Any], buren: Mapping[str, str | None]
) -> str | None:
    pad = f"neighbour {item['neighbour_id']!r}"
    onderscheid = item["distinction"]
    fragment = item["feature_evidence"]
    ontbrekend = item["missing_feature_claim"]
    return _eerste(
        (
            (
                lambda: item["neighbour_id"] not in buren,
                f"{pad}: onbekende neighbour_id",
            ),
            (
                lambda: onderscheid == "distinguished"
                and (fragment is None or ontbrekend is not None),
                f"{pad}: distinguished vereist een kernfragment en geen missing_feature",
            ),
            (
                lambda: onderscheid == "not_distinguished"
                and (fragment is not None or ontbrekend is None),
                f"{pad}: not_distinguished vereist missing_feature en geen kernfragment",
            ),
            (
                lambda: onderscheid == "unclear" and fragment is not None,
                f"{pad}: unclear heeft geen kernfragment",
            ),
            (
                lambda: not _tekst(buren.get(item["neighbour_id"]))
                and onderscheid != "unclear",
                f"{pad}: een buur zonder beschrijving kan alleen unclear zijn",
            ),
        )
    )


def _buurfout(
    index: _Index, item: Mapping[str, Any], buren: Mapping[str, str | None]
) -> str | None:
    pad = f"neighbour {item['neighbour_id']!r}"
    losse_claims = [
        c for c in (item["missing_feature_claim"], item["uncertainty_claim"]) if c
    ]
    return (
        _buurlabelfout(item, buren)
        or _bewijsref(index, item["feature_evidence"], pad, _DEFINITIE)
        or _claimrefs(index, [*item["reason_claims"], *losse_claims], pad)
    )


def _gebruikte_ids(ruw: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    """(gebruikte bewijsplaatsen, gebruikte claims) over het hele concept."""
    bewijs = {k["evidence"] for k in ruw["core_features"]}
    bewijs.update(e for c in ruw["claims"] for e in c["evidence"])
    if ruw["genus_evidence"]:
        bewijs.add(ruw["genus_evidence"])
    claims = set(ruw["reason_claims"])
    claims.update(p for c in ruw["claims"] for p in c["premises"])
    for buur in ruw["neighbours"]:
        if buur["feature_evidence"]:
            bewijs.add(buur["feature_evidence"])
        claims.update(buur["reason_claims"])
        claims.update(
            c for c in (buur["missing_feature_claim"], buur["uncertainty_claim"]) if c
        )
    for voorstel in ruw["proposals"]:
        if voorstel["source_evidence"]:
            bewijs.add(voorstel["source_evidence"])
        claims.update(voorstel["reason_claims"])
    if ruw["question"] is not None:
        claims.update(ruw["question"]["claims"])
    return bewijs, claims


def _verwijzingsfout(
    ruw: Mapping[str, Any], buren: Mapping[str, str | None]
) -> str | None:
    index, fout = _index(ruw)
    if index is None:
        return fout
    for claim in ruw["claims"]:
        fout = _claimrolfout(index, claim)
        if fout:
            return fout
    fout = _bewijsref(index, ruw["genus_evidence"], "genus_evidence", _DEFINITIE)
    for kenmerk in ruw["core_features"]:
        fout = fout or _bewijsref(
            index, kenmerk["evidence"], f"core_feature {kenmerk['id']!r}", _DEFINITIE
        )
    fout = fout or _claimrefs(index, ruw["reason_claims"], "reason_claims")
    for buur in ruw["neighbours"]:
        fout = fout or _buurfout(index, buur, buren)
    for voorstel in ruw["proposals"]:
        pad = f"proposal {voorstel['id']!r}"
        fout = (
            fout
            or _bewijsref(index, voorstel["source_evidence"], pad, _BRONPREFIX)
            or _claimrefs(index, voorstel["reason_claims"], pad)
        )
    if ruw["question"] is not None:
        fout = fout or _claimrefs(index, ruw["question"]["claims"], "question")
    return fout or _samenhangfout(ruw, buren, index)


def _samenhangfout(
    ruw: Mapping[str, Any], buren: Mapping[str, str | None], index: _Index
) -> str | None:
    ids = [b["neighbour_id"] for b in ruw["neighbours"]]
    bewijs, claims = _gebruikte_ids(ruw)
    return _eerste(
        (
            (
                lambda: len(ids) != len(set(ids)) or set(ids) != set(buren),
                "elke verzonden buur moet precies één keer beoordeeld zijn",
            ),
            (
                lambda: not ruw["core_features"]
                and any(b["distinction"] == "distinguished" for b in ruw["neighbours"]),
                "een lege kenmerkenlijst strookt niet met een onderscheiden buur",
            ),
            (
                lambda: set(index.bewijs) - bewijs,
                f"ongebruikte bewijsplaats(en): {sorted(set(index.bewijs) - bewijs)}",
            ),
            (
                lambda: set(index.claims) - claims,
                f"ongebruikte claim(s): {sorted(set(index.claims) - claims)}",
            ),
        )
    )


# --- bewijsplaatsen tegen het gebonden materiaal ---------------------------------------


def _zelfde_definitie(a: str | None, b: str | None) -> bool:
    """Volledig gelijke definities, ongeacht witruimte, hoofdletters en slotpunt."""

    def vorm(tekst: str | None) -> str:
        return " ".join(str(tekst or "").split()).casefold().rstrip(" .")

    return bool(vorm(a)) and vorm(a) == vorm(b)


def _plaatsfout(item: Mapping[str, Any], materiaal: Mapping[str, str]) -> str | None:
    tekst = materiaal.get(item["material_id"])
    if tekst is None:
        return "onbekend materiaal"
    if item["material_sha256"] != _sha256(tekst):
        return "materiaalhash wijkt af"
    start, eind = item["start"], item["end"]
    if not 0 <= start < eind <= len(tekst):
        return "bewijsplaats buiten bereik"
    if tekst[start:eind] != item["quote"]:
        return "citaat wijkt af van de bewijsplaats"
    return None


def _bewijsfouten(
    ruw: Mapping[str, Any],
    materiaal: Mapping[str, str],
    buren: Mapping[str, str | None],
) -> list[dict[str, Any]]:
    fouten: list[dict[str, Any]] = []
    for item in ruw["evidence"]:
        reden = _plaatsfout(item, materiaal)
        if reden:
            fouten.append(
                {"reason": reden, "detail": f"{item['id']}: {item['quote'][:120]}"}
            )
    kern = materiaal.get(_DEFINITIE, "")
    for buur in ruw["neighbours"]:
        if buur["distinction"] == "distinguished" and _zelfde_definitie(
            kern, buren.get(buur["neighbour_id"])
        ):
            fouten.append(
                {
                    "reason": "kern gelijk aan de buurdefinitie",
                    "detail": buur["neighbour_id"],
                }
            )
    return fouten


# --- het gevalideerde concept ----------------------------------------------------------


def _label(locatie: str) -> str:
    if locatie in _LABELS:
        return _LABELS[locatie]
    if locatie.startswith(_BRONPREFIX):
        return f"bron {locatie.removeprefix(_BRONPREFIX)}"
    if locatie.startswith(_BUURPREFIX):
        return "beschrijving verwant begrip"
    return locatie


def _zin(tekst: str) -> str:
    schoon = _tekst(tekst)
    return schoon if schoon.endswith((".", "!", "?")) else f"{schoon}."


@dataclass(frozen=True)
class Ess05Concept:
    """Een conceptoordeel dat de vaste controles doorstond — nog níet geverifieerd.

    Alleen `contract.pas_verificatie_toe` maakt er na volledige, positieve
    verificatie een toepasbaar oordeel van; tot dan is het nooit een geldige
    motivering.
    """

    data: Mapping[str, Any]

    @property
    def hash(self) -> str:
        return concepthash(self.data)

    @property
    def lacks_differentia(self) -> bool:
        return not self.data["core_features"]

    def als_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.data))

    def _bewijs(self, ref: str) -> Mapping[str, Any]:
        return next(e for e in self.data["evidence"] if e["id"] == ref)

    def citaat(self, ref: str | None) -> str | None:
        return self._bewijs(ref)["quote"] if ref else None

    def bron_van(self, ref: str | None) -> str | None:
        if not ref:
            return None
        return str(self._bewijs(ref)["material_id"]).removeprefix(_BRONPREFIX)

    def claimtekst(self, refs: Iterable[str]) -> str:
        """Vaste weergave van gecontroleerde claims, zonder vrije tussentekst."""
        per_id = {c["id"]: c for c in self.data["claims"]}
        delen: list[str] = []
        for ref in refs:
            claim = per_id[ref]
            if claim["role"] == ROL_GEVOLGTREKKING:
                delen.append(f"Gevolgtrekking: {_zin(claim['text'])}")
            elif claim["role"] == ROL_AFWEZIGHEID:
                delen.append(
                    f"Niet in het aangeleverde materiaal: {_zin(claim['text'])}"
                )
            else:
                plaatsen = "; ".join(
                    f"{_label(self._bewijs(e)['material_id'])}: “{self._bewijs(e)['quote']}”"
                    for e in claim["evidence"]
                )
                delen.append(f"{_zin(claim['text'])} [{plaatsen}]")
        return " ".join(delen)


def valideer_concept(
    ruw: Any,
    materiaal: Mapping[str, str],
    buren: Mapping[str, str | None],
) -> tuple[Ess05Concept | None, list[dict[str, Any]]]:
    """(concept, []) of (None, fouten). Fail-closed; geen reparatie.

    `buren` is {neighbour_id: beschrijving of None} van de verzonden buren.
    De eerste fout heeft `reason == "structuurfout"` bij een schema- of
    verwijzingsfout; anders is het een niet-verifieerbare bewijsplaats.
    """
    fout = _vormfout(ruw) or _verwijzingsfout(ruw, buren)
    if fout is not None:
        return None, [{"reason": "structuurfout", "detail": fout}]
    fouten = _bewijsfouten(ruw, materiaal, buren)
    if fouten:
        return None, fouten
    return Ess05Concept(deepcopy(dict(ruw))), []


# --- het modelantwoord: bewijsplaatsen afleiden ------------------------------------------


def _antwoordbewijsveldfout(item: Mapping[str, Any], pad: str) -> str | None:
    return _eerste(
        (
            (lambda: not _tekst(item["id"]), f"{pad}.id ontbreekt"),
            (lambda: not _tekst(item["material_id"]), f"{pad}.material_id ontbreekt"),
            (
                lambda: not _tekst(item["material_sha256"]),
                f"{pad}.material_sha256 ontbreekt",
            ),
            (
                lambda: not isinstance(item["quote"], str) or not item["quote"],
                f"{pad}.quote ontbreekt",
            ),
        )
    )


def _antwoordvormfout(antwoord: Any) -> str | None:
    """Alleen wat het antwoord van het concept onderscheidt: schema en bewijsvelden."""
    fout = _exacte_velden(antwoord, _CONCEPTVELDEN, "antwoord")
    if fout:
        return fout
    if antwoord["schema_version"] != ANTWOORDSCHEMA:
        return f"schema_version moet {ANTWOORDSCHEMA!r} zijn"
    return _lijstfout(
        antwoord["evidence"],
        _ANTWOORDBEWIJSVELDEN,
        "evidence",
        _antwoordbewijsveldfout,
    )


def _treffers(tekst: str, citaat: str) -> list[int]:
    """Alle beginposities van `citaat` in `tekst`, ook overlappende."""
    posities: list[int] = []
    positie = tekst.find(citaat)
    while positie != -1:
        posities.append(positie)
        positie = tekst.find(citaat, positie + 1)
    return posities


def _plaatsbepaling(
    item: Mapping[str, Any], materiaal: Mapping[str, str]
) -> tuple[int | None, str | None]:
    """(begin, None) bij precies één letterlijke treffer, anders (None, reden)."""
    tekst = materiaal.get(item["material_id"])
    if tekst is None:
        return None, "onbekend materiaal"
    if item["material_sha256"] != _sha256(tekst):
        return None, "materiaalhash wijkt af"
    treffers = _treffers(tekst, item["quote"])
    if not treffers:
        return None, "citaat staat niet letterlijk in het aangewezen materiaal"
    if len(treffers) > 1:
        return None, (
            f"citaat is dubbelzinnig: het staat {len(treffers)} keer in het "
            "aangewezen materiaal"
        )
    return treffers[0], None


def _als_concept(antwoord: Mapping[str, Any], begin: Mapping[str, int]) -> dict:
    """Het concept met de afgeleide posities; verder letterlijk het antwoord."""
    concept = deepcopy(dict(antwoord))
    concept["schema_version"] = CONCEPTSCHEMA
    concept["evidence"] = [
        {
            "id": item["id"],
            "material_id": item["material_id"],
            "material_sha256": item["material_sha256"],
            "start": begin.get(item["id"], 0),
            "end": begin.get(item["id"], 0) + len(item["quote"]),
            "quote": item["quote"],
        }
        for item in antwoord["evidence"]
    ]
    return concept


def _ontsnap(antwoord: Mapping[str, Any]) -> dict[str, Any]:
    """XML-escaping uit de prompt terug in citaten en voorgestelde termen.

    Het materiaal staat XML-escaped in de prompt; een escape zoals `&amp;`
    staat voor één teken van de oorspronkelijke tekst.
    """
    kopie = deepcopy(dict(antwoord))
    for lijst, veld in (("evidence", "quote"), ("proposals", "term")):
        items = kopie.get(lijst)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and isinstance(item.get(veld), str):
                item[veld] = unescape(item[veld])
    return kopie


def valideer_antwoord(
    antwoord: Any,
    materiaal: Mapping[str, str],
    buren: Mapping[str, str | None],
) -> tuple[Ess05Concept | None, list[dict[str, Any]]]:
    """Leid uit een `ANTWOORDSCHEMA`-antwoord het concept af en valideer het.

    (concept, []) of (None, fouten); fail-closed, zonder reparatie. Volgorde
    zoals `valideer_concept`: eerst structuur (`reason == "structuurfout"`),
    dan per bewijsplaats de afleiding — alleen bij precies één letterlijke
    treffer in het aangewezen materiaal met de juiste hash — en daarna de
    overige vaste controles op het afgeleide concept.
    """
    if isinstance(antwoord, Mapping):
        antwoord = _ontsnap(antwoord)
    fout = _antwoordvormfout(antwoord)
    if fout is None:
        # Structuur- en verwijzingscontrole vóór de plaatsbepaling: dezelfde
        # prioriteit als bij een concept; de voorlopige posities gaan nergens heen.
        voorlopig = _als_concept(antwoord, {})
        fout = _vormfout(voorlopig) or _verwijzingsfout(voorlopig, buren)
    if fout is not None:
        return None, [{"reason": "structuurfout", "detail": fout}]
    begin: dict[str, int] = {}
    fouten: list[dict[str, Any]] = []
    for item in antwoord["evidence"]:
        positie, reden = _plaatsbepaling(item, materiaal)
        if reden is not None:
            fouten.append(
                {"reason": reden, "detail": f"{item['id']}: {item['quote'][:120]}"}
            )
        else:
            begin[item["id"]] = positie
    if fouten:
        return None, fouten
    return valideer_concept(_als_concept(antwoord, begin), materiaal, buren)


# --- verificatie -----------------------------------------------------------------------


def verplichte_controles(concept: Ess05Concept) -> tuple[str, ...]:
    """Alle items die de verifier moet afdekken, in vaste volgorde.

    `core_features` is altijd verplicht: ook de conclusie dat een lege
    kenmerkenlijst volledig is, wordt gecontroleerd. `completeness` dekt gemiste
    gegevens (alle buren, doel-/buurgevallen, onterecht `unclear`).
    """
    data = concept.data
    items = ["core_features"]
    items += [f"feature:{k['id']}" for k in data["core_features"]]
    items += [f"claim:{c['id']}" for c in data["claims"]]
    items += [f"neighbour:{b['neighbour_id']}" for b in data["neighbours"]]
    items += [f"proposal:{p['id']}" for p in data["proposals"]]
    if data["question"] is not None:
        items.append("question")
    items.append("completeness")
    return tuple(items)


@dataclass(frozen=True)
class Verificatieuitkomst:
    """Vrijgave alleen bij volledige, unieke, positieve dekking.

    `soort` is None bij vrijgave, anders `malformed_response`,
    `candidate_hash_mismatch` of `semantic_verification_failed`.
    """

    goedgekeurd: bool
    soort: str | None
    melding: str
    bevindingen: tuple[dict[str, str], ...] = ()


def _controlefout(item: Mapping[str, Any], pad: str) -> str | None:
    return _eerste(
        (
            (lambda: not _tekst(item["item"]), f"{pad}.item ontbreekt"),
            (
                lambda: item["outcome"] not in UITKOMSTEN,
                f"{pad}: onbekende outcome {item['outcome']!r}",
            ),
            (lambda: not _tekst(item["finding"]), f"{pad}.finding ontbreekt"),
        )
    )


def _niet_goed(soort: str, melding: str, bevindingen=()) -> Verificatieuitkomst:
    return Verificatieuitkomst(False, soort, melding, tuple(bevindingen))


def toets_verificatie(ruw: Any, concept: Ess05Concept) -> Verificatieuitkomst:
    """Toets een verificatieantwoord tegen exact dit concept. Fail-closed."""
    fout = _exacte_velden(ruw, _VERIFICATIEVELDEN, "verificatie") or (
        f"schema_version moet {VERIFICATIESCHEMA!r} zijn"
        if ruw["schema_version"] != VERIFICATIESCHEMA
        else None
    )
    fout = fout or _lijstfout(ruw["checks"], _CONTROLEVELDEN, "checks", _controlefout)
    if fout:
        return _niet_goed("malformed_response", fout)
    if ruw["candidate_hash"] != concept.hash:
        return _niet_goed(
            "candidate_hash_mismatch",
            "verificatie hoort niet bij exact dit conceptoordeel (candidate_hash wijkt af)",
        )
    verplicht = verplichte_controles(concept)
    gegeven = [c["item"] for c in ruw["checks"]]
    if len(gegeven) != len(set(gegeven)) or set(gegeven) != set(verplicht):
        return _niet_goed(
            "malformed_response",
            "verificatie dekt niet exact en uniek de verplichte controles "
            f"(ontbrekend: {sorted(set(verplicht) - set(gegeven))}, "
            f"onbekend: {sorted(set(gegeven) - set(verplicht))})",
        )
    afwijkend = tuple(
        {"item": c["item"], "outcome": c["outcome"], "finding": _tekst(c["finding"])}
        for c in ruw["checks"]
        if c["outcome"] != "supported"
    )
    if afwijkend:
        eerste = afwijkend[0]
        return _niet_goed(
            "semantic_verification_failed",
            f"semantische verificatie keurde het conceptoordeel niet goed "
            f"({len(afwijkend)} controle(s) niet ondersteund; eerste: "
            f"{eerste['item']} {eerste['outcome']}: {eerste['finding'][:200]})",
            afwijkend,
        )
    return Verificatieuitkomst(True, None, "alle verplichte controles ondersteund")
