# DEF-766 / ESS-03 — contractlacune voor het menselijke oordeel (acceptatie 5)

18 september 2026 · uitvoerder Claude Code CLI · werkboom `/Users/chrislehnen/.codex/worktrees/2075/Definitie-app`, basis `4cdb8ea43`.

**Status:** de onafhankelijke ESS-03-fixes (regelkaart, runtime_contract, evaluator, G/T/H-teksten, tests) zijn uitgevoerd. Acceptatie 5 — een afgerond menselijk ESS-03-oordeel of bevestigde niet-toepasselijkheid herkenbaar, versiegebonden en niet permanent `pending` — **kan binnen de bestaande contracten niet worden uitgevoerd zonder een nieuw besluit**. Hieronder staat wat de keten vandaag werkelijk ondersteunt, waar de aansluiting ontbreekt en welke kleinste besluitopties er zijn. Er is niets verzonnen (geen schema, enum, marker-code of knop).

## 1. Wat de gedeelde keten vandaag werkelijk ondersteunt

| Laag | Wat bestaat | Codeverwijzing |
|---|---|---|
| Evaluator | `judgment_review` levert altijd `review_required` met een leesbare reden en signalen; leest **geen** opgeslagen menselijk oordeel | `src/services/validation/evaluators/judgment_review.py:54-65` |
| Service | `review_required` landt uitsluitend in `review_items` (`rule_id`, `category`, `reason`, `signals`) — een **transiënte** lijst in het validatieresultaat; `rule_results` krijgt alleen een detail bij `metadata["rule_result"]` (CON-01/CON-02) of bij `ERROR` | `modular_validation_service.py:1598-1599`, `:1617-1626`, `:1640-1655` |
| Opslag van menselijk oordeel | **Regelspecifieke markers** in `validation_issues`: CON-01 (`CONTEXT_REVIEW_CODE`, `set_context_review`) en CON-02 (`SOURCE_REVIEW_CODE`, `set_source_review`), plus een categoriekeuze-event voor ESS-02 (`record_category_choice`, in `generation_prompt_data`). Elk met actor, `version_number`-binding, vingerafdruk en append-only historie | `src/database/models.py:671-786`, `:565-608`; `src/database/definitie_crud.py:486-560`, `:913-`, `:1093-`; `definitie_repository.py:137-159`, `:227-256` |
| Stale-detectie | Alleen voor die markers: `get_source_review_status()` → `present`/`stale`/`invalid`/`absent` op basis van `version_number`; CON-01 via vingerafdruk in `ContextMetadataEvaluator` | `models.py:686-718`; `evaluators/context_metadata.py:73-129` |
| Herlezen door evaluator | CON-01 en CON-02 lezen hun marker terug uit `ctx.metadata` (`context_review`, `source_review`) en zetten een afgerond oordeel om in `pass`/`fail`/uitzondering op het record; gewijzigde tekst/versie maakt het oordeel `stale` → opnieuw `review_required` | `context_metadata.py:77-129`; `get_contractvelden()` in `models.py:447-477` |
| UI | Experttab heeft **aparte secties met opslagknoppen alleen voor CON-01 en CON-02**; de generieke "Validatie Issues"-sectie toont opgeslagen violations; `validation_view` toont de open reden van ESS-01/ESS-02 letterlijk (`st.text`) en telt `review_required` in de dekking | `expert_review_tab.py:604-741` (CON-01, opslag `:1223`), `:745-` (CON-02, opslag `:1188`), `:1261-1299`; `validation_view.py:730-739` |
| Gate | `forbid_critical_issues` kijkt naar violations; `review_required` blokkeert niet zelfstandig; ontbrekende totaalscore is de bestaande DEF-622/630-gap | `src/services/policies/approval_gate_policy.py:30-45` |

**Conclusie:** ESS-01, ESS-02, ESS-04 en de overige `judgment_review`-regels hebben vandaag **geen** opgeslagen menselijk oordeel en geen stale-binding; ze blijven na elke validatie `review_required`. Dat is precies de situatie die DEF-750 voor ESS-02 als "C/D, gedeelde leveringen DEF-624/626/627/630" open liet (commit `97482d193`, laatste alinea). ESS-03 sluit nu op hetzelfde punt aan — niet op iets slechters, maar ook niet op iets beters.

## 2. Wat concreet ontbreekt voor acceptatie 5

1. **Geen generiek, regelonafhankelijk oordeelcontract.** De enige opslagvormen zijn per regel bedacht (`CONTEXT_REVIEW_CODE`, `SOURCE_REVIEW_CODE`, `CATEGORY_CHOICE_KEY`). Een ESS-03-oordeel opslaan vereist ófwel een nieuwe marker-code (nieuw enum-achtig contract in `models.py`/`definitie_crud.py`, verboden binnen deze opdracht), ófwel een generieke `rule_review`-marker die DEF-624 nog niet heeft vastgesteld.
2. **Geen weergave van "afgerond menselijk oordeel" of "bevestigd niet van toepassing" voor een `judgment_review`-regel.** `ResultStatus` kent `pass`/`fail`/`review_required`/`not_evaluated`/`error`; een bevestigde niet-toepasselijkheid heeft geen bestaande status en mag per opdracht niet als `not_evaluated` (ontbrekende invoer) worden vermomd. Tekstvoorstellen-v3 §1 trekt de v1-mapping naar `not_evaluated` expliciet terug.
3. **Geen terugleespad in `JudgmentReviewEvaluator`.** Anders dan `ContextMetadataEvaluator` en `SourceEvidenceEvaluator` leest hij niets uit `ctx.metadata`; er is dus ook geen plek waar een versiegebonden oordeel een `review_required` kan vervangen zonder nieuw contract.
4. **Geen UI-actie.** De experttab heeft geen generieke "oordeel per open regel"-invoer; een ESS-03-knop toevoegen is expliciet uitgesloten.

## 3. Kleinste besluitopties (voor Chris / DEF-624)

| Optie | Inhoud | Raakt | Wat het niet oplost |
|---|---|---|---|
| **A. Generieke `rule_review`-marker** (voorkeur uitvoerder) | Eén markervorm in `validation_issues` met `rule_id`, `verdict` (voldoet / voldoet niet / niet van toepassing), `reason`, `actor`, `version_number`, tekstvingerafdruk; `set_rule_review(definitie_id, rule_id, review, expected_version)` naast `set_context_review`; `JudgmentReviewEvaluator` leest `ctx.metadata["rule_reviews"][rule_id]` en zet een actueel oordeel om in een zichtbare, niet-pending uitkomst; stale → `review_required` met reden "oordeel hoort bij versie n" | `models.py`, `definitie_crud.py`, `definitie_repository.py`, `judgment_review.py`, `get_contractvelden()`, experttab-sectie voor open regels | Vereist een besluit over de weergavestatus van "niet van toepassing" (nieuwe `ResultStatus`-waarde of `rule_results`-detail zoals CON-01) — dat is het open DEF-624-punt |
| **B. Hergebruik van `rule_results`-detail zonder nieuwe status** | Een afgerond oordeel wordt als `metadata["rule_result"]`-detail (zoals CON-01: `status`, `parts`, `review`) geboekt; de statusenum blijft ongewijzigd; "niet van toepassing" is een `part` met eigen `outcome` | Zelfde opslag als A, maar geen enumwijziging | De regel blijft in `rule_statuses` `review_required` zolang niemand een status voor "afgerond zonder pass/fail" vaststelt; de dekkingstelling blijft dan "nog te beoordelen" |
| **C. Niets nu; ESS-03 volgt ESS-01/02/04** | ESS-03 blijft `review_required` tot DEF-624/626/627 de generieke keten leveren | Niets | Acceptatie 5 blijft open; geen regressie t.o.v. ESS-02 |

Elke optie moet dezelfde bindingen dragen als CON-01/CON-02: actor = handelende gebruiker (`_geldige_beoordelaar`), `expected_version`-lock, vingerafdruk op `get_definitie_tekst()` + term + contextlijsten, append-only historie, en nooit een oud oordeel als actueel na tekst-/contextwijziging (`update_definitie` laat de binding vervallen).

## 4. Wat deze implementatie wél bewijst (zie implementation-report-v1.md)

- ESS-03 geeft nooit meer een automatisch semantisch `pass`/`fail` op trefwoorden; ontbrekende term/tekst → `not_evaluated`; open oordeel → `review_required`; technische fout → `error` met apart foutonderdeel in `rule_results`.
- Geen individueel of categoriecijfer; geen violation, dus geen `critical`-bijdrage aan de gate en geen `unique_id`-herstelsuggestie.
- De open reden is in de gedeelde `validation_view` zichtbaar (zelfde pad als ESS-01/ESS-02).
- Opslag/teruglezen/UI-actie van een **menselijk** ESS-03-oordeel is **niet** geïmplementeerd en wordt niet geclaimd.
