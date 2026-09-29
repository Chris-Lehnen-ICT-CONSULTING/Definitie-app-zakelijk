import os
import sys
from pathlib import Path
ROOT = Path('/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app')
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from tests.offline_bootstrap import install
BASE = Path('/private/tmp/def835-q1-herreview-mFxx7E')
install(BASE / 'offline')
sys.path.insert(0, str(ROOT / 'src'))
import asyncio
import errno
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
    report('F2_latency_91s', {'latentie': data['latentie'], 'geslaagd': data['evaluatie']['mechanisch_geslaagd'], 'redenen': data['evaluatie']['redenen'], 'grootboek': k.stand()['fasen']})

async def storage(artefact):
    k = await t._kwal(folder('storage-' + artefact))
    original = m._schrijf_nieuw
    def fail(pad, data):
        if pad.name == artefact:
            raise OSError('geinjecteerde opslagfout')
        return original(pad, data)
    m._schrijf_nieuw = fail
    try:
        await t._fase(k, 'regressie', t.KwalProvider())
        error = None
    except m.ProefStopError as exc:
        error = exc.reden
    finally:
        m._schrijf_nieuw = original
    before = k.stand()
    present = sorted(p.name for p in k.proefmap.iterdir())
    provider = t.KwalProvider()
    try:
        await t._fase(k, 'ontwikkeling', provider)
        vervolg = 'toegestaan'
    except m.ProefGeweigerdError as exc:
        vervolg = exc.reden
    report('F3_artefactfout', {'artefact': artefact, 'fout': error, 'na_fout_bestanden': present, 'na_fout_fasen': before['fasen'], 'vervolg': vervolg, 'vervolgcalls': len(provider.inferenties())})

async def late_fsync():
    k = await t._kwal(folder('late-fsync'))
    original = os.fsync
    injected = [False]
    def fail(fd):
        if not injected[0] and k.grootboek.exists():
            doel = k.grootboek.stat()
            huidig = os.fstat(fd)
            if (doel.st_dev, doel.st_ino) == (huidig.st_dev, huidig.st_ino):
                rows = k.grootboek.read_text().splitlines()
                if rows and json.loads(rows[-1]).get('gebeurtenis') == 'fase_einde':
                    injected[0] = True
                    raise OSError(errno.EIO, 'geinjecteerde fsync-fout op fase_einde na flush')
        return original(fd)
    os.fsync = fail
    try:
        await t._fase(k, 'regressie', t.KwalProvider())
        error = None
    except OSError as exc:
        error = str(exc)
    finally:
        os.fsync = original
    before = k.stand()
    last = json.loads(k.grootboek.read_text().splitlines()[-1])
    provider = t.KwalProvider()
    try:
        vervolg = await t._fase(k, 'ontwikkeling', provider)
        outcome = {'toegestaan': True, 'geslaagd': vervolg['evaluatie']['mechanisch_geslaagd']}
    except m.ProefGeweigerdError as exc:
        outcome = {'toegestaan': False, 'reden': exc.reden}
    report('F3_fsync_na_flush', {'geinjecteerd': injected[0], 'fout': error, 'na_fout_stand': before, 'laatste_regel': last, 'vervolg': outcome, 'vervolgcalls': len(provider.inferenties())})

async def setup_race():
    k = await t._kwal(folder('race'))
    await t._fase(k, 'regressie', t.KwalProvider())
    return k

def worker(k, barrier, rejected, number):
    original = m._stand_voor_fase
    def synchronized(*args):
        stand = original(*args)
        barrier.wait(timeout=20)
        return stand
    m._stand_voor_fase = synchronized
    provider = t.KwalProvider()
    def held(request):
        if not rejected.wait(timeout=20):
            raise RuntimeError('tweede proces heeft nog niet geweigerd')
        return provider(request)
    try:
        data = asyncio.run(t._fase(k, 'ontwikkeling', held))
        outcome = {'geslaagd': data['evaluatie']['mechanisch_geslaagd']}
    except BaseException as exc:
        outcome = {'fouttype': type(exc).__name__, 'reden': getattr(exc, 'reden', None)}
        rejected.set()
    outcome.update({'inferenties': len(provider.inferenties()), 'telverzoeken': len(provider.verzoeken) - len(provider.inferenties())})
    (BASE / f'worker-{number}.json').write_text(json.dumps(outcome))

asyncio.run(latency())
for artefact in ('regressie-resultaat.json', 'regressie-bundel.json'):
    asyncio.run(storage(artefact))
asyncio.run(late_fsync())
k = asyncio.run(setup_race())
ctx = multiprocessing.get_context('fork')
barrier = ctx.Barrier(2)
rejected = ctx.Event()
workers = [ctx.Process(target=worker, args=(k, barrier, rejected, n)) for n in (1, 2)]
for p in workers:
    p.start()
for p in workers:
    p.join(40)
results = [json.loads((BASE / f'worker-{n}.json').read_text()) for n in (1, 2)]
report('F1_parallelle_ontwikkeling', {'workers': results, 'grootboek': k.stand(), 'slotbestand_aanwezig': (k.proefmap / m.SLOT_NAAM).exists(), 'exitcodes': [p.exitcode for p in workers]})
