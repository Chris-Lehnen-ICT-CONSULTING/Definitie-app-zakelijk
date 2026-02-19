"""Tests voor LegalStructureRecognizer."""

import pytest

from services.rag.legal_structure_recognizer import (
    LegalStructureRecognizer,
)


@pytest.fixture
def recognizer():
    return LegalStructureRecognizer()


class TestIsJuridischDocument:
    def test_wettekst_met_artikelen(self, recognizer, sample_wettekst):
        assert recognizer.is_juridisch_document(sample_wettekst) is True

    def test_generieke_tekst(self, recognizer, sample_generieke_tekst):
        assert recognizer.is_juridisch_document(sample_generieke_tekst) is False

    def test_lege_tekst(self, recognizer):
        assert recognizer.is_juridisch_document("") is False
        assert recognizer.is_juridisch_document("   ") is False

    def test_enkel_artikel(self, recognizer):
        tekst = "Artikel 1\nEnige bepaling."
        assert recognizer.is_juridisch_document(tekst) is False

    def test_twee_artikelen(self, recognizer):
        tekst = "Artikel 1\nEerste.\n\nArtikel 2\nTweede."
        assert recognizer.is_juridisch_document(tekst) is True

    def test_art_afkorting(self, recognizer):
        tekst = "Art. 1\nEerste.\n\nArt. 2\nTweede."
        assert recognizer.is_juridisch_document(tekst) is True

    def test_lowercase_artikel_ocr(self, recognizer):
        """OCR-output kan lowercase 'artikel' opleveren."""
        tekst = "artikel 1\nEerste.\n\nartikel 2\nTweede."
        assert recognizer.is_juridisch_document(tekst) is True

    def test_bw_notatie(self, recognizer):
        """Burgerlijk Wetboek: Artikel 10:1, Artikel 7:2."""
        tekst = "Artikel 10:1\nEerste.\n\nArtikel 10:2\nTweede."
        assert recognizer.is_juridisch_document(tekst) is True


class TestDetecteerStructuur:
    def test_detecteert_hoofdstukken(self, recognizer, sample_wettekst):
        elementen = recognizer.detecteer_structuur(sample_wettekst)
        hoofdstukken = [e for e in elementen if e.type == "hoofdstuk"]
        assert len(hoofdstukken) == 2
        assert hoofdstukken[0].nummer == "1"
        assert hoofdstukken[1].nummer == "2"

    def test_detecteert_artikelen(self, recognizer, sample_wettekst):
        elementen = recognizer.detecteer_structuur(sample_wettekst)
        artikelen = [e for e in elementen if e.type in ("artikel", "definitieblok")]
        assert len(artikelen) == 5

    def test_detecteert_bijlage(self, recognizer, sample_wettekst):
        elementen = recognizer.detecteer_structuur(sample_wettekst)
        bijlagen = [e for e in elementen if e.type == "bijlage"]
        assert len(bijlagen) == 1
        assert bijlagen[0].nummer == "I"

    def test_elementen_gesorteerd(self, recognizer, sample_wettekst):
        elementen = recognizer.detecteer_structuur(sample_wettekst)
        posities = [e.start for e in elementen]
        assert posities == sorted(posities)

    def test_elementen_hebben_tekst(self, recognizer, sample_wettekst):
        elementen = recognizer.detecteer_structuur(sample_wettekst)
        for elem in elementen:
            assert len(elem.tekst) > 0

    def test_lege_tekst(self, recognizer):
        assert recognizer.detecteer_structuur("") == []

    def test_bw_artikel_nummer_correct(self, recognizer):
        """BW-notatie moet volledig nummer vastleggen (10:1, niet 10)."""
        tekst = "Artikel 10:1\nEerste bepaling.\n\nArtikel 10:2\nTweede bepaling.\n"
        elementen = recognizer.detecteer_structuur(tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 2
        assert artikelen[0].nummer == "10:1"
        assert artikelen[1].nummer == "10:2"

    def test_detecteert_boek(self, recognizer):
        tekst = "Boek 7\n\nArtikel 1\nEerste.\n\nArtikel 2\nTweede.\n"
        elementen = recognizer.detecteer_structuur(tekst)
        boeken = [e for e in elementen if e.type == "boek"]
        assert len(boeken) == 1
        assert boeken[0].nummer == "7"

    def test_detecteert_titel(self, recognizer):
        tekst = "TITEL I\n\nArtikel 1\nEerste.\n\nArtikel 2\nTweede.\n"
        elementen = recognizer.detecteer_structuur(tekst)
        titels = [e for e in elementen if e.type == "titel"]
        assert len(titels) == 1
        assert titels[0].nummer == "I"


class TestDetecteerLeden:
    def test_artikel_met_leden(self, recognizer):
        tekst = (
            "Artikel 2\n"
            "1. Er is een basisregistratie personen.\n"
            "2. De basisregistratie heeft tot doel de overheid te voorzien.\n"
            "3. De basisregistratie bevat persoonsgegevens.\n"
        )
        leden = recognizer.detecteer_leden(tekst)
        assert len(leden) == 3
        assert leden[0].nummer == "1"
        assert leden[2].nummer == "3"

    def test_artikel_zonder_leden(self, recognizer):
        tekst = "Het college is verantwoordelijk voor het bijhouden van gegevens."
        leden = recognizer.detecteer_leden(tekst)
        assert len(leden) == 0

    def test_leden_hebben_tekst(self, recognizer):
        tekst = "1. Eerste lid tekst.\n2. Tweede lid tekst.\n"
        leden = recognizer.detecteer_leden(tekst)
        assert len(leden) == 2
        assert "Eerste lid" in leden[0].tekst
        assert "Tweede lid" in leden[1].tekst


class TestDetecteerWetNaam:
    def test_wet_op_de(self, recognizer):
        tekst = (
            "Wet op de gemeentelijke basisadministratie persoonsgegevens\n\nArtikel 1\n"
        )
        naam = recognizer.detecteer_wet_naam(tekst)
        assert naam is not None
        assert "gemeentelijke" in naam

    def test_wetboek_van(self, recognizer):
        tekst = "Wetboek van Strafrecht\n\nArtikel 1\n"
        naam = recognizer.detecteer_wet_naam(tekst)
        assert naam is not None
        assert "Strafrecht" in naam

    def test_besluit(self, recognizer):
        tekst = "Besluit aanwijzing registraties\n\nArtikel 1\n"
        naam = recognizer.detecteer_wet_naam(tekst)
        assert naam is not None
        assert "Besluit" in naam

    def test_geen_wet_naam(self, recognizer):
        tekst = "Dit is een willekeurige tekst zonder wetnaam."
        naam = recognizer.detecteer_wet_naam(tekst)
        assert naam is None

    def test_wet_naam_na_500_tekens(self, recognizer):
        """DEF-361: Wet-naam voorbij 500 tekens (bijv. PDF metadata) moet gevonden worden."""
        padding = "x" * 800 + "\n"
        tekst = padding + "Wetboek van Strafvordering\n\nArtikel 1\n"
        naam = recognizer.detecteer_wet_naam(tekst)
        assert naam is not None
        assert "Strafvordering" in naam

    def test_wet_naam_net_buiten_2000_tekens(self, recognizer):
        """Wet-naam voorbij 2000 tekens wordt niet gevonden (bedoeld gedrag)."""
        padding = "x" * 2100 + "\n"
        tekst = padding + "Wetboek van Strafrecht\n\nArtikel 1\n"
        naam = recognizer.detecteer_wet_naam(tekst)
        assert naam is None


class TestPaginaGrenzen:
    def test_pdf_pagina_nummers(self, recognizer, sample_pdf_tekst):
        elementen = recognizer.detecteer_structuur(sample_pdf_tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 3
        assert artikelen[0].pagina_nummer == 1
        assert artikelen[1].pagina_nummer == 2
        assert artikelen[2].pagina_nummer == 3

    def test_geen_pagina_grenzen(self, recognizer):
        tekst = "Artikel 1\nTekst.\n\nArtikel 2\nTekst.\n"
        elementen = recognizer.detecteer_structuur(tekst)
        for elem in elementen:
            assert elem.pagina_nummer is None


class TestFormfeedNormalisatie:
    """DEF-356: Formfeed-only tekst moet correct verwerkt worden."""

    def test_formfeed_only_is_juridisch(self, recognizer, sample_formfeed_only_tekst):
        """Tekst met alleen formfeeds (geen newlines) moet als juridisch herkend worden."""
        assert recognizer.is_juridisch_document(sample_formfeed_only_tekst) is True

    def test_formfeed_only_detecteert_artikelen(
        self, recognizer, sample_formfeed_only_tekst
    ):
        """Artikelen gescheiden door formfeeds moeten gedetecteerd worden."""
        elementen = recognizer.detecteer_structuur(sample_formfeed_only_tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 3

    def test_formfeed_pagina_nummers(self, recognizer, sample_formfeed_only_tekst):
        """Formfeed-gescheiden artikelen krijgen correcte paginanummers."""
        elementen = recognizer.detecteer_structuur(sample_formfeed_only_tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert artikelen[0].pagina_nummer == 1
        assert artikelen[1].pagina_nummer == 2
        assert artikelen[2].pagina_nummer == 3

    def test_gemixte_formfeed_newline(self, recognizer):
        """Mix van formfeeds en newlines werkt correct."""
        tekst = "Artikel 1\nEerste.\f\nArtikel 2\nTweede.\n\fArtikel 3\nDerde.\n"
        assert recognizer.is_juridisch_document(tekst) is True
        elementen = recognizer.detecteer_structuur(tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 3


class TestSamengesteldeArtikelnummers:
    """DEF-362: Punt-notatie (5.3.2) moet correct herkend worden."""

    def test_punt_notatie_herkend(self, recognizer):
        """Artikel 5.3.2 moet als '5.3.2' herkend worden, niet als '5'."""
        tekst = (
            "Artikel 5.3.2 De verdachte heeft recht op bijstand.\n\n"
            "Artikel 5.3.7 De raadsman kan inzage vorderen.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 2
        assert artikelen[0].nummer == "5.3.2"
        assert artikelen[1].nummer == "5.3.7"

    def test_diepe_punt_notatie(self, recognizer):
        """Diepere nesting (5.3.21) wordt volledig gevangen."""
        tekst = "Artikel 5.3.21 Bijzondere bepaling.\n\nArtikel 6 Normale bepaling.\n"
        elementen = recognizer.detecteer_structuur(tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert artikelen[0].nummer == "5.3.21"
        assert artikelen[1].nummer == "6"

    def test_bestaande_formaten_blijven_werken(self, recognizer):
        """BW dubbelpunt, letter-suffix, en simpele nummers werken nog."""
        tekst = (
            "Artikel 10:1 BW bepaling.\n\n"
            "Artikel 5a Aparte bepaling.\n\n"
            "Artikel 3 Gewone bepaling.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 3
        assert artikelen[0].nummer == "10:1"
        assert artikelen[1].nummer == "5a"
        assert artikelen[2].nummer == "3"

    def test_is_juridisch_met_punt_notatie(self, recognizer):
        """Document met punt-notatie artikelen is juridisch."""
        tekst = "Artikel 5.3.2 Eerste bepaling.\n\nArtikel 5.3.7 Tweede bepaling.\n"
        assert recognizer.is_juridisch_document(tekst) is True


class TestArtikelRegexZonderDollarAnchor:
    """DEF-356: Artikel regex moet ook matchen als er tekst na het nummer staat."""

    def test_artikel_met_tekst_erna(self, recognizer):
        """'Artikel 1 Strafvordering heeft...' moet matchen."""
        tekst = (
            "Artikel 1 Strafvordering heeft betrekking op strafbare feiten.\n\n"
            "Artikel 2 De officier van justitie is belast met de vervolging.\n"
        )
        assert recognizer.is_juridisch_document(tekst) is True

    def test_artikel_nummering_correct_met_tekst_erna(self, recognizer):
        """Artikelnummer moet correct geëxtraheerd worden ondanks trailing tekst."""
        tekst = (
            "Artikel 1 Strafvordering betreft.\n\n"
            "Artikel 2 De vervolging geschiedt.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        artikelen = [e for e in elementen if e.type == "artikel"]
        assert len(artikelen) == 2
        assert artikelen[0].nummer == "1"
        assert artikelen[1].nummer == "2"


class TestLetterLeden:
    """DEF-356: Letter-leden (a., b., c.) herkenning."""

    def test_letter_leden_gedetecteerd(
        self, recognizer, sample_artikel_met_letter_leden
    ):
        """Letter-leden worden herkend door detecteer_leden()."""
        leden = recognizer.detecteer_leden(
            sample_artikel_met_letter_leden, include_letter_leden=True
        )
        nummers = [lid.nummer for lid in leden]
        assert "a" in nummers
        assert "b" in nummers
        assert "c" in nummers
        assert "1" in nummers

    def test_letter_leden_exclusief(self, recognizer, sample_artikel_met_letter_leden):
        """Met include_letter_leden=False worden alleen numerieke leden gedetecteerd."""
        leden = recognizer.detecteer_leden(
            sample_artikel_met_letter_leden, include_letter_leden=False
        )
        nummers = [lid.nummer for lid in leden]
        assert "a" not in nummers
        assert "1" in nummers
        assert "2" in nummers
        assert "3" in nummers


class TestDefinitieblokDetectie:
    def test_definitieblok_herkend(self, recognizer, sample_definitieblok):
        tekst = sample_definitieblok + "\nArtikel 2\nAndere bepaling."
        elementen = recognizer.detecteer_structuur(tekst)
        defblokken = [e for e in elementen if e.type == "definitieblok"]
        assert len(defblokken) == 1

    def test_normaal_artikel_niet_als_definitieblok(self, recognizer):
        tekst = (
            "Artikel 1\n"
            "Het college is verantwoordelijk.\n\n"
            "Artikel 2\n"
            "De ingezetene doet aangifte.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        defblokken = [e for e in elementen if e.type == "definitieblok"]
        assert len(defblokken) == 0

    def test_opening_zonder_opsomming_geen_definitieblok(self, recognizer):
        """Opening phrase maar geen lettered items = geen definitieblok."""
        tekst = (
            "Artikel 1\n"
            "In deze wet wordt verstaan onder basisregistratie "
            "de registratie als bedoeld in de wet.\n\n"
            "Artikel 2\n"
            "Andere bepaling.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        defblokken = [e for e in elementen if e.type == "definitieblok"]
        assert len(defblokken) == 0

    def test_voor_de_toepassing_variant(self, recognizer):
        tekst = (
            "Artikel 1\n"
            "Voor de toepassing van deze regeling wordt verstaan onder:\n"
            "a. begrip: uitleg;\n"
            "b. ander begrip: andere uitleg.\n\n"
            "Artikel 2\n"
            "Bepaling.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        defblokken = [e for e in elementen if e.type == "definitieblok"]
        assert len(defblokken) == 1

    def test_genummerde_opsomming_avg_stijl(self, recognizer):
        """AVG/GDPR-stijl: genummerde definities 1), 2), 3)."""
        tekst = (
            "Artikel 1\n"
            "In deze verordening wordt verstaan onder:\n"
            "1) persoonsgegevens: alle informatie over een geidentificeerde persoon;\n"
            "2) verwerking: een bewerking of geheel van bewerkingen;\n"
            "3) verwerkingsverantwoordelijke: de persoon die het doel bepaalt.\n\n"
            "Artikel 2\n"
            "Bepaling.\n"
        )
        elementen = recognizer.detecteer_structuur(tekst)
        defblokken = [e for e in elementen if e.type == "definitieblok"]
        assert len(defblokken) == 1
