"""DEF-771 WP1 — bouwt het INT-02-skillcontract uit de dossierbronnen.

Exacte teksten worden rechtstreeks uit de bronbestanden gelezen (regel voor
regel, op vindbaar voorvoegsel), zodat niets is overgetypt of ingekort. Het
script faalt als een bronregel ontbreekt of meerdere keren voorkomt. Uitvoer:
de canonieke bron en de bytegelijke kopie in de opgegeven skillmap.

Gebruik: python wp1-contractopbouw.py <pad-naar-skills/>
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

DOSSIER = Path(__file__).resolve().parents[2]
VERSIE = "def771-int02/1"


def regels(pad: str) -> list[str]:
    return (DOSSIER / pad).read_text(encoding="utf-8").split("\n")


SYN = regels("gedeeld/gezamenlijke-synthese-v5.md")
REG = regels("gedeeld/gezamenlijk-casusregister-v5.md")
BES = regels("gedeeld/besluiten-chris-v1.md")
B3 = regels("b-codex-cli/onderzoek-b-v3.md")


def een(bron: list[str], voorvoegsel: str) -> str:
    treffers = [r for r in bron if r.startswith(voorvoegsel)]
    if len(treffers) != 1:
        raise SystemExit(f"{len(treffers)} treffers voor {voorvoegsel!r}")
    return treffers[0]


def na(regel: str, label: str) -> str:
    """Tekst na een label, zonder de tekst zelf te wijzigen."""
    if not regel.startswith(label):
        raise SystemExit(f"label {label!r} ontbreekt")
    return regel[len(label) :]


def cellen(regel: str) -> list[str]:
    return [c.strip() for c in regel.strip().strip("|").split(" | ")]


def rij(casus: str) -> str:
    c = cellen(een(REG, f"| {casus} |"))
    if len(c) != 6:
        raise SystemExit(f"{casus}: {len(c)} kolommen in het register")
    return f"| {c[0]} | {c[1]} | {c[2]} | {c[5]} |"


def besluitrij(nr: str) -> str:
    c = cellen(een(BES, f"| **{nr}** |"))
    return f"| {c[0]} | {c[1]} | {c[2]} |"


record = json.loads(
    (DOSSIER.parents[4] / "src/toetsregels/regels/INT-02.json").read_text("utf-8")
)
if record.get("contractversie") != VERSIE:
    raise SystemExit("record is niet aan deze contractversie gebonden")

NORM = na(een(SYN, "> Een definitie beschrijft wat het begrip is"), "> ")
toel = een(SYN, "| `INT-02.json` toelichting |")
ANNOTATIE = toel.split('met bronannotatie "', 1)[1].split('" |', 1)[0]
if record["toelichting"] != f"{NORM} {ANNOTATIE}":
    raise SystemExit("record-toelichting wijkt af van synthese §2/§6")

scope = een(B3, "(v3: RA-B-12) (v3: RA-B-13) De rollen blijven behouden.")
MATRIX_START = B3.index(een(B3, "| Veld | Zelf toetsobject voor INT-02?"))
matrix = []
for r in B3[MATRIX_START:]:
    if not r.startswith("|"):
        break
    matrix.append(r)

signalen = cellen(een(BES, "| **B3** |"))

goed, fout = record["goede_voorbeelden"], record["foute_voorbeelden"]
herkomst = {
    goed[0]: (
        "C01",
        "ASTRA *Geen beslisregel*, JUIST-voorbeeld; letterlijk bronpaar (`review_policy`)",
    ),
    goed[1]: (
        "C10",
        "ASTRA *Afleidingsregel*, synthetische ASTRA-parafrase; proefinvoer A-P1 `a-claude-cli/bewijs/p1-invoer.json` (INT02-C10)",
    ),
    goed[2]: (
        "C05",
        "synthetisch, historisch geval; proefinvoer A-P1 `a-claude-cli/bewijs/p1-invoer.json` (INT02-C05)",
    ),
    fout[0]: (
        "C02",
        "ASTRA *Geen beslisregel*, ONJUIST-voorbeeld; letterlijk bronpaar (`review_policy`)",
    ),
    fout[1]: (
        "C12",
        "synthetische bewerking van het Ppw-voorbeeld uit ASTRA *Beslisregel*, premisse actorinstructie; proefinvoer A-P1 `a-claude-cli/bewijs/p1-invoer.json` (INT02-C12)",
    ),
    fout[2]: (
        "C52",
        "synthetisch, premisse bevestigde voorschriftfunctie (alleen onder N-breed); proefinvoer B-P1 `b-codex-cli/bewijs/proeven-b-v1.py` (INT02-C52)",
    ),
}
if len(herkomst) != 6:
    raise SystemExit("recordvoorbeelden wijken af van de verwachte zes")

KOP = "| ID | Kern en bedoeling | T-referentie N-breed (N-eng indien anders) | Herkomst / bewijs |\n|---|---|---|---|"

delen = [
    "# INT-02 — begripscriterium tegenover beslisregel",
    "",
    f"**Contractversie:** `{VERSIE}` · **Datum:** 25 september 2026 · **Issue:** DEF-771",
    "",
    "Besloten door Chris op 25 september 2026 (besluiten B1–B6 hieronder; bron `gedeeld/besluiten-chris-v1.md` in het DEF-771-dossier `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/` van de Definitie-app). De N/G/T/H-teksten, de bronannotatie en de veldrollen zijn letterlijk overgenomen uit `gedeeld/gezamenlijke-synthese-v5.md` §1–§6 en `b-codex-cli/onderzoek-b-v3.md` §Q2/V02, de voorbeelden uit `gedeeld/gezamenlijk-casusregister-v5.md`. Waar overgenomen onderzoekstekst nog een voorstel of keuze noemt ([V], [K]), is de besluitentabel leidend. Canonieke bron: `definitie-toetsregels/references/int02-beslisregel.md`; `definitie-nederlandse-definities` draagt een byte-identieke, versiegebonden kopie in zijn eigen `references/` zodat dat pakket zelfstandig leesbaar is — wijzig alleen de canonieke bron en kopieer die opnieuw. Het app-regelrecord `src/toetsregels/regels/INT-02.json` is via het veld `contractversie` aan deze versie gebonden; uitleg, toelichting, toetsvraag en `example_pair_reason` staan hieronder letterlijk. Dit advies is geen opgeslagen review of vaststelling.",
    "",
    "**Uitvoeringsstatus.** Deze contractversie publiceert norm, regelrecord en skilltekst. De appzijde van G (de hardgecodeerde INT-02-instructie in de promptmodule) en van T (INT-02-passagehulp, S1-signalen, niet uitgevoerd bij lege kern of ontbrekende context, zichtbare reden in de UI) is daarmee nog niet uitgevoerd; tot dan geeft de app voor INT-02 een open beoordeling (`review_required`) met de toetsvraag als reden. Dit contract bewijst geen uitrol en geen kwaliteitswinst.",
    "",
    "## Besluiten van Chris (25 september 2026)",
    "",
    "| Nr | Keuze | Besluit Chris |",
    "|---|---|---|",
    *(besluitrij(nr) for nr in ("B1", "B2", "B3", "B4", "B5", "B6")),
    "",
    "Gevolg voor dit contract: N is de brede variant, als lokale operationalisering met bronsteun (B1); T volgt O1, de menselijke reviewroute zonder cijfer, en O2 is een afzonderlijk later besluit (B2); signalen zijn uitsluitend leeshulp (B3); dit bestand is het ene versiegebonden contract (B4); INT-02 kent geen zelfstandige vaststel- of exportblokkade (B5, DEF-831); er is geen INT-02-herstelroute (B6, DEF-832).",
    "",
    "**Bestaand beleid (bevestigd):** "
    + een(BES, "Context verplicht vóór genereren én toetsen"),
    "",
    "## Bron en herkomst",
    "",
    een(SYN, "Labels: [F] bronfeit"),
    "",
    een(SYN, "**De bron.** ASTRA INT-02:"),
    "",
    f"**Lokale bronannotatie (record-toelichting):** {ANNOTATIE}",
    "",
    "## N — norm (brede variant, B1)",
    "",
    f"> {NORM}",
    "",
    f"**Uitleg (record):** {record['uitleg']}",
    "",
    f"**Toetsvraag (record):** {record['toetsvraag']}",
    "",
    een(SYN, "**Uitzonderingen en grenzen [V]:**"),
    "",
    "## Veldrollen",
    "",
    een(SYN, "**Veldrollen.** Leidende bijlage:"),
    "",
    "Leidende matrix: B3 §Q2/V02 (`b-codex-cli/onderzoek-b-v3.md`), met de scopezin uit RA-B-12/13; de aanvullingen uit RB-A-07 zijn in de rijen verwerkt.",
    "",
    na(scope, "(v3: RA-B-12) (v3: RA-B-13) "),
    "",
    *matrix,
    "",
    "## G — generatie-instructie",
    "",
    een(SYN, "> Beschrijf wat het begrip is met de kenmerken"),
    "",
    een(SYN, "**Apptekst na G (uitvoeringsacceptatie, SC-07):**"),
    "",
    "## T — toetsinstructie, reviewerhulp en meldingen",
    "",
    "Besluit B2: O1 nu — de bestaande reviewroute (`judgment_review`, `excluded_from_score`) met INT-02-passagehulp; het oordeel blijft menselijk binnen de integrale expertbeoordeling, zonder cijfer. O2 (scoreloze AI-beoordeling) is een afzonderlijk later besluit met onafhankelijke goldset. De meldingen en de statusmapping hieronder gelden voor de menselijke beoordeling en voor een eventueel later gekozen O2.",
    "",
    een(SYN, "**T-tekst (reviewer en eventuele O2)"),
    "",
    een(SYN, "**Reviewerhulp (O1, exacte tekst):**"),
    "",
    een(SYN, "**Appmeldingen [V, B3 V06]:**"),
    "",
    f"**Signaalbeleid — besluit B3: {signalen[2].strip('*')}.** {signalen[3]} De concrete markerlijst is in deze contractversie niet vastgesteld.",
    "",
    "Onderzoekstekst vóór het besluit (synthese §4):",
    "",
    een(SYN, "**Signaalbeleid [K2b, SC-12].**"),
    "",
    "## H — toelichtingsvoorstel, geen INT-02-herstelroute (B6, DEF-832)",
    "",
    "Er is geen INT-02-herstelroute (DEF-832). Toetsen wijzigt de tekst nooit. H specificeert uitsluitend een afzonderlijk gevraagd toelichtingsvoorstel als nieuw concept, met de diagnose en de stopregels hieronder.",
    "",
    een(SYN, "*Besluit Chris 25-09-2026 (K5; DEF-832):*"),
    "",
    een(SYN, "Diagnose vóór advies:"),
    "",
    een(SYN, "Voor INT-02 betreft H uitsluitend"),
    "",
    "## Voorbeelden",
    "",
    "Ontwerpverwachtingen uit het gezamenlijke casusregister v5, geen gemeten model- of beoordelaarskwaliteit en geen goldset. Kern, T-referentie en herkomst zijn letterlijk uit het register overgenomen; de exacte proefinvoer staat in het genoemde bewijsbestand. Uit het register:",
    "",
    "- Referentieoordelen voor voorschrift/discretie zijn conditioneel: "
    + een(REG, "**Normversies.**").split(
        "Referentieoordelen voor voorschrift/discretie zijn conditioneel: ", 1
    )[1],
    "- "
    + een(REG, "**Algemene voorwaarde (SC-05).**").split(". Ontbreekt", 1)[0]
    + ".",
    "- " + een(REG, "**T-referentie:**"),
    "",
    "### Positief (✅)",
    "",
    KOP,
    *(rij(c) for c in ("C10", "C05", "C19", "C53", "C112", "C113", "C116")),
    "",
    "### Negatief (❌)",
    "",
    KOP,
    *(rij(c) for c in ("C02", "C12", "C52", "C105", "C114")),
    "",
    "### Grens",
    "",
    KOP,
    *(rij(c) for c in ("C16", "C24", "C55", "C58", "C107")),
    "",
    "### Regelrecord",
    "",
    "Het record draagt naast het letterlijke ASTRA-paar (`review_policy`) uitsluitend de functievoorbeelden uit synthese §6. Hun herkomst staat hier, niet in de voorbeeldtekst, omdat die tekst in de generatieprompt wordt weergegeven. De vorm `term: tekst` volgt het ASTRA-paar; term en tekst komen uit de proefinvoer.",
    "",
    "| Lijst | Voorbeeldtekst (exact) | Casus | Herkomst |",
    "|---|---|---|---|",
    *(
        f"| goede_voorbeelden | {v} | {herkomst[v][0]} | {herkomst[v][1]} |"
        for v in goed
    ),
    *(
        f"| foute_voorbeelden | {v} | {herkomst[v][0]} | {herkomst[v][1]} |"
        for v in fout
    ),
    "",
    f"`example_pair_reason`: {record['runtime_contract']['example_pair_reason']}",
    "",
    "## Bewijsgrenzen",
    "",
    'Dit contract is tekst- en contractgelijkheid (bewaakt door `tests/unit/validation/test_def771_int02_contract.py` in de Definitie-app), geen menselijke normvalidatie, modelmeting of effectbewijs. Status na implementatie zonder effectbewijs: "geïmplementeerd; kwaliteitswinst nog niet vastgesteld" (synthese §8). Uit synthese §10:',
    "",
    een(SYN, "Offline serviceproeven met synthetische tekst"),
    "",
    "## Geparkeerd",
    "",
    een(BES, "INT-10 (`indien`-patroon;"),
    "",
]

tekst = "\n".join(delen)
if "  \n" in tekst or " \n" in tekst:
    raise SystemExit("regel met afsluitende spatie")

doel = Path(sys.argv[1])
canoniek = doel / "definitie-toetsregels/references/int02-beslisregel.md"
kopie = doel / "definitie-nederlandse-definities/references/int02-beslisregel.md"
for pad in (canoniek, kopie):
    if pad.exists() and "--vervang-eigen-uitvoer" not in sys.argv:
        raise SystemExit(f"{pad} bestaat al; niet overschreven")
canoniek.write_text(tekst, encoding="utf-8")
shutil.copyfile(canoniek, kopie)
print(canoniek, len(tekst.split("\n")), "regels")
