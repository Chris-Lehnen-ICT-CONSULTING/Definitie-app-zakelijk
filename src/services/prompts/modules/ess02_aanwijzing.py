"""De gedeelde ESS-02-generatieaanwijzing (DEF-750).

Eén tekst voor alle promptplaatsen die ESS-02 raken (regelkaart in
`JSONBasedRulesModule`, betekenislaagsectie in `SemanticCategorisationModule`),
zodat checklist, regeltransformatie en categoriehints niet elk een eigen
variant dragen die alsnog vier exclusieve keuzes of een markerplicht
suggereert. Tekst volgens de vastgestelde ESS-02-besluiten (DEF-749): niveau
en aard apart, vier overlappende richtingen als hulp, geen verplicht
woordenlijstje, opgegeven categorie als te controleren betekenisclaim.

Onvoldoende grond (reviewcorrecties P2): het uitvoercontract is één zin met
uitsluitend de definitiekern, zonder toelichting. De aanwijzing vraagt
daarom géén afzonderlijke melding in of naast de uitvoer — dat zou met het
contract botsen. Twee gevallen blijven onderscheiden:

- onvoldoende grond zónder werkelijke tegenspraak: één voorlopige kandidaat
  voor de best ondersteunde lezing, zonder vermenging van betekenislagen en
  zonder verzonnen grond (dezelfde lijn als ESS-01/DEF-746: hoogstens een
  herkenbaar voorlopig voorstel; grond, onzekerheid of toelichting niet in de
  definitiekern);
- werkelijke tegenspraak tussen bronnen of context over de bedoelde
  betekenislaag: besluit C3 — eerst verduidelijken; niet stil kiezen; een
  opgegeven categorie, standaardwaarde of modelvoorstel is geen bevestiging.

Contractgrens (DEF-750, A — historie): het enkelvoudige uitvoercontract kende
geen actieve verduidelijkings- of afbreekroute, en de generieke ESS-02-uitkomst
`review_required` registreert géén specifiek ontbrekende keuze of
bronconflict (het reviewitem is met en zonder conflictbronnen gelijk). De
instructie was dus normatief, geen werkende verduidelijking.

Gesloten in DEF-751 stap 2: het additieve modelconflictcontract
(`services.modelantwoord`, instructie in `DefinitionTaskModule`) geeft het
model één strikt parseerbare uitzondering — bij werkelijke tegenspraak géén
definitie maar een melding met gerichte vraag en minstens twee lezingen met
aangeleverde grond. De orchestrator takt die melding af vóór voorbeelden,
opschoning, validatie en opslag; de UI toont haar als melding van het model
en vraagt een expliciete verduidelijking, die als DATA in het contextblok
naar een nieuwe generatie reist. Die verduidelijking is de keuze van de
bedoelde betekenislaag door de gebruiker: een bedoeling, geen bronfeit en
geen ESS-02-oordeel — ESS-02 blijft binnen de bestaande expertbeoordeling
te beoordelen (DEF-624). Wat géén conflict is (overlap tussen richtingen,
eigen onzekerheid, ontbrekend label) blijft de gewone voorlopige generatie
van DEF-750.
"""

from __future__ import annotations

__all__ = ["GEDEELDE_ESS02_AANWIJZING"]

GEDEELDE_ESS02_AANWIJZING = (
    "Definieer de onderbouwde bedoelde betekenis: laat bovenbegrip en kenmerken "
    "duidelijk maken of de tekst een algemeen begrip of één bepaald ding (ook "
    "abstract, zoals een bepaalde methode of regeling) of voorval betreft, en waar "
    "relevant of de kern een activiteit of haar uitkomst is. Gebruik een "
    "inhoudelijk passend zelfstandig naamwoord of naamwoordgroep; type, exemplaar, "
    "proces en resultaat zijn geen verplicht woordenlijstje. Een activiteit mag "
    "haar uitkomst noemen zonder van betekenis te veranderen. Een opgegeven "
    "categorie is een te controleren betekenisclaim, geen toestemming om "
    "strijdige broninhoud te herschrijven. Bij onvoldoende grond zonder werkelijke "
    "tegenspraak: verzin geen context, bron, identiteit of expertbesluit, vermeng "
    "de betekenislagen niet als alternatief en geef één voorlopige kandidaat voor "
    "de door context en bronnen best ondersteunde lezing, zonder melding, "
    "toelichting of tweede lezing in de zin; ESS-02 blijft dan nog te beoordelen. "
    "Bij werkelijke tegenspraak tussen bronnen of context over de bedoelde "
    "betekenislaag: kies niet stil tussen de lezingen; de betekenis moet eerst "
    "worden verduidelijkt en een opgegeven categorie, standaardwaarde of "
    "modelvoorstel geldt niet als bevestiging. Een expliciete verduidelijking "
    "van de gebruiker in het contextblok is diens bedoeling (keuze van de "
    "betekenislaag), geen bronfeit: definieer die lezing zonder de bronnen te "
    "herschrijven."
)
