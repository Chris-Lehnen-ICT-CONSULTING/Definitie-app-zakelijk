"""DEF-751 B1 — verliesvrije categorieweergave (pure helper).

De editor kende vier keuzes terwijl het schema elf waarden toestaat; een
geladen ENT/ACT/… crashte op ``list.index``. De helper levert de opties en de
index zodat de geladen waarde exact terugkomt, zonder omzetting en zonder
claim over herkomst ("bestaande waarde — ongewijzigd", niet "historisch").
"""

from __future__ import annotations

import pytest

from domain.ontological_categories import OntologischeCategorie
from ui.components.formatters.definition_formatter_utils import (
    CATEGORY_DISPLAY_NAMES,
)
from ui.helpers.categorie_weergave import (
    GEEN_CATEGORIE,
    STANDAARD_CATEGORIEEN,
    bouw_categorie_opties,
    categorie_label,
    generatiecategorie_van,
    is_opslagcategorie,
)

pytestmark = [pytest.mark.unit]


def test_standaardkeuzes_zijn_precies_de_vier_enumwaarden():
    assert [c.value for c in OntologischeCategorie] == STANDAARD_CATEGORIEEN


@pytest.mark.parametrize("waarde", ["type", "proces", "resultaat", "exemplaar"])
def test_standaardwaarde_geeft_vier_opties_en_eigen_index(waarde):
    opties, index = bouw_categorie_opties(waarde)
    assert opties == STANDAARD_CATEGORIEEN
    assert opties[index] == waarde


@pytest.mark.parametrize("waarde", ["ENT", "ACT", "REL", "ATT", "AUT", "STA", "OTH"])
def test_schemawaarde_buiten_de_vier_komt_exact_terug_als_extra_optie(waarde):
    opties, index = bouw_categorie_opties(waarde)
    assert opties == [*STANDAARD_CATEGORIEEN, waarde]
    assert opties[index] == waarde


def test_onbekende_geladen_waarde_crasht_niet_en_wordt_niet_omgezet():
    opties, index = bouw_categorie_opties("Onbekend-Legacy")
    assert opties[index] == "Onbekend-Legacy"
    assert "proces" in opties and opties[index] != "proces"


@pytest.mark.parametrize("leeg", [None, ""])
def test_ontbrekende_waarde_wordt_geen_proces(leeg):
    opties, index = bouw_categorie_opties(leeg)
    assert opties[index] == GEEN_CATEGORIE
    assert GEEN_CATEGORIE == ""


def test_label_benoemt_bestaande_waarde_als_ongewijzigd_zonder_herkomstclaim():
    label = categorie_label("ENT")
    assert "Entiteit" in label
    assert "bestaande waarde" in label and "ongewijzigd" in label
    assert "historisch" not in label.lower()
    assert "Type" in categorie_label("type")
    assert "ongewijzigd" not in categorie_label("type")
    assert "geen categorie" in categorie_label(GEEN_CATEGORIE).lower()


def test_opslagcategorie_is_de_schemaset_zonder_extra_kopie():
    # De set komt uit de bestaande formatter-tabel; hier geen tweede lijst.
    for waarde in CATEGORY_DISPLAY_NAMES:
        assert is_opslagcategorie(waarde)
    assert not is_opslagcategorie("Type")  # schema-CHECK is hoofdlettergevoelig
    assert not is_opslagcategorie("entiteit")
    assert not is_opslagcategorie("")
    assert not is_opslagcategorie(None)


@pytest.mark.parametrize(
    ("invoer", "verwacht"),
    [
        ("type", OntologischeCategorie.TYPE),
        ("PROCES", OntologischeCategorie.PROCES),
        ("Resultaat", OntologischeCategorie.RESULTAAT),
        ("exemplaar", OntologischeCategorie.EXEMPLAAR),
    ],
)
def test_generatiecategorie_herkent_de_vier_keuzes_ongeacht_kast(invoer, verwacht):
    assert generatiecategorie_van(invoer) is verwacht


@pytest.mark.parametrize("invoer", ["ENT", "Kind", "", None, "proces "])
def test_generatiecategorie_geeft_geen_stille_default(invoer):
    assert generatiecategorie_van(invoer) is None
