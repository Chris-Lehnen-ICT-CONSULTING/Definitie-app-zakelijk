#!/usr/bin/env python3
"""Fail-closed validatiegate tegen de live Linear-SSOT (DEF-665).

De vorige opzet las lokale planningsbestanden. Dat is vervangen: het
vastgestelde implementatieplan in Linear is de enige bron. Er is bewust géén
lokale document- of antwoordbestand-fallback en geen `--fake`-modus; is de bron
onbereikbaar, dan is de uitkomst ongeldig en nooit stil groen.

De gate haalt het document op, controleert de vaste identiteit (document-UUID,
canonieke URL, project-UUID, expliciet `archivedAt: null`, niet-lege titel en
inhoud, tijdzonebewuste `updatedAt` die niet in de toekomst ligt), eist dat de
twee verplichte secties bestaan én gevuld zijn, leest de unieke `DEF-<nummer>`-
verwijzingen uit de werkelijke inhoud, en lost die op via de Linear-issuequery in
batches van hoogstens twintig. Per verwijzing moeten de opgevraagde en de
teruggegeven identifier gelijk zijn en moeten een geldig UUID, een niet-lege
titel, een volledige state en teamsleutel `DEF` aanwezig zijn; hetzelfde
onderliggende UUID voor twee identifiers is ongeldig. Na de verwijzingen wordt de
bron opnieuw gelezen: wijzigde identiteit, `updatedAt` of de inhoudshash tijdens
de scan, dan is de uitkomst ongeldig in plaats van verouderd groen.

Bewust niet gemodelleerd: fase-, status- of roadmapvolgorde. Gearchiveerde of
historische verwijzingen mogen bestaan; de gate leidt daar geen planningsbeleid
uit af.

Publiek contract:
    exit 0 = geldige bron, alle verwijzingen opgelost, bron ongewijzigd
    exit 1 = geldige scan met een inhoudelijke bevinding in de bron
    exit 2 = ongeldige scan — nooit stil groen

Transport: uitsluitend POST naar de vaste GraphQL-endpoint, met een opener die
redirects wéigert (de sleutel wordt dus nooit doorgestuurd), zonder omgevings-
proxy, met standaard TLS-verificatie, een timeout van 30 seconden en een
begrensde read van 2 MiB.

Stdout draagt precies één JSON-document met uitsluitend vaste metadata: `gate`,
`status`, `exit_code`, `reason`, `counts` en `source`. Nooit de sleutel, nooit
documentinhoud of -titel, nooit een API-boodschap, nooit een traceback.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, NoReturn

API_URL = "https://api.linear.app/graphql"
API_KEY_ENV = "LINEAR_API_KEY"

#: Vaste bronidentiteit; niet configureerbaar, ook niet via de CLI.
DOCUMENT_ID = "53d2a81b-50c5-4c07-9b91-358ace998145"
PROJECT_ID = "56c63653-5332-4c89-b0eb-09bc483e76f5"
DOCUMENT_URL = (
    "https://linear.app/definitie-app/document/"
    "implementatieplan-definitieagent-kwaliteitsketen-645f1330ac28"
)
TEAM_KEY = "DEF"

VEREISTE_SECTIES = ("## SSOT en bronhiërarchie", "## 3. Roadmap en afhankelijkheden")

MAX_REFERENTIES = 200
BATCHGROOTTE = 20
TIMEOUT_SECONDEN = 30
MAX_ANTWOORD_BYTES = 2 * 1024 * 1024

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_INVALID = 2

#: `DEF665` mag niet meetellen: er moet een echt koppelteken staan.
_REFERENTIE = re.compile(r"(?<![0-9A-Za-z])DEF-([0-9]+)(?![0-9])")
_UUID = re.compile(
    r"\A[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z"
)
#: Alleen zichtbare ASCII: dit weert spaties, CR en LF uit de header.
_SLEUTELTEKENS = re.compile(r"\A[\x21-\x7e]+\Z")

_DOCUMENT_QUERY = """query Bron($id: String!) {
  document(id: $id) {
    id
    url
    title
    content
    archivedAt
    updatedAt
    project { id }
  }
}
"""

_ISSUE_VELDEN = "id identifier title state { id name type } team { key }"


class GateError(Exception):
    """Ongeldige scan; draagt uitsluitend een vaste, veilige reden."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _DubbeleSleutelError(ValueError):
    """Herhaalde sleutel in het JSON-antwoord; de betekenis is dan dubbelzinnig."""


class _StrikteJSONError(ValueError):
    """`NaN`, `Infinity` of `-Infinity`: geen geldige JSON, dus niet aanvaard."""


def _ongeldig(reden: str) -> NoReturn:
    raise GateError(reden)


class _WeigerRedirect(urllib.request.HTTPRedirectHandler):
    """Volg geen enkele redirect: de sleutel mag nooit worden doorgestuurd."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bouw_opener() -> urllib.request.OpenerDirector:
    """Vaste opener: geen redirects, geen omgevingsproxy, standaard TLS."""
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        _WeigerRedirect(),
    )


def _standaard_transport(verzoek: urllib.request.Request, *, timeout: float) -> Any:
    return bouw_opener().open(verzoek, timeout=timeout)


def _sleutel() -> str:
    """De sleutel komt uitsluitend uit de omgeving; nooit uit argv of een bestand."""
    ruw = os.environ.get(API_KEY_ENV)
    if ruw is None or not ruw.strip():
        _ongeldig("missing_api_key")
    if not _SLEUTELTEKENS.match(ruw):
        _ongeldig("invalid_api_key")
    return ruw


def _paren(paren: list[tuple[str, Any]]) -> dict:
    namen = [naam for naam, _ in paren]
    if len(set(namen)) != len(namen):
        raise _DubbeleSleutelError(API_KEY_ENV)
    return dict(paren)


def _weiger_constante(_naam: str) -> NoReturn:
    raise _StrikteJSONError(API_KEY_ENV)


def _controleer_fouten(data: dict) -> None:
    """`errors` mag ontbreken of een lege lijst zijn; al het andere blokkeert."""
    if "errors" not in data:
        return
    fouten = data["errors"]
    # Een verkeerd type is niet "geen fout": de betekenis is dan onbekend.
    if not isinstance(fouten, list):
        _ongeldig("graphql_errors")
    # Ook naast een gevulde `data`: een deelsucces telt niet als succes.
    if fouten:
        _ongeldig("graphql_errors")


def _ontleed(rauw: bytes) -> dict:
    """Ontleed het antwoord; elke afwijking is ongeldig, nooit doorgegeven tekst."""
    try:
        tekst = rauw.decode("utf-8")
    except UnicodeDecodeError:
        _ongeldig("malformed_response")
    try:
        data = json.loads(
            tekst, object_pairs_hook=_paren, parse_constant=_weiger_constante
        )
    except _DubbeleSleutelError:
        _ongeldig("duplicate_json_keys")
    except (_StrikteJSONError, ValueError):
        _ongeldig("malformed_response")
    if not isinstance(data, dict):
        _ongeldig("malformed_response")
    _controleer_fouten(data)
    lading = data.get("data")
    if not isinstance(lading, dict):
        _ongeldig("malformed_response")
    return lading


def _verstuur(
    transport: Callable[..., Any],
    sleutel: str,
    query: str,
    variabelen: dict,
) -> dict:
    lichaam = json.dumps({"query": query, "variables": variabelen}).encode("utf-8")
    verzoek = urllib.request.Request(
        API_URL,
        data=lichaam,
        headers={"Authorization": sleutel, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with transport(verzoek, timeout=TIMEOUT_SECONDEN) as antwoord:
            status = getattr(antwoord, "status", None)
            eind_url = getattr(antwoord, "url", None)
            rauw = antwoord.read(MAX_ANTWOORD_BYTES + 1)
    except urllib.error.HTTPError:
        # Een geweigerde redirect komt hier ook binnen: er is geen tweede
        # verzoek gedaan, dus de sleutel is nooit doorgestuurd.
        _ongeldig("http_status")
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError, ValueError):
        _ongeldig("transport_failure")

    if status != 200:
        _ongeldig("http_status")
    if eind_url != API_URL:
        _ongeldig("redirect_refused")
    if len(rauw) > MAX_ANTWOORD_BYTES:
        _ongeldig("response_too_large")
    return _ontleed(rauw)


def _haal_document(transport: Callable[..., Any], sleutel: str) -> dict:
    lading = _verstuur(transport, sleutel, _DOCUMENT_QUERY, {"id": DOCUMENT_ID})
    knoop = lading.get("document")
    if not isinstance(knoop, dict):
        _ongeldig("document_unavailable")
    return knoop


def _valideer_identiteit(knoop: dict) -> None:
    project = knoop.get("project")
    project_id = project.get("id") if isinstance(project, dict) else None
    if (
        knoop.get("id") != DOCUMENT_ID
        or knoop.get("url") != DOCUMENT_URL
        or project_id != PROJECT_ID
    ):
        _ongeldig("document_identity_mismatch")

    if "archivedAt" not in knoop:
        _ongeldig("document_archive_state_unknown")
    if knoop["archivedAt"] is not None:
        _ongeldig("document_archived")

    titel = knoop.get("title")
    if not isinstance(titel, str) or not titel.strip():
        _ongeldig("document_title_empty")


def _tijdstip(knoop: dict) -> str:
    """Genormaliseerd, tijdzonebewust en niet in de toekomst."""
    ruw = knoop.get("updatedAt")
    if not isinstance(ruw, str) or not ruw.strip():
        _ongeldig("document_updated_at_invalid")
    try:
        moment = datetime.fromisoformat(ruw.replace("Z", "+00:00"))
    except ValueError:
        _ongeldig("document_updated_at_invalid")
    if moment.tzinfo is None or moment.utcoffset() is None:
        _ongeldig("document_updated_at_invalid")
    if moment > datetime.now(UTC):
        _ongeldig("document_updated_at_invalid")
    return moment.astimezone(UTC).isoformat()


def _documentinhoud(knoop: dict) -> str:
    inhoud = knoop.get("content")
    if not isinstance(inhoud, str) or not inhoud.strip():
        _ongeldig("document_empty")
    return inhoud


def _sectie_gevuld(inhoud: str, kop: str) -> bool:
    """De kop moet bestaan én er moet echte tekst onder staan."""
    regels = inhoud.splitlines()
    for index, regel in enumerate(regels):
        if regel.strip() != kop:
            continue
        for volgende in regels[index + 1 :]:
            if volgende.lstrip().startswith("#"):
                break
            if volgende.strip():
                return True
        return False
    return False


def _referenties(inhoud: str) -> list[str]:
    """Unieke DEF-verwijzingen uit de werkelijke inhoud, in documentvolgorde."""
    gevonden: list[str] = []
    bekend: set[str] = set()
    for treffer in _REFERENTIE.finditer(inhoud):
        waarde = f"DEF-{treffer.group(1)}"
        if waarde not in bekend:
            bekend.add(waarde)
            gevonden.append(waarde)
    return gevonden


def _issue_query(aantal: int) -> str:
    declaraties = ", ".join(f"$r{index}: String!" for index in range(aantal))
    aliassen = "\n  ".join(
        f"i{index}: issue(id: $r{index}) {{ {_ISSUE_VELDEN} }}"
        for index in range(aantal)
    )
    return f"query Verwijzingen({declaraties}) {{\n  {aliassen}\n}}\n"


def _valideer_issue(knoop: Any, verwacht: str, uuids: set[str]) -> str:
    if not isinstance(knoop, dict):
        _ongeldig("reference_unresolved")
    if knoop.get("identifier") != verwacht:
        _ongeldig("reference_identifier_mismatch")

    uuid = knoop.get("id")
    if not isinstance(uuid, str) or not _UUID.match(uuid):
        _ongeldig("reference_invalid")

    titel = knoop.get("title")
    if not isinstance(titel, str) or not titel.strip():
        _ongeldig("reference_invalid")

    toestand = knoop.get("state")
    if not isinstance(toestand, dict):
        _ongeldig("reference_invalid")
    for veld in ("id", "name", "type"):
        waarde = toestand.get(veld)
        if not isinstance(waarde, str) or not waarde.strip():
            _ongeldig("reference_invalid")

    team = knoop.get("team")
    if not isinstance(team, dict) or team.get("key") != TEAM_KEY:
        _ongeldig("reference_invalid")

    # Dezelfde UUID kan in een andere letterkast terugkomen; normaliseer vóór de
    # vergelijking. De identifier blijft wél exact vergeleken.
    genormaliseerd = uuid.lower()
    if genormaliseerd in uuids:
        _ongeldig("reference_duplicate_uuid")
    return genormaliseerd


def _los_op(
    transport: Callable[..., Any],
    sleutel: str,
    referenties: list[str],
) -> int:
    """Los elke verwijzing op in batches; één fout verwerpt het hele deelsucces."""
    uuids: set[str] = set()
    for start in range(0, len(referenties), BATCHGROOTTE):
        deel = referenties[start : start + BATCHGROOTTE]
        variabelen = {f"r{index}": naam for index, naam in enumerate(deel)}
        lading = _verstuur(transport, sleutel, _issue_query(len(deel)), variabelen)
        for index, naam in enumerate(deel):
            uuids.add(_valideer_issue(lading.get(f"i{index}"), naam, uuids))
    return len(uuids)


def _vingerafdruk(knoop: dict) -> tuple:
    """Identiteit, titel, tijdstempel en inhoudshash: elke wijziging valt op."""
    project = knoop.get("project")
    inhoud = knoop.get("content")
    tekst = inhoud if isinstance(inhoud, str) else ""
    return (
        knoop.get("id"),
        knoop.get("url"),
        project.get("id") if isinstance(project, dict) else None,
        knoop.get("archivedAt"),
        knoop.get("title"),
        knoop.get("updatedAt"),
        hashlib.sha256(tekst.encode("utf-8")).hexdigest(),
    )


def _haal_bron(transport: Callable[..., Any], sleutel: str) -> tuple[dict, str, str]:
    """Haal het document op en valideer het volledig; ook bij de hercontrole."""
    knoop = _haal_document(transport, sleutel)
    _valideer_identiteit(knoop)
    tijdstip = _tijdstip(knoop)
    inhoud = _documentinhoud(knoop)
    return knoop, tijdstip, inhoud


def _publiceer(staat: dict, status: str, code: int, reden: str | None) -> int:
    """Precies één JSON-document op stdout; nooit een vals succes."""
    rapport = {
        "gate": "epic-validation",
        "status": status,
        "exit_code": code,
        "reason": reden,
        "counts": staat["counts"],
        "source": staat["source"],
    }
    print(json.dumps(rapport, indent=2, sort_keys=True, ensure_ascii=True))
    return code


def _draai(staat: dict, transport: Callable[..., Any]) -> int | None:
    sleutel = _sleutel()

    knoop, tijdstip, inhoud = _haal_bron(transport, sleutel)

    staat["source"] = {
        "document_id": DOCUMENT_ID,
        "updated_at": tijdstip,
        "content_sha256": hashlib.sha256(inhoud.encode("utf-8")).hexdigest(),
    }

    if not all(_sectie_gevuld(inhoud, kop) for kop in VEREISTE_SECTIES):
        return _publiceer(staat, "findings", EXIT_FINDINGS, "section_missing")

    referenties = _referenties(inhoud)
    if not referenties:
        _ongeldig("no_references")
    if len(referenties) > MAX_REFERENTIES:
        _ongeldig("too_many_references")
    staat["counts"]["references"] = len(referenties)

    opgelost = _los_op(transport, sleutel, referenties)

    # Pas ná de verwijzingen: de bron wordt opnieuw volledig gevalideerd, en pas
    # daarna vergeleken. Wijzigde er iets, dan is elk resultaat verouderd en dus
    # ongeldig — niet stil groen.
    hercontrole, _, _ = _haal_bron(transport, sleutel)
    if _vingerafdruk(hercontrole) != _vingerafdruk(knoop):
        _ongeldig("source_changed")

    staat["counts"]["resolved"] = opgelost
    return None


def main(*, transport: Callable[..., Any] | None = None) -> int:
    """Draai de gate. `transport` is uitsluitend een testnaad, geen CLI-optie."""
    staat: dict = {
        "counts": {"references": 0, "resolved": 0},
        "source": {"document_id": None, "updated_at": None, "content_sha256": None},
    }
    kanaal = _standaard_transport if transport is None else transport
    try:
        vroeg = _draai(staat, kanaal)
    except GateError as fout:
        return _publiceer(staat, "invalid", EXIT_INVALID, fout.reason)
    except Exception:
        # Buitengrens: wat hier ontsnapt kan bron- of sleutelinhoud dragen, dus
        # alleen de vaste reden naar buiten — nooit een traceback.
        return _publiceer(staat, "invalid", EXIT_INVALID, "unexpected_failure")

    if vroeg is not None:
        return vroeg
    return _publiceer(staat, "ok", EXIT_OK, None)


if __name__ == "__main__":
    sys.exit(main())
