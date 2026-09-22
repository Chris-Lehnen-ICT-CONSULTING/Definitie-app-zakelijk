# ESS-03 — browsercontrole eindstand (v3, Opus 5)

Coördinator (Cowork-Claude) bediende de echte app via de ingebouwde browser van de Claude-desktopapp op 22-09-2026, ca. 05:05–05:15 (lokale tijd Mac). Verse Streamlit-start uit de werkboom op HEAD `c0d3423ab` (feature/DEF-766-ess03-ai-beoordeling), http://127.0.0.1:8546, log `/tmp/def766-ai-20260921/browser-app-v3-start.log`, omgeving geladen uit de project-`.env` (sleutel niet ingezien). Provider Anthropic, model `claude-opus-5` (sidebar). Alleen synthetisch lokaal record ID 3 (`meetobject`), geen productiegegevens. Server na afloop gestopt.

## Stappen en waarnemingen

1. **Heropenen record 3 (uitgangssituatie).** Opgeslagen AI-sectie toont de eerdere pass (Opus 4.8, prompt 2, met later gewiste verduidelijking) expliciet als **historisch en niet toegepast** ("eerdere beoordeling geldt niet meer: tekst, context, term, bedoelde betekenis of bronnen zijn gewijzigd"). Geen modelcall.
2. **Valideren met lege ESS-03-verduidelijking (call 1).** Uitkomst: **Onvoldoende informatie — zonder cijfer**, `claude-opus-5`, onderbouwing benoemt de ontbrekende registratieconventie, precies één gerichte vraag, bewijs uit definitie en toelichting, vervolgstap "beantwoord de vraag in de ESS-03-verduidelijking en toets opnieuw; de definitie wordt niet automatisch herschreven". Totaalscore blijft "niet beschikbaar" (DEF-743); ESS-03 in de lijst regels zonder cijfer.
3. **Verduidelijking invullen** (vooraf vastgelegde tekst uit `browser-v2-clarification-input.md`) **en opnieuw Valideren (call 2).** Uitkomst: **Voldoet — zonder cijfer**, `claude-opus-5`; onderbouwing verwijst naar de verduidelijking (fysieke eenheid, register R, één nummer per installatie, continuïteit bij onderdeelvervanging). Definitietekst ongewijzigd.
4. **Opslaan.** Versie v5 → **v6**. Database: `generation_prompt_data.ess03_verduidelijking` = de ingevulde tekst; `ess03_assessment.status=assessed`, `verdict=pass`, `attribution.model=claude-opus-5`, `attribution.stop_reason=end_turn`, `prompt_version=ess03-assess/2`; historie 4 eerdere beoordelingen behouden.
5. **Annuleren → opnieuw zoeken → Bewerk geselecteerde (heropenen).** Verduidelijking staat in het veld; opgeslagen AI-sectie toont **Voldoet als actueel** met dezelfde onderbouwing. Geen modelcall (serverlog: precies 2 POST-requests naar de API in deze sessie).
6. **Definitietekst wijzigen zonder opslaan** (" (proefwijziging)" toegevoegd). Opgeslagen AI-sectie toont de pass direct als **historisch/niet toegepast**; geen modelcall. Daarna **Annuleren** zonder opslaan: database blijft v6 met ongewijzigde tekst.

## Conclusie

Het enige sinds de modelwissel niet-gemeten gebruikerspad — onvoldoende informatie → verduidelijking → opnieuw toetsen → opslaan → heropenen → stale bij wijziging — werkt op Opus 5 met de thinking-guard zoals bedoeld: vier-uitkomstenweergave zonder cijfer, één vraag, geen automatische herschrijving, duurzame opslag met modelbinding en `stop_reason`, correcte actualiteit bij heropenen en bij wijziging.

Niet in deze fase gemeten: negatieve ESS-03 met echte vaststel-/exportactie (afgedekt door de actieproef-tests en de eerdere browserfasen); NA- en generatiepad (browserbewijs fase 1, Opus 4.8; eindset op Opus 5).

## Budget

2 beoordelingscalls in deze fase. Totaal: 26 (t/m browser v2) + 2 (rookproef) + 30 (eindset) + 2 = **60 van 60**.

## Bekende, niet-ESS-03 restpunten

- Auto-save-fouten door ontbrekende tabel `definitie_drafts` in de lokale testdatabase (pre-existing, buiten scope; handmatig opslaan werkt).
- Voorbeelden/synoniemen aan record 3 stammen nog van het eerdere begrip "kiezel" (testdata, geen ESS-03-gedrag).
