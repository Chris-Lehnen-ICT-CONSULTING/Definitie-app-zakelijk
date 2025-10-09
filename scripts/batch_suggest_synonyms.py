#!/usr/bin/env python3
"""
Batch Synonym Suggestion CLI Script

Process multiple juridische hoofdtermen en genereer GPT-4 synonym suggestions.
Suggestions worden opgeslagen in de database en geëxporteerd naar CSV.

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
    hoofdterm,synoniem,confidence,rationale,status
    verdachte,beschuldigde,0.85,"In strafrecht context...",pending
"""

import argparse
import asyncio
import csv
import logging
import sys
from pathlib import Path
from time import sleep
from typing import List

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from repositories.synonym_repository import SynonymRepository, get_synonym_repository
from services.synonym_automation.gpt4_suggester import (
    GPT4SynonymSuggester,
    SynonymSuggestion,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Batch processor voor synonym suggestions."""

    def __init__(
        self,
        suggester: GPT4SynonymSuggester,
        repository: SynonymRepository | None = None,
        rate_limit: float = 1.0,
        dry_run: bool = False,
    ):
        """
        Initialize batch processor.

        Args:
            suggester: GPT4SynonymSuggester instance
            repository: SynonymRepository instance (None for dry-run)
            rate_limit: Seconds to wait between API calls (0 = no limit)
            dry_run: If True, don't save to database
        """
        self.suggester = suggester
        self.repository = repository
        self.rate_limit = rate_limit
        self.dry_run = dry_run

    async def process_term(self, term: str) -> List[SynonymSuggestion]:
        """
        Process single term and generate suggestions.

        Args:
            term: Hoofdterm to process

        Returns:
            List of SynonymSuggestion objects
        """
        try:
            suggestions = await self.suggester.suggest_synonyms(term)

            # Save to database (unless dry-run)
            if not self.dry_run and self.repository:
                for suggestion in suggestions:
                    try:
                        self.repository.save_suggestion(
                            hoofdterm=suggestion.hoofdterm,
                            synoniem=suggestion.synoniem,
                            confidence=suggestion.confidence,
                            rationale=suggestion.rationale,
                            context=suggestion.context_used,
                        )
                    except ValueError as e:
                        # Duplicate suggestion - log and continue
                        logger.warning(f"Skipping duplicate: {e}")

            return suggestions

        except Exception as e:
            logger.error(f"Error processing '{term}': {e}")
            return []

    async def process_terms(self, terms: List[str]) -> List[dict]:
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

            suggestions = await self.process_term(term)

            if suggestions:
                print(f"  ✓ Found {len(suggestions)} suggestions")
                for suggestion in suggestions:
                    results.append(
                        {
                            "hoofdterm": suggestion.hoofdterm,
                            "synoniem": suggestion.synoniem,
                            "confidence": suggestion.confidence,
                            "rationale": suggestion.rationale,
                            "status": "pending",
                        }
                    )
            else:
                print(f"  ✗ No suggestions generated")

            # Rate limiting (except for last term)
            if self.rate_limit > 0 and i < total:
                sleep(self.rate_limit)

        return results


def load_terms_from_csv(csv_path: Path) -> List[str]:
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
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    terms = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate column
        if "hoofdterm" not in reader.fieldnames:
            raise ValueError(
                f"CSV must have 'hoofdterm' column. Found: {reader.fieldnames}"
            )

        # Extract terms
        for row in reader:
            term = row["hoofdterm"].strip()
            if term:  # Skip empty rows
                terms.append(term)

    logger.info(f"Loaded {len(terms)} terms from {csv_path}")
    return terms


def export_to_csv(results: List[dict], output_path: Path):
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
        fieldnames = ["hoofdterm", "synoniem", "confidence", "rationale", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Exported {len(results)} suggestions to {output_path}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch process synonym suggestions voor juridische termen",
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
        "--confidence",
        type=float,
        default=0.6,
        help="Minimum confidence threshold (default: 0.6)",
    )
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
        help="Preview without saving to database",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4-turbo",
        help="GPT model to use (default: gpt-4-turbo)",
    )
    parser.add_argument(
        "--max-synonyms",
        type=int,
        default=8,
        help="Maximum synonyms per term (default: 8)",
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

    logger.info(f"Processing {len(terms)} terms with GPT-4")
    if args.dry_run:
        logger.info("DRY RUN: Results will not be saved to database")

    # Initialize services
    suggester = GPT4SynonymSuggester(
        model=args.model,
        min_confidence=args.confidence,
        max_synonyms=args.max_synonyms,
    )

    repository = None
    if not args.dry_run:
        try:
            repository = get_synonym_repository()
            logger.info("Connected to synonym repository")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            sys.exit(1)

    # Process terms
    processor = BatchProcessor(
        suggester=suggester,
        repository=repository,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run,
    )

    try:
        results = await processor.process_terms(terms)

        # Export results
        if results:
            export_to_csv(results, args.output)
            print(f"\n✓ Success: Generated {len(results)} suggestions")
            print(f"  Output: {args.output}")

            if not args.dry_run:
                print(f"  Database: Updated with new suggestions")
            else:
                print(f"  Database: NOT updated (dry-run mode)")

            sys.exit(0)
        else:
            print(f"\n✗ No suggestions generated")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
