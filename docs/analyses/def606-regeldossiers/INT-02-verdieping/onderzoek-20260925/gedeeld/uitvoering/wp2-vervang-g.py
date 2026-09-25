"""DEF-771 WP2: vervang uitsluitend de INT-02-instructie door de exacte G uit synthese v5 §3."""

import textwrap

SYN = (
    "docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/"
    "gedeeld/gezamenlijke-synthese-v5.md"
)
MODULE = "src/services/prompts/modules/json_based_rules_module.py"
OUD = (
    '            "INT-02": "Vermijd voorwaardelijke formuleringen zoals '
    "'indien', 'mits', 'tenzij', 'alleen als'\","
)

g = [
    r
    for r in open(SYN, encoding="utf-8").read().splitlines()
    if r.startswith("> Beschrijf wat het begrip is met de kenmerken")
]
assert len(g) == 1
g = g[0][2:]
delen = textwrap.wrap(
    g, width=68, break_long_words=False, break_on_hyphens=False, drop_whitespace=False
)
assert "".join(delen) == g
regels = [
    "            # DEF-771 (B4): G uit synthese v5 §3 na SC-C-02; zelfde norm als",
    "            # INT-02.json en het skillcontract def771-int02/1.",
    '            "INT-02": (',
]
for d in delen:
    assert '"' not in d and "\\" not in d
    regels.append(f'                "{d}"')
regels.append("            ),")

src = open(MODULE, encoding="utf-8").read()
assert src.count(OUD) == 1, "oude INT-02-regel niet eenduidig gevonden"
open(MODULE, "w", encoding="utf-8").write(src.replace(OUD, "\n".join(regels)))
print(len(regels), "regels")
