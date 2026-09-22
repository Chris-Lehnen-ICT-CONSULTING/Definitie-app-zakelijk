"""DEF-766 — echte ESS-03-beoordelingen op vooraf vastgelegde gevallen (proefrunner).

Draait de productieklassen (`Ess03AssessmentService` op `AIServiceV2` met de
geconfigureerde `ModelRouter`-route voor taak `validation`) op een
gevallenbestand met vooraf vastgelegde verwachtingen, en schrijft per geval het
volledige beoordelingsdocument, het ruwe modelantwoord, de prompt- en
invoerhashes, duur, waargenomen transportpogingen en fouten naar een
JSON-bestand. Geen productie-DB, geen webzoekactie, geen cache (AIServiceV2
`use_cache=False`, dienstcache 0, en de dienst zelf vraagt per opt-in geen
cache), geen retries (`AI_SDK_MAX_RETRIES=0` én de opt-ins `max_attempts=1`/
`max_retries=0` van de dienst), harde deadline per beoordeling (`--timeout`,
standaard 60 s, aanroep én nabewerking) en voor de gehele run
(`--total-deadline`, standaard max-calls × timeout: een geval waarvoor het
resterende budget geen volledige aanroep meer toelaat wordt niet gestart en
als zodanig vastgelegd), begrensde uitvoer (`--max-tokens`, standaard 1200).
API-sleutels worden alleen geladen (uit de project-`.env`), nooit afgedrukt.

Gebruik:
    python scripts/ess03/run_ess03_gevallen.py \
        --gevallen tests/fixtures/ess03/ontwikkelgevallen_v2.json \
        --uit /tmp/def766-ai-20260921/ontwikkelrun-v2.json [--max-calls 8]

Een label wordt nooit uit modeluitvoer afgeleid: de vergelijking is
verwacht-vs-gekregen; de verwachtingen komen uit het gevallenbestand. Naar
het model gaan uitsluitend begrip, tekst, context, bronnen en de bedoelde
betekenis (toelichting, categorie, verduidelijkingen) — nooit `verwacht`,
`grond` of `doel`.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Geen SDK-retries en geen dotenv-verrassingen vóór de imports van de app.
os.environ.setdefault("AI_SDK_MAX_RETRIES", "0")

from config.dotenv_loader import load_project_dotenv
from domain.ess03.contract import Intentie
from services.validation.ess03_assessment_service import (
    Ess03AssessmentService,
    bouw_beoordelingsprompt,
    laad_ess03_norm,
)

logger = logging.getLogger("ess03.proefrunner")


def _laad_env() -> str:
    """Laad de `.env` van de werkboom, anders die van het hoofdproject; meld alleen welke."""
    kandidaten = [
        PROJECT_ROOT / ".env",
        Path.home() / "Projecten" / "Definitie-app" / ".env",
    ]
    for pad in kandidaten:
        if pad.is_file():
            load_project_dotenv(pad=pad, force=True)
            return str(pad)
    return "geen .env gevonden"


def _sha(tekst: str) -> str:
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


class _RuwVangendeAI:
    """Dunne wrapper om de AI-service: bewaart het ruwe antwoord per aanroep."""

    def __init__(self, binnen: Any) -> None:
        self._binnen = binnen
        self.laatste: dict[str, Any] | None = None

    @property
    def default_model(self) -> Any:
        return getattr(self._binnen, "default_model", None)

    async def generate_definition(self, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            resultaat = await self._binnen.generate_definition(**kwargs)
        except Exception as exc:
            self.laatste = {
                "duur_s": round(time.perf_counter() - start, 3),
                "fout": f"{type(exc).__name__}: {exc}",
                "ruwe_tekst": None,
            }
            raise
        self.laatste = {
            "duur_s": round(time.perf_counter() - start, 3),
            "fout": None,
            "ruwe_tekst": getattr(resultaat, "text", None),
            "model": getattr(resultaat, "model", None),
            "tokens_used": getattr(resultaat, "tokens_used", None),
            "cached": bool(getattr(resultaat, "cached", False)),
            "retry_count": getattr(resultaat, "retry_count", None),
        }
        return resultaat


def _bouw_dienst(
    timeout: int, max_tokens: int
) -> tuple[Ess03AssessmentService, _RuwVangendeAI, dict]:
    from config.config_manager import get_config_manager
    from services.ai import create_ai_client
    from services.ai.model_router import ModelRouter
    from services.ai_service_v2 import AIServiceV2

    config = get_config_manager()
    provider = config.api.ai_provider
    api_key = (
        config.api.anthropic_api_key
        if provider == "anthropic"
        else config.api.openai_api_key
    )
    if not api_key:
        msg = f"geen API-sleutel voor provider {provider!r} in de omgeving/.env"
        raise SystemExit(msg)
    router = ModelRouter.from_config()
    client = create_ai_client(
        provider=provider, api_key=api_key, timeout=float(timeout)
    )
    ai = AIServiceV2(use_cache=False, ai_client=client, model_router=router)
    vangend = _RuwVangendeAI(ai)
    dienst = Ess03AssessmentService(
        vangend,
        model_router=router,
        timeout_seconds=timeout,
        max_tokens=max_tokens,
        cache_size=0,
    )
    route_provider, route_model = router.get_model("validation")
    accepteert_temp = router.accepts_temperature(route_model, provider=route_provider)
    modelconfig = {
        "provider": route_provider,
        "model": route_model,
        "task_type": "validation",
        "temperature_requested": 0.0,
        # DEF-441/DEF-731: de client laat `temperature` weg voor modelfamilies
        # die dat niet accepteren; dan is er geen determinismeclaim.
        "temperature_sent": 0.0 if accepteert_temp else None,
        "max_tokens": max_tokens,
        "timeout_seconds": timeout,
        "ai_service_cache": False,
        "dienst_cache_size": 0,
        "dienst_optins": {
            "use_cache": False,
            "max_attempts": 1,
            "max_retries": 0,
            "token_estimate": "heuristic",
        },
        "sdk_max_retries_env": os.environ.get("AI_SDK_MAX_RETRIES"),
    }
    return dienst, vangend, modelconfig


def _intentie(geval: dict[str, Any]) -> Intentie:
    return Intentie(
        toelichting=geval.get("toelichting"),
        categorie=geval.get("categorie"),
        betekenisverduidelijking=geval.get("betekenisverduidelijking"),
        verduidelijking=geval.get("verduidelijking"),
    )


#: Velden van een geval die het oordeel beschrijven en NOOIT naar het model gaan.
_AFGESCHERMD: frozenset[str] = frozenset({"verwacht", "grond", "doel"})


def _controleer_afscherming(
    geval: dict[str, Any],
    prompts: tuple[str, str],
    norm: Mapping[str, str],
) -> None:
    """Fail-closed: de prompt is onafhankelijk van de afgeschermde velden.

    De prompt opgebouwd uit het geval zónder `verwacht`/`grond`/`doel` moet
    tekenidentiek zijn aan de verzonden prompt; de grond en het doel mogen
    bovendien nergens letterlijk voorkomen. (Een tekstuele zoektocht naar het
    verwachte label alleen zou op de vaste antwoordwoordenschat van de prompt
    afgaan en bewijst niets.)
    """
    from domain.sources.normalisatie import canoniseer_bronnen

    kaal = {k: v for k, v in geval.items() if k not in _AFGESCHERMD}
    herbouwd = bouw_beoordelingsprompt(
        kaal["begrip"],
        kaal["tekst"],
        kaal.get("context") or {},
        canoniseer_bronnen(kaal.get("bronnen") or []),
        intentie=_intentie(kaal),
        norm=norm,
    )
    if herbouwd != prompts:
        msg = f"{geval['id']}: de prompt hangt af van afgeschermde velden"
        raise SystemExit(msg)
    for veld in ("grond", "doel"):
        waarde = geval.get(veld)
        if (
            isinstance(waarde, str)
            and waarde.strip()
            and any(waarde in p for p in prompts)
        ):
            msg = f"{geval['id']}: veld {veld!r} staat letterlijk in de prompt"
            raise SystemExit(msg)


async def _draai(
    gevallen: list[dict[str, Any]],
    *,
    timeout: int,
    max_tokens: int,
    max_calls: int,
    total_deadline: float,
) -> dict:
    from domain.sources.normalisatie import canoniseer_bronnen

    dienst, vangend, modelconfig = _bouw_dienst(timeout, max_tokens)
    norm = laad_ess03_norm()
    resultaten: list[dict[str, Any]] = []
    run_start = time.perf_counter()
    for geval in gevallen[:max_calls]:
        resterend = total_deadline - (time.perf_counter() - run_start)
        if resterend < timeout:
            # Harde totale deadline: een aanroep die niet volledig binnen het
            # resterende budget past wordt niet gestart (en dus niet geteld).
            resultaten.append(
                {
                    "id": geval["id"],
                    "verwacht": geval["verwacht"],
                    "gekregen_verdict": "<niet_gestart>",
                    "gekregen_status": None,
                    "correct": False,
                    "niet_gestart": (
                        f"totale deadline: resterend {resterend:.1f} s < {timeout} s"
                    ),
                }
            )
            logger.warning("%s: niet gestart (totale deadline)", geval["id"])
            continue
        intentie = _intentie(geval)
        bronnen = canoniseer_bronnen(geval.get("bronnen") or [])
        system_prompt, prompt = bouw_beoordelingsprompt(
            geval["begrip"],
            geval["tekst"],
            geval.get("context") or {},
            bronnen,
            intentie=intentie,
            norm=norm,
        )
        _controleer_afscherming(geval, (system_prompt, prompt), norm)
        vangend.laatste = None
        start = time.perf_counter()
        beoordeling = await dienst.assess(
            geval["begrip"],
            geval["tekst"],
            geval.get("context") or {},
            geval.get("bronnen") or [],
            intentie=intentie,
            correlation_id=f"def766-proef-{geval['id']}",
        )
        document = beoordeling.als_dict()
        oordeel = document.get("judgment") or {}
        attributie = document.get("attribution") or {}
        gekregen = (
            oordeel.get("verdict")
            if document.get("status") == "assessed" and oordeel
            else f"<{document.get('status')}>"
        )
        resultaten.append(
            {
                "id": geval["id"],
                "verwacht": geval["verwacht"],
                "gekregen_verdict": gekregen,
                "gekregen_status": oordeel.get("status") if oordeel else None,
                "correct": gekregen == geval["verwacht"],
                "duur_totaal_s": round(time.perf_counter() - start, 3),
                "elapsed_seconds_dienst": document.get("elapsed_seconds"),
                "attempts_observed": attributie.get("attempts_observed"),
                "retries_observed": attributie.get("retries_observed"),
                "cached": attributie.get("cached"),
                "error": document.get("error"),
                "aanroep": vangend.laatste,
                "hashes": {
                    "system_prompt_sha256": _sha(system_prompt),
                    "user_prompt_sha256": _sha(prompt),
                    "kandidaat_sha256": _sha(geval["tekst"]),
                    "fingerprint": document.get("fingerprint"),
                    "norm_sha256": document.get("norm_sha256"),
                    "raw_response_sha256": document.get("raw_response_sha256"),
                },
                "beoordeling": document,
            }
        )
        logger.info(
            "%s: verwacht=%s gekregen=%s (%s) %.1fs pogingen=%s",
            geval["id"],
            geval["verwacht"],
            gekregen,
            "OK" if gekregen == geval["verwacht"] else "AFWIJKEND",
            resultaten[-1]["duur_totaal_s"],
            attributie.get("attempts_observed"),
        )
    gestart_n = [r for r in resultaten if "niet_gestart" not in r]
    return {
        "schema": "def766-ess03-proefrun/2",
        "gestart": datetime.now(UTC).isoformat(),
        "totale_duur_s": round(time.perf_counter() - run_start, 3),
        "total_deadline_s": total_deadline,
        "modelconfig": modelconfig,
        "prompt_version": Ess03AssessmentService.PROMPT_VERSION,
        "norm_sha256": dienst.norm_sha256,
        "system_prompt_sha256": _sha(
            bouw_beoordelingsprompt("x", "y", {}, (), intentie=None, norm=norm)[0]
        ),
        "aantal": len(resultaten),
        "aanroepen_gestart": len(gestart_n),
        "transportpogingen_waargenomen": sum(
            int(r.get("attempts_observed") or 0) for r in gestart_n
        ),
        "correct": sum(1 for r in resultaten if r["correct"]),
        "per_klasse": _per_klasse(resultaten),
        "resultaten": resultaten,
    }


def _per_klasse(resultaten: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    telling: dict[str, dict[str, int]] = {}
    for r in resultaten:
        klasse = telling.setdefault(r["verwacht"], {"totaal": 0, "correct": 0})
        klasse["totaal"] += 1
        klasse["correct"] += int(r["correct"])
    return telling


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gevallen", required=True, type=Path)
    parser.add_argument("--uit", required=True, type=Path)
    parser.add_argument("--max-calls", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument(
        "--total-deadline",
        type=float,
        default=None,
        help="harde deadline voor de gehele run in seconden (standaard max-calls × timeout)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    env_bron = _laad_env()
    logger.info(".env geladen uit: %s (sleutels worden niet getoond)", env_bron)
    bestand = json.loads(args.gevallen.read_text(encoding="utf-8"))
    gevallen = bestand["gevallen"]
    total_deadline = (
        args.total_deadline
        if args.total_deadline is not None
        else float(args.max_calls * args.timeout)
    )
    uitkomst = asyncio.run(
        _draai(
            gevallen,
            timeout=args.timeout,
            max_tokens=args.max_tokens,
            max_calls=args.max_calls,
            total_deadline=total_deadline,
        )
    )
    uitkomst["gevallenbestand"] = {
        "pad": str(args.gevallen),
        "sha256": _sha(args.gevallen.read_text(encoding="utf-8")),
        "schema": bestand.get("schema"),
        "status": bestand.get("status"),
    }
    args.uit.parent.mkdir(parents=True, exist_ok=True)
    args.uit.write_text(
        json.dumps(uitkomst, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(
        "Klaar: %s/%s correct; %s aanroepen gestart, %s transportpogingen "
        "waargenomen, %.1f s totaal; per klasse %s; uitvoer %s",
        uitkomst["correct"],
        uitkomst["aantal"],
        uitkomst["aanroepen_gestart"],
        uitkomst["transportpogingen_waargenomen"],
        uitkomst["totale_duur_s"],
        json.dumps(uitkomst["per_klasse"], ensure_ascii=False),
        args.uit,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
