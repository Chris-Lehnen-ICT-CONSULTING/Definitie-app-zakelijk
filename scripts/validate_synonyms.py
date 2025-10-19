#!/usr/bin/env python3
"""
Juridische Synoniemen Validator
================================

Validates the juridische_synoniemen.yaml file for:
- Empty synonym lists
- Duplicate synonyms within same hoofdterm
- Cross-contamination (synonyms appearing under multiple hoofdtermen)
- Circular references (hoofdterm appears as synonym elsewhere)
- Inconsistent normalization (spacing, underscores)
- YAML syntax errors

Exit codes:
    0: Validation passed
    1: Validation failed with errors

Usage:
    python scripts/validate_synonyms.py
    python scripts/validate_synonyms.py --config path/to/synoniemen.yaml
    python scripts/validate_synonyms.py --no-color
"""

import argparse
import sys
from pathlib import Path

import yaml


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls) -> None:
        """Disable all colors for non-color terminals."""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""
        cls.BOLD = ""
        cls.RESET = ""


def normalize_term(term: str) -> str:
    """
    Normalize a term according to the application's normalization rules.

    Rules:
    - Lowercase
    - Strip whitespace
    - Replace underscores with spaces

    Args:
        term: The term to normalize

    Returns:
        Normalized term
    """
    return term.lower().strip().replace("_", " ")


def load_yaml_file(file_path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """
    Load and parse the YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Tuple of (parsed data, list of errors)
    """
    errors = []

    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return {}, errors

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            errors.append("YAML file is empty")
            return {}, errors

        if not isinstance(data, dict):
            errors.append(f"Expected dict at root level, got {type(data).__name__}")
            return {}, errors

        return data, errors

    except yaml.YAMLError as e:
        errors.append(f"YAML syntax error: {e}")
        return {}, errors
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return {}, errors


def parse_synonym_entry(entry: any) -> tuple[str, float]:
    """
    Parse a synonym entry (legacy or weighted format).

    Args:
        entry: Either a string (legacy) or dict with 'synoniem' and 'weight'

    Returns:
        Tuple of (synonym_term, weight)
    """
    # Legacy format: plain string
    if isinstance(entry, str):
        return (entry, 1.0)

    # Enhanced format: dict with 'synoniem' and optional 'weight'
    if isinstance(entry, dict):
        if "synoniem" in entry:
            term = entry["synoniem"]
            weight = float(entry.get("weight", 1.0))
            return (term, weight)
        # Invalid dict format - return as-is for error reporting
        return (str(entry), 1.0)

    # Unknown format
    return (str(entry), 1.0)


def validate_empty_lists(data: dict[str, list[str]]) -> list[str]:
    """
    Validate that no hoofdterm has an empty synonym list.

    Args:
        data: The parsed YAML data

    Returns:
        List of error messages
    """
    errors = []

    for hoofdterm, synoniemen in data.items():
        # Skip _clusters section (validated separately)
        if hoofdterm == "_clusters":
            continue

        if not synoniemen:
            errors.append(f"Empty synonym list for hoofdterm: '{hoofdterm}'")
        elif not isinstance(synoniemen, list):
            errors.append(
                f"Invalid type for '{hoofdterm}': expected list, got {type(synoniemen).__name__}"
            )

    return errors


def validate_duplicates_within_hoofdterm(data: dict[str, list[str]]) -> list[str]:
    """
    Validate that no hoofdterm has duplicate synonyms.

    Args:
        data: The parsed YAML data

    Returns:
        List of error messages
    """
    errors = []

    for hoofdterm, synoniemen in data.items():
        if not isinstance(synoniemen, list):
            continue

        # Track both raw and normalized forms
        seen_normalized: dict[str, str] = {}

        for syn_entry in synoniemen:
            # Parse entry (supports both legacy and weighted formats)
            syn, weight = parse_synonym_entry(syn_entry)

            if not isinstance(syn, str):
                errors.append(
                    f"Non-string synonym in '{hoofdterm}': {syn} ({type(syn).__name__})"
                )
                continue

            normalized = normalize_term(syn)

            if normalized in seen_normalized:
                original = seen_normalized[normalized]
                errors.append(
                    f"Duplicate synonym in '{hoofdterm}': '{syn}' (same as '{original}' after normalization)"
                )
            else:
                seen_normalized[normalized] = syn

    return errors


def validate_cross_contamination(data: dict[str, list[str]]) -> list[str]:
    """
    Validate that no synonym appears under multiple hoofdtermen.

    Args:
        data: The parsed YAML data

    Returns:
        List of error messages
    """
    errors = []

    # Build reverse mapping: normalized synonym -> list of (hoofdterm, weight)
    synonym_to_hoofdtermen: dict[str, list[tuple[str, float]]] = {}

    for hoofdterm, synoniemen in data.items():
        if not isinstance(synoniemen, list):
            continue

        for syn_entry in synoniemen:
            # Parse entry (supports both legacy and weighted formats)
            syn, weight = parse_synonym_entry(syn_entry)

            if not isinstance(syn, str):
                continue

            normalized = normalize_term(syn)

            if normalized not in synonym_to_hoofdtermen:
                synonym_to_hoofdtermen[normalized] = []

            synonym_to_hoofdtermen[normalized].append((hoofdterm, weight))

    # Find cross-contamination
    for syn_normalized, hoofdtermen_list in synonym_to_hoofdtermen.items():
        if len(hoofdtermen_list) > 1:
            hoofdtermen_str = ", ".join(f"'{ht}'" for ht, _ in sorted(hoofdtermen_list))
            errors.append(
                f"Cross-contamination: synonym '{syn_normalized}' appears under multiple hoofdtermen: {hoofdtermen_str}"
            )

    return errors


def validate_circular_references(data: dict[str, list[str]]) -> list[str]:
    """
    Validate that no hoofdterm appears as a synonym elsewhere.

    Args:
        data: The parsed YAML data

    Returns:
        List of error messages
    """
    errors = []

    # Normalize all hoofdtermen
    normalized_hoofdtermen = {normalize_term(ht) for ht in data}

    # Check if any synonym matches a hoofdterm
    for hoofdterm, synoniemen in data.items():
        if not isinstance(synoniemen, list):
            continue

        for syn_entry in synoniemen:
            # Parse entry (supports both legacy and weighted formats)
            syn, weight = parse_synonym_entry(syn_entry)

            if not isinstance(syn, str):
                continue

            normalized_syn = normalize_term(syn)

            if normalized_syn in normalized_hoofdtermen:
                errors.append(
                    f"Circular reference: synonym '{syn}' in '{hoofdterm}' is also a hoofdterm"
                )

    return errors


def validate_synonym_weights(data: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    """
    Validate synonym weights (enhanced format only).

    Checks:
    - Weight range (0.0-1.0)
    - Warning for unusual weights (< 0.5 or > 1.0)
    - Warning for weight conflicts (same synonym, different weights)

    Args:
        data: The parsed YAML data

    Returns:
        Tuple of (error_list, warning_list)
    """
    errors = []
    warnings = []

    # Track weights for cross-hoofdterm comparison
    synonym_weights: dict[str, list[tuple[str, float]]] = {}

    for hoofdterm, synoniemen in data.items():
        if not isinstance(synoniemen, list):
            continue

        for syn_entry in synoniemen:
            # Skip legacy format (no weight validation needed)
            if isinstance(syn_entry, str):
                continue

            # Enhanced format validation
            if isinstance(syn_entry, dict):
                if "synoniem" not in syn_entry:
                    errors.append(
                        f"Dict entry in '{hoofdterm}' missing 'synoniem' key: {syn_entry}"
                    )
                    continue

                syn = syn_entry["synoniem"]
                normalized_syn = normalize_term(syn)

                # Check if weight is present
                if "weight" not in syn_entry:
                    # Not an error - weight defaults to 1.0
                    continue

                try:
                    weight = float(syn_entry["weight"])
                except (ValueError, TypeError) as e:
                    errors.append(
                        f"Invalid weight for '{syn}' in '{hoofdterm}': {syn_entry.get('weight')} ({e})"
                    )
                    continue

                # Validate weight range
                if weight < 0.0 or weight > 1.0:
                    errors.append(
                        f"Weight for '{syn}' in '{hoofdterm}' outside valid range [0.0, 1.0]: {weight}"
                    )

                # Warning for unusual weights
                if 0.0 <= weight < 0.5:
                    warnings.append(
                        f"Low weight for '{syn}' in '{hoofdterm}': {weight} (< 0.5) - may be too weak"
                    )
                elif weight > 1.0:
                    warnings.append(
                        f"Weight for '{syn}' in '{hoofdterm}' exceeds 1.0: {weight}"
                    )

                # Track for cross-hoofdterm comparison
                if normalized_syn not in synonym_weights:
                    synonym_weights[normalized_syn] = []
                synonym_weights[normalized_syn].append((hoofdterm, weight))

    # Check for weight conflicts (same synonym, different weights in multiple hoofdtermen)
    for syn_normalized, weight_list in synonym_weights.items():
        if len(weight_list) > 1:
            # Check if weights differ
            weights = [w for _, w in weight_list]
            if len(set(weights)) > 1:
                weight_strs = ", ".join(f"'{ht}': {w}" for ht, w in sorted(weight_list))
                warnings.append(
                    f"Weight conflict for synonym '{syn_normalized}': {weight_strs}"
                )

    return errors, warnings


def validate_normalization_consistency(data: dict[str, list[str]]) -> list[str]:
    """
    Validate normalization consistency.

    Checks:
    - Hoofdtermen should use underscores for multi-word terms
    - Synonyms should use spaces (will be normalized at runtime)
    - No leading/trailing whitespace in raw values

    Args:
        data: The parsed YAML data

    Returns:
        List of warning messages (not errors, as these are style issues)
    """
    warnings = []

    for hoofdterm, synoniemen in data.items():
        # Skip _clusters section
        if hoofdterm == "_clusters":
            continue

        # Check hoofdterm for whitespace issues
        if hoofdterm != hoofdterm.strip():
            warnings.append(f"Hoofdterm has leading/trailing whitespace: '{hoofdterm}'")

        # Check if multi-word hoofdterm uses spaces instead of underscores
        if " " in hoofdterm:
            suggested = hoofdterm.replace(" ", "_")
            warnings.append(
                f"Hoofdterm '{hoofdterm}' contains spaces, consider using underscores: '{suggested}'"
            )

        if not isinstance(synoniemen, list):
            continue

        for syn in synoniemen:
            if not isinstance(syn, str):
                continue

            # Check for whitespace issues
            if syn != syn.strip():
                warnings.append(
                    f"Synonym has leading/trailing whitespace in '{hoofdterm}': '{syn}'"
                )

            # Check if synonym uses underscore (should use spaces)
            if "_" in syn:
                warnings.append(
                    f"Synonym contains underscore in '{hoofdterm}': '{syn}' (underscores are normalized to spaces)"
                )

    return warnings


def validate_clusters(data: dict[str, any]) -> tuple[list[str], list[str]]:
    """
    Validate semantic clusters in _clusters section.

    Checks:
    - Empty cluster lists
    - Duplicate terms within same cluster
    - Terms appearing in multiple clusters (cross-cluster contamination)
    - Terms that are both hoofdterm and in a cluster (potential confusion)

    Args:
        data: The parsed YAML data

    Returns:
        Tuple of (error_list, warning_list)
    """
    errors = []
    warnings = []

    # Get _clusters section
    clusters_data = data.get("_clusters")

    # No clusters is valid (optional feature)
    if clusters_data is None:
        return errors, warnings

    if not isinstance(clusters_data, dict):
        errors.append(
            f"_clusters section has invalid type: {type(clusters_data).__name__}, expected dict"
        )
        return errors, warnings

    # Build reverse mapping: normalized term → list of cluster names
    term_to_clusters: dict[str, list[str]] = {}

    # Collect all hoofdtermen (for cross-reference check)
    hoofdtermen = {normalize_term(ht) for ht in data if ht != "_clusters"}

    for cluster_name, terms in clusters_data.items():
        if not isinstance(terms, list):
            errors.append(
                f"Cluster '{cluster_name}' has invalid type: {type(terms).__name__}, expected list"
            )
            continue

        if not terms:
            errors.append(f"Cluster '{cluster_name}' is empty")
            continue

        # Track normalized terms for duplicate detection
        seen_normalized: dict[str, str] = {}

        for term_raw in terms:
            if not isinstance(term_raw, str):
                errors.append(
                    f"Non-string term in cluster '{cluster_name}': {term_raw} ({type(term_raw).__name__})"
                )
                continue

            normalized = normalize_term(term_raw)

            # Check for duplicates within same cluster
            if normalized in seen_normalized:
                original = seen_normalized[normalized]
                errors.append(
                    f"Duplicate term in cluster '{cluster_name}': '{term_raw}' (same as '{original}' after normalization)"
                )
            else:
                seen_normalized[normalized] = term_raw

            # Build reverse mapping for cross-cluster check
            if normalized not in term_to_clusters:
                term_to_clusters[normalized] = []
            term_to_clusters[normalized].append(cluster_name)

            # Check if term is also a hoofdterm (warning, not error)
            if normalized in hoofdtermen:
                warnings.append(
                    f"Term '{normalized}' in cluster '{cluster_name}' is also a hoofdterm - may cause confusion"
                )

    # Check for cross-cluster contamination (term in multiple clusters)
    for term_normalized, cluster_list in term_to_clusters.items():
        if len(cluster_list) > 1:
            cluster_str = ", ".join(f"'{c}'" for c in sorted(cluster_list))
            errors.append(
                f"Cross-cluster contamination: term '{term_normalized}' appears in multiple clusters: {cluster_str}"
            )

    return errors, warnings


def print_header(title: str, color: str = Colors.CYAN) -> None:
    """Print a formatted section header."""
    print(f"\n{color}{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{color}{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")


def print_summary(
    data: dict[str, list[str]],
    all_errors: list[str],
    all_warnings: list[str],
) -> None:
    """Print validation summary."""
    print_header("Validation Summary", Colors.BLUE)

    # Count statistics
    num_hoofdtermen = len(data)
    num_synoniemen = sum(len(syns) for syns in data.values() if isinstance(syns, list))

    print(f"{Colors.BOLD}File Statistics:{Colors.RESET}")
    print(f"  Hoofdtermen: {num_hoofdtermen}")
    print(f"  Total synonyms: {num_synoniemen}")
    print(
        f"  Average synonyms per hoofdterm: {num_synoniemen / max(num_hoofdtermen, 1):.1f}"
    )

    print(f"\n{Colors.BOLD}Validation Results:{Colors.RESET}")
    print(
        f"  {Colors.RED}Errors: {len(all_errors)}{Colors.RESET}"
        if all_errors
        else f"  {Colors.GREEN}Errors: 0{Colors.RESET}"
    )
    print(
        f"  {Colors.YELLOW}Warnings: {len(all_warnings)}{Colors.RESET}"
        if all_warnings
        else "  Warnings: 0"
    )

    if not all_errors and not all_warnings:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All validations passed!{Colors.RESET}")
    elif not all_errors:
        print(
            f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Validation passed with warnings{Colors.RESET}"
        )
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Validation failed{Colors.RESET}")


def main() -> int:
    """
    Main validation function.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    parser = argparse.ArgumentParser(
        description="Validate juridische_synoniemen.yaml file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/juridische_synoniemen.yaml"),
        help="Path to the synoniemen YAML file (default: config/juridische_synoniemen.yaml)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    print_header("Juridische Synoniemen Validator", Colors.MAGENTA)
    print(f"Validating: {Colors.BOLD}{args.config}{Colors.RESET}\n")

    # Load YAML file
    data, load_errors = load_yaml_file(args.config)

    if load_errors:
        print(f"{Colors.RED}{Colors.BOLD}YAML Loading Errors:{Colors.RESET}")
        for error in load_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
        return 1

    # Run all validations
    all_errors: list[str] = []
    all_warnings: list[str] = []

    # 1. Empty lists
    print(f"{Colors.CYAN}[1/5] Checking for empty synonym lists...{Colors.RESET}")
    empty_errors = validate_empty_lists(data)
    all_errors.extend(empty_errors)
    if empty_errors:
        for error in empty_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    else:
        print(f"  {Colors.GREEN}✓ No empty lists found{Colors.RESET}")

    # 2. Duplicates within hoofdterm
    print(
        f"\n{Colors.CYAN}[2/5] Checking for duplicate synonyms within hoofdtermen...{Colors.RESET}"
    )
    dup_errors = validate_duplicates_within_hoofdterm(data)
    all_errors.extend(dup_errors)
    if dup_errors:
        for error in dup_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    else:
        print(f"  {Colors.GREEN}✓ No duplicates found{Colors.RESET}")

    # 3. Cross-contamination
    print(
        f"\n{Colors.CYAN}[3/5] Checking for cross-contamination (synonyms under multiple hoofdtermen)...{Colors.RESET}"
    )
    cross_errors = validate_cross_contamination(data)
    all_errors.extend(cross_errors)
    if cross_errors:
        for error in cross_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    else:
        print(f"  {Colors.GREEN}✓ No cross-contamination found{Colors.RESET}")

    # 4. Circular references
    print(f"\n{Colors.CYAN}[4/5] Checking for circular references...{Colors.RESET}")
    circular_errors = validate_circular_references(data)
    all_errors.extend(circular_errors)
    if circular_errors:
        for error in circular_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    else:
        print(f"  {Colors.GREEN}✓ No circular references found{Colors.RESET}")

    # 5. Synonym weights (v2.0)
    print(f"\n{Colors.CYAN}[5/6] Validating synonym weights...{Colors.RESET}")
    weight_errors, weight_warnings = validate_synonym_weights(data)
    all_errors.extend(weight_errors)
    all_warnings.extend(weight_warnings)
    if weight_errors:
        for error in weight_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    if weight_warnings:
        for warning in weight_warnings:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} {warning}")
    if not weight_errors and not weight_warnings:
        print(f"  {Colors.GREEN}✓ All weights are valid{Colors.RESET}")

    # 6. Normalization consistency
    print(f"\n{Colors.CYAN}[6/7] Checking normalization consistency...{Colors.RESET}")
    norm_warnings = validate_normalization_consistency(data)
    all_warnings.extend(norm_warnings)
    if norm_warnings:
        for warning in norm_warnings:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} {warning}")
    else:
        print(f"  {Colors.GREEN}✓ Normalization is consistent{Colors.RESET}")

    # 7. Cluster validation
    print(f"\n{Colors.CYAN}[7/7] Validating semantic clusters...{Colors.RESET}")
    cluster_errors, cluster_warnings = validate_clusters(data)
    all_errors.extend(cluster_errors)
    all_warnings.extend(cluster_warnings)
    if cluster_errors:
        for error in cluster_errors:
            print(f"  {Colors.RED}✗{Colors.RESET} {error}")
    if cluster_warnings:
        for warning in cluster_warnings:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} {warning}")
    if not cluster_errors and not cluster_warnings:
        clusters_data = data.get("_clusters")
        if clusters_data:
            num_clusters = len(clusters_data)
            print(
                f"  {Colors.GREEN}✓ All {num_clusters} clusters are valid{Colors.RESET}"
            )
        else:
            print(
                f"  {Colors.GREEN}✓ No clusters defined (optional feature){Colors.RESET}"
            )

    # Print summary
    print_summary(data, all_errors, all_warnings)

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
