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

Het model levert het concept als **antwoord** (`ANTWOORDSCHEMA`,
`ess05-answer/2`): genest en citaat-eerst. Elke claim staat inline op de plaats
waar ze wordt gebruikt; bij material eerst de citaten (materiaal-ID,
materiaalhash, exact citaat), dan de tekst; bij inference eerst de geneste
premisseclaims, dan de tekst. Kern-, genus- en kenmerkcitaten staan ook inline.
Er zijn geen ID's en geen verwijzingen, dus ook geen losse of ongebruikte
claim of bewijsplaats. `valideer_antwoord` leidt daar deterministisch het
concept uit af: ID's in volgorde van eerste gebruik, identieke citaten en
identieke claims samengevoegd, en begin en eind uitsluitend bij precies één
letterlijke treffer in het aangewezen materiaal (R8-offsetherstel). Het
resultaat is een gewoon `CONCEPTSCHEMA`-concept; een antwoord in een ander
schema, met onbekende of verkeerd geordende velden, te diep genest, of met een
niet-letterlijk, dubbelzinnig of aan ander materiaal ontleend citaat wordt
geweigerd, nooit gerepareerd.

`ess05-answer/3` (R13-herstel) eist daarbovenop dat elke plaats haar eigen
route draagt (`_dekkingsfout`): de reden van het geheel steunt alleen op
materiaal van de kandidaat (definitie, context, bedoelde betekenis); per
verwant begrip bevat de route van `missing_feature` een kerncitaat én een
citaat dat het ontbrekende kenmerk draagt, en die van elke gevolgtrekking
direct in de buurreden een kerncitaat én materiaal van de buurkant (bron,
buurbeschrijving of afwezigheid). Vergelijkingen staan dus bij het verwante
begrip; de verifier hoeft geen ontbrekende kant van een vergelijking op te
merken, die weigert de code.

Het platte `ess05-answer/1` (`ANTWOORDSCHEMA_1`, R8–R11) en het geneste
`ess05-answer/2` zonder routedekking (`ANTWOORDSCHEMA_2`, R12–R13) blijven
alleen via die expliciete versie afleidbaar, voor de replay van historische
documenten; de actuele binding aanvaardt ze niet.

Grens: een bestaand citaat bewijst geen dragende gevolgtrekking, en de nesting
bewijst niet dat een claimtekst binnen haar citaten of premissen blijft. Deze
module claimt geen semantische juistheid; dat oordeel ligt bij de verifier.
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
    "ANTWOORDSCHEMA_1",
    "ANTWOORDSCHEMA_2",
    "CONCEPTSCHEMA",
    "MAX_CLAIMDIEPTE",
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
#: Versie van het modelantwoord van de eerste stap: genest en citaat-eerst,
#: zonder ID's en posities; de app leidt het concept af (`valideer_antwoord`).
#: answer/3 (R13-herstel): de vorm van answer/2 plus plaatsgebonden
#: routedekking (`_dekkingsfout`).
ANTWOORDSCHEMA = "ess05-answer/3"
#: Historisch genest antwoord (R12/R13) zonder routedekking; alleen afleidbaar
#: als deze versie expliciet is gevraagd.
ANTWOORDSCHEMA_2 = "ess05-answer/2"
#: Historisch plat antwoord (bewijsplaatsen en claims met ID's, zonder
#: posities); alleen afleidbaar als deze versie expliciet is gevraagd.
ANTWOORDSCHEMA_1 = "ess05-answer/1"
#: Maximale nesting van claims in een answer/2-antwoord: een claim op een
#: gebruiksplaats is niveau 1, haar premissen niveau 2, enzovoort.
MAX_CLAIMDIEPTE = 4
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
                lambda: bool(set(index.bewijs) - bewijs),
                f"ongebruikte bewijsplaats(en): {sorted(set(index.bewijs) - bewijs)}",
            ),
            (
                lambda: bool(set(index.claims) - claims),
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


# --- het historische platte antwoord (answer/1) en de plaatsbepaling ---------------------


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
    """answer/1: alleen wat het antwoord van het concept onderscheidt (schema, bewijs)."""
    fout = _exacte_velden(antwoord, _CONCEPTVELDEN, "antwoord")
    if fout:
        return fout
    if antwoord["schema_version"] != ANTWOORDSCHEMA_1:
        return f"schema_version moet {ANTWOORDSCHEMA_1!r} zijn"
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


# --- het geneste antwoord (answer/2): ID's toekennen en samenvoegen -------------------

_ANTWOORD2VELDEN = frozenset(
    {
        "schema_version",
        "genus_quote",
        "core_features",
        "reason",
        "neighbours",
        "proposals",
        "question",
    }
)
_CITAATVELDEN = frozenset({"material_id", "material_sha256", "quote"})
_BUUR2VELDEN = frozenset(
    {
        "neighbour_id",
        "distinction",
        "feature_quote",
        "reason",
        "missing_feature",
        "uncertainty",
    }
)
_VOORSTEL2VELDEN = frozenset({"term", "source_quote", "reason"})
#: Per rol exact deze velden in deze volgorde: citaten en premissen vóór de tekst.
_CLAIMVOLGORDE: dict[str, tuple[str, ...]] = {
    ROL_MATERIAAL: ("role", "quotes", "text"),
    ROL_GEVOLGTREKKING: ("role", "premises", "text"),
    ROL_AFWEZIGHEID: ("role", "text"),
}


class _AntwoordvormError(ValueError):
    """Structuurfout in een answer/2-antwoord; wordt een `structuurfout`."""


def _sleutel(waarde: Mapping[str, Any]) -> str:
    return json.dumps(waarde, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _unescape(waarde: Any) -> Any:
    return unescape(waarde) if isinstance(waarde, str) else waarde


def _lijst(waarde: Any, pad: str) -> list[Any]:
    if not isinstance(waarde, list):
        raise _AntwoordvormError(f"{pad} moet een lijst zijn")
    return waarde


def _uniek(ids: list[str], pad: str) -> list[str]:
    if len(ids) != len(set(ids)):
        raise _AntwoordvormError(f"{pad}: dubbel citaat of dubbele claim in één lijst")
    return ids


class _Vlakmaker:
    """answer/2 → platte conceptvorm, ID's in volgorde van eerste gebruik.

    Een identiek citaat (materiaal, hash, citaat) is één bewijsplaats; een
    identieke claim (rol, tekst en dezelfde citaten of premissen) is één claim.
    Een claim krijgt haar ID pas na haar citaten en premissen, zodat een
    premisse altijd een eerdere claim is.
    """

    def __init__(self) -> None:
        self.bewijs: list[dict[str, Any]] = []
        self.claims: list[dict[str, Any]] = []
        self._bewijs_ids: dict[str, str] = {}
        self._claim_ids: dict[str, str] = {}

    def citaat(self, item: Any, pad: str) -> str:
        fout = _exacte_velden(item, _CITAATVELDEN, pad) or _eerste(
            (
                (
                    lambda: not _tekst(item["material_id"]),
                    f"{pad}.material_id ontbreekt",
                ),
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
        if fout:
            raise _AntwoordvormError(fout)
        plaats = {
            "material_id": item["material_id"],
            "material_sha256": item["material_sha256"],
            "quote": unescape(item["quote"]),
        }
        sleutel = _sleutel(plaats)
        if sleutel not in self._bewijs_ids:
            self._bewijs_ids[sleutel] = f"E{len(self.bewijs) + 1}"
            self.bewijs.append({"id": self._bewijs_ids[sleutel], **plaats})
        return self._bewijs_ids[sleutel]

    def optioneel_citaat(self, item: Any, pad: str) -> str | None:
        return None if item is None else self.citaat(item, pad)

    def claim(self, item: Any, pad: str, diepte: int = 1) -> str:
        if diepte > MAX_CLAIMDIEPTE:
            raise _AntwoordvormError(
                f"{pad}: claims te diep genest (maximaal {MAX_CLAIMDIEPTE} niveaus)"
            )
        if not isinstance(item, Mapping):
            raise _AntwoordvormError(f"{pad} is geen object")
        rol = item.get("role")
        volgorde = _CLAIMVOLGORDE.get(rol) if isinstance(rol, str) else None
        if volgorde is None:
            raise _AntwoordvormError(f"{pad}: onbekende role {item.get('role')!r}")
        if tuple(item) != volgorde:
            raise _AntwoordvormError(
                f"{pad} heeft niet exact de velden {list(volgorde)} in de afgesproken "
                f"volgorde (gegeven: {list(item)})"
            )
        if not _tekst(item["text"]):
            raise _AntwoordvormError(f"{pad}.text ontbreekt")
        bewijs: list[str] = []
        premissen: list[str] = []
        if item["role"] == ROL_MATERIAAL:
            citaten = _lijst(item["quotes"], f"{pad}.quotes")
            if not citaten:
                raise _AntwoordvormError(f"{pad}: een materiaalclaim heeft een citaat")
            bewijs = _uniek(
                [self.citaat(c, f"{pad}.quotes[{i}]") for i, c in enumerate(citaten)],
                f"{pad}.quotes",
            )
        elif item["role"] == ROL_GEVOLGTREKKING:
            genest = _lijst(item["premises"], f"{pad}.premises")
            if not genest:
                raise _AntwoordvormError(f"{pad}: een gevolgtrekking heeft premissen")
            premissen = _uniek(
                [
                    self.claim(p, f"{pad}.premises[{i}]", diepte + 1)
                    for i, p in enumerate(genest)
                ],
                f"{pad}.premises",
            )
        inhoud = {
            "role": item["role"],
            "text": item["text"],
            "evidence": bewijs,
            "premises": premissen,
        }
        sleutel = _sleutel(inhoud)
        if sleutel not in self._claim_ids:
            self._claim_ids[sleutel] = f"C{len(self.claims) + 1}"
            self.claims.append({"id": self._claim_ids[sleutel], **inhoud})
        return self._claim_ids[sleutel]

    def optionele_claim(self, item: Any, pad: str) -> str | None:
        return None if item is None else self.claim(item, pad)

    def claimlijst(self, items: Any, pad: str) -> list[str]:
        return _uniek(
            [self.claim(c, f"{pad}[{i}]") for i, c in enumerate(_lijst(items, pad))],
            pad,
        )

    def buur(self, item: Any, pad: str) -> dict[str, Any]:
        fout = _exacte_velden(item, _BUUR2VELDEN, pad)
        if fout:
            raise _AntwoordvormError(fout)
        return {
            "neighbour_id": item["neighbour_id"],
            "distinction": item["distinction"],
            "feature_evidence": self.optioneel_citaat(
                item["feature_quote"], f"{pad}.feature_quote"
            ),
            "reason_claims": self.claimlijst(item["reason"], f"{pad}.reason"),
            "missing_feature_claim": self.optionele_claim(
                item["missing_feature"], f"{pad}.missing_feature"
            ),
            "uncertainty_claim": self.optionele_claim(
                item["uncertainty"], f"{pad}.uncertainty"
            ),
        }

    def voorstel(self, item: Any, pad: str, nummer: int) -> dict[str, Any]:
        fout = _exacte_velden(item, _VOORSTEL2VELDEN, pad)
        if fout:
            raise _AntwoordvormError(fout)
        return {
            "id": f"P{nummer}",
            "term": _unescape(item["term"]),
            "source_evidence": self.optioneel_citaat(
                item["source_quote"], f"{pad}.source_quote"
            ),
            "reason_claims": self.claimlijst(item["reason"], f"{pad}.reason"),
        }

    def vraag(self, item: Any) -> dict[str, Any] | None:
        if item is None:
            return None
        fout = _exacte_velden(item, _VRAAGVELDEN, "question")
        if fout:
            raise _AntwoordvormError(fout)
        return {
            "text": item["text"],
            "claims": self.claimlijst(item["claims"], "question.claims"),
        }


def _vlak_antwoord(antwoord: Any, schema: str) -> dict[str, Any]:
    """De platte conceptvorm (nog zonder posities) van een genest antwoord.

    Alleen structuur: typen, gesloten en geordende velden, nestingdiepte, geen
    ID's. Labelregels, verwijzingen en citaten volgen op het platte concept.
    answer/2 en answer/3 hebben dezelfde vorm; `schema` is de gevraagde versie.
    """
    if not isinstance(antwoord, Mapping):
        raise _AntwoordvormError("antwoord is geen object")
    # Eerst de versie: een antwoord in een ander schema krijgt die melding.
    if antwoord.get("schema_version") != schema:
        raise _AntwoordvormError(f"schema_version moet {schema!r} zijn")
    fout = _exacte_velden(antwoord, _ANTWOORD2VELDEN, "antwoord")
    if fout:
        raise _AntwoordvormError(fout)
    maker = _Vlakmaker()
    genus = maker.optioneel_citaat(antwoord["genus_quote"], "genus_quote")
    kenmerken = [
        {"id": f"F{i + 1}", "evidence": maker.citaat(c, f"core_features[{i}]")}
        for i, c in enumerate(_lijst(antwoord["core_features"], "core_features"))
    ]
    reden = maker.claimlijst(antwoord["reason"], "reason")
    buren = [
        maker.buur(b, f"neighbours[{i}]")
        for i, b in enumerate(_lijst(antwoord["neighbours"], "neighbours"))
    ]
    voorstellen = [
        maker.voorstel(p, f"proposals[{i}]", i + 1)
        for i, p in enumerate(_lijst(antwoord["proposals"], "proposals"))
    ]
    vraag = maker.vraag(antwoord["question"])
    return {
        "schema_version": CONCEPTSCHEMA,
        "genus_evidence": genus,
        "core_features": kenmerken,
        "evidence": maker.bewijs,
        "claims": maker.claims,
        "reason_claims": reden,
        "neighbours": buren,
        "proposals": voorstellen,
        "question": vraag,
    }


def _vlak(antwoord: Any, schema: str) -> tuple[Any, str | None]:
    """(platte vorm, None) of (None, structuurfout) voor precies deze antwoordversie."""
    if schema in (ANTWOORDSCHEMA, ANTWOORDSCHEMA_2):
        try:
            return _vlak_antwoord(antwoord, schema), None
        except _AntwoordvormError as exc:
            return None, str(exc)
    if schema == ANTWOORDSCHEMA_1:
        if isinstance(antwoord, Mapping):
            antwoord = _ontsnap(antwoord)
        return antwoord, _antwoordvormfout(antwoord)
    return None, f"onbekend antwoordschema {schema!r}"


#: answer/3: materiaal dat de kandidaat zelf beschrijft. De reden van het
#: geheel steunt alleen hierop; elke vergelijking staat bij het verwante begrip.
_KANDIDAATMATERIAAL = frozenset({_DEFINITIE, "context", "meaning"})
#: Merkteken in een route voor een afwezigheidsclaim (geen citaat).
_AFWEZIG = "afwezigheid"


def _is_buurkant(locatie: str) -> bool:
    return locatie.startswith((_BRONPREFIX, _BUURPREFIX)) or locatie == _AFWEZIG


def _is_kenmerkdrager(locatie: str) -> bool:
    return locatie.startswith((_BRONPREFIX, _BUURPREFIX)) or locatie == "meaning"


def _dekkingsfout(ruw: Mapping[str, Any]) -> str | None:
    """answer/3: draagt elke plaats haar eigen route? Fail-closed, geen reparatie.

    De route van een claim is de verzameling materiaal-ID's van haar citaten en
    die van al haar premissen (recursief); een afwezigheidsclaim telt als
    `_AFWEZIG`. Welke woorden een claim gebruikt, toetst de code niet: dat blijft
    bij de verifier. De code eist alleen dat de route beide kanten bevat die de
    plaats nodig heeft.
    """
    claims = {c["id"]: c for c in ruw["claims"]}
    bron = {e["id"]: e["material_id"] for e in ruw["evidence"]}

    def route(ref: str) -> set[str]:
        claim = claims[ref]
        locaties = {bron[e] for e in claim["evidence"]}
        if claim["role"] == ROL_AFWEZIGHEID:
            locaties.add(_AFWEZIG)
        for premisse in claim["premises"]:
            locaties |= route(premisse)
        return locaties

    for ref in ruw["reason_claims"]:
        buiten = route(ref) - _KANDIDAATMATERIAAL
        if buiten:
            return (
                f"reason van het geheel: claim {ref!r} steunt op {sorted(buiten)}; "
                "zij steunt alleen op definitie, context of bedoelde betekenis, een "
                "vergelijking staat bij het verwante begrip"
            )
    for buur in ruw["neighbours"]:
        pad = f"neighbour {buur['neighbour_id']!r}"
        ontbrekend = buur["missing_feature_claim"]
        if ontbrekend is not None:
            locaties = route(ontbrekend)
            if _DEFINITIE not in locaties or not any(
                _is_kenmerkdrager(x) for x in locaties
            ):
                return (
                    f"{pad}: missing_feature {ontbrekend!r} steunt op "
                    f"{sorted(locaties)}; vereist is een citaat uit de definitie én "
                    "een citaat uit een bron, de buurbeschrijving of de bedoelde "
                    "betekenis dat het kenmerk draagt"
                )
        for ref in buur["reason_claims"]:
            if claims[ref]["role"] != ROL_GEVOLGTREKKING:
                continue
            locaties = route(ref)
            if _DEFINITIE not in locaties or not any(_is_buurkant(x) for x in locaties):
                return (
                    f"{pad}: gevolgtrekking {ref!r} in reason steunt op "
                    f"{sorted(locaties)}; vereist is een citaat uit de definitie én "
                    "materiaal van de buurkant (bron, buurbeschrijving of afwezigheid)"
                )
    return None


def valideer_antwoord(
    antwoord: Any,
    materiaal: Mapping[str, str],
    buren: Mapping[str, str | None],
    *,
    schema: str = ANTWOORDSCHEMA,
) -> tuple[Ess05Concept | None, list[dict[str, Any]]]:
    """Leid uit een antwoord in precies `schema` het concept af en valideer het.

    Standaard het actuele `ANTWOORDSCHEMA` (answer/2); het historische
    `ANTWOORDSCHEMA_1` alleen als die versie expliciet is gevraagd. Een
    antwoord in een andere versie wordt nooit herkend of omgezet.

    (concept, []) of (None, fouten); fail-closed, zonder reparatie. Volgorde
    zoals `valideer_concept`: eerst structuur (`reason == "structuurfout"`),
    dan per bewijsplaats de afleiding — alleen bij precies één letterlijke
    treffer in het aangewezen materiaal met de juiste hash — en daarna de
    overige vaste controles op het afgeleide concept.
    """
    vlak, fout = _vlak(antwoord, schema)
    if fout is None:
        # Structuur- en verwijzingscontrole vóór de plaatsbepaling: dezelfde
        # prioriteit als bij een concept; de voorlopige posities gaan nergens heen.
        voorlopig = _als_concept(vlak, {})
        fout = _vormfout(voorlopig) or _verwijzingsfout(voorlopig, buren)
        if fout is None and schema == ANTWOORDSCHEMA:
            fout = _dekkingsfout(voorlopig)
    if fout is not None:
        return None, [{"reason": "structuurfout", "detail": fout}]
    begin: dict[str, int] = {}
    fouten: list[dict[str, Any]] = []
    for item in vlak["evidence"]:
        positie, reden = _plaatsbepaling(item, materiaal)
        # `_plaatsbepaling` geeft (begin, None) of (None, reden): geen positie
        # betekent altijd een reden.
        if positie is None:
            fouten.append(
                {"reason": reden, "detail": f"{item['id']}: {item['quote'][:120]}"}
            )
        else:
            begin[item["id"]] = positie
    if fouten:
        return None, fouten
    return valideer_concept(_als_concept(vlak, begin), materiaal, buren)


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


def _niet_goed(
    soort: str, melding: str, bevindingen: Iterable[dict[str, str]] = ()
) -> Verificatieuitkomst:
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
