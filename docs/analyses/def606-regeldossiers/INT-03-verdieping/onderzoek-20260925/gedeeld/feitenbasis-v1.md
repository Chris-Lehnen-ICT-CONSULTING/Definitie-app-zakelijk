# Gedeelde feitenbasis — INT-03 (Voornaamwoord-verwijzing duidelijk) — 25 september 2026

Opdracht van Chris (25-09-2026, Cowork): onderzoek INT-03 met de skill `toetsregel-onderzoek` zoals de regel in de app is geïmplementeerd: (1) als toetsingsmechanisme, (2) als instructie voor het genereren van definities, inclusief de skills die daarbij worden gebruikt. Uitvoerders: Cowork (onderzoeker A, coördinator), Codex CLI (onderzoeker B, afzonderlijke sessie) en Claude Code CLI (onderzoeker C, afzonderlijke sessie, aanvullend onafhankelijk onderzoek). Tijd is belangrijk: gericht en compact, geen algemene herstart van het dossier.

Dit bestand bevat uitsluitend gedeelde feiten, bronverwijzingen en historisch materiaal. Het bevat geen nieuwe conclusies van onderzoeker A.

## 1. Identiteit en leesbasis

- Regel: INT-03 — "Voornaamwoord-verwijzing duidelijk". Linear-registratie: DEF-772 (Backlog, placeholder 17-09-2026, geen comments op 25-09), onder epic DEF-606. Gerelateerd: DEF-624 (resultaat-/beoordelingscontract, In Progress), DEF-625 (normherkomst), DEF-626 (snapshots), DEF-630 (vaststellen/export), DEF-638 (gedeeld herstel).
- Repository: /Users/chrislehnen/Projecten/Definitie-app. Leesbasis: commit `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` (2026-09-23, merge PR #472 DEF-766). Onderzoeksbranch: `onderzoek/DEF-772-INT-03-20260925` (afgesplitst van main op dezelfde commit; alleen onderzoeksbestanden, geen codewijziging, geen commits zonder opdracht). De werkboom bevat al eerder aanwezige untracked bestanden van Chris; laat die intact.
- Werkmap: docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925/ met `gedeeld/`, `onderzoek-a/` (Cowork), `onderzoek-b/` (Codex CLI), `onderzoek-c/` (Claude Code CLI). Schrijf uitsluitend in de eigen map.
- Methodiek: skill `toetsregel-onderzoek` op de Mac: /Users/chrislehnen/.agents/skills/toetsregel-onderzoek/ (SKILL.md 24-09-2026, sha256 66d65b3f…; references van 23-09) — deze versie bevat Q6 met beoogde kwaliteitswinst en de sectie "Effectevaluatie van de verbeterslag" in references/genereren-en-toetsen.md. De Cowork-gesynchroniseerde kopie is ouder (sha256 94206774…); inhoudelijk gelden Q1–Q6, G/T/H, de veldmatrix en de effectevaluatie uit de Mac-versie.

## 2. Historisch dossier (mag door iedereen gelezen worden)

- docs/analyses/def606-regeldossiers/INT-03-v1.md (11-09-2026, basis d68a98a9; SHA-256 volgens DEF-772: b01ecc2c…), met bewijsmap INT-03-bewijs-v1/ (gevallen.json: zes gevallen; uitkomsten.json: 12 resultaten, beide laadpaden review_required; claude-review.json).
- docs/analyses/2026-09-07-definitiekwaliteit-dossiers-int-sam.md §INT-03 (regels 128–156): gevallen P/N/G (pijl/overdracht/pijl) alle review_required; conclusie "formulering grotendeels passend, oordeel ontbreekt"; opmerking dat de INT-regel-ID in de adapterproef alleen bij juridische/wettelijke context in de prompt zat (7-09-claim, te actualiseren).
- docs/analyses/2026-09-11-def606-productonderzoek-bewijs/ en docs/analyses/2026-09-17-DEF-606-centraal-regelregister-v1.md (regelregister).
- Appbreed besluit 15-09-2026: geen totaalscore als kwaliteitscijfer (docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md; DEF-624-beschrijving).
- Naburige afgeronde onderzoeken als werkvormvoorbeeld (geen normbron voor INT-03): INT-01-verdieping/onderzoek-20260923/, ESS-05-verdieping/onderzoek-20260923/, CON-01-verdieping/.

## 3. Externe norm (gelezen 25-09-2026)

ASTRA-pagina letterlijk in gedeeld/astra-INT-03-raw-20260925.txt. Kern:
- Regel: "Voor ieder voornaamwoord binnen een definitie dient duidelijk te zijn ''waarnaar'' verwezen wordt."
- Toelichting: voornaamwoorden "(zoals ‘hij’, ‘het’, ‘zij’, ‘die’, ‘dit’, ‘dat’) verwijzen naar "dingen" (zoals personen, dieren, voorwerpen of concepten); in de definitie moet duidelijk zijn welk ding dat betreft." Verwijst naar onzetaal.nl/taalloket/voornaamwoord.
- Voorbeelden (begrip "context"): ONJUIST "… waardoor het volledig kan worden begrepen …"; JUIST(ER) "… waardoor die gebeurtenis volledig kan worden begrepen …".
- Brondocument DBT (Ross) §4.3; prioriteit hoog; aanbeveling verplicht; geldigheid "alle"; status definitief; type "term".
Niet gelezen: Ross DBT §4.3 zelf en de Onze Taal-pagina (geen toegang georganiseerd; claims daarover markeren als niet geverifieerd).

## 4. Regelrecord in de app (src/toetsregels/regels/INT-03.json, laatste wijziging cbadffd55 2026-08-12 DEF-624)

- uitleg: "Definities mogen geen voornaamwoorden bevatten waarvan niet direct duidelijk is waarnaar verwezen wordt."
- toelichting (lokaal, niet in ASTRA): "Voornaamwoorden als 'deze', 'dit', 'die', 'daarvan' enzovoort verwijzen naar een antecedent. In een definitie moet altijd in dezelfde zin of zinsdeel staan welk zelfstandig naamwoord bedoeld is, zodat de definitie zelfstandig en eenduidig leesbaar blijft."
- toetsvraag: "Bevat de definitie voornaamwoorden zoals 'deze', 'dit', 'die'? Zo ja: is voor de lezer direct helder waarnaar ze verwijzen?"
- herkenbaar_patronen (10, eigen toevoeging; ASTRA kent geen patronen): \bdeze\b, \bdit\b, \bdie\b, \bdaarvan\b, \bdaarbij\b, \bwaarvan\b, \bwaarmee\b, \binzienelijk maken\b (sic), \bwaarbij\b, \bin het kader\b. Niet in de lijst: 'het', 'hij', 'zij', 'dat', 'hun', 'zijn/haar', 'ervan', 'hiervan', 'daarmee'.
- goede_/foute_voorbeelden: het ASTRA-paar (verschil 'die gebeurtenis' vs 'het'); beide zinnen bevatten tweemaal 'die'.
- prioriteit hoog; aanbeveling verplicht; geldigheid "gehele definitie" (ASTRA: "alle"); type "interne structuur" (ASTRA: "term"); brondocument "ASTRA" (herkomst DBT 4.3 afgevlakt).
- runtime_contract: evaluator judgment_review; required_inputs [definition_text]; executability judgment; automation_status review_required; score_policy excluded_from_score; example_pair_policy review_policy; reden "voornaamwoord-antecedentresolutie vergt woordsoortanalyse; het patroon vuurt ook op het eigen goede voorbeeld"; issue DEF-624.
- Extra patroon buiten het record: src/validation/additional_patterns.py regel 36–38: `\b(deze|dit|die|daarvan)\b(?!\s+(begrip|definitie|regel))`.
- Config: INT-03 staat in config/toetsregels/toetsregels_config.yaml (regel 151) en config/config.yaml (regel 183).
- Testfixture: tests/fixtures/toetsregels/runtime_cases.yaml regels 378–387: probe begrip "regeling", tekst "regeling waarbij deze afspraak geldt", verwacht review_required (issue DEF-624).

## 5. Toetsingsmechanisme (live keten)

- Keten: config → src/toetsregels/manager.py / cached_manager → src/services/validation/modular_validation_service.py (`_evaluate_json_rule`, registry.resolve(record.evaluator) regel ~1451) → src/services/validation/evaluators/judgment_review.py.
- JudgmentReviewEvaluator.evaluate (regels 66–77): voor INT-03 geen regelspecifieke tak; reden = toetsvraag uit het record (letterlijk), uitkomst altijd `EvaluationOutcome.review_required(reden, signals=…)`. Signalen = de regexpatronen (record + additional_patterns) die op ctx.cleaned_text vuren; alleen de patroonstrings, geen geciteerde passages. Alleen ESS-01, ESS-02 en ESS-04 hebben een tak met `_reden_met_passages` (letterlijke fragmenten in de reden).
- Docstring judgment_review.py: INT-03 is "projectuitbreiding" van de dertien reviewplichtige regels (naast DEF-624-acht, SAM-01, STR-08, STR-09, ESS-02); "bij alle dertien vuren de eigen patronen ook op het gedocumenteerde goede voorbeeld, of missen ze het gedocumenteerde foute voorbeeld volledig". Een algemene AI-jury is bewust niet ingevoerd; per regel apart besluit (ADR-001), zoals gedaan voor CON-02 (DEF-743) en ESS-03 (DEF-766, AI-telbaarheidsbeoordeling `countability_assessment`).
- Resultaatcontract: src/services/validation/interfaces.py ReviewRequirement {rule_id, category, reason, signals}; statussen pass/fail/review_required/not_evaluated/error/not_applicable. UI: src/ui/components/validation_view.py (label "🟠 Nog te beoordelen"), expert_review_tab.py, export_txt.py ("nog te beoordelen").
- Legacy: src/toetsregels/regels/INT-03.py en src/toetsregels/validators/INT_03.py (identiek): regex-hit → fail 0.0 tenzij het goede voorbeeld letterlijk in de tekst staat; `get_generation_hints()` met vier hints. Volgens DEF-606-onderzoek (11-08-2026) is deze .py-laag een restant zonder productieconsument. Te controleren, niet aannemen.

## 6. Generatie-instructie (live prompt) en skills

- Live promptmodule: src/services/prompts/modular_prompt_adapter.py regels 102–110 registreert JSONBasedRulesModule(rule_prefix="INT", module_id="integrity_rules", priority 70). src/services/prompts/modules/json_based_rules_module.py `_format_rule` (regels ~262–300) rendert per regel: "🔹 **INT-03 - Voornaamwoord-verwijzing duidelijk**", "- <uitleg>", "- **Instructie:** <instruction_map>" en bij include_examples "  ✅ <goed>" / "  ❌ <fout>". instruction_map regel 378: "Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin". Toetsvraag wordt sinds DEF-171 niet meer in de prompt gezet.
- src/services/prompts/modules/integrity_rules_module.py `_build_int03_rule` (regels 183–200) bevat een hardcoded variant met een extra ✅-voorbeeld ("Voorwaarde: bepaling die aangeeft onder welke omstandigheden een handeling is toegestaan"); deze module wordt in de adapter niet geregistreerd (alleen export in modules/__init__.py). Te verifiëren of iets anders haar gebruikt.
- Skills op de Mac (actief voor Claude Code en Codex): ~/.claude/skills/definitie-toetsregels/ en ~/.agents/skills/definitie-toetsregels/ (SKILL.md sha256 21b4157c…, reference.md f32521057…, bron van waarheid ~/Projecten/_claude-global-setup/skills/definitie-toetsregels/, identieke hashes). reference.md regel 64: "| INT-03 | Duidelijke voornaamwoord-verwijzing | **hoog** | Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent |". SKILL.md heeft geen INT-03-sectie (wel voor CON-01/02, ESS-01/02/03/04).
- ~/.claude/skills/definitie-nederlandse-definities/reference.md regel 185 (sectie "Verboden Patronen" → "Vermijden"): "Impliciete verwijzingen: `deze`, `dit`, `die`, `dat` zonder duidelijk antecedent". Diezelfde reference beveelt elders de betrekkelijke bijzin aan ("persoon die wordt verdacht van een strafbaar feit" ✅).
- De Cowork-gesynchroniseerde skills heten `toetsregels` en `nederlandse-definities` (andere hashes, INT-03-regels inhoudelijk gelijk).

## 7. Bekende buurregels (alleen voor concrete relaties)

INT-01 (één begrijpelijke zin; historisch dossier noemt dat INT-01-patronen 'die' afkeuren), INT-04 (lidwoordverwijzing), INT-10, ARAI-05 (impliciete aannames), CON-CIRC-001 (lemmaherhaling), ESS-05, SAM-05. Besluiten van die dossiers zijn geen INT-03-norm.

## 8. Status per onderzoeksvraag (vertrekpunt, geen conclusie)

- Bewezen (historisch, 11-09): judgment_review levert altijd review_required, ongeacht ambiguïteit; beide laadpaden gelijk. Te actualiseren op 26f2374d omdat de validatieketen daarna door DEF-766/DEF-767 is gewijzigd.
- Ontbrekend feit: of INT-03 in de live generatieprompt in álle varianten staat (7-09-claim: alleen bij juridische context); wat de gerenderde INT-03-blok exact is; of de legacy .py-laag en IntegrityRulesModule ergens geladen worden; hoe de UI de reden en signalen voor INT-03 toont; of een reviewbesluit per INT-03-signaal wordt opgeslagen.
- Open beleidskeuzes (niet door onderzoekers te beslissen): reikwijdte van de norm ("dezelfde zin" lokaal vs ASTRA), of INT-03 een AI-beoordeling krijgt zoals ESS-03/CON-02 of menselijk oordeel blijft, welke uitkomsten en meldingstekst, herstelbeleid (herhaling van het zelfstandig naamwoord vs betekenisbehoud).

## 9. Spelregels

Geen implementatie, geen wijziging van bestaande bestanden buiten de eigen onderzoeksmap, geen issues, geen live modelcalls, geen brede testsuite. Kleine offline proeven met synthetische invoer en vooraf vastgelegde verwachtingen zijn toegestaan (tests/offline_bootstrap.py; voorbeeld INT-01-verdieping/onderzoek-20260923/onderzoek-a/proef-v2.py). Casus-IDs: prefix INT03-E (nieuw); historische IDs (INT-03-bewijs-v1/gevallen.json, P/N/G uit 7-09) niet hernummeren. Bewaar de eigen eerste versie vóór het lezen van andermans nieuwe conclusies.
