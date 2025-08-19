"""
Nederlandse Pluralia Tantum - woorden die alleen in meervoud bestaan.

Geëxtraheerd uit legacy lookup.py om Nederlandse taalkundige
kennis te bewaren voor correcte grammatica validatie.
"""


class PluraliatantumChecker:
    """
    Nederlandse pluralia tantum validatie.

    Pluralia tantum zijn woorden die alleen in meervoudsvorm bestaan
    in het Nederlands. Deze moeten niet als "grammaticaal incorrect"
    gemarkeerd worden in tekst validatie.
    """

    # Volledige Nederlandse pluralia tantum set (104 woorden)
    # Geëxtraheerd uit nl_pluralia_tantum_100.json
    PLURALIA_TANTUM_WOORDEN = {
        # Basis Nederlandse pluralia tantum
        "aanstalten",
        "alcoholica",
        "amoretten",
        "annalen",
        "auspiciën",
        "avances",
        "bescheiden",
        "besognes",
        "capriolen",
        "chemicaliën",
        "conserven",
        "consorten",
        "contreien",
        "coulissen",
        "data",
        "diggelen",
        "erven",
        "exequiën",
        "exuviën",
        "fecaliën",
        "fikken",
        "financiën",
        "fratsen",
        "gebroeders",
        "genitaliën",
        "gezusters",
        "hersenen",
        "hurken",
        "infusoriën",
        "inkomsten",
        "jatten",
        "kladden",
        "kleren",
        "kosten",
        "landerijen",
        "lauweren",
        "leges",
        "letteren",
        "lieden",
        "lurven",
        "manen",
        "manschappen",
        "manufacturen",
        "mazelen",
        "memoires",
        "middeleeuwen",
        "notulen",
        "omstreken",
        "onkosten",
        "onlusten",
        "paperassen",
        "perikelen",
        "personalia",
        "planariën",
        "pokken",
        "prammen",
        "prullaria",
        "quisquiliën",
        "regionen",
        "represailles",
        "revenuen",
        "saturnaliën",
        "schorseneren",
        "scrupules",
        "smiezen",
        "spiritualia",
        "stelten",
        "strapatsen",
        "subtropen",
        "tierelantijnen",
        "troebelen",
        "troepen",
        "tropen",
        "valuta",
        "victualiën",
        "waterpokken",
        "watten",
        "wittebroodsweken",
        "zemelen",
        # Kosten-gerelateerde pluralia tantum
        "aankoopkosten",
        "aanloopkosten",
        "aanmaakkosten",
        "aansluitkosten",
        "aanloopmoeilijkheden",
        "afvloeiingskosten",
        "afluisterpraktijken",
        "alternatieve kosten",
        # Militaire/wetenschappelijke termen
        "ABC-wapens",
        "analecten",
        # Geografische namen (eilanden, bergketens)
        "Aleoeten",
        "Azoren",
        "Balearen",
        "Caraïben",
        "Ardennen",
        "Apennijnen",
        "Dolomieten",
        "Karpaten",
        "Pyreneeën",
        "Lofoten",
        "Filipijnen",
        "Salomonseilanden",
        "Bahama's",
        "Dardanellen",
        "Amerikaanse Maagdeneilanden",
    }

    @classmethod
    def is_plurale_tantum(cls, woord: str) -> bool:
        """
        Check of een woord een plurale tantum is.

        Args:
            woord: Het te controleren woord (case-insensitive)

        Returns:
            True als het woord alleen in meervoud bestaat
        """
        return woord.lower() in cls.PLURALIA_TANTUM_WOORDEN

    @classmethod
    def get_alle_woorden(cls) -> set[str]:
        """
        Krijg alle pluralia tantum woorden.

        Returns:
            Set van alle Nederlandse pluralia tantum woorden
        """
        return cls.PLURALIA_TANTUM_WOORDEN.copy()

    @classmethod
    def tel_woorden(cls) -> int:
        """
        Tel het totaal aantal pluralia tantum woorden.

        Returns:
            Aantal woorden in de database
        """
        return len(cls.PLURALIA_TANTUM_WOORDEN)

    @classmethod
    def zoek_woorden_met_prefix(cls, prefix: str) -> set[str]:
        """
        Zoek alle pluralia tantum woorden met een bepaalde prefix.

        Args:
            prefix: De prefix om op te zoeken

        Returns:
            Set van woorden die met de prefix beginnen
        """
        prefix_lower = prefix.lower()
        return {
            woord
            for woord in cls.PLURALIA_TANTUM_WOORDEN
            if woord.startswith(prefix_lower)
        }

    @classmethod
    def is_geografische_naam(cls, woord: str) -> bool:
        """
        Check of een plurale tantum een geografische naam is.

        Args:
            woord: Het te controleren woord

        Returns:
            True als het een geografische plurale tantum is
        """
        geografische_woorden = {
            "Aleoeten",
            "Azoren",
            "Balearen",
            "Caraïben",
            "Ardennen",
            "Apennijnen",
            "Dolomieten",
            "Karpaten",
            "Pyreneeën",
            "Lofoten",
            "Filipijnen",
            "Salomonseilanden",
            "Bahama's",
            "Dardanellen",
            "Amerikaanse Maagdeneilanden",
        }
        return woord in geografische_woorden
