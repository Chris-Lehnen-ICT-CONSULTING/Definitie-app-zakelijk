#!/usr/bin/env python3
"""
RAG Smoke Test — DEF-318

Bewijs (of ontkracht) dat RAG-context betere definities oplevert dan
de huidige context-loze generator. Go/no-go beslissing voor Fase 3.

Gebruik:
    .venv/bin/python src/tools/rag_smoke_test.py
    .venv/bin/python src/tools/rag_smoke_test.py --wettekst data/wetteksten/wid.txt
    .venv/bin/python src/tools/rag_smoke_test.py --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from services.interfaces import DefinitionOrchestratorInterface
    from services.rag.rag_service import RAGService

# src/ op het pad zetten
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(override=True)

from services.container import ContainerConfigs, ServiceContainer
from services.interfaces import GenerationRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

# ── Test configuratie ─────────────────────────────────────────────

COLLECTION_NAME = "smoke_test_wid"


class TermConfig(TypedDict):
    """Configuratie per testterm — begrip met zijn context-lijsten."""

    begrip: str
    organisatorische_context: list[str]
    juridische_context: list[str]
    wettelijke_basis: list[str]


TEST_TERMS: list[TermConfig] = [
    {
        "begrip": "identificeren",
        "organisatorische_context": ["Strafrechtketen"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": ["Wet op de identificatieplicht"],
    },
    {
        "begrip": "identiteitsbewijs",
        "organisatorische_context": ["Strafrechtketen"],
        "juridische_context": ["Bestuursrecht"],
        "wettelijke_basis": ["Wet op de identificatieplicht"],
    },
    {
        "begrip": "toonplicht",
        "organisatorische_context": ["Politie"],
        "juridische_context": ["Bestuursrecht"],
        "wettelijke_basis": ["Wet op de identificatieplicht"],
    },
    {
        "begrip": "identiteit",
        "organisatorische_context": ["Strafrechtketen"],
        "juridische_context": ["Strafrecht"],
        "wettelijke_basis": [],
    },
    {
        "begrip": "reisdocument",
        "organisatorische_context": ["Strafrechtketen"],
        "juridische_context": ["Bestuursrecht"],
        "wettelijke_basis": ["Paspoortwet"],
    },
]


# ── Result dataclasses ────────────────────────────────────────────


@dataclass
class TermResult:
    begrip: str
    definitie_zonder_rag: str = ""
    score_zonder_rag: float = 0.0
    violations_zonder_rag: int = 0
    definitie_met_rag: str = ""
    score_met_rag: float = 0.0
    violations_met_rag: int = 0
    rag_chunks_count: int = 0
    rag_chunks_preview: list[str] = field(default_factory=list)
    score_verschil: float = 0.0
    beter_met_rag: bool = False
    error: str | None = None


@dataclass
class SmokeTestReport:
    timestamp: str = ""
    wettekst: str = ""
    collection_id: int = 0
    chunks_ingested: int = 0
    terms_tested: int = 0
    terms_improved: int = 0
    avg_score_zonder_rag: float = 0.0
    avg_score_met_rag: float = 0.0
    avg_score_lift: float = 0.0
    go_no_go: str = ""
    results: list[TermResult] = field(default_factory=list)


# ── Core functies ─────────────────────────────────────────────────


def ingest_wettekst(rag_service: "RAGService", wettekst_path: str) -> tuple[int, int]:
    """Ingest wettekst in RAG pipeline. Retourneert (collection_id, chunk_count)."""
    logger.info(f"\n{'='*60}")
    logger.info("STAP 1: Wettekst ingesten in RAG")
    logger.info(f"{'='*60}")

    tekst = Path(wettekst_path).read_text(encoding="utf-8")
    logger.info(f"  Bestand: {wettekst_path}")
    logger.info(f"  Lengte: {len(tekst)} tekens, ~{len(tekst.split())} woorden")

    collection_id = rag_service._ensure_collection(COLLECTION_NAME)

    # Check of er al chunks zijn (hergebruik)
    stats = rag_service.get_collection_stats(collection_id)
    if stats.get("chunk_count", 0) > 0:
        logger.info(
            f"  Collection '{COLLECTION_NAME}' bevat al {stats['chunk_count']} chunks — hergebruik"
        )
        return collection_id, stats["chunk_count"]

    rag_service.ingest_document(
        tekst=tekst,
        collection_id=collection_id,
        filename=Path(wettekst_path).name,
        file_type="text/plain",
        rechtsgebied="Bestuursrecht",
    )

    stats = rag_service.get_collection_stats(collection_id)
    chunk_count = stats.get("chunk_count", 0)
    logger.info(f"  Ingested: {chunk_count} chunks in collection {collection_id}")
    return collection_id, chunk_count


async def generate_definition(
    orchestrator: "DefinitionOrchestratorInterface",
    begrip: str,
    org_ctx: list[str],
    jur_ctx: list[str],
    wet_basis: list[str],
) -> tuple[str, float, int, dict[str, Any]]:
    """Genereer definitie via orchestrator. Retourneert (tekst, score, violation_count, metadata)."""
    request = GenerationRequest(
        id=str(uuid.uuid4()),
        begrip=begrip,
        organisatorische_context=org_ctx,
        juridische_context=jur_ctx,
        wettelijke_basis=wet_basis,
        actor="rag_smoke_test",
    )

    response = await orchestrator.create_definition(request)

    if not response.success:
        return f"[ERROR: {response.error}]", 0.0, 0, {}

    definitie = response.definition.definitie if response.definition else ""
    score = 0.0
    violation_count = 0

    vr = response.validation_result
    if vr:
        # validation_result kan een dict of dataclass zijn
        if isinstance(vr, dict):
            score = vr.get("overall_score", vr.get("score", 0.0)) or 0.0
            violations = vr.get("violations", [])
            violation_count = len(violations) if violations else 0
        else:
            score = vr.score or 0.0
            violation_count = len(vr.violations or [])

    metadata = response.metadata or {}
    return definitie, score, violation_count, metadata


def preview_rag_chunks(
    rag_service: "RAGService", begrip: str, collection_id: int
) -> list[str]:
    """Haal RAG chunks op en geef preview terug."""
    context = rag_service.retrieve_context(
        query=begrip, collection_id=collection_id, top_k=5
    )
    previews = []
    for chunk in context.chunks:
        text = chunk.get("chunk_text", "")[:150]
        score = chunk.get("score", 0)
        previews.append(f"[score={score:.3f}] {text}...")
    return previews


async def run_smoke_test(
    wettekst_path: str,
    dry_run: bool = False,
    output_dir: str = "data/rag-smoke-test-results",
) -> SmokeTestReport:
    """Voer de volledige smoke test uit."""
    report = SmokeTestReport(
        timestamp=datetime.now().isoformat(),
        wettekst=wettekst_path,
    )

    # ── Container & services ──────────────────────────────────
    logger.info("\nServiceContainer initialiseren...")
    # use_database=False → NullRepository, voorkomt duplicate-errors en DB-pollution
    config = ContainerConfigs.development()
    config["use_database"] = False
    container = ServiceContainer(config)
    orchestrator = container.orchestrator()
    rag_service = container.rag_service

    if not rag_service:
        logger.error("RAGService niet beschikbaar! Check OPENAI_API_KEY.")
        report.go_no_go = "ERROR: RAGService niet beschikbaar"
        return report

    # ── Stap 1: Ingest ────────────────────────────────────────
    collection_id, chunk_count = ingest_wettekst(rag_service, wettekst_path)
    report.collection_id = collection_id
    report.chunks_ingested = chunk_count

    if dry_run:
        logger.info("\n[DRY RUN] Chunks bekijken zonder generatie...")
        for term_cfg in TEST_TERMS:
            previews = preview_rag_chunks(
                rag_service, term_cfg["begrip"], collection_id
            )
            logger.info(f"\n  {term_cfg['begrip']}:")
            for p in previews:
                logger.info(f"    {p}")
        report.go_no_go = "DRY_RUN"
        return report

    # ── Stap 2-4: Per term genereren ──────────────────────────
    logger.info(f"\n{'='*60}")
    logger.info("STAP 2-4: Definities genereren (5 termen, met en zonder RAG)")
    logger.info(f"{'='*60}")

    original_rag_service = orchestrator.rag_service

    for i, term_cfg in enumerate(TEST_TERMS, 1):
        begrip = term_cfg["begrip"]
        result = TermResult(begrip=begrip)

        logger.info(f"\n--- Term {i}/5: {begrip} ---")

        try:
            # A: Zonder RAG
            logger.info("  Genereren ZONDER RAG...")
            orchestrator.rag_service = None
            (
                result.definitie_zonder_rag,
                result.score_zonder_rag,
                result.violations_zonder_rag,
                _,
            ) = await generate_definition(
                orchestrator,
                begrip,
                term_cfg["organisatorische_context"],
                term_cfg["juridische_context"],
                term_cfg["wettelijke_basis"],
            )
            logger.info(
                f"    Score: {result.score_zonder_rag:.2f} "
                f"({result.violations_zonder_rag} violations)"
            )
            logger.info(f"    Definitie: {result.definitie_zonder_rag[:120]}...")

            # B: RAG chunks preview
            result.rag_chunks_preview = preview_rag_chunks(
                rag_service, begrip, collection_id
            )
            result.rag_chunks_count = len(result.rag_chunks_preview)
            logger.info(f"  RAG chunks gevonden: {result.rag_chunks_count}")

            # C: Met RAG
            logger.info("  Genereren MET RAG...")
            orchestrator.rag_service = original_rag_service
            (
                result.definitie_met_rag,
                result.score_met_rag,
                result.violations_met_rag,
                metadata,
            ) = await generate_definition(
                orchestrator,
                begrip,
                term_cfg["organisatorische_context"],
                term_cfg["juridische_context"],
                term_cfg["wettelijke_basis"],
            )
            logger.info(
                f"    Score: {result.score_met_rag:.2f} "
                f"({result.violations_met_rag} violations)"
            )
            logger.info(f"    Definitie: {result.definitie_met_rag[:120]}...")
            logger.info(
                f"    RAG status: {metadata.get('rag_status', 'unknown')}, "
                f"chunks used: {metadata.get('rag_chunks_count', 0)}"
            )

            # D: Vergelijking
            result.score_verschil = result.score_met_rag - result.score_zonder_rag
            result.beter_met_rag = result.score_met_rag > result.score_zonder_rag

            indicator = (
                "+"
                if result.beter_met_rag
                else ("-" if result.score_verschil < 0 else "=")
            )
            logger.info(f"  [{indicator}] Score verschil: {result.score_verschil:+.2f}")

        except Exception as e:
            result.error = str(e)
            logger.error(f"  FOUT: {e}")

        report.results.append(result)

    # Herstel orchestrator
    orchestrator.rag_service = original_rag_service

    # ── Stap 5: Analyse ───────────────────────────────────────
    logger.info(f"\n{'='*60}")
    logger.info("STAP 5: Analyse & Go/No-Go")
    logger.info(f"{'='*60}")

    valid_results = [r for r in report.results if r.error is None]
    report.terms_tested = len(valid_results)
    report.terms_improved = sum(1 for r in valid_results if r.beter_met_rag)

    if valid_results:
        report.avg_score_zonder_rag = sum(
            r.score_zonder_rag for r in valid_results
        ) / len(valid_results)
        report.avg_score_met_rag = sum(r.score_met_rag for r in valid_results) / len(
            valid_results
        )
        report.avg_score_lift = report.avg_score_met_rag - report.avg_score_zonder_rag

    # Go/No-Go beslissing
    if report.terms_improved >= 3:
        report.go_no_go = "GO"
    elif report.terms_improved <= 2 and report.avg_score_lift < 0:
        report.go_no_go = "ONVERWACHT"
    else:
        report.go_no_go = "NO-GO"

    # ── Output ────────────────────────────────────────────────
    _print_summary(report)
    _write_report(report, output_dir)

    return report


def _print_summary(report: SmokeTestReport) -> None:
    """Print samenvatting naar console."""
    logger.info(f"\n{'='*60}")
    logger.info("RESULTAAT")
    logger.info(f"{'='*60}")

    logger.info(f"\n  Wettekst: {report.wettekst}")
    logger.info(f"  Chunks ingested: {report.chunks_ingested}")
    logger.info(f"  Termen getest: {report.terms_tested}")
    logger.info(f"  Termen verbeterd: {report.terms_improved}/{report.terms_tested}")
    logger.info(f"  Gem. score zonder RAG: {report.avg_score_zonder_rag:.3f}")
    logger.info(f"  Gem. score met RAG:    {report.avg_score_met_rag:.3f}")
    logger.info(f"  Gem. score lift:       {report.avg_score_lift:+.3f}")

    logger.info(
        f"\n  {'Term':<25} {'Zonder':>8} {'Met RAG':>8} {'Verschil':>10} {'Beter?':>7}"
    )
    logger.info(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*10} {'-'*7}")
    for r in report.results:
        if r.error:
            logger.info(f"  {r.begrip:<25} {'ERROR':>8} {'':>8} {'':>10} {'':>7}")
        else:
            indicator = "Ja" if r.beter_met_rag else "Nee"
            logger.info(
                f"  {r.begrip:<25} {r.score_zonder_rag:>8.3f} {r.score_met_rag:>8.3f} "
                f"{r.score_verschil:>+10.3f} {indicator:>7}"
            )

    go_emoji = {"GO": "[GO]", "NO-GO": "[NO-GO]", "ONVERWACHT": "[!?]"}.get(
        report.go_no_go, report.go_no_go
    )
    logger.info(f"\n  Beslissing: {go_emoji} {report.go_no_go}")

    if report.go_no_go == "GO":
        logger.info("  -> 3+ termen scoren hoger met RAG. Investeer in DEF-298.")
    elif report.go_no_go == "NO-GO":
        logger.info(
            "  -> <3 termen verbeteren. Eerst RAG-kwaliteit verbeteren "
            "(meer docs, betere chunking) voor Fase 3."
        )
    elif report.go_no_go == "ONVERWACHT":
        logger.info(
            "  -> RAG-context levert LAGERE scores op. "
            "Analyseer waarom (ruis in chunks?)."
        )


def _write_report(report: SmokeTestReport, output_dir: str) -> None:
    """Schrijf rapport als markdown en JSON."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Markdown rapport
    md_path = out / f"smoke-test-{ts}.md"
    lines = [
        "# RAG Smoke Test Rapport",
        f"\n**Datum:** {report.timestamp}",
        f"**Wettekst:** {report.wettekst}",
        f"**Chunks ingested:** {report.chunks_ingested}",
        f"**Beslissing:** {report.go_no_go}",
        "\n## Resultaten",
        "",
        "| Term | Score zonder RAG | Score met RAG | Verschil | Beter? |",
        "|------|-----------------|---------------|----------|--------|",
    ]
    for r in report.results:
        if r.error:
            lines.append(f"| {r.begrip} | ERROR | - | - | - |")
        else:
            beter = "Ja" if r.beter_met_rag else "Nee"
            lines.append(
                f"| {r.begrip} | {r.score_zonder_rag:.3f} | {r.score_met_rag:.3f} "
                f"| {r.score_verschil:+.3f} | {beter} |"
            )

    lines.extend(
        [
            "",
            "## Samenvatting",
            "",
            f"- Termen getest: {report.terms_tested}",
            f"- Termen verbeterd: {report.terms_improved}/{report.terms_tested}",
            f"- Gemiddelde score zonder RAG: {report.avg_score_zonder_rag:.3f}",
            f"- Gemiddelde score met RAG: {report.avg_score_met_rag:.3f}",
            f"- Gemiddelde score lift: {report.avg_score_lift:+.3f}",
            "",
            "## Go/No-Go criteria",
            "",
            "- **GO**: 3+ van 5 termen scoren hoger met RAG-context",
            "- **NO-GO**: 0-2 termen scoren hoger",
            "- **ONVERWACHT**: RAG-context levert lagere scores",
            "",
            f"**Beslissing: {report.go_no_go}**",
            "",
            "## Detail per term",
            "",
        ]
    )

    for r in report.results:
        lines.append(f"### {r.begrip}")
        if r.error:
            lines.append(f"\n**Error:** {r.error}\n")
            continue
        lines.extend(
            [
                "",
                f"**Zonder RAG** (score: {r.score_zonder_rag:.3f}, violations: {r.violations_zonder_rag}):",
                f"> {r.definitie_zonder_rag}",
                "",
                f"**Met RAG** (score: {r.score_met_rag:.3f}, violations: {r.violations_met_rag}):",
                f"> {r.definitie_met_rag}",
                "",
                f"**RAG chunks ({r.rag_chunks_count}):**",
            ]
        )
        for chunk in r.rag_chunks_preview:
            lines.append(f"- `{chunk}`")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"\n  Rapport: {md_path}")

    # JSON voor machine-leesbaar
    json_path = out / f"smoke-test-{ts}.json"
    json_data = {
        "timestamp": report.timestamp,
        "wettekst": report.wettekst,
        "collection_id": report.collection_id,
        "chunks_ingested": report.chunks_ingested,
        "terms_tested": report.terms_tested,
        "terms_improved": report.terms_improved,
        "avg_score_zonder_rag": report.avg_score_zonder_rag,
        "avg_score_met_rag": report.avg_score_met_rag,
        "avg_score_lift": report.avg_score_lift,
        "go_no_go": report.go_no_go,
        "results": [
            {
                "begrip": r.begrip,
                "definitie_zonder_rag": r.definitie_zonder_rag,
                "score_zonder_rag": r.score_zonder_rag,
                "violations_zonder_rag": r.violations_zonder_rag,
                "definitie_met_rag": r.definitie_met_rag,
                "score_met_rag": r.score_met_rag,
                "violations_met_rag": r.violations_met_rag,
                "rag_chunks_count": r.rag_chunks_count,
                "score_verschil": r.score_verschil,
                "beter_met_rag": r.beter_met_rag,
                "error": r.error,
            }
            for r in report.results
        ],
    }
    json_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logger.info(f"  JSON:    {json_path}")


# ── CLI ───────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAG Smoke Test — DEF-318: bewijs dat RAG-context definities verbetert"
    )
    parser.add_argument(
        "--wettekst",
        default="data/wetteksten/wid.txt",
        help="Pad naar de wettekst (default: data/wetteksten/wid.txt)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Alleen chunks bekijken, geen definities genereren",
    )
    parser.add_argument(
        "--output-dir",
        default="data/rag-smoke-test-results",
        help="Output directory voor rapporten",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging (DEBUG level)",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not Path(args.wettekst).exists():
        logger.error(f"Wettekst niet gevonden: {args.wettekst}")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY_PROD"):
        logger.error("OPENAI_API_KEY niet gezet! Export deze eerst.")
        sys.exit(1)

    report = asyncio.run(
        run_smoke_test(
            wettekst_path=args.wettekst,
            dry_run=args.dry_run,
            output_dir=args.output_dir,
        )
    )

    # Exit code: 0 = GO, 1 = NO-GO/ERROR, 2 = ONVERWACHT
    if report.go_no_go == "GO":
        sys.exit(0)
    elif report.go_no_go == "ONVERWACHT":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
