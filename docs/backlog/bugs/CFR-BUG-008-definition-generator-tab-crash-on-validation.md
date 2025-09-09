Title: Definitie Generatie-tab crasht wanneer validatiesectie faalt

Status: Open
Severity: Medium-High (UI-robustheid)
Componenten: UI, Definition Generator, Error Handling

Beschrijving
- Bij het renderen van de “🚀 Definitie Generatie”-tab verschijnt bovenin “✅ Kwaliteitstoetsing”, gevolgd door een generieke foutmelding “❌ Er is een fout opgetreden in tab '🚀 Definitie Generatie'”.
- Dit wijst erop dat een fout in een subsectie (waarschijnlijk validatie) niet lokaal wordt afgehandeld en de gehele tab-rendering onderbreekt.

Reproductiestappen
1) Genereer een definitie (V2 pad).
2) Open de “🚀 Definitie Generatie”-tab.
3) Observeer de algemene tab-foutmelding.

Verwacht gedrag
- Een fout in de validatie- of bronnen-sectie mag de rest van de tab niet breken. De sectie toont een nette foutmelding en de rest blijft zichtbaar (definitie, categorie, bronnen).

Huidig gedrag
- Een uitzondering in een subsectie zorgt voor een globale tab-fout.

Context/Analyse
- `_render_tab_content` heeft een try/except op tab-niveau, maar subsectie-methodes binnen `DefinitionGeneratorTab` hebben beperkte isolatie.
- Combineer met CFR-BUG-007 (dict vs object) voor de primaire oorzaak, maar los hiervan moet isolatie de UI robuuster maken.

Mogelijke Oplossingen
- Binnen `DefinitionGeneratorTab._render_generation_results` per sectie try/except toevoegen (validatie, voorbeelden, bronnen), met logging en gebruikersvriendelijke melding.

Acceptatiecriteria
- Een fout in één sectie veroorzaakt geen globale tab-fout.
- Gebruiker ziet per sectie een nette foutmelding met optie om details te tonen.

Referenties
- `src/ui/components/definition_generator_tab.py` (sectie-rendering)
- `src/ui/tabbed_interface.py` (tab error handling)

