---
owner: validation
status: draft
last_verified: 2025-09-16
applies_to: definitie-app@current
canonical: true
---

# V2 Validator Migratieplan per Toetsregel

Doel: elke bestaande toetsregel (JSON + legacy Python) migreren naar de V2‑validator (`ModularValidationService`) zonder backwards‑compatibility shims, conform CLAUDE.md, README (EPIC‑010 gates), V2‑contracten en schema.sql.

Bronnen
- JSON regels: `src/toetsregels/regels/*.json`
- Legacy Python: `src/toetsregels/regels/*.py` en (soms) `src/toetsregels/validators/*.py`
- V2 validator: `src/services/validation/modular_validation_service.py`
- Orchestrator: `src/services/orchestrators/validation_orchestrator_v2.py`
- Loader/manager: `src/toetsregels/loader.py`, `src/toetsregels/manager.py`
- Legacy interpreter referentie: `src/validation/definitie_validator.py`

Architectuurkeuzes (V2)
- Geen aanroep van legacy validators; logica wordt in V2 generiek geïnterpreteerd op basis van JSON + beperkte regel‑specifieke uitbreidingen.
- Schema‑conforme output (TypedDict) met deterministische scores en gesorteerde violations.
- Regelseverity/gewicht: afgeleid uit JSON (`aanbeveling`, `prioriteit`), identiek aan `definitie_validator.ValidationRegelInterpreter` waar zinvol.

Algemene migratiestappen per regel
1) JSON inlezen via ToetsregelManager (al aanwezig). Zorg dat `loader.load_toetsregels()` de `id` overschrijft naar bestandsnaam (hyphenated, gebeurt al).
2) Bepaal evaluatietype:
   - forbidden_patterns (regex) → FORBIDDEN_PATTERN violation
   - required_elements (afgeleid; bijv. ESS‑02) → MISSING_ELEMENT
   - structure_checks (afgeleid) → STRUCTURE_ISSUE
3) Severity en weight bepalen op basis van JSON (`aanbeveling`, `prioriteit`).
4) Scoreberekening: startscore 1.0; aftrek per overtreding met multiplier o.b.v. severity (zoals in legacy interpreter), bodemen op 0.0.
5) Violations deterministisch sorteren op `code`.
6) Tests: unit (rule‑specifiek) + integratie (end‑to‑end via orchestrator V2).

Bekende extra patronen (uit legacy interpreter) — samenvoegen
- CON-01, ESS-01, INT-01, INT-03, STR-01, STR-02 hebben aanvullende regexen in `validation/definitie_validator.py` (mappen naar `additional_patterns`). Deze meenemen in de V2‑evaluatie.

Specifieke notitie ESS‑02
- Ondersteun metadata‑override (marker) en eenduidigheid (exact één categorie). Zie `src/toetsregels/validators/ESS_02.py` voor referentiegedrag.

---

## ARAI‑regels

ARAI‑01 … ARAI‑06 (formele/algemene regels)
- Bestanden: `src/toetsregels/regels/ARAI-0X.json` (+ `.py`)
- Stappen per regel:
  1) Lees JSON en extraheer `herkenbaar_patronen` → `FORBIDDEN_PATTERN` checks in V2.
  2) Bepaal severity/weight uit JSON.
  3) Voeg tests toe: 2× foute/2× goede voorbeelden uit JSON (unit), integratie via orchestrator.
  4) Als Python‑module extra detectie bevat t.o.v. JSON, port minimalistisch als extra regex.

Regels: ARAI-01, ARAI-02, ARAI-02SUB1, ARAI-02SUB2, ARAI-03, ARAI-04, ARAI-04SUB1, ARAI-05, ARAI-06.

---

## CON‑regels

CON‑01 — Eigen definitie voor elke context (zonder expliciet te benoemen)
- JSON: `src/toetsregels/regels/CON-01.json`
- Extra: aanvullende patronen in legacy interpreter (UI/juridische namen, “volgens het Wetboek…”).
- Stappen:
  1) Merge JSON‑patronen + aanvullende regexen → één lijst in V2.
  2) FORBIDDEN_PATTERN violations met `category="samenhang"`.
  3) Tests: JSON goede/foute voorbeelden + extra negatieve case (OM/DJI/“in de context van”).

CON‑02 — Authentieke bron (indien van toepassing)
- JSON: `src/toetsregels/regels/CON-02.json`
- Stappen:
  1) Definieer `required_elements=["authentieke_bron_basis"]` → `_has_authentic_source_basis` equivalent in V2.
  2) MISSING_ELEMENT bij ontbreken; severity volgens JSON.
  3) Tests: met/zonder bronindicatoren (“volgens”, “conform”, “wet/regeling”).

---

## ESS‑regels

ESS‑01 — Essentie, niet doel
- JSON: `src/toetsregels/regels/ESS-01.json`
- Extra: aanvullende patronen ("om te", "met als doel", …) al in JSON; legacy voegt o.a. "gericht op" toe (al aanwezig).
- Stappen:
  1) FORBIDDEN_PATTERN op alle doelgerichte frasen.
  2) Tests: JSON goede/foute voorbeelden, plus randgeval “ten behoeve van”.

ESS‑02 — Ontologische categorie expliciteren
- JSON: `src/toetsregels/regels/ESS-02.json`; Python: `src/toetsregels/validators/ESS_02.py` (referentie‑gedrag) en `src/toetsregels/regels/ESS-02.py`.
- Stappen:
  1) Implementatie in V2: 
     - metadata override: `context.marker ∈ {type, exemplaar/particulier, proces/activiteit, resultaat/uitkomst}` → direct pass (1.0).
     - Regexhits per categorie uit JSON; precies één categorie → pass; meerdere → ambigu‑violation; geen → missing‑element/structure‑issue.
  2) Violations:
     - `CONTENT_ISSUE` bij ambiguïteit; `MISSING_ELEMENT` bij geen marker; severity=critical indien JSON `verplicht`+`hoog`.
  3) Tests: één‑hit, multi‑hit (fail), none‑hit (fail), metadata override (pass).

ESS‑03 — Unieke identificatie/onderscheidbaarheid
- JSON: `src/toetsregels/regels/ESS-03.json`
- Stappen: required element `_has_unique_identification` equivalent; MISSING_ELEMENT bij ontbreken; tests met “code/id/registratie/nummer”.

ESS‑04 — Objectief toetsbare elementen
- JSON: `src/toetsregels/regels/ESS-04.json`
- Stappen: required element `_has_testable_element` equivalent; tests met cijfers/term‑triggers.

ESS‑05 — Onderscheidende kenmerken
- JSON: `src/toetsregels/regels/ESS-05.json`
- Stappen: required element `_has_distinguishing_feature` equivalent; tests met “onderscheidt/kenmerk”.

---

## INT‑regels

INT‑01 — Eén zin (maximaal) / duidelijke structuur
- JSON: `src/toetsregels/regels/INT-01.json`
- Extra: aanvullende patronen in legacy (meerdere zinnen detectie, “;” heuristiek).
- Stappen: structure checks `max_one_sentence`, `clear_structure` (≥5 woorden); voeg aanvullende regex uit legacy toe; tests met dubbele zinnen en minimale lengte.

INT‑02 — (Titel en inhoud, afhankelijk van JSON)
- JSON: `src/toetsregels/regels/INT-02.json`
- Stappen: toepassen zoals JSON: forbidden/required/structure; tests met voorbeelden.

INT‑03 — Verwijswoorden (“deze/dit/die”) vermijden
- JSON: `src/toetsregels/regels/INT-03.json`
- Extra: aanvullende patroon (uitsluiten wanneer gevolgd door “begrip/definitie/regel”).
- Stappen: FORBIDDEN_PATTERN + uitzondering; tests met en zonder uitzonderingsfrase.

INT‑04 … INT‑10
- JSON: `src/toetsregels/regels/INT-0X.json`
- Stappen: idem: JSON → V2 mapping; voeg waar nodig extra regex uit legacy toe.

---

## SAM‑regels (samenhang)

SAM‑01 … SAM‑08
- JSON: `src/toetsregels/regels/SAM-0X.json`
- Stappen per regel: JSON patronen/vereisten → V2; categoriseer violations als `samenhang`; tests per JSON voorbeelden.

---

## STR‑regels (structuur)

STR‑01 — Start met zelfstandig naamwoord
- JSON: `src/toetsregels/regels/STR-01.json`
- Extra: aanvullende verboden starts ("is", "de/het/een", "wordt", …) uit legacy.
- Stappen: structure check `proper_noun_start` met forbidden starts; tests met “is/wordt” (fail) en correcte start (pass).

STR‑02 — Concrete terminologie (tegen vage termen)
- JSON: `src/toetsregels/regels/STR-02.json`
- Extra: aanvullende regex voor vage termen zonder specificatie.
- Stappen: structure check `concrete_terminology`; tests met “proces/activiteit/zaak/ding” zonder specificatie (fail), met specificatie (pass).

STR‑03 … STR‑09
- JSON: `src/toetsregels/regels/STR-0X.json`
- Stappen: JSON → V2 mapping; structure‑categorie voor violations; tests per voorbeelden.

---

## VER‑regels (verschijningsvorm)

VER‑01 — Term in enkelvoud
- JSON: `src/toetsregels/regels/VER-01.json`
- Stappen: eenvoudige lemma‑check (heuristisch: eindigt op “en” ≠ plurale tantum whitelist); tests met “gegevens/voertuigen” (fail) en “gegeven/voertuig” (pass).

VER‑02 … VER‑03
- JSON: `src/toetsregels/regels/VER-0X.json`
- Stappen: JSON → V2 mapping; tests per voorbeelden.

---

## Overstijgende werkzaamheden

1) V2 Evaluatie‑engine uitbreiden
   - In `modular_validation_service.py`: 
     - Laad regels (`ToetsregelManager.get_all_regels()` – al beschikbaar).
     - Evalueer per regel:
       * Forbidden patterns → matches → violations
       * Derived required elements / structure checks (zoals in legacy helpermethoden) → violations
     - Severity→multiplier, gewicht→aggregatie.
     - Map rule→category (`juridisch/structuur/samenhang/taal`) op basis van prefix (ESS/STR/SAM/CON/…)
   - Voeg `additional_patterns` voor CON‑01/ESS‑01/INT‑01/INT‑03/STR‑01/STR‑02.

2) Tests
   - Unit per regel (minimaal 2 foute + 2 goede voorbeelden, waar aanwezig in JSON).
   - Integratie: orchestrator V2 pad met realistische definities; schema‑conforme output.

3) Documenteer aanpassingen (CHANGELOG) – geen nieuwe docsstructuur, enkel dit plan.

Risico’s & mitigaties
- Regex vals‑positief/negatief → golden tests per regel; extra voorbeelden toevoegen.
- Performance bij veel regexen → compile cache + limiet op matches (early break).
- Inconsistentie tussen JSON en Python‑module → JSON leidend; Python alleen als referentie voor uitbreidingen.

Acceptatiecriteria (globaal)
- [ ] Alle regels uit `src/toetsregels/regels/*.json` worden geëvalueerd in V2 (zonder legacy aanroep)
- [ ] Severity/weight volgen JSON (met multiplier mapping)
- [ ] Schema‑conforme output; deterministische sorting
- [ ] Golden tests per regel groen (minimaal basis cases)
- [ ] ESS‑02: metadata‑override + eenduidigheid (1 hit) + ambigu (multi‑hit) afgedekt

---

## Per‑Regel Validatie Specificatie (velden + methode)

Onderstaande lijst specificeert per toetsregel waar (welke velden) en hoe (methode) gevalideerd wordt in de V2‑validator. Indien nodig worden afgeleide checks gebruikt zoals in de legacy helpermethoden. Severity en gewicht volgen JSON.

Legenda velden
- definitie: `Definition.definitie` (string)
- begrip: `Definition.begrip` (lemma/term)
- organisatorische_context/juridische_context/wettelijke_basis: contextlijsten (TEXT JSON arrays in DB; in memory list[str])
- ontologische_categorie: `Definition.ontologische_categorie` (optioneel)
- marker: `context["marker"]` in ValidationContext (optioneel)

ARAI (ARAI‑01, ARAI‑02, ARAI‑02SUB1, ARAI‑02SUB2, ARAI‑03, ARAI‑04, ARAI‑04SUB1, ARAI‑05, ARAI‑06)
- Velden: definitie
- Methode: JSON `herkenbaar_patronen` → FORBIDDEN_PATTERN violations; extra regex uit legacy (indien aanwezig) toevoegen.
- Violatiecategorie: taal/juridisch (afhankelijk van regel; default: juridisch)

CON‑01 — Eigen definitie voor elke context (zonder expliciet te benoemen)
- Velden: definitie
- Methode: JSON patronen (o.a. “in de context van”, “juridisch”, “DJI/OM/ZM/KMAR”, “Wetboek van …”) + aanvullende regexen uit legacy interpreter → FORBIDDEN_PATTERN.
- Violatiecategorie: samenhang

CON‑02 — Authentieke bron (indien van toepassing)
- Velden: definitie (primair)
- Methode: required element `authentieke_bron_basis` → _has_authentic_source_basis (regex: “volgens|conform|gebaseerd|bepaald|bedoeld|wet|regeling”). Bij ontbreek → MISSING_ELEMENT.
- Violatiecategorie: samenhang

ESS‑01 — Essentie, niet doel
- Velden: definitie
- Methode: FORBIDDEN_PATTERN op doelgerichte frasen uit JSON (bv. “om te”, “met als doel”, “teneinde”, “zodat”, “gericht op”).
- Violatiecategorie: juridisch

ESS‑02 — Ontologische categorie expliciteren
- Velden: definitie, marker (context), ontologische_categorie (optioneel)
- Methode: 
  - Marker‑override: als `marker ∈ {type, exemplaar/particulier, proces/activiteit, resultaat/uitkomst}` → PASS.
  - Regex per categorie uit JSON: tel categorie‑hits; exact één → PASS; >1 → CONTENT_ISSUE “ambiguïteit”; 0 → MISSING_ELEMENT “ontologische categorie ontbreekt”.
  - Structure check: `explicit_ontological_category` (fallback op indicatoren: “soort|type|categorie|klasse|proces|activiteit|handeling|resultaat|uitkomst|product|effect|exemplaar|instantie|specifiek”).
- Violatiecategorie: juridisch

ESS‑03 — Unieke identificatie
- Velden: definitie
- Methode: required element `unieke_identificatie_criterium` → _has_unique_identification (regex: “uniek|specifiek|identificeer|registratie|nummer|code|id”).
- Violatiecategorie: juridisch

ESS‑04 — Objectief toetsbare elementen
- Velden: definitie
- Methode: required element `objectief_toetsbaar_element` → _has_testable_element (regex: getallen, “binnen|na|voor|volgens|conform|gebaseerd op”).
- Violatiecategorie: juridisch

ESS‑05 — Onderscheidende kenmerken
- Velden: definitie
- Methode: required element `onderscheidend_kenmerk` → _has_distinguishing_feature (regex: “onderscheidt|specifiek|bijzonder|kenmerk|eigenschap”).
- Violatiecategorie: juridisch

INT‑01 — Eén zin / duidelijke structuur
- Velden: definitie
- Methode: structure checks `max_one_sentence` (regex splitsers), `clear_structure` (≥5 woorden). Aanvullende regexen uit legacy (“.;” heuristiek) meenemen.
- Violatiecategorie: structuur

INT‑02 — (volgt JSON)
- Velden: definitie
- Methode: patronen/vereisten/structuur uit JSON → overeenkomstige FORBIDDEN_PATTERN/MISSING_ELEMENT/STRUCTURE_ISSUE.
- Violatiecategorie: structuur (of juridisch, volgens JSON)

INT‑03 — Verwijswoorden vermijden
- Velden: definitie
- Methode: FORBIDDEN_PATTERN op “deze|dit|die|daarvan” met uitzondering als gevolgd door “begrip|definitie|regel” (lookahead‑uitzondering zoals legacy).
- Violatiecategorie: structuur

INT‑04 — Onduidelijke artikel‑verwijzingen
- Velden: definitie
- Methode: structure check `clear_article_references` (regex op “de proces/activiteit” zonder specificatie).
- Violatiecategorie: structuur

INT‑06, INT‑07, INT‑08, INT‑09, INT‑10 — (volgen JSON)
- Velden: definitie
- Methode: JSON patronen/vereisten → overeenkomstige checks; structure of juridisch categorie per regeltype.

SAM‑01 … SAM‑08 — Samenhangregels
- Velden: definitie (primair; sommige kunnen cross‑checks vereisen, maar JSON is leidend)
- Methode: JSON patronen/structuur → samenhang‑categorie violations.

STR‑01 — Start met zelfstandig naamwoord
- Velden: definitie
- Methode: structure check `proper_noun_start` + forbidden starts (regex: “^(is|de|het|een|wordt|betreft|zijn|kan|moet|mag)\b”).
- Violatiecategorie: structuur

STR‑02 — Concrete terminologie
- Velden: definitie
- Methode: structure check `concrete_terminology` (verbied vage termen zonder specificatie: “proces|activiteit|zaak|ding” zonder kwalificatie).
- Violatiecategorie: structuur

STR‑03 … STR‑09 — (volgen JSON)
- Velden: definitie
- Methode: JSON patronen/vereisten/structuur → overeenkomstige checks.

VER‑01 — Term in enkelvoud
- Velden: begrip (lemma/term)
- Methode: eenvoudige lemma‑heuristiek: detecteer meervoud (regex “\b(\w+en)\b”) met whitelist voor plurale tantum (lijst uitbreidbaar vanuit JSON “goede/foute voorbeelden”).
- Violatiecategorie: taal/vorm

VER‑02 … VER‑03 — (volgen JSON)
- Velden: begrip of definitie (afhankelijk van JSON “geldigheid”)
- Methode: JSON patronen/vereisten → overeenkomstige checks.

---

### CON‑01 — Deep: Daadwerkelijke Validatie + DB‑kruischeck

Doel van de regel (samengevat):
- De definitie moet contextspecifiek geformuleerd zijn ZONDER de context expliciet te benoemen in de tekst.
- Voor hetzelfde begrip met exact dezelfde contextcombinatie moet er géén parallelle “nieuwe” definitie ontstaan; toon dan de bestaande (UI‑verantwoordelijkheid), de validator kan dit signaleren.

Invoer/velden
- begrip (string)
- definitie (string)
- organisatorische_context: list[str]
- juridische_context: list[str]
- wettelijke_basis: list[str]
- categorie (optioneel, voor uniqueness)
- repository (injectie via ServiceContainer)

Normalisatie
- Contextlijsten normaliseren (casefold, trim, unieke volgorde) en serialiseren naar canonieke JSON (zoals schema.sql). Dit moet overeenkomen met de opslagvorm in DB (TEXT met JSON array).

Valideer (in volgorde)
1) Context verplicht (primary gate)
   - Check: minimaal één van de drie contextlijsten heeft lengte > 0.
   - Fout: MISSING_ELEMENT (critical) code: CON-01-NO-CONTEXT, message: “Geen context opgegeven (organisatorisch/juridisch/wettelijk).”
   - Rationale: Zonder context is de definitie niet contextspecifiek; regeldoel niet haalbaar.

2) Duplicate contextcombinatie (signaal; geen hard fail, tenzij policy)
   - Query (DB): zoek in `definities` naar record(s) met:
     - `begrip = ?`
     - genormaliseerde `organisatorische_context` exact gelijk
     - genormaliseerde `juridische_context` exact gelijk
     - (optioneel) `categorie = ?` (meenemen indien betekenislaag vastligt)
     - `status != 'archived'`
   - Als gevonden:
     - Violatie: INFO of WARNING (afhankelijk van gewenste gate) code: CON-01-DUP, message: “Bestaande definitie met dezelfde context gevonden”, metadata: {existing_definition_id, status}.
     - UI‑actie (buiten validator): toon bestaande definitie. Geen hard fail tenzij policy bepaalt dat dubbelen geblokkeerd worden bij established.
   - Rationale: schema.sql heeft UNIQUE op (begrip, organisatorische_context, juridische_context, categorie, status). Bij andere status kan er al bestaan; dit willen we signaleren i.p.v. falen.

3) Geen expliciete contextbenoeming in definitietekst (taalpatroon)
   - Check: FORBIDDEN_PATTERN op JSON‑patronen (o.a. “in de context van”, “juridisch(e)”, “DJI/OM/ZM/KMAR”, “volgens het Wetboek van …”).
   - Fout: FORBIDDEN_PATTERN (high) code: CON-01-TEXT-CONTEXT, message: “Definitie benoemt de context expliciet; formuleer impliciet.”
   - Rationale: regeltekst eist impliciete context; expliciet benoemen is tegenregel.

4) (Optioneel) Implicietheidscheck lichtgewicht
   - Soft‑heuristiek: als tekst letterlijk een of meer van de opgegeven contexttermen bevat, verhoog waarschuwing (geen extra fail) — voorkomt valse zekerheid.

Fail/Pass logica samengevat
- Fail (hard): stap 1 (geen context) of stap 3 (expliciete context in tekst) — conform regelintentie en JSON.
- Niet‑fail maar signaal: stap 2 duplicate → INFO/WARNING + metadata zodat UI kan tonen/redirecten.

Alternatieve failcondities
- Policy‑gedreven: duplicate als ERROR wanneer bestaande definitie status ‘established’ heeft (om wildgroei te voorkomen). Deze keuze is product/UX‑gedreven; default in V2 = waarschuwing.

### CON‑02 — Deep: Authentieke bron vereist (indien van toepassing)

Velden
- definitie (primair), wettelijke_basis (list[str], secundair signaal)

Validatie
- Primary: required element `authentieke_bron_basis` in definitietekst (regex: “\b(volgens|conform|gebaseerd|bepaald|bedoeld|wet|regeling)\b”).
  - Fail: MISSING_ELEMENT (high/critical volgens JSON) code: CON-02-NO-BASIS als geen indicatoren voorkomen.
- Secondary: als `wettelijke_basis` lijst niet leeg is, telt dit als extra signaal (kan INFO toevoegen bij afwezigheid in tekst); geen hard pass zonder tekstindicator (tenzij productbesluit).
- Geen DB‑query vereist.

Fail/Pass
- Pass: tekst bevat bron‑indicatoren (en optioneel non‑empty `wettelijke_basis`).
- Fail: geen indicatoren in tekst (en lege `wettelijke_basis` → versterkt de melding in suggestions/metadata).

---

### ESS‑01 — Deep: Essentie, niet doel

Velden
- definitie

Validatie
- FORBIDDEN_PATTERN: doel/gebruik‑frases uit JSON (“om te”, “met als doel”, “bedoeld om/voor”, “teneinde”, “zodat”, “gericht op”, “ten behoeve van”).
- Geen DB‑query.

Fail/Pass
- Pass: geen doel‑frases.
- Fail: één of meer doel‑frases aangetroffen → FORBIDDEN_PATTERN (high/critical conform JSON).

---

### ESS‑02 — Deep: Ontologische categorie expliciteren

Velden
- definitie, context.marker (override), ontologische_categorie (optioneel signaal voor prompt, niet voor pass)

Validatie
- Marker‑override: als `marker ∈ {type, exemplaar/particulier, proces/activiteit, resultaat/uitkomst}` → PASS (score 1.0).
- Regex per categorie (JSON): tel categorie‑hits.
  - 1 categorie → PASS (met metadata: {category, patterns}).
  - >1 categorie → CONTENT_ISSUE (critical): “ambiguïteit – meerdere categorieën herkend”.
  - 0 categorie → MISSING_ELEMENT (critical): “ontologische categorie niet expliciet”.
- Structure fallback: `explicit_ontological_category` (indicatoren: “soort|type|categorie|klasse|proces|activiteit|handeling|resultaat|uitkomst|product|effect|exemplaar|instantie|specifiek”).
- Geen DB‑query.

Fail/Pass
- Pass: marker of exact één categorie‑hit.
- Fail: 0 of >1 categorie‑hits.

---

### ESS‑03 — Deep: Unieke identificatie

Velden
- definitie

Validatie
- Required element `_has_unique_identification` (regex: “\b(uniek|specifiek|identificeer|registratie|nummer|code|id)\b”).
- Geen DB‑query.

Fail/Pass
- Pass: indicator aanwezig.
- Fail: afwezig → MISSING_ELEMENT (severity volgens JSON).

---

### ESS‑04 — Deep: Objectief toetsbare elementen

Velden
- definitie

Validatie
- Required element `_has_testable_element` (regex: “\b(\d+|binnen|na|voor|volgens|conform|gebaseerd op)\b”).
- Geen DB‑query.

Fail/Pass
- Pass: objectief toetsbaar element aanwezig.
- Fail: afwezig → MISSING_ELEMENT.

---

### ESS‑05 — Deep: Onderscheidende kenmerken

Velden
- definitie

Validatie
- Required element `_has_distinguishing_feature` (regex: “\b(onderscheidt|specifiek|bijzonder|kenmerk|eigenschap)\b”).
- Geen DB‑query.

Fail/Pass
- Pass: onderscheidend element aanwezig.
- Fail: afwezig → MISSING_ELEMENT.

---

### INT‑01 — Deep: Eén zin / duidelijke structuur

Velden
- definitie

Validatie
- Structure `max_one_sentence`: splits op [.!?]+, maximaal 1 zin (lege trailing split toegestaan).
- Structure `clear_structure`: minimaal 5 woorden (duidelijkheidseis).
- Aanvullende heuristiek (legacy): detecteer “.;” en ‘;’ gevolgd door kleine letter als zinscheiding.
- Geen DB‑query.

Fail/Pass
- Fail: >1 zin of te weinig woorden.
- Pass: 1 zin en voldoende woorden.

---

### INT‑03 — Deep: Verwijswoorden vermijden

Velden
- definitie

Validatie
- FORBIDDEN_PATTERN: “\b(deze|dit|die|daarvan)\b”
- Uitzondering: toestaan bij expliciete toelichting “\b(deze|dit|die)\b\s+(begrip|definitie|regel)” (geen violation).
- Geen DB‑query.

Fail/Pass
- Fail: pronomen zonder uitzondering.
- Pass: geen pronomen of met uitzondering.

---

### INT‑04 — Deep: Duidelijke artikel‑verwijzingen

Velden
- definitie

Validatie
- Structure `clear_article_references`: verbied “\bde\s+(proces|activiteit)\b(?!\s+\w+)” (vage artikel+generiek zonder nadere specificatie).
- Geen DB‑query.

Fail/Pass
- Fail: onduidelijke artikel‑verwijzing.
- Pass: geen vage artikel‑verwijzing of wel specificeert.

---

### STR‑01 — Deep: Start met zelfstandig naamwoord

Velden
- definitie

Validatie
- Structure `proper_noun_start`: niet beginnen met hulpwerkwoord/artikel.
- FORBIDDEN starts: “^(is|de|het|een|wordt|betreft|zijn|kan|moet|mag)\b”.
- Geen DB‑query.

Fail/Pass
- Fail: begint met verboden start.
- Pass: begint met zelfstandig naamwoord/naamwoordgroep.

---

### STR‑02 — Deep: Concrete terminologie (tegen vaagheid)

Velden
- definitie

Validatie
- Structure `concrete_terminology`: verbied vage termen zonder specificatie: “\b(proces|activiteit|zaak|ding)\b(?!\s+\w+)”.
- Geen DB‑query.

Fail/Pass
- Fail: vage term zonder nadere kwalificatie.
- Pass: voldoende gespecificeerde term of geen vage term.

---

### VER‑01 — Deep: Term in enkelvoud

Velden
- begrip (lemma)

Validatie
- Heuristiek meervoud: regex “\b(\w+en)\b” (NL meervoudsvorm); whitelist van plurale tantum (uitbreidbaar) zoals ‘kosten’, ‘hersenen’. JSON voorbeelden helpen whitelist opstellen.
- Geen DB‑query.

Fail/Pass
- Fail: meervoudig lemma dat geen plurale tantum is.
- Pass: enkelvoud of erkende plurale tantum.

---

## Per‑Regel Deep Spec Index (compact)

ARAI‑01..06 (+SUB1/SUB2):
- Velden: definitie; Methode: JSON forbidden patterns; Geen DB; Fail: pattern‑match; Pass: geen match.

CON‑01: zie deep‑sectie.

CON‑02:
- Velden: definitie (+wettelijke_basis signaal); Methode: bronindicatoren in tekst (required), optioneel signaal vanuit lijst; Geen DB; Fail: geen indicatoren; Pass: wel indicatoren.

ESS‑01..05: zie deep‑secties (boven) voor 01..05.

INT‑01/03/04: zie deep‑secties; INT‑02/06/07/08/09/10 volgen JSON (forbidden/required/structure) zonder DB.

SAM‑01..08:
- Velden: definitie; Methode: JSON patronen/coherentie‑checks; Geen DB; Fail: pattern‑match; Pass: geen match.

STR‑01/02: zie deep‑secties; STR‑03..09 volgen JSON (forbidden/required/structure) zonder DB.

VER‑01: zie deep‑sectie; VER‑02/03 volgen JSON (velden: begrip of definitie volgens “geldigheid”).

---

## ARAI — Deep Specificaties

### ARAI‑01 — Formele correctheid (volgt JSON)
- Velden: definitie
- Validatie: JSON `herkenbaar_patronen` (formele/taalconstructies die niet thuishoren in definities) → FORBIDDEN_PATTERN (severity volgens JSON).
- Fail/Pass: match → fail; geen match → pass.

### ARAI‑02 / ARAI‑02SUB1 / ARAI‑02SUB2 — Precisie/consistentie subregels
- Velden: definitie
- Validatie: JSON patronen per subregel; geen DB; FORBIDDEN_PATTERN of structure per definitie van de JSON.
- Fail/Pass: match → fail; geen match → pass.

### ARAI‑03 — Terminologische correctheid
- Velden: definitie
- Validatie: JSON patronen; FORBIDDEN_PATTERN.

### ARAI‑04 / ARAI‑04SUB1 — Modale hulpwerkwoorden vermijden
- Velden: definitie
- Validatie: JSON patronen op “kan, moet, mag, zou, dient” etc. → FORBIDDEN_PATTERN (verlegd van doel/regelspraak naar definitie‑essentie).

### ARAI‑05 / ARAI‑06 — Overige formele/taalregels
- Velden: definitie
- Validatie: JSON patronen → FORBIDDEN_PATTERN.

---

## SAM — Deep Specificaties

### SAM‑01 — Kwalificatie leidt niet tot afwijking
- Velden: definitie
- Validatie: JSON patronen op kwalificaties (“juridisch”, “technisch”, “operationeel”, …). Signaleer misleidende kwalificatie wanneer de definitie daardoor afwijkt van algemeen aanvaarde betekenis.
- Fail/Pass: match → fail (semantische misleiding); of waarschuwing afhankelijk van policy.

### SAM‑02 … SAM‑08 — Samenhangregels
- Velden: definitie
- Validatie: JSON patronen (coherentie/consistentie) → FORBIDDEN_PATTERN of STRUCTURE_ISSUE conform JSON.
- DB: niet vereist.

---

## STR — Deep Specificaties (aanvullend)

### STR‑03 — Begripsstructuur correct (volgt JSON)
- Velden: definitie
- Validatie: JSON patronen/structuur → STRUCTURE_ISSUE.

### STR‑04 — Tautologie/cirkelredenering vermijden (volgt JSON)
- Velden: definitie
- Validatie: JSON patronen (bijv. herhalen van kernterm zonder afbakening) → STRUCTURE_ISSUE.

### STR‑05 — Zinsbouw helder (volgt JSON)
- Velden: definitie
- Validatie: JSON structuurregels (interpunctie, bijzinnen) → STRUCTURE_ISSUE.

### STR‑06 — Terminologie consistent (volgt JSON)
- Velden: definitie
- Validatie: JSON patronen → FORBIDDEN_PATTERN/STRUCTURE_ISSUE.

### STR‑07 — Redundantie vermijden (volgt JSON)
- Velden: definitie
- Validatie: JSON patronen (dubbelingen/overbodig taalgebruik) → STRUCTURE_ISSUE.

### STR‑08 — Afbakening compleet (volgt JSON)
- Velden: definitie
- Validatie: JSON vereisten → MISSING_ELEMENT/STRUCTURE_ISSUE.

### STR‑09 — Jargon vermijden (volgt JSON)
- Velden: definitie
- Validatie: JSON patronen (vakjargon zonder toelichting) → FORBIDDEN_PATTERN.

---

## INT — Deep Specificaties (aanvullend)

### INT‑02 — Geen beslisregel (voorwaarden/normen uit de definitie)
- Velden: definitie
- Validatie: FORBIDDEN_PATTERN op voorwaardelijke/normatieve frasen: “indien, mits, alleen als, tenzij, voor zover, op voorwaarde dat, in geval dat”.
- Fail/Pass: match → fail; geen match → pass.

### INT‑06 — Geen toelichting in definitiezin
- Velden: definitie
- Validatie: FORBIDDEN_PATTERN op “bijvoorbeeld/zoals/dit houdt in/dat wil zeggen/namelijk”.
- Fail/Pass: match → fail; geen match → pass.

### INT‑07 — Afkortingen toegelicht
- Velden: definitie
- Validatie: detecteer afkortingen (regex \b[A-Z]{2,6}\b en whitelist). Fail wanneer zonder toelichting tussen haakjes of zonder link/uitwerking in hetzelfde stuk tekst.
- Fail/Pass: onverklaarde afkorting → fail; verklaard of gelinkt → pass.

### INT‑08 — Positieve formulering
- Velden: definitie
- Validatie: FORBIDDEN_PATTERN op negatieve formuleringen (“niet/geen/zonder/uitgezonderd/…”) met ruimte voor uitzonderingen als ze specificerend zijn (optie: waarschuwing i.p.v. error).

### INT‑09 — Limitatieve opsomming
- Velden: definitie
- Validatie: FORBIDDEN_PATTERN op “zoals/bijvoorbeeld/onder andere/etc./enz./o.a./inclusief/waaronder begrepen/al dan niet”.
- Fail/Pass: match → fail; geen match → pass.

### INT‑10 — Geen ontoegankelijke achtergrondkennis
- Velden: definitie
- Validatie: FORBIDDEN_PATTERN op “zie/zoals gedefinieerd in/afgekort als/zoals bekend binnen/volgens interne richtlijn/interne notitie/…”.
- Fail/Pass: match → fail; geen match → pass. Toegestaan: expliciete, openbare bron met duidelijke verwijzing.

---

## VER — Deep Specificaties (aanvullend)

### VER‑02 — (volgt JSON)
- Velden: begrip of definitie (volgens JSON geldigheid)
- Validatie: JSON patronen; geen DB.

### VER‑03 — (volgt JSON)
- Velden: begrip of definitie
- Validatie: JSON patronen; geen DB.

---

## V2 Interne Regels (ModularValidationService) — Deep Specificaties

### VAL‑EMP‑001 — Lege tekst
- Velden: definitie
- Validatie: `len(chars) == 0` → fail (error). Geen DB.
- Fail/Pass: leeg → fail; anders → pass.

### VAL‑LEN‑001 — Te kort
- Velden: definitie
- Validatie: woorden < 5 of chars < 15 → fail (error). Geen DB.

### VAL‑LEN‑002 — Te lang/overdadig
- Velden: definitie
- Validatie: woorden > 80 of chars > 600 → fail (error). Geen DB.

### ESS‑CONT‑001 — Essentiële inhoud aanwezig (grove heuristiek)
- Velden: definitie
- Validatie: woorden < 6 → fail (error) “Essentiële inhoud ontbreekt of te summier”. Geen DB.

### CON‑CIRC‑001 — Circulair (begrip in definitie)
- Velden: begrip, definitie
- Validatie: regex match van begrip binnen definitietekst (word boundary, case‑insensitive) → fail (error).

### STR‑TERM‑001 — Terminologie/structuur kleinigheid
- Velden: definitie
- Validatie: specifieke verkeerde term (bijv. “HTTP protocol” i.p.v. “HTTP‑protocol”) → fail (warning). Uitbreidbaar.

### STR‑ORG‑001 — Zwakke zinsstructuur of redundantie
- Velden: definitie
- Validatie: lange, aaneengeregen zin (chars > 300 en ≥6 komma’s) of redundantiepatroon (“simpel … complex”/vice versa) → fail (warning).
