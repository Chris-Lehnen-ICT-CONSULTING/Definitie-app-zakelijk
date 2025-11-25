"""
Juridische synoniemen service voor verbeterde term matching.

Deze service ondersteunt bidirectionele synonym expansion voor Wikipedia + SRU lookups.
Synoniemen worden gebruikt als fallback wanneer primaire zoektermen geen resultaten opleveren.

Sinds v2.0: Ondersteunt weighted synonyms voor confidence-based ranking.

Gebruik:
    service = JuridischeSynoniemlService()
    synoniemen = service.get_synoniemen("onherroepelijk")
    # → ["kracht van gewijsde", "rechtskracht", "in kracht van gewijsde", ...]

    expanded = service.expand_query_terms("voorlopige hechtenis", max_synonyms=3)
    # → ["voorlopige hechtenis", "voorarrest", "bewaring", "inverzekeringstelling"]

    # Weighted synonyms (v2.0+)
    weighted = service.get_synonyms_with_weights("onherroepelijk")
    # → [("kracht van gewijsde", 0.95), ("rechtskracht", 0.90), ...]

    best = service.get_best_synonyms("onherroepelijk", threshold=0.85)
    # → ["kracht van gewijsde", "rechtskracht"]
"""

import logging
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML niet beschikbaar - synoniemen service werkt niet volledig")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeightedSynonym:
    """
    Represents a synonym with confidence weight.

    Attributes:
        term: The synonym term (normalized)
        weight: Confidence weight (0.0-1.0)
                1.0 = exact/perfect synonym
                0.95 = nearly exact
                0.85-0.90 = strong synonym
                0.70-0.80 = good synonym
                0.50-0.65 = weak/contextual synonym
                < 0.50 = questionable (use with caution)
    """

    term: str
    weight: float = 1.0

    def __post_init__(self):
        """Validate weight range and warn on unusual values."""
        if not 0.0 <= self.weight <= 1.0:
            logger.warning(
                f"Synonym '{self.term}' has weight {self.weight} outside valid range [0.0, 1.0]"
            )
        elif self.weight < 0.5:
            logger.warning(
                f"Synonym '{self.term}' has low weight {self.weight} (< 0.5) - may be too weak"
            )
        elif self.weight > 1.0:
            logger.warning(
                f"Synonym '{self.term}' has weight {self.weight} > 1.0 - capping to 1.0"
            )
            # Note: frozen dataclass, so we can't modify. Validation only.


class JuridischeSynoniemlService:
    """
    Service voor juridische synoniemen lookup en query expansion.

    Ondersteunt:
    - Bidirectionele synonym matching (zoek term → vind synoniemen, en vice versa)
    - Query expansion voor verbeterde recall in Wikipedia/SRU
    - Configurable maximum synoniemen per term
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialiseer synoniemen service.

        Args:
            config_path: Pad naar juridische_synoniemen.yaml (optioneel)
                        Default: config/juridische_synoniemen.yaml
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Zoek config relatief aan project root
            # src/services/web_lookup → src → Definitie-app
            current = Path(__file__).parent.parent.parent.parent
            self.config_path = current / "config" / "juridische_synoniemen.yaml"

        # Synoniemen database: {normalized_term: [WeightedSynonym]}
        # Sorted by weight (highest first)
        self.synoniemen: dict[str, list[WeightedSynonym]] = {}

        # Reverse index voor bidirectionele lookup: {synoniem: hoofdterm}
        self.reverse_index: dict[str, str] = {}

        # Semantic clusters: {cluster_name: [term1, term2, ...]}
        # Terms are RELATED (not synonyms) - for cascade fallback and suggestions
        self.clusters: dict[str, list[str]] = {}

        # Reverse cluster index: {term: cluster_name}
        self.term_to_cluster: dict[str, str] = {}

        # Load synoniemen uit YAML
        self._load_synoniemen()

        logger.info(
            f"Synoniemen service geïnitialiseerd met {len(self.synoniemen)} hoofdtermen, "
            f"{len(self.reverse_index)} synoniemen, en {len(self.clusters)} clusters"
        )

    def _normalize_term(self, term: str) -> str:
        """
        Normaliseer term voor consistente lookup.

        Conversies:
        - Lowercase
        - Strip whitespace
        - Vervang underscores met spaties (YAML keys)
        """
        return term.lower().strip().replace("_", " ")

    def _load_synoniemen(self) -> None:
        """
        Laad synoniemen uit YAML config.

        YAML format (backward compatible):
            # Legacy format (plain strings, weight defaults to 1.0):
            hoofdterm:
              - synoniem1
              - synoniem2

            # Enhanced format (with weights):
            hoofdterm:
              - synoniem: synoniem1
                weight: 0.95
              - synoniem: synoniem2
                weight: 0.90
              - synoniem3  # Legacy format still works

        Bouwt beide forward index (term → synoniemen) en reverse index (synoniem → term).
        Synoniemen worden gesorteerd op weight (hoogste eerst).
        """
        if not YAML_AVAILABLE:
            logger.warning("PyYAML niet beschikbaar - synoniemen niet geladen")
            return

        if not self.config_path.exists():
            logger.warning(
                f"Synoniemen config niet gevonden: {self.config_path}. "
                f"Synoniemen service werkt zonder synoniemen."
            )
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                logger.warning("Lege synoniemen config - geen synoniemen geladen")
                return

            # Bouw forward index (hoofdterm → synoniemen) en laad clusters
            for hoofdterm_raw, synoniemen_raw in data.items():
                # Handle special _clusters section
                if hoofdterm_raw == "_clusters":
                    self._load_clusters(synoniemen_raw)
                    continue

                # Skip comments/metadata entries
                if not isinstance(synoniemen_raw, list):
                    continue

                hoofdterm = self._normalize_term(hoofdterm_raw)

                # Parse synoniemen (supports both formats)
                weighted_synoniemen: list[WeightedSynonym] = []

                for syn_entry in synoniemen_raw:
                    # Legacy format: plain string
                    if isinstance(syn_entry, str):
                        normalized = self._normalize_term(syn_entry)
                        if normalized:  # Skip empty
                            weighted_synoniemen.append(
                                WeightedSynonym(term=normalized, weight=1.0)
                            )

                    # Enhanced format: dict with 'synoniem' and 'weight' keys
                    elif isinstance(syn_entry, dict):
                        if "synoniem" in syn_entry:
                            normalized = self._normalize_term(syn_entry["synoniem"])
                            weight = float(syn_entry.get("weight", 1.0))

                            # Clamp weight to valid range [0.0, 1.0]
                            weight = max(0.0, min(1.0, weight))

                            if normalized:  # Skip empty
                                weighted_synoniemen.append(
                                    WeightedSynonym(term=normalized, weight=weight)
                                )
                        else:
                            logger.warning(
                                f"Dict synonym entry in '{hoofdterm_raw}' missing 'synoniem' key: {syn_entry}"
                            )

                    else:
                        logger.warning(
                            f"Unexpected synonym type in '{hoofdterm_raw}': {type(syn_entry).__name__}"
                        )

                if not weighted_synoniemen:
                    continue

                # Sort by weight (highest first)
                weighted_synoniemen.sort(key=lambda ws: ws.weight, reverse=True)

                self.synoniemen[hoofdterm] = weighted_synoniemen

                # Bouw reverse index: elk synoniem wijst naar hoofdterm
                for ws in weighted_synoniemen:
                    self.reverse_index[ws.term] = hoofdterm

            logger.info(
                f"Geladen: {len(self.synoniemen)} hoofdtermen, "
                f"{len(self.reverse_index)} synoniemen uit {self.config_path}"
            )

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {self.config_path}: {e}")
        except Exception as e:
            logger.error(f"Fout bij laden synoniemen uit {self.config_path}: {e}")

    def _load_clusters(self, clusters_data: dict) -> None:
        """
        Laad semantic clusters uit _clusters sectie.

        YAML format:
            _clusters:
              rechtsmiddelen:
                - rechtsmiddel
                - hoger_beroep
                - cassatie
              straffen:
                - gevangenisstraf
                - taakstraf

        Args:
            clusters_data: Dict van cluster_name → list[term]

        Bouwt beide forward index (cluster → terms) en reverse index (term → cluster).
        Terms kunnen slechts in één cluster zitten (exclusief lidmaatschap).
        """
        if not isinstance(clusters_data, dict):
            logger.warning(
                f"_clusters section has invalid type: {type(clusters_data).__name__}, expected dict"
            )
            return

        for cluster_name, terms in clusters_data.items():
            if not isinstance(terms, list):
                logger.warning(
                    f"Cluster '{cluster_name}' has invalid type: {type(terms).__name__}, expected list"
                )
                continue

            if not terms:
                logger.warning(f"Cluster '{cluster_name}' is empty")
                continue

            # Normalize all terms
            normalized_terms = []
            for term_raw in terms:
                if not isinstance(term_raw, str):
                    logger.warning(
                        f"Non-string term in cluster '{cluster_name}': {term_raw}"
                    )
                    continue

                normalized = self._normalize_term(term_raw)
                if not normalized:
                    continue

                # Check for duplicate membership (term already in another cluster)
                if normalized in self.term_to_cluster:
                    existing_cluster = self.term_to_cluster[normalized]
                    logger.warning(
                        f"Term '{normalized}' appears in multiple clusters: "
                        f"'{existing_cluster}' and '{cluster_name}'. "
                        f"Keeping first occurrence ('{existing_cluster}')."
                    )
                    continue

                normalized_terms.append(normalized)
                self.term_to_cluster[normalized] = cluster_name

            if normalized_terms:
                self.clusters[cluster_name] = normalized_terms
                logger.debug(
                    f"Loaded cluster '{cluster_name}' with {len(normalized_terms)} terms"
                )

        logger.info(
            f"Geladen: {len(self.clusters)} clusters met "
            f"{len(self.term_to_cluster)} totaal termen"
        )

    def get_synoniemen(self, term: str) -> list[str]:
        """
        Haal synoniemen op voor een term (bidirectioneel).

        Bidirectionele lookup:
        1. Als term een hoofdterm is → return synoniemen (sorted by weight)
        2. Als term een synoniem is → return synoniemen van hoofdterm
        3. Anders → return lege lijst

        Note: Returns plain strings (no weights). Use get_synonyms_with_weights()
              for weighted results.

        Args:
            term: Zoekterm

        Returns:
            Lijst van synoniemen (sorted by weight, highest first)

        Example:
            >>> service.get_synoniemen("onherroepelijk")
            ['kracht van gewijsde', 'rechtskracht', 'in kracht van gewijsde', ...]

            >>> service.get_synoniemen("kracht van gewijsde")  # reverse lookup
            ['onherroepelijk', 'rechtskracht', 'in kracht van gewijsde', ...]
        """
        normalized = self._normalize_term(term)

        # Case 1: Term is hoofdterm
        if normalized in self.synoniemen:
            return [ws.term for ws in self.synoniemen[normalized]]

        # Case 2: Term is synoniem → lookup hoofdterm → return synoniemen
        if normalized in self.reverse_index:
            hoofdterm = self.reverse_index[normalized]
            weighted_syns = self.synoniemen.get(hoofdterm, [])

            # Extract terms
            synoniemen = [ws.term for ws in weighted_syns]

            # Voeg hoofdterm toe aan resultaat (volledige synoniemen set)
            if hoofdterm not in synoniemen:
                synoniemen.insert(0, hoofdterm)

            # Verwijder de originele term uit resultaat (niet jezelf als synoniem)
            return [s for s in synoniemen if s != normalized]

        # Case 3: Niet gevonden
        return []

    def get_synonyms_with_weights(self, term: str) -> list[tuple[str, float]]:
        """
        Haal synoniemen op met hun confidence weights (bidirectioneel).

        Bidirectionele lookup zoals get_synoniemen(), maar returnt (term, weight) tuples.
        Hoofdterm krijgt weight 1.0 bij reverse lookup.

        Args:
            term: Zoekterm

        Returns:
            Lijst van (synonym, weight) tuples, sorted by weight (highest first)

        Example:
            >>> service.get_synonyms_with_weights("onherroepelijk")
            [("kracht van gewijsde", 0.95), ("rechtskracht", 0.90), ...]

            >>> service.get_synonyms_with_weights("voorarrest")  # reverse lookup
            [("voorlopige hechtenis", 1.0), ("bewaring", 0.90), ...]
        """
        normalized = self._normalize_term(term)

        # Case 1: Term is hoofdterm
        if normalized in self.synoniemen:
            return [(ws.term, ws.weight) for ws in self.synoniemen[normalized]]

        # Case 2: Term is synoniem → lookup hoofdterm → return synoniemen
        if normalized in self.reverse_index:
            hoofdterm = self.reverse_index[normalized]
            weighted_syns = self.synoniemen.get(hoofdterm, [])

            # Build result: hoofdterm (weight 1.0) + synoniemen
            results: list[tuple[str, float]] = []

            # Add hoofdterm first
            results.append((hoofdterm, 1.0))

            # Add other synoniemen (exclude original term)
            for ws in weighted_syns:
                if ws.term != normalized:
                    results.append((ws.term, ws.weight))

            # Sort by weight (highest first)
            results.sort(key=lambda x: x[1], reverse=True)

            return results

        # Case 3: Niet gevonden
        return []

    def get_best_synonyms(self, term: str, threshold: float = 0.85) -> list[str]:
        """
        Haal alleen synoniemen op boven een bepaalde weight threshold.

        Nuttig voor high-precision queries waar je alleen sterke synoniemen wilt.

        Args:
            term: Zoekterm
            threshold: Minimum weight (0.0-1.0). Default: 0.85 (strong synonyms only)

        Returns:
            Lijst van synoniemen met weight >= threshold, sorted by weight

        Example:
            >>> service.get_best_synonyms("onherroepelijk", threshold=0.90)
            ['kracht van gewijsde', 'rechtskracht']  # Only weight >= 0.90

            >>> service.get_best_synonyms("onherroepelijk", threshold=0.50)
            ['kracht van gewijsde', 'rechtskracht', 'definitieve uitspraak', ...]
        """
        weighted = self.get_synonyms_with_weights(term)
        return [syn for syn, weight in weighted if weight >= threshold]

    def expand_query_terms(self, term: str, max_synonyms: int = 3) -> list[str]:
        """
        Expand term met synoniemen voor query diversificatie.

        Gebruikt synoniemen om query recall te verhogen. Beperkt aantal
        synoniemen om query complexity te managen.

        Args:
            term: Originele zoekterm
            max_synonyms: Maximum aantal synoniemen toe te voegen (default: 3)

        Returns:
            Lijst met [originele_term, synonym1, synonym2, ...]

        Example:
            >>> service.expand_query_terms("voorlopige hechtenis", max_synonyms=2)
            ['voorlopige hechtenis', 'voorarrest', 'bewaring']
        """
        # Start met originele term
        expanded = [term]

        # Haal synoniemen op
        synoniemen = self.get_synoniemen(term)

        if not synoniemen:
            return expanded

        # Voeg top-N synoniemen toe
        expanded.extend(synoniemen[:max_synonyms])

        return expanded

    def has_synoniemen(self, term: str) -> bool:
        """
        Check of een term synoniemen heeft.

        Args:
            term: Zoekterm

        Returns:
            True als term synoniemen heeft, anders False
        """
        return len(self.get_synoniemen(term)) > 0

    def get_all_terms(self) -> set[str]:
        """
        Haal alle bekende termen op (hoofdtermen + synoniemen).

        Returns:
            Set van alle termen in de database
        """
        all_terms: set[str] = set()

        # Voeg hoofdtermen toe
        all_terms.update(self.synoniemen.keys())

        # Voeg synoniemen toe
        all_terms.update(self.reverse_index.keys())

        return all_terms

    def find_matching_synoniemen(self, text: str) -> dict[str, list[str]]:
        """
        Vind alle juridische termen in een tekst en hun synoniemen.

        Gebruikt greedy matching om termen te vinden in langere teksten.
        Nuttig voor text enrichment en context analysis.

        Args:
            text: Tekst om te scannen

        Returns:
            Dict van {gevonden_term: [synoniemen]}

        Example:
            >>> text = "De verdachte kreeg een onherroepelijke veroordeling"
            >>> service.find_matching_synoniemen(text)
            {
                'verdachte': ['beklaagde', 'beschuldigde', ...],
                'onherroepelijke': ['kracht van gewijsde', 'rechtskracht', ...]
            }
        """
        normalized_text = self._normalize_term(text)
        matches: dict[str, list[str]] = {}

        # Check alle bekende termen
        for term in self.get_all_terms():
            if term in normalized_text:
                synoniemen = self.get_synoniemen(term)
                if synoniemen:
                    matches[term] = synoniemen

        return matches

    def get_stats(self) -> dict[str, int]:
        """
        Haal statistieken op over synoniemen database.

        Returns:
            Dict met statistieken
        """
        total_synoniemen = sum(len(syns) for syns in self.synoniemen.values())

        return {
            "hoofdtermen": len(self.synoniemen),
            "totaal_synoniemen": total_synoniemen,
            "unieke_synoniemen": len(self.reverse_index),
            "gemiddeld_per_term": int(
                total_synoniemen / len(self.synoniemen) if self.synoniemen else 0
            ),
            "clusters": len(self.clusters),
            "termen_in_clusters": len(self.term_to_cluster),
        }

    # === SEMANTIC CLUSTER METHODS ===

    def get_related_terms(self, term: str) -> list[str]:
        """
        Haal gerelateerde termen op uit dezelfde semantic cluster.

        Gerelateerde termen zijn NIET synoniemen, maar delen wel een semantisch domein.
        Bijvoorbeeld: "hoger beroep", "cassatie", "verzet" zijn allemaal rechtsmiddelen.

        Args:
            term: Zoekterm

        Returns:
            Lijst van gerelateerde termen (exclusief de term zelf), of lege lijst
            als term niet in een cluster zit.

        Example:
            >>> service.get_related_terms("hoger beroep")
            ['rechtsmiddel', 'cassatie', 'verzet', 'herziening']

            >>> service.get_related_terms("onbekende term")
            []
        """
        normalized = self._normalize_term(term)

        # Lookup cluster
        cluster_name = self.term_to_cluster.get(normalized)
        if not cluster_name:
            return []

        # Get all terms in cluster, excluding the term itself
        cluster_terms = self.clusters.get(cluster_name, [])
        return [t for t in cluster_terms if t != normalized]

    def get_cluster_name(self, term: str) -> str | None:
        """
        Haal cluster naam op voor een term.

        Args:
            term: Zoekterm

        Returns:
            Cluster naam, of None als term niet in een cluster zit.

        Example:
            >>> service.get_cluster_name("hoger beroep")
            'rechtsmiddelen'

            >>> service.get_cluster_name("onbekende term")
            None
        """
        normalized = self._normalize_term(term)
        return self.term_to_cluster.get(normalized)

    def expand_with_related(
        self, term: str, max_synonyms: int = 3, max_related: int = 2
    ) -> list[str]:
        """
        Expand term met ZOWEL synoniemen als gerelateerde cluster termen.

        Deze methode combineert synonym expansion (voor precision) met cluster
        expansion (voor recall). Nuttig voor cascade fallback queries.

        Args:
            term: Originele zoekterm
            max_synonyms: Maximum aantal synoniemen (default: 3)
            max_related: Maximum aantal gerelateerde cluster termen (default: 2)

        Returns:
            Lijst met [originele_term, synonyms..., related_terms...]

        Example:
            >>> service.expand_with_related("hoger beroep", max_synonyms=2, max_related=2)
            ['hoger beroep', 'appel', 'appelprocedure', 'cassatie', 'rechtsmiddel']
            #                 ^original  ^synonyms            ^related cluster terms

        Use cases:
            - Cascade fallback: probeer eerst synoniemen, dan gerelateerde termen
            - Context enrichment: voeg semantisch gerelateerde context toe aan prompts
            - Related suggestions: "Je zou ook kunnen zoeken naar: cassatie, verzet"
        """
        # Start met originele term
        expanded = [term]

        # Voeg synoniemen toe (high precision)
        synoniemen = self.get_synoniemen(term)
        if synoniemen:
            expanded.extend(synoniemen[:max_synonyms])

        # Voeg gerelateerde cluster termen toe (high recall)
        related = self.get_related_terms(term)
        if related:
            # Filter out terms already added as synonyms
            new_related = [r for r in related if r not in expanded]
            expanded.extend(new_related[:max_related])

        return expanded


# Module-level singleton voor hergebruik
_singleton: JuridischeSynoniemlService | None = None


def get_synonym_service(config_path: str | None = None) -> JuridischeSynoniemlService:
    """
    Haal singleton synoniemen service op.

    Args:
        config_path: Optioneel custom config pad

    Returns:
        JuridischeSynoniemlService instance
    """
    global _singleton

    if _singleton is None or config_path is not None:
        _singleton = JuridischeSynoniemlService(config_path)

    return _singleton
