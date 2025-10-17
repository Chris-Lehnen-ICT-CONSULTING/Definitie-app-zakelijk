"""
Toetsregel CON-01: Contextspecifieke formulering zonder expliciete benoeming

Deze toetsregel controleert of de definitie géén expliciete verwijzing bevat naar de opgegeven context(en).
Gemigreerd van legacy core.py
"""

import logging
import re
from typing import Any

try:
    from database.definitie_repository import DefinitieRepository
except Exception:  # pragma: no cover
    DefinitieRepository = None  # type: ignore

logger = logging.getLogger(__name__)


class CON01Validator:
    """Validator voor CON-01: Contextspecifieke formulering zonder expliciete benoeming."""

    def __init__(self, config: dict):
        """
        Initialiseer validator met configuratie uit JSON.

        Args:
            config: Dictionary met configuratie uit CON-01.json
        """
        self.config = config
        # Normaliseer naar weergave met koppelteken
        self.id = str(config.get("id", "CON-01")).replace("_", "-")
        self.naam = config.get(
            "naam", "Contextspecifieke formulering zonder expliciete benoeming"
        )
        self.uitleg = config.get("uitleg", "")
        self.herkenbaar_patronen = config.get("herkenbaar_patronen", [])
        self.goede_voorbeelden = config.get("goede_voorbeelden", [])
        self.foute_voorbeelden = config.get("foute_voorbeelden", [])
        self.prioriteit = config.get("prioriteit", "hoog")

        # Compile regex patronen voor performance
        self.compiled_patterns = []
        for pattern in self.herkenbaar_patronen:
            try:
                self.compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Ongeldig regex patroon in {self.id}: {pattern} - {e}")

    def _extract_context_dict(self, context: dict | None) -> dict[str, Any]:
        """Extract en normaliseer context dictionary."""
        contexten: dict[str, Any] = {}
        if context:
            if isinstance(context.get("contexten"), dict):
                contexten = context.get("contexten") or {}
            else:
                contexten = {
                    "organisatorische_context": context.get("organisatorische_context")
                    or [],
                    "juridische_context": context.get("juridische_context") or [],
                    "wettelijke_basis": context.get("wettelijke_basis") or [],
                }
        return contexten

    def _check_duplicate_context(
        self, begrip: str, contexten: dict[str, Any]
    ) -> tuple[bool, str] | None:
        """
        Controleer of er duplicaten bestaan met dezelfde context.

        Returns None als check niet nodig of OK, anders (False, melding).
        """
        if not (DefinitieRepository and begrip):
            return None

        try:
            repo = DefinitieRepository()

            def _as_str_one(val: Any) -> str:
                if isinstance(val, list):
                    return str(val[0]) if val else ""
                return str(val or "")

            org = _as_str_one(contexten.get("organisatorische_context", []))
            jur = _as_str_one(contexten.get("juridische_context", []))
            wet = contexten.get("wettelijke_basis", [])
            wet_list = wet if isinstance(wet, list) else []

            if org or jur or wet_list:
                cnt = repo.count_exact_by_context(
                    begrip=begrip,
                    organisatorische_context=org,
                    juridische_context=jur,
                    wettelijke_basis=wet_list,
                )
                if cnt > 1:
                    return (
                        False,
                        f"❌ {self.id}: er bestaan meerdere definities voor dit begrip met dezelfde context (aantal: {cnt}). Consolidatie of hergebruik aanbevolen.",
                    )
        except Exception:  # Soft-fail
            pass
        return None

    def _check_explicit_context_terms(
        self, definitie_lc: str, contexten: dict[str, Any]
    ) -> tuple[bool, str] | None:
        """
        Controleer of user-gegeven context letterlijk in definitie voorkomt.

        Returns None als OK, anders (False, melding).
        """
        expliciete_hits = []
        for _label, waardelijst in contexten.items():
            if not waardelijst:
                continue
            for context_value in waardelijst:
                term = context_value.lower().strip()
                # Check varianten van context woorden
                varianten = {term, term + "e", term + "en", term.rstrip("e")}
                for var in varianten:
                    if var and var in definitie_lc:
                        expliciete_hits.append(var)

        if expliciete_hits:
            gevonden = ", ".join(sorted(set(expliciete_hits)))
            return (
                False,
                f"❌ {self.id}: opgegeven context letterlijk in definitie herkend ('{gevonden}')",
            )
        return None

    def _find_broad_context_terms(self, definitie: str) -> set[str]:
        """Zoek bredere contexttermen via regex patronen."""
        contextuele_term_hits = set()
        for pattern in self.compiled_patterns:
            matches = pattern.findall(definitie)
            # Filter false positives: "om" en "zm" alleen als hoofdletters
            for match in matches:
                match_lower = match.lower()
                # Skip "om" en "zm" tenzij ze in hoofdletters staan in de originele definitie
                if match_lower in ("om", "zm"):
                    if match.upper() == match:  # Alleen als hoofdletters
                        contextuele_term_hits.add(match_lower)
                else:
                    contextuele_term_hits.add(match_lower)
        return contextuele_term_hits

    def _evaluate_results(
        self,
        contextuele_term_hits: set[str],
        definitie_lc: str,
    ) -> tuple[bool, str, float]:
        """Evalueer gevonden patronen en voorbeelden om validatie resultaat te bepalen."""
        goede_match = any(vb.lower() in definitie_lc for vb in self.goede_voorbeelden)
        foute_match = any(vb.lower() in definitie_lc for vb in self.foute_voorbeelden)

        if contextuele_term_hits and foute_match:
            return (
                False,
                f"❌ {self.id}: bredere contexttermen herkend ({', '.join(sorted(contextuele_term_hits))}), en lijkt op fout voorbeeld",
                0.0,
            )
        if contextuele_term_hits:
            return (
                False,
                f"🟡 {self.id}: bredere contexttaal herkend ({', '.join(sorted(contextuele_term_hits))}), formulering mogelijk vaag",
                0.5,
            )
        if foute_match:
            return False, f"❌ {self.id}: definitie bevat expliciet fout voorbeeld", 0.0
        if goede_match:
            return True, f"✔️ {self.id}: definitie komt overeen met goed voorbeeld", 1.0

        # Fallback - niets herkend
        return True, f"✔️ {self.id}: geen expliciete contextverwijzing aangetroffen", 0.9

    def validate(
        self, definitie: str, begrip: str, context: dict | None = None
    ) -> tuple[bool, str, float]:
        """
        Valideer definitie volgens CON-01 regel.

        Deze regel controleert of de definitie geen expliciete verwijzing bevat
        naar de opgegeven context(en). De context moet impliciet doorklinken
        zonder letterlijke benoeming.

        Args:
            definitie: De te valideren definitie
            begrip: Het begrip dat gedefinieerd wordt
            context: Optionele context informatie

        Returns:
            Tuple van (succes, melding, score)
        """
        definitie_lc = definitie.lower()
        # Ondersteun zowel legacy 'contexten' als V2 velden op top-niveau
        contexten = self._extract_context_dict(context)

        # 0️⃣ Check: er mag niet meer dan 1 definitie bestaan met exact zelfde begrip + context
        duplicate_check = self._check_duplicate_context(begrip, contexten)
        if duplicate_check:
            return (duplicate_check[0], duplicate_check[1], 0.0)

        # 1️⃣ Dynamisch: user-gegeven contexten
        explicit_check = self._check_explicit_context_terms(definitie_lc, contexten)
        if explicit_check:
            return (explicit_check[0], explicit_check[1], 0.0)

        # 2️⃣ Herken bredere contexttermen via patronen
        contextuele_term_hits = self._find_broad_context_terms(definitie)

        # 3️⃣ & 4️⃣ Vergelijk met voorbeelden en evalueer
        return self._evaluate_results(contextuele_term_hits, definitie_lc)

    def get_generation_hints(self) -> list[str]:
        """
        Geef hints voor definitie generatie.

        Returns:
            Lijst met instructies voor de AI generator
        """
        hints = []

        hints.append(
            "Formuleer de definitie contextneutraal zonder expliciete verwijzingen"
        )
        hints.append(
            "Vermijd termen zoals: 'binnen de context van', 'juridisch', 'beleidsmatig'"
        )
        hints.append("Vermijd organisatienamen zoals: DJI, OM, KMAR")
        hints.append("Laat de context impliciet doorklinken in de formulering")

        if self.goede_voorbeelden:
            hints.append(f"Goed voorbeeld: {self.goede_voorbeelden[0]}")

        return hints


def create_validator(config_path: str | None = None) -> CON01Validator:
    """
    Factory functie om validator te maken.

    Args:
        config_path: Optioneel pad naar configuratie bestand

    Returns:
        CON01Validator instantie
    """
    import json
    import os

    # Gebruik default config path als niet opgegeven; val terug naar 'regels/' indien nodig
    if not config_path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        primary = os.path.join(current_dir, "CON-01.json")
        if os.path.exists(primary):
            config_path = primary
        else:
            # Fallback naar ../regels/CON-01.json (canonieke locatie)
            parent = os.path.dirname(current_dir)
            rules_path = os.path.join(parent, "regels", "CON-01.json")
            config_path = rules_path

    # Laad configuratie
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    return CON01Validator(config)
