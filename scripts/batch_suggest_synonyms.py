#!/usr/bin/env python3
"""
Batch Synonym Suggestion CLI Script (v3.1)

Process multiple juridische hoofdtermen en genereer GPT-4 synonym suggestions
via SynonymOrchestrator architecture.

Architecture v3.1: Uses SynonymOrchestrator.ensure_synonyms() → ai_pending members

Usage Examples:
    # Process from CSV file
    python scripts/batch_suggest_synonyms.py --input data/terms.csv --output data/results.csv

    # Process inline terms
    python scripts/batch_suggest_synonyms.py --terms "verdachte,getuige" --confidence 0.7

    # Dry run (preview only, no database save)
    python scripts/batch_suggest_synonyms.py --terms "rechter" --dry-run

    # With rate limiting (1.5 seconds between API calls)
    python scripts/batch_suggest_synonyms.py --input data/terms.csv --rate-limit 1.5

Input CSV Format:
    hoofdterm
    verdachte
    getuige
    rechter

Output CSV Format:
    hoofdterm,synoniem,weight,rationale,status
    verdachte,beschuldigde,0.85,"In strafrecht context...",ai_pending
"""

import argparse
import asyncio
import csv
import json
import logging
import sys
from pathlib import Path
from time import sleep

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from repositories.synonym_registry import SynonymRegistry
from services.container import get_container
from services.synonym_orchestrator import SynonymOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class BatchProcessorV3:
    """
    Batch processor voor synonym suggestions (Architecture v3.1).

    Uses SynonymOrchestrator.ensure_synonyms() to generate and save
    suggestions as ai_pending members in synonym_groups tables.
    """

    def __init__(
        self,
        orchestrator: SynonymOrchestrator,
        registry: SynonymRegistry,
        rate_limit: float = 1.0,
        dry_run: bool = False,
        min_count: int = 5,
    ):
        """
        Initialize batch processor.

        Args:
            orchestrator: SynonymOrchestrator instance
            registry: SynonymRegistry instance
            rate_limit: Seconds to wait between API calls (0 = no limit)
            dry_run: If True, only query existing (no GPT-4 enrichment)
            min_count: Minimum synonyms to ensure per term
        """
        self.orchestrator = orchestrator
        self.registry = registry
        self.rate_limit = rate_limit
        self.dry_run = dry_run
        self.min_count = min_count

    async def process_term(self, term: str) -> list[dict]:
        """
        Process single term and generate suggestions via orchestrator.

        Args:
            term: Hoofdterm to process

        Returns:
            List of synonym result dictionaries
        """
        try:
            if self.dry_run:
                # Dry run: only query existing (no GPT-4 enrichment)
                synonyms = self.orchestrator.get_synonyms_for_lookup(
                    term, max_results=20
                )
                ai_pending_count = 0
            else:
                # Live mode: trigger GPT-4 enrichment if needed
                synonyms, ai_pending_count = await self.orchestrator.ensure_synonyms(
                    term=term, min_count=self.min_count, context=None
                )

            if ai_pending_count > 0:
                logger.info(
                    f"  ✓ {ai_pending_count} new AI suggestions generated for '{term}'"
                )

            # Convert to result dicts
            results = []
            for syn in synonyms:
                # Extract rationale from context if available
                rationale = ""
                if hasattr(syn, "context") and syn.context:
                    try:
                        context_dict = (
                            json.loads(syn.context)
                            if isinstance(syn.context, str)
                            else syn.context
                        )
                        rationale = context_dict.get("rationale", "")
                    except Exception:
                        pass

                results.append(
                    {
                        "hoofdterm": term,
                        "synoniem": syn.term,
                        "weight": syn.weight,
                        "rationale": rationale,
                        "status": syn.status if hasattr(syn, "status") else "unknown",
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Error processing '{term}': {e}", exc_info=True)
            return []

    async def process_terms(self, terms: list[str]) -> list[dict]:
        """
        Process multiple terms with progress feedback.

        Args:
            terms: List of hoofdtermen to process

        Returns:
            List of result dictionaries for CSV export
        """
        results = []
        total = len(terms)

        for i, term in enumerate(terms, 1):
            print(f"\n[{i}/{total}] Processing: {term}")

            term_results = await self.process_term(term)

            if term_results:
                print(f"  ✓ Found {len(term_results)} synonyms")
                results.extend(term_results)
            else:
                print("  ✗ No synonyms found")

            # Rate limiting (except for last term)
            if self.rate_limit > 0 and i < total:
                sleep(self.rate_limit)

        return results


def load_terms_from_csv(csv_path: Path) -> list[str]:
    """
    Load hoofdtermen from CSV file.

    Args:
        csv_path: Path to CSV file with 'hoofdterm' column

    Returns:
        List of hoofdtermen

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is malformed or missing 'hoofdterm' column
    """
    if not csv_path.exists():
        msg = f"CSV file not found: {csv_path}"
        raise FileNotFoundError(msg)

    terms = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate column
        if "hoofdterm" not in reader.fieldnames:
            msg = f"CSV must have 'hoofdterm' column. Found: {reader.fieldnames}"
            raise ValueError(msg)

        # Extract terms
        for row in reader:
            term = row["hoofdterm"].strip()
            if term:  # Skip empty rows
                terms.append(term)

    logger.info(f"Loaded {len(terms)} terms from {csv_path}")
    return terms


def export_to_csv(results: list[dict], output_path: Path):
    """
    Export results to CSV file.

    Args:
        results: List of result dictionaries
        output_path: Path to output CSV file
    """
    if not results:
        logger.warning("No results to export")
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["hoofdterm", "synoniem", "weight", "rationale", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Exported {len(results)} synonyms to {output_path}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch process synonym suggestions voor juridische termen (v3.1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        type=Path,
        help="CSV file with hoofdtermen (column: 'hoofdterm')",
    )
    input_group.add_argument(
        "--terms",
        type=str,
        help="Comma-separated hoofdtermen (e.g., 'verdachte,getuige')",
    )

    # Configuration options
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synonym_suggestions.csv"),
        help="Output CSV path (default: data/synonym_suggestions.csv)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds between API calls (default: 1.0, 0 = no limit)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Query existing only (no GPT-4 enrichment)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=5,
        help="Minimum synonyms to ensure per term (default: 5)",
    )

    args = parser.parse_args()

    # Load terms
    if args.input:
        try:
            terms = load_terms_from_csv(args.input)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to load terms from CSV: {e}")
            sys.exit(1)
    else:
        # Parse comma-separated terms
        terms = [t.strip() for t in args.terms.split(",") if t.strip()]

    if not terms:
        logger.error("No terms to process")
        sys.exit(1)

    logger.info(f"Processing {len(terms)} terms with SynonymOrchestrator v3.1")
    if args.dry_run:
        logger.info("DRY RUN: Only querying existing synonyms (no GPT-4 enrichment)")

    # Initialize services via container
    try:
        container = get_container()
        orchestrator = container.synonym_orchestrator()
        registry = container.synonym_registry()
        logger.info("Connected to SynonymOrchestrator + SynonymRegistry (v3.1)")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        sys.exit(1)

    # Process terms
    processor = BatchProcessorV3(
        orchestrator=orchestrator,
        registry=registry,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run,
        min_count=args.min_count,
    )

    try:
        results = await processor.process_terms(terms)

        # Export results
        if results:
            export_to_csv(results, args.output)
            print(f"\n✓ Success: Generated {len(results)} synonym entries")
            print(f"  Output: {args.output}")

            if not args.dry_run:
                print("  Database: Updated with new ai_pending members (v3.1)")
            else:
                print("  Database: Only queried existing (no enrichment)")

            sys.exit(0)
        else:
            print("\n✗ No synonyms generated")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
