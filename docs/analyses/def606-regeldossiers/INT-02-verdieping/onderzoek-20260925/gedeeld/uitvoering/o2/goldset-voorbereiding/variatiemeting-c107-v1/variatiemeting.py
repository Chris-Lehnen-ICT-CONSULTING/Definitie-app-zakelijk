#!/usr/bin/env python3
"""DEF-835 — variatiemeting C107 (besluit 11), buiten het kwalificatieprotocol.

Beoordeelt alleen geval C107 N keer na elkaar (standaard 5, hard maximaal 5)
via exact dezelfde productieketen als de kwalificatieproef v5: de dienst,
het profiel, het model, prompt /3, contract /2, de limieten per call en
`use_cache=False` komen uit de proefrunner
(`scripts/analysis/def835_int02_modelproef.py`), inclusief diens `Waarnemer`
aan de httpx-grens (payloadcontrole, tokenmeting, boeking van gemelde usage).

Buiten het protocol: geen manifest, akkoordbestand of grootboek van de
kwalificatie wordt gelezen, geschreven of als bewijs hergebruikt. De uitkomst
is een meting van variatie, geen kwalificatie en geen DEF-815-claim.

Invoer: uitsluitend het veld `invoer` van C107 uit
`goldset-freeze-v1/kwalificatie-gevallen-v1.json`. Het bestand wordt als
geheel geparsed (JSON), maar van andere gevallen wordt niets gebruikt,
getoond of gelogd, en van C107 alleen de invoer (geen label).

Standaard een dry-run: de keten draait met het opvangtransport van de runner
en verstuurt niets; er wordt geen sleutel gelezen. Alleen met `--live` gaat
er verkeer naar de provider. Geen automatische herhaling: de dienst doet één
poging, de SDK en httpx doen geen retry, en per run is precies één inferentie
toegestaan. Bij een technische fout, citaatfout of afwijking van de waarnemer
stopt de meting. Kostenstop: vóór elke call moet de conservatieve besteding
(gemelde usage x routerprijzen; een call zonder betrouwbare boeking telt voor
de volle reservering) plus de volle reservering van die call binnen US$0,50
blijven.

Uitvoer in een nieuwe map (exclusief aangemaakt): eerst `herkomst.json`,
dan per run een regel in `runs.jsonl` (live), tot slot `samenvatting.json`.
De sleutel komt alleen uit de bestaande configuratie (omgevingsvariabele
`ANTHROPIC_API_KEY` via de ConfigManager) en wordt nooit gelogd of bewaard.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("def835_int02_variatiemeting")

SCRIPT_PAD = Path(__file__).resolve()
MAP = SCRIPT_PAD.parent
GEVALLEN_PAD = MAP.parent / "goldset-freeze-v1" / "kwalificatie-gevallen-v1.json"
RUNNER_RELATIEF = Path("scripts/analysis/def835_int02_modelproef.py")


def _vind_repo() -> Path:
    for kandidaat in SCRIPT_PAD.parents:
        if (kandidaat / RUNNER_RELATIEF).is_file():
            return kandidaat
    msg = "repository met de proefrunner niet gevonden"
    raise RuntimeError(msg)


REPO = _vind_repo()
SRC = REPO / "src"
CONTRACT_PAD = REPO / "src/domain/int02/contract.py"
DIENST_PAD = REPO / "src/services/validation/int02_assessment_service.py"

GEVAL_ID = "C107"
STANDAARD_AANTAL = 5
MAX_AANTAL = 5
KOSTENSTOP_USD = 0.50
#: Ruim boven 5 x de deadline per call (120 s).
TOTALE_LOOPTIJD_SECONDEN = 900.0
KWALIFICATIE_TEKST = "variatiemeting:besluit-11:buiten-kwalificatie:geen-DEF-815"
HERKOMST_SOORT = "def835-int02-variatiemeting-herkomst/1"
RUN_SOORT = "def835-int02-variatiemeting-run/1"
SAMENVATTING_SOORT = "def835-int02-variatiemeting-samenvatting/1"
CLAIM = (
    "Variatiemeting op C107 buiten het kwalificatieprotocol (besluit 11): "
    "dezelfde keten als kwalificatieproef v5, N losse calls. Geen kwalificatie, "
    "geen DEF-815-claim. Kosten = gemelde usage x routerprijzen; geen "
    "providerfactuur."
)


def _laad_runner() -> Any:
    """De proefrunner als module; hergebruikt een al geladen exemplaar."""
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    naam = "def835_int02_modelproef"
    if naam in sys.modules:
        return sys.modules[naam]
    spec = importlib.util.spec_from_file_location(naam, REPO / RUNNER_RELATIEF)
    if spec is None or spec.loader is None:
        msg = "proefrunner niet laadbaar"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[naam] = module
    spec.loader.exec_module(module)
    return module


runner = _laad_runner()


class MetingGeweigerdError(Exception):
    """De meting start niet (niets verstuurd); `reden` is een code."""

    def __init__(self, reden: str) -> None:
        super().__init__(reden)
        self.reden = reden


def _sha_bestand(pad: Path) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


def _eis_aantal(aantal: int) -> None:
    if isinstance(aantal, bool) or not isinstance(aantal, int):
        raise MetingGeweigerdError("aantal_ongeldig")
    if not 1 <= aantal <= MAX_AANTAL:
        raise MetingGeweigerdError("aantal_buiten_grens")


def _meetlimieten(aantal: int) -> Any:
    """Limieten per call gelijk aan de kwalificatie; aantal en plafond eigen."""
    return replace(
        runner.KWALIFICATIELIMIETEN,
        max_inferentie=aantal,
        max_telverzoeken=aantal,
        budget_usd=KOSTENSTOP_USD,
        totale_looptijd_seconden=TOTALE_LOOPTIJD_SECONDEN,
    )


def _prijzen(router: Any) -> dict[str, float]:
    """Routerprijzen via de runner; één volle reservering moet passen.

    De runner eist dat alle calls vooraf samen in het budget passen; hier
    bewaakt de kostenstop elke call vooraf, dus de controle geldt per call.
    """
    return runner._prijzen(router, replace(_meetlimieten(1), max_inferentie=1))


def lees_c107() -> Any:
    """Alleen het veld `invoer` van C107; geen label, geen andere gevallen."""
    data = json.loads(GEVALLEN_PAD.read_text("utf-8"))
    gevallen = data.get("gevallen") if isinstance(data, dict) else None
    treffers = [
        g.get("invoer")
        for g in gevallen or []
        if isinstance(g, dict) and g.get("id") == GEVAL_ID
    ]
    if len(treffers) != 1 or not isinstance(treffers[0], dict):
        raise MetingGeweigerdError("c107_niet_gevonden")
    return runner.lees_invoer(treffers[0])


def _git(*args: str) -> str | None:
    try:
        uit = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return uit.stdout.strip()


def _herkomst(
    voorbereiding: dict[str, Any], modus: str, aantal: int, limieten: Any
) -> dict[str, Any]:
    import anthropic

    from domain.int02.contract import CONTRACTVERSIE
    from services.validation.int02_assessment_service import PROMPT_VERSION

    gewijzigd = _git("status", "--porcelain", "--", *runner.KETENBESTANDEN)
    return {
        "soort": HERKOMST_SOORT,
        "claim": CLAIM,
        "aangemaakt": runner._nu(),
        "modus": modus,
        "aantal": aantal,
        "git_head": _git("rev-parse", "HEAD"),
        "ketenbestanden_lokaal_gewijzigd": (
            gewijzigd.splitlines() if gewijzigd is not None else None
        ),
        "script_sha256": _sha_bestand(SCRIPT_PAD),
        "contract_sha256": _sha_bestand(CONTRACT_PAD),
        "dienst_sha256": _sha_bestand(DIENST_PAD),
        "runner_sha256": _sha_bestand(REPO / RUNNER_RELATIEF),
        "gevallenbron_sha256": _sha_bestand(GEVALLEN_PAD),
        "geval": GEVAL_ID,
        **voorbereiding["hashes"],
        "profiel_id": runner.KWALIFICATIE_PROFIEL_ID,
        "provider": runner.PROVIDER,
        "model": runner.MODEL,
        "promptversie": PROMPT_VERSION,
        "contractversie": CONTRACTVERSIE,
        "limieten": asdict(limieten),
        "kostenstop_usd": KOSTENSTOP_USD,
        "prijzen_per_token": voorbereiding["prijzen"],
        "reservering_per_call_usd": runner._reservering(
            limieten, voorbereiding["prijzen"]
        ),
        "versies": {"anthropic": anthropic.__version__, "httpx": httpx.__version__},
    }


async def _bereid_voor() -> dict[str, Any]:
    """Offline: router, prijzen, C107 en de opgevangen payload (niets verstuurd)."""
    router = runner._bouw_router()
    prijzen = _prijzen(router)
    invoer = lees_c107()
    waarnemer = await runner._vang(
        router,
        runner.KWALIFICATIELIMIETEN,
        [(GEVAL_ID, invoer)],
        runner.KWALIFICATIE_PROFIEL_ID,
    )
    hashes = runner._gevalhashes(GEVAL_ID, invoer, waarnemer)
    del hashes["id"]
    return {
        "router": router,
        "prijzen": prijzen,
        "invoer": invoer,
        "hashes": hashes,
        "opgevangen": len(waarnemer.opgevangen),
    }


def _schrijf_regel(pad: Path, regel: dict[str, Any]) -> None:
    with pad.open("a", encoding="utf-8") as bestand:
        bestand.write(json.dumps(regel, ensure_ascii=False, sort_keys=True) + "\n")
        bestand.flush()
        os.fsync(bestand.fileno())


def _uitkomst(regel: dict[str, Any]) -> str:
    status, verdict = regel["status"], regel["verdict"]
    if status in ("error", "gestopt", "uitzondering"):
        return f"{status}/{regel['foutcategorie'] or regel['reden'] or 'onbekend'}"
    return status if verdict in (None, status) else f"{status}/{verdict}"


def _runregel(
    run: int, tijdstempel: str, beoordeling: Any, meting: dict[str, Any]
) -> dict[str, Any]:
    document = beoordeling.document.als_dict()
    oordeel = document.get("oordeel") or {}
    passages = [
        {
            "function": p.get("function"),
            "quote": p.get("quote"),
            "start": p.get("start"),
            "end": p.get("end"),
            "ground": {
                k: (p.get("ground") or {}).get(k)
                for k in ("field", "quote", "start", "end", "ref")
            },
        }
        for p in oordeel.get("passages") or []
    ]
    vraag = oordeel.get("question")
    return {
        "soort": RUN_SOORT,
        "run": run,
        "tijdstempel": tijdstempel,
        "status": beoordeling.status,
        "verdict": oordeel.get("verdict"),
        "reden": beoordeling.reden,
        "uncertainty": oordeel.get("uncertainty"),
        "coverage": oordeel.get("coverage"),
        "passages": passages,
        "vraag_gesteld": isinstance(vraag, str) and bool(vraag.strip()),
        "vraag": vraag,
        "redenering": oordeel.get("reason"),
        "foutcategorie": document.get("foutcategorie"),
        "foutdetail": document.get("foutdetail"),
        "usage": meting.get("usage"),
        "kosten_usd": meting.get("kosten_usd"),
        "reservering_usd": meting.get("reservering_usd"),
        "duur_ms": meting.get("duur_ms"),
        "dienst_duur_ms": (document.get("uitvoering") or {}).get("duur_ms"),
        "gerapporteerd_model": meting.get("gerapporteerd_model"),
        "stop_reason": beoordeling.stop_reason,
        "request_id": meting.get("request_id"),
        "payload_sha256": meting.get("payload_sha256"),
        "antwoord_sha256": beoordeling.antwoord_sha256,
        "promptversie": beoordeling.promptversie,
        "contractversie": document.get("contractversie"),
        "gecachet": beoordeling.gecachet,
    }


def _foutregel(run: int, tijdstempel: str, status: str, reden: str) -> dict[str, Any]:
    """Run zonder dienstresultaat: geen inhoud, alleen de reden."""
    return {
        "soort": RUN_SOORT,
        "run": run,
        "tijdstempel": tijdstempel,
        "status": status,
        "verdict": None,
        "reden": reden,
        "foutcategorie": reden,
        "foutdetail": None,
    }


def _besteding(verstuurd: int, geboekt: float, reservering: float) -> float:
    """Conservatief: een verstuurde call zonder betrouwbare boeking telt voor
    de volle reservering. Uit de tellers van de waarnemer, niet uit `metingen`
    (een geweigerde tweede poging overschrijft de meting van de run)."""
    onzeker = verstuurd - (1 if geboekt > 0 else 0)
    return geboekt + max(onzeker, 0) * reservering


async def _meet(
    voorbereiding: dict[str, Any],
    limieten: Any,
    aantal: int,
    api_sleutel: str,
    binnen: httpx.AsyncBaseTransport | None,
    runs_pad: Path,
) -> dict[str, Any]:
    """N runs na elkaar; stopt bij de eerste fout, afwijking of kostenstop."""
    prijzen = voorbereiding["prijzen"]
    payload_sha = voorbereiding["hashes"]["payload_sha256"]
    sleutels = [f"{GEVAL_ID}-run{i}" for i in range(1, aantal + 1)]
    waarnemer = runner.Waarnemer(
        modus="live",
        # Dienstconstructie exact als de kwalificatie (zelfde RateLimitConfig).
        limieten=runner.KWALIFICATIELIMIETEN,
        binnen=binnen or httpx.AsyncHTTPTransport(retries=0),
        verwacht=dict.fromkeys(sleutels, payload_sha),
        prijzen=prijzen,
    )
    dienst, http = runner._bouw_dienst(
        voorbereiding["router"],
        waarnemer,
        api_sleutel,
        KWALIFICATIE_TEKST,
        runner.KWALIFICATIE_PROFIEL_ID,
    )
    reservering = runner._reservering(limieten, prijzen)
    regels: list[dict[str, Any]] = []
    besteed = 0.0
    stopreden: str | None = None
    try:
        async with asyncio.timeout(limieten.totale_looptijd_seconden):
            for run, sleutel in enumerate(sleutels, start=1):
                if besteed + reservering > KOSTENSTOP_USD:
                    stopreden = "kostenstop"
                    break
                # Precies één inferentie en één tokenmeting per run: een
                # tweede poging binnen dezelfde run stopt vóór verzending.
                waarnemer.limieten = replace(
                    limieten, max_inferentie=run, max_telverzoeken=run
                )
                waarnemer.besteed_usd = besteed
                waarnemer.huidig = sleutel
                voor = waarnemer.inferenties
                tijdstempel = runner._nu()
                try:
                    beoordeling = await dienst.assess(
                        voorbereiding["invoer"],
                        correlation_id=f"def835-variatiemeting-{sleutel}",
                    )
                except Exception as exc:
                    regel = _foutregel(run, tijdstempel, "uitzondering", "uitzondering")
                    regel["uitzonderingstype"] = type(exc).__name__
                    stopreden = waarnemer.stopreden or "uitzondering"
                else:
                    meting = waarnemer.metingen.get(sleutel, {})
                    regel = _runregel(run, tijdstempel, beoordeling, meting)
                    stopreden = waarnemer.stopreden or runner._stopreden(beoordeling)
                besteed += _besteding(
                    waarnemer.inferenties - voor,
                    waarnemer.besteed_usd - besteed,
                    reservering,
                )
                regel["besteed_usd_conservatief"] = besteed
                regel["uitkomst"] = _uitkomst(regel)
                _schrijf_regel(runs_pad, regel)
                regels.append(regel)
                if stopreden is not None:
                    break
    except TimeoutError:
        stopreden = waarnemer.stopreden or "totale_looptijd"
    finally:
        await http.aclose()
    return {
        "regels": regels,
        "stopreden": stopreden,
        "inferenties": waarnemer.inferenties,
        "telverzoeken": waarnemer.telverzoeken,
        "besteed": besteed,
    }


def _samenvatting(
    modus: str, aantal: int, uitkomst: dict[str, Any] | None, opgevangen: int
) -> dict[str, Any]:
    regels = uitkomst["regels"] if uitkomst else []
    telling = Counter(r["uitkomst"] for r in regels)
    return {
        "soort": SAMENVATTING_SOORT,
        "claim": CLAIM,
        "modus": modus,
        "afgerond": runner._nu(),
        "aantal_gevraagd": aantal,
        "aantal_uitgevoerd": len(regels),
        "inferenties": uitkomst["inferenties"] if uitkomst else 0,
        "telverzoeken": uitkomst["telverzoeken"] if uitkomst else 0,
        "opgevangen_zonder_verzending": opgevangen,
        "stopreden": uitkomst["stopreden"] if uitkomst else None,
        "kosten_usd_conservatief": uitkomst["besteed"] if uitkomst else 0.0,
        "kostenstop_usd": KOSTENSTOP_USD,
        "telling": dict(sorted(telling.items())),
        "runs": [
            {
                "run": r["run"],
                "uitkomst": r["uitkomst"],
                "function": [p["function"] for p in r.get("passages", [])],
                "uncertainty": r.get("uncertainty"),
                "vraag_gesteld": r.get("vraag_gesteld"),
            }
            for r in regels
        ],
    }


async def voer_uit(
    uitvoer: Path,
    *,
    aantal: int = STANDAARD_AANTAL,
    live: bool = False,
    sleutel: Callable[[], str | None] | None = None,
    binnen: httpx.AsyncBaseTransport | None = None,
) -> dict[str, Any]:
    """Dry-run (standaard) of live meting; geeft de samenvatting terug."""
    _eis_aantal(aantal)
    uitvoer = Path(uitvoer).resolve()
    if uitvoer.exists():
        raise MetingGeweigerdError("uitvoermap_bestaat")
    limieten = _meetlimieten(aantal)
    modus = "live" if live else "dry-run"
    with runner._proefomgeving():
        voorbereiding = await _bereid_voor()
        api_sleutel = None
        if live:
            api_sleutel = (sleutel or runner._lees_sleutel)()
            if not runner._gevuld(api_sleutel):
                raise MetingGeweigerdError("sleutel_ontbreekt")
        try:
            uitvoer.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise MetingGeweigerdError("uitvoermap_bestaat") from None
        runner._schrijf_nieuw(
            uitvoer / "herkomst.json",
            _herkomst(voorbereiding, modus, aantal, limieten),
        )
        uitkomst = None
        if live:
            uitkomst = await _meet(
                voorbereiding,
                limieten,
                aantal,
                str(api_sleutel),
                binnen,
                uitvoer / "runs.jsonl",
            )
    samenvatting = _samenvatting(modus, aantal, uitkomst, voorbereiding["opgevangen"])
    runner._schrijf_nieuw(uitvoer / "samenvatting.json", samenvatting)
    return samenvatting


def _aantal(waarde: str) -> int:
    try:
        aantal = int(waarde)
    except ValueError:
        msg = "geen geheel getal"
        raise argparse.ArgumentTypeError(msg) from None
    if not 1 <= aantal <= MAX_AANTAL:
        msg = f"aantal moet tussen 1 en {MAX_AANTAL} liggen"
        raise argparse.ArgumentTypeError(msg)
    return aantal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--aantal",
        type=_aantal,
        default=STANDAARD_AANTAL,
        help=f"aantal runs (1-{MAX_AANTAL}, standaard {STANDAARD_AANTAL})",
    )
    parser.add_argument("--uitvoer", type=Path, required=True, help="nieuwe uitvoermap")
    parser.add_argument("--live", action="store_true", help="echte verzending")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logger.setLevel(logging.INFO)
    start = time.monotonic()
    try:
        samenvatting = asyncio.run(
            voer_uit(args.uitvoer, aantal=args.aantal, live=args.live)
        )
    except (MetingGeweigerdError, runner.ProefGeweigerdError) as fout:
        logger.error("geweigerd: %s", fout.reden)
        return 2
    logger.info(
        "%s: %d/%d runs, stopreden %s, telling %s, kosten (conservatief) $%.6f, %.1f s",
        samenvatting["modus"],
        samenvatting["aantal_uitgevoerd"],
        samenvatting["aantal_gevraagd"],
        samenvatting["stopreden"],
        samenvatting["telling"],
        samenvatting["kosten_usd_conservatief"],
        time.monotonic() - start,
    )
    return 0 if samenvatting["stopreden"] is None else 3


if __name__ == "__main__":
    sys.exit(main())
