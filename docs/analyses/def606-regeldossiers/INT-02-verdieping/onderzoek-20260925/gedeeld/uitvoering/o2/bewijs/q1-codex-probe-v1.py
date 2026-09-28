import os
import sys
from pathlib import Path
ROOT = Path('/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app')
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from tests.offline_bootstrap import install
BASE = Path('/private/tmp/def835-q1-review-qjykDS')
install(BASE / 'offline')
sys.path.insert(0, str(ROOT / 'src'))
import asyncio
import importlib.util
import json
import logging
import multiprocessing
import time
from types import SimpleNamespace
logging.disable(logging.CRITICAL)
spec = importlib.util.spec_from_file_location('review_helpers', ROOT / 'tests/unit/validation/test_def835_int02_modelproef.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
m = t.m

def folder(name):
    p = BASE / name
    p.mkdir()
    return p

def report(name, data):
    print(json.dumps({'probe': name, **data}, ensure_ascii=False), flush=True)

async def latency():
    k = await t._kwal(folder('latency'))
    await t._tot_en_met(k, 'ontwikkeling')
    original = m.time
    offset = [0.0]
    provider = t.KwalProvider()
    def delayed(request):
        if request.url.path == '/v1/messages':
            offset[0] += 91.0
        return provider(request)
    m.time = SimpleNamespace(monotonic=lambda: time.monotonic() + offset[0])
    try:
        data = await t._fase(k, 'holdout', delayed)
    finally:
        m.time = original
    report('latency_91s', {'latentie': data['latentie'], 'evaluatie': data['evaluatie'], 'grootboek': k.stand()['fasen']})

async def storage():
    k = await t._kwal(folder('storage'))
    original = m._schrijf_nieuw
    def fail(pad, data):
        if pad.name == 'regressie-resultaat.json':
            raise OSError('geinjecteerde opslagfout')
        return original(pad, data)
    m._schrijf_nieuw = fail
    try:
        await t._fase(k, 'regressie', t.KwalProvider())
    except OSError as exc:
        error = str(exc)
    finally:
        m._schrijf_nieuw = original
    before = k.stand()
    present = sorted(p.name for p in k.proefmap.iterdir())
    provider = t.KwalProvider()
    vervolg = await t._fase(k, 'ontwikkeling', provider)
    report('storage_error', {'fout': error, 'na_fout_bestanden': present, 'na_fout_fasen': before['fasen'], 'vervolgcalls': len(provider.inferenties()), 'vervolg_geslaagd': vervolg['evaluatie']['mechanisch_geslaagd']})

async def setup_race():
    k = await t._kwal(folder('race'))
    await t._fase(k, 'regressie', t.KwalProvider())
    return k

def worker(k, barrier, number):
    original = m.Grootboek.lees
    reads = [0]
    def synchronized(cls, pad, sha):
        boek = original(pad, sha)
        reads[0] += 1
        if reads[0] == 2:
            barrier.wait(timeout=30)
        return boek
    m.Grootboek.lees = classmethod(synchronized)
    provider = t.KwalProvider()
    try:
        data = asyncio.run(t._fase(k, 'ontwikkeling', provider))
        outcome = {'geslaagd': data['evaluatie']['mechanisch_geslaagd']}
    except BaseException as exc:
        outcome = {'fouttype': type(exc).__name__, 'reden': getattr(exc, 'reden', None)}
    outcome.update({'inferenties': len(provider.inferenties()), 'telverzoeken': len(provider.verzoeken) - len(provider.inferenties()), 'ids': provider.inferenties()})
    (BASE / f'worker-{number}.json').write_text(json.dumps(outcome))

asyncio.run(latency())
asyncio.run(storage())
k = asyncio.run(setup_race())
ctx = multiprocessing.get_context('fork')
barrier = ctx.Barrier(2)
workers = [ctx.Process(target=worker, args=(k, barrier, n)) for n in (1, 2)]
for p in workers:
    p.start()
for p in workers:
    p.join(40)
results = [json.loads((BASE / f'worker-{n}.json').read_text()) for n in (1, 2)]
try:
    state = k.stand()
except Exception as exc:
    state = {'fouttype': type(exc).__name__, 'reden': getattr(exc, 'reden', None)}
report('parallelle_ontwikkeling', {'workers': results, 'cumulatieve_inferenties_echt_bij_nepprovider': 3 + sum(r['inferenties'] for r in results), 'cumulatieve_tokenmetingen': 3 + sum(r['telverzoeken'] for r in results), 'grootboek': state, 'exitcodes': [p.exitcode for p in workers]})
