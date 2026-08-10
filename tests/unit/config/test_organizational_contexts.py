"""DEF-603: regressietest organisatiekeuze.

US-442 (okt 2025) verwijderde onbedoeld IND, NFI en de Raad voor de
Kinderbescherming uit de organisatiekeuze: de vervangende selector leest
`ui_cfg.organizational_contexts` en die lijst miste de drie organisaties
uit het (verweesde) `context_options.ORGANIZATIONS`.
"""

from pathlib import Path

import pytest
import yaml

from config.config_manager import ConfigManager, UIConfig

pytestmark = [pytest.mark.unit]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_YAML = PROJECT_ROOT / "config" / "config.yaml"

# De drie organisaties die in US-442 uit de keuzelijst verdwenen.
HERSTELDE_ORGANISATIES = ["IND", "NFI", "Raad voor de Kinderbescherming"]

# De volledige verwachte keuzelijst (16 opties, DEF-603-acceptatie).
# Expliciete constante: een vergelijking tussen twee bronnen onderling kan
# niet zien dat er in béíde iets verdwijnt — precies wat US-442 deed.
# Volgorde is betekenisvol (dropdown-volgorde) en dus onderdeel van de eis.
VERWACHTE_ORGANISATIES = [
    "OM",
    "ZM",
    "Reclassering",
    "DJI",
    "NP",
    "Justid",
    "KMAR",
    "FIOD",
    "CJIB",
    "IND",
    "NFI",
    "Raad voor de Kinderbescherming",
    "Strafrechtketen",
    "Migratieketen",
    "Justitie en Veiligheid",
    "Anders...",
]


@pytest.fixture(scope="module")
def yaml_lijst() -> list[str]:
    assert CONFIG_YAML.exists(), (
        f"config.yaml niet gevonden op {CONFIG_YAML} — is dit testbestand "
        "verplaatst? PROJECT_ROOT rekent met parents[3] vanaf tests/unit/config/."
    )
    data = yaml.safe_load(CONFIG_YAML.read_text(encoding="utf-8"))
    return data["ui"]["organizational_contexts"]


class TestOrganisatiekeuze:
    @pytest.mark.parametrize("organisatie", HERSTELDE_ORGANISATIES)
    def test_dataclass_default_bevat_herstelde_organisaties(self, organisatie):
        assert organisatie in UIConfig().organizational_contexts

    @pytest.mark.parametrize("organisatie", HERSTELDE_ORGANISATIES)
    def test_yaml_overlay_bevat_herstelde_organisaties(self, organisatie, yaml_lijst):
        # De config.yaml-overlay wint van de dataclass-default; de fix moet
        # dus op beide plekken staan.
        assert organisatie in yaml_lijst

    def test_dataclass_default_is_de_volledige_lijst(self):
        assert UIConfig().organizational_contexts == VERWACHTE_ORGANISATIES

    def test_yaml_overlay_is_de_volledige_lijst(self, yaml_lijst):
        assert yaml_lijst == VERWACHTE_ORGANISATIES

    def test_yaml_en_dataclass_default_zijn_identiek(self, yaml_lijst):
        # Bewuste projectinvariant, geen momentopname: dit project spiegelt
        # config.yaml en de dataclass-defaults; drift tussen die twee was
        # het mechanisme waardoor deze regressie kon ontstaan.
        assert yaml_lijst == UIConfig().organizational_contexts

    def test_via_de_echte_configlaadweg(self):
        # De UI leest via ConfigManager (yaml → _apply_config_dict → .ui),
        # niet via UIConfig() of de rauwe yaml. Deze test faalt als de
        # ui-sectie niet meer op UIConfig gemapt wordt — de rauwe-yaml-tests
        # hierboven blijven dan ten onrechte groen.
        assert ConfigManager().ui.organizational_contexts == VERWACHTE_ORGANISATIES

    def test_anders_blijft_laatste_optie(self):
        assert UIConfig().organizational_contexts[-1] == "Anders..."
