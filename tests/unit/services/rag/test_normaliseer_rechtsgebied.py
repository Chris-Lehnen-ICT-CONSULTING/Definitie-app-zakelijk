"""Tests voor rechtsgebied normalisatie (DEF-371)."""

import pytest

from services.rag.constants import RECHTSGEBIEDEN, normaliseer_rechtsgebied


class TestNormaliseerRechtsgebied:
    """Tests voor de normaliseer_rechtsgebied() functie."""

    @pytest.mark.parametrize(
        ("invoer", "verwacht"),
        [
            # Exacte key
            ("strafrecht", "strafrecht"),
            ("bestuursrecht", "bestuursrecht"),
            ("burgerlijk_recht", "burgerlijk_recht"),
            # Titlecase label
            ("Strafrecht", "strafrecht"),
            ("Bestuursrecht", "bestuursrecht"),
            ("Burgerlijk recht", "burgerlijk_recht"),
            ("Europees recht", "europees_recht"),
            # Case-insensitive
            ("STRAFRECHT", "strafrecht"),
            ("BESTUURSRECHT", "bestuursrecht"),
            # Aliassen (diverse casings)
            ("civiel recht", "burgerlijk_recht"),
            ("Civiel recht", "burgerlijk_recht"),
            ("CIVIEL RECHT", "burgerlijk_recht"),
            ("civiel_recht", "burgerlijk_recht"),
            ("privaatrecht", "burgerlijk_recht"),
            ("PRIVAATRECHT", "burgerlijk_recht"),
            # Whitespace trimming
            ("  strafrecht  ", "strafrecht"),
            (" Bestuursrecht ", "bestuursrecht"),
        ],
    )
    def test_bekende_waarden(self, invoer: str, verwacht: str):
        assert normaliseer_rechtsgebied(invoer) == verwacht

    @pytest.mark.parametrize(
        "invoer",
        [
            "onbekend",
            "criminal law",
            "straf-recht",
            "xyz",
        ],
    )
    def test_onbekende_waarden_geven_none(self, invoer: str):
        assert normaliseer_rechtsgebied(invoer) is None

    @pytest.mark.parametrize("invoer", ["", "  "])
    def test_lege_invoer_geeft_none(self, invoer: str):
        assert normaliseer_rechtsgebied(invoer) is None

    def test_none_invoer_geeft_none(self):
        """None wordt geaccepteerd en geeft None terug (type: str | None)."""
        assert normaliseer_rechtsgebied(None) is None

    def test_alle_keys_normaliseren_naar_zichzelf(self):
        """Elke key in RECHTSGEBIEDEN moet naar zichzelf normaliseren."""
        for key in RECHTSGEBIEDEN:
            assert normaliseer_rechtsgebied(key) == key

    def test_alle_labels_normaliseren_naar_key(self):
        """Elk label in RECHTSGEBIEDEN moet naar de bijbehorende key normaliseren."""
        for key, label in RECHTSGEBIEDEN.items():
            assert normaliseer_rechtsgebied(label) == key
