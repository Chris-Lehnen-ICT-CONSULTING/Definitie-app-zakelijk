"""
DUP-01: Database Duplicate Detection.

Detecteert of een definitie al bestaat in de database.
"""

import logging

logger = logging.getLogger(__name__)


class DUP01:
    """Detecteer duplicate definities in database."""

    def __init__(self):
        """Initialize duplicate detector."""
        self.repository = None
        self._initialize_repository()

    def _initialize_repository(self):
        """Lazy initialize repository via ServiceContainer singleton (DEF-183)."""
        try:
            from services.container import get_container

            container = get_container()
            self.repository = container.repository()
        except Exception as e:
            logger.warning(
                f"Could not initialize repository for duplicate detection: {e}"
            )
            self.repository = None

    def check(
        self, definitie: str, begrip: str = "", context: dict | None = None
    ) -> dict:
        """
        Check voor duplicate definities in database.

        Args:
            definitie: De te controleren definitie
            begrip: Het begrip waarvoor de definitie is
            context: Extra context (niet gebruikt voor duplicate check)

        Returns:
            Validatie resultaat dict
        """
        if not self.repository:
            # Can't check without repository
            return {
                "voldoet": True,
                "toelichting": "Duplicate check overgeslagen (database niet beschikbaar)",
            }

        if not begrip:
            # Need begrip to check for duplicates
            return {
                "voldoet": True,
                "toelichting": "Duplicate check overgeslagen (begrip ontbreekt)",
            }

        try:
            # Zoek bestaande definities voor dit begrip
            existing = self.repository.search_definitions(search_term=begrip)

            if not existing:
                return {
                    "voldoet": True,
                    "toelichting": "Geen bestaande definities gevonden voor dit begrip",
                }

            # Normaliseer definitie voor vergelijking
            normalized_new = self._normalize_text(definitie)

            # Check voor exacte of bijna-exacte duplicates
            for record in existing:
                if record.get("begrip", "").lower() == begrip.lower():
                    existing_def = record.get("definitie_gecorrigeerd") or record.get(
                        "definitie", ""
                    )
                    normalized_existing = self._normalize_text(existing_def)

                    # Exacte match
                    if normalized_new == normalized_existing:
                        return {
                            "voldoet": False,
                            "toelichting": f"Exacte duplicate gevonden (ID: {record.get('id')})",
                            "suggestie": "Gebruik de bestaande definitie of pas deze substantieel aan",
                        }

                    # Similarity check (> 90% overlap)
                    similarity = self._calculate_similarity(
                        normalized_new, normalized_existing
                    )
                    if similarity > 0.9:
                        return {
                            "voldoet": False,
                            "toelichting": f"Zeer vergelijkbare definitie gevonden ({int(similarity*100)}% overlap, ID: {record.get('id')})",
                            "suggestie": "Overweeg de bestaande definitie te updaten in plaats van een nieuwe toe te voegen",
                        }

            return {
                "voldoet": True,
                "toelichting": f"Geen duplicates gevonden ({len(existing)} bestaande definities gecontroleerd)",
            }

        except Exception as e:
            logger.error(f"Error during duplicate check: {e}")
            return {
                "voldoet": True,
                "toelichting": "Duplicate check mislukt (technische fout)",
            }

    def _normalize_text(self, text: str) -> str:
        """
        Normaliseer tekst voor vergelijking.

        - Lowercase
        - Verwijder extra whitespace
        - Verwijder interpunctie aan einde
        """
        if not text:
            return ""

        normalized = text.lower().strip()
        # Verwijder trailing punctuation
        while normalized and normalized[-1] in ".,;:!?":
            normalized = normalized[:-1].strip()
        # Collapse whitespace
        return " ".join(normalized.split())

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Bereken similarity tussen twee teksten.

        Simpele word-based Jaccard similarity.
        """
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 and not words2:
            return 1.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)
