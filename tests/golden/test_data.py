#!/usr/bin/env python3
"""
Test data for golden tests.

This module contains reference data for testing toetsregels with known good and bad examples.
"""

# Juridische definities - Goed en slecht
JURIDISCHE_DEFINITIES = {
    "hypotheek": {
        "correct": [
            "Een beperkt zakelijk recht op een onroerende zaak dat strekt tot zekerheid voor de voldoening van een vordering.",
            "Het recht van pand op registergoederen tot zekerheid van een geldlening.",
            "Een zakelijk zekerheidsrecht op onroerend goed ten behoeve van een schuldeiser.",
        ],
        "incorrect": {
            "circular": "Een hypotheek is een hypothecair recht.",
            "te_kort": "Een lening.",
            "vaag": "Iets met een huis en geld.",
            "geen_lidwoord": "Zekerheidsrecht op onroerend goed.",
            "voorbeelden": "Een zekerheidsrecht, bijvoorbeeld op een woning of kantoorpand.",
            "tegenstrijdig": "Een recht dat zowel zakelijk als persoonlijk is.",
        },
    },
    "eigendom": {
        "correct": [
            "Het meest omvattende recht dat een persoon op een zaak kan hebben.",
            "Het recht om vrij over een zaak te beschikken en anderen van elk gebruik uit te sluiten.",
            "Het volledige heerschappij over een zaak binnen de grenzen van de wet.",
        ],
        "incorrect": {
            "circular": "Eigendom is het recht van eigenaar zijn.",
            "voorbeelden": "Het recht op zaken zoals huizen, auto's of geld.",
            "informeel": "Als iets van jou is.",
            "tegenstrijdig": "Het recht om te beschikken zonder te mogen gebruiken.",
            "te_complex": "Het recht dat ontstaat wanneer men krachtens titel en levering, dan wel door verjaring, occupatie, natrekking, vermenging, zaaksvorming, vruchtvorming of afscheiding, de rechthebbende wordt.",
        },
    },
    "overeenkomst": {
        "correct": [
            "Een meerzijdige rechtshandeling waarbij partijen jegens elkaar verbintenissen aangaan.",
            "Een wilsovereenstemming tussen twee of meer partijen strekkende tot het scheppen van verbintenissen.",
            "De rechtshandeling waarbij partijen zich over en weer of eenzijdig tot een prestatie verbinden.",
        ],
        "incorrect": {
            "circular": "Een overeenkomst tussen partijen.",
            "te_simpel": "Een afspraak.",
            "vaag": "Wanneer mensen iets afspreken over iets.",
            "geen_juridisch": "Een belofte die je moet nakomen.",
            "met_spelling": "Een meerszijdige rechthandeling.",  # Spelling error
        },
    },
    "verbintenis": {
        "correct": [
            "Een rechtsbetrekking tussen twee of meer personen waarbij de een jegens de ander tot een prestatie gerechtigd is.",
            "De rechtsband waarbij een schuldenaar gehouden is tot een prestatie jegens een schuldeiser.",
            "Een vermogensrechtelijke betrekking tussen personen krachtens welke de een van de ander iets kan vorderen.",
        ],
        "incorrect": {
            "circular": "Een verbintenis is wat partijen verbindt.",
            "voorbeelden": "Een verplichting zoals betalen, leveren of iets doen.",
            "te_abstract": "De relatie tussen recht en plicht.",
            "onvolledig": "Een verplichting.",
        },
    },
    "erfdienstbaarheid": {
        "correct": [
            "Een last waarmee een onroerende zaak ten behoeve van een andere onroerende zaak is bezwaard.",
            "Het zakelijk recht waarbij een erf ten behoeve van een ander erf met een last is bezwaard.",
            "Een beperkt zakelijk recht dat een onroerende zaak bezwaart ten behoeve van een andere onroerende zaak.",
        ],
        "incorrect": {
            "persoonlijk": "Een recht van overpad voor de buurman.",
            "voorbeelden": "Een recht zoals recht van overpad of uitweg.",
            "vaag": "Een soort beperking op je eigendom.",
            "geen_zakelijk": "Een afspraak tussen buren over gebruik van elkaars grond.",
        },
    },
}

# Test zinnen voor context
CONTEXT_ZINNEN = {
    "hypotheek": [
        "De bank heeft een hypotheek gevestigd op het pand.",
        "De hypotheek strekt tot zekerheid voor de lening.",
        "Bij verkoop moet eerst de hypotheek worden afgelost.",
    ],
    "eigendom": [
        "De eigendom van het perceel is overgegaan op de koper.",
        "Hij kan zijn eigendom niet bewijzen.",
        "De eigendom is belast met een erfdienstbaarheid.",
    ],
    "overeenkomst": [
        "Partijen hebben een overeenkomst gesloten.",
        "De overeenkomst is nietig wegens wilsgebrek.",
        "Uit de overeenkomst vloeien wederzijdse verplichtingen voort.",
    ],
}

# Regel prioriteiten voor testing
REGEL_PRIORITEITEN = {
    "HOOG": ["ESS-001", "ESS-002", "STR-003", "CON-001"],
    "MIDDEN": ["STR-002", "VER-001", "VER-002", "SAM-001"],
    "LAAG": ["STR-004", "ARAI-001", "INT-002"],
}

# Verwachte scores voor verschillende kwaliteitsniveaus
KWALITEIT_DREMPELS = {
    "uitstekend": 0.85,  # > 85% score
    "goed": 0.70,  # 70-85% score
    "voldoende": 0.60,  # 60-70% score
    "matig": 0.50,  # 50-60% score
    "onvoldoende": 0.0,  # < 50% score
}

# Edge cases voor robuustheidstests
EDGE_CASES = {
    "empty": "",
    "single_word": "Test",
    "only_spaces": "   ",
    "only_punctuation": "...!!!???",
    "very_short": "Een test.",
    "very_long": "Een " + " zeer" * 200 + " lange definitie.",
    "special_chars": "Een definitie met §, ©, ®, ™ en € tekens.",
    "unicode": "Een definitie met émphasis, naïef en café.",
    "html_entities": "Een definitie met &lt;tags&gt; en &amp; tekens.",
    "sql_injection": "'; DROP TABLE definitions; --",
    "newlines": "Een definitie\nmet\nmeerdere\nregels.",
    "tabs": "Een\tdefinitie\tmet\ttabs.",
    "mixed_quotes": "Een definitie met \"dubbele\" en 'enkele' quotes.",
    "numbers": "Een definitie met 123 getallen en 45.67 decimalen.",
    "all_caps": "EEN DEFINITIE IN HOOFDLETTERS.",
    "no_period": "Een definitie zonder punt",
    "multiple_periods": "Een definitie. Met meerdere. Punten.",
    "question": "Is dit een definitie?",
    "exclamation": "Dit is een definitie!",
}
