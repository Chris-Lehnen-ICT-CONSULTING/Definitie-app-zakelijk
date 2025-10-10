#!/usr/bin/env python3
"""
Batch script voor het extraheren van Wikipedia synoniemen voor juridische termen.

Dit script:
1. Laadt hoofdtermen uit juridische_synoniemen.yaml
2. Zoekt voor elke term naar synoniemen via Wikipedia API
3. Exporteert resultaten naar CSV voor handmatige review
4. Toont progress bar en error handling

Usage:
    python scripts/extract_wikipedia_synonyms.py
    python scripts/extract_wikipedia_synonyms.py --output data/custom_output.csv
    python scripts/extract_wikipedia_synonyms.py --rate-limit 2.0  # Slower rate
    python scripts/extract_wikipedia_synonyms.py --max-terms 10  # Test met 10 termen
"""

import asyncio
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path voor imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("ERROR: PyYAML niet geïnstalleerd. Run: pip install pyyaml")
    sys.exit(1)

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Warning: tqdm niet geïnstalleerd (geen progress bar). Run: pip install tqdm")

from services.web_lookup.wikipedia_synonym_extractor import (
    SynonymCandidate, WikipediaSynonymExtractor)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/wikipedia_synonym_extraction.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_hoofdtermen(config_path: Path) -> list[str]:
    """
    Laad hoofdtermen uit juridische_synoniemen.yaml.

    Args:
        config_path: Pad naar juridische_synoniemen.yaml

    Returns:
        Lijst van hoofdtermen
    """
    if not config_path.exists():
        logger.error(f"Config bestand niet gevonden: {config_path}")
        return []

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning("Lege config - geen hoofdtermen gevonden")
            return []

        # Extract hoofdtermen (skip _clusters and metadata)
        hoofdtermen = []
        for key, value in data.items():
            # Skip special sections
            if key.startswith("_") or not isinstance(value, list):
                continue

            # Normalize term (replace underscores with spaces)
            normalized = key.replace("_", " ").strip()
            if normalized:
                hoofdtermen.append(normalized)

        logger.info(f"Geladen: {len(hoofdtermen)} hoofdtermen uit {config_path}")
        return sorted(hoofdtermen)

    except yaml.YAMLError as e:
        logger.error(f"YAML parse error in {config_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Fout bij laden hoofdtermen uit {config_path}: {e}")
        return []


async def extract_synonyms_batch(
    hoofdtermen: list[str],
    rate_limit_delay: float = 1.0,
    max_terms: int | None = None,
) -> list[SynonymCandidate]:
    """
    Extract Wikipedia synonyms voor een batch van hoofdtermen.

    Args:
        hoofdtermen: Lijst van hoofdtermen om te verwerken
        rate_limit_delay: Delay tussen requests in seconden (Wikipedia: 1 req/sec)
        max_terms: Maximum aantal termen om te verwerken (None = alle)

    Returns:
        Lijst van alle gevonden SynonymCandidate objecten
    """
    all_candidates: list[SynonymCandidate] = []

    # Limit aantal termen indien gespecificeerd
    terms_to_process = hoofdtermen[:max_terms] if max_terms else hoofdtermen

    logger.info(
        f"Starting batch extraction voor {len(terms_to_process)} termen "
        f"(rate limit: {rate_limit_delay}s)"
    )

    # Initialize extractor
    async with WikipediaSynonymExtractor(
        language="nl", rate_limit_delay=rate_limit_delay
    ) as extractor:

        # Progress bar setup
        if TQDM_AVAILABLE:
            progress = tqdm(terms_to_process, desc="Extracting Wikipedia synonyms")
        else:
            progress = terms_to_process

        for i, term in enumerate(progress, 1):
            try:
                # Update progress description
                if TQDM_AVAILABLE:
                    progress.set_description(f"Processing: {term[:30]}")

                # Extract synonyms
                candidates = await extractor.extract_synonyms(term)

                # Add to results
                all_candidates.extend(candidates)

                # Log progress
                if not TQDM_AVAILABLE:
                    logger.info(
                        f"[{i}/{len(terms_to_process)}] Processed '{term}': "
                        f"{len(candidates)} candidates found"
                    )

            except Exception as e:
                logger.error(f"Error processing '{term}': {e}")
                continue

    logger.info(
        f"Batch extraction complete: {len(all_candidates)} total candidates found"
    )
    return all_candidates


def export_to_csv(candidates: list[SynonymCandidate], output_path: Path) -> None:
    """
    Exporteer synonym candidates naar CSV bestand.

    CSV format:
        hoofdterm, synoniem_kandidaat, confidence, source_type, wikipedia_url, edit_distance, redirect_type

    Args:
        candidates: Lijst van SynonymCandidate objecten
        output_path: Pad voor output CSV bestand
    """
    if not candidates:
        logger.warning("Geen candidates om te exporteren")
        return

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "hoofdterm",
                "synoniem_kandidaat",
                "confidence",
                "source_type",
                "wikipedia_url",
                "edit_distance",
                "redirect_type",
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for candidate in candidates:
                writer.writerow(candidate.to_dict())

        logger.info(f"Exported {len(candidates)} candidates to {output_path}")
        print(
            f"\n✓ Successfully exported {len(candidates)} candidates to {output_path}"
        )

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        print(f"\n✗ Error exporting to CSV: {e}")


def print_summary(candidates: list[SynonymCandidate]) -> None:
    """
    Print summary statistieken van extraction results.

    Args:
        candidates: Lijst van SynonymCandidate objecten
    """
    if not candidates:
        print("\nNo candidates found.")
        return

    # Calculate statistics
    total = len(candidates)
    by_source = {}
    by_confidence = {"high": 0, "medium": 0, "low": 0}
    unique_terms = set()

    for candidate in candidates:
        # Count by source type
        by_source[candidate.source_type] = by_source.get(candidate.source_type, 0) + 1

        # Count by confidence level
        if candidate.confidence >= 0.85:
            by_confidence["high"] += 1
        elif candidate.confidence >= 0.70:
            by_confidence["medium"] += 1
        else:
            by_confidence["low"] += 1

        # Track unique hoofdtermen
        unique_terms.add(candidate.hoofdterm)

    # Print summary
    print("\n" + "=" * 60)
    print("WIKIPEDIA SYNONYM EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"\nTotal candidates found: {total}")
    print(f"Unique hoofdtermen processed: {len(unique_terms)}")
    print("\nBy source type:")
    for source, count in sorted(by_source.items()):
        print(f"  - {source:20s}: {count:3d} ({count/total*100:.1f}%)")
    print("\nBy confidence level:")
    print(
        f"  - High (≥0.85):   {by_confidence['high']:3d} ({by_confidence['high']/total*100:.1f}%)"
    )
    print(
        f"  - Medium (0.70-0.84): {by_confidence['medium']:3d} ({by_confidence['medium']/total*100:.1f}%)"
    )
    print(
        f"  - Low (<0.70):    {by_confidence['low']:3d} ({by_confidence['low']/total*100:.1f}%)"
    )
    print("\n" + "=" * 60)

    # Show top 10 candidates
    print("\nTop 10 highest confidence candidates:")
    print("-" * 60)
    top_candidates = sorted(candidates, key=lambda c: c.confidence, reverse=True)[:10]
    for i, candidate in enumerate(top_candidates, 1):
        print(
            f"{i:2d}. {candidate.hoofdterm:25s} → {candidate.synoniem:25s} "
            f"({candidate.confidence:.2f}, {candidate.source_type})"
        )
    print()


async def main(
    output_path: Path | None = None,
    rate_limit_delay: float = 1.0,
    max_terms: int | None = None,
) -> None:
    """
    Main async function voor batch Wikipedia synonym extraction.

    Args:
        output_path: Output CSV path (default: data/wikipedia_synonym_candidates.csv)
        rate_limit_delay: Delay tussen requests (default: 1.0 sec)
        max_terms: Maximum aantal termen om te verwerken (None = alle)
    """
    # Setup paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "juridische_synoniemen.yaml"

    if output_path is None:
        output_path = project_root / "data" / "wikipedia_synonym_candidates.csv"

    # Create logs directory if not exists
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("WIKIPEDIA SYNONYM EXTRACTOR - Batch Processing")
    print("=" * 60)
    print(f"\nConfig: {config_path}")
    print(f"Output: {output_path}")
    print(f"Rate limit: {rate_limit_delay} sec/request")
    if max_terms:
        print(f"Max terms: {max_terms} (test mode)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load hoofdtermen
    print("Loading hoofdtermen from config...")
    hoofdtermen = load_hoofdtermen(config_path)

    if not hoofdtermen:
        print("ERROR: No hoofdtermen loaded. Check config file.")
        return

    print(f"✓ Loaded {len(hoofdtermen)} hoofdtermen")
    print()

    # Extract synonyms
    print("Extracting Wikipedia synonyms...")
    print("(This may take a while due to Wikipedia API rate limits)")
    print()

    candidates = await extract_synonyms_batch(
        hoofdtermen, rate_limit_delay=rate_limit_delay, max_terms=max_terms
    )

    # Export results
    print("\nExporting results to CSV...")
    export_to_csv(candidates, output_path)

    # Print summary
    print_summary(candidates)

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nNext steps:")
    print(f"1. Review the CSV file: {output_path}")
    print("2. Manually validate synonym candidates")
    print("3. Add validated synonyms to juridische_synoniemen.yaml")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Wikipedia synonyms for juridische termen"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output CSV path (default: data/wikipedia_synonym_candidates.csv)",
    )
    parser.add_argument(
        "--rate-limit",
        "-r",
        type=float,
        default=1.0,
        help="Rate limit delay in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--max-terms",
        "-m",
        type=int,
        help="Maximum aantal termen om te verwerken (voor testing)",
    )

    args = parser.parse_args()

    # Parse output path
    output_path = Path(args.output) if args.output else None

    # Run async main
    asyncio.run(main(output_path, args.rate_limit, args.max_terms))
