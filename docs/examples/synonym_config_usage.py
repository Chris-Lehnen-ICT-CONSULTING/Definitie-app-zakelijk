"""
SynonymConfiguration Usage Examples

This file demonstrates how the SynonymConfiguration will be integrated
into the SynonymOrchestrator (PHASE 2.1).

Architecture Reference:
    docs/architectuur/synonym-orchestrator-architecture-v3.1.md
    Lines 325-501: SynonymOrchestrator specification
"""

# Example 1: Basic Usage in SynonymOrchestrator
# =============================================

from config.synonym_config import SynonymPolicy, get_synonym_config


class SynonymOrchestrator:
    """Example implementation showing config usage."""

    def __init__(self, registry, gpt4_suggester):
        self.registry = registry
        self.gpt4_suggester = gpt4_suggester
        self.config = get_synonym_config()  # ← Load centralized config

    def get_synonyms_for_lookup(
        self,
        term: str,
        max_results: int = 5,
        min_weight: float | None = None,
    ):
        """
        Get synonyms met TTL cache + governance.

        Uses config for:
        - Governance policy (strict vs pragmatic)
        - Min weight threshold
        """
        term_normalized = term.lower().strip()

        # Determine statuses based on governance policy
        statuses = ["active"]
        if self.config.policy == SynonymPolicy.PRAGMATIC:
            statuses.append("ai_pending")

        # Use config for min_weight threshold
        min_weight = min_weight or self.config.min_weight_for_weblookup

        # Query registry
        synonyms = self.registry.get_synonyms(
            term=term_normalized,
            statuses=statuses,  # ← Policy-driven
            min_weight=min_weight,  # ← Config-driven
            order_by=["is_preferred DESC", "weight DESC", "usage_count DESC"],
            limit=max_results * 2,
        )

        return synonyms[:max_results]

    async def ensure_synonyms(
        self, term: str, min_count: int | None = None, context: dict | None = None
    ):
        """
        Ensure term has min_count synoniemen (GPT-4 sync OK!).

        Uses config for:
        - Min synonyms threshold
        - GPT-4 timeout
        """
        # Use config threshold if not specified
        min_count = min_count or self.config.min_synonyms_threshold

        # Check existing
        existing = self.get_synonyms_for_lookup(term, max_results=10)

        if len(existing) >= min_count:
            return existing[:min_count], 0  # ✅ Fast path

        # Slow path: GPT-4 enrichment
        import asyncio

        try:
            ai_suggestions = await asyncio.wait_for(
                self.gpt4_suggester.suggest_synonyms(
                    term=term,
                    definitie=context.get("definitie") if context else None,
                    context=context.get("tokens") if context else None,
                ),
                timeout=self.config.gpt4_timeout_seconds,  # ← Config timeout
            )

            # Save suggestions...
            # (implementation details omitted)

            return existing, len(ai_suggestions)

        except TimeoutError:
            return existing, 0  # Fail gracefully


# Example 2: Policy-Based Behavior
# =================================


def example_policy_comparison():
    """Show how policy affects synonym selection."""
    from config.synonym_config import get_policy_statuses

    print("Policy Comparison:")
    print("-" * 60)

    # STRICT policy
    strict_statuses = get_policy_statuses(SynonymPolicy.STRICT)
    print(f"STRICT policy: statuses = {strict_statuses}")
    print("  → Only approved synonyms (status='active')")
    print("  → Best for compliance-critical environments")
    print()

    # PRAGMATIC policy
    pragmatic_statuses = get_policy_statuses(SynonymPolicy.PRAGMATIC)
    print(f"PRAGMATIC policy: statuses = {pragmatic_statuses}")
    print("  → AI-pending synonyms also allowed")
    print("  → Better coverage, pending review")
    print()


# Example 3: Runtime Configuration Reload
# ========================================


def example_admin_ui_reload():
    """Show how admin UI can reload configuration."""
    from config.synonym_config import reload_config

    # Admin changes config via UI
    print("Admin updates synonym_config.yaml...")

    # Reload configuration
    new_config = reload_config()
    print(f"Configuration reloaded: policy={new_config.policy.value}")

    # All new orchestrator calls will use updated config
    # (existing instances need to be recreated or manually update config)


# Example 4: Validation Before Use
# =================================


def example_validation():
    """Show how to validate config before using it."""
    from config.synonym_config import SynonymConfiguration

    # Load custom config
    config = SynonymConfiguration.from_yaml("config/synonym_config.yaml")

    # Validate
    errors = config.validate()

    if errors:
        print("❌ Configuration errors detected:")
        for error in errors:
            print(f"  - {error}")
        # Handle errors (e.g., refuse to start, use defaults, etc.)
    else:
        print("✅ Configuration is valid")


# Example 5: Environment Variable Override
# =========================================


def example_env_override():
    """Show how to use environment variable for config path."""
    import os

    # Set custom config path via environment
    os.environ["SYNONYM_CONFIG_PATH"] = "/path/to/custom/config.yaml"

    # Config will be loaded from custom path
    from config.synonym_config import get_synonym_config

    config = get_synonym_config()
    print(f"Loaded from: {os.environ['SYNONYM_CONFIG_PATH']}")


# Example 6: Weight Threshold Usage
# ==================================


def example_weight_thresholds():
    """Show how weight thresholds are used."""
    config = get_synonym_config()

    # Example synonym with weight
    synonym_weight = 0.96

    # Check if preferred
    if synonym_weight >= config.preferred_weight_threshold:
        is_preferred = True
        print(
            f"✅ Synonym weight {synonym_weight} >= {config.preferred_weight_threshold}"
        )
        print("   → Marked as preferred (is_preferred=TRUE)")
    else:
        is_preferred = False
        print(
            f"❌ Synonym weight {synonym_weight} < {config.preferred_weight_threshold}"
        )
        print("   → Not preferred")

    # Check if usable in weblookup
    if synonym_weight >= config.min_weight_for_weblookup:
        print(
            f"✅ Synonym weight {synonym_weight} >= {config.min_weight_for_weblookup}"
        )
        print("   → Included in weblookup")
    else:
        print(f"❌ Synonym weight {synonym_weight} < {config.min_weight_for_weblookup}")
        print("   → Excluded from weblookup")


# Example 7: Cache Configuration
# ===============================


def example_cache_config():
    """Show how cache configuration is used."""
    config = get_synonym_config()

    print("Cache Configuration:")
    print("-" * 60)
    print(f"TTL: {config.cache_ttl_seconds}s ({config.cache_ttl_seconds // 3600}h)")
    print(f"Max Size: {config.cache_max_size} entries")
    print()
    print("Example cache implementation:")
    print(f"  if time.time() - cache_timestamp > {config.cache_ttl_seconds}:")
    print("      # Entry expired, refetch from database")
    print()
    print(f"  if len(cache) >= {config.cache_max_size}:")
    print("      # Evict oldest entry (LRU)")


if __name__ == "__main__":
    print("=" * 80)
    print("SynonymConfiguration Usage Examples")
    print("=" * 80)
    print()

    example_policy_comparison()
    print()

    print("For more examples, see individual functions in this file.")
    print()
    print("Integration Points:")
    print(
        "  - SynonymOrchestrator.get_synonyms_for_lookup() → uses policy + min_weight"
    )
    print("  - SynonymOrchestrator.ensure_synonyms() → uses min_synonyms + timeout")
    print("  - TTL Cache → uses cache_ttl + cache_max_size")
    print("  - Weight calculation → uses preferred_threshold")
