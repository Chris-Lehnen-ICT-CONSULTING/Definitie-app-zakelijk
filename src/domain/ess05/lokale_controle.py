"""ESS-05 lokale controle — één uitspraak tegen uitsluitend haar eigen route (DEF-768).

Fase A van de bewijsisolatie (`reports/DEF-768-AI-20260927-R14/oplossingsonderzoek-v1.md`,
§3B). Een **controlepakket** bevat precies wat één lokaal verificatieverzoek mag
bevatten:

- de te toetsen uitspraak en haar rol;
- bij `material`: uitsluitend haar eigen citaten, elk met een generieke
  herkomst (definitie, context, bedoelde betekenis, bron, beschrijving van een
  verwant begrip) en de omvang (`volledige tekst` of `fragment`); het citaat
  sluit de route af;
- bij `inference`: uitsluitend de aangewezen directe premissen, als tekst.

Geen ander materiaal, geen andere claims, geen concept of concepthash, geen
claim-ID's. Materiaal-ID, materiaalhash en posities staan in de **binding**,
buiten de modelpayload; zo verandert tekst buiten de route het verzoek niet,
terwijl de binding elke wijziging van het gebonden materiaal wel ziet. Het
pakket bindt aan zijn eigen inhoud (`hash`); een globale conceptidentiteit
blijft bij de registratie.

`toets_lokale_verificatie` controleert het antwoord fail-closed (schema,
pakkethash, exact één controle-item, bekende uitkomst) en geeft de uitkomst
ongewijzigd door: een `supported` op een ontoereikende route wordt niet in code
gerepareerd.

Grens: een afwezigheidsclaim vraagt een expliciet begrensde volledige
materiaalset en valt buiten fase A. Een gevolgtrekking wordt hier getoetst op
haar directe premissen; dat die premissen zelf gedragen zijn, is een aparte,
eerdere controle in de latere productketen. Deze module claimt geen
semantische juistheid.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from domain.ess05.bewijs import (
    _BUURPREFIX,
    _CONTROLEVELDEN,
    ROL_AFWEZIGHEID,
    ROL_GEVOLGTREKKING,
    ROL_MATERIAAL,
    Ess05Concept,
    _controlefout,
    _exacte_velden,
    _label,
    _lijstfout,
    _sha256,
    _tekst,
    concepthash,
)

__all__ = [
    "CONTROLE_ITEM",
    "LOKAAL_VERIFICATIESCHEMA",
    "OMVANG_FRAGMENT",
    "OMVANG_VOLLEDIG",
    "PAKKETSCHEMA",
    "Citaatverwijzing",
    "Lokaalpakket",
    "LokaleUitkomst",
    "PakketfoutError",
    "bouw_gevolgtrekkingspakket",
    "bouw_materiaalpakket",
    "pakket_uit_concept",
    "toets_lokale_verificatie",
]

#: Versie van het controlepakket (wat het model ziet).
PAKKETSCHEMA = "ess05-local-packet/1"
#: Versie van het antwoord op één lokale controle.
LOKAAL_VERIFICATIESCHEMA = "ess05-local-verification/1"
#: Het enige controle-item van een pakket: de uitspraak zelf.
CONTROLE_ITEM = "uitspraak"
OMVANG_VOLLEDIG = "volledige tekst"
OMVANG_FRAGMENT = "fragment"

_ANTWOORDVELDEN = frozenset({"schema_version", "packet_hash", "checks"})


class PakketfoutError(ValueError):
    """Het pakket kan niet uit gebonden gegevens worden opgebouwd (fail-closed)."""


@dataclass(frozen=True)
class Citaatverwijzing:
    """Een bewijsplaats in gebonden materiaal: materiaal-ID en halfopen bereik."""

    material_id: str
    start: int
    end: int


@dataclass(frozen=True)
class Lokaalpakket:
    """Eén lokale controle: `inhoud` gaat naar het model, `binding` nooit."""

    inhoud: Mapping[str, Any]
    binding: Mapping[str, Any]

    @property
    def hash(self) -> str:
        return concepthash(dict(self.inhoud))

    @property
    def rol(self) -> str:
        return str(self.inhoud["rol"])


def _uitspraak(tekst: Any) -> str:
    schoon = _tekst(tekst)
    if not schoon:
        msg = "de uitspraak ontbreekt"
        raise PakketfoutError(msg)
    return schoon


def _herkomst(material_id: str, buurtermen: Mapping[str, str]) -> str:
    label = _label(material_id)
    term = buurtermen.get(material_id.removeprefix(_BUURPREFIX))
    if material_id.startswith(_BUURPREFIX) and term:
        return f"{label} '{term}'"
    return label


def _pakket(inhoud: dict[str, Any], binding: dict[str, Any]) -> Lokaalpakket:
    zonder_hash = Lokaalpakket(MappingProxyType(inhoud), MappingProxyType({}))
    return Lokaalpakket(
        MappingProxyType(inhoud),
        MappingProxyType({**binding, "pakket_hash": zonder_hash.hash}),
    )


def bouw_materiaalpakket(
    uitspraak: str,
    citaten: Sequence[Citaatverwijzing],
    materiaal: Mapping[str, str],
    *,
    buurtermen: Mapping[str, str] | None = None,
    binding: Mapping[str, Any] | None = None,
) -> Lokaalpakket:
    """Een materiaalclaim met uitsluitend haar citaten uit gebonden materiaal.

    Elk citaat moet binnen het bereik van bekend materiaal liggen; de
    omvang (`volledige tekst`/`fragment`) volgt uit het bereik.
    """
    tekst = _uitspraak(uitspraak)
    if not citaten:
        msg = "een materiaalclaim heeft minstens één citaat nodig"
        raise PakketfoutError(msg)
    termen = dict(buurtermen or {})
    delen, bindingen = [], []
    for nummer, ref in enumerate(citaten, start=1):
        bron = materiaal.get(ref.material_id)
        if bron is None:
            msg = f"citaat {nummer}: onbekend materiaal {ref.material_id!r}"
            raise PakketfoutError(msg)
        if not 0 <= ref.start < ref.end <= len(bron):
            msg = f"citaat {nummer}: bereik {ref.start}-{ref.end} buiten het materiaal"
            raise PakketfoutError(msg)
        volledig = ref.start == 0 and ref.end == len(bron)
        delen.append(
            {
                "id": f"B{nummer}",
                "herkomst": _herkomst(ref.material_id, termen),
                "omvang": OMVANG_VOLLEDIG if volledig else OMVANG_FRAGMENT,
                "citaat": bron[ref.start : ref.end],
            }
        )
        bindingen.append(
            {
                "material_id": ref.material_id,
                "material_sha256": _sha256(bron),
                "start": ref.start,
                "end": ref.end,
            }
        )
    inhoud = {
        "schema_version": PAKKETSCHEMA,
        "rol": ROL_MATERIAAL,
        "uitspraak": tekst,
        "citaten": delen,
    }
    return _pakket(inhoud, {**dict(binding or {}), "citaten": bindingen})


def bouw_gevolgtrekkingspakket(
    uitspraak: str,
    premissen: Sequence[str],
    *,
    binding: Mapping[str, Any] | None = None,
) -> Lokaalpakket:
    """Een gevolgtrekking met uitsluitend haar directe premissen (als tekst)."""
    tekst = _uitspraak(uitspraak)
    if not premissen:
        msg = "een gevolgtrekking heeft minstens één premisse nodig"
        raise PakketfoutError(msg)
    delen = []
    for nummer, premisse in enumerate(premissen, start=1):
        schoon = _tekst(premisse)
        if not schoon:
            msg = f"premisse {nummer} is leeg"
            raise PakketfoutError(msg)
        delen.append({"id": f"P{nummer}", "uitspraak": schoon})
    inhoud = {
        "schema_version": PAKKETSCHEMA,
        "rol": ROL_GEVOLGTREKKING,
        "uitspraak": tekst,
        "premissen": delen,
    }
    return _pakket(inhoud, dict(binding or {}))


def pakket_uit_concept(
    concept: Ess05Concept,
    claim_id: str,
    materiaal: Mapping[str, str],
    *,
    buurtermen: Mapping[str, str] | None = None,
) -> Lokaalpakket:
    """Het pakket van één claim uit een gevalideerd concept, exact haar eigen route.

    material: haar bewijsplaatsen, gebonden aan `materiaal` (hash en citaat
    moeten kloppen); inference: de teksten van haar directe premissen. De
    concepthash en de claim-ID's staan alleen in de binding.
    """
    data = concept.data
    claims = {c["id"]: c for c in data["claims"]}
    claim = claims.get(claim_id)
    if claim is None:
        msg = f"onbekende claim {claim_id!r}"
        raise PakketfoutError(msg)
    binding = {"concept_hash": concept.hash, "claim": claim_id}
    if claim["role"] == ROL_GEVOLGTREKKING:
        return bouw_gevolgtrekkingspakket(
            claim["text"],
            [claims[p]["text"] for p in claim["premises"]],
            binding={**binding, "premissen": list(claim["premises"])},
        )
    if claim["role"] == ROL_AFWEZIGHEID:
        msg = (
            f"{claim_id}: een afwezigheidsclaim vraagt een begrensde volledige "
            "materiaalset en valt buiten de lokale controle van fase A"
        )
        raise PakketfoutError(msg)
    plaatsen = {e["id"]: e for e in data["evidence"]}
    refs = []
    for ref in claim["evidence"]:
        plaats = plaatsen[ref]
        tekst = materiaal.get(plaats["material_id"])
        if tekst is None or _sha256(tekst) != plaats["material_sha256"]:
            msg = f"{claim_id}/{ref}: materiaalhash wijkt af van de binding"
            raise PakketfoutError(msg)
        if tekst[plaats["start"] : plaats["end"]] != plaats["quote"]:
            msg = f"{claim_id}/{ref}: citaat wijkt af van de bewijsplaats"
            raise PakketfoutError(msg)
        refs.append(
            Citaatverwijzing(plaats["material_id"], plaats["start"], plaats["end"])
        )
    return bouw_materiaalpakket(
        claim["text"],
        refs,
        materiaal,
        buurtermen=buurtermen,
        binding={**binding, "bewijs": list(claim["evidence"])},
    )


@dataclass(frozen=True)
class LokaleUitkomst:
    """`uitkomst` (supported/unsupported/undetermined) of een fout (`soort`)."""

    uitkomst: str | None
    soort: str | None
    melding: str
    bevinding: str | None = None


def _fout(soort: str, melding: str) -> LokaleUitkomst:
    return LokaleUitkomst(None, soort, melding)


def toets_lokale_verificatie(ruw: Any, pakket: Lokaalpakket) -> LokaleUitkomst:
    """Toets één lokaal antwoord tegen exact dit pakket. Fail-closed, geen reparatie."""
    fout = _exacte_velden(ruw, _ANTWOORDVELDEN, "lokale verificatie") or (
        f"schema_version moet {LOKAAL_VERIFICATIESCHEMA!r} zijn"
        if ruw["schema_version"] != LOKAAL_VERIFICATIESCHEMA
        else None
    )
    fout = fout or _lijstfout(ruw["checks"], _CONTROLEVELDEN, "checks", _controlefout)
    if fout:
        return _fout("malformed_response", fout)
    if ruw["packet_hash"] != pakket.hash:
        return _fout(
            "packet_hash_mismatch",
            "antwoord hoort niet bij exact dit controlepakket (packet_hash wijkt af)",
        )
    items = [c["item"] for c in ruw["checks"]]
    if items != [CONTROLE_ITEM]:
        return _fout(
            "malformed_response",
            f"lokale verificatie dekt niet exact het ene item {CONTROLE_ITEM!r} "
            f"(gekregen: {items})",
        )
    (controle,) = ruw["checks"]
    return LokaleUitkomst(
        uitkomst=controle["outcome"],
        soort=None,
        melding=f"lokale controle: {controle['outcome']}",
        bevinding=_tekst(controle["finding"]),
    )
