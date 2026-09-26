import copy
import json
import sys
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
checked = 0
def check(condition, name):
    global checked
    assert condition, name
    checked += 1
for cid, expected in [('C112','pass'), ('C105','fail')]:
    for field in ('begrip','bron'):
        for quoted in (False, True):
            c = case(cid)
            value = ' \tGeldige betekenisgrond\n '
            c['invoer']['begrip'] = value
            c['invoer']['bronnen'] = [{'id':'B1','tekst':value}]
            g = ground(field, 'B1' if field == 'bron' else None)
            if quoted:
                g.update(quote=value, start=0, end=len(value))
            c['modelrespons']['passages'][0]['ground'] = g
            doc = assess(c)
            check(doc.status == expected and doc.invoer.als_dict() == c['invoer'] and toets_actualiteit(doc,doc.invoer,cfg).status == expected, f'filled {cid}/{field}/{quoted}')
    c = case(cid)
    c['invoer'].update(begrip='', bronnen=[{'id':'unused','tekst':''}])
    check(assess(c).status == expected, f'unused empty fields {cid}')
    c = case(cid)
    c['invoer']['begrip'] = '\u00a0\u2003'
    c['modelrespons']['passages'][0]['ground'] = ground('begrip')
    check(assess(c).foutcategorie == 'invalid_citation', f'unicode whitespace {cid}')

literal = r'{grond} {passage} {één vraag} {citaat} {handeling/afweging} \1 \g<0>'
c = case('C112')
c['invoer']['bronnen'] = [{'id':literal, 'tekst':literal}]
c['modelrespons']['passages'][0]['ground'] = dict(field='bron',ref=literal,quote=literal,start=0,end=len(literal))
doc = assess(c)
check(doc.status == 'pass' and ('grond: bronpassage ' + literal + " ('" + literal + "').") in doc.melding, 'literal source id and quote')
c = case('C107')
c['modelrespons'].update(reason='De betekenis van {één vraag} is onbekend.',question='Wat betekent ' + literal + '?')
doc = assess(c)
check(doc.melding == 'INT-02 — Onvoldoende informatie. De betekenis van {één vraag} is onbekend. Vraag: Wat betekent ' + literal + '?' and doc.vraag == c['modelrespons']['question'], 'literal question')
c = case('C112')
c['modelrespons'].update(verdict='not_applicable',passages=[],scope_reason=literal,coverage='none')
check(assess(c).melding == 'INT-02 — Niet van toepassing. ' + literal + '. Er is geen oordeel over de definitiekern.', 'literal NA')

doc = assess(case('C112'))
for content in ('{', 'null', '[]', '{}', '"text"', 'true', '1'*5000, '['*100000+']'*100000, '['*100000):
    check(toets_actualiteit(replace(doc,oordeel_json=content),doc.invoer,cfg).status == 'error', 'corrupt or invalid replay')
check(toets_actualiteit(doc,doc.invoer,cfg).status == 'pass','valid replay')
changed = replace(doc.invoer,begrip='gewijzigd begrip')
result = toets_actualiteit(doc,changed,cfg)
check((result.status,result.reden) == ('review_required','historical'),'valid historical replay')
print(f'{checked} gerichte tegenproeven geslaagd')
