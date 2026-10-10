"""DEF-846: het regelingenregister (matrix wet- en regelgeving × rechtsgebied).

Eén lijst in ``config/bronnenlijst.yaml`` voor de keuzelijst "wettelijke
basis" en de bronbibliotheek. Inhoud vastgesteld door Chris op 10-10-2026
(``docs/analyses/2026-10-09-rag-meting/matrix-concept-v2.md``, 30 regelingen).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.rechtsgebieden import RECHTSGEBIEDEN
from domain.sources.regelingen import RegisterError, lees_register, register

pytestmark = [pytest.mark.unit]

ROOT = Path(__file__).resolve().parents[3]
ECHT = ROOT / "config" / "bronnenlijst.yaml"

BASIS = """
bronnen:
  - sleutel: sr
    label: Wetboek van Strafrecht
    naam: Wetboek van Strafrecht
    formaat: bwb
    bwb_id: BWBR0001854
    versie: "2026-07-01"
    collectie: "Sr (versie 1-7-2026)"
    wet_regeling: "Wetboek van Strafrecht (versie 1-7-2026)"
    rechtsgebieden: [strafrecht, jeugdrecht]
  - sleutel: sv-nieuw
    label: Wetboek van Strafvordering (toekomstig)
    naam: Wetboek van Strafvordering
    formaat: op
    urls: [https://x/a.xml]
    bestanden: [a.xml]
    collectie: "Sv (nieuw)"
    wet_regeling: "Wetboek van Strafvordering (nieuw)"
    rechtsgebieden: [strafrecht]
    kenmerken: [alleen_expliciete_keuze]
  - sleutel: wpg
    label: Wet politiegegevens
    naam: Wet politiegegevens
    aliassen: [Wet op de politiegegevens]
    rechtsgebieden: [strafrecht, bestuursrecht]
  - sleutel: evrm
    label: EVRM (inclusief protocollen)
    naam: Verdrag tot bescherming van de rechten van de mens
    kenmerken: [alle_rechtsgebieden]
"""


def _register(tmp_path, tekst=BASIS):
    pad = tmp_path / "bronnenlijst.yaml"
    pad.write_text(tekst, encoding="utf-8")
    return lees_register(pad)


# --- laden en opvragen -------------------------------------------------------


def test_labels_in_volgorde_van_de_lijst(tmp_path):
    reg = _register(tmp_path)
    assert reg.labels() == [
        "Wetboek van Strafrecht",
        "Wetboek van Strafvordering (toekomstig)",
        "Wet politiegegevens",
        "EVRM (inclusief protocollen)",
    ]


def test_regeling_zonder_formaat_heeft_geen_bibliotheekbron(tmp_path):
    reg = _register(tmp_path)
    assert reg.zoek("Wet politiegegevens").collectie is None
    assert not reg.zoek("Wet politiegegevens").heeft_bibliotheekbron
    assert reg.zoek("Wetboek van Strafrecht").collectie == "Sr (versie 1-7-2026)"


def test_zoeken_op_label_alias_en_hoofdletters(tmp_path):
    reg = _register(tmp_path)
    assert reg.zoek("Wet op de politiegegevens").sleutel == "wpg"
    assert reg.zoek("  wetboek van strafrecht ").sleutel == "sr"
    assert reg.zoek("Burgerlijk Wetboek") is None
    assert reg.zoek("") is None


def test_normaliseren_vertaalt_aliassen_en_laat_vrije_invoer_staan(tmp_path):
    reg = _register(tmp_path)
    assert reg.normaliseer(
        ["Wet op de politiegegevens", "Wet politiegegevens", "Eigen tekst"]
    ) == ["Wet politiegegevens", "Eigen tekst"]


def test_rechtsgebied_kiest_regelingen_behalve_alleen_expliciet(tmp_path):
    reg = _register(tmp_path)
    sleutels = [r.sleutel for r in reg.voor_rechtsgebied("strafrecht")]
    # sv-nieuw telt alleen bij expliciete keuze (besluit B-2); evrm hoort bij
    # alle rechtsgebieden (besluit B-5).
    assert sleutels == ["sr", "wpg", "evrm"]
    assert [r.sleutel for r in reg.voor_rechtsgebied("familierecht")] == ["evrm"]


def test_hoort_bij(tmp_path):
    reg = _register(tmp_path)
    assert reg.zoek("Wetboek van Strafvordering (toekomstig)").hoort_bij("strafrecht")
    assert not reg.zoek("Wet politiegegevens").hoort_bij("familierecht")
    assert reg.zoek("EVRM (inclusief protocollen)").hoort_bij("belastingrecht")


def test_collecties_vergelijken_met_de_bibliotheek(tmp_path):
    reg = _register(tmp_path)
    zonder_regel, ontbrekend = reg.vergelijk_collecties(
        ["Sr (versie 1-7-2026)", "user_documents", "Oude collectie"]
    )
    assert zonder_regel == ["Oude collectie", "user_documents"]
    assert ontbrekend == ["Sv (nieuw)"]


# --- laadcontrole --------------------------------------------------------------


@pytest.mark.parametrize(
    ("vervang", "fout"),
    [
        (
            ("rechtsgebieden: [strafrecht, bestuursrecht]", "rechtsgebieden: [vaag]"),
            "onbekend rechtsgebied",
        ),
        (
            ("rechtsgebieden: [strafrecht, bestuursrecht]", "rechtsgebieden: []"),
            "geen rechtsgebied",
        ),
        (("sleutel: wpg", "sleutel: sr"), "dubbele sleutel"),
        (
            ("label: Wet politiegegevens", "label: wetboek van strafrecht"),
            "dubbel label",
        ),
        (
            (
                "aliassen: [Wet op de politiegegevens]",
                "aliassen: [Wetboek van Strafrecht]",
            ),
            "dubbel label",
        ),
        (
            ('collectie: "Sv (nieuw)"', 'collectie: "Sr (versie 1-7-2026)"'),
            "dubbele collectie",
        ),
        (
            ("kenmerken: [alleen_expliciete_keuze]", "kenmerken: [onzin]"),
            "onbekend kenmerk",
        ),
        (
            (
                "kenmerken: [alle_rechtsgebieden]",
                "kenmerken: [alle_rechtsgebieden]\n    rechtsgebieden: [strafrecht]",
            ),
            "alle_rechtsgebieden",
        ),
        (("    label: Wet politiegegevens\n", ""), "label"),
        (("    naam: Wet politiegegevens\n", ""), "naam"),
        (('    collectie: "Sv (nieuw)"\n', ""), "collectie"),
    ],
)
def test_ongeldig_register_wordt_geweigerd(tmp_path, vervang, fout):
    tekst = BASIS.replace(*vervang)
    assert tekst != BASIS, "vervanging trof niets"
    with pytest.raises(RegisterError, match=fout):
        _register(tmp_path, tekst)


# --- de vastgestelde inhoud (Chris, 10-10-2026) --------------------------------


def test_echt_register_is_geldig_en_compleet():
    reg = lees_register(ECHT)
    assert len(reg.regelingen) == 30
    assert sum(r.heeft_bibliotheekbron for r in reg.regelingen) == 21
    for regeling in reg.regelingen:
        assert set(regeling.rechtsgebieden) <= set(RECHTSGEBIEDEN)


def test_echt_register_vastgestelde_besluiten():
    reg = lees_register(ECHT)
    zoek = reg.zoek
    # B-2: nieuw WvSv alleen bij expliciete keuze, met volledige rechtsgebieden
    sv_nieuw = zoek("Wetboek van Strafvordering (toekomstig)")
    assert sv_nieuw.alleen_expliciete_keuze
    assert (
        sv_nieuw.rechtsgebieden
        == zoek("Wetboek van Strafvordering (huidig)").rechtsgebieden
    )
    assert sv_nieuw not in reg.voor_rechtsgebied("strafrecht")
    # B-5: EVRM hoort bij alle rechtsgebieden
    assert zoek("EVRM (inclusief protocollen)").alle_rechtsgebieden
    # AVG niet onder strafrecht (art. 2 lid 2 onder d AVG); wel bestuursrecht
    avg = zoek("Algemene verordening gegevensbescherming")
    assert not avg.hoort_bij("strafrecht")
    assert avg.hoort_bij("bestuursrecht")
    # B-1: sanctierecht = strafrechtelijk; niet bij Awb/AVG/UAVG/Wpg
    for label in (
        "Algemene wet bestuursrecht",
        "Algemene verordening gegevensbescherming",
        "Uitvoeringswet Algemene verordening gegevensbescherming",
        "Wet politiegegevens",
    ):
        assert not zoek(label).hoort_bij("sanctierecht"), label
    # B-3: Wet RO breed
    assert len(zoek("Wet op de rechterlijke organisatie").rechtsgebieden) == 7
    # Besluit 3: BW per boek; het algemene label bestaat niet meer
    assert zoek("Burgerlijk Wetboek") is None
    assert zoek("Burgerlijk Wetboek Boek 1 – Personen- en familierecht").hoort_bij(
        "familierecht"
    )
    # B-4: geen "Uitvoeringswet EU-richtlijnen"
    assert zoek("Uitvoeringswet EU-richtlijnen") is None
    # B-6: jeugdinrichtingen, tbs en Penitentiaire maatregel kiesbaar zonder bron
    for label in (
        "Beginselenwet justitiële jeugdinrichtingen",
        "Reglement justitiële jeugdinrichtingen",
        "Beginselenwet verpleging ter beschikking gestelden",
        "Reglement verpleging ter beschikking gestelden",
        "Penitentiaire maatregel",
    ):
        assert zoek(label) is not None and not zoek(label).heeft_bibliotheekbron


@pytest.mark.parametrize(
    ("oud", "nieuw"),
    [
        ("Wet op de politiegegevens", "Wet politiegegevens"),
        ("Vreemdelingenwet", "Vreemdelingenwet 2000"),
        ("Wet op de Identificatieplicht", "Wet op de identificatieplicht"),
        (
            "Europees Verdrag voor de Rechten van de Mens",
            "EVRM (inclusief protocollen)",
        ),
        ("Wetboek van Strafvordering (huidig)", "Wetboek van Strafvordering (huidig)"),
    ],
)
def test_oude_keuzelijstwaarden_blijven_herkend(oud, nieuw):
    assert register().normaliseer([oud]) == [nieuw]


def test_echte_bibliotheekcollecties_hebben_een_registerregel():
    """De 21 collecties van 9 oktober 2026 (data/bronnen.db) staan erin."""
    collecties = [
        "Sv (nieuw, i.w.t. 1-4-2029)", "Sv (geldend, versie 1-7-2026)",
        "Sr (versie 1-7-2026)", "Gratiewet (versie 1-4-2021)",
        "Pbw (versie 1-11-2025)", "Reclasseringsregeling 1995 (versie 26-6-2019)",
        "Wet RO (versie 1-7-2025)", "Wpg (versie 1-9-2026)",
        "Wjsg (versie 1-9-2026)", "UAVG (versie 1-9-2026)",
        "AVG (Verordening (EU) 2016/679)",
    ]  # fmt: skip
    zonder_regel, _ = lees_register(ECHT).vergelijk_collecties(collecties)
    assert zonder_regel == []
