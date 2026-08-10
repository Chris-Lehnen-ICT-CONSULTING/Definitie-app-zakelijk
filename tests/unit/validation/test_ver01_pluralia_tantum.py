"""DEF-605: VER-01 moet de volledige pluralia-tantum-lijst erkennen.

De live whitelist in ``_lemma_is_singular`` bevatte slechts 2 van de 104
woorden uit ``domain.linguistisch.pluralia_tantum``; 59 reële termen
(bescheiden, erven, inkomsten, onkosten, …) werden ten onrechte afgekeurd.
"""

import pytest

from domain.linguistisch.pluralia_tantum import PluraliatantumChecker
from services.validation.modular_validation_service import ModularValidationService
from toetsregels.manager import get_toetsregel_manager

pytestmark = [pytest.mark.unit]

ALLE_PLURALIA = sorted(PluraliatantumChecker.get_alle_woorden())

# Échte meervouden met een enkelvoud — VER-01 moet hier wél op aanslaan.
ECHTE_MEERVOUDEN = [
    "besluiten",
    "processen",
    "maatregelen",
    "gegevens",  # aandachtspunt 3 (DEF-605): bewust NIET whitelisten
    "scherven",  # eindigt op 'erven' — mag niet via suffix-matching slippen
    "germanen",  # eindigt op 'manen' — idem
]

# Samenstellingen met een productieve plurale-tantum-kop.
SAMENSTELLINGEN = [
    "verhuiskosten",
    "neveninkomsten",
    "aankoopkosten",  # staat ook letterlijk in de lijst
    "afvloeiingskosten",
]

# Golden subset: letterlijk genoteerd, onafhankelijk van de bronlijst.
# Detecteert verwijderingen uit PLURALIA_TANTUM_WOORDEN — de parametrisatie
# over get_alle_woorden() krimpt dan alleen maar mee en blijft groen.
GOLDEN_SUBSET = [
    "aanstalten",
    "bescheiden",
    "erven",
    "financiën",
    "hersenen",
    "inkomsten",
    "kleren",
    "kosten",
    "landerijen",
    "letteren",
    "lieden",
    "manschappen",
    "notulen",
    "onkosten",
    "Azoren",  # gekapitaliseerde geografische naam
]


@pytest.fixture(scope="module")
def svc() -> ModularValidationService:
    return ModularValidationService(get_toetsregel_manager(), None, None)


class TestLemmaIsSingular:
    @pytest.mark.parametrize("woord", ALLE_PLURALIA)
    def test_volledige_lijst_geldt_als_enkelvoud_acceptabel(self, svc, woord):
        assert svc._lemma_is_singular(
            woord
        ), f"'{woord}' staat in pluralia_tantum.py maar wordt afgekeurd"

    @pytest.mark.parametrize("woord", ECHTE_MEERVOUDEN)
    def test_echte_meervouden_blijven_afgekeurd(self, svc, woord):
        assert not svc._lemma_is_singular(woord)

    @pytest.mark.parametrize("woord", SAMENSTELLINGEN)
    def test_samenstellingen_met_plurale_tantum_kop(self, svc, woord):
        assert svc._lemma_is_singular(woord)

    def test_case_insensitief(self, svc):
        assert svc._lemma_is_singular("Bescheiden")
        assert svc._lemma_is_singular("INKOMSTEN")

    def test_leeg_begrip_passeert_lemma_check(self, svc):
        # Pre-existing gedrag, hier vastgelegd: leeg/None begrip wordt niet
        # als meervoud afgekeurd; lege input is aan andere regels (min_chars
        # e.d.), niet aan VER-01.
        assert svc._lemma_is_singular("")
        assert svc._lemma_is_singular(None)


class TestPluraliatantumChecker:
    def test_geografische_namen_case_insensitief(self):
        # Regressie: gekapitaliseerde entries matchten nooit doordat de
        # input werd gelowercased maar de set niet.
        assert PluraliatantumChecker.is_plurale_tantum("Azoren")
        assert PluraliatantumChecker.is_plurale_tantum("azoren")
        assert PluraliatantumChecker.is_geografische_naam("azoren")

    @pytest.mark.parametrize("woord", GOLDEN_SUBSET)
    def test_golden_subset_blijft_in_de_lijst(self, woord):
        assert PluraliatantumChecker.is_plurale_tantum(
            woord
        ), f"'{woord}' is uit PLURALIA_TANTUM_WOORDEN verdwenen"

    def test_lijst_omvang_ratchet(self):
        # Mag alleen groeien; detecteert stille verwijderingen.
        assert PluraliatantumChecker.tel_woorden() >= 104

    def test_koppen_guard_tegen_false_accepts(self):
        # Korte koppen matchen gewone meervouden (scherven→erven,
        # Germanen→manen). Elke kop moet >= 6 tekens zijn en zelf een
        # plurale tantum uit de lijst.
        for kop in PluraliatantumChecker.SAMENSTELLINGS_KOPPEN:
            assert len(kop) >= 6, f"kop '{kop}' is te kort — false-accept-risico"
            assert PluraliatantumChecker.is_plurale_tantum(kop)

    def test_samenstelling_alleen_op_productieve_koppen(self):
        assert PluraliatantumChecker.is_plurale_tantum_of_samenstelling("verhuiskosten")
        assert PluraliatantumChecker.is_plurale_tantum_of_samenstelling(
            "neveninkomsten"
        )
        # Geen generieke suffix-matching: dit zijn gewone meervouden.
        assert not PluraliatantumChecker.is_plurale_tantum_of_samenstelling("scherven")
        assert not PluraliatantumChecker.is_plurale_tantum_of_samenstelling("germanen")


class TestVer01EndToEnd:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("begrip", ["bescheiden", "inkomsten", "onkosten"])
    async def test_plurale_tantum_triggert_geen_lemma_violation(self, svc, begrip):
        # VER-01 heeft naast het lemma-pad ook een herkenbaar_patronen-pad
        # dat op de definitietekst matcht (en de begrippen zelf eindigen op
        # -en); daarom filteren we op de lemma-melding. De positieve
        # controle hieronder borgt dat die melding bestaat én dat het
        # lemma-pad daadwerkelijk draait.
        res = await svc.validate_definition(
            begrip=begrip,
            text=f"{begrip}: officieel stuk dat als bewijs dient",
            ontologische_categorie=None,
            context={},
        )
        lemma_violations = [
            v
            for v in res.get("violations", [])
            if v.get("code") == "VER-01"
            and "lijkt meervoud" in (v.get("message") or "")
        ]
        assert (
            not lemma_violations
        ), f"VER-01 keurt plurale tantum '{begrip}' nog steeds af als meervoud"

    @pytest.mark.asyncio
    async def test_positieve_controle_echt_meervoud_triggert_lemma_violation(self, svc):
        # Positieve controle: bewijst dat het lemma-pad draait en dat de
        # meldingstekst waarop de negatieve test filtert echt bestaat.
        # Zonder deze test zou de negatieve test vacuüm groen zijn zodra
        # VER-01 niet draait of de melding herformuleerd wordt.
        res = await svc.validate_definition(
            begrip="besluiten",
            text="besluiten: officieel stuk dat als bewijs dient",
            ontologische_categorie=None,
            context={},
        )
        lemma_violations = [
            v
            for v in res.get("violations", [])
            if v.get("code") == "VER-01"
            and "lijkt meervoud" in (v.get("message") or "")
        ]
        assert lemma_violations, (
            "VER-01-lemma-pad draait niet of de meldingstekst is gewijzigd — "
            "daarmee is de negatieve test hierboven betekenisloos"
        )
