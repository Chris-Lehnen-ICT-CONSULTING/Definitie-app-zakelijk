"""Zelfstandige offline repro voor de WP5a-review; wijzigt geen repositorybestanden."""
import asyncio
import importlib.util
import json
import logging
from pathlib import Path
import sys
import tempfile
from dataclasses import replace

ROOT = Path('/private/tmp/def835-wp2-review-20260927')
spec = importlib.util.spec_from_file_location('wp5a_helpers', ROOT / 'tests/unit/services/orchestrators/test_def835_int02_wrappers.py')
h = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = h
spec.loader.exec_module(h)
from domain.int02.contract import CONTRACTVERSIE, MELDING_NE, ontbrekende_invoer, toets_actualiteit

logging.disable(logging.CRITICAL)

class Cleaning:
    def __init__(self, replacement):
        self.replacement = replacement
    def clean_text(self, text):
        return self.replacement

async def main():
    root = Path(tempfile.mkdtemp(prefix='wp5a-codex-offline-', dir='/private/tmp'))
    regels = h._schrijf_regelmap(root / 'regels', o2=True)
    manager = h.ToetsregelManager(base_dir=str(regels.parent))
    empty = {k: [] for k in h.CONTEXT}
    cases = [
        ('NE_cleaning_verwijdert_kern', h.KERN, '', {}, False),
        ('NE_cleaning_voegt_kern_toe', '', h.KERN, {}, False),
        ('NE_zonder_cleaning', h.KERN, None, {}, False),
        ('ongeldige_recordkern_zonder_context', None, None, {}, True),
        ('ongeldige_bedoeling_zonder_context', h.KERN, None, {'int02_bedoeling': 42}, False),
    ]
    for name, kern, replacement, extra, recordroute in cases:
        svc = h.ModularValidationService(toetsregel_manager=manager, cleaning_service=Cleaning(replacement) if replacement is not None else None)
        dienst = h.FakeDienst(h._pass_respons())
        orch = h.ValidationOrchestratorV2(svc, int02_assessment_service=dienst)
        metadata = h._metadata(**empty, **extra)
        if recordroute:
            record = h._record(kern)
            record.organisatorische_context = []
            result = await orch.validate_definition(record, h.ValidationContext(metadata=metadata))
        else:
            result = await orch.validate_text(h.BEGRIP, kern, context=h.ValidationContext(metadata=metadata))
        detail = result.get('rule_results', {}).get('INT-02')
        expected = 'error' if recordroute or extra else MELDING_NE.replace('{kern/context}', ontbrekende_invoer(h._invoer(kern, **empty)))
        print(json.dumps({'case': name, 'expected': expected, 'calls': len(dienst.calls), 'detail': detail}, ensure_ascii=False))
        assert len(dienst.calls) == 0
        assert detail['status'] == 'not_evaluated'
        if name == 'NE_zonder_cleaning':
            assert detail['contract_version'] != CONTRACTVERSIE
            assert detail['review'] is None and 'assessment' not in detail
        elif name.startswith('NE_'):
            assert detail['parts'][0]['reason'] != expected

    # Foutinjectie op de dienstgrens: dezelfde invoer, een oud coherent document,
    # maar de dienst heeft een nieuw expliciet profiel. Geen cachebug geclaimd.
    original_ai = h.FakeAI(h._pass_respons())
    old_service = h.Int02AssessmentService(original_ai, h.FakeRouter(), profiel=h._profiel(), budget=h._budget())
    old_result = await old_service.assess(h._invoer())
    class NewRouter(h.FakeRouter):
        def get_model(self, task_type):
            return h.PROVIDER, 'fake-new-model'
    new_ai = h.FakeAI(h._pass_respons())
    class ReturnsOldResult(h.Int02AssessmentService):
        async def assess(self, invoer, **kwargs):
            return old_result
    stale_service = ReturnsOldResult(new_ai, NewRouter(), profiel=h._profiel(model='fake-new-model'), budget=h._budget())
    from services.validation.int02_assessment_service import PROMPT_VERSION
    current_config = stale_service._configuratie(stale_service._route(), PROMPT_VERSION)
    oracle = toets_actualiteit(old_result.document, h._invoer(), current_config)
    svc = h.ModularValidationService(toetsregel_manager=manager)
    orch = h.ValidationOrchestratorV2(svc, int02_assessment_service=stale_service)
    result = await h._via_tekst(orch)
    detail = result['rule_results']['INT-02']
    print(json.dumps({'case': 'configuratiebinding', 'WP1_met_actuele_config': {'status': oracle.status, 'reden': oracle.reden}, 'wrapper': {'status': detail['status'], 'review': detail['review'], 'document_model': detail['assessment']['binding']['model']}, 'actueel_model': current_config.model, 'nieuwe_ai_calls': new_ai.calls}, ensure_ascii=False))
    assert oracle.reden == 'historical'
    assert detail['status'] == 'pass' and detail['review']['actuality'] == 'current'
    assert new_ai.calls == 0
    print('REPRO_ASSERTIONS_OK; alle aangeroepen AI-grenzen zijn lokale fakes')

asyncio.run(main())
