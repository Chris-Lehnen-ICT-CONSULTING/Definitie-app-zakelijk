#!/usr/bin/env python3
"""Integriteitscheck van het CON-02 acceptatiepakket.

Dit is GEEN acceptatietest en bewijst niets over app- of modelgedrag. Het
controleert uitsluitend dat het pakket structureel klopt en de historische
basis niet is vervormd. Alle vergelijkingen gebruiken de snapshots in
``basis/`` en relatieve paden binnen het pakket; er wordt nooit een extern
(historisch) pad geopend. De repo-kopieën van de kruisreviewbestanden worden,
indien aanwezig, alleen tegen de snapshot-hash gecontroleerd.

Controles:
  1. pakketstructuur (verplichte bestanden en basis-snapshots aanwezig)
  2. 31 C02-P-casussen en 94 unieke IDs (register, overzicht, formulier)
  3. exacte gelijkheid van scenario-input met basis/v6 en basis/v2 incl.
     reproductie van scenario_input_sha256
  4. per casussectie in het formulier: titel, bronnen, ieder inputveld,
     gegeven/wanneer, letterlijke passages, lege oordeelvelden
  5. 13 fixtures: sha256/bytes gelijk aan basis/bronmanifest-v3 en manifest;
     passages letterlijk in de fixturebytes
  6. alle menselijke oordelen leeg (pending / null / goldset false)
  7. basis-snapshots gelijk aan de bij bouw vastgelegde sha256's

Aanroep:
  python3 verifieer_pakket.py [PAKKETMAP]        # integriteitscheck
  python3 verifieer_pakket.py [PAKKETMAP] --zelftest
      # bewijst dat de check discrimineert: in-memory mutanten moeten rood
      # worden, het ongewijzigde pakket groen. Schrijft niets.

Exit 0 = integer (of zelftest geslaagd); exit 1 = afwijking.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HASH_VELDEN = ["scenario", "title", "input", "given", "source_ids"]
EERSTE_ZES = ["C02-P01", "C02-P02", "C02-P04", "C02-P11", "C02-P16", "C02-P31"]
VERPLICHT = [
    "START-HIER.md",
    "deskundigenformulier.md",
    "acceptatie-register.json",
    "bronmanifest-sha256.json",
    "overzicht-94-ids.md",
    "bouw_pakket.py",
    "bronfixtures",
    "basis",
]
SYNTHETISCH_KINDS = ("intentional_test_mutation", "identical_bytes_renamed")
KOP_RE = re.compile(r"^## (C02-P\d\d) — (.*?)(?: ★ eerste zes)?$", re.M)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def scenario_hash(case: dict) -> str:
    sub = {k: v for k, v in case.items() if k in HASH_VELDEN}
    return sha_bytes(json.dumps(sub, sort_keys=True, ensure_ascii=False).encode())


def md_quote(tekst: str) -> str:
    return "\n".join("> " + r for r in tekst.splitlines())


def toon(v) -> str:
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def oordeel_leeg(e: dict) -> bool:
    return (
        e.get("status") == "pending"
        and all(e.get(k) is None for k in ("actor", "datum", "besluit", "motivering"))
        and e.get("goldset") is False
    )


def formulier_secties(form: str) -> dict[str, tuple[str, str]]:
    """{case_id: (titel, sectietekst)} — sectie loopt tot de volgende casuskop."""
    koppen = list(KOP_RE.finditer(form))
    out: dict[str, tuple[str, str]] = {}
    for i, m in enumerate(koppen):
        einde = koppen[i + 1].start() if i + 1 < len(koppen) else len(form)
        out[m.group(1)] = (m.group(2), form[m.start() : einde])
    return out


# Exact lege beoordelingsblok zoals de bouwer het schrijft (regels zonder "\n").
# De verifier eist per casus dat het complete blok — van de kop "### 6." tot het
# einde van de casussectie — regel-voor-regel hieraan gelijk is. Elke extra of
# afwijkende regel (ook een vervolgregel onder Motivering) telt als ingevuld.
OORDEELBLOK_KOP = "### 6. Deskundig oordeel (in te vullen)"
OORDEELBLOK_LEEG = [
    OORDEELBLOK_KOP,
    "",
    "- [ ] **Acceptatie** — historische verwachting + huidige laag zijn juist als acceptatiecriterium",
    "- [ ] **Afwijzing** — zie motivering",
    "- **Motivering:** ",
    "- **Actor (naam/rol):** ",
    "- **Datum:** ",
    "",
    "---",
]


def _regels(tekst: str) -> list[str]:
    """Regels zonder trailing whitespace; lege regels aan begin/eind weggelaten."""
    r = [x.rstrip() for x in tekst.splitlines()]
    while r and not r[0]:
        r.pop(0)
    while r and not r[-1]:
        r.pop()
    return r


def formulier_oordelen_leeg(form: str) -> list[str]:
    """Meldt per casussectie een beoordelingsblok dat niet exact de lege template is."""
    fouten = []
    verwacht = _regels("\n".join(OORDEELBLOK_LEEG))
    for cid, (_, sec) in formulier_secties(form).items():
        n = sec.count(OORDEELBLOK_KOP)
        if n != 1:
            fouten.append(f"[formulier-oordeel] {cid}: beoordelingsblok {n}x gevonden")
            continue
        blok = _regels(sec[sec.index(OORDEELBLOK_KOP) :])
        if blok != verwacht:
            afw = next(
                (
                    i
                    for i, (a, b) in enumerate(zip(blok, verwacht, strict=False))
                    if a != b
                ),
                min(len(blok), len(verwacht)),
            )
            regel = blok[afw] if afw < len(blok) else "(ontbrekende regel)"
            fouten.append(
                f"[formulier-oordeel] {cid}: beoordelingsblok wijkt af van lege template "
                f"bij regel {afw + 1}: {regel[:60]!r}"
            )
    return fouten


# ---------------------------------------------------------------------------
# Laden (alle I/O) — gescheiden van controleren (puur in-memory)
# ---------------------------------------------------------------------------
def laad(pkg: Path) -> dict:
    ontbreekt = [n for n in VERPLICHT if not (pkg / n).exists()]
    if ontbreekt:
        return {"structuur_fouten": [f"[structuur] ontbreekt: {n}" for n in ontbreekt]}
    reg = json.loads((pkg / "acceptatie-register.json").read_text(encoding="utf-8"))
    basis: dict[str, bytes] = {}
    for naam, info in reg["gelezen_bronnen"].items():
        p = pkg / info["snapshot"]
        basis[naam] = p.read_bytes() if p.exists() else b""
    repo = pkg.parents[2]
    repo_kopie: dict[str, bytes | None] = {}
    for naam, info in reg["gelezen_bronnen"].items():
        rel = info.get("repo_pad")
        if rel:
            p = repo / rel
            repo_kopie[naam] = p.read_bytes() if p.exists() else None
    fixtures = {
        p.relative_to(pkg).as_posix(): p.read_bytes()
        for p in (pkg / "bronfixtures").rglob("*")
        if p.is_file()
    }
    return {
        "structuur_fouten": [],
        "reg": reg,
        "man": json.loads(
            (pkg / "bronmanifest-sha256.json").read_text(encoding="utf-8")
        ),
        "form": (pkg / "deskundigenformulier.md").read_text(encoding="utf-8"),
        "overzicht_md": (pkg / "overzicht-94-ids.md").read_text(encoding="utf-8"),
        "basis": basis,
        "repo_kopie": repo_kopie,
        "fixtures": fixtures,
    }


# ---------------------------------------------------------------------------
def controleer(d: dict) -> list[str]:
    if d.get("structuur_fouten"):
        return list(d["structuur_fouten"])
    f: list[str] = []
    reg, man, form = d["reg"], d["man"], d["form"]

    # 7. basis-snapshots gelijk aan bij bouw vastgelegde hashes; repo-kopie idem
    for naam, info in reg["gelezen_bronnen"].items():
        b = d["basis"].get(naam, b"")
        if not b:
            f.append(f"[basis] snapshot ontbreekt: {info['snapshot']}")
        elif sha_bytes(b) != info["sha256"]:
            f.append(f"[basis] snapshot gewijzigd: {info['snapshot']}")
        rk = d["repo_kopie"].get(naam)
        if rk is not None and sha_bytes(rk) != info["sha256"]:
            f.append(f"[basis] repo-kopie wijkt af van snapshot: {info['repo_pad']}")
    if any(x.startswith("[basis] snapshot") for x in f):
        return f

    def basis_json(naam: str):
        return json.loads(d["basis"][naam].decode("utf-8"))

    v6 = basis_json("register_praktijk_v6")
    v2 = basis_json("register_kruisreview_v2")
    bm3 = basis_json("bronmanifest_v3")
    v6_p = {c["id"]: c for c in v6["cases"] if c["id"].startswith("C02-P")}
    v2_all = {c["id"]: c for c in v2["cases"]}

    # 2. aantallen en unieke IDs
    cases = reg["cases"]
    ids = [c["id"] for c in cases]
    if (
        len(cases) != 31
        or len(set(ids)) != 31
        or not all(i.startswith("C02-P") for i in ids)
    ):
        f.append(
            f"[aantal] verwacht 31 unieke C02-P, gevonden {len(cases)}/{len(set(ids))}"
        )
    ov = reg["overzicht_94"]
    ov_ids = [o["id"] for o in ov]
    if len(ov) != 94 or len(set(ov_ids)) != 94:
        f.append(
            f"[aantal] verwacht 94 unieke IDs, gevonden {len(ov)}/{len(set(ov_ids))}"
        )
    if set(ov_ids) != set(v2_all):
        f.append("[aantal] overzicht_94 IDs wijken af van basis/v2")
    if (
        not set(ids) <= set(ov_ids)
        or sum(o["in_acceptatiepakket_31"] for o in ov) != 31
    ):
        f.append("[aantal] overzicht markeert niet exact de 31 P-IDs als in pakket")
    if len(re.findall(r"^\| (C02-|CW-)", d["overzicht_md"], re.M)) != 94:
        f.append("[aantal] overzicht-94-ids.md bevat niet 94 rijen")
    secties = formulier_secties(form)
    if list(secties) != sorted(ids):
        f.append("[formulier] casuskoppen komen niet overeen met de 31 P-IDs")
    if reg.get("eerste_zes_voorgesteld") != EERSTE_ZES:
        f.append("[start] eerste zes wijken af")

    # 5. fixtures
    bm3_by = {s["id"]: s for s in bm3["sources"]}
    fx = man["fixtures"]
    fx_by = {x["id"]: x for x in fx}
    if len(fx) != 13 or set(fx_by) != set(bm3_by):
        f.append(
            f"[fixtures] verwacht 13 IDs gelijk aan basis/bronmanifest-v3, gevonden {len(fx)}"
        )
    if set(d["fixtures"]) != {x["pakketpad"] for x in fx}:
        f.append("[fixtures] bestanden in bronfixtures/ wijken af van manifest")
    for x in fx:
        b = d["fixtures"].get(x["pakketpad"])
        src = bm3_by.get(x["id"], {})
        if b is None:
            f.append(f"[fixtures] ontbreekt: {x['pakketpad']}")
            continue
        h = sha_bytes(b)
        if h != x["sha256"] or h != src.get("sha256") or len(b) != src.get("bytes"):
            f.append(
                f"[fixtures] {x['id']} hash/bytes wijken af van basis/bronmanifest-v3"
            )
        if (x["kind"] in SYNTHETISCH_KINDS) != x["synthetisch"]:
            f.append(f"[fixtures] {x['id']} synthetisch-label inconsistent met kind")
        tekst = b.decode("utf-8")
        for ps in x["passages"]:
            if ps["passage"] not in tekst:
                f.append(
                    f"[passage] {x['id']} '{ps['locator']}' niet letterlijk in fixture"
                )

    # 3+4. per casus: register versus basis, en formulier-sectie versus register
    for c in cases:
        cid = c["id"]
        h = c["historisch_ongewijzigd"]
        o6 = v6_p.get(cid)
        o2 = v2_all.get(cid, {}).get("historisch_record_ongewijzigd")
        if not o6 or not o2:
            f.append(f"[input] {cid} ontbreekt in basis-registers")
            continue
        for veld in (
            "title",
            "route",
            "priority",
            "source_ids",
            "input",
            "given",
            "when",
        ):
            if h[veld] != o6[veld] or h[veld] != o2[veld]:
                f.append(f"[input] {cid}.{veld} wijkt af van basis")
        if h["retrieval_recipe"] != o6.get("retrieval_recipe"):
            f.append(f"[input] {cid}.retrieval_recipe wijkt af van basis")
        hh = scenario_hash(o6)
        if hh != h["scenario_input_sha256"] or hh != o2["scenario_input_sha256"]:
            f.append(f"[input] {cid} scenario_input_sha256 niet reproduceerbaar")
        hv = c["historische_verwachtingen"]
        if (
            hv["then_v6"] != o6["then"]
            or hv["source_based_oracle"] != o6["source_based_oracle"]
            or hv["expert_question"] != o6["expert_question"]
        ):
            f.append(f"[verwachting] {cid} then/oracle/vraag wijkt af van basis/v6")
        if any(hv["gth_v1"][k] != o2[k] for k in ("G", "T", "H")):
            f.append(f"[verwachting] {cid} G/T/H wijkt af van basis/v2")
        if (
            hv["actuele_verwachting_v1_kruisreview"]
            != v2_all[cid]["actuele_verwachting_v1"]
        ):
            f.append(
                f"[verwachting] {cid} actuele_verwachting_v1 wijkt af van basis/v2"
            )
        for bb in c["bronbinding"]:
            if bb["sha256"] != fx_by.get(bb["id"], {}).get("sha256"):
                f.append(f"[bronbinding] {cid} {bb['id']} hash wijkt af van manifest")
        # 6. register-oordelen leeg, geen uitvoeringsclaim
        if not oordeel_leeg(c["expert"]):
            f.append(f"[oordeel] niet leeg: {cid}")
        if c.get("voorbeoordeling_codex_cowork") is not None:
            f.append(f"[oordeel] voorbeoordeling in register ingevuld: {cid}")
        bs = c["bewijsstatus"]
        if (
            bs["ketenuitvoering"] != "geen"
            or bs["modelkwaliteit_bewezen"]
            or bs["modelcontext_vastgelegd"]
        ):
            f.append(f"[bewijs] {cid} claimt uitvoering/modelkwaliteit")

        # 4. formulier: uitsluitend binnen de eigen casussectie
        if cid not in secties:
            f.append(f"[formulier] {cid} sectie ontbreekt")
            continue
        titel, sec = secties[cid]
        if titel != h["title"]:
            f.append(f"[formulier] {cid} titel wijkt af van register")
        if f"**Bronnen:** {', '.join(h['source_ids'])} ·" not in sec:
            f.append(f"[formulier] {cid} bronnenregel wijkt af van register")
        for k, v in h["input"].items():
            if f"- **{k}:** {toon(v)}\n" not in sec:
                f.append(f"[formulier] {cid} input.{k} niet exact in eigen sectie")
        if f"- **Gegeven:** {h['given']}\n" not in sec:
            f.append(f"[formulier] {cid} gegeven niet exact in eigen sectie")
        if f"- **Wanneer:** {h['when']}\n" not in sec:
            f.append(f"[formulier] {cid} wanneer niet exact in eigen sectie")
        if f"- **Deskundigenvraag:** {hv['expert_question']}\n" not in sec:
            f.append(f"[formulier] {cid} deskundigenvraag niet exact in eigen sectie")
        for bb in c["bronbinding"]:
            if f"sha256 `{bb['sha256']}`" not in sec:
                f.append(f"[formulier] {cid} hash {bb['id']} niet in eigen sectie")
            for ps in bb["passages"]:
                if md_quote(ps["passage"]) not in sec:
                    f.append(
                        f"[formulier] {cid} passage {bb['id']}/{ps['locator']} niet in eigen sectie"
                    )
        if (c["in_eerste_zes"]) != (f"## {cid} — {titel} ★ eerste zes" in sec):
            f.append(f"[formulier] {cid} eerste-zes-markering inconsistent")
    f.extend(formulier_oordelen_leeg(form))
    if re.search(r"^- \[[xX]\]", form, re.M):
        f.append("[formulier-oordeel] aangevinkt vakje aanwezig")
    for o in ov:
        if (
            not oordeel_leeg(o["expert"])
            or o["deskundig_gevalideerd_kruisreview"] is not False
        ):
            f.append(f"[oordeel] overzicht {o['id']} niet leeg")
    return f


# ---------------------------------------------------------------------------
# Zelftest: in-memory mutanten (schrijft niets)
# ---------------------------------------------------------------------------
def _vervang_in_sectie(form: str, cid: str, oud: str, nieuw: str) -> str:
    m = next(x for x in KOP_RE.finditer(form) if x.group(1) == cid)
    volgende = next((x for x in KOP_RE.finditer(form) if x.start() > m.start()), None)
    einde = volgende.start() if volgende else len(form)
    sec = form[m.start() : einde]
    if oud not in sec:
        msg = f"zelftest: '{oud[:40]}…' niet in sectie {cid}"
        raise RuntimeError(msg)
    return form[: m.start()] + sec.replace(oud, nieuw, 1) + form[einde:]


def zelftest(d: dict) -> int:
    reg = d["reg"]
    p01 = next(c for c in reg["cases"] if c["id"] == "C02-P01")
    p02 = next(c for c in reg["cases"] if c["id"] == "C02-P02")
    def01 = p01["historisch_ongewijzigd"]["input"]["definitie"]
    def02 = p02["historisch_ongewijzigd"]["input"]["definitie"]

    mutanten: list[tuple[str, str]] = []

    def mutant(naam: str, tag: str, fn) -> None:
        dd = copy.deepcopy(d)
        fn(dd)
        fouten = controleer(dd)
        hit = any(x.startswith(tag) for x in fouten)
        mutanten.append((naam, "ROOD" if hit else "GROEN (FOUT)"))
        for x in fouten[:3]:
            mutanten.append(("    " + x, ""))
        if not hit:
            mutanten.append(("    !! niet gedetecteerd", ""))

    # Codex P2-mutant: alleen in het formulier, P01-definitie vervangen door P02-definitie
    mutant(
        "formulier: P01-definitie vervangen door P02-definitie (tekst komt elders voor)",
        "[formulier] C02-P01 input.definitie",
        lambda dd: dd.update(
            form=_vervang_in_sectie(
                dd["form"],
                "C02-P01",
                f"- **definitie:** {def01}\n",
                f"- **definitie:** {def02}\n",
            )
        ),
    )

    # Volledige verwisseling P01<->P02 in het formulier
    def wissel(dd):
        tmp = "\x00TMP\x00"
        fm = _vervang_in_sectie(
            dd["form"],
            "C02-P01",
            f"- **definitie:** {def01}\n",
            f"- **definitie:** {tmp}\n",
        )
        fm = _vervang_in_sectie(
            fm, "C02-P02", f"- **definitie:** {def02}\n", f"- **definitie:** {def01}\n"
        )
        dd["form"] = _vervang_in_sectie(
            fm, "C02-P01", f"- **definitie:** {tmp}\n", f"- **definitie:** {def02}\n"
        )

    mutant(
        "formulier: definities P01 en P02 onderling verwisseld",
        "[formulier] C02-P0",
        wissel,
    )
    # Passage in verkeerde sectie: P31 lid-1-passage uit eigen sectie halen (staat nog in P01)
    lid1 = next(
        ps["passage"]
        for ps in p01["bronbinding"][0]["passages"]
        if ps["locator"] == "artikel 1:3 lid 1"
    )
    mutant(
        "formulier: passage lid 1 uit P31-sectie verwijderd (staat nog in P01)",
        "[formulier] C02-P31 passage",
        lambda dd: dd.update(
            form=_vervang_in_sectie(dd["form"], "C02-P31", md_quote(lid1), "> (weg)")
        ),
    )

    # Register: input vervormd
    def reg_input(dd):
        dd["reg"]["cases"][0]["historisch_ongewijzigd"]["input"]["definitie"] += " X"

    mutant("register: P01 input.definitie vervormd", "[input] C02-P01", reg_input)

    # Fixturebytes
    def fx(dd):
        dd["fixtures"]["bronfixtures/awb-3-2-20260815.txt"] += b"\n"

    mutant("fixture: awb-3-2 één byte toegevoegd", "[fixtures] S-AWB32", fx)

    # Oordeel in register
    def oordeel(dd):
        dd["reg"]["cases"][1]["expert"]["actor"] = "iemand"

    mutant("register: actor ingevuld bij P02", "[oordeel] niet leeg: C02-P02", oordeel)
    # Oordeel in formulier
    mutant(
        "formulier: acceptatievakje P03 aangevinkt",
        "[formulier-oordeel] C02-P03",
        lambda dd: dd.update(
            form=_vervang_in_sectie(
                dd["form"], "C02-P03", "- [ ] **Acceptatie**", "- [x] **Acceptatie**"
            )
        ),
    )
    # Sluitreview-mutant: meerregelige motivering (label leeg, tekst op vervolgregel)
    mutant(
        "formulier: P05 motivering op vervolgregel ('- **Motivering:**\\n  Bron steunt deze definitie.')",
        "[formulier-oordeel] C02-P05",
        lambda dd: dd.update(
            form=_vervang_in_sectie(
                dd["form"],
                "C02-P05",
                "- **Motivering:** \n",
                "- **Motivering:**\n  Bron steunt deze definitie.\n",
            )
        ),
    )
    # Vervolgtekst ná het laatste veld (Datum) binnen het blok
    mutant(
        "formulier: P06 extra alinea na Datum in het beoordelingsblok",
        "[formulier-oordeel] C02-P06",
        lambda dd: dd.update(
            form=_vervang_in_sectie(
                dd["form"],
                "C02-P06",
                "- **Datum:** \n",
                "- **Datum:** \n\nAkkoord, geen bezwaar.\n",
            )
        ),
    )
    # Laatste casus (sectie loopt tot bestandseinde): motivering ingevuld op de labelregel
    mutant(
        "formulier: P31 (laatste sectie) motivering op labelregel ingevuld",
        "[formulier-oordeel] C02-P31",
        lambda dd: dd.update(
            form=_vervang_in_sectie(
                dd["form"], "C02-P31", "- **Motivering:** \n", "- **Motivering:** ok\n"
            )
        ),
    )

    # Basis-snapshot vervormd
    def basis(dd):
        dd["basis"]["register_praktijk_v6"] += b" "

    mutant("basis: snapshot v6 gewijzigd", "[basis] snapshot gewijzigd", basis)

    schoon = controleer(d)
    print(
        "ZELFTEST — ongewijzigd pakket:",
        "GROEN" if not schoon else f"ROOD ({len(schoon)} afwijkingen)",
    )
    for x in schoon[:5]:
        print("   ", x)
    alles_rood = True
    for naam, status in mutanten:
        if status:
            print(f"  {status:14} {naam}")
            alles_rood &= status == "ROOD"
        else:
            print(f"                 {naam}")
    ok = not schoon and alles_rood
    print(
        "ZELFTEST",
        "GESLAAGD: alle mutanten rood, ongewijzigd groen." if ok else "MISLUKT.",
    )
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    pkg = Path(args[0]).resolve() if args else Path(__file__).resolve().parent
    d = laad(pkg)
    if "--zelftest" in argv:
        return zelftest(d)
    fouten = controleer(d)
    if fouten:
        print(f"INTEGRITEIT: {len(fouten)} afwijking(en) in {pkg.name}")
        for x in fouten:
            print("  -", x)
        return 1
    print(
        f"INTEGRITEIT OK ({pkg.name}) — structuur, 31 P + 94 unieke IDs, exacte input per casussectie, "
        "13 hashes, passages letterlijk, oordelen leeg, basis-snapshots ongewijzigd."
    )
    print(
        "Let op: integriteitscheck, geen acceptatietest en geen bewijs van app- of modelgedrag."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
