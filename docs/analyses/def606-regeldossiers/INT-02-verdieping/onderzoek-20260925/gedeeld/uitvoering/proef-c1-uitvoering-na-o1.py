"""DEF-771 WP3 — nieuwe C1-replay na O1; historische proef en uitkomsten blijven ongemoeid.

Bron: a-cowork/bewijs/proef-c1-verwachtingen.json (alleen gelezen) plus C13, C23,
C50, C59 en C105. Elk geval draait met synthetische context (RR-route) en
contextloos (NE-route; C50 contextloos = C56). Nieuwe verwachtingen staan hier
vóór de run vast: historische signalen, behalve de goedgekeurde S1-afwijkingen.
De NE-reden wordt uit het publieke resultaat gelezen (rule_results['INT-02'],
contract 2.2.0) en vergeleken met de hier vastgelegde exacte melding.
Promptrendering met juridische context (anders toont de module INT-02 niet).
Offline-bootstrap vóór applicatie-imports; geen modelcalls of productiedata.
Exit 0 alleen als alle gevallen overeenkomen, citaten kloppen en G rendert.
Gebruik (app-root): .venv/bin/python <dit script> <nieuw-uitvoerpad.json>
"""

import asyncio
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[7]
sys.path[:0] = [str(REPO), str(REPO / "src")]
from tests import offline_bootstrap

offline_bootstrap.install()

HIST = Path(__file__).parents[2] / "a-cowork/bewijs/proef-c1-verwachtingen.json"
EXTRA = [
    (
        "INT02-C13",
        "vervallenverklaring",
        "besluit waarmee de bevoegde autoriteit een vergunning intrekt wanneer zij dat na afweging van de belangen van de houder evenredig acht.",
        [],
    ),
    ("INT02-C23", "toegang", "Toegang:", []),
    (
        "INT02-C50",
        "stelselmatige dader",
        "Persoon die als stelselmatige dader geldt indien hij in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld.",
        [r"\bindien\b"],
    ),
    (
        "INT02-C59",
        "beslisregel",
        "beslisregel: Algoritme waarvoor oordeelsvorming nodig is.",
        [],
    ),
    ("INT02-C105", "toelating", "De medewerker laat de aanvrager toe.", []),
]
S1_AFWIJKING = {
    "INT02-C02": [r"\bmoet\b"],
    "INT02-C82": [r"\btenzij\b", r"\bvan\s+oordeel\s+is\b"],
    "INT02-C83": [r"\bnaar\s+eigen\s+inzicht\b", r"\bredelijk\s+acht\b"],
}
ZONDER_KERN = {"INT02-C06", "INT02-C23"}
NE = "INT-02 — Niet uitgevoerd: {kern/context} ontbreekt. Er is geen inhoudelijk oordeel."
G_BEGIN = "- **Instructie:** Beschrijf wat het begrip is met de kenmerken"
CONTEXT = {"organisatorische_context": ["Synthetische proefcontext DEF-771"]}
BRONNEN = [
    "src/services/validation/evaluators/judgment_review.py",
    "src/services/validation/modular_validation_service.py",
    "src/services/prompts/modules/json_based_rules_module.py",
    "src/toetsregels/regels/INT-02.json",
]


def sha(pad: Path) -> str:
    return hashlib.sha256(pad.read_bytes()).hexdigest()


async def toets(gevallen):
    from services.validation.modular_validation_service import ModularValidationService
    from toetsregels.manager import get_toetsregel_manager

    svc, uit = ModularValidationService(get_toetsregel_manager(), None, None), []
    for gid, begrip, tekst, origineel, signalen in gevallen:
        for variant, context in (("met_context", CONTEXT), ("zonder_context", {})):
            r = await svc.validate_definition(
                begrip=begrip, text=tekst, context=context
            )
            item = {i["rule_id"]: i for i in r["review_required"]}.get("INT-02") or {}
            reden = item.get("reason", "")
            grond = [
                naam
                for naam, weg in (
                    ("kern", gid in ZONDER_KERN),
                    ("context", variant == "zonder_context"),
                )
                if weg
            ]
            nieuw = {
                "status": "not_evaluated" if grond else "review_required",
                "signals": [] if grond else sorted(signalen),
                "ne_reden": (
                    NE.replace("{kern/context}", " en ".join(grond)) if grond else None
                ),
            }
            deel = (r["rule_results"].get("INT-02") or {}).get("parts") or [{}]
            werkelijk = {
                "status": r["rule_statuses"].get("INT-02"),
                "ne_reden": deel[0].get("reason"),
                "reason": reden or None,
                "signals": sorted(item.get("signals", [])),
                "violation": any(v.get("code") == "INT-02" for v in r["violations"]),
                "passages": [
                    [p, int(s), int(e)]
                    for p, (s, e) in zip(
                        re.findall(r"de passage '(.+?)' een kenmerk", reden, re.S),
                        re.findall(r"getoetste kern: (\d+)–(\d+) ", reden),
                        strict=True,
                    )
                ],
            }
            uit.append(
                {
                    "id": gid,
                    "casus": (
                        "INT02-C56 (contextloze variant van C50)"
                        if (gid, variant) == ("INT02-C50", "zonder_context")
                        else gid
                    ),
                    "variant": variant,
                    "context": context,
                    "tekst": tekst,
                    "verwacht_origineel_T_main": origineel,
                    "verwacht_nieuw": nieuw,
                    "werkelijk": werkelijk,
                    "citaten_kloppen": all(
                        tekst[s:e] == p for p, s, e in werkelijk["passages"]
                    ),
                    "match": nieuw == {k: werkelijk[k] for k in nieuw}
                    and not werkelijk["violation"],
                }
            )
    return uit


def render():
    from services.definition_generator_config import UnifiedGeneratorConfig
    from services.definition_generator_context import EnrichedContext
    from services.prompts.modules.base_module import ModuleContext
    from services.prompts.modules.json_based_rules_module import JSONBasedRulesModule

    uit = {}
    for include in (True, False):
        mod = JSONBasedRulesModule("INT", "integrity_rules", "INT", "🔒", "INT", 70)
        mod.initialize({"include_examples": include})
        ctx = ModuleContext(
            begrip="proef",
            enriched_context=EnrichedContext(
                base_context={"juridisch": ["Strafrecht"]},
                sources=[],
                expanded_terms={},
                confidence_scores={},
                metadata={},
            ),
            config=UnifiedGeneratorConfig(),
            shared_state={},
        )
        blok = mod.execute(ctx).content.split("🔹 **INT-02")[1].split("🔹 **INT-03")[0]
        uit[f"include_examples={include}"] = ("🔹 **INT-02" + blok).splitlines()
    return uit


def main() -> int:
    doel = Path(sys.argv[1])
    if doel.exists():
        raise SystemExit(f"{doel} bestaat al; kies een nieuwe pogingnaam")
    hist = json.loads(HIST.read_text("utf-8"))["gevallen"]
    gevallen = [
        (
            g["id"],
            g["begrip"],
            g["tekst"],
            g["verwacht_T_main"],
            S1_AFWIJKING.get(g["id"], g["verwacht_T_main"]["signals"]),
        )
        for g in hist
    ]
    gevallen += [(i, b, t, None, s) for i, b, t, s in EXTRA]
    git = ["git", "-C", str(REPO)]
    uit = {
        "proef": "C1 na O1 (DEF-771 WP3)",
        "commando": " ".join(sys.argv),
        "commit": subprocess.run(
            [*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        ).stdout.strip(),
        "werkboom_gewijzigd": subprocess.run(
            [*git, "status", "--porcelain", "--", "src", "tests"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.splitlines(),
        "hashes_voor_run": {p: sha(REPO / p) for p in BRONNEN}
        | {"script": sha(Path(__file__)), "historische_verwachtingen": sha(HIST)},
        "start_utc": datetime.now(UTC).isoformat(),
    }
    uit["toetsing"] = asyncio.run(toets(gevallen))
    uit["prompt_rendering"] = render()
    uit["eind_utc"] = datetime.now(UTC).isoformat()
    uit["samenvatting"] = {
        "g_gerenderd": {
            k: any(r.startswith(G_BEGIN) for r in v)
            for k, v in uit["prompt_rendering"].items()
        },
        "uitvoeringen": len(uit["toetsing"]),
        "match": sum(t["match"] for t in uit["toetsing"]),
        "mismatch": [
            f"{t['id']}/{t['variant']}" for t in uit["toetsing"] if not t["match"]
        ],
        "citaatfouten": [t["id"] for t in uit["toetsing"] if not t["citaten_kloppen"]],
    }
    samenvatting = uit["samenvatting"]
    uit["exitstatus"] = int(
        bool(samenvatting["mismatch"] or samenvatting["citaatfouten"])
        or not all(samenvatting["g_gerenderd"].values())
    )
    doel.write_text(json.dumps(uit, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps(samenvatting, ensure_ascii=False))
    return uit["exitstatus"]


if __name__ == "__main__":
    raise SystemExit(main())
