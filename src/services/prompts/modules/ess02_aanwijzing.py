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

Open contractgrens (DEF-750, A): het enkelvoudige uitvoercontract kent geen
actieve verduidelijkings- of afbreekroute, en de generieke ESS-02-uitkomst
`review_required` registreert géén specifiek ontbrekende keuze of
bronconflict (het reviewitem is met en zonder conflictbronnen gelijk). Deze
instructie is dus normatief, geen werkende verduidelijking; de route hoort
bij de bron-/contexttegenspraak-als-verduidelijkingsvraag van DEF-751 (B)
en het gedeelde resultaat-/beoordelingscontract van DEF-624.
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
    "modelvoorstel geldt niet als bevestiging."
)
