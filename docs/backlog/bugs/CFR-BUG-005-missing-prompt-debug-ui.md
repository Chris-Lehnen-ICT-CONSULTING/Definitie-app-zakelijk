Title: Prompt Debug UI ontbreekt – kan prompts niet meer analyseren

Status: Open
Severity: Medium
Componenten: UI, Definition Generator, Prompt Debug

Beschrijving
- Na recente UI-wijzigingen ontbreekt het debugblok waarmee de prompts (prompt template + ingevulde context) inzichtelijk zijn. Hierdoor is het niet mogelijk om de exacte prompt die naar het LLM gaat te analyseren of te reproduceren.

Reproductiestappen
1) Start de app en ga naar de tab “🚀 Definitie Generatie”.
2) Genereer een definitie via de Quick Actions of hoofdknop.
3) Zoek naar een “Prompt Debug”/“Prompt Inspectie” sectie of expander.
4) Er is geen sectie zichtbaar met de prompt template en ingevulde waarden.

Verwacht gedrag
- Een duidelijke “Prompt Debug” sectie (expander) waarin zichtbaar is:
  - De gebruikte prompt template (inclusief placeholders)
  - De ingevulde context (organisatorisch, juridisch, wettelijk)
  - Eventuele extra metadata (model, temperatuur, tokens)

Huidig gedrag
- Geen prompt debug sectie aanwezig. Analyse en troubleshooting van prompt-opbouw is niet mogelijk.

Context/Analyse
- De module `ui.components.prompt_debug_section` bestaat nog en wordt in `DefinitionGeneratorTab._render_generation_results` geïmporteerd, maar de zichtbaarheid is afhankelijk van `agent_result` velden en/of `saved_record.metadata['prompt_template']`.
- In het nieuwe V2-pad wordt de template mogelijk niet (meer) opgeslagen in `saved_record.metadata` en/of niet op de verwachte sleutel (`prompt_template`), waardoor de UI niets toont.

Mogelijke Oorzaken
- Ontbrekende mapping van prompt-velden in de V2 service output.
- `saved_record.metadata` bevat geen `prompt_template` of gebruikt een andere sleutelnaam.
- De debugsectie wordt pas getoond als `agent_result` een bepaalde structuur heeft (dict met specifieke keys) die niet geleverd wordt.

Acceptatiecriteria
- Na generatie is er altijd een “Prompt Debug” expander zichtbaar met minimaal:
  - De uiteindelijke prompt (string) die naar het model is gestuurd.
  - De belangrijkste context-velden die in de prompt zijn ingevuld.
- Werkt voor zowel legacy- als V2-servicepad.

Referenties
- `src/ui/components/definition_generator_tab.py` (prompt debug integratie)
- `src/ui/components/prompt_debug_section.py`
- `src/ui/tabbed_interface.py` (V2 pad en opslag van metadata)

