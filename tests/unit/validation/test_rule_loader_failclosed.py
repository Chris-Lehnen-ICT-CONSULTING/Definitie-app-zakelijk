"""DEF-606: beide echte laadpaden falen zichtbaar op een kapotte regelset.

De contractvalidatie stond tot nu toe alleen in `ModularValidationService`.
De laders eronder — `ToetsregelManager` (unit-/testpad) en
`RuleCache`/`CachedToetsregelManager` (productiepad) — sloegen een
onleesbaar of contractloos bestand over met `logger.error` + `continue` en
leverden gewoon de rest af. Dat is een stille validatie-bypass: de regel
verdwijnt uit de set, de score gaat omhoog, en niemand ziet het.

Deze suite draait tegen de échte laders met een tijdelijke regelmap. Elke
case wordt over beide paden geparametriseerd, zodat het productiepad niet
kan achterblijven op het testpad — precies de divergentie die DEF-606
blootlegde.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from toetsregels.cached_manager import CachedToetsregelManager
from toetsregels.manager import ToetsregelManager
from toetsregels.rule_cache import _load_single_rule_cached, get_rule_cache
from toetsregels.runtime_contract import (
    RuleContractError,
    root_contract_policy,
)

pytestmark = [pytest.mark.unit]

ECHTE_REGELS_DIR = (
    Path(__file__).resolve().parents[3] / "src" / "toetsregels" / "regels"
)

# Root-required velden komen uit de root-SSOT, niet uit een eigen lijstje.
ROOT_VERPLICHTE_VELDEN = list(root_contract_policy().record_required_fields)

# Een willekeurige, maar bestaande regel om te muteren. CON-02 is een
# gewone declaratieve regel zonder bijzondere contractvorm.
PROEFREGEL = "CON-02"


@pytest.fixture
def regelmap(tmp_path: Path) -> Path:
    """Een volledige kopie van de échte regelset in een tijdelijke map.

    De volledigheidscontrole draait tegen het manifest in de root-SSOT, dus
    een verzonnen mini-regelset zou altijd falen op "onvolledig" en nooit de
    fout aantonen die de test wil bewijzen. Werken met een kopie van de
    echte 53 records houdt de tests eerlijk: alleen de mutatie die de test
    aanbrengt mag het verschil maken.
    """
    doel = tmp_path / "regels"
    shutil.copytree(ECHTE_REGELS_DIR, doel)
    return tmp_path


def _pad(basis: Path, rule_id: str) -> Path:
    return basis / "regels" / f"{rule_id}.json"


def _schrijf(basis: Path, rule_id: str, inhoud: Any) -> None:
    pad = _pad(basis, rule_id)
    if isinstance(inhoud, str):
        pad.write_text(inhoud, encoding="utf-8")
    else:
        pad.write_text(
            json.dumps(inhoud, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _lees(basis: Path, rule_id: str) -> dict[str, Any]:
    return json.loads(_pad(basis, rule_id).read_text(encoding="utf-8"))


def _zonder_veld(basis: Path, rule_id: str, veld: str) -> None:
    data = _lees(basis, rule_id)
    data.pop(veld, None)
    _schrijf(basis, rule_id, data)


def _laad_via_manager(basis: Path) -> dict[str, dict[str, Any]]:
    return ToetsregelManager(base_dir=str(basis)).get_all_regels()


def _laad_via_cache(basis: Path) -> dict[str, dict[str, Any]]:
    """Het productiepad: CachedToetsregelManager → RuleCache → disk."""
    cache = get_rule_cache()
    cache.regels_dir = basis / "regels"
    cache.clear_cache()
    return CachedToetsregelManager().get_all_regels()


def _los_via_manager(basis: Path, rule_id: str) -> dict[str, Any] | None:
    return ToetsregelManager(base_dir=str(basis)).load_regel(rule_id)


def _los_via_cache(basis: Path, rule_id: str) -> dict[str, Any] | None:
    # De single-loader is alleen bereikbaar als fallback binnen RuleCache;
    # hier direct aangeroepen zodat het pad zelf getoetst wordt en niet de
    # bulk ervoor.
    return _load_single_rule_cached.__wrapped__(str(basis / "regels"), rule_id)


BULKPADEN = [
    pytest.param(_laad_via_manager, id="ToetsregelManager"),
    pytest.param(_laad_via_cache, id="RuleCache (productiepad)"),
]

LOSSE_PADEN = [
    pytest.param(_los_via_manager, id="ToetsregelManager.load_regel"),
    pytest.param(_los_via_cache, id="RuleCache single-load"),
]


@pytest.fixture(autouse=True)
def _schone_cache():
    """Laat geen tijdelijke regelset achter in de proces-brede singleton.

    `RuleCache` is een singleton; een testmap die blijft hangen zou de
    volgende testmodule stilletjes op een lege regelset zetten.
    """
    yield
    cache = get_rule_cache()
    cache.regels_dir = ECHTE_REGELS_DIR
    cache.clear_cache()


class TestGeldigeRegelsetLaadt:
    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_volledige_geldige_set_komt_door(self, regelmap, laad):
        regels = laad(regelmap)
        assert set(regels) == set(root_contract_policy().rule_ids)

    @pytest.mark.parametrize("los", LOSSE_PADEN)
    def test_geldige_losse_regel_komt_door(self, regelmap, los):
        assert los(regelmap, PROEFREGEL) is not None

    @pytest.mark.parametrize("los", LOSSE_PADEN)
    def test_ontbrekend_bestand_levert_none_bij_losse_load(self, regelmap, los):
        # Een regel die er niet is, is iets anders dan een regel die kapot
        # is; alleen het eerste mag stil None opleveren.
        assert los(regelmap, "BESTAAT-NIET") is None


class TestRootVerplichteVeldenBulk:
    """Een ontbrekend root-required veld mag nooit worden aangevuld.

    `RuleCache` vulde `naam`, `uitleg` en `prioriteit` met defaults vóór de
    contractvalidatie; een bronrecord zonder die velden passeerde daardoor
    alsnog. De defaults horen ná validatie, en alleen voor optionele velden.
    """

    @pytest.mark.parametrize("veld", ROOT_VERPLICHTE_VELDEN)
    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_ontbrekend_verplicht_veld_faalt(self, regelmap, laad, veld):
        _zonder_veld(regelmap, PROEFREGEL, veld)
        with pytest.raises(RuleContractError, match=PROEFREGEL):
            laad(regelmap)


class TestRootVerplichteVeldenLos:
    """De losse laadpaden zijn even streng als de bulkpaden.

    `load_regel` en `_load_single_rule_cached` controleerden alleen de
    JSON-vorm; een record zonder contract kwam ongehinderd door.
    """

    @pytest.mark.parametrize("veld", ROOT_VERPLICHTE_VELDEN)
    @pytest.mark.parametrize("los", LOSSE_PADEN)
    def test_ontbrekend_verplicht_veld_faalt(self, regelmap, los, veld):
        _zonder_veld(regelmap, PROEFREGEL, veld)
        with pytest.raises(RuleContractError, match=PROEFREGEL):
            los(regelmap, PROEFREGEL)

    @pytest.mark.parametrize("los", LOSSE_PADEN)
    def test_onbekende_evaluator_faalt(self, regelmap, los):
        data = _lees(regelmap, PROEFREGEL)
        data["runtime_contract"]["evaluator"] = "verzonnen_evaluator"
        _schrijf(regelmap, PROEFREGEL, data)
        with pytest.raises(RuleContractError, match="verzonnen_evaluator"):
            los(regelmap, PROEFREGEL)

    @pytest.mark.parametrize("los", LOSSE_PADEN)
    def test_ongeldige_json_faalt(self, regelmap, los):
        _schrijf(regelmap, PROEFREGEL, '{"id": "CON-02", kapot,,}')
        with pytest.raises(RuleContractError, match=PROEFREGEL):
            los(regelmap, PROEFREGEL)


class TestKapotteRegelsetFaaltZichtbaar:
    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_onbekende_evaluator_faalt(self, regelmap, laad):
        data = _lees(regelmap, PROEFREGEL)
        data["runtime_contract"]["evaluator"] = "verzonnen_evaluator"
        _schrijf(regelmap, PROEFREGEL, data)
        with pytest.raises(RuleContractError, match="verzonnen_evaluator"):
            laad(regelmap)

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_ongeldige_json_faalt(self, regelmap, laad):
        _schrijf(regelmap, PROEFREGEL, '{"id": "CON-02", kapot,,}')
        with pytest.raises(RuleContractError, match=PROEFREGEL):
            laad(regelmap)

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_json_dat_geen_object_is_faalt(self, regelmap, laad):
        _schrijf(regelmap, PROEFREGEL, "[1, 2, 3]")
        with pytest.raises(RuleContractError, match=PROEFREGEL):
            laad(regelmap)

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_id_bestandsnaamdrift_faalt(self, regelmap, laad):
        data = _lees(regelmap, PROEFREGEL)
        data["id"] = "HEEL-ANDERS-99"
        _schrijf(regelmap, PROEFREGEL, data)
        with pytest.raises(RuleContractError, match=PROEFREGEL):
            laad(regelmap)


class TestManifestVolledigheid:
    """De verwachte regel-ID-set komt uit de root-SSOT, niet uit de map zelf.

    Zolang de volledigheidscontrole de directory-glob als verwachting
    gebruikt, is zij tautologisch: een verdwenen regelbestand wordt dan ook
    niet meer verwacht en de controle blijft groen.
    """

    def test_manifest_dekt_de_regels_op_disk(self):
        op_disk = {p.stem for p in ECHTE_REGELS_DIR.glob("*.json")}
        manifest = set(root_contract_policy().rule_ids)
        assert manifest == op_disk, (
            f"manifest mist: {sorted(op_disk - manifest)} · "
            f"manifest kent onbekende regels: {sorted(manifest - op_disk)}"
        )

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_ontbrekend_regelbestand_faalt(self, regelmap, laad):
        _pad(regelmap, PROEFREGEL).unlink()
        with pytest.raises(RuleContractError, match="onvolledig"):
            laad(regelmap)

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_onverwacht_extra_regelbestand_faalt(self, regelmap, laad):
        data = _lees(regelmap, PROEFREGEL)
        data["id"] = "ZZZ-99"
        _schrijf(regelmap, "ZZZ-99", data)
        with pytest.raises(RuleContractError, match="ZZZ-99"):
            laad(regelmap)


class TestGeenGedeeltelijkeRegelset:
    """Alles of niets: één kapot bestand levert nooit een halve set op."""

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_kapotte_regel_levert_geen_restset(self, regelmap, laad):
        _schrijf(regelmap, PROEFREGEL, "{ dit is geen json")
        with pytest.raises(RuleContractError):
            laad(regelmap)

    @pytest.mark.parametrize("laad", BULKPADEN)
    def test_tweede_aanroep_serveert_geen_gecachte_halve_set(self, regelmap, laad):
        """Een mislukte load mag niets in de cache achterlaten.

        De oude RuleCache bewaarde de overgebleven regels een uur lang; een
        tweede aanroep leverde dan stilzwijgend de incomplete set.
        """
        _schrijf(regelmap, PROEFREGEL, "{ kapot")
        with pytest.raises(RuleContractError):
            laad(regelmap)
        with pytest.raises(RuleContractError):
            laad(regelmap)

    def test_manager_cachet_niets_na_mislukte_load(self, regelmap):
        _schrijf(regelmap, PROEFREGEL, "{ kapot")
        manager = ToetsregelManager(base_dir=str(regelmap))
        with pytest.raises(RuleContractError):
            manager.get_all_regels()
        assert not manager._regels_cache, (
            f"manager hield {len(manager._regels_cache)} regels vast na een "
            f"mislukte load"
        )

    def test_rulecache_cachet_niets_na_mislukte_load(self, regelmap):
        _schrijf(regelmap, PROEFREGEL, "{ kapot")
        cache = get_rule_cache()
        cache.regels_dir = regelmap / "regels"
        cache.clear_cache()
        with pytest.raises(RuleContractError):
            cache.get_all_rules()
        assert cache._rules_memo is None, "RuleCache hield een memo vast"
