"""DEF-770 G24: gerichte offline regressietests voor reviewbevindingen 1-5.

Geen netwerk en geen applicatie-import: `anthropic.Anthropic` wordt vervangen
door een nep-provider die elke ontvangen aanvraag telt, en bronactivering,
uitpakken en app-nabewerking worden vervangen door nepfuncties. Alle invoer is
synthetisch en hier gedefinieerd; er is geen sleutel nodig (de testwaarde is
geen secret).

Draai tegen de herstelkopie (rood verwacht) en tegen de huidige versie (groen):

    <venv-python> -B g24_regressie_offline.py --werkmap <nieuwe map> \\
        [--harnas <pad naar g24_harnas.py>]

Elke test krijgt een eigen submap; niets wordt verwijderd of overschreven.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import traceback
import types
from pathlib import Path
from typing import Any

HIER = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HIER))  # effectproef_bron, ook voor een herstelkopie elders

MODEL = "claude-opus-5"
NEPSLEUTEL = "testwaarde-geen-secret"
TESTS: list[Any] = []


def test(fn):
    TESTS.append(fn)
    return fn


class Onderbreking(BaseException):
    """Nagebootste procesonderbreking nadat de provider de aanvraag ontving."""


# ---------------------------------------------------------------- nep-provider


class NepUsage:
    def __init__(self, i: int, o: int) -> None:
        self.input_tokens, self.output_tokens = i, o

    def model_dump(self, **_: Any) -> dict[str, int]:
        return {"input_tokens": self.input_tokens, "output_tokens": self.output_tokens}


class NepBlok:
    def __init__(self, tekst: str) -> None:
        self.type, self.text = "text", tekst


class NepResponse:
    def __init__(
        self,
        n: int,
        model: str = MODEL,
        stop: str = "end_turn",
        i: int = 1000,
        o: int = 50,
    ) -> None:
        self.id = f"msg_nep_{n}"
        self.model, self.stop_reason = model, stop
        self.content = [NepBlok(f"synthetische nepdefinitie {n}")]
        self.usage = NepUsage(i, o)

    def model_dump(self, **_: Any) -> dict[str, Any]:
        return {
            "id": self.id,
            "model": self.model,
            "stop_reason": self.stop_reason,
            "content": [{"type": "text", "text": b.text} for b in self.content],
            "usage": self.usage.model_dump(),
        }


class NepProvider:
    def __init__(self, gedrag: Any = None) -> None:
        self.ontvangen: list[dict[str, Any]] = []
        self.clients: list[dict[str, Any]] = []
        self.gedrag = gedrag or (lambda n, body: NepResponse(n))

    def fabriek(self, **kw: Any) -> Any:
        self.clients.append({k: v for k, v in kw.items() if k != "api_key"})
        provider = self

        class _Berichten:
            def create(self, **body: Any) -> Any:
                provider.ontvangen.append(body)  # "provider heeft ontvangen"
                return provider.gedrag(len(provider.ontvangen), body)

            def count_tokens(self, **_: Any) -> Any:
                raise AssertionError("count_tokens hoort in deze tests niet")

        return types.SimpleNamespace(messages=_Berichten())


@contextlib.contextmanager
def vervang(obj: Any, naam: str, waarde: Any):
    oud = getattr(obj, naam)
    setattr(obj, naam, waarde)
    try:
        yield
    finally:
        setattr(obj, naam, oud)


@contextlib.contextmanager
def nep_anthropic(provider: NepProvider):
    import anthropic

    os.environ["ANTHROPIC_API_KEY"] = NEPSLEUTEL
    with vervang(anthropic, "Anthropic", provider.fabriek):
        yield


def uitkomst(fn: Any, *args: Any) -> Any:
    """Exitcode; SystemExit met tekst en gewone excepties tellen als niet-nul."""
    try:
        return fn(*args)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else f"stop: {exc.code}"
    except Onderbreking:
        raise
    except Exception as exc:
        return f"exceptie: {type(exc).__name__}: {exc}"


# ---------------------------------------------------------------- fixtures


def canoniek(obj: Any) -> bytes:
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def schrijf(pad: Path, obj: Any) -> str:
    data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    with open(pad, "xb") as f:
        f.write(data)
    return sha(data)


def run_fixtures(
    map_: Path,
    invoeren: int = 6,
    herhalingen: int = 2,
    max_tokens: int = 1000,
    plafond: float = 5.0,
    geteld: int = 1000,
    muteer: Any = None,
) -> argparse.Namespace:
    verzoeken: dict[str, Any] = {}
    aanroepen = []
    for i in range(1, invoeren + 1):
        inv = f"SYN-G{i:02d}"
        for arm in ("oud", "nieuw"):
            body = {
                "model": MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": f"synthetisch {inv} {arm}"}],
                "thinking": {"type": "disabled"},
            }
            h = sha(canoniek(body))
            verzoeken[h] = body
            for n in range(1, herhalingen + 1):
                aanroepen.append(
                    {
                        "call_id": f"{inv}__{arm}__h{n}",
                        "invoer_id": inv,
                        "arm": arm,
                        "herhaling": n,
                        "request_sha256": h,
                        "begrip_gesanitiseerd": f"synbegrip{i}",
                    }
                )
    manifest = {
        "soort": "synthetisch testmanifest",
        "armen": {"oud": {"commit": "a" * 40}, "nieuw": {"commit": "b" * 40}},
        "beleid": {"provider": "anthropic", "model": MODEL, "max_tokens": max_tokens},
        "herhalingen": herhalingen,
        "plafond_usd": plafond,
        "verzoeken": verzoeken,
        "aanroepen": aanroepen,
    }
    if muteer:
        muteer(manifest)
    m_sha = schrijf(map_ / "manifest.json", manifest)
    totaal = sum(
        (geteld * 5.0 + manifest["verzoeken"][c["request_sha256"]]["max_tokens"] * 25.0)
        / 1_000_000
        for c in manifest["aanroepen"]
    )
    counts = {
        "manifest_sha256": m_sha,
        "tellingen": {h: {"input_tokens": geteld} for h in verzoeken},
        "max_kosten_usd_totaal": round(totaal, 6),
        "plafond_usd": plafond,
        "binnen_plafond": totaal <= plafond,
    }
    c_sha = schrijf(map_ / "counts.json", counts)
    schrijf(
        map_ / "goedkeuring.json",
        {
            "manifest_sha256": m_sha,
            "counts_sha256": c_sha,
            "plafond_usd": plafond,
            "goedgekeurd_door": "synthetische testfixture",
            "datum": "2026-09-24",
        },
    )
    return argparse.Namespace(
        manifest=map_ / "manifest.json",
        counts=map_ / "counts.json",
        goedkeuring=map_ / "goedkeuring.json",
        uitvoermap=map_ / "uit",
        env_file=None,
        timeout=5.0,
    )


def draai(g: Any, ns: argparse.Namespace, provider: NepProvider) -> Any:
    with nep_anthropic(provider):
        return uitkomst(g.cmd_run, ns)


def eis(rc: Any, nul: bool, provider: NepProvider, aantal: int) -> None:
    """Exitcode (nul of niet-nul) en exact aantal door de provider ontvangen."""
    if (rc == 0) != nul:
        raise AssertionError(f"exitcode {rc!r}, verwacht {'0' if nul else 'niet-0'}")
    if len(provider.ontvangen) != aantal:
        raise AssertionError(f"{len(provider.ontvangen)} ontvangen, verwacht {aantal}")


LANG_A = (
    "Een synthetische proefvergunning  wordt verleend\nvoor een termijn die de "
    "proefdienst vaststelt. "
) * 12
LANG_B = ("De synthetische aanvrager meldt iedere wijziging binnen vijf dagen. ") * 11
DOELGROEP = ("medewerkers van de synthetische proefdienst en hun leidinggevenden, ") * 9


def lange_invoer(inv_id: str = "SYN-LANG") -> dict[str, Any]:
    return {
        "id": inv_id,
        "stratum": "synthetisch",
        "begrip": "proefvergunning",
        "organisatorische_context": ["Synthetische Proefdienst"],
        "juridische_context": [],
        "wettelijke_basis": [],
        "bronpassages": [
            {"id": "P1", "tekst": LANG_A, "herkomst": "Synthetische regeling, art. 1"},
            {"id": "P2", "tekst": LANG_B, "herkomst": "Synthetische regeling, art. 2"},
        ],
        "bedoelde_betekenis": "SYNTHETISCH-LABEL-NIET-NAAR-MODEL",
        "doelgroep": DOELGROEP,
        "beschermde_kenmerken": ["SYNTHETISCH-KENMERK-NIET-NAAR-MODEL"],
        "beschermde_namen": [],
        "beschermde_negaties": [],
    }


def app_witruimte(tekst: str) -> str:
    """Zoals sanitize_snippet: WS_RE=\\s+ -> ' ' en strip."""
    return re.sub(r"\s+", " ", tekst).strip()


def nep_receipt(snippets: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    """Nabootsing van het documentkanaal: witruimte, kap 500 per fragment."""
    bronnen, xmls = [], []
    for idx, s in enumerate(snippets):
        volledig = app_witruimte(s["snippet"])
        inhoud = volledig[:500]
        xml = f'<bron nr="{idx + 1}">{html.escape(inhoud, quote=False)}</bron>'
        xmls.append(xml)
        bronnen.append(
            {
                "source_type": "document",
                "input_index": idx,
                "content": inhoud,
                "truncated": inhoud != volledig,
                "sanitized": inhoud != s["snippet"],
                "xml": xml,
            }
        )
    receipt = {"sources": bronnen, "omitted": [], "errors": []}
    return receipt, "PROMPT\n" + "\n".join(xmls) + "\nEINDE"


# ---------------------------------------------------------------- bevinding 1


@test
def b1_lange_bronnen_verliesloos_gefragmenteerd(g: Any, map_: Path) -> None:
    inv = lange_invoer()
    assert all(len(p["tekst"]) > 500 for p in inv["bronpassages"])
    assert sum(len(p["tekst"]) for p in inv["bronpassages"]) > 800
    assert len(inv["doelgroep"]) > 500
    snippets, relaties, normalisatie = g.bron_snippets(inv)
    assert g.FRAGMENT_MAX < 500, g.FRAGMENT_MAX
    assert all(len(s["snippet"]) <= g.FRAGMENT_MAX for s in snippets)
    tekst = json.dumps(snippets, ensure_ascii=False)
    for label in ("SYNTHETISCH-LABEL", "SYNTHETISCH-KENMERK"):
        assert label not in tekst, f"beoordelaarsveld in snippets: {label}"
    inhoud = {r["input_index"]: snippets[r["input_index"]]["snippet"] for r in relaties}
    herbouwd = g.reconstrueer(relaties, inhoud)
    verwacht = {
        "P1": app_witruimte(LANG_A),
        "P2": app_witruimte(LANG_B),
        g.DOELGROEP_ID: app_witruimte(f"Doelgroep: {DOELGROEP}"),
    }
    assert herbouwd == verwacht, "reconstructie wijkt af van de genormaliseerde bron"
    assert {b: n["genormaliseerd"] for b, n in normalisatie.items()} == verwacht
    assert normalisatie["P1"]["witruimte_gewijzigd"] is True


@test
def b1_harde_knip_zonder_spatie_verliesloos(g: Any, map_: Path) -> None:
    for tekst in ("x" * 1000, "kort", "a " + "y" * 900 + " b", "z" * 450, "z" * 451):
        delen = g.fragmenteer(tekst)
        assert all(0 < len(d) <= g.FRAGMENT_MAX for d, _ in delen), tekst[:20]
        assert "".join(d + s for d, s in delen) == tekst, tekst[:20]
        assert all(d == d.strip() for d, _ in delen), "fragment met rand-witruimte"


@test
def b1_receiptpoort_eist_volledige_inhoud(g: Any, map_: Path) -> None:
    snippets, relaties, normalisatie = g.bron_snippets(lange_invoer())
    snippets = g.fase_29(snippets)
    receipt, prompt = nep_receipt(snippets)
    goed = g._controleer_receipt(receipt, snippets, relaties, normalisatie, prompt)
    assert goed["alles_volledig_in_prompt"] is True, goed
    # Inhoud wijkt af, maar niet 'afgekapt' en XML staat in de prompt: moet falen.
    receipt["sources"][1]["content"] = receipt["sources"][1]["content"][:-3]
    fout = g._controleer_receipt(receipt, snippets, relaties, normalisatie, prompt)
    assert fout["alles_volledig_in_prompt"] is False, "inhoud_gelijk telt niet mee"


@test
def b1_ongefragmenteerde_lange_bron_valt_af(g: Any, map_: Path) -> None:
    """Eén fragment > 500 (oude route) wordt in de nabootsing afgekapt."""
    snippets, relaties, normalisatie = g.bron_snippets(lange_invoer())
    groot = dict(snippets[0], snippet=app_witruimte(LANG_A))
    receipt, prompt = nep_receipt([groot])
    rel = [dict(relaties[0], aantal=1, input_index=0, scheiding_na="")]
    uit = g._controleer_receipt(
        receipt, [groot], rel, {"P1": normalisatie["P1"]}, prompt
    )
    assert uit["alles_volledig_in_prompt"] is False


# ---------------------------------------------------------------- bevinding 2


@test
def b2_onderbreking_na_ontvangst_wordt_niet_herzonden(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)

    def breek(n: int, body: Any) -> Any:
        raise Onderbreking("proces valt weg na ontvangst")

    eerste = NepProvider(breek)
    try:
        draai(g, ns, eerste)
    except Onderbreking:
        pass
    else:
        raise AssertionError("onderbreking niet doorgegeven")
    assert len(eerste.ontvangen) == 1
    tweede = NepProvider()
    rc = draai(g, ns, tweede)
    assert rc != 0, f"herstart gaf {rc!r}"
    assert (
        tweede.ontvangen == []
    ), f"{len(tweede.ontvangen)} aanvragen opnieuw verstuurd"


@test
def b2_opslagfout_stopt_blijvend(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)
    eerste_id = "SYN-G01__oud__h1"
    echte_link = os.link

    def kapotte_link(src: Any, dst: Any, *a: Any, **k: Any) -> None:
        if Path(dst).name == f"{eerste_id}.json":
            raise OSError("nagebootste opslagfout")
        echte_link(src, dst, *a, **k)

    eerste = NepProvider()
    with vervang(os, "link", kapotte_link):
        rc = draai(g, ns, eerste)
    eis(rc, False, eerste, 1)
    tweede = NepProvider()
    eis(draai(g, ns, tweede), False, tweede, 0)


@test
def b2_verkeerd_model_stopt_blijvend(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)
    eerste = NepProvider(lambda n, b: NepResponse(n, model="claude-ander-model"))
    eis(draai(g, ns, eerste), False, eerste, 1)
    assert (ns.uitvoermap / "SYN-G01__oud__h1.json").exists(), "response niet bewaard"
    tweede = NepProvider()
    eis(draai(g, ns, tweede), False, tweede, 0)


@test
def b2_cutoff_stopt_blijvend(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)
    eerste = NepProvider(lambda n, b: NepResponse(n, stop="max_tokens", o=1000))
    eis(draai(g, ns, eerste), False, eerste, 1)
    tweede = NepProvider()
    eis(draai(g, ns, tweede), False, tweede, 0)


@test
def b2_geldige_hervatting_slaat_over(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)
    eerste = NepProvider()
    eis(draai(g, ns, eerste), True, eerste, 24)
    assert all(c.get("max_retries") == 0 for c in eerste.clients), eerste.clients
    tweede = NepProvider()
    eis(draai(g, ns, tweede), True, tweede, 0)


# ---------------------------------------------------------------- bevinding 3


def _nep_bron(g: Any):
    def activeer(bron: Path, sessie: Path) -> Any:
        (sessie / "werk").mkdir(parents=True)
        os.chdir(sessie / "werk")  # zoals activeer_bron: werkmap wisselt
        return types.SimpleNamespace(gate_is_actief=lambda: True)

    def pak_uit(repo: Path, bron: Path) -> dict[str, Any]:
        bron.mkdir()
        return {
            "uitgepakte_leden": 0,
            "overgeslagen_leden": [],
            "uitsluitingsregel": "nep",
        }

    def binding(repo: Path, verwacht: Any) -> dict[str, Any]:
        return {
            "archief": str(repo),
            "archief_sha256": "nep",
            "commit": verwacht or "c" * 40,
        }

    return contextlib.ExitStack(), [
        (g.eb, "activeer_bron", activeer),
        (g.eb, "pak_uit", pak_uit),
        (g.eb, "bronbinding", binding),
        (g.eb, "sleutelhashes", lambda bron: {}),
        (g.eb, "herkomstcontrole", lambda bron, modules: {}),
    ]


def _nabewerk_fixture(g: Any, map_: Path, weglaten: int = 0) -> argparse.Namespace:
    ns = run_fixtures(map_)
    manifest = json.loads(ns.manifest.read_text(encoding="utf-8"))
    m_sha = sha(ns.manifest.read_bytes())
    uit = map_ / "uit"
    uit.mkdir()
    calls = [c for c in manifest["aanroepen"] if c["arm"] == "oud"]
    for c in calls[weglaten:]:
        schrijf(
            uit / f"{c['call_id']}.json",
            {
                "call_id": c["call_id"],
                "request_sha256": c["request_sha256"],
                "manifest_sha256": m_sha,
                "model": MODEL,
                "stop_reason": "end_turn",
                "tekst": f"synthetische nepdefinitie {c['call_id']}",
            },
        )
    os.chdir(map_)
    return argparse.Namespace(
        arm="oud",
        repo=Path("nep.tar"),
        manifest=Path("manifest.json"),
        uitvoermap=Path("uit"),
        output=Path("nabewerk.json"),
        werkmap=None,
    )


async def _nep_nabewerk(raw: str, begrip: str) -> dict[str, Any]:
    return {"soort": "nep", "invoer_lengte": len(raw)}


def _met_nepbron(g: Any, fn: Any, ns: argparse.Namespace) -> Any:
    stapel, patches = _nep_bron(g)
    with stapel:
        for obj, naam, waarde in patches:
            stapel.enter_context(vervang(obj, naam, waarde))
        stapel.enter_context(vervang(g, "_nabewerk_een", _nep_nabewerk))
        return uitkomst(fn, ns)


@test
def b3_nabewerk_relatief_pad_vindt_resultaten(g: Any, map_: Path) -> None:
    ns = _nabewerk_fixture(g, map_)
    rc = _met_nepbron(g, g.cmd_nabewerk, ns)
    rapport = json.loads((map_ / "nabewerk.json").read_text(encoding="utf-8"))
    gevonden = [r for r in rapport["rijen"] if "ruwe_tekst" in r]
    assert len(gevonden) == 12, f"{len(gevonden)} van 12 resultaten gevonden"
    assert rc == 0, rc


@test
def b3_nabewerk_ontbrekend_resultaat_is_onvolledig(g: Any, map_: Path) -> None:
    ns = _nabewerk_fixture(g, map_, weglaten=1)
    rc = _met_nepbron(g, g.cmd_nabewerk, ns)
    assert rc != 0, f"ontbrekend resultaat gaf {rc!r}"


@test
def b3_prepare_invoerpad_is_echte_bron(g: Any, map_: Path) -> None:
    schrijf(map_ / "invoer.json", [lange_invoer()])
    os.chdir(map_)

    async def nep_prepare(inv: Any, beleid: Any) -> dict[str, Any]:
        return {
            "invoer_id": inv["id"],
            "prompt_deterministisch": True,
            "controle": {"alles_volledig_in_prompt": True},
        }

    ns = argparse.Namespace(
        arm="oud",
        repo=Path("nep.tar"),
        input=Path("invoer.json"),
        output=Path("prep.json"),
        werkmap=None,
        verwachte_commit=None,
    )
    stapel, patches = _nep_bron(g)
    with stapel:
        for obj, naam, waarde in patches:
            stapel.enter_context(vervang(obj, naam, waarde))
        stapel.enter_context(vervang(g, "_beleid", lambda: {"model": MODEL}))
        stapel.enter_context(vervang(g, "_prepare_invoer", nep_prepare))
        rc = uitkomst(g.cmd_prepare, ns)
    rapport = json.loads((map_ / "prep.json").read_text(encoding="utf-8"))
    verwacht = str((map_ / "invoer.json").resolve())
    assert rapport["invoer"]["pad"] == verwacht, rapport["invoer"]["pad"]
    assert rc == 0, rc


# ---------------------------------------------------------------- bevinding 4


@test
def b4_laatste_response_boven_budget_stopt(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)
    eerste = NepProvider(
        lambda n, b: NepResponse(n, o=200_000) if n == 24 else NepResponse(n)
    )
    eis(draai(g, ns, eerste), False, eerste, 24)
    assert (ns.uitvoermap / "SYN-G06__nieuw__h2.json").exists(), "response niet bewaard"
    tweede = NepProvider()
    eis(draai(g, ns, tweede), False, tweede, 0)


@test
def b4_invoer_boven_telling_stopt_direct(g: Any, map_: Path) -> None:
    ns = run_fixtures(map_)
    eerste = NepProvider(lambda n, b: NepResponse(n, i=1500))
    eis(draai(g, ns, eerste), False, eerste, 1)


# ---------------------------------------------------------------- bevinding 5


def _geweigerd(g: Any, ns: argparse.Namespace) -> None:
    provider = NepProvider()
    eis(draai(g, ns, provider), False, provider, 0)
    assert provider.clients == [], f"client aangemaakt: {provider.clients}"


@test
def b5_smoke_manifest_mag_niet_betaald(g: Any, map_: Path) -> None:
    _geweigerd(g, run_fixtures(map_, invoeren=2))


@test
def b5_max_tokens_afwijkend_geweigerd(g: Any, map_: Path) -> None:
    _geweigerd(g, run_fixtures(map_, max_tokens=2000))


@test
def b5_plafond_boven_5_geweigerd(g: Any, map_: Path) -> None:
    _geweigerd(g, run_fixtures(map_, plafond=6.0))


@test
def b5_dubbele_call_id_geweigerd(g: Any, map_: Path) -> None:
    def dubbel(m: dict[str, Any]) -> None:
        m["aanroepen"][1] = dict(m["aanroepen"][0])

    _geweigerd(g, run_fixtures(map_, muteer=dubbel))


@test
def b5_derde_herhaling_geweigerd(g: Any, map_: Path) -> None:
    _geweigerd(g, run_fixtures(map_, invoeren=4, herhalingen=3))


# ---------------------------------------------------------------- runner


def laad(pad: Path) -> Any:
    spec = importlib.util.spec_from_file_location("g24_onder_test", pad)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--harnas", type=Path, default=HIER / "g24_harnas.py")
    p.add_argument("--werkmap", type=Path, required=True)
    a = p.parse_args()
    harnas = a.harnas.resolve()
    werk = a.werkmap.resolve()
    werk.mkdir(exist_ok=False)
    g = laad(harnas)
    uitslagen = []
    for fn in TESTS:
        map_ = werk / fn.__name__
        map_.mkdir()
        cwd, env = os.getcwd(), dict(os.environ)
        try:
            fn(g, map_)
            ok, reden = True, ""
        except AssertionError as exc:
            ok, reden = False, f"AssertionError: {exc}"
        except BaseException as exc:  # ook Onderbreking of ontbrekende functie
            laatste = traceback.format_exc(limit=-1).strip().splitlines()[-1]
            ok, reden = False, f"{type(exc).__name__}: {exc} | {laatste}"
        finally:
            os.chdir(cwd)
            os.environ.clear()
            os.environ.update(env)
        uitslagen.append({"test": fn.__name__, "ok": ok, "reden": reden})
        print("PASS" if ok else "FAIL", fn.__name__, reden)
    samenvatting = {
        "harnas": str(harnas),
        "harnas_sha256": sha(harnas.read_bytes()),
        "testbestand_sha256": sha(Path(__file__).resolve().read_bytes()),
        "geslaagd": sum(u["ok"] for u in uitslagen),
        "totaal": len(uitslagen),
        "uitslagen": uitslagen,
    }
    schrijf(werk / "uitslag.json", samenvatting)
    print(f"{samenvatting['geslaagd']}/{samenvatting['totaal']} geslaagd")
    return 0 if all(u["ok"] for u in uitslagen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
