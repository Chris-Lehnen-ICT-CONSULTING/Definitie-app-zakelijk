#!/usr/bin/env python3
"""Regressietests voor de Linear-masterplangate (DEF-665).

De gate valideert niet langer lokale `docs/epics/`- en `docs/stories/`-bestanden
maar de **live Linear-SSOT**: het vastgestelde implementatieplandocument en de
DEF-issues waarnaar dat document verwijst. Er is bewust géén lokale document- of
antwoordbestand-fallback; zonder bereikbare bron is de uitkomst ongeldig, nooit
stil groen.

Hermetisch: standaard-library `unittest` (plus de al aanwezige PyYAML om de
workflow te lezen). Geen app-imports, geen conftest, geen envloader, geen echt
netwerk, geen echte sleutel en geen originele opslag. Het uitgaande verkeer loopt
via één injecteerbare transport-seam; de tests draaien de **echte** `main()` en
bouwen geen parallelle implementatie na.

Fixtures blijven bewust staan (`tempfile.mkdtemp`); er wordt niets verwijderd.

Publiek contract van de gate:
    exit 0 = geldige bron, alle verwijzingen opgelost, bron ongewijzigd
    exit 1 = geldige scan met inhoudelijke bevinding in de bron (bijvoorbeeld een
             ontbrekende of lege verplichte sectie)
    exit 2 = ongeldige scan (ontbrekende sleutel, transportfout, HTTP-fout,
             redirect, timeout, te groot of misvormd antwoord, GraphQL-fouten,
             identiteitsafwijking, lege verwijzingsverzameling, onoplosbare
             verwijzing of een bron die tijdens de scan wijzigde)

Stdout draagt precies één JSON-document met uitsluitend vaste metadata:
`gate`, `status`, `exit_code`, `reason`, `counts` en `source`. Nooit de sleutel,
nooit vrije API-tekst, nooit documentinhoud, nooit een traceback.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import ssl
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock
from urllib.request import Request

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "scripts" / "ci" / "epic_validation_gate.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "epic-validation.yml"

#: Vaste bronidentiteit uit linear161-live-source-metadata.json.
API_URL = "https://api.linear.app/graphql"
API_KEY_ENV = "LINEAR_API_KEY"
DOCUMENT_ID = "53d2a81b-50c5-4c07-9b91-358ace998145"
PROJECT_ID = "56c63653-5332-4c89-b0eb-09bc483e76f5"
DOCUMENT_URL = (
    "https://linear.app/definitie-app/document/"
    "implementatieplan-definitieagent-kwaliteitsketen-645f1330ac28"
)
TEAM_KEY = "DEF"

SECTIE_SSOT = "## SSOT en bronhiërarchie"
SECTIE_ROADMAP = "## 3. Roadmap en afhankelijkheden"

#: Nooit een echte sleutel in de tests; deze waarde mag nergens in de uitvoer
#: opduiken, ook niet in een foutpad.
DUMMY_SLEUTEL = "lin_api_DEF665_DUMMY_GEEN_ECHTE_SLEUTEL"

#: Staat in titel, inhoud en in elke API-foutboodschap; een doorgegeven waarde
#: zou hierdoor meteen zichtbaar zijn.
MARKER = "DEF665-LINEAR-MARKER"

UPDATED_AT = "2026-09-08T17:29:48.184Z"
TOEKOMST = "2099-01-01T00:00:00.000Z"
NAIEF = "2026-09-08T17:29:48.184"

#: Het rapport draagt uitsluitend deze sleutels; geen vrije API-tekst.
RAPPORT_SLEUTELS = {"gate", "status", "exit_code", "reason", "counts", "source"}
BRON_SLEUTELS = {"document_id", "updated_at", "content_sha256"}
TELLING_SLEUTELS = {"references", "resolved"}

#: Een reden is een vast token, geen doorgegeven boodschap.
REDEN = re.compile(r"\A[a-z][a-z0-9_]{0,63}\Z")

MAX_ANTWOORD_BYTES = 2 * 1024 * 1024


def _inhoud(
    *,
    ssot: str | None = "Bron: DEF-101",
    roadmap: str | None = "Vervolg: DEF-102",
) -> str:
    """Dummy-documentinhoud; `None` laat de sectie volledig weg."""
    regels = [f"# Implementatieplan {MARKER}", ""]
    if ssot is not None:
        regels += [SECTIE_SSOT, ssot, ""]
    if roadmap is not None:
        regels += [SECTIE_ROADMAP, roadmap, ""]
    return "\n".join(regels)


def _document(
    *,
    inhoud: str | None = None,
    document_id: str = DOCUMENT_ID,
    url: str = DOCUMENT_URL,
    project_id: str | None = PROJECT_ID,
    archived_at: Any = None,
    updated_at: str = UPDATED_AT,
    titel: str | None = None,
    weglaten: tuple[str, ...] = (),
) -> dict:
    knoop = {
        "id": document_id,
        "url": url,
        "title": f"Implementatieplan {MARKER}" if titel is None else titel,
        "content": _inhoud() if inhoud is None else inhoud,
        "archivedAt": archived_at,
        "updatedAt": updated_at,
        "project": None if project_id is None else {"id": project_id},
    }
    for sleutel in weglaten:
        knoop.pop(sleutel, None)
    return knoop


def _issue(
    identifier: str,
    *,
    uuid: str | None = None,
    team: str = TEAM_KEY,
    weglaten: tuple[str, ...] = (),
) -> dict:
    nummer = int(identifier.rsplit("-", 1)[1])
    knoop = {
        "id": uuid or f"00000000-0000-4000-8000-{nummer:012d}",
        "identifier": identifier,
        "title": f"Dummy {identifier} {MARKER}",
        "state": {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Todo",
            "type": "unstarted",
        },
        "team": {"key": team},
    }
    for sleutel in weglaten:
        knoop.pop(sleutel, None)
    return knoop


class NepAntwoord:
    """Minimaal antwoord-object: status, definitieve URL en begrensde read."""

    def __init__(
        self,
        lichaam: bytes,
        *,
        status: int = 200,
        url: str = API_URL,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._lichaam = lichaam
        self.status = status
        self.url = url
        self.headers = dict(headers or {})

    def read(self, hoeveel: int | None = None) -> bytes:
        if hoeveel is None:
            return self._lichaam
        return self._lichaam[:hoeveel]

    def geturl(self) -> str:
        return self.url

    def __enter__(self) -> NepAntwoord:
        return self

    def __exit__(self, *_uitzondering: object) -> bool:
        return False


class NepTransport:
    """Registreert elk uitgaand verzoek en levert vooraf vastgelegde antwoorden."""

    def __init__(self, *antwoorden: NepAntwoord | BaseException) -> None:
        self.antwoorden = list(antwoorden)
        self.verzoeken: list[Request] = []
        self.timeouts: list[float | None] = []

    def __call__(self, verzoek: Request, *, timeout: float | None = None) -> Any:
        self.verzoeken.append(verzoek)
        self.timeouts.append(timeout)
        if not self.antwoorden:
            raise AssertionError("meer verzoeken dan voorbereide antwoorden")
        antwoord = self.antwoorden.pop(0)
        if isinstance(antwoord, BaseException):
            raise antwoord
        return antwoord

    def lichamen(self) -> list[dict]:
        return [json.loads(verzoek.data.decode("utf-8")) for verzoek in self.verzoeken]


def _bytes(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _doc_antwoord(**kwargs: Any) -> NepAntwoord:
    return NepAntwoord(_bytes({"data": {"document": _document(**kwargs)}}))


def _issue_antwoord(*issues: dict | None) -> NepAntwoord:
    """Aliassen `i0..iN`, één batch, in dezelfde volgorde als de verwijzingen."""
    data = {f"i{index}": issue for index, issue in enumerate(issues)}
    return NepAntwoord(_bytes({"data": data}))


def _goede_reeks(**kwargs: Any) -> NepTransport:
    """Document, één issuebatch met DEF-101/DEF-102, en de bronhercontrole."""
    return NepTransport(
        _doc_antwoord(**kwargs),
        _issue_antwoord(_issue("DEF-101"), _issue("DEF-102")),
        _doc_antwoord(**kwargs),
    )


def _new_dir(prefix: str) -> Path:
    """Verse fixture-map die bewust blijft staan, met canoniek pad."""
    return Path(tempfile.mkdtemp(prefix=f"def665-{prefix}-")).resolve()


def _gate_module():
    """Laad het gate-script los van packages, conftest of app-imports."""
    spec = importlib.util.spec_from_file_location("def665_linear_gate", GATE)
    assert spec is not None and spec.loader is not None, GATE
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _draai_module(
    module: Any,
    transport: NepTransport,
    *,
    sleutel: str | None = DUMMY_SLEUTEL,
) -> tuple[int, str]:
    """Draai de echte `main()` van een geladen module; geef code plus stdout."""
    omgeving = {
        sleutel_: waarde
        for sleutel_, waarde in os.environ.items()
        if sleutel_ != API_KEY_ENV
    }
    if sleutel is not None:
        omgeving[API_KEY_ENV] = sleutel

    buffer = io.StringIO()
    with mock.patch.dict(os.environ, omgeving, clear=True), redirect_stdout(buffer):
        code = module.main(transport=transport)
    return code, buffer.getvalue()


def _draai(
    transport: NepTransport,
    *,
    sleutel: str | None = DUMMY_SLEUTEL,
) -> tuple[int, str]:
    return _draai_module(_gate_module(), transport, sleutel=sleutel)


def _rapport(uitvoer: str) -> dict:
    """Stdout moet precies één JSON-rapport zijn; anders is er geen bewijs."""
    try:
        data = json.loads(uitvoer)
    except ValueError as fout:
        raise AssertionError(
            f"stdout is geen JSON-rapport ({fout}): {uitvoer!r}"
        ) from None
    assert isinstance(data, dict), data
    return data


def _controleer_vorm(rapport: dict, uitvoer: str) -> None:
    """Vaste sleutels, vaste redentokens, geen sleutel- of markerlek."""
    assert set(rapport) == RAPPORT_SLEUTELS, sorted(rapport)
    assert rapport["gate"] == "epic-validation", rapport
    assert set(rapport["source"]) == BRON_SLEUTELS, rapport["source"]
    assert set(rapport["counts"]) == TELLING_SLEUTELS, rapport["counts"]
    for waarde in rapport["counts"].values():
        assert isinstance(waarde, int), rapport["counts"]
    if rapport["reason"] is not None:
        assert REDEN.match(rapport["reason"]), rapport["reason"]
    assert MARKER not in uitvoer, "documentinhoud of API-tekst lekt naar de uitvoer"
    assert DUMMY_SLEUTEL not in uitvoer, "de sleutel mag nooit in de uitvoer staan"
    assert "Traceback" not in uitvoer, uitvoer


def _ongeldig(transport: NepTransport, *, reden: str | None = None) -> dict:
    """Verwacht exit 2 met een vaste reden en een vormvast rapport."""
    code, uitvoer = _draai(transport)
    rapport = _rapport(uitvoer)
    _controleer_vorm(rapport, uitvoer)
    assert code == 2, (code, rapport)
    assert rapport["status"] == "invalid", rapport
    assert rapport["exit_code"] == 2, rapport
    assert rapport["reason"], "een ongeldige scan noemt haar reden"
    if reden is not None:
        assert rapport["reason"] == reden, rapport
    return rapport


#: Genormaliseerd, tijdzonebewust ISO-8601 in UTC.
TIJDSTEMPEL = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+00:00)\Z")
SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")


def _headers(verzoek: Request) -> dict[str, str]:
    return {sleutel.lower(): waarde for sleutel, waarde in verzoek.header_items()}


class TestLinearMasterplanGate(unittest.TestCase):
    """De live Linear-SSOT is de bron; nooit een stille groene doorgang."""

    def test_geldige_live_bron_is_groen_met_vaste_metadata(self):
        transport = _goede_reeks()
        code, uitvoer = _draai(transport)
        rapport = _rapport(uitvoer)
        _controleer_vorm(rapport, uitvoer)

        assert code == 0, (code, rapport)
        assert rapport["status"] == "ok", rapport
        assert rapport["exit_code"] == 0, rapport
        assert rapport["reason"] is None, rapport
        assert rapport["counts"] == {"references": 2, "resolved": 2}, rapport

        bron = rapport["source"]
        assert bron["document_id"] == DOCUMENT_ID, bron
        assert TIJDSTEMPEL.match(bron["updated_at"]), bron
        assert SHA256.match(bron["content_sha256"]), bron
        verwacht = hashlib.sha256(_inhoud().encode("utf-8")).hexdigest()
        assert bron["content_sha256"] == verwacht, bron

        # Document, één issuebatch en de hercontrole van de bron.
        assert len(transport.verzoeken) == 3, transport.verzoeken

    def test_ontbrekende_sleutel_faalt_zonder_netwerk(self):
        gevallen = (
            ("niet gezet", None),
            ("leeg", ""),
            ("spaties", "   "),
            ("alleen crlf", "\r\n"),
            ("sleutel met crlf", DUMMY_SLEUTEL + "\r\n"),
            ("sleutel met newline", DUMMY_SLEUTEL + "\nX-Injected: 1"),
        )
        for naam, waarde in gevallen:
            with self.subTest(naam=naam):
                transport = _goede_reeks()
                code, uitvoer = _draai(transport, sleutel=waarde)
                rapport = _rapport(uitvoer)
                _controleer_vorm(rapport, uitvoer)
                assert code == 2, (code, rapport)
                assert rapport["reason"] in {
                    "missing_api_key",
                    "invalid_api_key",
                }, rapport
                assert transport.verzoeken == [], "geen netwerk zonder geldige sleutel"

    def test_uitgaand_verzoek_is_vast_en_draagt_de_sleutel_alleen_in_de_header(self):
        transport = _goede_reeks()
        code, _ = _draai(transport)
        assert code == 0, code

        for verzoek in transport.verzoeken:
            assert isinstance(verzoek, Request), verzoek
            assert verzoek.get_method() == "POST", verzoek.get_method()
            assert verzoek.full_url == API_URL, verzoek.full_url
            kop = _headers(verzoek)
            assert kop.get("authorization") == DUMMY_SLEUTEL, sorted(kop)
            assert kop.get("content-type") == "application/json", sorted(kop)
        assert transport.timeouts == [30, 30, 30], transport.timeouts

        lichamen = transport.lichamen()
        for lichaam in lichamen:
            assert set(lichaam) <= {"query", "variables"}, sorted(lichaam)
            assert isinstance(lichaam["query"], str) and lichaam["query"], lichaam
            assert DUMMY_SLEUTEL not in json.dumps(lichaam), "sleutel hoort in de kop"
        assert "document" in lichamen[0]["query"], lichamen[0]
        assert "issue" in lichamen[1]["query"], lichamen[1]
        assert "document" in lichamen[2]["query"], lichamen[2]

    def test_bronidentiteit_moet_exact_kloppen(self):
        vreemd = "00000000-0000-4000-8000-0000000000ff"
        gevallen = (
            ("ander document-id", {"document_id": vreemd}),
            ("andere url", {"url": DOCUMENT_URL + "-anders"}),
            ("ander project", {"project_id": vreemd}),
            ("geen project", {"project_id": None}),
            ("gearchiveerd", {"archived_at": UPDATED_AT}),
            ("archivedAt ontbreekt", {"weglaten": ("archivedAt",)}),
            ("titel ontbreekt", {"weglaten": ("title",)}),
            ("updatedAt in de toekomst", {"updated_at": TOEKOMST}),
            ("updatedAt zonder tijdzone", {"updated_at": NAIEF}),
            ("updatedAt leeg", {"updated_at": ""}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                _ongeldig(NepTransport(_doc_antwoord(**kwargs)))

    def test_lege_inhoud_is_ongeldig_en_ontbrekende_sectie_is_een_bevinding(self):
        for naam, inhoud in (("leeg", ""), ("alleen witruimte", "   \n\n")):
            with self.subTest(naam=naam):
                _ongeldig(NepTransport(_doc_antwoord(inhoud=inhoud)))

        for naam, kwargs in (
            ("ssot ontbreekt", {"ssot": None}),
            ("roadmap ontbreekt", {"roadmap": None}),
            ("ssot leeg", {"ssot": ""}),
            ("roadmap leeg", {"roadmap": ""}),
        ):
            with self.subTest(naam=naam):
                transport = NepTransport(_doc_antwoord(inhoud=_inhoud(**kwargs)))
                code, uitvoer = _draai(transport)
                rapport = _rapport(uitvoer)
                _controleer_vorm(rapport, uitvoer)
                assert code == 1, (code, rapport)
                assert rapport["status"] == "findings", rapport
                assert rapport["exit_code"] == 1, rapport
                assert rapport["reason"] == "section_missing", rapport

    def test_lege_verwijzingsverzameling_is_ongeldig(self):
        inhoud = _inhoud(ssot="Bron: geen", roadmap="Vervolg: geen")
        _ongeldig(NepTransport(_doc_antwoord(inhoud=inhoud)), reden="no_references")

    def test_verwijzingsproblemen_zijn_ongeldig(self):
        gedeeld = "00000000-0000-4000-8000-000000000101"
        gevallen = (
            ("niet opgelost", (_issue("DEF-101"), None)),
            ("verkeerde identifier", (_issue("DEF-101"), _issue("DEF-999"))),
            ("herhaald uuid", (_issue("DEF-101"), _issue("DEF-102", uuid=gedeeld))),
            ("leeg uuid", (_issue("DEF-101"), _issue("DEF-102", uuid=""))),
            ("geen uuid-vorm", (_issue("DEF-101"), _issue("DEF-102", uuid="102"))),
            ("ander team", (_issue("DEF-101"), _issue("DEF-102", team="OPS"))),
            ("geen state", (_issue("DEF-101"), _issue("DEF-102", weglaten=("state",)))),
            ("geen titel", (_issue("DEF-101"), _issue("DEF-102", weglaten=("title",)))),
        )
        for naam, issues in gevallen:
            with self.subTest(naam=naam):
                _ongeldig(NepTransport(_doc_antwoord(), _issue_antwoord(*issues)))

    def test_transportproblemen_zijn_ongeldig(self):
        elders = "https://elders.example/graphql"
        groot = _bytes({"data": {"tekst": "x" * (MAX_ANTWOORD_BYTES + 16)}})
        gevallen = (
            ("http 500", NepAntwoord(_bytes({"data": None}), status=500)),
            ("http 401", NepAntwoord(_bytes({"data": None}), status=401)),
            (
                "redirect",
                NepAntwoord(b"", status=302, url=elders, headers={"Location": elders}),
            ),
            ("andere eind-url", NepAntwoord(_bytes({"data": {}}), url=elders)),
            ("timeout", TimeoutError("timeout")),
            ("os-fout", OSError("i/o")),
            ("te groot antwoord", NepAntwoord(groot)),
            ("misvormde json", NepAntwoord(b"{geen json")),
            ("geen utf-8", NepAntwoord(b'{"data": "\xff\xfe"}')),
            (
                "dubbele json-sleutels",
                NepAntwoord(
                    b'{"data": {"document": null}, "data": {"document": null}}'
                ),
            ),
            ("graphql-fouten", NepAntwoord(_bytes({"errors": [{"message": MARKER}]}))),
            (
                "gedeeltelijke graphql-fouten",
                NepAntwoord(
                    _bytes(
                        {
                            "data": {"document": _document()},
                            "errors": [{"message": MARKER}],
                        }
                    )
                ),
            ),
            ("document ontbreekt", NepAntwoord(_bytes({"data": {"document": None}}))),
            ("geen data-sleutel", NepAntwoord(_bytes({"foo": 1}))),
            ("geen object", NepAntwoord(_bytes([1, 2, 3]))),
        )
        for naam, antwoord in gevallen:
            with self.subTest(naam=naam):
                _ongeldig(NepTransport(antwoord))

    def test_foutenveld_van_het_verkeerde_type_blokkeert(self):
        """Een `errors` dat geen lijst is, is onbekend — dus niet 'geen fout'."""
        gevallen = (
            ("leeg object", {}),
            ("null", None),
            ("false", False),
            ("nul", 0),
            ("lege tekst", ""),
            ("losse tekst", MARKER),
        )
        for naam, waarde in gevallen:
            with self.subTest(naam=naam):
                eerste = _bytes({"data": {"document": _document()}, "errors": waarde})
                transport = NepTransport(
                    NepAntwoord(eerste),
                    _issue_antwoord(_issue("DEF-101"), _issue("DEF-102")),
                    _doc_antwoord(),
                )
                _ongeldig(transport, reden="graphql_errors")

    def test_lege_foutenlijst_blokkeert_niet(self):
        leeg = _bytes({"data": {"document": _document()}, "errors": []})
        transport = NepTransport(
            NepAntwoord(leeg),
            _issue_antwoord(_issue("DEF-101"), _issue("DEF-102")),
            NepAntwoord(leeg),
        )
        code, uitvoer = _draai(transport)
        rapport = _rapport(uitvoer)
        _controleer_vorm(rapport, uitvoer)

        assert code == 0, (code, rapport)
        assert rapport["status"] == "ok", rapport

    def test_json_met_nan_of_infinity_is_ongeldig(self):
        lading = json.dumps({"document": _document()}).encode("utf-8")
        for naam, constante in (
            ("nan", b"NaN"),
            ("infinity", b"Infinity"),
            ("negatieve infinity", b"-Infinity"),
        ):
            with self.subTest(naam=naam):
                lichaam = b'{"extra": ' + constante + b', "data": ' + lading + b"}"
                transport = NepTransport(
                    NepAntwoord(lichaam),
                    _issue_antwoord(_issue("DEF-101"), _issue("DEF-102")),
                    _doc_antwoord(),
                )
                _ongeldig(transport, reden="malformed_response")

    def test_hercontrole_valideert_de_bron_opnieuw_volledig(self):
        """De tweede lezing doorloopt dezelfde controles, niet alleen een hash."""
        gevallen = (
            ("archivedAt ontbreekt", {"weglaten": ("archivedAt",)}),
            ("titel ontbreekt", {"weglaten": ("title",)}),
            ("gearchiveerd", {"archived_at": UPDATED_AT}),
            ("titel leeg", {"titel": "   "}),
            ("updatedAt zonder tijdzone", {"updated_at": NAIEF}),
            ("inhoud leeg", {"inhoud": ""}),
            ("ander project", {"project_id": "00000000-0000-4000-8000-0000000000ff"}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                transport = NepTransport(
                    _doc_antwoord(),
                    _issue_antwoord(_issue("DEF-101"), _issue("DEF-102")),
                    _doc_antwoord(**kwargs),
                )
                _ongeldig(transport)

    def test_hetzelfde_uuid_in_andere_letterkast_telt_als_dubbel(self):
        gedeeld = "0000abcd-0000-4000-8000-000000000101"
        transport = NepTransport(
            _doc_antwoord(),
            _issue_antwoord(
                _issue("DEF-101", uuid=gedeeld),
                _issue("DEF-102", uuid=gedeeld.upper()),
            ),
        )
        _ongeldig(transport, reden="reference_duplicate_uuid")

    def test_fout_in_een_latere_batch_verwerpt_het_deelsucces(self):
        transport = NepTransport(
            _doc_antwoord(),
            NepAntwoord(_bytes({"errors": [{"message": MARKER}]})),
        )
        rapport = _ongeldig(transport)
        assert rapport["counts"]["resolved"] == 0, rapport

    def test_bron_die_tijdens_de_scan_wijzigt_is_ongeldig(self):
        gevallen = (
            ("andere updatedAt", {"updated_at": "2026-09-07T08:00:00.000Z"}),
            ("andere inhoud", {"inhoud": _inhoud(roadmap="Vervolg: DEF-102 (nieuw)")}),
            ("andere titel", {"titel": "Implementatieplan (hernoemd)"}),
        )
        for naam, kwargs in gevallen:
            with self.subTest(naam=naam):
                transport = NepTransport(
                    _doc_antwoord(),
                    _issue_antwoord(_issue("DEF-101"), _issue("DEF-102")),
                    _doc_antwoord(**kwargs),
                )
                _ongeldig(transport, reden="source_changed")

    def test_verwijzingen_worden_in_batches_van_hoogstens_twintig_opgevraagd(self):
        refs = tuple(f"DEF-{200 + index}" for index in range(25))
        inhoud = _inhoud(
            ssot="Bron: " + " ".join(refs[:20]),
            roadmap="Vervolg: " + " ".join(refs[20:]),
        )
        transport = NepTransport(
            _doc_antwoord(inhoud=inhoud),
            _issue_antwoord(*(_issue(ref) for ref in refs[:20])),
            _issue_antwoord(*(_issue(ref) for ref in refs[20:])),
            _doc_antwoord(inhoud=inhoud),
        )
        code, uitvoer = _draai(transport)
        rapport = _rapport(uitvoer)
        _controleer_vorm(rapport, uitvoer)

        assert code == 0, (code, rapport)
        assert rapport["counts"] == {"references": 25, "resolved": 25}, rapport
        assert len(transport.verzoeken) == 4, transport.verzoeken

    def test_te_veel_verwijzingen_is_ongeldig(self):
        refs = tuple(f"DEF-{1000 + index}" for index in range(201))
        inhoud = _inhoud(ssot="Bron: " + " ".join(refs), roadmap="Vervolg: DEF-102")
        _ongeldig(NepTransport(_doc_antwoord(inhoud=inhoud)))

    def test_geldige_lokale_documenten_leveren_nooit_een_groene_uitkomst(self):
        """Gedragsbewijs: echte, geldige lokale planningsbestanden redden niets."""
        root = _new_dir("legacyroot")
        (root / "docs" / "epics").mkdir(parents=True)
        (root / "docs" / "stories").mkdir(parents=True)
        (root / "docs" / "epics" / "EPIC-1.md").write_text(
            "---\nid: EPIC-1\ntitle: Dummy epic\nstatus: draft\n"
            "owner: def665\npriority: low\n---\n\n# dummy\n",
            encoding="utf-8",
        )
        (root / "docs" / "stories" / "US-1.md").write_text(
            "---\nid: US-1\nepic: EPIC-1\ntitle: Dummy story\nstatus: draft\n"
            "priority: low\n---\n\n# dummy\n",
            encoding="utf-8",
        )
        # Een inert antwoordbestand dat de gate nadrukkelijk niet mag gebruiken.
        (root / "response.json").write_text(
            json.dumps({"data": {"document": _document()}}), encoding="utf-8"
        )

        gevallen = (
            ("zonder sleutel", None, _goede_reeks()),
            ("falend transport", DUMMY_SLEUTEL, NepTransport(OSError("geen netwerk"))),
        )
        for naam, sleutel, transport in gevallen:
            with self.subTest(naam=naam):
                module = _gate_module()
                # De oude gate leidde haar scope uit ROOT af; bestaat dat attribuut
                # niet meer, dan zet `create=True` het alleen voor deze test.
                with mock.patch.object(module, "ROOT", root, create=True):
                    code, uitvoer = _draai_module(module, transport, sleutel=sleutel)
                rapport = _rapport(uitvoer)
                _controleer_vorm(rapport, uitvoer)
                assert code == 2, (code, rapport)
                assert rapport["status"] == "invalid", rapport

    def test_bronidentiteit_is_vast_en_niet_instelbaar(self):
        module = _gate_module()
        assert module.API_URL == API_URL, module.API_URL
        assert module.DOCUMENT_ID == DOCUMENT_ID, module.DOCUMENT_ID
        assert module.PROJECT_ID == PROJECT_ID, module.PROJECT_ID
        assert module.DOCUMENT_URL == DOCUMENT_URL, module.DOCUMENT_URL
        assert module.TEAM_KEY == TEAM_KEY, module.TEAM_KEY

    def test_standaardopener_weigert_redirects_voordat_de_sleutel_meegaat(self):
        """De echte opener mag niet volgen-en-daarna-controleren."""
        # Een expliciete lege ProxyHandler levert geen handlermethodes op en komt
        # dus niet in `opener.handlers` terecht. Het gedrag dat telt is dat urllib
        # de omgevingsproxy nooit uitleest; dat toetsen we hier rechtstreeks.
        with mock.patch.object(
            urllib.request,
            "getproxies",
            side_effect=AssertionError("omgevingsproxy werd uitgelezen"),
        ):
            opener = _gate_module().bouw_opener()

        omleiders = [
            behandelaar
            for behandelaar in opener.handlers
            if isinstance(behandelaar, urllib.request.HTTPRedirectHandler)
        ]
        assert len(omleiders) == 1, opener.handlers

        verzoek = Request(
            API_URL,
            data=b"{}",
            headers={"Authorization": DUMMY_SLEUTEL},
            method="POST",
        )
        elders = "https://elders.example/graphql"
        for status in (301, 302, 303, 307, 308):
            besluit = omleiders[0].redirect_request(
                verzoek, io.BytesIO(b""), status, "Found", {"location": elders}, elders
            )
            # None betekent: urllib doet geen tweede verzoek, dus de header met de
            # sleutel wordt nergens heen gestuurd.
            assert besluit is None, (status, besluit)

        https = [
            behandelaar
            for behandelaar in opener.handlers
            if isinstance(behandelaar, urllib.request.HTTPSHandler)
        ]
        assert len(https) == 1, opener.handlers
        context = https[0]._context
        assert context.verify_mode == ssl.CERT_REQUIRED, context.verify_mode
        assert context.check_hostname is True, context.check_hostname


MAKEFILE = REPO_ROOT / "Makefile"

#: Het exacte, onvoorwaardelijke commando van de gatestap. Een vergelijking op de
#: volledige regel weigert een stapnaam, commentaar of `echo` die het commando
#: slechts noemt.
GATECOMMANDO = "make epic-check > validation-report.json"
RAPPORTBESTAND = "validation-report.json"
ARTEFACTNAAM = "validation-report"

WORKFLOW_SJABLOON = """name: Epic and Story Validation

on:
  workflow_dispatch:

jobs:
  validate-structure:
    runs-on: ubuntu-latest

    steps:
{stap}
      - name: Upload Validation Report
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: validation-report
          path: validation-report.json
"""


def _workflow_stappen(pad: Path | None = None) -> list[dict]:
    """De stappen van `jobs.validate-structure`; alleen lezen, niets uitvoeren."""
    document = yaml.safe_load((pad or WORKFLOW).read_text(encoding="utf-8"))
    return document["jobs"]["validate-structure"]["steps"]


def _gatestap(pad: Path | None = None) -> dict:
    """De ene stap die de gedeelde gate onvoorwaardelijk en blokkerend draait."""
    stappen = [
        stap
        for stap in _workflow_stappen(pad)
        if isinstance(stap.get("run"), str) and stap["run"].strip() == GATECOMMANDO
    ]
    assert (
        len(stappen) == 1
    ), f"verwacht precies één stap met exact {GATECOMMANDO!r}: {stappen}"
    stap = stappen[0]
    assert "if" not in stap, stap
    assert stap.get("continue-on-error") in (None, False), stap
    return stap


def _workflow_variant(naam: str, commando: str, voorwaarde: str | None) -> Path:
    regels = [f"      - name: Valideer structuur ({GATECOMMANDO})"]
    if voorwaarde is not None:
        regels.append(f"        if: {voorwaarde}")
    regels.append(f"        run: {commando}")
    pad = _new_dir("workflowvariant") / f"{naam.replace(' ', '-')}.yml"
    pad.write_text(
        WORKFLOW_SJABLOON.format(stap="\n".join(regels) + "\n"), encoding="utf-8"
    )
    return pad


def _make_recept(doel: str) -> str:
    """De receptregels van één Make-doel; puur tekstueel, niets uitgevoerd."""
    recept: list[str] = []
    verzamelen = False
    for regel in MAKEFILE.read_text(encoding="utf-8").splitlines():
        if regel.startswith(f"{doel}:"):
            verzamelen = True
            continue
        if verzamelen:
            if regel.startswith("\t"):
                recept.append(regel)
                continue
            break
    return "\n".join(recept)


class TestWorkflowKoppeling(unittest.TestCase):
    """De workflow moet de gedeelde gate onvoorwaardelijk blijven aanroepen."""

    def test_workflow_roept_de_gedeelde_gate_onvoorwaardelijk_aan(self):
        _gatestap()

        uploads = [
            stap
            for stap in _workflow_stappen()
            if str(stap.get("uses", "")).startswith("actions/upload-artifact@")
        ]
        assert len(uploads) == 1, uploads
        assert uploads[0]["if"] == "always()", uploads[0]
        assert uploads[0]["with"]["name"] == ARTEFACTNAAM, uploads[0]
        assert RAPPORTBESTAND in str(uploads[0]["with"]["path"]), uploads[0]

    def test_stapnaam_of_uitgeschakelde_stap_telt_niet_als_aanroep(self):
        gevallen = (
            ("alleen genoemd", f'echo "{GATECOMMANDO}"', None),
            ("uitgeschakeld", GATECOMMANDO, "false"),
        )
        for naam, commando, voorwaarde in gevallen:
            with self.subTest(naam=naam):
                variant = _workflow_variant(naam, commando, voorwaarde)
                try:
                    _gatestap(variant)
                except AssertionError:
                    continue
                raise AssertionError(f"{naam}: deze variant hoort te worden afgewezen")

    def test_makefile_epic_check_roept_dezelfde_gate_aan(self):
        recept = _make_recept("epic-check")
        assert recept, "make-doel epic-check ontbreekt"
        assert "scripts/ci/epic_validation_gate.py" in recept, recept
        assert "-I" in recept and "-B" in recept, recept

    def test_gatestap_geeft_de_sleutel_uitsluitend_via_de_secret_door(self):
        stap = _gatestap()
        omgeving = stap.get("env") or {}
        assert omgeving.get(API_KEY_ENV) == "${{ secrets.LINEAR_API_KEY }}", stap
        assert "lin_api_" not in yaml.safe_dump(stap), "geen sleutelwaarde in de yaml"

    def test_triggers_blijven_ongewijzigd(self):
        document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        # YAML 1.1 leest de sleutel `on` als de boolean True.
        triggers = document.get("on", document.get(True))
        assert set(triggers) == {"push", "pull_request", "workflow_dispatch"}, triggers
        for gebeurtenis in ("push", "pull_request"):
            paden = triggers[gebeurtenis]["paths"]
            assert ".github/workflows/epic-validation.yml" in paden, paden
            assert "scripts/ci/epic_validation_gate.py" in paden, paden
            assert "scripts/ci/test_epic_validation_gate.py" in paden, paden

    def test_ontbrekende_secret_laat_de_gate_falen_in_plaats_van_overslaan(self):
        transport = _goede_reeks()
        code, uitvoer = _draai(transport, sleutel=None)
        rapport = _rapport(uitvoer)

        assert code == 2, (code, rapport)
        assert rapport["status"] == "invalid", rapport
        assert transport.verzoeken == [], "een ontbrekende secret is geen groene skip"


if __name__ == "__main__":
    unittest.main()
