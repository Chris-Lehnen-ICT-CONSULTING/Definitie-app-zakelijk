# cowork-aanvulling-op-eigen-v1 — verwerking van nalevering2 en van de Codex-codeaanvulling

Claude Cowork, 18 september 2026. Aanvulling op `cowork-onderzoek-v1.md` (sha256 `7f9138d152d1bd617c4df340bf52ce4c00b3cc1b4cec2bd8d55d9a4a07062708`), dat **ongewijzigd blijft**.

Dit stuk verwerkt uitsluitend wat door nieuw bronmateriaal verandert:
- de vier bestanden uit `nalevering2-4cdb8ea43/` (hashgelijk, commit `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`);
- twee bevindingen uit `codex-codeaanvulling-v1.md` en uit de Codex-proefuitvoer die mijn eigen voorstellen raken.

Het is geen reviewverwerking: de Codex-review op mijn v1 heb ik nog niet ontvangen. Die verwerk ik apart zodra zij er is.

---

## A-01 — Bewijsgat R9 is gesloten; §5.2 wordt harder

**Mijn v1 zei** (§5.2, §8, risico R9): de signaalclaims staan "onder voorbehoud van eventuele extra patronen" omdat `validation/additional_patterns.py` niet leesbaar was; ik noemde dit de gerichte nalevering met de hoogste prioriteit.

**Nieuw bronfeit.** `nalevering2-4cdb8ea43/src/validation/additional_patterns.py` bevat `_ADDITIONAL_PATTERNS` met entries voor ARAI-01, ARAI-02, ARAI-03, ESS-01, INT-01, INT-03, STR-01, STR-02 en SAM-01. **Er is geen ESS-04-entry**, en `get_additional_patterns(code)` geeft `list(_ADDITIONAL_PATTERNS.get(code.upper(), []))`, dus een lege lijst.

**Gevolg.** De vijftien patronen in `src/toetsregels/regels/ESS-04.json` zijn de volledige signaalset voor ESS-04. Het voorbehoud in §5.2 en in bijlage A vervalt; de vijf aangetoonde patroondefecten (vier dode percentagepatronen, `weken?` dat "week" mist, `dagen?` dat "dag" mist) en de trefwoord-pass van `bevat`/`omvat` staan zonder voorbehoud. Risico R9 vervalt uit de risicotabel.

**Ongewijzigd.** De aard van het bewijs blijft een replica: bijlage A voert `_signalen` en `evaluate` regel voor regel na en importeert het pakket niet. Dat blijft zo vermeld.

## A-02 — Routering naar `judgment_review` is nu positief vastgesteld

**Mijn v1 zei** (§8, prioriteit 2): of ESS-04 werkelijk naar `judgment_review` wordt gerouteerd leidde ik af uit het record plus het contract, niet uit het register.

**Nieuw bronfeit.** `registry.py`: expliciete registratie, "geen dynamische bestandsimport, geen `spec_from_file_location`, geen fallback naar default-pass bij een onbekend type". `resolve()` gooit `UnknownEvaluatorError` bij een onbekend of niet-geregistreerd type; `register()` weigert een dubbele registratie en een evaluator zonder geldig `evaluator_type`.

**Gevolg.** Er is geen pad waarlangs ESS-04 stil zonder evaluator of met een andere evaluator kan eindigen: `"evaluator": "judgment_review"` in het record wordt bij het laden tegen `EvaluatorType` gelegd en bij afwezigheid faalt de resolutie zichtbaar. §5.1 en §5.2 winnen hiermee aan hardheid. Prioriteit 2 uit §8 vervalt.

## A-03 — De replicagrond van bijlage A is bevestigd

**Mijn v1 zei** (§8, prioriteit 3): mijn replica steunt op aannames over `EvaluationContext` (`cleaned_text`, `metadata`).

**Nieuw bronfeit.** `types_internal.py`: `EvaluationContext` is een frozen dataclass met `raw_text`, `cleaned_text`, `begrip`, `locale`, `profile`, `correlation_id`, `tokens`, `metadata`. `from_params(text, cleaned=None, ...)` zet `cleaned_text = cleaned if cleaned is not None else text`.

**Gevolg.** Mijn replica gebruikte de invoertekst als `cleaned_text`; dat is precies het gedrag van `from_params` zonder expliciete `cleaned`. De proefopzet in bijlage A klopt op dit punt. Prioriteit 3 uit §8 vervalt.

## A-04 — De vaststelpoort: §5.7 wordt harder, niet anders

**Mijn v1 zei** (§5.7, §8 prioriteit 4): de werkelijke drempels en `allow_hard_override` kende ik niet.

**Nieuw bronfeit.** `approval_gate_policy.py`, `DEFAULT_POLICY`: `min_one_context_required: True`, `forbid_critical_issues: True`, `hard_min_score: 0.75`, `soft_min_score: 0.65`, `allow_high_issues_with_override: True`, `missing_wettelijke_basis_soft: True`, `allow_hard_override: **False**`. Het woord "review" komt in het hele bestand niet voor.

**Gevolg.** Twee dingen. Ten eerste: `allow_hard_override` staat standaard uit, dus de hard blocks in `_evaluate_gate` zijn werkelijk blokkerend en niet stilzwijgend overrulebaar — dat is strenger dan ik in §5.7 openliet. Ten tweede, en belangrijker: het beleidscontract zelf kent geen begrip van een openstaande reviewplicht. De poort kan de `review_required`-status van ESS-04 dus niet alleen feitelijk niet zien (§5.7), maar heeft er ook geen beleidsplaats voor. §5.7 en §6.7 blijven inhoudelijk staan en worden hiermee onderbouwd in plaats van gecorrigeerd. Prioriteit 4 uit §8 vervalt.

## A-05 — Correctie op mijn §6.7: het reviewcontract moet expliciet scoreloos zijn

**Mijn v1 zei** (§6.7): sla een menselijk ESS-04-oordeel op met de uitkomsten voldoet / voldoet niet / nog te beoordelen / niet beoordeelbaar, naar het CON-01-model, en laat `runtime_contract` verder ongewijzigd — §6.1 zegt uitdrukkelijk "`score_policy: excluded_from_score` blijft".

**Tegenbewijs, aangedragen door Codex** (`codex-codeaanvulling-v1.md`) **en door mij geverifieerd** in `modular_validation_service.py`:
- regels 977-994: `if record.score_policy is not ScorePolicy.SCORED: weights[code] = 0.0` — beide niet-scorende policies krijgen gewicht nul;
- regels 1013-1022: `zonder_cijfer` wordt **alleen** gevuld voor `ScorePolicy.NO_SCORE`;
- `_verwerk_uitkomst` (1568-1630): bij PASS `if not geen_cijfer: rule_scores[code] = 1.0 if outcome.score is None else outcome.score`; bij FAIL idem via `_outcome_naar_violation`;
- `_calculate_category_scores` (2034-2071): bucketeert `rule_scores` op prefix — ESS valt via `category_for_rule` in "juridisch" — en middelt **ongewogen**;
- regel 1168: de blanking-lus `for code in zonder_cijfer: detailed[category_for_rule(code)] = None` raakt alleen `NO_SCORE`-regels.

**Gevolg voor mijn voorstel.** Zolang ESS-04 `review_required` levert is er geen cijferlek — dat blijft waar, en dat stelt Codex ook zo. Maar mijn §6.7 introduceert juist een menselijk oordeel met de uitkomsten voldoet/voldoet niet. Zou dat oordeel in de bestaande PASS/FAIL-vorm worden teruggevoerd terwijl `score_policy: excluded_from_score` blijft, dan landt er een 1,0 of 0,0 in `rule_scores`, telt die mee in het ongewogen gemiddelde van de categorie "juridisch", en wordt die categorie níet geblankt. Dat is exact het cijfer dat het besluit van 15 september 2026 uitsluit.

**Correctie op §6.7 en §6.1.** Aan het opslagvoorstel wordt een vijfde punt toegevoegd, en §6.1's "`runtime_contract` ongewijzigd" wordt daarmee voorwaardelijk:

> 5. **Het reviewcontract is expliciet scoreloos.** Een menselijk ESS-04-oordeel levert nooit een numerieke bijdrage aan een regel-, categorie- of totaalscore. Het wordt teruggevoerd als gestructureerde uitkomst (`rule_result`), niet als PASS/FAIL met score. Blijft `score_policy: excluded_from_score` staan, dan moet het terugvoerpad aantoonbaar buiten `rule_scores` om lopen; wordt gekozen voor `no_score`, dan is dat een contractwijziging die op zichzelf niets bewijst — zij vraagt een concrete `rule_result`-structuur, transport door `neem_contractvelden_over`, en controle van de consumers (`render_rule_results`, dekkingstelling, export). Welke van beide: te beoordelen bij het ontwerp van de reviewroute, niet nu.

**Herkomst.** Deze correctie komt van Codex; ik heb haar geverifieerd en neem haar over. Mijn §6.7 was op dit punt onvolledig.

## A-06 — Bijstelling in mijn §3.3: werk- of kalenderdagen

**Mijn v1 zei** (§3.3, tabel): werk- of kalenderdagen is nodig "altijd" zodra een termijn in dagen in de kern staat.

**Bijstelling.** Codex houdt dit voorwaardelijk ("uitsluitend waar die de uitkomst veranderen"). Dat is juister: bij "binnen 3 dagen" of "binnen 10 dagen" verandert de conventie de uitkomst wel, bij "binnen 3 jaar" niet. Mijn eigen criterium in dezelfde paragraaf — nodig wanneer twee redelijke beoordelaars zonder dat element tot een ander oordeel over hetzelfde geval kunnen komen — leidt overigens tot precies die voorwaardelijke uitkomst; de "altijd" in de tabel was strenger dan mijn eigen criterium. Ik trek hem in ten gunste van de voorwaardelijke formulering. Dit raakt niet mijn G-tekst in §6.2, die de conventie vraagt bij een termijn *in dagen* en daarmee in het relevante bereik blijft.

## A-07 — Correctie op mijn §6.5: `voldoende` is wél een ARAI-03-patroon

**Mijn v1 zei** (§6.5): "De enige overlap die ik in mijn voorgestelde patroonlijst laat staan is `voldoende`, `substantieel`, `passend`, `redelijk` — die staan niet in ARAI-03's lijst (`effectief`, `belangrijk`, `relevant`, `toereikend`, `adequaat`) en vullen hem dus aan in plaats van hem te dupliceren."

**Tegenbewijs.** `additional_patterns.py` geeft ARAI-03 twee aanvullende patronen bovenop het record: `\bdoeltreffend\b` en **`\bvoldoende\b`**. Mijn claim was gebaseerd op alleen `ARAI-03.json` en is daarmee onjuist voor `voldoende`.

**Correctie.** In mijn voorgestelde ESS-04-patroonlijst (§6.1, voorkeursvariant) vervalt `\bvoldoende\b`; de overige drie (`substanti(eel|ele)`, `passend(e)?`, `redelijk(e)?`) blijven en overlappen niet met ARAI-03. De redenering van §6.5 — geen ARAI-03-woordenlijst dupliceren in ESS-04, en de gronden in de reviewtekst uit elkaar houden — blijft ongewijzigd; alleen dit ene woord ging fout. Terzijde: dat ARAI-03 zijn patronen deels buiten het record in Python heeft staan, is zelf de moeite van het melden waard bij een volgend regeldossier — het regelrecord toont daar niet de volledige signaalset. Voor ESS-04 speelt dat niet (A-01).

## A-08 — Aanscherping van mijn §5.3: het transportdefect bestond, en is verholpen

**Mijn v1 zei** (§5.3): ik had op grond van `mappers.py` en `types.py` transportverlies vermoed; `result_contract.py` weerlegt dat, en ik noteerde het als "een hypothese die door bewijs is verworpen".

**Aanvulling.** Die formulering was te absoluut in de andere richting. De hypothese was juist voor de oudere codebasis. In `werkboom/` (commit `50d0770`) zetten `types.py:601` en `:716` `passed_rules = ["BASIC-001","BASIC-002","BASIC-003"]`, draagt `mappers.py:29` `DEFAULT_PASSED_RULES`, en bestaat `neem_contractvelden_over` niet — de drie contractvelden gingen daar dus wél verloren en er werden geslaagde regels verzonnen. Codex heeft dat als C03/P02 gemeten en op beide basissen uitgevoerd; ik heb het statisch op de oude werkboom bevestigd.

**Juiste formulering.** Het transportdefect was reëel op `50d0770` en is op `4cdb8ea43` verholpen door `result_contract.CONTRACTVELDEN` plus `neem_contractvelden_over`. Mijn v1 beschrijft correct dat er op de actuele commit geen verlies is; wat ik ten onrechte liet staan is dat de hypothese "verworpen" zou zijn — zij was achterhaald, niet onjuist. Dit verandert niets aan enige conclusie in §5 of §6.

## A-09 — Nieuwe bevinding uit de Codex-proefuitvoer: cijfers in een niet-uitgevoerde run

**Niet in mijn v1 en niet in het Codex-onderzoek.** In `codex-reviewpakket-v1/proef-actueel-uitvoer-v1.log` draagt `legacy_output` tegelijk:

```
"overall_score": 0.0,
"is_acceptable": false,
"validation_status": "validation_unknown",
"unknown_reason": "contract_status_missing",
"detailed_scores": {"taal": 0.9, "juridisch": 0.9, "structuur": 0.9, "samenhang": 0.9}
```

**Oorzaak, door mij in de code nagegaan.** `_convert_legacy_dict_to_unified` vult `detailed_scores` via `_scores_per_categorie(overall_score)` met de invoerscore 0,9 (`types.py:806-808`, `:222-229`). Daarna maakt `met_expliciete_runstatus` het resultaat fail-closed door `is_acceptable` op False en een numerieke `overall_score` op 0,0 te zetten — maar het raakt `detailed_scores` niet, conform zijn eigen docstring ("Alle overige velden … reizen ongewijzigd mee").

**Gevolg.** Een resultaat dat expliciet geen uitgevoerde run is, draagt vier categoriecijfers van 0,9 naast een totaalscore van 0,0. Voor ESS-04 betekent dit dat een openstaande reviewplicht in een unknown-resultaat naast een ogenschijnlijk goed categoriecijfer "juridisch" komt te staan — de categorie waarin ESS-04 valt. Dit is geen ESS-04-defect en de eigenaar ligt bij het resultaatcontract (DEF-624/622); ik registreer het als gezamenlijke bevinding voor de besluitnotitie, met de aantekening dat ik niet heb onderzocht of een consumer deze `detailed_scores` toont.

---

## Wat hierdoor niet verandert

De zes hoofdbevindingen uit §1 van mijn v1 blijven ongewijzigd, en vier ervan zijn door de nalevering harder geworden (A-01, A-02, A-04). De normanalyse (§2), de veldrollen (§3), de relaties (§4) en de voorgestelde teksten voor regel, G, T en H (§6.1-§6.6) staan, met de drie correcties hierboven: A-05 (scoreloos reviewcontract), A-06 (dagconventie voorwaardelijk) en A-07 (`voldoende` vervalt uit de patroonlijst).

Van de acht ontbrekende bestanden in §8 zijn er vier nagekomen; de resterende vier blijven open: `violation_builder.py` (`category_for_rule`), `readiness.py`, `test_rule_runtime_matrix.py` en enige ESS-04-test in de actuele commit. Geen daarvan draagt een conclusie in dit onderzoek; ze zijn alleen nodig om bestaande claims verder te verharden.

Risico R8 (geen UI-bewijs) en R10 (geen eigen end-to-end-proef) blijven onveranderd staan. R9 vervalt (A-01).

---

## Bestandsstatus

| Bestand | Status | SHA-256 |
|---|---|---|
| `cowork-onderzoek-v1.md` | ongewijzigd | `7f9138d152d1bd617c4df340bf52ce4c00b3cc1b4cec2bd8d55d9a4a07062708` |
| `cowork-toegang-v1.md` | ongewijzigd | `32219d913a48203528134eee58e73fcfd62a3e742860dbb0a1073730a0747a74` |
| `cowork-toegang-v1-aanvulling-v1.md` | ongewijzigd | `c6cb0c4ffbea113cc6a99e6e35ecf43f01aa0eafa0b3ab5c2cf0c228cafdfb2e` |
| `cowork-bewijs-v1/` | ongewijzigd | zie bijlage B van v1 |
| `cowork-review-op-codex-v1.md` | nieuw | `ee25c9e82d209f0c77c2ab8f7cdcf676b91589ab8e5fa90790ee6873da6a81bb` |
| `cowork-aanvulling-op-eigen-v1.md` | dit bestand | apart gemeld bij overdracht |

Volgende benodigde overdracht: de Codex-review op mijn v1, zodat ik die punt voor punt kan verwerken als overgenomen, deels overgenomen, afgewezen met grond of open.
