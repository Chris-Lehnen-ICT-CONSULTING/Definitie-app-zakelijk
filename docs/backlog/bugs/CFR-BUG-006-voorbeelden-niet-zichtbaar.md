Title: Voorbeelden/tegenvoorbeelden ontbreken in Definitie Generatie resultaten

Status: Open
Severity: High (functionaliteit ontbreekt)
Componenten: UI, Definition Generator, Voorbeelden

Beschrijving
- Na het genereren van een definitie worden geen voorbeelden (voorbeeldzinnen), tegenvoorbeelden, synoniemen/antoniemen of toelichting getoond. Er is ook geen lege placeholder of melding dat deze ontbreken.

Reproductiestappen
1) Start de app en voer een begrip + context in.
2) Klik “Genereer Definitie”.
3) Ga naar “🚀 Definitie Generatie” resultaten-sectie.
4) Let op dat er geen sectie “Voorbeelden” of subsecties (tegenvoorbeelden, synoniemen) zichtbaar worden.

Verwacht gedrag
- Een sectie “Voorbeelden” met de door de generator teruggegeven voorbeelden-structuur:
  - voorbeeldzinnen
  - praktijkvoorbeelden
  - tegenvoorbeelden
  - synoniemen/antoniemen
  - toelichting
- Indien leeg: toon een duidelijke placeholder/melding.

Huidig gedrag
- Geen sectie zichtbaar en geen placeholder; UI toont niets over voorbeelden.

Context/Analyse
- In `DefinitionGeneratorTab._render_generation_results` wordt alleen gerenderd als `agent_result.get("voorbeelden")` bestaat.
- In het nieuwe V2-pad lijkt `agent_result` geen `voorbeelden` key te bevatten, of de key is anders benoemd.
- Er is logica die de voorbeelden bij aanwezigheid in session state zet (export), maar niet wanneer de key ontbreekt.

Mogelijke Oorzaken
- V2 service vult `voorbeelden` niet (meer) aan in het resultaat, of gebruikt andere sleutel(s).
- Mapping van service-output naar UI ontbreekt.

Acceptatiecriteria
- Bij succesvolle generatie verschijnen voorbeelden-secties wanneer de service ze levert.
- Als de service geen voorbeelden levert, toont de UI een nette placeholder (“Geen voorbeelden beschikbaar”).
- Werkt voor zowel legacy- als V2 servicepad.

Referenties
- `src/ui/components/definition_generator_tab.py` (rendering van voorbeelden)
- `src/services/unified_definition_service_v2.py` (of service die `agent_result` vormgeeft)

