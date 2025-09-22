---
canonical: true
status: draft
owner: ui
last_verified: 2025-09-22
applies_to: definitie-app@current
links:
  stories:
    - US-236
  epics:
    - EPIC-004
---

# Validatie‑weergave Unificatie (V2) — Implementatieplan

Doel: één gedeelde validatie‑renderer voor de drie tabbladen (Definitie‑generatie, Bewerk, Expert Review) met exact dezelfde inhoud en indeling als de bewezen Generatie‑weergave: Gate‑status, toggle voor details, gedetailleerde lijst met kleur/iconen en inline uitleg per regel.

## Scope & Niet‑Scope
- In scope:
  - Extractie van bestaande renderlogica uit Generatie naar `ui/components/validation_view.py`.
  - Aansluiten van Generatie/ Edit/ Expert op de gedeelde renderer.
  - Behoud huidige teksten, iconen, sorting, expanders en gate‑status.
- Niet in scope:
  - Wijzigingen aan validatie‑engine of V2‑contract.
  - Aanpassing van gate‑policy of -berekening.
  - Styling buiten de validatieblokjes.

## API van de gedeelde renderer
```
render_validation_detailed_list(
  validation_result: dict,
  *,
  key_prefix: str,
  show_toggle: bool = True,
  gate: dict | None = None,
) -> None
```
- `validation_result`: V2 dict (overall_score, violations, passed_rules, …)
- `key_prefix`: sessiesleutelprefix ("gen", "edit_{id}", "review_{id}")
- `show_toggle`: of de details toggelbaar zijn (true voor consistentie)
- `gate`: optionele gate‑dict (Generatie gebruikt dit al; Edit/Expert meestal `None`)

## Stappenplan
1) Extractie (zonder gedrag te wijzigen)
   - Verplaats helpers uit Generatie:
     - `_rule_sort_key`, `_extract_rule_id_from_line`, `_build_rule_hint_markdown`
   - Implementeer `render_validation_detailed_list(...)` met de huidige bouw van regels/expanders.
   - Toon optioneel gate‑status bovenaan indien `gate` is opgegeven.
2) Generatie aansluiten
   - Vervang de huidige inline list‑render door `render_validation_detailed_list(..., key_prefix='gen', show_toggle=True, gate=gate)`.
   - Behoud: gate‑melding, toggle, sessiekeys, exacte teksten en expanders.
3) Edit aansluiten
   - Roep de renderer op met `key_prefix=f'edit_{id}'`, `show_toggle=True`, `gate=None`.
   - Header “Kwaliteitstoetsing” erboven tonen.
4) Expert aansluitingen
   - Bij Re‑validate: sla V2‑resultaat in session (`review_{id}`) en render full‑width onder de knoppen via de renderer.
5) Verificatie
   - Generatie vóór/na vergelijking (visueel 1:1; desnoods screenshot/regtest).
   - Edit/Expert tonen exact dezelfde regels en uitleg als Generatie.
6) Documentatie
   - Update US‑236 status naar “In uitvoering/Done” zodra afgerond.
   - Korte notitie in UI‑handleiding: ‘Validatieblok is overal uniform’.

## Risico’s & Mitigatie
- Visuele regressie → Gefaseerde aansluiting, 1:1 verificatie in Generatie vóór/na.
- Statebotsingen → uniek `key_prefix` per context.
- Performance → gebruik bestaande caching/paging; toggle uit bij default om flood te voorkomen.

## Rollbackplan
- Per tab kunnen we snel terug naar vorige inline render indien nodig (oude codepad behouden tot definitieve verificatie).

## Definition of Done
- Eén renderer, drie tabbladen consistent, geen informatieverlies, gate behouden, toggle identiek, verificaties OK.

