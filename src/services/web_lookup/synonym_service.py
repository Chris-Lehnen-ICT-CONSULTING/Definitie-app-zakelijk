"""
Juridische synoniemen service voor verbeterde term matching.

Deze service ondersteunt bidirectionele synonym expansion voor Wikipedia + SRU lookups.
Synoniemen worden gebruikt als fallback wanneer primaire zoektermen geen resultaten opleveren.

Gebruik:
    service = JuridischeSynoniemlService()
    synoniemen = service.get_synoniemen("onherroepelijk")
    # → ["kracht van gewijsde", "rechtskracht", "in kracht van gewijsde", ...]

    expanded = service.expand_query_terms("voorlopige hechtenis", max_synonyms=3)
    # → ["voorlopige hechtenis", "voorarrest", "bewaring", "inverzekeringstelling"]
"""

import logging
from pathlib import Path

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("Warning: PyYAML niet beschikbaar - synoniemen service werkt niet volledig")

logger = logging.getLogger(__name__)


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

        # Synoniemen database: {normalized_term: [synoniemen]}
        self.synoniemen: dict[str, list[str]] = {}

        # Reverse index voor bidirectionele lookup: {synoniem: hoofdterm}
        self.reverse_index: dict[str, str] = {}

        # Load synoniemen uit YAML
        self._load_synoniemen()

        logger.info(
            f"Synoniemen service geïnitialiseerd met {len(self.synoniemen)} hoofdtermen "
            f"en {len(self.reverse_index)} synoniemen"
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

        YAML format:
            hoofdterm:
              - synoniem1
              - synoniem2

        Bouwt beide forward index (term → synoniemen) en reverse index (synoniem → term).
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

            # Bouw forward index (hoofdterm → synoniemen)
            for hoofdterm_raw, synoniemen_raw in data.items():
                # Skip comments/metadata entries
                if not isinstance(synoniemen_raw, list):
                    continue

                hoofdterm = self._normalize_term(hoofdterm_raw)

                # Normaliseer synoniemen
                synoniemen = [
                    self._normalize_term(s)
                    for s in synoniemen_raw
                    if isinstance(s, str)
                ]

                # Filter lege synoniemen
                synoniemen = [s for s in synoniemen if s]

                if not synoniemen:
                    continue

                self.synoniemen[hoofdterm] = synoniemen

                # Bouw reverse index: elk synoniem wijst naar hoofdterm
                for syn in synoniemen:
                    self.reverse_index[syn] = hoofdterm

            logger.info(
                f"Geladen: {len(self.synoniemen)} hoofdtermen, "
                f"{len(self.reverse_index)} synoniemen uit {self.config_path}"
            )

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {self.config_path}: {e}")
        except Exception as e:
            logger.error(f"Fout bij laden synoniemen uit {self.config_path}: {e}")

    def get_synoniemen(self, term: str) -> list[str]:
        """
        Haal synoniemen op voor een term (bidirectioneel).

        Bidirectionele lookup:
        1. Als term een hoofdterm is → return synoniemen
        2. Als term een synoniem is → return synoniemen van hoofdterm
        3. Anders → return lege lijst

        Args:
            term: Zoekterm

        Returns:
            Lijst van synoniemen (kan leeg zijn)

        Example:
            >>> service.get_synoniemen("onherroepelijk")
            ['kracht van gewijsde', 'rechtskracht', 'in kracht van gewijsde', ...]

            >>> service.get_synoniemen("kracht van gewijsde")  # reverse lookup
            ['onherroepelijk', 'rechtskracht', 'in kracht van gewijsde', ...]
        """
        normalized = self._normalize_term(term)

        # Case 1: Term is hoofdterm
        if normalized in self.synoniemen:
            return self.synoniemen[normalized].copy()

        # Case 2: Term is synoniem → lookup hoofdterm → return synoniemen
        if normalized in self.reverse_index:
            hoofdterm = self.reverse_index[normalized]
            synoniemen = self.synoniemen.get(hoofdterm, []).copy()

            # Voeg hoofdterm toe aan resultaat (volledige synoniemen set)
            if hoofdterm not in synoniemen:
                synoniemen.insert(0, hoofdterm)

            # Verwijder de originele term uit resultaat (niet jezelf als synoniem)
            synoniemen = [s for s in synoniemen if s != normalized]

            return synoniemen

        # Case 3: Niet gevonden
        return []

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
            "gemiddeld_per_term": (
                total_synoniemen / len(self.synoniemen) if self.synoniemen else 0
            ),
        }


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
