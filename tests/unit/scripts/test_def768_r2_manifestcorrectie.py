"""DEF-768 R2-OC-01: de actieve T/G-promptketen valt volledig onder de freeze.

Review `/private/tmp/def768-r2-ontwikkelcorrectie-review-result.md` (R2-OC-01):
`output_specification_module.py` is actief in de G-prompt maar stond niet in
het codemanifest; een instructiewijziging veranderde de G-prompt terwijl alle
verplichte freezevelden gelijk bleven.

Bewijs, offline met de fake-providergrens van de runnertests:
1. Een trace in een vers proces bepaalt de begrensde promptketen (aangeroepen
   functies, alle uitgevoerde modules onder src/services/prompts/, gelezen
   databestanden, directe imports van die promptmodules) en die keten staat
   volledig in het manifest.
2. Een bytewijziging in een ketenbestand verandert `code_sha256`, en een
   eerdere freeze wordt dan vóór reservering en netwerk geweigerd.
3. Een verouderde regelcache kan de G-prompt niet stil laten afwijken van de
   gehashte regelbronnen: de runner bouwt G-prompts op verse regels.
"""

from __future__ import annotations

import asyncio
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.unit.scripts.test_def768_ess05_proefrunner import (
    G_INVOER,
    ROOT,
    _FakeProvider,
    _g_invoer_actueel,
    _omgeving,
)
from tests.unit.scripts.test_def768_r2_runner import _freeze, _g, _opslag

pytestmark = [pytest.mark.unit]

sys.path.insert(0, str(ROOT / "scripts" / "ess05"))

import proefgrootboek as gb
import run_ess05_proef as runner

TRACE = ROOT / "tests" / "unit" / "scripts" / "def768_promptketen_trace.py"

#: (bestand, oud, nieuw): de reviewrepro plus een regelbron en de regelconfig.
MUTATIES = [
    pytest.param(
        "src/services/prompts/modules/output_specification_module.py",
        b"formele",
        b"bondige",
        id="output_specification",
    ),
    pytest.param(
        "src/toetsregels/regels/STR-01.json",
        b"zelfstandig naamwoord",
        b"zelfstandig woord",
        id="regel-json",
    ),
    pytest.param(
        "config/toetsregels/toetsregels_config.yaml",
        b"STR-01",
        b"STR-0X",
        id="toetsregels-config",
    ),
]


@pytest.fixture(scope="module")
def keten() -> dict:
    proces = subprocess.run(
        [sys.executable, str(TRACE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert proces.returncode == 0, proces.stderr[-2000:]
    return json.loads(proces.stdout)


class TestKetendekking:
    def test_trace_ziet_de_bekende_g_modules(self, keten):
        """Zelfcontrole: de trace mist de reviewrepro en de al gebonden modules niet."""
        for pad in (
            "src/services/prompts/modules/output_specification_module.py",
            "src/services/prompts/modules/json_based_rules_module.py",
            "src/services/prompts/modules/context_awareness_module.py",
            "src/toetsregels/regels/ESS-05.json",
            "config/toetsregels/toetsregels_config.yaml",
        ):
            assert pad in keten["keten"], pad

    def test_volledige_promptketen_staat_in_het_manifest(self, keten):
        assert keten["niet_in_manifest"] == []

    def test_alle_regelbronnen_staan_in_het_manifest(self):
        manifest = runner.codemanifest()
        regels = sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "src" / "toetsregels" / "regels").glob("*.json")
        )
        assert regels
        assert [r for r in regels if r not in manifest] == []


@pytest.mark.parametrize(("pad", "oud", "nieuw"), MUTATIES)
class TestBronwijzigingNaFreeze:
    @staticmethod
    def _gemuteerd(monkeypatch, pad: str, oud: bytes, nieuw: bytes) -> None:
        doel = (ROOT / pad).resolve()
        assert oud in doel.read_bytes()
        echt = runner._sha_bestand

        def sha(bestand):
            if Path(bestand).resolve() != doel:
                return echt(bestand)
            return runner.hashlib.sha256(
                doel.read_bytes().replace(oud, nieuw, 1)
            ).hexdigest()

        monkeypatch.setattr(runner, "_sha_bestand", sha)

    def test_wijziging_verandert_de_codehash(self, monkeypatch, pad, oud, nieuw):
        voor = runner.code_sha256()
        self._gemuteerd(monkeypatch, pad, oud, nieuw)
        assert runner.code_sha256() != voor

    def test_oude_g_freeze_voor_reservering_geweigerd(
        self, tmp_path, monkeypatch, pad, oud, nieuw
    ):
        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = _freeze(tmp_path, omg, "g")
        self._gemuteerd(monkeypatch, pad, oud, nieuw)
        with pytest.raises(gb.BudgetSchendingError, match="code_sha256"):
            _g(omg, tmp_path, _g_invoer_actueel(tmp_path), nieuw_grootboek=True,
               freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []
        assert not _opslag(tmp_path).grootboek.exists()

    def test_oude_t_freeze_geweigerd(self, tmp_path, monkeypatch, pad, oud, nieuw):
        from tests.unit.scripts.test_def768_ess05_proefrunner import (
            _gevallenbestand,
        )
        from tests.unit.scripts.test_def768_r2_runner import _t

        provider = _FakeProvider()
        omg = _omgeving(provider)
        freeze = _freeze(tmp_path, omg, "t")
        self._gemuteerd(monkeypatch, pad, oud, nieuw)
        with pytest.raises(gb.BudgetSchendingError, match="code_sha256"):
            _t(omg, tmp_path, _gevallenbestand(tmp_path, 5), fase="t_eind",
               nieuw_grootboek=True, freeze=freeze)  # fmt: skip
        assert provider.aanroepen == []
        assert not _opslag(tmp_path).grootboek.exists()

    def test_ongewijzigde_freeze_blijft_passen(
        self, tmp_path, monkeypatch, pad, oud, nieuw
    ):
        """Controle: zonder mutatie geen weigering (de test discrimineert)."""
        omg = _omgeving(_FakeProvider())
        freeze = _freeze(tmp_path, omg, "g")
        assert runner.controleer_freeze(
            freeze, omg, runner.PROEVEN["R2"], "g", dataset_sha256="x", herhaal_ids=[]
        ) == runner._sha_bestand(freeze)


class TestVerseRegelbron:
    def test_verouderde_regelcache_komt_niet_in_de_g_prompt(self):
        from toetsregels.rule_cache import get_rule_cache

        cache = get_rule_cache()
        cache.clear_cache()
        regels = copy.deepcopy(cache.get_all_rules())
        marker = "VEROUDERDE-CACHE-MARKER"
        for regel in regels.values():
            for sleutel, waarde in list(regel.items()):
                if isinstance(waarde, str):
                    regel[sleutel] = f"{waarde} {marker}"
        cache._rules_memo = regels
        cache._rules_memo_ts = time.monotonic()
        try:
            data = json.loads(G_INVOER.read_text(encoding="utf-8"))
            prompts = asyncio.run(runner.g_prompts(data, alleen_actueel=True))
        finally:
            cache.clear_cache()
        for item in prompts:
            assert marker not in item["varianten"]["actueel"]
