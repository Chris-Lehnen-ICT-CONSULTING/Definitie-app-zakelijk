# Verwachtingen vóór uitvoering — onderzoekslijn A (INT-02)

Vastgelegd 25-09-2026 vóór het draaien van `proef-p1-service.py` en `proef-p2-prompt.py`. Leesbasis: HEAD `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3` (werkboom van Chris; checkout-branch `onderzoek/DEF-772-INT-03-20260925`, geen getrackte wijzigingen). Twee soorten verwachting: **(a) voorspelling huidige code** (grond: codelezing) en **(b) normverwachting** (grond: ASTRA-norm + voorstel; staat in het casusregister, niet hier herhaald). Proeven bewijzen alleen (a).

## P1 — ModularValidationService rechtstreeks (zoals `tests/unit/validation/test_v2_golden_int_more.py`)

Aanroep: `ModularValidationService(get_toetsregel_manager(), None, None).validate_definition(begrip=…, text=…, ontologische_categorie=None, context={} | {context})`. Geen cleaning-service (tweede parameter `None`), dus `cleaned_text == text`.

Grond: `judgment_review.py:65-78` levert voor INT-02 altijd `review_required` met `reden = toetsvraag` (geen INT-02-tak); `_signalen` (r. 195-216) geeft de regexstrings die treffen; `INT-02.json` ongewijzigd sinds `d68a98a9` (git diff leeg). `INT-01.json` en `INT-10.json` dragen `\bindien\b` met evaluator `generic`, `automated`, `scored`.

| Voorspelling | Betreft |
|---|---|
| V1 | Elke casus (ook lege tekst C06): INT-02 in `review_required`, `rule_statuses["INT-02"] == "review_required"`, niet in `passed_rules`, geen INT-02-violation. |
| V2 | `reason` voor INT-02 is letterlijk de toetsvraag "Bevat de definitie geen voorwaardelijke of normatieve formuleringen zoals beslisregels?" — zonder passagecitaat. |
| V3 | `signals` is niet-leeg precies bij teksten met indien/mits/tenzij/alleen als/voor zover/op voorwaarde dat/in geval dat (C03, C04, C11, C12, C17, C19, C20, C21, C24, C25, C26); leeg bij C01, C02, C05, C06, C10, C13, C14, C15, C16, C18, C22, C23, C27. |
| V4 | Context meegeven (C29 = tekst C03 + juridische/organisatorische context) verandert INT-02-status, reden en signalen niet. |
| V5 | Teksten met `indien` leveren daarnaast een **gescoorde** violation op INT-01 en/of INT-10 (onzeker: hangt af van generic-evaluatorlogica; te meten). |
| V6 | Teksten met `moet` (C02, C14, C15) leveren een ARAI-04-/ARAI-04SUB1-violation (onzeker; te meten). |
| V7 | Historische uitkomsten C01–C06 (11-09, `d68a98a9`) worden exact gereproduceerd voor INT-02 (status/signalen). |

## P2 — Generatieprompt-rendering (module-niveau)

Aanroep: `get_cached_orchestrator()` + `ModularPromptAdapter()`-standaardconfig (`include_examples_in_rules=True`), daarna `execute()` van de geregistreerde modules `integrity_rules`, `structure_rules`, `ess_rules`, `arai_rules` met een contextobject zonder `enriched_context`.

| Voorspelling | Grond |
|---|---|
| W1 | INT-sectie bevat exact: `🔹 **INT-02 - Geen beslisregel**`, `- Een definitie bevat geen beslisregels of voorwaarden.`, `- **Instructie:** Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'`, `  ✅ transitie-eis: … ondersteunt …`, `  ❌ transitie-eis: … moet ondersteunen …`. Geen toetsvraag. | `json_based_rules_module.py:228-281, 377` |
| W2 | Geen geregistreerde module is een `IntegrityRulesModule`; de tekst "❌ Toegang: toestemming verleend … indien alle voorwaarden zijn vervuld" komt in geen enkele module-uitvoer voor. | `modular_prompt_adapter.py:70-135` |
| W3 | STR-sectie toont bij STR-09 `  ✅ Een persoon met een paspoort of, indien niet beschikbaar, een identiteitskaart` — een goed voorbeeld mét `indien`, naast de INT-02-instructie die `indien` vermijdt. | `STR-09.json:13` |
| W4 | ESS-sectie toont bij ESS-03 een instructie met "behoud inhoudelijk noodzakelijke namen en voorwaarden". | `json_based_rules_module.py:358-359` |
| W5 | INT-sectie bevat ook INT-01 met een eigen goed/fout-voorbeeld en de INT-01-instructie; ARAI-sectie bevat ARAI-04 "Vermijd modale hulpwerkwoorden zoals 'kan', 'moet', 'mag', 'zal'". | idem |

Niet in deze proeven: volledige promptassemblage via `build_prompt` met echte `EnrichedContext`, echte modeluitvoer, UI-weergave, opslag, vaststelgate, import/export.
