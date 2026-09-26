"""DEF-768 WP7 — ESS-05-proefrunner (uitvoercontract v2, variant A, max 60 calls).

Fases (elk een eigen aanroep; één grootboek over alles):

    nulcall       offline routeproef, nooit netwerk, nooit grootboek
    ontwikkeling  13 vooraf gelabelde ontwikkelgevallen (één ronde)
    t_eind        20 onafhankelijke eindgevallen (bestand pas na freeze)
    t_herhaling   de 4 `herhaal_ids` van de eindset, elk 2× (8 calls)
    g             4 G-invoeren × {basis, actueel} × 2 runs (16 calls)

Beveiligingen (zie ook `proefgrootboek`):

- zonder `--droog` of `--echt` doet de runner niets; `--droog` blokkeert elke
  socketverbinding en raakt grootboek noch client;
- `AI_SDK_MAX_RETRIES=0` geforceerd vóór de app-imports; per aanroep de
  opt-ins `use_cache=False`, `max_attempts=1`, `max_retries=0`; de
  SDK-wacht weigert een SDK-client met retries ≠ 0; dienstcache 0;
- elke call wordt vóór het netwerk in het grootboek gereserveerd; fasecaps
  13/20/8/16, reserve 3, totaal 60; het plan wordt vóóraf tegen de resterende
  fasecap gecontroleerd; hervatten slaat gereserveerde sleutels over;
- één duurzame proefidentiteit: echte calls gebruiken altijd
  `reports/DEF-768-AI-20260924/callgrootboek.jsonl` met anker en slot,
  ongeacht `--uitmap`; een ander `--grootboek` wordt geweigerd;
- `t_eind` en `t_herhaling` (en hun reserve) hangen aan één eindbinding:
  datasethash, voorafgekozen `herhaal_ids`, codemanifesthash en de hash van
  de effectieve model-/promptconfiguratie (`effectieve_config`: route,
  maxtokens, temperatuur-/thinkingbeleid, timeouts, promptgrens; geen
  geheimen) — een afwijking wordt vóór het netwerk geweigerd;
- de technische reserve alleen via `--technische-herhaling <sleutel>`, met
  dezelfde prompt en effectieve configuratie als de oorspronkelijke poging;
- elke G-variant (basis en actueel) valt als complete prompt onder dezelfde
  grens als de productieketen (`PromptServiceV2.max_prompt_lengte`);
- deadline per call (`--timeout`, plus marge voor de buitenste annulering) en
  per aanroep van de runner (`--totaal-deadline`): een call die niet meer
  volledig past, start niet;
- één runner tegelijk (`Proefslot`); uitvoer alleen naar nieuwe bestanden;
  sleutels nooit in uitvoer.

Ronde 2 (`--proef R2`, DEF-768-AI-20260924-R2; zonder `--proef` altijd R1,
dat gesloten is voor echte calls): eigen opslag
`reports/DEF-768-AI-20260924-R2/` (grootboek, anker, slot, freezes), fases
ontwikkeling 9, g_ontwikkeling 4 (alleen de actuele variant op de
oorspronkelijke G1–G4-invoer), t_eind 20, t_herhaling 8, g 16, reserve 3;
samen met ronde 1 nooit boven 117 (alleen-lezen controle van het R1-grootboek).
Beide eindgroepen (T: t_eind+t_herhaling, G: g) vereisen `--freeze`: alle
verplichte velden (`freezevelden`) worden vóór elke call vergeleken en de
freezehash gaat in de eindbinding.

Ronde 8 (`--proef R8`, DEF-768-AI-20260925-R8, ADR-003-keten) was open voor
echte calls binnen het gepinde budgetbesluit van Chris (25-09,
`logs/def768/ronde8-budgetgoedkeuring-v1.json`: 68 modelstappen, max USD 25
routerbudget, cumulatief 427, reserve 0, geen automatische extra ronde). Een
echte run toetst dat besluit (hash en inhoud tegen de proefidentiteit) vóór
omgeving, grootboek en netwerk en legt zijn hash in elke reservering. Fases: ontwikkeling (R720, R715, R717; elk twee stappen),
verificatie_alleen (zes gemigreerde R7-antwoorden, alleen de verifier),
t_eind en t_herhaling. Aanvullend voor R8, vóór grootboek en netwerk: runner
en expliciete verifier op de productiegrenzen (`productiegrenzen`), begroot
model en tarief, stap-1-payload binnen de bytegrens, kostenplan binnen het
plafond, geen nulcallroutes, stopregel en fasevolgorde. Na elk geval legt de
runner de acceptatie duurzaam vast; het eerste niet-geaccepteerde geval stopt
de proef. R8 stopte na één betaalde stap (R720, USD 0,098735) en is gesloten
voor echte calls; zijn besluit blijft gepind als grond onder R9.

Ronde 9 (`--proef R9`, DEF-768-AI-20260926-R9, gerichte herproef na het
R8-offsetherstel; besluit Chris 26-09,
`logs/def768/ronde9-herproefgoedkeuring-v1.json`) was open voor echte calls: 64
modelstappen (ontwikkeling alleen R720, verificatie_alleen op de ongewijzigde
R8-V-invoer, t_eind, t_herhaling), reserve 0, cumulatief 424, routerplafond
USD 24,901265 binnen het kader van USD 25 inclusief de werkelijke R8-kosten.
Het besluit draagt het oorspronkelijke 68/25-besluit en de payloadtoestemming
(beide op hash gepind) mee. Een run toetst vóór grootboek en netwerk ook de
vastgelegde prompt- en antwoordcontractidentiteit (`contract`), die ook in de
freeze van beide eindgroepen staat. R9 is gesloten na de inhoudelijke stop op
R720 (26-09, `reports/DEF-768-AI-20260926-R9/inhoudelijke-stop-v1.json`): de
verifier gaf een ongestaafde deelzin vrij. Het contract blijft historisch op
`ess05-assess/15`/`ess05-verify/2` gepind.

Ronde 10 (`--proef R10`, DEF-768-AI-20260926-R10, gerichte proef na het
R9-bewijsherstel; besluit Chris 26-09,
`logs/def768/ronde10-herproefgoedkeuring-v1.json`) was open voor echte calls: 65
modelstappen (ontwikkeling alleen R720 uit de R9-selectie, verificatie_alleen
op V7 = de zes R8-controles opnieuw gebonden aan verify/3 plus het ongewijzigde
R9-C5-concept, `maak_r10_verificatie_invoer.py`; t_eind, t_herhaling), reserve
0, cumulatief 427, routerplafond USD 24,722355 binnen het kader van USD 25
inclusief de werkelijke R8- en R9-kosten. Het besluit draagt het
oorspronkelijke 68/25-besluit, het R9-besluit en de payloadtoestemming (alle op
hash gepind) mee; het contract is `ess05-assess/16`/`ess05-verify/3`. R10 is
gesloten na de inhoudelijke stop op R720 (26-09,
`reports/DEF-768-AI-20260926-R10/inhoudelijke-stop-v1.json`): de verifier droeg
een deelzin van C3 met de ongeciteerde bronzin na E7. Contract en V7 blijven
historisch gepind; de code draagt sinds het C3-herstel `ess05-assess/17`/
`ess05-verify/4`.

Ronde 11 (`--proef R11`, DEF-768-AI-20260926-R11, gerichte proef na het
R10-C3-herstel; besluit Chris 26-09, "akkoord",
`logs/def768/ronde11-herproefgoedkeuring-v1.json`) is de enige open ronde: 66
modelstappen (ontwikkeling alleen R720 uit de R9-selectie, verificatie_alleen
op V8 = V7 opnieuw gebonden aan verify/4 plus het ongewijzigde R10-C3-concept,
`maak_r11_verificatie_invoer.py`; t_eind, t_herhaling), reserve 0, cumulatief
430, routerplafond USD 24,529390 binnen het kader van USD 25 inclusief de
werkelijke R8-, R9- en R10-kosten. Het aantal stappen gaat exact 3 boven het
oorspronkelijke kader (68 → 71); die verruiming (`kaderverruiming_modelstappen`)
geldt alleen voor R11 en alleen als het gepinde besluit haar exact noemt. Het
contract is `ess05-assess/17`/`ess05-verify/4`.

Voorbeeld (droog, offline):

    .venv/bin/python scripts/ess05/run_ess05_proef.py --fase ontwikkeling \\
        --gevallen tests/fixtures/ess05/ontwikkelgevallen_v1.json --droog
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import logging
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Geen SDK-retries: geforceerd (niet setdefault) vóór de app-imports.
_SDK_RETRIES_VOORAF_GEZET = "AI_SDK_MAX_RETRIES" in os.environ
os.environ["AI_SDK_MAX_RETRIES"] = "0"

import migreer_r7_naar_v2 as mig
import proefgrootboek as gb
import proefinvoer as pi

logger = logging.getLogger("ess05.proefrunner")

STANDAARD_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924"
T_FASES = ("ontwikkeling", "t_eind", "t_herhaling")
G_FASES = ("g_ontwikkeling", "g")
#: R8: alleen de verificatiestap op bevroren, gemigreerde concepten.
V_FASES = ("verificatie_alleen",)
BASISCOMMIT = "26f2374d302fc66fc0b12ed29dc34585f7c0a5c3"
#: Buitenste annuleringsmarge boven de dienstdeadline (s).
MARGE_S = 10
G_MAX_TOKENS = 500  # productie: DefinitionOrchestratorV2, PHASE 4
_TECHNISCHE_FOUTEN = frozenset({"timeout", "rate_limit", "connection", "unknown"})
#: Codemanifest: runner, directe projectimports van runner/invoer/transport
#: (zie de AST-dekkingstest) en de promptbouw/-grens. Het manifest gaat als
#: `code_sha256` in de eindbinding van het grootboek.
_CODEBESTANDEN = (
    "scripts/ess05/run_ess05_proef.py",
    "scripts/ess05/proefgrootboek.py",
    "scripts/ess05/proefinvoer.py",
    # R8: verificatiemateriaal en itembinding van de verifier-only-fase.
    "scripts/ess05/migreer_r7_naar_v2.py",
    "src/services/validation/ess05_assessment_service.py",
    "src/services/validation/ai_beoordeling_transport.py",
    "src/domain/ess05/__init__.py",
    "src/domain/ess05/contract.py",
    # ADR-003: gesloten bewijscontract en de semantische verificatiestap.
    "src/domain/ess05/bewijs.py",
    # R8-offsetherstel: modeluitvoerparser van transport en ESS-05-replay.
    "src/domain/modeluitvoer.py",
    "src/services/validation/ess05_verification_service.py",
    "src/domain/ess03/contract.py",
    "src/domain/context/contract.py",
    "src/domain/context/normalisatie.py",
    "src/domain/sources/normalisatie.py",
    "src/toetsregels/runtime_contract.py",
    "src/services/interfaces.py",
    "src/services/orchestrators/definition_orchestrator_v2.py",
    "src/services/prompts/ess05_generatieburen.py",
    "src/services/prompts/sanitization.py",
    "src/services/prompts/modular_prompt_adapter.py",
    "src/services/prompts/modular_prompt_builder.py",
    "src/services/prompts/modules/json_based_rules_module.py",
    # Ronde 2: bronneninstructie (G-betekenisbehoud) staat in deze module.
    "src/services/prompts/modules/definition_task_module.py",
    "src/services/prompts/modules/semantic_categorisation_module.py",
    # Ontwikkelcorrectie R2: grens op de contextmechanismen (G4) valt onder de freeze.
    "src/services/prompts/modules/context_awareness_module.py",
    "src/services/prompts/prompt_service_v2.py",
    # R2-OC-01: overige actieve delen van de bestaande T/G-promptketen (offline
    # trace in een vers proces, zie test_def768_r2_manifestcorrectie.py).
    "src/services/prompts/modules/__init__.py",
    "src/services/prompts/modules/base_module.py",
    "src/services/prompts/modules/ess02_aanwijzing.py",
    "src/services/prompts/modules/expertise_module.py",
    "src/services/prompts/modules/grammar_module.py",
    "src/services/prompts/modules/integrity_rules_module.py",
    "src/services/prompts/modules/metrics_module.py",
    "src/services/prompts/modules/output_specification_module.py",
    "src/services/prompts/modules/prompt_orchestrator.py",
    "src/services/prompts/modules/structure_rules_module.py",
    "src/services/prompts/modules/template_module.py",
    "src/services/definition_generator_config.py",
    "src/services/definition_generator_context.py",
    "src/services/definition_generator_prompts.py",
    "src/services/web_lookup/config_loader.py",
    "src/services/web_lookup/sanitization.py",
    "src/toetsregels/cached_manager.py",
    "src/toetsregels/rule_cache.py",
    "src/monitoring/cache_monitoring.py",
    "src/utils/cache.py",
    "src/utils/type_helpers.py",
    "src/utils/xml_source_formatter.py",
    "config/toetsregels/toetsregels_config.yaml",
    "config/web_lookup_defaults.yaml",
    # ESS-05.json valt ook onder _CODEPATRONEN; hier blijft hij expliciet.
    "src/toetsregels/regels/ESS-05.json",
    "src/services/ai_service_v2.py",
    "src/services/ai/__init__.py",
    "src/services/ai/anthropic_client.py",
    "src/services/ai/model_router.py",
    "src/services/modelantwoord.py",
    "src/opschoning/opschoning_enhanced.py",
    "src/config/config_manager.py",
    "src/utils/async_api.py",
    "config/config.yaml",
)
#: Patronen in het manifest: elke regelbron komt als regeltekst in de G-prompt,
#: ook een later toegevoegde. Een patroon zonder treffer is een harde fout.
_CODEPATRONEN = ("src/toetsregels/regels/*.json",)
#: Directe imports die bewust buiten het manifest blijven (met reden).
BUITEN_CODEMANIFEST = {
    "src/config/dotenv_loader.py": "laadt alleen de sleutel uit .env; geen prompt- of transportinhoud",
}


# --- hulp -------------------------------------------------------------------------


def _sha_tekst(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _sha_bestand(pad: Path) -> str:
    return hashlib.sha256(Path(pad).read_bytes()).hexdigest()


def _stempel() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=PROJECT_ROOT, capture_output=True, check=True
        ).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.CalledProcessError):
        return None


def codemanifest() -> dict[str, str]:
    """sha256 per manifestbestand; een ontbrekend bestand is een harde fout."""
    ontbrekend = [p for p in _CODEBESTANDEN if not (PROJECT_ROOT / p).is_file()]
    ontbrekend += [p for p in _CODEPATRONEN if not any(PROJECT_ROOT.glob(p))]
    if ontbrekend:
        msg = f"codemanifest onvolledig, ontbrekend: {ontbrekend}"
        raise pi.InvoerfoutError(msg)
    paden = dict.fromkeys(_CODEBESTANDEN)
    for patroon in _CODEPATRONEN:
        treffers = (
            p.relative_to(PROJECT_ROOT).as_posix() for p in PROJECT_ROOT.glob(patroon)
        )
        paden.update(dict.fromkeys(sorted(treffers)))
    return {pad: _sha_bestand(PROJECT_ROOT / pad) for pad in paden}


def code_sha256() -> str:
    """Eén hash over het volledige codemanifest (voor de eindbinding)."""
    return pi.sha_json(codemanifest())


def identiteit() -> dict[str, Any]:
    """Git-HEAD, hash van de getrackte werkboomdiff en het codemanifest."""
    diff = _git("diff", "HEAD", "--binary")
    hashes = codemanifest()
    return {
        "git_head": (_git("rev-parse", "HEAD") or "").strip() or None,
        "tracked_diff_sha256": _sha_tekst(diff) if diff is not None else None,
        "codehashes": hashes,
        "code_sha256": pi.sha_json(hashes),
    }


@contextlib.contextmanager
def geen_netwerk() -> Iterator[None]:
    """Blokkeer elke uitgaande socketverbinding (droog en nulcall)."""

    def _weiger(*_args: Any, **_kwargs: Any) -> Any:
        msg = "droog: netwerk is geblokkeerd in deze modus"
        raise OSError(msg)

    oud_connect, oud_create = socket.socket.connect, socket.create_connection
    socket.socket.connect = _weiger  # type: ignore[method-assign]
    socket.create_connection = _weiger  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket.connect = oud_connect  # type: ignore[method-assign]
        socket.create_connection = oud_create  # type: ignore[assignment]


def _nieuwe_map(uitmap: Path, naam: str) -> Path:
    doel = Path(uitmap) / f"{naam}-{_stempel()}"
    doel.mkdir(parents=True, exist_ok=False)
    return doel


@dataclass(frozen=True)
class Proefopslag:
    """Eén grootboek + anker + slot; onafhankelijk van `--uitmap`."""

    root: Path

    @property
    def grootboek(self) -> Path:
        return Path(self.root) / "callgrootboek.jsonl"

    @property
    def slot(self) -> Path:
        return self.grootboek.with_name(self.grootboek.name + ".lock")


#: De enige opslag voor echte calls van ronde 1 (afgesproken rapportroot).
CANONIEKE_OPSLAG = Proefopslag(STANDAARD_UITMAP)
#: Ronde 2: eigen rapportroot, grootboek, anker, slot en freezes.
R2_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R2"
#: Ronde 3: eigen rapportroot, grootboek, anker, slot en freezes.
R3_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R3"
#: G-ontwikkeling (R2) draait uitsluitend op de oorspronkelijke G1–G4-invoer.
G_ONTWIKKELINVOER_SHA256 = (
    "e20b6fb43016e401dc2a7b377959ba5fc6d7147ee21cfd5d117d5551174bacc7"
)
#: Ronde 3: de vastgelegde T-ontwikkelselectie (7 R2-gevallen + 2 positieve)
#: en de vier R2-G-invoeren met actuele binding (maak_r3_ontwikkelinvoer.py).
R3_T_ONTWIKKELINVOER_SHA256 = (
    "994b2129592dfbfddce0cb3cbbbe0aadd6c03348529a269e4fc7409397d7df38"
)
R3_G_ONTWIKKELINVOER_SHA256 = (
    "f102ad1f5ffe0ab326cf8cf326944ce99088fabc35e330d8869dcd59b5d16a63"
)
#: Ronde 4: eigen rapportroot, grootboek, anker, slot en freezes.
R4_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260924-R4"
#: Ronde 4: T = R308, R312, R313 (driemaal), R302, R3P1, R3P2, R320; G = R3G3
#: (tweemaal), R2G4, R3G1 (maak_r4_ontwikkelinvoer.py).
R4_T_ONTWIKKELINVOER_SHA256 = (
    "668ec1d826d41f6e5a8706983d5ec760b98cd9b8cd34070adcea4e1d34bd97c0"
)
R4_G_ONTWIKKELINVOER_SHA256 = (
    "b3735871c080454b0e9614419935abc6639a69206f8063d20d43ffd21daa2d2a"
)
#: Ronde 5: eigen rapportroot, grootboek, anker, slot en freezes.
R5_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R5"
#: Ronde 5: T = R410, R411, R414, R409, R412, R417, R403, R313, R3P1; G = R4G1
#: (tweemaal), R3G3, R2G4 (maak_r5_ontwikkelinvoer.py).
R5_T_ONTWIKKELINVOER_SHA256 = (
    "aa60485c36224bff73d7903e6029e5b18ecb09013da059810c9b47b07537fd33"
)
R5_G_ONTWIKKELINVOER_SHA256 = (
    "bd98dabf868441c4161fb5264afafebb2a6f3326b0d613a2ae3c9b5960ec571c"
)
#: Ronde 6 (alleen T): eigen rapportroot, grootboek, anker, slot en freeze.
R6_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R6"
#: Ronde 6: T = R514, R508, R504, R512, R511, R516, R313, R507, R506
#: (maak_r6_ontwikkelinvoer.py); geen G-ontwikkelinvoer.
R6_T_ONTWIKKELINVOER_SHA256 = (
    "2e7a4bb54706efa5ecf7ee8b33e5ab8abf7eb5fcfbc183af87f270d35037f67d"
)
#: Ronde 7 (alleen T): eigen rapportroot, grootboek, anker, slot en freeze.
R7_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R7"
#: Ronde 7: T = R614, R614-D2, R514, R508, R504, R516, R610, R620, R606
#: (maak_r7_ontwikkelinvoer.py); geen G-ontwikkelinvoer.
R7_T_ONTWIKKELINVOER_SHA256 = (
    "1685f57c3219cd967daf77d49c16ab01311d38f9305f67f86cbed7e0acae2360"
)
#: Ronde 8 (ADR-003-keten): eigen rapportroot, grootboek, anker, slot en freezes.
R8_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260925-R8"
#: Ronde 8: T = R720, R715, R717 (maak_r8_ontwikkelinvoer.py).
R8_T_ONTWIKKELINVOER_SHA256 = (
    "d07846942171801e9e31dbd6b372023e4e1ba322a024ff2354430cec1fd291f0"
)
#: Ronde 8: zes gemigreerde R7-antwoorden (migreer_r7_naar_v2.py).
R8_V_INVOER_SHA256 = "ddece7dbbdf928be8c89aca819e110ea0e8ad6e45aaf6ce582fe27c7528d155c"
#: Ronde 8: het budgetbesluit van Chris ("budget is goedgekeurd", 25-09),
#: gepind op pad en hash (`controleer_budgetbesluit`).
R8_BUDGETBESLUIT = PROJECT_ROOT / "logs" / "def768" / "ronde8-budgetgoedkeuring-v1.json"
R8_BUDGETBESLUIT_SHA256 = (
    "bf82cd3bfd6cea12fc0d3d97df2305c922fdde8c19fb84db6f0a1e3320195d17"
)
#: Ronde 9 (gerichte herproef): eigen rapportroot, grootboek, anker, slot en freezes.
R9_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R9"
#: Ronde 9: T = alleen R720, exact uit de R8-selectie (maak_r9_ontwikkelinvoer.py).
R9_T_ONTWIKKELINVOER_SHA256 = (
    "4e11ebe579ba9852217951fdf21466dc3131f2ba925f49fb7114b242eef3439d"
)
#: Ronde 9: het herproefbesluit van Chris ("Ja", 26-09), gepind op pad en hash.
R9_BUDGETBESLUIT = (
    PROJECT_ROOT / "logs" / "def768" / "ronde9-herproefgoedkeuring-v1.json"
)
R9_BUDGETBESLUIT_SHA256 = (
    "89ea16dddc7bb4403d4aa6f6fdaebc385f8fb40c40e1d6698b98bcd321765018"
)
#: De toestemming voor verzending naar Anthropic (25-09, max 68 calls, USD 25),
#: waarbinnen R8 en R9 samen blijven; gepind op pad en hash.
R9_PAYLOADTOESTEMMING = (
    PROJECT_ROOT / "logs" / "def768" / "ronde8-anthropic-versturingstoestemming-v1.json"
)
R9_PAYLOADTOESTEMMING_SHA256 = (
    "a118986fa8c05161beb4f1b8eae642cc5b8ba05cb879519b289a734f26ac3a08"
)
#: Ronde 9: de prompt- en antwoordcontractidentiteit van de offsetherstelcode
#: (3dd7010e2); een run op andere code start niets (`_controleer_contract`).
R9_CONTRACT = MappingProxyType(
    {
        "prompt_version": "ess05-assess/15",
        "verification_prompt_version": "ess05-verify/2",
        "answer_schema_version": "ess05-answer/1",
        "concept_schema_version": "ess05-concept/1",
        "verification_schema_version": "ess05-verification/1",
    }
)
#: Ronde 10 (gerichte proef na het R9-bewijsherstel): eigen rapportroot,
#: grootboek, anker, slot en freezes.
R10_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R10"
#: Ronde 10: V7 (maak_r10_verificatie_invoer.py): de zes R8-items, alleen hun
#: verificatieprompthash opnieuw berekend (verify/3), plus V-N4 = het
#: ongewijzigde R9-R720-concept met foutdrager claim:C5.
R10_V_INVOER_SHA256 = "4eee1c703894d572c5c4a32664abfc5c3203d14bcf5ba994f51e06e5abf63c4d"
#: Ronde 10: het besluit van Chris ("ja", 26-09), gepind op pad en hash.
R10_BUDGETBESLUIT = (
    PROJECT_ROOT / "logs" / "def768" / "ronde10-herproefgoedkeuring-v1.json"
)
R10_BUDGETBESLUIT_SHA256 = (
    "7ca9ca3ec1c864c86a50f5b27ba51ef262174e6840dba2dd310afde04b0157a8"
)
#: Ronde 10: de gereviewde contractidentiteit van het R9-bewijsherstel
#: (a832315d9); een run op andere code start niets (`_controleer_contract`).
R10_CONTRACT = MappingProxyType(
    {
        "prompt_version": "ess05-assess/16",
        "verification_prompt_version": "ess05-verify/3",
        "answer_schema_version": "ess05-answer/1",
        "concept_schema_version": "ess05-concept/1",
        "verification_schema_version": "ess05-verification/1",
    }
)
#: Ronde 11 (gerichte proef na het R10-C3-herstel): eigen rapportroot,
#: grootboek, anker, slot en freezes.
R11_UITMAP = PROJECT_ROOT / "reports" / "DEF-768-AI-20260926-R11"
#: Ronde 11: V8 (maak_r11_verificatie_invoer.py): de zeven V7-items, alleen hun
#: verificatieprompthash opnieuw berekend (verify/4), plus V-N5 = het
#: ongewijzigde R10-R720-concept met foutdrager claim:C3.
R11_V_INVOER_SHA256 = "d25bae233b6cc35760c8e86ae3d83b35b262ad0bcc1fa9cb4e864d40fec30164"
#: Ronde 11: het besluit van Chris ("akkoord", 26-09), gepind op pad en hash.
R11_BUDGETBESLUIT = (
    PROJECT_ROOT / "logs" / "def768" / "ronde11-herproefgoedkeuring-v1.json"
)
R11_BUDGETBESLUIT_SHA256 = (
    "b7396db9b2940709ee064f36682b1df46d6c820b62769f07156822a0d16c0b14"
)
#: Ronde 11: de gereviewde contractidentiteit van het R10-C3-herstel
#: (657bf67c8); een run op andere code start niets (`_controleer_contract`).
R11_CONTRACT = MappingProxyType(
    {
        "prompt_version": "ess05-assess/17",
        "verification_prompt_version": "ess05-verify/4",
        "answer_schema_version": "ess05-answer/1",
        "concept_schema_version": "ess05-concept/1",
        "verification_schema_version": "ess05-verification/1",
    }
)


@dataclass(frozen=True)
class Proef:
    """Een vaste proef: grootboekidentiteit, canonieke opslag en regels."""

    naam: str
    identiteit: gb.Proefidentiteit
    opslag: Proefopslag
    #: Afgesloten rondes: lezen, droog en verifiëren, geen echte calls meer.
    echt_toegestaan: bool
    #: Eindgroepen vereisen een gecontroleerde freeze (`--freeze`).
    freeze_vereist: bool
    #: Vastgelegde ontwikkelinvoer (sha256 van het bestand); None = geen binding.
    t_ontwikkelinvoer_sha256: str | None = None
    g_ontwikkelinvoer_sha256: str | None = None
    #: R8: vastgelegde verifier-only-invoer (sha256 van het bestand).
    v_invoer_sha256: str | None = None
    #: R8: het gepinde budgetbesluit dat deze ronde voor echte calls opent.
    budgetbesluit: Path | None = None
    budgetbesluit_sha256: str | None = None
    #: R9: de gepinde payloadtoestemming onder het oorspronkelijke kader.
    payloadtoestemming: Path | None = None
    payloadtoestemming_sha256: str | None = None
    #: R9: vastgelegde prompt- en antwoordcontractidentiteit (`contractidentiteit`).
    contract: Mapping[str, str] | None = None
    #: R11: modelstappen boven het oorspronkelijke kader van de grond (R8: 68),
    #: alleen geldig als het gepinde besluit deze verruiming exact noemt; 0 =
    #: geen verruiming, en dan mag het besluit er ook geen noemen.
    kaderverruiming_modelstappen: int = 0


PROEVEN = {
    "R1": Proef("R1", gb.R1, CANONIEKE_OPSLAG, False, False),
    # Ronde 2 is afgerond (uitkomst-en-vervolg-v2): alleen-lezen voorganger.
    "R2": Proef(
        "R2",
        gb.R2,
        Proefopslag(R2_UITMAP),
        False,
        True,
        g_ontwikkelinvoer_sha256=G_ONTWIKKELINVOER_SHA256,
    ),
    # Ronde 3 is afgerond (57/60, reserve gesloten): alleen-lezen voorganger.
    "R3": Proef(
        "R3",
        gb.R3,
        Proefopslag(R3_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R3_T_ONTWIKKELINVOER_SHA256,
        g_ontwikkelinvoer_sha256=R3_G_ONTWIKKELINVOER_SHA256,
    ),
    # Ronde 4 is afgerond (57/60, reserve gesloten): alleen-lezen voorganger.
    "R4": Proef(
        "R4",
        gb.R4,
        Proefopslag(R4_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R4_T_ONTWIKKELINVOER_SHA256,
        g_ontwikkelinvoer_sha256=R4_G_ONTWIKKELINVOER_SHA256,
    ),
    # Ronde 5 is afgerond (57/60, reserve gesloten): alleen-lezen voorganger.
    "R5": Proef(
        "R5",
        gb.R5,
        Proefopslag(R5_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R5_T_ONTWIKKELINVOER_SHA256,
        g_ontwikkelinvoer_sha256=R5_G_ONTWIKKELINVOER_SHA256,
    ),
    # Ronde 6 is afgerond (37/40, reserve gesloten): alleen-lezen voorganger;
    # alleen T-fases, G bestaat niet in gb.R6 en wordt geweigerd.
    "R6": Proef(
        "R6",
        gb.R6,
        Proefopslag(R6_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R6_T_ONTWIKKELINVOER_SHA256,
    ),
    # Ronde 7: alleen T-fases; G bestaat niet in gb.R7 en wordt geweigerd.
    # Gesloten voor echte calls sinds ADR-003 (DEF-768, offline implementatie
    # bewijscontrole): de huidige T-software is tweestaps (conceptoordeel +
    # semantische verificatie) en past niet op de R7-freeze (eenstaps T/13)
    # noch op één clientaanroep per reservering. Budget blijft ongewijzigd;
    # een nieuwe proef vereist een eigen, onderbouwd budgetbesluit.
    "R7": Proef(
        "R7",
        gb.R7,
        Proefopslag(R7_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R7_T_ONTWIKKELINVOER_SHA256,
    ),
    # Ronde 8: duurzaam gestopt na één betaalde stap (R720, 25-09) en gesloten
    # voor echte calls. Het besluit (68 modelstappen, max USD 25, cumulatief
    # 427, reserve 0) blijft gepind: het is de grond onder het R9-besluit.
    "R8": Proef(
        "R8",
        gb.R8,
        Proefopslag(R8_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R8_T_ONTWIKKELINVOER_SHA256,
        v_invoer_sha256=R8_V_INVOER_SHA256,
        budgetbesluit=R8_BUDGETBESLUIT,
        budgetbesluit_sha256=R8_BUDGETBESLUIT_SHA256,
    ),
    # Ronde 9: geregistreerd binnen het herproefbesluit (64 modelstappen,
    # plafond USD 24,901265, cumulatief 424, reserve 0); de V-invoer is die van
    # R8. Gesloten na de inhoudelijke stop op R720 (26-09, inhoudelijke-stop-
    # v1.json); besluit en contract blijven historisch gepind. Een nieuwe proef
    # vereist een eigen besluit en een eigen registratie.
    "R9": Proef(
        "R9",
        gb.R9,
        Proefopslag(R9_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R9_T_ONTWIKKELINVOER_SHA256,
        v_invoer_sha256=R8_V_INVOER_SHA256,
        budgetbesluit=R9_BUDGETBESLUIT,
        budgetbesluit_sha256=R9_BUDGETBESLUIT_SHA256,
        payloadtoestemming=R9_PAYLOADTOESTEMMING,
        payloadtoestemming_sha256=R9_PAYLOADTOESTEMMING_SHA256,
        contract=R9_CONTRACT,
    ),
    # Ronde 10: geregistreerd binnen het gepinde besluit (65 modelstappen,
    # plafond USD 24,722355, cumulatief 427, reserve 0). Ontwikkeling is exact
    # de R9-selectie (alleen R720); V is V7. Zelfde payloadtoestemming. Gesloten
    # na de inhoudelijke stop op R720 (26-09, C3); besluit, contract en V7
    # blijven historisch gepind. R1–R10 zijn gesloten.
    "R10": Proef(
        "R10",
        gb.R10,
        Proefopslag(R10_UITMAP),
        False,
        True,
        t_ontwikkelinvoer_sha256=R9_T_ONTWIKKELINVOER_SHA256,
        v_invoer_sha256=R10_V_INVOER_SHA256,
        budgetbesluit=R10_BUDGETBESLUIT,
        budgetbesluit_sha256=R10_BUDGETBESLUIT_SHA256,
        payloadtoestemming=R9_PAYLOADTOESTEMMING,
        payloadtoestemming_sha256=R9_PAYLOADTOESTEMMING_SHA256,
        contract=R10_CONTRACT,
    ),
    # Ronde 11: open binnen het gepinde besluit (66 modelstappen, plafond USD
    # 24,529390, cumulatief 430, reserve 0); R1–R10 gesloten. Ontwikkeling is
    # exact de R9-selectie (alleen R720); V is V8. Zelfde payloadtoestemming.
    # Als enige ronde 3 modelstappen boven het oorspronkelijke kader (71).
    "R11": Proef(
        "R11",
        gb.R11,
        Proefopslag(R11_UITMAP),
        True,
        True,
        t_ontwikkelinvoer_sha256=R9_T_ONTWIKKELINVOER_SHA256,
        v_invoer_sha256=R11_V_INVOER_SHA256,
        budgetbesluit=R11_BUDGETBESLUIT,
        budgetbesluit_sha256=R11_BUDGETBESLUIT_SHA256,
        payloadtoestemming=R9_PAYLOADTOESTEMMING,
        payloadtoestemming_sha256=R9_PAYLOADTOESTEMMING_SHA256,
        contract=R11_CONTRACT,
        kaderverruiming_modelstappen=3,
    ),
}
#: Zonder `--proef` altijd ronde 1; nooit stilzwijgend een latere ronde.
STANDAARD_PROEF = PROEVEN["R1"]


def _controleer_ontwikkelinvoer(proef: Proef, fase: str, pad: Path) -> None:
    """Ontwikkelfases alleen op de vastgelegde invoer (vóór grootboek en netwerk)."""
    if fase == "ontwikkeling" and proef.t_ontwikkelinvoer_sha256 is not None:
        verwacht, soort = proef.t_ontwikkelinvoer_sha256, "T-ontwikkelselectie"
    elif fase == "g_ontwikkeling":
        verwacht, soort = proef.g_ontwikkelinvoer_sha256, "G-ontwikkelinvoer"
    elif fase in V_FASES:
        verwacht, soort = proef.v_invoer_sha256, "verifier-only-invoer"
    else:
        return
    if verwacht is None or _sha_bestand(pad) != verwacht:
        msg = (
            f"ronde {proef.naam}: {fase} draait alleen op de vastgelegde {soort} "
            f"(sha256 {verwacht}); {pad} geweigerd"
        )
        raise gb.BudgetSchendingError(msg)


def _controleer_opslag(omg: Omgeving, opslag: Proefopslag, proef: Proef) -> None:
    """Echte calls uitsluitend binnen een open proef, tegen haar canonieke opslag."""
    if not omg.echt:
        return
    if not proef.echt_toegestaan:
        msg = (
            f"ronde {proef.naam} ({proef.identiteit.proef_id}) is gesloten voor "
            "echte calls; lezen, droog en verifiëren blijven mogelijk"
        )
        raise gb.BudgetSchendingError(msg)
    if Path(opslag.root).resolve() != proef.opslag.root.resolve():
        msg = (
            f"echte calls alleen met het canonieke proefgrootboek "
            f"{proef.opslag.grootboek}; {opslag.grootboek} geweigerd"
        )
        raise gb.BudgetSchendingError(msg)


def t_stappen(dienst: Any) -> tuple[tuple[str, str], ...]:
    """De modelstappen van één T-geval, in vaste volgorde: (task_type, stapnaam).

    ADR-003: conceptoordeel en, als de dienst een verifier heeft, de
    semantische verificatie. Elke stap krijgt een eigen reservering.
    """
    stappen = [(dienst.TASK_TYPE, "beoordeling")]
    verifier = getattr(dienst, "verification_service", None)
    if verifier is not None:
        stappen.append((verifier.TASK_TYPE, "verificatie"))
    return tuple(stappen)


def clientaanroepen_per_t_geval(dienst: Any) -> int:
    """Hoeveel clientaanroepen de T-dienst per geval ten hoogste doet."""
    return len(t_stappen(dienst))


def _controleer_registratie(omg: Omgeving, proef: Proef) -> None:
    """Echte calls alleen met de geregistreerde proef, niet met een kopie.

    Een programmatisch aangepaste `Proef` (bv. een oude ronde met
    `echt_toegestaan=True`) hergebruikt anders een oude goedkeuring.
    """
    if omg.echt and PROEVEN.get(proef.naam) is not proef:
        msg = (
            f"ronde {proef.naam} is niet de geregistreerde proef; echte calls "
            "alleen via PROEVEN — geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)


def _controleer_goedkeuring(omg: Omgeving, proef: Proef) -> None:
    """Echte T-calls alleen als de ronde dit aantal modelstappen goedkeurde.

    Vóór grootboek en netwerk. R1 t/m R7 keurden één stap per geval goed (de
    eenstaps-software); de tweestaps-T vereist een nieuw budgetbesluit en een
    eigen identiteit — een oude goedkeuring wordt niet hergebruikt.
    """
    _controleer_registratie(omg, proef)
    if not omg.echt:
        return
    nodig = clientaanroepen_per_t_geval(omg.dienst)
    if nodig != proef.identiteit.modelstappen_per_geval:
        msg = (
            f"T vraagt {nodig} modelstappen per geval; ronde {proef.naam} keurde "
            f"{proef.identiteit.modelstappen_per_geval} goed — echte calls "
            "vereisen een eigen budgetbesluit en proefidentiteit; geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)


def productiegrenzen() -> dict[str, dict[str, int]]:
    """Max_tokens en deadline van beide productiestappen, uit hun constructors.

    De container bouwt `Ess05AssessmentService` en `Ess05VerificationService`
    zonder eigen grenzen; hun standaardwaarden zijn dus de productiegrenzen.
    """
    import inspect

    from services.validation.ess05_assessment_service import Ess05AssessmentService
    from services.validation.ess05_verification_service import (
        Ess05VerificationService,
    )

    grenzen = {}
    for stap, klasse in (
        ("beoordeling", Ess05AssessmentService),
        ("verificatie", Ess05VerificationService),
    ):
        parameters = inspect.signature(klasse.__init__).parameters
        grenzen[stap] = {
            "max_tokens": parameters["max_tokens"].default,
            "timeout_s": parameters["timeout_seconds"].default,
        }
    return grenzen


def controleer_budgetbesluit(proef: Proef) -> str:
    """Het gepinde budgetbesluit, getoetst tegen de proefidentiteit; geeft zijn hash.

    Fail-closed: ontbrekend, onleesbaar, een andere hash, of een inhoud die niet
    exact de caps, reserve, cumulatieve grens, historie en het kostenplafond
    van de identiteit draagt. Een besluit verruimt nooit iets: de identiteit
    blijft de grens, het besluit moet er precies op passen.
    """
    identiteit, kb = proef.identiteit, proef.identiteit.kostenbewaking
    pad, verwacht = proef.budgetbesluit, proef.budgetbesluit_sha256
    if (
        pad is None
        or verwacht is None
        or kb is None
        or identiteit.cumulatief_max is None
    ):
        msg = f"ronde {proef.naam} heeft geen budgetbesluit voor echte calls"
        raise gb.BudgetSchendingError(msg)
    try:
        inhoud = Path(pad).read_bytes()
        data = json.loads(inhoud)
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"budgetbesluit {pad} ontbreekt of is onleesbaar: {exc}"
        raise gb.BudgetSchendingError(msg) from exc
    if hashlib.sha256(inhoud).hexdigest() != verwacht:
        msg = f"budgetbesluit {Path(pad).name} wijkt af van de gepinde hash {verwacht}"
        raise gb.BudgetSchendingError(msg)
    velden = {
        "type": "gebruikersgoedkeuring-proefbudget",
        "extra_modelaanroepen_max": identiteit.totaal_max,
        "cumulatief_max": identiteit.cumulatief_max,
        "historisch_verbruik": identiteit.cumulatief_max - identiteit.totaal_max,
        "reserve": identiteit.reserve_max,
        "fasen_modelstappen_max": dict(identiteit.fasecaps),
    }
    afwijkend = [k for k, v in velden.items() if data.get(k) != v]
    if _nusd(data.get("kostenbudget_usd")) != kb.plafond_nusd:
        afwijkend.append("kostenbudget_usd")
    if not str(data.get("gebruikersantwoord") or "").strip():
        afwijkend.append("gebruikersantwoord")
    if identiteit.kostenkader_nusd is not None:
        afwijkend += _kaderafwijkingen(proef, data)
    if afwijkend:
        msg = (
            f"budgetbesluit past niet op {identiteit.proef_id} (afwijkend: "
            f"{afwijkend}); geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)
    return verwacht


def _nusd(waarde: Any) -> Decimal | None:
    """Een USD-bedrag uit een besluit in nanodollars; None als het geen getal is."""
    try:
        return Decimal(str(waarde)) * 10**9
    except InvalidOperation:
        return None


def _kaderketen(proef: Proef) -> tuple[Proef, ...]:
    """De geregistreerde voorgangers binnen het kader, nieuwste eerst.

    Van de directe voorganger tot en met de grond: de eerste voorganger onder
    kostenbewaking zonder eigen kostenkader, wiens besluit het oorspronkelijke
    kader draagt (R9: R8; R10: R9, R8; R11: R10, R9, R8).
    """
    keten: list[Proef] = []
    for vorige in gb.voorgangerketen(proef.identiteit):
        geregistreerd = next(
            (p for p in PROEVEN.values() if p.identiteit is vorige), None
        )
        if geregistreerd is None or vorige.kostenbewaking is None:
            break
        keten.append(geregistreerd)
        if vorige.kostenkader_nusd is None:
            return tuple(keten)
    msg = f"ronde {proef.naam}: geen voorganger met budgetbesluit als kader"
    raise gb.BudgetSchendingError(msg)


def _controleer_payloadtoestemming(proef: Proef, grond: Proef) -> None:
    """De gepinde payloadtoestemming, passend op het oorspronkelijke kader."""
    pad, verwacht = proef.payloadtoestemming, proef.payloadtoestemming_sha256
    kader = proef.identiteit.kostenkader_nusd
    try:
        inhoud = Path(pad).read_bytes() if pad is not None else b""
        data = json.loads(inhoud)
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"payloadtoestemming {pad} ontbreekt of is onleesbaar: {exc}"
        raise gb.BudgetSchendingError(msg) from exc
    if verwacht is None or hashlib.sha256(inhoud).hexdigest() != verwacht:
        msg = f"payloadtoestemming {Path(pad).name} wijkt af van de gepinde hash {verwacht}"
        raise gb.BudgetSchendingError(msg)
    if (
        data.get("budget_calls_max") != grond.identiteit.totaal_max
        or _nusd(data.get("budget_usd_max")) != kader
        or not str(data.get("user_reply") or "").strip()
    ):
        msg = (
            f"payloadtoestemming past niet op het kader van {grond.naam} "
            f"({grond.identiteit.totaal_max} calls, {kader} nUSD); geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)


def _kaderafwijkingen(proef: Proef, data: Mapping[str, Any]) -> list[str]:
    """R9–R11: het besluit draagt het oorspronkelijke kader van de grond (R8).

    Het oorspronkelijke besluit, de besluiten van de rondes ertussen en de
    payloadtoestemming moeten zelf gepind en geldig zijn. Het besluit noemt per
    voorganger binnen het kader zijn verbruik (`r8_…`, `r9_…`, `r10_…`); samen
    met deze ronde exact USD 25 en binnen de 68 stappen, of binnen 68 plus de
    geregistreerde verruiming (`_verruimingsafwijkingen`). De werkelijke kosten
    toetst `gb.controleer_cumulatief` tegen hun grootboeken.
    """
    identiteit = proef.identiteit
    keten = _kaderketen(proef)
    grond = keten[-1]
    for vorige in keten:
        controleer_budgetbesluit(vorige)
    _controleer_payloadtoestemming(proef, grond)
    g, kader = grond.identiteit, identiteit.kostenkader_nusd
    afwijkend = []
    if _nusd(data.get("oorspronkelijk_kostenbudget_usd")) != kader or (
        kader != g.kostenbewaking.plafond_nusd
    ):
        afwijkend.append("oorspronkelijk_kostenbudget_usd")
    usd = [f"{p.naam.lower()}_verbruik_usd" for p in keten]
    bedragen = [_nusd(data.get(sleutel)) for sleutel in usd]
    if (
        None in bedragen
        or sum(bedragen) + identiteit.kostenbewaking.plafond_nusd != kader
    ):
        afwijkend += usd
    if data.get("oorspronkelijk_extra_budget") != g.totaal_max:
        afwijkend.append("oorspronkelijk_extra_budget")
    if data.get("oorspronkelijk_cumulatief_plafond") != g.cumulatief_max:
        afwijkend.append("oorspronkelijk_cumulatief_plafond")
    sleutels = [f"{p.naam.lower()}_verbruik_modelstappen" for p in keten]
    stappen = [data.get(sleutel) for sleutel in sleutels]
    if not all(
        isinstance(s, int) and not isinstance(s, bool) and s >= 0 for s in stappen
    ) or (
        sum(stappen) + identiteit.totaal_max
        > g.totaal_max + proef.kaderverruiming_modelstappen
        or data.get("historisch_verbruik")
        != g.cumulatief_max - g.totaal_max + sum(stappen)
    ):
        afwijkend += sleutels
    return afwijkend + _verruimingsafwijkingen(proef, g, data)


_VERRUIMINGSVELDEN = (
    "goedgekeurde_verruiming_modelaanroepen",
    "nieuw_gezamenlijk_modelaanroepen_max",
    "nieuw_cumulatief_plafond",
)


def _verruimingsafwijkingen(
    proef: Proef, grond: gb.Proefidentiteit, data: Mapping[str, Any]
) -> list[str]:
    """R11: een verruiming boven het oorspronkelijke kader, gebonden aan één besluit.

    Zonder geregistreerde verruiming mag het besluit geen verruimingsveld
    noemen (geen algemene budgetverruiming via een besluit). Met verruiming n
    noemt het besluit exact n, het nieuwe gezamenlijke maximum (68 + n) en het
    nieuwe cumulatieve plafond (427 + n), dat ook de grens van de identiteit is.
    Het oorspronkelijke 68/427 blijft als historie in eigen velden staan.
    """
    n = proef.kaderverruiming_modelstappen
    if not n:
        return [f"verruiming:{k}" for k in _VERRUIMINGSVELDEN if k in data]
    verwacht = (n, grond.totaal_max + n, grond.cumulatief_max + n)
    afwijkend = [
        f"verruiming:{k}"
        for k, v in zip(_VERRUIMINGSVELDEN, verwacht, strict=True)
        if data.get(k) != v
    ]
    if proef.identiteit.cumulatief_max != grond.cumulatief_max + n:
        afwijkend.append("verruiming:cumulatief_max")
    return afwijkend


def contractidentiteit(omg: Omgeving) -> dict[str, str]:
    """Prompt- en antwoordcontractversies zoals de gebouwde omgeving ze draagt."""
    from domain.ess05 import bewijs

    return {
        "prompt_version": omg.dienst.PROMPT_VERSION,
        "verification_prompt_version": omg.dienst.verification_service.PROMPT_VERSION,
        "answer_schema_version": bewijs.ANTWOORDSCHEMA,
        "concept_schema_version": bewijs.CONCEPTSCHEMA,
        "verification_schema_version": bewijs.VERIFICATIESCHEMA,
    }


def _controleer_contract(omg: Omgeving, proef: Proef) -> None:
    """R9: de code draagt exact de vastgelegde contractidentiteit (vóór alles)."""
    if proef.contract is None:
        return
    werkelijk = contractidentiteit(omg)
    if werkelijk != dict(proef.contract):
        msg = (
            f"ronde {proef.naam}: contractidentiteit {werkelijk} is niet de "
            f"vastgelegde {dict(proef.contract)} — geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)


def _besluit_voor(omg: Omgeving, proef: Proef) -> str | None:
    """Hash van het budgetbesluit voor een echte R8-run; None offline of vóór R8."""
    if not omg.echt or proef.identiteit.kostenbewaking is None:
        return None
    return controleer_budgetbesluit(proef)


def _standaard_max_tokens(proef: Proef) -> int:
    """`--max-tokens-t` zonder waarde: R8 de productiegrens, oudere rondes 1500."""
    if proef.identiteit.kostenbewaking is not None:
        return productiegrenzen()["beoordeling"]["max_tokens"]
    return 1500


def _controleer_productiegrenzen(omg: Omgeving, proef: Proef) -> None:
    """R8: runner en expliciete verifier exact op de productiegrenzen (vóór alles)."""
    kb = proef.identiteit.kostenbewaking
    if kb is None:
        return
    verwacht = productiegrenzen()
    verifier = omg.dienst.verification_service
    werkelijk = {
        "beoordeling": {
            "max_tokens": omg.dienst._max_tokens,
            "timeout_s": omg.dienst._timeout_seconds,
        },
        "verificatie": {
            "max_tokens": verifier.max_tokens,
            "timeout_s": verifier.timeout_seconds,
        },
    }
    if (
        werkelijk != verwacht
        or omg.timeout != verwacht["beoordeling"]["timeout_s"]
        or any(g["max_tokens"] != kb.max_tokens for g in verwacht.values())
    ):
        msg = (
            f"ronde {proef.naam}: runner en verifier moeten op de productiegrenzen "
            f"draaien ({verwacht}, begroot max_tokens {kb.max_tokens}); kreeg "
            f"{werkelijk}, transporttimeout {omg.timeout} — geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)


def _controleer_kostenroute(omg: Omgeving, proef: Proef) -> None:
    """R8: routemodel, routertarief en thinkingbeleid zoals begroot (vóór alles)."""
    kb = proef.identiteit.kostenbewaking
    if kb is None:
        return
    for route in ("t", "t_verificatie"):
        cfg = omg.modelconfig[route]
        model = cfg["model"]
        if model != kb.model:
            msg = (
                f"ronde {proef.naam}: model {model!r} voor {cfg['task_type']} is "
                f"niet het begrote {kb.model!r} — geen call gestart"
            )
            raise gb.BudgetSchendingError(msg)
        prijs, bekend = omg.prijs(route)
        tarief = (round(prijs["input"] * 1e9), round(prijs["output"] * 1e9))
        if not bekend or tarief != (kb.tarief_invoer_nusd, kb.tarief_uitvoer_nusd):
            msg = (
                f"ronde {proef.naam}: tarief {tarief} nUSD/token voor {model!r} "
                f"(bekend: {bekend}) is niet het begrote "
                f"({kb.tarief_invoer_nusd}, {kb.tarief_uitvoer_nusd}) — geen call gestart"
            )
            raise gb.BudgetSchendingError(msg)
        if not omg.router.thinking_default_on(model, provider=cfg["provider"]):
            msg = (
                f"ronde {proef.naam}: thinking voor {model!r} wordt niet expliciet "
                "uitgezet; de SDK-wacht zou elke call weigeren — geen call gestart"
            )
            raise gb.BudgetSchendingError(msg)


def _payloadbytes(
    omg: Omgeving, route: str, max_tokens: int, system: str, user: str
) -> int:
    """Bytes van de body zoals de Anthropic-client hem voor deze stap verstuurt.

    Beide ESS-05-stappen vragen temperature 0.0 (`eenmalige_aanroep`); de
    client stuurt hem alleen mee als de router hem voor dit model toelaat.
    """
    cfg = omg.modelconfig[route]
    velden: dict[str, Any] = {
        "model": cfg["model"],
        "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if omg.router.accepts_temperature(cfg["model"], provider=cfg["provider"]):
        velden["temperature"] = 0.0
    return gb.payloadbytes(velden)


def _controleer_bytegrens(
    proef: Proef, task_type: str, sleutel: str, bytes_: int
) -> None:
    kb = proef.identiteit.kostenbewaking
    if kb is not None and bytes_ > kb.bytegrens[task_type]:
        msg = (
            f"{sleutel}: payload {bytes_} bytes > bytegrens {kb.bytegrens[task_type]} "
            f"voor {task_type} — geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)


def _buitenste_deadline(omg: Omgeving, stappen: int) -> int:
    """Buitenste annulering: elke modelstap zijn eigen deadline, plus marge."""
    return stappen * omg.timeout + MARGE_S


def _controleer_kostenplan(boek: gb.Grootboek, fase: str, gevallen: int) -> None:
    """R8: stopregel, fasevolgorde en kostengrens van het hele plan (vóór elke call)."""
    kb = boek.identiteit.kostenbewaking
    stappen = boek.identiteit.fasestappen
    if kb is None or stappen is None:
        return
    boek.controleer_fasestart(fase)
    per_geval = sum(kb.stapgrens_nusd(t) for t in stappen[fase])
    lopend = boek.kostenstand()["lopend_nusd"]
    if lopend + gevallen * per_geval > kb.plafond_nusd:
        msg = (
            f"kostenplan: lopend {lopend} + {gevallen} × {per_geval} > "
            f"{kb.plafond_nusd} nUSD (niets gestart)"
        )
        raise gb.BudgetSchendingError(msg)


def _t_acceptatie(record: dict[str, Any], *, volledig: bool) -> tuple[bool, str]:
    """Automatisch toetsbare acceptatie van één T-geval (geen inhoudelijke rubric).

    Ontwikkelpoort: beide stappen voltooid (structureel geldig, niet afgekapt),
    een vrijgegeven oordeel en de juiste status. Eindfases (`volledig`) ook elk
    buurlabel. Een onnodige weigering of `unclear` telt niet als acceptatie.
    """
    stappen = record["reserveringen"]
    statussen = [s["afsluitstatus"] for s in stappen]
    if record["transport"]["bewakingsweigering"]:
        return False, "bewakingsweigering"
    document = record["beoordelingsdocument"] or {}
    if document.get("status") != "assessed":
        soort = (document.get("error") or {}).get("type")
        return False, f"geen vrijgegeven oordeel ({soort}; stappen {statussen})"
    if len(stappen) != 2 or any(s != "voltooid" for s in statussen):
        return False, f"niet elke modelstap voltooid ({statussen})"
    vergelijking = record["vergelijking"]
    if not vergelijking["status_correct"]:
        return False, (
            f"status {vergelijking['gekregen']} is niet de verwachte "
            f"{vergelijking['verwacht']}"
        )
    fout = [b["term"] for b in vergelijking["per_buur"] if not b["correct"]]
    if volledig and fout:
        return False, f"buurlabel onjuist: {fout}"
    return True, "beide stappen voltooid, oordeel vrijgegeven, status correct" + (
        " en elk buurlabel correct" if volledig else ""
    )


def _stop_bij_bewaking(sleutel: str, schending: str | None, *fouten: Any) -> None:
    """Stop de run bij een bewakingsweigering (T en G).

    Leidend is de weigering op de reservering zelf (`schending`): een hogere
    laag (`AIServiceV2`) pakt de `BudgetSchendingError` in zonder klassenaam.
    De tekstcontrole blijft als vangnet.
    """
    if schending is not None or any(
        f and "BudgetSchendingError" in str(f) for f in fouten
    ):
        msg = f"bewaking greep in bij {sleutel}: run gestopt"
        raise gb.BudgetSchendingError(msg)


class GevalGestoptError(gb.BudgetSchendingError):
    """De run stopt na een gestarte (en dus meegetelde) aanroep; draagt zijn resultaat.

    Zo komt ook een afgewezen, betaalde stap in `resultaten` van de
    samenvatting; stopregel en budgetboekhouding blijven ongewijzigd.
    """

    def __init__(self, msg: str, resultaat: dict[str, Any]) -> None:
        super().__init__(msg)
        self.resultaat = resultaat


def _stop_met_resultaat(
    resultaat: dict[str, Any],
    sleutel: str,
    schending: str | None,
    acceptatie: Mapping[str, Any] | None,
    *fouten: Any,
) -> None:
    """Bewakingsweigering of niet-geaccepteerd geval: stop, met het resultaat erbij."""
    try:
        _stop_bij_bewaking(sleutel, schending, *fouten)
    except gb.BudgetSchendingError as exc:
        raise GevalGestoptError(str(exc), resultaat) from exc
    if acceptatie is not None and not acceptatie["geaccepteerd"]:
        msg = (
            f"{sleutel}: geval niet geaccepteerd ({acceptatie['reden']}); proef gestopt"
        )
        raise GevalGestoptError(msg, resultaat)


def _grootboek(opslag: Proefopslag, nieuw: bool, proef: Proef) -> gb.Grootboek:
    pad, identiteit = opslag.grootboek, proef.identiteit
    if nieuw:
        return gb.Grootboek.nieuw(pad, identiteit=identiteit)
    return gb.Grootboek.open(pad, identiteit=identiteit)


def _lees_voorganger(
    omg: Omgeving,
    proef: Proef,
    voorganger_opslag: Proefopslag | Sequence[Proefopslag] | None,
) -> tuple[gb.Grootboek, ...] | None:
    """De grootboeken van alle vorige rondes, nieuwste eerst, alleen-lezen.

    Zonder `voorganger_opslag` de canonieke; echte calls tellen uitsluitend
    tegen de canonieke. Eén opslag geldt voor de directe voorganger; een
    keten moet volledig zijn (R3: R2 dan R1). Ontbreekt of wijkt een schakel
    af, dan faalt dit vóór er iets wordt aangemaakt of gereserveerd.
    """
    keten = gb.voorgangerketen(proef.identiteit)
    if not keten:
        return None
    canoniek = tuple(
        next(p.opslag for p in PROEVEN.values() if p.identiteit is vorige)
        for vorige in keten
    )
    if voorganger_opslag is None:
        opslagen = canoniek
    elif isinstance(voorganger_opslag, Proefopslag):
        opslagen = (voorganger_opslag,)
    else:
        opslagen = tuple(voorganger_opslag)
    if len(opslagen) != len(keten):
        msg = (
            f"voorgangerketen onvolledig: {len(opslagen)} opslag(en) voor "
            f"{[v.proef_id for v in keten]}; niets aangemaakt of gereserveerd"
        )
        raise gb.BudgetSchendingError(msg)
    for opslag, vast in zip(opslagen, canoniek, strict=True):
        if omg.echt and Path(opslag.root).resolve() != vast.root.resolve():
            msg = f"echte calls tellen alleen tegen het canonieke {vast.grootboek}"
            raise gb.BudgetSchendingError(msg)
    return tuple(
        gb.Grootboek.lees(opslag.grootboek, identiteit=vorige)
        for opslag, vorige in zip(opslagen, keten, strict=True)
    )


def _controleer_voorganger(
    boek: gb.Grootboek, voorganger: tuple[gb.Grootboek, ...] | None, aantal: int
) -> dict[str, Any] | None:
    """Cumulatieve grens met alle vorige rondes; stand van de directe voorganger.

    `keten` en `keten_totaal` tonen elke meegetelde ronde.
    """
    if voorganger is None:
        return None
    gb.controleer_cumulatief(boek, voorganger, aantal)
    keten = [
        {"proef_id": b.identiteit.proef_id, "totaal": b.samenvatting()["totaal"]}
        for b in voorganger
    ]
    return {
        **voorganger[0].samenvatting(),
        "keten": keten,
        "keten_totaal": sum(k["totaal"] for k in keten),
        "cumulatief_max": boek.identiteit.cumulatief_max,
    }


def _fase_van(proef: Proef, fase: str, toegestaan: Sequence[str]) -> None:
    if fase not in toegestaan or fase not in proef.identiteit.fasecaps:
        msg = f"fase {fase!r} bestaat niet in ronde {proef.naam}"
        raise gb.BudgetSchendingError(msg)


# --- freeze (ronde 2) -----------------------------------------------------------------

FREEZESCHEMA = "def768-r2-eindfreeze/1"
#: Velden die, indien aanwezig in de freeze, gelijk moeten zijn aan de run.
_FREEZE_OPTIONEEL = ("dataset_sha256", "herhaal_ids")


def freezevelden(omg: Omgeving, proef: Proef, groep: str) -> dict[str, Any]:
    """De verplichte, uit de gebouwde omgeving berekende freezevelden."""
    from services.validation.ess05_assessment_service import _systeemprompt

    velden: dict[str, Any] = {
        "schema": FREEZESCHEMA,
        "proef_id": proef.identiteit.proef_id,
        "groep": groep,
        "code_sha256": code_sha256(),
        "effectieve_config_sha256": pi.sha_json(effectieve_config(omg)),
    }
    if groep in ("t", "v"):  # R8: V bevriest op dezelfde T-code en -configuratie
        velden["prompt_version"] = omg.dienst.PROMPT_VERSION
        velden["verification_prompt_version"] = (
            omg.dienst.verification_service.PROMPT_VERSION
        )
        velden["system_prompt_sha256"] = _sha_tekst(_systeemprompt(omg.norm))
        velden["norm_sha256"] = omg.dienst.norm_sha256
        if proef.contract is not None:  # R9; freezes van R8 en ouder ongewijzigd
            velden.update(contractidentiteit(omg))
    else:
        velden["g_actueel_instructie_sha256"] = _sha_tekst(pi.huidige_g_instructie())
    return velden


def controleer_freeze(
    pad: Path | None,
    omg: Omgeving,
    proef: Proef,
    groep: str,
    *,
    dataset_sha256: str,
    herhaal_ids: list[str],
) -> str:
    """sha256 van het freezebestand, na vergelijking met de huidige run.

    Elk verplicht veld (`freezevelden`) moet exact gelijk zijn; dataset en
    herhaal_ids alleen als de freeze ze al vastlegt (een freeze vóór de
    vrijgave van de eindset kent de dataset nog niet; het grootboek bindt hem
    dan bij de eerste eindreservering). Andere velden zijn vrije toelichting.
    """
    if pad is None:
        msg = f"ronde {proef.naam}, eindgroep {groep!r}: --freeze is verplicht"
        raise gb.BudgetSchendingError(msg)
    try:
        freeze = json.loads(Path(pad).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"freeze {pad} is onleesbaar: {exc}"
        raise gb.BudgetSchendingError(msg) from exc
    verwacht = freezevelden(omg, proef, groep)
    run = {"dataset_sha256": dataset_sha256, "herhaal_ids": list(herhaal_ids)}
    afwijkend = [k for k, v in verwacht.items() if freeze.get(k) != v] + [
        k for k in _FREEZE_OPTIONEEL if k in freeze and freeze[k] != run[k]
    ]
    if afwijkend:
        msg = (
            f"freeze {Path(pad).name} past niet bij deze run (afwijkend of "
            f"ontbrekend: {afwijkend}); geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)
    return _sha_bestand(pad)


class _Deadline:
    def __init__(self, totaal: float | None) -> None:
        self._totaal = totaal
        self._start = time.monotonic()

    def past(self, nodig: float) -> bool:
        if self._totaal is None:
            return True
        return self._totaal - (time.monotonic() - self._start) >= nodig


# --- omgeving -----------------------------------------------------------------------


@dataclass
class Omgeving:
    """De productieketen boven de (bewaakte) providergrens."""

    ai: Any
    dienst: Any
    router: Any
    norm: dict[str, str]
    timeout: int
    sdk_bewaakt: bool
    geheimen: tuple[str, ...]
    modelconfig: dict[str, Any]
    g_temperatuur: float
    #: Echte (betaalde) providerclient: alleen tegen de canonieke opslag.
    echt: bool = False

    def netwerk_gestart(self, reservering: gb.Reservering) -> bool:
        """Met SDK-wacht: gemeten; zonder (tests): conservatief = client aangeroepen."""
        if self.sdk_bewaakt:
            return reservering.netwerk_gestart
        return reservering.client_aanroepen > 0

    def prijs(self, route: str) -> tuple[dict[str, float], bool]:
        """Tarief van het gevraagde routemodel (`t`/`g`), niet van een SDK-alias.

        Staat het model niet in de pricing-config, dan is het tarief onbekend
        (de terugvalprijs van de router wordt dan niet gebruikt).
        """
        model = self.modelconfig[route]["model"]
        bekend = bool(model) and model in self.router.get_active_pricing()
        return self.router.get_pricing(model or ""), bekend


def bouw_omgeving(
    provider_client: Any,
    router: Any,
    *,
    timeout: int,
    max_tokens_t: int,
    sdk_bewaakt: bool,
    geheimen: tuple[str, ...],
    echt: bool = False,
    verifier_max_tokens: int | None = None,
) -> Omgeving:
    """`verifier_max_tokens` (R8): expliciete verifier met deze grens en dezelfde
    deadline, zoals de container hem bouwt; None = de interne standaardverifier."""
    from config.config_manager import get_prompt_temperature
    from services.ai_service_v2 import AIServiceV2
    from services.validation.ess05_assessment_service import (
        Ess05AssessmentService,
        laad_ess05_norm,
    )
    from services.validation.ess05_verification_service import (
        Ess05VerificationService,
    )

    bewaakt = gb.BewaakteClient(provider_client)
    ai = AIServiceV2(use_cache=False, ai_client=bewaakt, model_router=router)
    verifier = (
        Ess05VerificationService(
            ai,
            model_router=router,
            timeout_seconds=timeout,
            max_tokens=verifier_max_tokens,
        )
        if verifier_max_tokens is not None
        else None
    )
    dienst = Ess05AssessmentService(
        ai,
        model_router=router,
        timeout_seconds=timeout,
        max_tokens=max_tokens_t,
        cache_size=0,
        verification_service=verifier,
    )
    g_temperatuur = float(get_prompt_temperature("definition"))
    t_provider, t_model = router.get_model("validation")
    g_provider, g_model = router.get_model("definition_core")
    v_provider, v_model = dienst.verification_service.modelsleutel()
    modelconfig = {
        "t": {
            "task_type": "validation",
            "provider": t_provider,
            "model": t_model,
            "temperature_requested": 0.0,
            "temperature_sent": (
                0.0
                if router.accepts_temperature(t_model, provider=t_provider)
                else None
            ),
            "thinking_expliciet_uit": router.thinking_default_on(
                t_model, provider=t_provider
            ),
            "max_tokens": max_tokens_t,
            "prompt_version": dienst.PROMPT_VERSION,
            "norm_sha256": dienst.norm_sha256,
        },
        # ADR-003: tarief en route van de tweede stap (kosten per reservering).
        "t_verificatie": {
            "task_type": dienst.verification_service.TASK_TYPE,
            "provider": v_provider,
            "model": v_model,
        },
        "g": {
            "route": "AIServiceV2.default_model (definition_core), model=None zoals productie",
            "provider": g_provider,
            "model": g_model,
            "temperature_requested": g_temperatuur,
            "temperature_sent": (
                g_temperatuur
                if router.accepts_temperature(g_model, provider=g_provider)
                else None
            ),
            "max_tokens": G_MAX_TOKENS,
        },
        "timeout_s": timeout,
        "buitenste_marge_s": MARGE_S,
        "ai_service_cache": False,
        "dienst_cache_size": 0,
        "optins": {"use_cache": False, "max_attempts": 1, "max_retries": 0},
        "AI_SDK_MAX_RETRIES": os.environ.get("AI_SDK_MAX_RETRIES"),
        "AI_SDK_MAX_RETRIES_vooraf_in_omgeving": _SDK_RETRIES_VOORAF_GEZET,
        "sdk_wacht_actief": sdk_bewaakt,
    }
    return Omgeving(
        ai=ai,
        dienst=dienst,
        router=router,
        norm=laad_ess05_norm(),
        timeout=timeout,
        sdk_bewaakt=sdk_bewaakt,
        geheimen=geheimen,
        modelconfig=modelconfig,
        g_temperatuur=g_temperatuur,
        echt=echt,
    )


def _laad_env() -> str:
    from config.dotenv_loader import load_project_dotenv

    for pad in (
        PROJECT_ROOT / ".env",
        Path.home() / "Projecten" / "Definitie-app" / ".env",
    ):
        if pad.is_file():
            load_project_dotenv(pad=pad, force=True)
            return str(pad)
    return "geen .env gevonden"


def live_omgeving(
    *, timeout: int, max_tokens_t: int, verifier_max_tokens: int | None = None
) -> Omgeving:
    """De echte providerclient met SDK-wacht; sleutel alleen op aanwezigheid gecontroleerd."""
    import anthropic.resources.messages as sdk_messages

    from config.config_manager import get_config_manager
    from services.ai import create_ai_client
    from services.ai.model_router import ModelRouter

    logger.info(".env geladen uit: %s (waarden worden niet getoond)", _laad_env())
    config = get_config_manager()
    provider = config.api.ai_provider
    if provider != "anthropic":
        msg = (
            f"SDK-bewaking is alleen voor 'anthropic' gebouwd; provider is {provider!r}"
        )
        raise SystemExit(msg)
    sleutel = config.api.anthropic_api_key
    logger.info("API-sleutel voor %s aanwezig: %s", provider, bool(sleutel))
    if not sleutel:
        msg = "geen API-sleutel in omgeving/.env; geen call gedaan"
        raise SystemExit(msg)
    gb.installeer_sdk_wacht(sdk_messages.AsyncMessages)
    client = create_ai_client(
        provider=provider, api_key=sleutel, timeout=float(timeout)
    )
    return bouw_omgeving(
        client,
        ModelRouter.from_config(),
        timeout=timeout,
        max_tokens_t=max_tokens_t,
        sdk_bewaakt=True,
        geheimen=(sleutel,),
        echt=True,
        verifier_max_tokens=verifier_max_tokens,
    )


def effectieve_config(omg: Omgeving) -> dict[str, Any]:
    """De werkelijk toegepaste, niet-geheime model-/promptconfiguratie (binding).

    Gelezen uit de gebouwde omgeving zelf — de ESS-05-dienst (binding, maxtokens,
    timeout, passagegrens), de router (route per taak, temperatuur- en
    thinkingbeleid van dát model) en de promptservice (complete-promptgrens) —
    niet uit een parallel configobject. Budgetknoppen (`--max-calls`,
    `--totaal-deadline`) zijn geen generatie-instelling en vallen erbuiten.
    Bevat de configuratie een geheim, dan wordt zij geweigerd.
    """
    dienst, router = omg.dienst, omg.router
    t_binding = dienst.binding().als_dict()
    t_provider, t_model = t_binding["provider"], t_binding["model"]
    g_provider, g_model = router.get_model("definition_core")
    t_temperatuur = 0.0  # Ess05AssessmentService.assess: temperature=0.0
    cfg: dict[str, Any] = {
        "schema": "def768-ess05-effectieve-config/1",
        "t": {
            **t_binding,
            "task_type": dienst.TASK_TYPE,
            "temperature_requested": t_temperatuur,
            "temperature_sent": (
                t_temperatuur
                if router.accepts_temperature(t_model, provider=t_provider)
                else None
            ),
            "thinking_expliciet_uit": router.thinking_default_on(
                t_model, provider=t_provider
            ),
            "max_tokens": dienst._max_tokens,
            "timeout_s": dienst._timeout_seconds,
            "max_passage_chars": dienst._max_passage_chars,
            "dienst_cache_size": dienst._cache_size,
        },
        # ADR-003: de tweede, afzonderlijke stap (semantische verificatie).
        "t_verificatie": _verifierconfig(dienst.verification_service, router),
        "g": {
            "task_type": "definition_core",
            "provider": g_provider,
            "model": g_model,
            "temperature_requested": omg.g_temperatuur,
            "temperature_sent": (
                omg.g_temperatuur
                if router.accepts_temperature(g_model, provider=g_provider)
                else None
            ),
            "thinking_expliciet_uit": router.thinking_default_on(
                g_model, provider=g_provider
            ),
            "max_tokens": G_MAX_TOKENS,
            "max_prompt_length": pi.g_promptgrens(),
        },
        "transport": {
            "timeout_s": omg.timeout,
            "buitenste_marge_s": MARGE_S,
            "ai_service_cache": omg.modelconfig["ai_service_cache"],
            "optins": omg.modelconfig["optins"],
            "AI_SDK_MAX_RETRIES": omg.modelconfig["AI_SDK_MAX_RETRIES"],
            "sdk_wacht_actief": omg.sdk_bewaakt,
        },
    }
    tekst = json.dumps(cfg, sort_keys=True, ensure_ascii=False)
    if any(geheim and geheim in tekst for geheim in omg.geheimen):
        msg = "effectieve configuratie bevat een geheim; niet vastgelegd of gebonden"
        raise gb.BudgetSchendingError(msg)
    return cfg


def _verifierconfig(verifier: Any, router: Any) -> dict[str, Any]:
    """Route, model, prompt en grenzen van de verificatiestap (uit de dienst)."""
    provider, model = verifier.modelsleutel()
    temperatuur = 0.0  # eenmalige_aanroep: temperature=0.0
    return {
        "task_type": verifier.TASK_TYPE,
        "provider": provider,
        "model": model,
        "prompt_version": verifier.PROMPT_VERSION,
        "temperature_requested": temperatuur,
        "temperature_sent": (
            temperatuur
            if router.accepts_temperature(model, provider=provider)
            else None
        ),
        "thinking_expliciet_uit": router.thinking_default_on(model, provider=provider),
        "max_tokens": verifier.max_tokens,
        "timeout_s": verifier.timeout_seconds,
    }


# --- planning -------------------------------------------------------------------------


def plan_t(
    fase: str, gevallen: list[dict[str, Any]], herhaal: list[str]
) -> list[tuple[str, dict[str, Any]]]:
    if fase == "t_herhaling":
        per_id = {g["id"]: g for g in gevallen}
        return [
            (f"t_herhaling|{gid}|herhaling-{n}", per_id[gid])
            for gid in herhaal
            for n in (1, 2)
        ]
    return [(f"{fase}|{g['id']}|1", g) for g in gevallen]


def _lege_ruimte(geval: dict[str, Any]) -> Any:
    if isinstance(geval.get("lege_ruimte_bevestiging"), dict):
        return pi.bind_lege_ruimte(
            pi.modelprojectie(geval), geval["lege_ruimte_bevestiging"]
        )
    return geval.get("lege_ruimte")


def _selecteer(
    plan: list[tuple[str, Any]],
    boek: gb.Grootboek,
    herhalingen: Sequence[str],
) -> tuple[list[tuple[str, Any, bool]], int]:
    """(uit te voeren (sleutel, item, technisch), aantal overgeslagen)."""
    if herhalingen:
        bekend = {s for s, _ in plan}
        onbekend = [h for h in herhalingen if h not in bekend]
        if onbekend:
            msg = f"--technische-herhaling voor onbekende sleutel(s): {onbekend}"
            raise gb.BudgetSchendingError(msg)
        return [(s, item, True) for s, item in plan if s in herhalingen], 0
    open_ = [(s, item, False) for s, item in plan if not boek.poging_gestart(s)]
    return open_, len(plan) - len(open_)


def _controleer_plan(
    boek: gb.Grootboek, fase: str, aantal: int, technisch: bool, stappen: int = 1
) -> None:
    """Past het plan, met elke modelstap als eigen call, nog in het budget?

    Alleen een vooraftoets: er wordt niets gereserveerd; elke stap reserveert
    pas bij haar aanroep.
    """
    stand = boek.samenvatting()
    identiteit = boek.identiteit
    if technisch:
        vrij = identiteit.reserve_max - stand["reserve"]
        soort = "technische reserve"
    else:
        vrij = identiteit.fasecaps[fase] - stand["per_fase"][fase]
        soort = f"fasecap {fase}"
    vrij = min(vrij, identiteit.totaal_max - stand["totaal"])
    aantal *= stappen
    if aantal > vrij:
        msg = f"plan vraagt {aantal} calls; {soort} laat nog {vrij} toe (niets gestart)"
        raise gb.BudgetSchendingError(msg)


def _eindbinding(
    omg: Omgeving,
    proef: Proef,
    groep: gb.Eindgroep | None,
    freeze: Path | None,
    *,
    dataset_sha256: str,
    herhaal_ids: list[str],
    code_sha256: str,
    config_sha256: str,
) -> dict[str, Any] | None:
    """De binding van een eindgroep (None erbuiten), met freeze waar vereist."""
    if groep is None:
        if freeze is not None:
            msg = "--freeze hoort alleen bij een eindfase"
            raise gb.BudgetSchendingError(msg)
        return None
    binding: dict[str, Any] = {
        "dataset_sha256": dataset_sha256,
        "herhaal_ids": list(herhaal_ids),
        "code_sha256": code_sha256,
        "config_sha256": config_sha256,
    }
    if proef.freeze_vereist:
        binding["freeze_sha256"] = controleer_freeze(
            freeze,
            omg,
            proef,
            groep.naam,
            dataset_sha256=dataset_sha256,
            herhaal_ids=herhaal_ids,
        )
    elif freeze is not None:
        msg = f"ronde {proef.naam} kent geen --freeze"
        raise gb.BudgetSchendingError(msg)
    return binding


# --- T ------------------------------------------------------------------------------------


def _afsluitstatus_t(document: dict[str, Any], netwerk: bool) -> str:
    if document.get("status") == "assessed":
        return "voltooid"
    soort = (document.get("error") or {}).get("type")
    if soort in _TECHNISCHE_FOUTEN:
        return "technisch" if netwerk else "niet_verzonden"
    if soort == "input_truncated":
        return "niet_verzonden"
    return "modelfout"


def _vergelijk(
    geval: dict[str, Any],
    prompt: pi.TPrompt,
    document: dict[str, Any] | None,
    uitkomst: dict[str, Any],
) -> dict[str, Any]:
    term_per_id = {b.id: b.term for b in prompt.buren}
    # ADR-003: `judgment` is alleen weergave; tel het uitsluitend als de replay
    # het oordeel (concept + geldige verificatie) daadwerkelijk toepaste.
    toegepast = ((uitkomst.get("review") or {}).get("assessment") or {}).get("applied")
    oordeel = ((document or {}).get("judgment") or {}) if toegepast else {}
    gekregen = {
        term_per_id.get(n.get("neighbour_id")): n
        for n in oordeel.get("neighbours") or []
    }
    per_buur = []
    for verwachting in pi.per_buur_verwachtingen(geval):
        oordeel_buur = gekregen.get(verwachting["term"]) or {}
        per_buur.append(
            {
                "term": verwachting["term"],
                "verwacht": verwachting["distinction"],
                "gekregen": oordeel_buur.get("distinction"),
                "correct": oordeel_buur.get("distinction")
                == verwachting["distinction"],
                # Uitgebreide verwachting (citaat, kenmerk, grond) voor de
                # inhoudelijke beoordeling; niet automatisch gescoord.
                "verwachting": verwachting,
                "gekregen_citaat": oordeel_buur.get("distinguishing_feature_quote"),
                "gekregen_kenmerk": oordeel_buur.get("missing_feature"),
            }
        )
    return {
        "verwacht": geval["verwacht"],
        "gekregen": uitkomst.get("status"),
        "status_correct": uitkomst.get("status") == geval["verwacht"],
        "lacks_differentia": oordeel.get("lacks_differentia"),
        "per_buur": per_buur,
        "vraag": (uitkomst.get("review") or {}).get("question"),
        "voorstellen": (uitkomst.get("review") or {}).get("proposals"),
        "rubric": {
            "bron": "runplan v2 §5.4",
            "criteria": [
                "juiste relevante buur",
                "werkelijk onderscheidend of ontbrekend kenmerk",
                "steun in bron of bedoelde betekenis",
                "juiste omgang met overlap en onzekerheid",
                "geen verzonnen feit of bron",
            ],
            "beoordeling": None,
        },
    }


def _faseregistratie(document: dict[str, Any] | None) -> dict[str, Any]:
    """Beide stappen afzonderlijk: attributie, tijd en ruwe-antwoordhash (ADR-003)."""
    doc = document or {}
    fout = doc.get("error") or {}
    fasen: dict[str, Any] = {}
    for fase, attributie, tijd, ruw, prompt in (
        (
            "beoordeling",
            "attribution",
            "assessed_at",
            "raw_response_sha256",
            "prompt_version",
        ),
        (
            "verificatie",
            "verification_attribution",
            "verified_at",
            "verification_raw_response_sha256",
            "verification_prompt_version",
        ),
    ):
        attr = doc.get(attributie) or {}
        fasen[fase] = {
            "task_type": attr.get("task_type"),
            "provider": attr.get("provider"),
            "model": attr.get("model"),
            "tokens_used": attr.get("tokens_used"),
            "prompt_version": doc.get(prompt),
            "tijd": doc.get(tijd),
            "raw_response_sha256": doc.get(ruw),
            "fout": fout if fout.get("phase") == _FOUTFASE[fase] else None,
        }
    return fasen


_FOUTFASE = {"beoordeling": "assessment", "verificatie": "verification"}


_FOUTSTAP = {fase: stap for stap, fase in _FOUTFASE.items()}
#: Tariefroute (`Omgeving.prijs`) per modelstap.
_PRIJSROUTE = {"beoordeling": "t", "verificatie": "t_verificatie"}


def _stapstatus(
    document: dict[str, Any] | None,
    stap: str,
    *,
    laatste: bool,
    netwerk: bool,
    afbraak: str,
) -> str:
    """Afsluitstatus van één stapreservering.

    Een latere stap start alleen na een verwerkt antwoord van de vorige, dus
    een eerdere stap is `voltooid`. Zonder document (afgebroken of onverwachte
    fout) krijgt de lopende stap `technisch` na netwerkstart, anders `afbraak`.
    Met document bepaalt de fout van díe stap de status (zie `_afsluitstatus_t`).
    """
    if document is None:
        if not laatste:
            return "voltooid"
        return "technisch" if netwerk else afbraak
    fout = document.get("error") or {}
    if document.get("status") == "assessed" or _FOUTSTAP.get(fout.get("phase")) != stap:
        return "voltooid"
    return _afsluitstatus_t(document, netwerk)


def _sluit_stappen(
    omg: Omgeving,
    boek: gb.Grootboek,
    poging: gb.Stappenpoging,
    document: dict[str, Any] | None,
    afbraak: str,
) -> list[dict[str, Any]]:
    """Sluit elke gemaakte stapreservering af; geeft per stap de afsluiting."""
    statussen = [
        _stapstatus(
            document,
            stap,
            laatste=index == len(poging.gereserveerd) - 1,
            netwerk=omg.netwerk_gestart(reservering),
            afbraak=afbraak,
        )
        for index, (stap, _, reservering) in enumerate(poging.gereserveerd)
    ]
    return _sluit_met_statussen(omg, boek, poging, statussen)


def _sluit_met_statussen(
    omg: Omgeving,
    boek: gb.Grootboek,
    poging: gb.Stappenpoging,
    statussen: list[str],
) -> list[dict[str, Any]]:
    """Sluit elke stapreservering met haar status; onder kostenbewaking met de
    werkelijke kosten uit de SDK-usage (None zonder usage: dan telt de grens)."""
    kb = boek.identiteit.kostenbewaking
    gesloten = []
    for (stap, res, reservering), status in zip(
        poging.gereserveerd, statussen, strict=True
    ):
        kosten = gb.kosten_nusd(reservering.sdk, kb) if kb is not None else None
        boek.sluit(
            res["seq"],
            status,
            netwerk_gestart=omg.netwerk_gestart(reservering),
            details={
                "client_aanroepen": reservering.client_aanroepen,
                "sdk_aanroepen": reservering.sdk_aanroepen,
            },
            kosten_werkelijk_nusd=kosten,
        )
        gesloten.append(
            {
                "stap": stap,
                "res": res,
                "reservering": reservering,
                "status": status,
                "kosten_nusd": kosten,
            }
        )
    return gesloten


def _stapregistratie(
    omg: Omgeving, gesloten: list[dict[str, Any]], document: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Per reservering: identiteit, afsluiting, ruw antwoord, attributie, kosten."""
    fasen = _faseregistratie(document)
    taken = {naam: taak for taak, naam in t_stappen(omg.dienst)}
    registratie = []
    for item in gesloten:
        stap, res, reservering = item["stap"], item["res"], item["reservering"]
        tekst = reservering.antwoord.get("text")
        prijs, bekend = omg.prijs(_PRIJSROUTE[stap])
        registratie.append(
            {
                "stap": stap,
                # Ook zonder document (annulering) blijft de stap herleidbaar.
                "task_type": taken.get(stap),
                "seq": res["seq"],
                "sleutel": res["sleutel"],
                "poging": res.get("poging"),
                "budget_bron": res["budget_bron"],
                "afsluitstatus": item["status"],
                "netwerk_gestart": omg.netwerk_gestart(reservering),
                "client_aanroepen": reservering.client_aanroepen,
                "sdk_aanroepen": reservering.sdk_aanroepen,
                "bewakingsweigering": reservering.schending,
                "ruw_antwoord": tekst,
                "ruw_antwoord_sha256": (
                    _sha_tekst(tekst) if isinstance(tekst, str) else None
                ),
                "attributie": fasen[stap],
                "transport": {
                    "client": {
                        k: v for k, v in reservering.antwoord.items() if k != "text"
                    },
                    "sdk": reservering.sdk,
                },
                "kosten": gb.kosten(reservering.sdk, prijs, prijs_bekend=bekend),
                # R8: begrote grens, gemeten payload en werkelijke kosten (nUSD).
                "kosten_grens_nusd": res.get("kosten_grens_nusd"),
                "payload_bytes": reservering.payload_bytes,
                "kosten_nusd": item.get("kosten_nusd"),
            }
        )
    return registratie


def _tokens(stappen: list[dict[str, Any]]) -> dict[str, int] | None:
    """Werkelijke SDK-usage over de stappen, alleen als elke stap usage heeft."""
    usages = [(s["transport"]["sdk"] or {}).get("usage") or {} for s in stappen]
    invoer = [u.get("input_tokens") for u in usages]
    uitvoer = [u.get("output_tokens") for u in usages]
    if not stappen or not all(isinstance(t, int) for t in invoer + uitvoer):
        return None
    return {"input": sum(invoer), "output": sum(uitvoer)}


def _totaalkosten(stappen: list[dict[str, Any]]) -> float | None:
    """Som over de stappen, alleen als elke stap bekende kosten heeft."""
    bedragen = [s["kosten"].get("usd") for s in stappen]
    if not bedragen or any(b is None for b in bedragen):
        return None
    return round(sum(bedragen), 6)


async def _t_call(
    omg: Omgeving,
    boek: gb.Grootboek,
    *,
    fase: str,
    sleutel: str,
    geval: dict[str, Any],
    bestand_sha: str,
    binding: dict[str, Any] | None,
    code_sha: str,
    config_sha: str,
    callmap: Path,
    besluit: str | None = None,
) -> dict[str, Any]:
    """Eén T-geval; elke modelstap reserveert bij haar aanroep (`Stappenpoging`).

    `besluit` (echte R8-run): hash van het budgetbesluit, in elke reservering.
    """
    from services.validation.ess05_verification_service import aanroepgrens

    projectie = pi.modelprojectie(geval)
    prompt = pi.bouw_t_prompt(projectie, omg.norm)
    pi.controleer_afscherming(geval, prompt.teksten, omg.norm)
    intentie = pi.intentie(projectie)
    poging = gb.Stappenpoging(
        boek,
        fase=fase,
        poging=sleutel,
        stappen=t_stappen(omg.dienst),
        invoer_sha256=bestand_sha,
        binding=binding,
        details={
            "geval": geval["id"],
            "prompt_sha256": prompt.sha256,
            "code_sha256": code_sha,
            "config_sha256": config_sha,
            **({"budgetbesluit_sha256": besluit} if besluit else {}),
        },
    )
    document, fout, afbraak = None, None, "afgebroken"
    # BC-04: een annulering wordt pas doorgegeven nadat het callrecord met
    # het al beschikbare stapbewijs is geschreven (zie onder).
    annulering: asyncio.CancelledError | None = None
    start = time.perf_counter()
    try:
        with aanroepgrens(poging.stap):
            beoordeling = await asyncio.wait_for(
                omg.dienst.assess(
                    projectie["begrip"],
                    projectie["tekst"],
                    projectie.get("context") or {},
                    prompt.bronnen_ruw,
                    buren=prompt.buren_ruw,
                    intentie=intentie,
                    uitgesloten_termen=projectie.get("uitgesloten_termen") or (),
                    correlation_id=f"def768-wp7-{sleutel}",
                ),
                timeout=_buitenste_deadline(omg, len(t_stappen(omg.dienst))),
            )
        document = beoordeling.als_dict()
    except TimeoutError:
        fout = "buitenste deadline verstreken; aanroep geannuleerd"
    except Exception as exc:
        fout = gb.scrub(f"{type(exc).__name__}: {exc}")
        afbraak = "niet_verzonden"
    except asyncio.CancelledError as exc:
        fout = "aanroep geannuleerd; wordt na registratie doorgegeven"
        annulering = exc
    finally:
        gesloten = _sluit_stappen(omg, boek, poging, document, afbraak)
    duur = round(time.perf_counter() - start, 3)
    uitkomst = pi.replay(
        projectie,
        lege_ruimte=_lege_ruimte(geval),
        assessment=document,
        binding=omg.dienst.binding(),
    )
    attributie = (document or {}).get("attribution") or {}
    stappen = _stapregistratie(omg, gesloten, document)
    status = stappen[-1]["afsluitstatus"] if stappen else "niet_verzonden"
    eerste_seq = stappen[0]["seq"] if stappen else None
    record = {
        "schema": "def768-ess05-proefcall/2",
        "fase": fase,
        "sleutel": sleutel,
        "seq": eerste_seq,
        "budget_bron": stappen[0]["budget_bron"] if stappen else None,
        "geval_id": geval["id"],
        "invoerbestand_sha256": bestand_sha,
        "geval_sha256": pi.sha_json(geval),
        "modelprojectie_sha256": pi.sha_json(projectie),
        "afsluitstatus": status,
        "fout": fout,
        "duur_s": duur,
        "prompt": {
            "system": prompt.teksten[0],
            "user": prompt.teksten[1],
            "sha256": prompt.sha256,
            "system_sha256": _sha_tekst(prompt.teksten[0]),
            "user_sha256": _sha_tekst(prompt.teksten[1]),
            "komt_overeen_met_dienst": (
                (document or {}).get("input", {}).get("prompt_sha256") == prompt.sha256
            ),
        },
        "ruw_antwoord": stappen[0]["ruw_antwoord"] if stappen else None,
        "ruw_antwoord_sha256": (document or {}).get("raw_response_sha256"),
        "fasen": _faseregistratie(document),
        # ADR-003 WP5: één reservering per feitelijke modelaanroep.
        "reserveringen": stappen,
        "beoordelingsdocument": document,
        "uitkomst": uitkomst,
        "vergelijking": _vergelijk(geval, prompt, document, uitkomst),
        "transport": {
            "client_aanroepen": sum(s["client_aanroepen"] for s in stappen),
            "sdk_aanroepen": sum(s["sdk_aanroepen"] for s in stappen),
            "bewakingsweigering": poging.schending,
            "netwerk_gestart": any(s["netwerk_gestart"] for s in stappen),
            "attempts_observed": attributie.get("attempts_observed"),
            "retries_observed": attributie.get("retries_observed"),
            "cache": {
                "ai_service": False,
                "dienst_cache_size": 0,
                "cached": attributie.get("cached"),
            },
            "tokens_used_aiservice_raming": attributie.get("tokens_used"),
        },
        "kosten": {"usd": _totaalkosten(stappen), "per_stap": "zie reserveringen"},
        "tokens": _tokens(stappen),
        "latentie_s": {
            "beoordeling": (document or {}).get("elapsed_seconds"),
            "verificatie": (document or {}).get("verification_elapsed_seconds"),
        },
    }
    kb = boek.identiteit.kostenbewaking
    acceptatie = None
    if kb is not None and poging.gereserveerd:
        geaccepteerd, reden = _t_acceptatie(record, volledig=fase != "ontwikkeling")
        acceptatie = {"geaccepteerd": geaccepteerd, "reden": reden}
        record["acceptatie"] = acceptatie
    naam = f"{eerste_seq:03d}" if eerste_seq is not None else "geen-reservering"
    bestand = f"{naam}-{fase}-{geval['id']}.json"
    gb.schrijf_nieuw(callmap / bestand, record, geheimen=omg.geheimen)
    if acceptatie is not None:
        # Duurzaam vóór elke verdere stap: het eerste niet-geaccepteerde geval
        # (ook een annulering of bewakingsweigering) stopt de proef.
        boek.registreer_geval(
            fase, sleutel, details={"callrecord": bestand}, **acceptatie
        )
    resultaat = {
        "sleutel": sleutel,
        "id": geval["id"],
        "verwacht": geval["verwacht"],
        "gekregen": uitkomst.get("status"),
        "status_correct": uitkomst.get("status") == geval["verwacht"],
        "afsluitstatus": status,
        "reserveringen": len(stappen),
        "kosten_usd": record["kosten"]["usd"],
        "tokens": record["tokens"],
        "latentie_s": record["latentie_s"],
        "duur_s": duur,
        "geaccepteerd": (acceptatie or {}).get("geaccepteerd"),
    }
    if annulering is not None:
        raise annulering
    _stop_met_resultaat(
        resultaat,
        sleutel,
        poging.schending,
        acceptatie,
        (document or {}).get("error"),
        fout,
    )
    logger.info(
        "%s: verwacht=%s gekregen=%s afsluiting=%s %.1fs",
        sleutel,
        geval["verwacht"],
        uitkomst.get("status"),
        status,
        duur,
    )
    return resultaat


def _vooraftoets_r8_t(
    omg: Omgeving,
    proef: Proef,
    fase: str,
    gevallen: list[dict[str, Any]],
    herhaal: list[str],
) -> None:
    """R8, vóór slot en grootboek: elk geval een modelgeval, stap 1 binnen de bytegrens.

    De begroting telt elk geval als twee modelstappen; een nulcallroute zou de
    fasevolgorde (alle gevallen geaccepteerd) onhaalbaar maken. De bytes van
    stap 2 hangen af van het concept; die toetst de SDK-wacht vóór verzending.
    """
    if proef.identiteit.kostenbewaking is None:
        return
    plan = plan_t(fase, gevallen, herhaal)
    nulcall = [
        geval["id"]
        for _, geval in plan
        if pi.route(pi.modelprojectie(geval), _lege_ruimte(geval))["soort"] == "nulcall"
    ]
    if nulcall:
        msg = (
            f"ronde {proef.naam} begroot elk geval als modelgeval; nulcallroute(s) "
            f"{sorted(set(nulcall))} geweigerd — geen call gestart"
        )
        raise gb.BudgetSchendingError(msg)
    for sleutel, geval in plan:
        prompt = pi.bouw_t_prompt(pi.modelprojectie(geval), omg.norm)
        system, user = prompt.teksten
        bytes_ = _payloadbytes(omg, "t", omg.dienst._max_tokens, system, user)
        _controleer_bytegrens(proef, omg.dienst.TASK_TYPE, sleutel, bytes_)


async def voer_t_fase(
    omg: Omgeving,
    *,
    fase: str,
    gevallenpad: Path,
    uitmap: Path,
    opslag: Proefopslag,
    proef: Proef = STANDAARD_PROEF,
    freeze: Path | None = None,
    voorganger_opslag: Proefopslag | None = None,
    nieuw_grootboek: bool = False,
    technische_herhalingen: Sequence[str] = (),
    max_calls: int | None = None,
    totaal_deadline: float | None = None,
) -> dict[str, Any]:
    if fase not in T_FASES:
        msg = f"geen T-fase: {fase!r}"
        raise ValueError(msg)
    _fase_van(proef, fase, T_FASES)
    _controleer_opslag(omg, opslag, proef)
    _controleer_goedkeuring(omg, proef)
    _controleer_productiegrenzen(omg, proef)
    _controleer_kostenroute(omg, proef)
    _controleer_contract(omg, proef)
    besluit = _besluit_voor(omg, proef)
    stappen = len(t_stappen(omg.dienst))
    if technische_herhalingen:
        # Elke modelstap heeft een eigen reservering; een technische herhaling
        # daarvan (welke stap, welk budget) is niet vastgelegd.
        msg = (
            f"technische herhaling van een meerstaps-T-geval ({stappen} "
            "modelstap(pen), elk een eigen reservering) is niet vastgelegd; geen "
            "call gestart"
        )
        raise gb.BudgetSchendingError(msg)
    _controleer_ontwikkelinvoer(proef, fase, gevallenpad)
    groep = proef.identiteit.eindgroep(fase)
    data = json.loads(Path(gevallenpad).read_text(encoding="utf-8"))
    # De eindfase legt de voorafgekozen herhaal_ids al vast (eindbinding).
    gevallen, herhaal = pi.valideer_gevallenbestand(
        data, herhaal_vereist=groep is not None
    )
    bestand_sha = _sha_bestand(gevallenpad)
    code_sha = code_sha256()
    config = effectieve_config(omg)
    config_sha = pi.sha_json(config)
    binding = _eindbinding(
        omg,
        proef,
        groep,
        freeze,
        dataset_sha256=bestand_sha,
        herhaal_ids=herhaal,
        code_sha256=code_sha,
        config_sha256=config_sha,
    )
    _vooraftoets_r8_t(omg, proef, fase, gevallen, herhaal)
    deadline = _Deadline(totaal_deadline)
    with gb.Proefslot(opslag.slot):
        vorige = _lees_voorganger(omg, proef, voorganger_opslag)
        boek = _grootboek(opslag, nieuw_grootboek, proef)
        boek.controleer_fasestart(fase)
        boek.controleer_binding(fase, bestand_sha, binding)  # vóór elke call
        voor = boek.samenvatting()
        routes, plan = [], []
        for sleutel, geval in plan_t(fase, gevallen, herhaal):
            route = pi.route(pi.modelprojectie(geval), _lege_ruimte(geval))
            if route["soort"] == "nulcall":
                routes.append(
                    {
                        "id": geval["id"],
                        "reden": route["reden"],
                        "uitkomst": route["uitkomst"],
                    }
                )
            else:
                plan.append((sleutel, geval))
        selectie, overgeslagen = _selecteer(plan, boek, technische_herhalingen)
        if max_calls is not None:
            selectie = selectie[:max_calls]
        _controleer_plan(boek, fase, len(selectie), False, stappen)
        _controleer_kostenplan(boek, fase, len(selectie))
        voorganger = _controleer_voorganger(boek, vorige, len(selectie) * stappen)
        runmap = _nieuwe_map(uitmap, fase)
        resultaten, niet_gestart = [], 0
        try:
            for sleutel, geval, _technisch in selectie:
                if not deadline.past(_buitenste_deadline(omg, stappen)):
                    niet_gestart += 1
                    continue
                try:
                    resultaten.append(
                        await _t_call(
                            omg,
                            boek,
                            fase=fase,
                            sleutel=sleutel,
                            geval=geval,
                            bestand_sha=bestand_sha,
                            binding=binding,
                            code_sha=code_sha,
                            config_sha=config_sha,
                            callmap=runmap / "calls",
                            besluit=besluit,
                        )
                    )
                except GevalGestoptError as exc:
                    resultaten.append(exc.resultaat)
                    raise
        finally:
            samenvatting = _samenvatting(
                omg,
                boek,
                voor,
                fase=fase,
                invoer=gevallenpad,
                bestand_sha=bestand_sha,
                resultaten=resultaten,
                overgeslagen=overgeslagen,
                niet_gestart=niet_gestart,
                routes=routes,
                technisch=technische_herhalingen,
                config=config,
            )
            samenvatting["grootboek"] = str(opslag.grootboek)
            samenvatting["eindbinding"] = binding
            samenvatting["voorganger_grootboek"] = voorganger
            samenvatting["budgetbesluit_sha256"] = besluit
            gb.schrijf_nieuw(
                runmap / "samenvatting.json", samenvatting, geheimen=omg.geheimen
            )
    return samenvatting


def _samenvatting(
    omg: Omgeving,
    boek: gb.Grootboek,
    voor: dict[str, Any],
    *,
    fase: str,
    invoer: Path,
    bestand_sha: str,
    resultaten: list[dict[str, Any]],
    overgeslagen: int,
    niet_gestart: int,
    routes: list[dict[str, Any]],
    technisch: Sequence[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    kosten = [r["kosten_usd"] for r in resultaten]
    tokens = [r.get("tokens") for r in resultaten]
    latenties = [
        s
        for r in resultaten
        for s in (r.get("latentie_s") or {}).values()
        if isinstance(s, int | float)
    ]
    return {
        # Gemeten, niet begroot: werkelijke SDK-usage en stapduur (ontwikkelpoort).
        "tokens": (
            {
                "input": sum(t["input"] for t in tokens),
                "output": sum(t["output"] for t in tokens),
            }
            if tokens and all(tokens)
            else None
        ),
        "latentie_s_max_per_stap": max(latenties) if latenties else None,
        "schema": "def768-ess05-proefrun/1",
        "proef_id": boek.identiteit.proef_id,
        "fase": fase,
        "tijd": datetime.now(UTC).isoformat(),
        "invoer": {"pad": str(invoer), "sha256": bestand_sha},
        "identiteit": identiteit(),
        "modelconfig": omg.modelconfig,
        "effectieve_config": config,
        "effectieve_config_sha256": pi.sha_json(config),
        "technische_herhalingen": list(technisch),
        "grootboek_voor": voor,
        "grootboek_na": boek.samenvatting(),
        "aanroepen_gestart": len(resultaten),
        "overgeslagen_al_gereserveerd": overgeslagen,
        "niet_gestart_deadline": niet_gestart,
        "nulcallroutes": routes,
        "status_correct": sum(1 for r in resultaten if r.get("status_correct")),
        "kosten_usd_bekend": round(sum(k for k in kosten if k is not None), 6),
        "kosten_onbekend": sum(1 for k in kosten if k is None),
        "resultaten": resultaten,
    }


# --- V (R8: alleen de verificatiestap) -----------------------------------------------------

#: Een verificatieantwoord dat al op vorm of binding strandt, is geen
#: semantische detectie van de bekende fout.
_SCHEMAWEIGERINGEN = frozenset({"malformed_response", "candidate_hash_mismatch"})


@dataclass(frozen=True)
class _VItem:
    """Eén bevroren verifier-only-item, opnieuw gebonden aan de huidige code."""

    sleutel: str
    item: dict[str, Any]
    concept: Any
    materiaal: dict[str, str]
    regels: str
    prompt: tuple[str, str]


def valideer_v_invoer(data: Any, omg: Omgeving) -> list[_VItem]:
    """De migratie-invoer, volledig opnieuw gebonden vóór grootboek en netwerk.

    Per item: gevalhash, materiaalhashes, een structureel geldig concept met
    exact de vastgelegde hash en controles, soort en foutdragers, en een
    verificatieprompt die byte-gelijk is aan de bevroren prompt.
    """
    from domain.ess05.bewijs import verplichte_controles
    from domain.ess05.contract import valideer_concept
    from services.validation.ess05_assessment_service import _TOETSINSTRUCTIE
    from services.validation.ess05_verification_service import (
        bouw_verificatieprompt,
        prompthash,
    )

    if (
        not isinstance(data, dict)
        or data.get("schema") != mig.INVOERSCHEMA
        or not isinstance(data.get("items"), list)
        or not data["items"]
    ):
        msg = f"verifier-only-invoer heeft niet het schema {mig.INVOERSCHEMA}"
        raise pi.InvoerfoutError(msg)
    ids = [item.get("id") for item in data["items"]]
    if len(set(ids)) != len(ids):
        msg = f"verifier-only-invoer heeft dubbele ids: {ids}"
        raise pi.InvoerfoutError(msg)
    uit = []
    for item in data["items"]:
        naam = item["id"]
        geval = item["geval"]
        if pi.sha_json(geval) != item["geval_sha256"]:
            msg = f"{naam}: geval wijkt af van geval_sha256"
            raise pi.InvoerfoutError(msg)
        materiaal, buren, regels = mig.verificatiemateriaal(geval, omg.norm)
        if {m: _sha_tekst(t) for m, t in materiaal.items()} != item["materiaal_sha256"]:
            msg = f"{naam}: materiaal wijkt af van de bevroren materiaalhashes"
            raise pi.InvoerfoutError(msg)
        concept, fouten = valideer_concept(item["concept"], materiaal, buren)
        if concept is None or concept.hash != item["concept_hash"]:
            msg = f"{naam}: concept voldoet niet of concept_hash wijkt af ({fouten})"
            raise pi.InvoerfoutError(msg)
        verplicht = list(verplichte_controles(concept))
        fout = item["foutdragende_items"]
        if (
            verplicht != item["verplichte_controles"]
            or item["soort"] not in ("goed", "fout")
            or (item["soort"] == "fout") != bool(fout)
            or not set(fout) <= set(verplicht)
        ):
            msg = f"{naam}: controles, soort of foutdragende items ongeldig"
            raise pi.InvoerfoutError(msg)
        system, user = bouw_verificatieprompt(
            regels, concept, norm=omg.norm, toetsinstructie=_TOETSINSTRUCTIE
        )
        if prompthash(system, user) != item["verificatieprompt_sha256"]:
            msg = f"{naam}: verificatieprompt wijkt af van de bevroren invoer"
            raise pi.InvoerfoutError(msg)
        uit.append(
            _VItem(
                f"verificatie_alleen|{naam}|1",
                item,
                concept,
                materiaal,
                regels,
                (system, user),
            )
        )
    return uit


def _v_status(resultaat: Any, netwerk: bool, afbraak: str) -> str:
    """Afsluitstatus van de verificatiestap (zie `_afsluitstatus_t`)."""
    from domain.ess05.contract import FOUT_SEMANTISCH

    if resultaat is None:
        return "technisch" if netwerk else afbraak
    if resultaat.fout in (None, FOUT_SEMANTISCH):
        return "voltooid"
    if resultaat.fout in _TECHNISCHE_FOUTEN:
        return "technisch" if netwerk else "niet_verzonden"
    return "modelfout"


def _v_acceptatie(
    v: _VItem, resultaat: Any, status: str, schending: str | None
) -> tuple[bool, str]:
    """Goed item: vrijgave. Fout item: `unsupported` op een aangewezen foutdrager.

    Een schemaweigering, een weigering elders, alleen `undetermined` op de
    foutdrager (onzekerheid, R11-01) of een vrijgave van een fout item is geen
    detectie; een weigering van een goed item is een onnodige weigering.
    """
    from domain.ess05.contract import FOUT_SEMANTISCH

    if schending:
        return False, f"bewakingsweigering: {schending}"
    if resultaat is None:
        return False, f"runtimefout zonder verificatieresultaat ({status})"
    if resultaat.fout in _SCHEMAWEIGERINGEN:
        return False, (
            f"schemaweigering ({resultaat.fout}) telt niet als semantische detectie"
        )
    if status != "voltooid":
        return False, f"runtimefout ({status}, {resultaat.fout})"
    if v.item["soort"] == "goed":
        if resultaat.goedgekeurd:
            return True, "goed item vrijgegeven"
        return False, f"onnodige weigering van een goed item ({resultaat.fout})"
    if resultaat.goedgekeurd:
        return False, "fout item vrijgegeven: bekende fout niet gedetecteerd"
    foutdragers = set(v.item["foutdragende_items"])
    per_foutdrager = {
        b["item"]: b["outcome"]
        for b in resultaat.uitkomst.bevindingen
        if b["item"] in foutdragers
    }
    geraakt = sorted(i for i, o in per_foutdrager.items() if o == "unsupported")
    if resultaat.fout != FOUT_SEMANTISCH or not geraakt:
        if per_foutdrager:
            return False, (
                f"foutdrager niet unsupported ({per_foutdrager}): onzekerheid "
                "is geen directe detectie"
            )
        return False, "semantische weigering buiten de foutdragende items"
    return True, f"bekende fout gedetecteerd op {geraakt}"


def _verificatieregistratie(resultaat: Any) -> dict[str, Any] | None:
    if resultaat is None:
        return None
    return {
        "fout": resultaat.fout,
        "melding": resultaat.melding,
        "ruw": dict(resultaat.ruw) if resultaat.ruw else None,
        "bevindingen": (
            [dict(b) for b in resultaat.uitkomst.bevindingen]
            if resultaat.uitkomst is not None
            else []
        ),
        "raw_response_sha256": resultaat.raw_hash,
        "verified_at": resultaat.verified_at,
        "invoer": dict(resultaat.invoer),
        "attributie": dict(resultaat.attributie),
    }


async def _v_call(
    omg: Omgeving,
    boek: gb.Grootboek,
    *,
    fase: str,
    v: _VItem,
    bestand_sha: str,
    binding: dict[str, Any] | None,
    code_sha: str,
    config_sha: str,
    callmap: Path,
    besluit: str | None = None,
) -> dict[str, Any]:
    """Eén verifier-only-item: één reservering, één verificatieaanroep."""
    from services.validation.ess05_assessment_service import _TOETSINSTRUCTIE
    from services.validation.ess05_verification_service import aanroepgrens

    verifier = omg.dienst.verification_service
    poging = gb.Stappenpoging(
        boek,
        fase=fase,
        poging=v.sleutel,
        stappen=((verifier.TASK_TYPE, "verificatie"),),
        invoer_sha256=bestand_sha,
        binding=binding,
        details={
            "item": v.item["id"],
            "concept_hash": v.concept.hash,
            "prompt_sha256": v.item["verificatieprompt_sha256"],
            "code_sha256": code_sha,
            "config_sha256": config_sha,
            **({"budgetbesluit_sha256": besluit} if besluit else {}),
        },
    )
    resultaat, fout, afbraak = None, None, "afgebroken"
    annulering: asyncio.CancelledError | None = None
    start = time.perf_counter()
    try:
        with aanroepgrens(poging.stap):
            resultaat = await asyncio.wait_for(
                verifier.verifieer(
                    v.concept,
                    v.materiaal,
                    v.regels,
                    norm=omg.norm,
                    toetsinstructie=_TOETSINSTRUCTIE,
                ),
                timeout=_buitenste_deadline(omg, 1),
            )
    except TimeoutError:
        fout = "buitenste deadline verstreken; aanroep geannuleerd"
    except Exception as exc:
        fout = gb.scrub(f"{type(exc).__name__}: {exc}")
        afbraak = "niet_verzonden"
    except asyncio.CancelledError as exc:
        fout = "aanroep geannuleerd; wordt na registratie doorgegeven"
        annulering = exc
    finally:
        statussen = [
            _v_status(resultaat, omg.netwerk_gestart(r), afbraak)
            for _, _, r in poging.gereserveerd
        ]
        gesloten = _sluit_met_statussen(omg, boek, poging, statussen)
    duur = round(time.perf_counter() - start, 3)
    stappen = _stapregistratie(omg, gesloten, None)
    for stap in stappen:
        stap["attributie"] = dict(resultaat.attributie) if resultaat else None
    status = stappen[-1]["afsluitstatus"] if stappen else "niet_verzonden"
    acceptatie = None
    if stappen:
        geaccepteerd, reden = _v_acceptatie(v, resultaat, status, poging.schending)
        acceptatie = {"geaccepteerd": geaccepteerd, "reden": reden}
    system, user = v.prompt
    record = {
        "schema": "def768-ess05-verifiercall/1",
        "fase": fase,
        "sleutel": v.sleutel,
        "seq": stappen[0]["seq"] if stappen else None,
        "item_id": v.item["id"],
        "soort": v.item["soort"],
        "bron": v.item["bron"],
        "invoerbestand_sha256": bestand_sha,
        "geval_sha256": v.item["geval_sha256"],
        "concept_hash": v.concept.hash,
        "foutdragende_items": v.item["foutdragende_items"],
        "afsluitstatus": status,
        "fout": fout,
        "duur_s": duur,
        "prompt": {
            "system": system,
            "user": user,
            "sha256": v.item["verificatieprompt_sha256"],
            "komt_overeen_met_dienst": bool(resultaat)
            and resultaat.invoer.get("prompt_sha256")
            == v.item["verificatieprompt_sha256"],
        },
        "ruw_antwoord": stappen[0]["ruw_antwoord"] if stappen else None,
        "verificatie": _verificatieregistratie(resultaat),
        "reserveringen": stappen,
        "tokens": _tokens(stappen),
        "latentie_s": {
            "verificatie": round(resultaat.verstreken, 3) if resultaat else None
        },
        "kosten": {"usd": _totaalkosten(stappen), "per_stap": "zie reserveringen"},
        "acceptatie": acceptatie,
    }
    naam = f"{record['seq']:03d}" if record["seq"] is not None else "geen-reservering"
    bestand = f"{naam}-{fase}-{v.item['id']}.json"
    gb.schrijf_nieuw(callmap / bestand, record, geheimen=omg.geheimen)
    if acceptatie is not None:
        boek.registreer_geval(
            fase, v.sleutel, details={"callrecord": bestand}, **acceptatie
        )
    resultaat = {
        "sleutel": v.sleutel,
        "id": v.item["id"],
        "soort": v.item["soort"],
        "afsluitstatus": status,
        "reserveringen": len(stappen),
        "kosten_usd": record["kosten"]["usd"],
        "tokens": record["tokens"],
        "latentie_s": record["latentie_s"],
        "duur_s": duur,
        "geaccepteerd": (acceptatie or {}).get("geaccepteerd"),
        "status_correct": (acceptatie or {}).get("geaccepteerd"),
    }
    if annulering is not None:
        raise annulering
    _stop_met_resultaat(resultaat, v.sleutel, poging.schending, acceptatie, fout)
    logger.info("%s: %s %.1fs", v.sleutel, (acceptatie or {}).get("reden"), duur)
    return resultaat


async def voer_v_fase(
    omg: Omgeving,
    *,
    gevallenpad: Path,
    uitmap: Path,
    opslag: Proefopslag,
    proef: Proef,
    fase: str = "verificatie_alleen",
    freeze: Path | None = None,
    voorganger_opslag: Proefopslag | Sequence[Proefopslag] | None = None,
    nieuw_grootboek: bool = False,
    technische_herhalingen: Sequence[str] = (),
    max_calls: int | None = None,
    totaal_deadline: float | None = None,
) -> dict[str, Any]:
    """R8 verifier-only: de bevroren migratie-invoer, elk item één verificatie."""
    _fase_van(proef, fase, V_FASES)
    _controleer_opslag(omg, opslag, proef)
    _controleer_registratie(omg, proef)
    _controleer_productiegrenzen(omg, proef)
    _controleer_kostenroute(omg, proef)
    _controleer_contract(omg, proef)
    besluit = _besluit_voor(omg, proef)
    if technische_herhalingen:
        msg = "technische herhaling in de verifier-only-fase is niet vastgelegd"
        raise gb.BudgetSchendingError(msg)
    _controleer_ontwikkelinvoer(proef, fase, gevallenpad)
    items = valideer_v_invoer(
        json.loads(Path(gevallenpad).read_text(encoding="utf-8")), omg
    )
    verifier = omg.dienst.verification_service
    for v in items:
        bytes_ = _payloadbytes(omg, "t_verificatie", verifier.max_tokens, *v.prompt)
        _controleer_bytegrens(proef, verifier.TASK_TYPE, v.sleutel, bytes_)
    bestand_sha = _sha_bestand(gevallenpad)
    code_sha = code_sha256()
    config = effectieve_config(omg)
    config_sha = pi.sha_json(config)
    binding = _eindbinding(
        omg,
        proef,
        proef.identiteit.eindgroep(fase),
        freeze,
        dataset_sha256=bestand_sha,
        herhaal_ids=[],
        code_sha256=code_sha,
        config_sha256=config_sha,
    )
    deadline = _Deadline(totaal_deadline)
    with gb.Proefslot(opslag.slot):
        vorige = _lees_voorganger(omg, proef, voorganger_opslag)
        boek = _grootboek(opslag, nieuw_grootboek, proef)
        boek.controleer_fasestart(fase)
        boek.controleer_binding(fase, bestand_sha, binding)  # vóór elke call
        voor = boek.samenvatting()
        selectie, overgeslagen = _selecteer([(v.sleutel, v) for v in items], boek, ())
        if max_calls is not None:
            selectie = selectie[:max_calls]
        _controleer_plan(boek, fase, len(selectie), False, 1)
        _controleer_kostenplan(boek, fase, len(selectie))
        voorganger = _controleer_voorganger(boek, vorige, len(selectie))
        runmap = _nieuwe_map(uitmap, fase)
        resultaten, niet_gestart = [], 0
        try:
            for _sleutel, v, _technisch in selectie:
                if not deadline.past(_buitenste_deadline(omg, 1)):
                    niet_gestart += 1
                    continue
                try:
                    resultaten.append(
                        await _v_call(
                            omg,
                            boek,
                            fase=fase,
                            v=v,
                            bestand_sha=bestand_sha,
                            binding=binding,
                            code_sha=code_sha,
                            config_sha=config_sha,
                            callmap=runmap / "calls",
                            besluit=besluit,
                        )
                    )
                except GevalGestoptError as exc:
                    resultaten.append(exc.resultaat)
                    raise
        finally:
            samenvatting = _samenvatting(
                omg,
                boek,
                voor,
                fase=fase,
                invoer=gevallenpad,
                bestand_sha=bestand_sha,
                resultaten=resultaten,
                overgeslagen=overgeslagen,
                niet_gestart=niet_gestart,
                routes=[],
                technisch=(),
                config=config,
            )
            samenvatting["grootboek"] = str(opslag.grootboek)
            samenvatting["eindbinding"] = binding
            samenvatting["voorganger_grootboek"] = voorganger
            samenvatting["budgetbesluit_sha256"] = besluit
            gb.schrijf_nieuw(
                runmap / "samenvatting.json", samenvatting, geheimen=omg.geheimen
            )
    return samenvatting


# --- G --------------------------------------------------------------------------------------


def controleer_g_teksten(data: dict[str, Any]) -> tuple[str, str]:
    """(basis, actueel) na hashcontrole tegen de bevroren invoer en de code."""
    teksten = data["g_teksten"]
    basis = teksten["basis"]["tekst"]
    if _sha_tekst(basis) != teksten["basis"]["sha256"]:
        msg = "basis-G-tekst wijkt af van zijn vastgelegde hash"
        raise pi.InvoerfoutError(msg)
    actueel = pi.huidige_g_instructie()
    if _sha_tekst(actueel) != teksten["actueel"]["sha256"]:
        msg = "de actuele G-tekst in de code wijkt af van de bevroren hash"
        raise pi.InvoerfoutError(msg)
    return basis, actueel


def _basis_in_git(basis: str) -> bool | None:
    bron = _git(
        "show", f"{BASISCOMMIT}:src/services/prompts/modules/json_based_rules_module.py"
    )
    return None if bron is None else f'"ESS-05": "{basis}"' in bron


#: Wat de G-proef vergelijkt (WP7-G-kanaal): alleen de instructieregel.
VERGELIJKINGSAARD = (
    "lokale vergelijking: de enige experimentele variant is de ESS-05-"
    "instructieregel (basis versus actueel); het burentransport van de "
    "G-kanaalfix is in beide varianten byte-identiek en is zelf geen variant"
)
G_ONTWIKKELAARD = (
    "G-ontwikkeling (ronde 2): alleen de actuele variant op de bekende "
    "G1–G4-invoer van ronde 1; bekend diagnostisch materiaal, geen vergelijking "
    "en geen eindbewijs"
)
G_ONTWIKKELAARD_R3 = (
    "G-ontwikkeling (ronde 3): alleen de actuele variant op de bekende "
    "R2G1–R2G4-invoer van ronde 2; bekend diagnostisch materiaal, geen "
    "vergelijking en geen eindbewijs"
)


G_ONTWIKKELAARD_R4 = (
    "G-ontwikkeling (ronde 4): alleen de actuele variant op de bekende "
    "R3G3 (tweemaal), R2G4 en R3G1; bekend diagnostisch materiaal, geen "
    "vergelijking en geen eindbewijs"
)


G_ONTWIKKELAARD_R5 = (
    "G-ontwikkeling (ronde 5): alleen de actuele variant op de bekende "
    "R4G1 (tweemaal), R3G3 en R2G4; bekend diagnostisch materiaal, geen "
    "vergelijking en geen eindbewijs"
)


def _g_ontwikkelaard(proef: Proef) -> str:
    if proef.identiteit is gb.R5:
        return G_ONTWIKKELAARD_R5
    if proef.identiteit is gb.R4:
        return G_ONTWIKKELAARD_R4
    if proef.identiteit is gb.R3:
        return G_ONTWIKKELAARD_R3
    return G_ONTWIKKELAARD


async def g_prompts(
    data: dict[str, Any], *, alleen_actueel: bool = False
) -> list[dict[str, Any]]:
    """Per invoer beide varianten, met determinisme-, regeldiff- en burenbewijs.

    `alleen_actueel` (G-ontwikkeling, ronde 2): alleen de huidige variant op
    de bestaande invoer; de bevroren actuele hash van die invoer hoort bij
    ronde 1 en wordt dan niet vergeleken (de run legt de huidige vast).
    De regelcache wordt eerst geleegd (R2-OC-01): een verouderde cache op
    schijf zou de prompt anders stil laten afwijken van de gehashte regelbronnen.
    """
    from toetsregels.rule_cache import get_rule_cache

    get_rule_cache().clear_cache()
    if alleen_actueel:
        basis, actueel = None, pi.huidige_g_instructie()
    else:
        basis, actueel = controleer_g_teksten(data)
    uitvoer = []
    for invoer in data["invoeren"]:
        prompt, buren = await pi.bouw_g_prompt_met_buren(invoer)
        if prompt != await pi.bouw_g_prompt(invoer):
            msg = f"{invoer['id']}: promptopbouw is niet deterministisch"
            raise pi.InvoerfoutError(msg)
        if basis is None:
            uitvoer.append(
                {
                    "invoer": invoer,
                    "varianten": {"actueel": prompt},
                    "verschil": None,
                    "buren": buren,
                }
            )
            continue
        oud, verschil = pi.basisvariant(prompt, actueel, basis)
        # Beide varianten onder dezelfde complete-promptgrens (reviewpunt 5).
        pi.controleer_promptlengte(invoer["id"], "basis", oud)
        uitvoer.append(
            {
                "invoer": invoer,
                "varianten": {"actueel": prompt, "basis": oud},
                "verschil": verschil,
                "buren": buren,
            }
        )
    return uitvoer


def plan_g(prompts: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    return [
        (
            f"g|{p['invoer']['id']}|{variant}|run{run}",
            {**p, "variant": variant, "run": run},
        )
        for p in prompts
        for run in (1, 2)
        for variant in ("basis", "actueel")
    ]


def plan_g_ontwikkeling(
    prompts: list[dict[str, Any]],
) -> list[tuple[str, dict[str, Any]]]:
    """Ronde 2: per bestaande invoer één call met de actuele variant."""
    return [
        (
            f"g_ontwikkeling|{p['invoer']['id']}|actueel|run1",
            {**p, "variant": "actueel", "run": 1},
        )
        for p in prompts
    ]


def _kern(tekst: str | None, begrip: str) -> dict[str, Any]:
    from opschoning.opschoning_enhanced import (
        extract_definition_from_gpt_response,
        opschonen_enhanced,
    )
    from services.modelantwoord import lees_modelantwoord

    if not tekst:
        return {"soort": None, "kern": None, "opgeschoond": None}
    return {
        "soort": lees_modelantwoord(tekst).soort,
        "kern": extract_definition_from_gpt_response(tekst),
        "opgeschoond": opschonen_enhanced(tekst, begrip, handle_gpt_format=True),
    }


async def _g_call(
    omg: Omgeving,
    boek: gb.Grootboek,
    *,
    sleutel: str,
    item: dict[str, Any],
    technisch: bool,
    bestand_sha: str,
    code_sha: str,
    config_sha: str,
    callmap: Path,
    fase: str = "g",
    binding: dict[str, Any] | None = None,
    instructie_sha: str | None = None,
) -> dict[str, Any]:
    from services.validation.ai_beoordeling_transport import Pogingenteller

    invoer, variant = item["invoer"], item["variant"]
    prompt = item["varianten"][variant]
    res = boek.reserveer(
        fase,
        sleutel,
        invoer_sha256=bestand_sha,
        binding=binding,
        technische_herhaling=technisch,
        details={
            "invoer": invoer["id"],
            "variant": variant,
            "prompt_sha256": _sha_tekst(prompt),
            "code_sha256": code_sha,
            "config_sha256": config_sha,
            "g_actueel_instructie_sha256": instructie_sha,
        },
    )
    reservering = gb.Reservering(seq=res["seq"], sleutel=res["sleutel"])
    teller = Pogingenteller()
    status, resultaat, fout = "afgebroken", None, None
    start = time.perf_counter()
    try:
        with gb.actief(reservering), teller:
            async with asyncio.timeout(omg.timeout + MARGE_S):
                resultaat = await omg.ai.generate_definition(
                    prompt=prompt,
                    temperature=omg.g_temperatuur,
                    max_tokens=G_MAX_TOKENS,
                    model=None,
                    timeout_seconds=omg.timeout,
                    use_cache=False,
                    max_attempts=1,
                    max_retries=0,
                    token_estimate="heuristic",
                    offload_postprocessing=True,
                )
        status = "voltooid" if getattr(resultaat, "text", None) else "modelfout"
    except TimeoutError:
        fout = "deadline verstreken; aanroep geannuleerd"
        status = "technisch" if omg.netwerk_gestart(reservering) else "afgebroken"
    except Exception as exc:
        fout = gb.scrub(f"{type(exc).__name__}: {exc}")
        status = "technisch" if omg.netwerk_gestart(reservering) else "niet_verzonden"
    finally:
        boek.sluit(
            res["seq"],
            status,
            netwerk_gestart=omg.netwerk_gestart(reservering),
            details={
                "client_aanroepen": reservering.client_aanroepen,
                "sdk_aanroepen": reservering.sdk_aanroepen,
            },
        )
    tekst = getattr(resultaat, "text", None)
    prijs, bekend = omg.prijs("g")
    record = {
        "schema": "def768-ess05-gcall/1",
        "fase": fase,
        "g_actueel_instructie_sha256": instructie_sha,
        "sleutel": res["sleutel"],
        "seq": res["seq"],
        "budget_bron": res["budget_bron"],
        "invoer_id": invoer["id"],
        "variant": variant,
        "run": item["run"],
        "invoerbestand_sha256": bestand_sha,
        "afsluitstatus": status,
        "fout": fout,
        "duur_s": round(time.perf_counter() - start, 3),
        "prompt": {"tekst": prompt, "sha256": _sha_tekst(prompt)},
        "instructieverschil": item["verschil"],
        "ruw_antwoord": tekst,
        "ruw_antwoord_sha256": _sha_tekst(tekst) if isinstance(tekst, str) else None,
        **_kern(tekst, invoer["begrip"]),
        "transport": {
            "client": {k: v for k, v in reservering.antwoord.items() if k != "text"},
            "sdk": reservering.sdk,
            "client_aanroepen": reservering.client_aanroepen,
            "sdk_aanroepen": reservering.sdk_aanroepen,
            "bewakingsweigering": reservering.schending,
            "netwerk_gestart": omg.netwerk_gestart(reservering),
            **teller.attributie(),
            "cache": {
                "ai_service": False,
                "cached": getattr(resultaat, "cached", None),
            },
            "tokens_used_aiservice_raming": getattr(resultaat, "tokens_used", None),
        },
        "kosten": gb.kosten(reservering.sdk, prijs, prijs_bekend=bekend),
        "rubric": {"bron": "runplan v2 §5.4", "beoordeling": None},
    }
    gb.schrijf_nieuw(
        callmap
        / f"{res['seq']:03d}-{fase}-{invoer['id']}-{variant}-run{item['run']}.json",
        record,
        geheimen=omg.geheimen,
    )
    _stop_bij_bewaking(res["sleutel"], reservering.schending, fout)
    logger.info("%s: afsluiting=%s kern=%r", res["sleutel"], status, record["kern"])
    return {
        "sleutel": res["sleutel"],
        "invoer": invoer["id"],
        "variant": variant,
        "run": item["run"],
        "afsluitstatus": status,
        "kern": record["kern"],
        "kosten_usd": record["kosten"].get("usd"),
    }


async def voer_g_fase(
    omg: Omgeving,
    *,
    g_invoerpad: Path,
    uitmap: Path,
    opslag: Proefopslag,
    proef: Proef = STANDAARD_PROEF,
    fase: str = "g",
    freeze: Path | None = None,
    voorganger_opslag: Proefopslag | None = None,
    nieuw_grootboek: bool = False,
    technische_herhalingen: Sequence[str] = (),
    max_calls: int | None = None,
    totaal_deadline: float | None = None,
) -> dict[str, Any]:
    _fase_van(proef, fase, G_FASES)
    _controleer_opslag(omg, opslag, proef)
    _controleer_registratie(omg, proef)
    data = json.loads(Path(g_invoerpad).read_text(encoding="utf-8"))
    bestand_sha = _sha_bestand(g_invoerpad)
    ontwikkeling = fase == "g_ontwikkeling"
    _controleer_ontwikkelinvoer(proef, fase, g_invoerpad)
    code_sha = code_sha256()
    config = effectieve_config(omg)
    config_sha = pi.sha_json(config)
    instructie_sha = _sha_tekst(pi.huidige_g_instructie())
    binding = _eindbinding(
        omg,
        proef,
        proef.identiteit.eindgroep(fase),
        freeze,
        dataset_sha256=bestand_sha,
        herhaal_ids=[],
        code_sha256=code_sha,
        config_sha256=config_sha,
    )
    prompts = await g_prompts(data, alleen_actueel=ontwikkeling)
    plan = plan_g_ontwikkeling(prompts) if ontwikkeling else plan_g(prompts)
    deadline = _Deadline(totaal_deadline)
    with gb.Proefslot(opslag.slot):
        vorige = _lees_voorganger(omg, proef, voorganger_opslag)
        boek = _grootboek(opslag, nieuw_grootboek, proef)
        boek.controleer_binding(fase, bestand_sha, binding)  # vóór elke call
        voor = boek.samenvatting()
        selectie, overgeslagen = _selecteer(plan, boek, technische_herhalingen)
        if max_calls is not None:
            selectie = selectie[:max_calls]
        _controleer_plan(boek, fase, len(selectie), bool(technische_herhalingen))
        voorganger = _controleer_voorganger(boek, vorige, len(selectie))
        runmap = _nieuwe_map(uitmap, fase)
        resultaten, niet_gestart = [], 0
        try:
            for sleutel, item, technisch in selectie:
                if not deadline.past(omg.timeout + MARGE_S):
                    niet_gestart += 1
                    continue
                resultaten.append(
                    await _g_call(
                        omg,
                        boek,
                        sleutel=sleutel,
                        item=item,
                        technisch=technisch,
                        bestand_sha=bestand_sha,
                        code_sha=code_sha,
                        config_sha=config_sha,
                        callmap=runmap / "calls",
                        fase=fase,
                        binding=binding,
                        instructie_sha=instructie_sha,
                    )
                )
        finally:
            samenvatting = _samenvatting(
                omg,
                boek,
                voor,
                fase=fase,
                invoer=g_invoerpad,
                bestand_sha=bestand_sha,
                resultaten=resultaten,
                overgeslagen=overgeslagen,
                niet_gestart=niet_gestart,
                routes=[],
                technisch=technische_herhalingen,
                config=config,
            )
            samenvatting["vergelijkbaarheid"] = [
                {"invoer": p["invoer"]["id"], "verschil": p["verschil"]}
                for p in prompts
            ]
            samenvatting["vergelijkingsaard"] = (
                _g_ontwikkelaard(proef) if ontwikkeling else VERGELIJKINGSAARD
            )
            samenvatting["buren"] = [
                {"invoer": p["invoer"]["id"], "buren": p["buren"]} for p in prompts
            ]
            samenvatting["g_actueel_instructie_sha256"] = instructie_sha
            samenvatting["grootboek"] = str(opslag.grootboek)
            samenvatting["eindbinding"] = binding
            samenvatting["voorganger_grootboek"] = voorganger
            gb.schrijf_nieuw(
                runmap / "samenvatting.json", samenvatting, geheimen=omg.geheimen
            )
    return samenvatting


# --- offline -------------------------------------------------------------------------------


def nulcallproef(gevallenpad: Path, uitmap: Path) -> dict[str, Any]:
    """Offline routeproef: geen client, geen grootboek, netwerk geblokkeerd."""
    with geen_netwerk():
        data = json.loads(Path(gevallenpad).read_text(encoding="utf-8"))
        gevallen, _ = pi.valideer_gevallenbestand(data, herhaal_vereist=False)
        resultaten = []
        for geval in gevallen:
            route = pi.route(pi.modelprojectie(geval), _lege_ruimte(geval))
            status = (route.get("uitkomst") or {}).get("status")
            zoals = route["soort"] == geval.get("verwacht_route") and (
                route["soort"] == "aanroep" or status == geval["verwacht"]
            )
            resultaten.append(
                {
                    "id": geval["id"],
                    "route": route["soort"],
                    "reden": route.get(
                        "reden", "zou aanroepen; in deze fase niet uitgevoerd"
                    ),
                    "uitkomst_status": status,
                    "verwacht_route": geval.get("verwacht_route"),
                    "verwacht": geval["verwacht"],
                    "zoals_verwacht": zoals,
                    "uitkomst": route.get("uitkomst"),
                }
            )
        samenvatting = {
            "schema": "def768-ess05-nulcallproef/1",
            "tijd": datetime.now(UTC).isoformat(),
            "invoer": {"pad": str(gevallenpad), "sha256": _sha_bestand(gevallenpad)},
            "identiteit": identiteit(),
            "echte_calls": 0,
            "alle_routes_zoals_verwacht": all(r["zoals_verwacht"] for r in resultaten),
            "resultaten": resultaten,
        }
        gb.schrijf_nieuw(
            _nieuwe_map(uitmap, "nulcall") / "nulcallproef.json",
            samenvatting,
            geheimen=(),
        )
    return samenvatting


def droogomgeving(
    *, timeout: int, max_tokens_t: int, verifier_max_tokens: int | None = None
) -> Omgeving:
    """De omgeving zoals `--echt` haar bouwt, zonder providerclient of sleutel.

    Alleen voor freezevelden en vooraftoetsen; er is geen client, dus geen
    call mogelijk. `sdk_bewaakt=True` zoals live, zodat de effectieve
    configuratie (en haar hash) gelijk is aan die van de echte run met
    dezelfde `--timeout` en `--max-tokens-t`.
    """
    from services.ai.model_router import ModelRouter

    return bouw_omgeving(
        None,
        ModelRouter.from_config(),
        timeout=timeout,
        max_tokens_t=max_tokens_t,
        sdk_bewaakt=True,
        geheimen=(),
        verifier_max_tokens=verifier_max_tokens,
    )


async def droogrun(
    fase: str,
    pad: Path,
    uitmap: Path,
    *,
    proef: Proef = STANDAARD_PROEF,
    timeout: int = 60,
    max_tokens_t: int | None = None,
) -> dict[str, Any]:
    """Alle prompts en controles van een fase, zonder client en zonder grootboek.

    R8: ook de productiegrenzen, de kostenroute en de bytegrens per item, met
    de omgeving zoals `--echt` haar bouwt (fail-closed, net als echt).
    """
    from services.validation.ess05_assessment_service import laad_ess05_norm

    if max_tokens_t is None:
        max_tokens_t = _standaard_max_tokens(proef)
    kb = proef.identiteit.kostenbewaking
    _fase_van(proef, fase, (*T_FASES, *G_FASES, *V_FASES))
    _controleer_ontwikkelinvoer(proef, fase, pad)
    omg_d = droogomgeving(
        timeout=timeout,
        max_tokens_t=max_tokens_t,
        verifier_max_tokens=max_tokens_t if kb is not None else None,
    )
    _controleer_productiegrenzen(omg_d, proef)
    _controleer_kostenroute(omg_d, proef)
    _controleer_contract(omg_d, proef)
    data = json.loads(Path(pad).read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = []
    if fase in V_FASES:
        verifier = omg_d.dienst.verification_service
        for v in valideer_v_invoer(data, omg_d):
            system, user = v.prompt
            bytes_ = _payloadbytes(
                omg_d, "t_verificatie", verifier.max_tokens, system, user
            )
            _controleer_bytegrens(proef, verifier.TASK_TYPE, v.sleutel, bytes_)
            items.append(
                {
                    "sleutel": v.sleutel,
                    "soort": v.item["soort"],
                    "prompt": {"system": system, "user": user},
                    "prompt_sha256": v.item["verificatieprompt_sha256"],
                    "concept_hash": v.concept.hash,
                    "foutdragende_items": v.item["foutdragende_items"],
                    "payload_bytes": bytes_,
                }
            )
        extra: dict[str, Any] = {"norm_sha256": pi.sha_json(omg_d.norm)}
    elif fase == "g_ontwikkeling":
        prompts = await g_prompts(data, alleen_actueel=True)
        for sleutel, item in plan_g_ontwikkeling(prompts):
            tekst = item["varianten"]["actueel"]
            items.append(
                {
                    "sleutel": sleutel,
                    "prompt": tekst,
                    "prompt_sha256": _sha_tekst(tekst),
                    "promptlengte": len(tekst),
                }
            )
        extra = {
            "g_actueel_instructie_sha256": _sha_tekst(pi.huidige_g_instructie()),
            "vergelijkingsaard": _g_ontwikkelaard(proef),
            "buren": [
                {"invoer": p["invoer"]["id"], "buren": p["buren"]} for p in prompts
            ],
        }
    elif fase == "g":
        prompts = await g_prompts(data)
        for sleutel, item in plan_g(prompts):
            tekst = item["varianten"][item["variant"]]
            items.append(
                {
                    "sleutel": sleutel,
                    "prompt": tekst,
                    "prompt_sha256": _sha_tekst(tekst),
                }
            )
        extra = {
            "basis_g_tekst_in_git": _basis_in_git(data["g_teksten"]["basis"]["tekst"]),
            "verschillen": [
                {"invoer": p["invoer"]["id"], "verschil": p["verschil"]}
                for p in prompts
            ],
            "vergelijkingsaard": VERGELIJKINGSAARD,
            "buren": [
                {"invoer": p["invoer"]["id"], "buren": p["buren"]} for p in prompts
            ],
        }
    else:
        norm = laad_ess05_norm()
        gevallen, herhaal = pi.valideer_gevallenbestand(
            data, herhaal_vereist=proef.identiteit.eindgroep(fase) is not None
        )
        _vooraftoets_r8_t(omg_d, proef, fase, gevallen, herhaal)
        for sleutel, geval in plan_t(fase, gevallen, herhaal):
            projectie = pi.modelprojectie(geval)
            route = pi.route(projectie, _lege_ruimte(geval))
            if route["soort"] == "nulcall":
                items.append({"sleutel": sleutel, "route": route})
                continue
            prompt = pi.bouw_t_prompt(projectie, norm)
            pi.controleer_afscherming(geval, prompt.teksten, norm)
            items.append(
                {
                    "sleutel": sleutel,
                    "route": route,
                    "prompt": {"system": prompt.teksten[0], "user": prompt.teksten[1]},
                    "prompt_sha256": prompt.sha256,
                    "buren": [b.als_dict() for b in prompt.buren],
                    "payload_bytes": _payloadbytes(
                        omg_d, "t", max_tokens_t, *prompt.teksten
                    ),
                }
            )
        extra = {"norm_sha256": pi.sha_json(norm)}
    groep = proef.identiteit.eindgroep(fase)
    if proef.freeze_vereist and groep is not None:
        velden = freezevelden(omg_d, proef, groep.naam)
        extra["freezevelden"] = {
            **velden,
            "dataset_sha256": _sha_bestand(pad),
            "herhaal_ids": data.get("herhaal_ids") if groep.herhaal_aantal else [],
        }
        extra["freezevelden_berekend_voor"] = {
            "timeout": timeout,
            "max_tokens_t": max_tokens_t,
            "let_op": "gelijk aan --echt alleen met dezelfde --timeout en --max-tokens-t",
        }
    samenvatting = {
        "schema": "def768-ess05-droogrun/1",
        "proef_id": proef.identiteit.proef_id,
        "fase": fase,
        "tijd": datetime.now(UTC).isoformat(),
        "invoer": {"pad": str(pad), "sha256": _sha_bestand(pad)},
        "identiteit": identiteit(),
        "echte_calls": 0,
        "geplande_calls": sum(1 for i in items if "prompt" in i),
        "fasecap": proef.identiteit.fasecaps[fase],
        **extra,
        "items": items,
    }
    gb.schrijf_nieuw(
        _nieuwe_map(uitmap, f"droog-{fase}") / "droogrun.json",
        samenvatting,
        geheimen=(),
    )
    return samenvatting


# --- CLI -------------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--fase", required=True, choices=("nulcall", *T_FASES, *V_FASES, *G_FASES)
    )
    p.add_argument(
        "--proef",
        choices=tuple(PROEVEN),
        default=STANDAARD_PROEF.naam,
        help=(
            "R1 (standaard) t/m R10 zijn gesloten voor echte calls; R11 "
            f"({gb.R11.proef_id}, opslag {PROEVEN['R11'].opslag.root}, "
            "cumulatief met R1 t/m R10 max 430) is open binnen het gepinde besluit "
            "(66 modelstappen, max USD 24,529390, reserve 0)"
        ),
    )
    p.add_argument(
        "--gevallen",
        type=Path,
        help="gevallenbestand (T-fases, nulcall) of verifier-only-invoer (R8 t/m R11)",
    )
    p.add_argument(
        "--g-invoer", type=Path, help="G-invoerbestand (fases g, g_ontwikkeling)"
    )
    p.add_argument(
        "--uitmap", type=Path, default=None, help="standaard: rapportroot van de proef"
    )
    p.add_argument(
        "--freeze",
        type=Path,
        default=None,
        help="R2–R7-eindfases: freezebestand dat vóór elke call wordt gecontroleerd",
    )
    p.add_argument(
        "--grootboek",
        type=Path,
        help=(
            "alleen ter bevestiging: echte calls gebruiken altijd het canonieke "
            "grootboek van de gekozen proef; een ander pad wordt geweigerd"
        ),
    )
    p.add_argument(
        "--nieuw-grootboek",
        action="store_true",
        help="alleen als grootboek én anker nog niet bestaan",
    )
    modus = p.add_mutually_exclusive_group()
    modus.add_argument(
        "--droog", action="store_true", help="offline: prompts en controles, geen calls"
    )
    modus.add_argument(
        "--echt", action="store_true", help="echte, betaalde calls binnen het grootboek"
    )
    p.add_argument(
        "--technische-herhaling", action="append", default=[], metavar="SLEUTEL"
    )
    p.add_argument("--max-calls", type=int, default=None)
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument(
        "--max-tokens-t",
        type=int,
        default=None,
        help="standaard: R8 t/m R11 de productiegrens (3000, ook de verifier); oudere 1500",
    )
    p.add_argument(
        "--totaal-deadline", type=float, default=None, help="seconden voor deze aanroep"
    )
    return p


def _invoerpad(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Path:
    pad = args.g_invoer if args.fase in G_FASES else args.gevallen
    if pad is None:
        parser.error(
            "--g-invoer (fases g, g_ontwikkeling) of --gevallen (overige fases) "
            "is verplicht"
        )
    return pad


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    proef = PROEVEN[args.proef]
    uitmap = args.uitmap if args.uitmap is not None else proef.opslag.root
    pad = _invoerpad(args, parser)
    if args.fase == "nulcall":
        uitkomst = nulcallproef(pad, uitmap)
        logger.info(
            "nulcallproef: zoals verwacht=%s", uitkomst["alle_routes_zoals_verwacht"]
        )
        return 0 if uitkomst["alle_routes_zoals_verwacht"] else 1
    if args.fase not in proef.identiteit.fasecaps:
        parser.error(f"fase {args.fase} bestaat niet in ronde {proef.naam}")
    max_tokens_t = (
        args.max_tokens_t
        if args.max_tokens_t is not None
        else _standaard_max_tokens(proef)
    )
    if args.droog:
        with geen_netwerk():
            uitkomst = asyncio.run(
                droogrun(
                    args.fase,
                    pad,
                    uitmap,
                    proef=proef,
                    timeout=args.timeout,
                    max_tokens_t=max_tokens_t,
                )
            )
        logger.info(
            "droog %s: %s geplande calls, 0 echte",
            args.fase,
            uitkomst["geplande_calls"],
        )
        return 0
    if not args.echt:
        parser.error(
            "kies --droog (offline) of --echt (betaalde calls); zonder keuze gebeurt niets"
        )
    if not proef.echt_toegestaan:
        parser.error(
            f"ronde {proef.naam} ({proef.identiteit.proef_id}) is gesloten voor "
            "echte calls; alleen een ronde met een eigen gepind budgetbesluit "
            "staat open"
        )
    if proef.identiteit.kostenbewaking is not None:
        # Vóór sleutel, client en grootboek: het besluit moet exact passen.
        try:
            controleer_budgetbesluit(proef)
        except gb.BudgetSchendingError as exc:
            parser.error(str(exc))
    # Eén duurzame proefidentiteit: het grootboek volgt nooit --uitmap.
    if (
        args.grootboek is not None
        and Path(args.grootboek).resolve() != proef.opslag.grootboek.resolve()
    ):
        parser.error(
            f"--grootboek {args.grootboek}: echte calls gebruiken uitsluitend "
            f"{proef.opslag.grootboek}"
        )
    omg = live_omgeving(
        timeout=args.timeout,
        max_tokens_t=max_tokens_t,
        verifier_max_tokens=(
            max_tokens_t if proef.identiteit.kostenbewaking is not None else None
        ),
    )
    gemeen = {
        "uitmap": uitmap,
        "opslag": proef.opslag,
        "proef": proef,
        "freeze": args.freeze,
        "nieuw_grootboek": args.nieuw_grootboek,
        "technische_herhalingen": tuple(args.technische_herhaling),
        "max_calls": args.max_calls,
        "totaal_deadline": args.totaal_deadline,
    }
    if args.fase in G_FASES:
        uitkomst = asyncio.run(
            voer_g_fase(omg, fase=args.fase, g_invoerpad=pad, **gemeen)
        )
    elif args.fase in V_FASES:
        uitkomst = asyncio.run(
            voer_v_fase(omg, fase=args.fase, gevallenpad=pad, **gemeen)
        )
    else:
        uitkomst = asyncio.run(
            voer_t_fase(omg, fase=args.fase, gevallenpad=pad, **gemeen)
        )
    logger.info(
        "Klaar: %s calls gestart; grootboek %s/%s; kosten bekend $%s, onbekend %s",
        uitkomst["aanroepen_gestart"],
        uitkomst["grootboek_na"]["totaal"],
        proef.identiteit.totaal_max,
        uitkomst["kosten_usd_bekend"],
        uitkomst["kosten_onbekend"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
