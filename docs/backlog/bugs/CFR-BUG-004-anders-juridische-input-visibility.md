---
id: CFR-BUG-004
canonical: true
status: active
owner: ui
last_verified: 2025-09-09
applies_to: definitie-app@current
severity: HOOG
impact: Juridische custom context niet in te voeren via UI
epic: EPIC-010
related_stories:
- US-042
- US-043
created: 2025-09-09
---

# CFR-BUG-004: “Anders…” invoerveld ontbreekt bij Juridische context

## Samenvatting

Bij het selecteren van “Anders…” onder “⚖️ Juridische context” verschijnt soms geen tekstinvoerveld om een custom waarde in te voeren. Dit lijkt alleen op te treden wanneer bij “📋 Organisatorische context” eerder “Anders…” gekozen is en/of daar al een custom waarde is ingevuld. Voor Organisatorisch werkt de “Anders…”-flow wel zoals verwacht.

## Status

- Status: OPEN
- Severity: HOOG (blokkeert invoer van juridische maatwerkcontext in bepaalde volgordes)
- Epic: EPIC-010 (Context Flow Refactoring)

## Omgeving

- UI: Streamlit
- Component: Enhanced Context Manager Selector
- Bestanden:
  - `src/ui/components/enhanced_context_manager_selector.py`
  - `src/ui/tabbed_interface.py`

## Stappen om te reproduceren

1. Open de app en ga naar “🎯 Context Configuratie”.
2. Onder “📋 Organisatorische context”: selecteer “Anders…”, voer een custom waarde in (bv. “Team Opsporing X”).
3. Ga vervolgens naar “⚖️ Juridische context”: selecteer “Anders…”.
4. Observeer: het tekstinvoerveld voor de juridische custom waarde verschijnt niet in bepaalde sessies/volgordes.

Opmerking: als “Anders…” en/of de custom waarde bij Organisatorisch wordt verwijderd, verschijnt het juridische invoerveld doorgaans weer.

## Verwacht gedrag

- Zodra “Anders…” in “⚖️ Juridische context” is geselecteerd, verschijnt altijd een tekstinvoerveld om een custom juridische waarde in te voeren, onafhankelijk van keuzes bij andere contexten.

## Feitelijk gedrag

- Het juridische tekstinvoerveld verschijnt niet consistent wanneer “Anders…” bij Organisatorisch reeds actief is of er een custom org-waarde staat.

## Impact

- Gebruikers kunnen geen custom juridische context invoeren in bepaalde volgordes → onvolledige/onjuiste context voor generatie en validatie.

## Root Cause Hypothese

- Key-collisions en rerun-interacties tussen widgets van verschillende kolommen:
  - Historisch gebruik van overlappende widget-keys (bv. `jur_multiselect`, `custom_jur_input`) en legacy `st.session_state` sleutels (`*_values`).
  - Een `st.rerun()` bij het invullen van een custom waarde kan de render-cyclus beïnvloeden, waardoor het juridische invoerveld niet (opnieuw) wordt getoond.

## Recente wijzigingen (mitigaties toegepast)

- Namespacing van widget-keys in enhanced selector (voorkomt key-collisions):
  - Multiselect keys: `cm_org_multiselect`, `cm_jur_multiselect`, `cm_wet_multiselect`
  - Custom input keys: `cm_custom_org_input`, `cm_custom_jur_input`, `cm_custom_wet_input`
- Verwijderen van `st.rerun()` bij het verwerken van custom invoer in `EnhancedContextManagerSelector`.

Commit/patch referenties:
- `src/ui/components/enhanced_context_manager_selector.py` – keys genamespace’d en rerun verwijderd
- `src/ui/tabbed_interface.py` – fallback naar legacy session state code verwijderd; ContextManager-only selector geactiveerd

## Actieplan (Proposed Fix)

1. Confirmatie in UI (rooktest) na namespacing en zonder `st.rerun()`:
   - Controleren dat het juridische invoerveld altijd verschijnt bij selectie “Anders…”, ongeacht organisatorische keuzes.
2. Verifiëren dat er geen resterende key-collisions zijn:
   - Scannen op gebruik van `jur_multiselect`, `custom_jur_input`, `jur_context_values` buiten de enhanced selector en ze neutraliseren/verwijderen indien nog in gebruik voor UI state.
3. Eventueel: fallback voor edge-cases
   - Als `st.multiselect` defaults/selection inconsistent raakt, forceer alleen lokale lijst-mutaties (zonder rerun) en schrijf via `ContextManager` door.
4. Tests uitbreiden/aanpassen:
   - Unit-test die simuleert: eerst org-Anders custom, daarna jur-Anders toont input.

## Verificatiestappen (DoD)

- [ ] Smoke test: juridische invoerveld verschijnt altijd na kiezen “Anders…”, ook wanneer organisatorisch ‘Anders…’ actief is met custom waarde.
- [ ] Geen crashes/“default not in options” fouten.
- [ ] Context wordt correct opgeslagen in `ContextManager` en gebruikt bij generatie/lookup.
- [ ] Geen key-collision logs of warnings in console.

## Gerelateerde artefacten

- Stories: US-042 (Anders custom input), US-043 (legacy routes verwijderen)
- Epic: EPIC-010 (Context Flow Refactoring)

## Wijzigingslog

| Datum       | Versie | Wijziging |
|-------------|--------|-----------|
| 09-09-2025  | 1.0    | Bug aangemaakt, mitigaties beschreven, DoD gedefinieerd |
