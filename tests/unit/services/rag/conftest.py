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
