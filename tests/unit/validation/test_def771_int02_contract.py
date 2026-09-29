"""INT-02 (DEF-771, WP1): regelrecord en skillcontract als één versiegebonden contract.

Besluit B4 van Chris (25 september 2026, `besluiten-chris-v1.md`): record en
beide skills worden afgeleid uit één bronbestand met versie (ESS-03-patroon).
De canonieke bron is `definitie-toetsregels/references/int02-beslisregel.md`
in de beheerde skillrepository; `definitie-nederlandse-definities` draagt een
bytegelijke kopie.

Twee soorten tests:

- Recordtests (altijd): het record draagt exact de vervangteksten uit
  synthese v5 §6, bewaart het letterlijke ASTRA-paar en `review_policy`, en
  draagt de contractversie. De constanten hieronder zijn een **dossierkopie**
  van synthese v5 §2/§6, niet de canonieke bron.
- Skilltests: lezen de beheerde skills uit een tweede repository. Zet daarvoor
  `DEF771_SKILLS_ROOT` op de map `skills/` van `_claude-global-setup`. Zonder
  die variabele worden deze tests expliciet overgeslagen met reden (zichtbaar
  via `-ra`); een gezet maar ongeldig pad faalt.

Wat deze tests niet bewijzen: normjuistheid, modelgedrag, promptrendering
(WP2), reviewerhulp of signalen in de app (WP3) of een uitgerolde skill.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from toetsregels.runtime_contract import build_rule_record

pytestmark = [pytest.mark.unit]

REGEL = Path(__file__).resolve().parents[3] / "src/toetsregels/regels/INT-02.json"
CONTRACTVERSIE = "def771-int02/2"
CONTRACT = "definitie-toetsregels/references/int02-beslisregel.md"
KOPIE = "definitie-nederlandse-definities/references/int02-beslisregel.md"

# --- Dossierkopie van synthese v5 §2 en §6 (niet canoniek) -------------------
NORMTEKST = "Een definitie beschrijft wat het begrip is met de kenmerken die bepalen wat ertoe behoort. Zij is geen handelingsvoorschrift of procedure voor een actor en bevat geen discretionaire beslisregel die een afweging over handelen of rechtsgevolg voorschrijft. Begripsbepalende criteria, voorwaarden en uitzonderingen zijn toegestaan, ook in voorwaardelijke zinsvorm ('indien', 'mits', 'tenzij', 'alleen als', 'voor zover'); een afleidbaar begrip wordt juist gedefinieerd met de deterministische afleiding uit de relevante feiten; een gebonden handelingsopdracht is niet enkel door haar determinisme een afleidingsregel. Dat een kenmerk door een mens moet worden waargenomen of beoordeeld, maakt het niet tot een beslisregel. Een bevoegdheid, beslissing, procedure of constitutief rechtsgevolg als begripskenmerk beschrijven is op zichzelf geen overtreding; beoordeel of de definitiekern zelf het handelen voorschrijft of de afweging als beslisregel uitvoert. Woorden als 'indien' of 'moet' bewijzen geen overtreding en hun afwezigheid bewijst geen naleving."
BRONANNOTATIE = "De uitsluiting van zelfstandige actorvoorschriften/procedures is lokale operationalisering; ASTRA benoemt discretionaire beslisregels en staat afleidingsregels toe, verplicht bij afleidbare begrippen; de theoretische aansluiting en het voorbeeld zijn bij ASTRA redactionele bespreekpunten."
UITLEG = "Een definitie beschrijft het begrip met kenmerken die bepalen wat ertoe behoort; zij is geen handelingsvoorschrift of procedure voor een actor en bevat geen discretionaire beslisregel. Criteria, voorwaarden en deterministische afleidingen zijn toegestaan, ook in voorwaardelijke vorm. Een bevoegdheid, beslissing, procedure of constitutief rechtsgevolg als begripskenmerk beschrijven is op zichzelf geen overtreding."
TOETSVRAAG = "Bakenen de relevante passages het begrip af met criteria of een deterministische afleiding, zonder als handelingsvoorschrift, procedure of discretionaire beslisregel te functioneren?"
BRONDOCUMENT = "ASTRA (verwijst naar DBT §4.2; DBT niet rechtstreeks onderzocht)"
EXAMPLE_PAIR_REASON = "Het ASTRA-paar verschilt in het modale werkwoord moet. Dat raakt ARAI-04 en kan onder de bevestigde voorschriftlezing ook de lokale INT-02-functiegrens raken. Onder de enge discretionaire variant is zonder discretionaire grond geen INT-02-afkeur bewezen. Het paar blijft een reviewgeval; ASTRA noemt het weinig sprekend. Het woord bewijst op zichzelf geen actorfunctie, rolomkering of betekenisbehoud bij verwijdering."
REF_TOETSREGELS = "Beschrijf begripscriteria en onderbouwde afleidingen; geef geen actorvoorschrift of discretionaire beslisregel als kern. Voorwaardelijke zinsvorm is toegestaan; een bevoegdheid, beslissing of rechtsgevolg als kenmerk beschrijven mag. N/G/T/H: references/int02-beslisregel.md"
REF_NEDERLANDS = "- Beslisregels en voorschriften (INT-02): geen handelingsvoorschrift of discretionaire beslisregel als definitiekern. Behoud begripscriteria, voorwaarden en deterministische afleidingen, ook in voorwaardelijke vorm. Menselijke beoordeling van een kwalitatief of constitutief kenmerk is op zichzelf geen beslisregel; een verplichting, bevoegdheid, beslissing, procedure of rechtsgevolg beschrijven mag. Zie references/int02-beslisregel.md."
SKILL_DUIDING = "INT-02 levert geen kwaliteitscijfer; de huidige appuitkomst is een open beoordeling. De totaalscore is bij besluit van 15 september 2026 definitief vervallen als kwaliteitscijfer, acceptatiegrond en hersteldriver. Het actieve JSON-runtimecontract bepaalt de evaluator; de losse INT02Validator is geen bewijs van de actieve uitvoering."

# ASTRA-bronpaar (C01/C02) en functievoorbeelden uit §6 met de exacte
# proefinvoer (A-P1 `p1-invoer.json`: C05, C10, C12; B-P1 `proeven-b-v1.py`: C52).
ASTRA_JUIST = "transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken."
ASTRA_ONJUIST = "transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken."
C10 = "stelselmatige dader: persoon die in de vijf jaar voorafgaand aan het laatste feit drie maal wegens een misdrijf onherroepelijk is veroordeeld."
C05 = "even getal: Geheel getal dat zonder rest door twee deelbaar is."
C12 = "weigering: besluit waarmee de bevoegde autoriteit een aanvraag afwijst, tenzij zij van oordeel is dat de aanvrager daardoor onevenredig zou worden benadeeld."
C52 = "aanvraag: Aanvraag die de behandelaar moet afwijzen bij een ontbrekende bijlage."

VOORBEELD_IDS = {
    "Positief": ("C10", "C05", "C19", "C53", "C112", "C113", "C116"),
    "Negatief": ("C02", "C12", "C52", "C105", "C114"),
    "Grens": ("C16", "C24", "C55", "C58", "C107"),
}


def _record() -> dict:
    return json.loads(REGEL.read_text(encoding="utf-8"))


# --- Recordtests ------------------------------------------------------------


def test_record_draagt_exacte_teksten_uit_synthese_par6():
    data = _record()
    assert data["uitleg"] == UITLEG
    assert data["toelichting"] == f"{NORMTEKST} {BRONANNOTATIE}"
    assert data["toetsvraag"] == TOETSVRAAG
    assert data["type"] == "gehele definitie"
    assert data["brondocument"] == BRONDOCUMENT
    assert data["runtime_contract"]["example_pair_reason"] == EXAMPLE_PAIR_REASON


def test_record_bewaart_astra_paar_review_policy_en_evaluator():
    data = _record()
    contract = data["runtime_contract"]
    assert data["goede_voorbeelden"][0] == ASTRA_JUIST
    assert data["foute_voorbeelden"][0] == ASTRA_ONJUIST
    assert contract["example_pair_policy"] == "review_policy"
    assert contract["evaluator"] == "judgment_review"
    assert contract["score_policy"] == "excluded_from_score"
    # WP3 (K-9): context is vereiste invoer; zonder context niet uitgevoerd.
    assert contract["required_inputs"] == ["definition_text", "context_lists"]
    build_rule_record("INT-02", data)


def test_record_voegt_uitsluitend_de_functievoorbeelden_uit_par6_toe():
    data = _record()
    assert data["goede_voorbeelden"] == [ASTRA_JUIST, C10, C05]
    assert data["foute_voorbeelden"] == [ASTRA_ONJUIST, C12, C52]


def test_record_is_gebonden_aan_de_contractversie():
    assert _record()["contractversie"] == CONTRACTVERSIE


# --- Skilltests (tweede repository) -----------------------------------------


@pytest.fixture(scope="module")
def skills() -> Path:
    waarde = os.environ.get("DEF771_SKILLS_ROOT")
    if not waarde:
        pytest.skip(
            "DEF771_SKILLS_ROOT niet gezet: skillcontract (tweede repository "
            "_claude-global-setup) niet gecontroleerd"
        )
    pad = Path(waarde)
    if not (pad / "definitie-toetsregels").is_dir():
        pytest.fail(f"DEF771_SKILLS_ROOT={pad} bevat geen definitie-toetsregels/")
    return pad


@pytest.fixture(scope="module")
def contract(skills: Path) -> str:
    return (skills / CONTRACT).read_text(encoding="utf-8")


def test_contract_draagt_versie_en_datum_gelijk_aan_record(contract: str):
    versie = re.search(r"\*\*Contractversie:\*\* `([^`]+)`", contract)
    assert versie is not None
    assert versie.group(1) == CONTRACTVERSIE == _record()["contractversie"]
    assert "25 september 2026" in contract.split("\n## ", 1)[0]


def test_kopie_in_nederlandse_definities_is_bytegelijk(skills: Path):
    assert (skills / KOPIE).read_bytes() == (skills / CONTRACT).read_bytes()


def test_record_teksten_staan_letterlijk_in_het_canonieke_contract(contract: str):
    data = _record()
    for veld in ("uitleg", "toetsvraag"):
        assert data[veld] in contract, veld
    assert NORMTEKST in contract
    assert BRONANNOTATIE in contract
    assert data["runtime_contract"]["example_pair_reason"] in contract
    for voorbeeld in data["goede_voorbeelden"] + data["foute_voorbeelden"]:
        assert voorbeeld in contract, voorbeeld


def test_contract_bevat_n_g_t_h_en_geen_herstelroute(contract: str):
    for kop in ("## N ", "## Veldrollen", "## G ", "## T ", "## H ", "## Voorbeelden"):
        assert f"\n{kop}" in contract, kop
    assert "DEF-832" in contract
    assert "geen INT-02-herstelroute" in contract


def test_contract_publiceert_de_s1_markers_uit_het_record(contract: str):
    for patroon in _record()["herkenbaar_patronen"][7:]:
        assert f"`{patroon}`" in contract, patroon


@pytest.mark.parametrize("groep", sorted(VOORBEELD_IDS))
def test_contract_bevat_voorbeelden_per_groep(contract: str, groep: str):
    sectie = contract.split(f"\n### {groep}", 1)[1].split("\n### ", 1)[0]
    for casus in VOORBEELD_IDS[groep]:
        assert f"\n| {casus} |" in sectie, casus


def test_reference_zinnen_vervangen(skills: Path):
    toetsregels = (skills / "definitie-toetsregels/reference.md").read_text("utf-8")
    assert f"| INT-02 | Geen beslisregel | midden | {REF_TOETSREGELS} |" in toetsregels
    assert "Vermijd voorwaardelijke formuleringen" not in toetsregels
    nederlands = (skills / "definitie-nederlandse-definities/reference.md").read_text(
        "utf-8"
    )
    assert f"\n{REF_NEDERLANDS}\n" in nederlands
    assert "- Voorwaardelijke formuleringen:" not in nederlands


@pytest.mark.parametrize(
    "skill", ["definitie-toetsregels", "definitie-nederlandse-definities"]
)
def test_skill_md_bevat_gericht_int02_blok(skills: Path, skill: str):
    tekst = (skills / skill / "SKILL.md").read_text("utf-8")
    blok = tekst.split("\n## INT-02 — begripscriterium tegenover beslisregel\n", 1)
    assert len(blok) == 2
    blok = blok[1].split("\n## ", 1)[0]
    assert "(references/int02-beslisregel.md)" in blok
    assert CONTRACTVERSIE in blok
    assert SKILL_DUIDING in blok
    assert "Toetsen wijzigt nooit tekst." in blok
    assert "Skilladvies is geen opgeslagen expertbeoordeling." in blok
