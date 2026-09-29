import os
import sys
from pathlib import Path
ROOT = Path('/Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app')
BASE = Path('/private/tmp/def835-q1-f3-final-Lj72jE')
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from tests.offline_bootstrap import install
install(BASE / 'offline')
sys.path.insert(0, str(ROOT / 'src'))
import asyncio
import errno
import importlib.util
import json
import logging
import httpx
logging.disable(logging.CRITICAL)

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

t = module('review_helpers_f3_final', ROOT / 'tests/unit/validation/test_def835_int02_modelproef.py')
m = t.m

async def probe():
    scratch = BASE / 'late-fsync'
    scratch.mkdir()
    k = await t._kwal(scratch)
    original = os.fsync
    injected = []
    def fail(fd):
        if not injected and k.grootboek.exists():
            target, current = k.grootboek.stat(), os.fstat(fd)
            if (target.st_dev, target.st_ino) == (current.st_dev, current.st_ino):
                rows = k.grootboek.read_text().splitlines()
                if rows and json.loads(rows[-1]).get('gebeurtenis') == 'fase_einde':
                    injected.append(True)
                    raise OSError(errno.EIO, 'geinjecteerde fsync-fout op fase_einde na flush')
        return original(fd)
    provider = t.KwalProvider()
    os.fsync = fail
    try:
        await t._fase(k, 'regressie', provider)
        raise AssertionError('verwachte EIO bleef uit')
    except OSError as exc:
        assert exc.errno == errno.EIO
        error = str(exc)
    finally:
        os.fsync = original
    assert injected == [True]
    assert len(provider.inferenties()) == 3
    last = json.loads(k.grootboek.read_text().splitlines()[-1])
    assert last['gebeurtenis'] == 'fase_einde' and last['mechanisch_geslaagd'] is True
    fresh = module('review_fresh_f3_final', ROOT / 'scripts/analysis/def835_int02_modelproef.py')
    assert fresh is not m and fresh.Grootboek is not m.Grootboek
    calls = t.KwalProvider()
    key_reads = []
    try:
        await fresh.voer_kwalificatie_uit(
            k.manifest, k.tmp / 'kwal-akkoord.json', k.gevallen, 'ontwikkeling',
            sleutel=lambda: key_reads.append(True) or t.SLEUTEL,
            binnen=httpx.MockTransport(calls),
        )
        raise AssertionError('vervolgfase werd toegelaten')
    except fresh.ProefGeweigerdError as exc:
        reason = exc.reden
        assert reason == 'afronding_onvolledig'
    assert calls.verzoeken == [] and key_reads == []
    assert (k.proefmap / 'regressie-afronding.open').is_file()
    assert not (k.proefmap / 'regressie-afronding.voltooid').exists()
    print(json.dumps({
        'probe': 'F3_fsync_na_flush_verse_runner', 'resultaat': 'geslaagd',
        'geinjecteerde_fout': error, 'regressiecalls': len(provider.inferenties()),
        'leesbare_succesregel': last['mechanisch_geslaagd'],
        'verse_runner': fresh.__name__, 'weigering': reason,
        'vervolgtransporten': len(calls.verzoeken), 'sleutel_gelezen': bool(key_reads),
        'open_blijft': True, 'voltooid_aanwezig': False,
    }, ensure_ascii=False))

asyncio.run(probe())
