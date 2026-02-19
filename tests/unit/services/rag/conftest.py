"""Shared fixtures en sample wetteksten voor RAG chunking tests."""

import pytest


@pytest.fixture
def sample_wettekst() -> str:
    """Realistische Nederlandse wettekst met meerdere artikelen en leden."""
    return (
        "Wet op de gemeentelijke basisadministratie persoonsgegevens\n\n"
        "HOOFDSTUK 1. ALGEMENE BEPALINGEN\n\n"
        "Artikel 1\n"
        "In deze wet wordt verstaan onder:\n"
        "a. basisregistratie: een registratie als bedoeld in artikel 2;\n"
        "b. ingezetene: degene die zijn adres heeft in een gemeente;\n"
        "c. niet-ingezetene: degene die zijn adres heeft buiten Nederland;\n"
        "d. persoonsgegeven: elk gegeven betreffende een geidentificeerde of "
        "identificeerbare natuurlijke persoon;\n"
        "e. college: het college van burgemeester en wethouders;\n"
        "f. minister: Onze Minister van Binnenlandse Zaken.\n\n"
        "Artikel 2\n"
        "1. Er is een basisregistratie personen.\n"
        "2. De basisregistratie personen heeft tot doel de overheid te voorzien "
        "van betrouwbare persoonsgegevens.\n"
        "3. De basisregistratie personen bevat persoonsgegevens over ingezetenen "
        "en niet-ingezetenen.\n\n"
        "Artikel 3\n"
        "Het college van de gemeente is verantwoordelijk voor het bijhouden van "
        "persoonsgegevens over de ingezetenen van die gemeente.\n\n"
        "HOOFDSTUK 2. INSCHRIJVING EN ADRES\n\n"
        "Artikel 4\n"
        "1. Iedere ingezetene wordt ingeschreven in de basisregistratie.\n"
        "2. De inschrijving geschiedt in de gemeente waar de ingezetene zijn "
        "adres heeft.\n"
        "3. Bij algemene maatregel van bestuur kunnen regels worden gesteld over "
        "de wijze van inschrijving.\n\n"
        "Artikel 5\n"
        "1. De ingezetene die zijn adres wijzigt doet hiervan aangifte bij het "
        "college van de gemeente waar hij zijn nieuwe adres heeft.\n"
        "2. De aangifte wordt gedaan binnen vier weken na de adreswijziging.\n\n"
        "Bijlage I\n"
        "Overzicht van de categorieën persoonsgegevens die worden opgenomen "
        "in de basisregistratie personen.\n"
    )


@pytest.fixture
def sample_generieke_tekst() -> str:
    """Niet-juridische tekst voor generieke chunking tests."""
    return (
        "# Handleiding Definitie-app\n\n"
        "## Installatie\n\n"
        "De Definitie-app kan worden geïnstalleerd via pip. Zorg ervoor dat "
        "Python 3.11 of hoger is geïnstalleerd op uw systeem. De applicatie "
        "maakt gebruik van Streamlit als web framework.\n\n"
        "## Configuratie\n\n"
        "Na installatie dient u een configuratiebestand aan te maken. "
        "Dit bestand bevat de API keys voor OpenAI en de database locatie. "
        "Kopieer het voorbeeld configuratiebestand en pas het aan.\n\n"
        "## Gebruik\n\n"
        "Start de applicatie met het commando `streamlit run src/main.py`. "
        "De applicatie opent automatisch in uw webbrowser. U kunt nu "
        "definities genereren door een begrip in te voeren.\n"
    )


@pytest.fixture
def sample_definitieblok() -> str:
    """Wettekst met een definitieblok dat intact moet blijven."""
    return (
        "Artikel 1\n"
        "In deze wet wordt verstaan onder:\n"
        "a. basisregistratie: een registratie als bedoeld in artikel 2;\n"
        "b. ingezetene: degene die zijn adres heeft in een gemeente;\n"
        "c. niet-ingezetene: degene die zijn adres heeft buiten Nederland;\n"
        "d. persoonsgegeven: elk gegeven betreffende een geidentificeerde of "
        "identificeerbare natuurlijke persoon;\n"
        "e. college: het college van burgemeester en wethouders;\n"
        "f. minister: Onze Minister van Binnenlandse Zaken.\n"
    )


@pytest.fixture
def sample_pdf_tekst() -> str:
    """Tekst met form-feed pagina-scheiders (typisch voor PDF extractie)."""
    return (
        "Artikel 1\nEerste artikel tekst.\n"
        "\f"
        "Artikel 2\nTweede artikel tekst.\n"
        "\f"
        "Artikel 3\nDerde artikel tekst.\n"
    )


@pytest.fixture
def sample_formfeed_only_tekst() -> str:
    """PDF-tekst met ALLEEN formfeeds, GEEN newlines (Wetboek v. Strafvordering scenario)."""
    return (
        "Artikel 1 De verdachte heeft recht op bijstand."
        "\f"
        "Artikel 2 De rechter beslist over de voorlopige hechtenis."
        "\f"
        "Artikel 3 Het openbaar ministerie is belast met de opsporing."
    )


@pytest.fixture
def sample_artikel_met_letter_leden() -> str:
    """Artikel met zowel numerieke als letter-leden."""
    return (
        "Artikel 1\n"
        "1. In deze wet wordt verstaan onder:\n"
        "a. basisregistratie: een registratie;\n"
        "b. ingezetene: een persoon;\n"
        "c. college: het bestuur.\n"
        "2. De minister kan nadere regels stellen.\n"
        "3. Dit artikel is niet van toepassing op bijzondere gevallen.\n"
    )


@pytest.fixture
def sample_groot_generiek_document() -> str:
    """Groot generiek document dat paragraaf-split nodig heeft."""
    sectie = "Dit is een lange paragraaf met veel tekst. " * 50  # ~500 tokens
    return (
        "# Groot Document\n\n"
        f"## Sectie 1\n\n{sectie}\n\n"
        f"Een tweede paragraaf met andere inhoud. {sectie}\n\n"
        f"## Sectie 2\n\n{sectie}\n"
    )
