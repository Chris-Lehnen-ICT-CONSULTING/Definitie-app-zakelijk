import copy
import json
import sys
import traceback
from dataclasses import replace
from pathlib import Path

ROOT = Path('/private/tmp/def835-wp1-review-20260926')
sys.path.insert(0, str(ROOT))
from tests.offline_bootstrap import install
install()
sys.path.insert(0, str(ROOT / 'src'))
from domain.int02.contract import Configuratie, Uitvoering, maak_invoer, beoordeel, toets_actualiteit

cases = json.loads((ROOT / 'tests/fixtures/def835_int02_ontwerpgevallen.json').read_text())['gevallen']
cfg = Configuratie(normhash='a'*64, promptversie='probe', routeringshash='b'*64, provider='fake', model='fake')
execution = Uitvoering(actor='ai', status='completed')
def case(cid):
    return copy.deepcopy(next(c for c in cases if c['id'] == cid))
def assess(c):
    return beoordeel(maak_invoer(**c['invoer']), cfg, c['modelrespons'], execution)
def ground(field, ref=None):
    return dict(field=field, ref=ref, quote=None, start=None, end=None)

for cid in ('C112', 'C105'):
    for field in ('begrip', 'bron'):
        for empty in ('', ' \t\n'):
            c = case(cid)
            if field == 'begrip':
                c['invoer']['begrip'] = empty
            else:
                c['invoer']['bronnen'] = [{'id': 'B1', 'tekst': empty}]
            c['modelrespons']['passages'][0]['ground'] = ground(field, 'B1' if field == 'bron' else None)
            doc = assess(c)
            print('EMPTY', cid, field, repr(empty), 'actual=', (doc.status, doc.foutcategorie), 'expected=error/invalid_citation', 'replay=', toets_actualiteit(doc, doc.invoer, cfg).status)

for cid, quote in [('C112', 'Veld met de tekst {grond}.'), ('C105', 'De medewerker vult {grond} in.')]:
    c = case(cid)
    c['invoer']['kern'] = quote
    c['modelrespons']['passages'][0].update(quote=quote, start=0, end=len(quote), ground=ground('kern'))
    doc = assess(c)
    print('LITERAL', cid, 'quote=', repr(quote), 'literal_preserved=', quote in doc.melding, 'message=', repr(doc.melding))

c = case('C107')
c['modelrespons'].update(reason='De betekenis van {één vraag} is onbekend.', question='Wat betekent dit veld?')
doc = assess(c)
print('QUESTION', 'question_marks=', doc.melding.count('?'), 'expected=1', 'message=', repr(doc.melding))

c = case('C112')
doc = assess(c)
for name, payload in [('invalid-json-control', '{'), ('deep-invalid-json', '[' * 1100), ('long-integer-json', '1' * 5000)]:
    replay_doc = replace(doc, oordeel_json=payload)
    try:
        result = toets_actualiteit(replay_doc, doc.invoer, cfg)
        print('REPLAY', name, 'actual=', result.status, 'expected=error')
    except Exception as exc:
        print('REPLAY', name, 'UNEXPECTED', type(exc).__name__, str(exc))
        print(''.join(traceback.format_exception(exc)))
