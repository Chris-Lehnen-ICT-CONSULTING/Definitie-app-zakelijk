Title: Validatiedetails: AttributeError door dict i.p.v. object met `overall_score`

Status: Open
Severity: High (UI-crash in resultaten)
Componenten: UI, Validation, Definition Generator

Beschrijving
- In de resultaten-sectie verschijnt “✅ Kwaliteitstoetsing”, gevolgd door een algemene tab-fout. In de debug-details staat:
  - Error type: AttributeError
  - Error message: 'dict' object has no attribute 'overall_score'

Reproductiestappen
1) Genereer een definitie via de hoofdknop (nieuwe services geactiveerd).
2) Ga naar tab “🚀 Definitie Generatie”.
3) Observeer foutmelding in de tab en debug-details.

Verwacht gedrag
- Validatieresultaten worden getoond zonder fouten, ongeacht of het resultaat een dict of object is.

Huidig gedrag
- `_render_validation_results` verwacht een object met attribuut `overall_score`, maar ontvangt een dict (V2 pad). Hierdoor ontstaat een AttributeError en faalt de tab-rendering.

Context/Analyse
- In `tabbed_interface._handle_definition_generation` worden gedetailleerde toetsresultaten via `toets_definitie()` berekend en in session state `beoordeling_gen` gezet.
- Tegelijkertijd checkt `DefinitionGeneratorTab._render_generation_results` op `agent_result.get("validation_details")` en geeft dat door aan `_render_validation_results`, die veronderstelt dat het een object is met `overall_score`.
- In het V2 pad is `validation_details` een dict/JSON‑achtige structuur, niet een object met attributen.

Mogelijke Oplossingen
- Adapter toevoegen: detecteer dict‑vorm en gebruik `validation_details.get("overall_score")` enz.
- Of converteer dict → dataclass/Typed object voordat `_render_validation_results` aangeroepen wordt.
- Isolatie van sectie-fouten: vang exceptions binnen de validatie-rendering, zodat de rest van de tab blijft werken.

Acceptatiecriteria
- Geen AttributeError meer wanneer `validation_details` een dict is.
- Validatieresultaten (overall score en details) worden consistent getoond.
- Sectie-fouten breken de hele tab niet.

Referenties
- `src/ui/components/definition_generator_tab.py` (`_render_validation_results`)
- `src/ui/tabbed_interface.py` (plaatsen waar validatie wordt uitgevoerd en in state gezet)
