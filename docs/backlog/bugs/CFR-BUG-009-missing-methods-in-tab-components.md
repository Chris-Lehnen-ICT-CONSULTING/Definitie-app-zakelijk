Title: Ontbrekende methodes in tab-componenten gedetecteerd (“has no attribute”)

Status: Open
Severity: Medium
Componenten: UI, Tab Components

Beschrijving
- Tijdens het renderen van tabs verschijnt een hint: “💡 Dit lijkt op een ontbrekende method. Controleer of alle tab methods geïmplementeerd zijn.”
- Dit wordt getriggerd wanneer een AttributeError van het type “has no attribute …” optreedt in `_render_tab_content`.

Reproductiestappen
1) Start de UI en laat alle tabs renderen.
2) Wanneer een tab-component een niet-bestaande methode aanroept (bijv. `render()` ontbreekt of hernoemd), verschijnt de hint.

Verwacht gedrag
- Tab-componenten implementeren consistente, verwachte methodes (zoals `render()`), of de UI vangt mismatch af met een duidelijke melding én fallbacks.

Huidig gedrag
- Hint wijst op mogelijk ontbrekende methodes in een of meerdere tab-componenten. Dit kan regressies maskeren.

Context/Analyse
- Recent zijn componenten hernoemd of vervangen (bijv. context selector). Andere tabs kunnen nog legacy paden/methodes gebruiken.
- Controle nodig op alle tab-classes (`ExpertReviewTab`, `HistoryTab`, etc.) of ze de verwachtte surface (render-methode) exporteren, en of import-paden correct zijn.

Mogelijke Oplossingen
- Uniformeer tab-interface (abstracte basis of protocol) en test op aanwezigheid van `render` voor aanroep.
- Voeg ontwikkelaarshulp toe: op tab-fout een lijstje met vereiste methods en daadwerkelijk aanwezige attributen.

Acceptatiecriteria
- Geen “has no attribute” hints meer tijdens normale flow.
- Als een tab ontbrekende methodes heeft, toont de UI een duidelijke, actiegerichte melding zonder crash.

Referenties
- `src/ui/tabbed_interface.py` (`_render_tab_content` error handling)
- `src/ui/components/*_tab.py`

