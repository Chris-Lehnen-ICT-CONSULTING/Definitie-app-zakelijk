---
canonical: true
status: active
owner: platform
last_verified: 2025-09-19
applies_to: definitie-app@current
---

# Web Lookup Testcases (UI + Script)

## Voorbereiding
- Zet timeout voor kwaliteit: `export WEB_LOOKUP_TIMEOUT_SECONDS=10.0`
- Start applicatie: `streamlit run src/main.py`
- In de Generator‑tab, onder “📚 Gebruikte Bronnen”, vink aan:
  - “🐛 SRU/WL debug: Toon lookup attempts (JSON)”
  - “🐛 Debug: Toon ruwe web_lookup data (JSON)”

## Contextprofielen
- Profiel A (OM/Strafrecht)
  - Organisatorisch: `OM`
  - Juridisch: `Strafrecht`
  - Wettelijk: `Wetboek van Strafrecht`, `Wetboek van Strafvordering`
- Profiel B (ZM/Strafrecht)
  - Organisatorisch: `ZM`
  - Juridisch: `Strafrecht`
  - Wettelijk: `Wetboek van Strafvordering`
- Profiel C (DJI/Bestuursrecht)
  - Organisatorisch: `DJI`
  - Juridisch: `Bestuursrecht`
  - Wettelijk: `Awb`

## Begrippen per profiel
- Profiel A (OM/Strafrecht)
  - `vonnistekst` (let op fallback naar `vonnis` / `uitspraak`)
  - `tenlastelegging`
  - `strafbeschikking`
  - `bevel` (evt. specifieker: `bevel tot bewaring`)
  - `opsporing`
- Profiel B (ZM/Strafrecht)
  - `vonnis`
  - `uitspraak`
  - `veroordeling`
  - `voorlopige hechtenis`
  - `dagvaarding`
- Profiel C (DJI/Bestuursrecht)
  - `beschikking`
  - `vergunning`
  - `last onder dwangsom`
  - `bezwaar`
  - `besluit`

## Verwachte uitkomsten (per test)
- `selected_sources` bevat juridische providers: `overheid`, `rechtspraak`, `overheid_zoek` (in die volgorde), daarna `wikipedia`, `wiktionary`.
- `attempts` toont voor SRU de endpoints en geëvalueerde termen (incl. fallback bij `vonnistekst`).
- `web_lookup_status = success` en `web_sources_count ≥ 1`.
- Onder “📚 Gebruikte Bronnen” is minimaal 1 bron zichtbaar met badge “→ In prompt”.
- Snippet‑injectie onder “### Contextinformatie uit bronnen:” (max. configurabel via `prompt_augmentation`).

## Beoordelingscriteria (Pass/Fail)
- PASS: Minstens 1 juridische bron (Overheid/Rechtspraak/Zoekservice) wordt gevonden en ≥1 snippet is in de prompt gezet.
- CONDITIONAL PASS: Alleen Wikipedia, maar legal endpoints gaven `no_results` ondanks 10s timeout.
- FAIL: `web_lookup_status = no_results` en `attempts` tonen geen geslaagde juridische hit (bij juridische profielen).

## Script (optioneel)
Gebruik het testscript voor snelle checks buiten de UI:

```bash
# Stel timeout in (indien gewenst)
export WEB_LOOKUP_TIMEOUT_SECONDS=10.0

# Voorbeelden
python scripts/test_web_lookup.py "vonnistekst"
python scripts/test_web_lookup.py "tenlastelegging"
python scripts/test_web_lookup.py "beschikking"
```

## Notities en tuning
- Timeout: default 10.0s (override via `WEB_LOOKUP_TIMEOUT_SECONDS`).
- Prompt‑augmentatie: tune in `config/web_lookup_defaults.yaml` (max_snippets, total_token_budget, prioritize_juridical).
- Indien termen structureel `no_results` geven in SRU:
  - Voeg gerichte fallbacktermen toe (bijv. `vonnistekst` → `vonnis`, `uitspraak`).
  - Verruim de SRU‑query of gebruik `overheid_zoek` endpoint als primair voor specifieke termen.

