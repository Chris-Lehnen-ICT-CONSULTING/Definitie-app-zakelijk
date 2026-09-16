"""De gedeelde ESS-02-generatieaanwijzing (DEF-750).

Eén tekst voor alle promptplaatsen die ESS-02 raken (regelkaart in
`JSONBasedRulesModule`, betekenislaagsectie in `SemanticCategorisationModule`),
zodat checklist, regeltransformatie en categoriehints niet elk een eigen
variant dragen die alsnog vier exclusieve keuzes of een markerplicht
suggereert. Tekst volgens de vastgestelde ESS-02-besluiten (DEF-749): niveau
en aard apart, vier overlappende richtingen als hulp, geen verplicht
woordenlijstje, opgegeven categorie als te controleren betekenisclaim.

Onvoldoende grond (reviewcorrectie P2): het uitvoercontract is één zin met
uitsluitend de definitiekern, zonder toelichting. De aanwijzing vraagt
daarom géén afzonderlijke melding in of naast de uitvoer — dat zou met het
contract botsen — maar één voorlopige kandidaat zonder vermenging van
betekenislagen en zonder verzonnen grond. De ontbrekende keuze blijft
zichtbaar via de ESS-02-beoordeling zelf (`review_required`, zie
`JudgmentReviewEvaluator._ess02_reden`), niet via de modeluitvoer. Dat is
dezelfde lijn als ESS-01 (DEF-746): hoogstens een herkenbaar voorlopig
voorstel; grond, onzekerheid of toelichting niet in de definitiekern.
"""

from __future__ import annotations

__all__ = ["GEDEELDE_ESS02_AANWIJZING"]

GEDEELDE_ESS02_AANWIJZING = (
    "Definieer de onderbouwde bedoelde betekenis. Laat het bovenbegrip en de "
    "kenmerken duidelijk maken of de tekst een algemeen begrip of één bepaald ding "
    "(ook abstract, zoals een bepaalde methode of regeling) of voorval betreft, en "
    "waar relevant of de kern een activiteit of haar uitkomst is. Gebruik een "
    "inhoudelijk passend zelfstandig naamwoord of een passende naamwoordgroep; "
    "type, exemplaar, proces en resultaat zijn geen verplicht woordenlijstje. Een "
    "activiteit mag haar uitkomst noemen zonder van betekenis te veranderen. "
    "Behandel een opgegeven categorie als te controleren betekenisclaim, niet als "
    "toestemming om strijdige broninhoud te herschrijven. Bij onvoldoende grond "
    "voor een noodzakelijke betekeniskeuze: verzin geen context, bron, identiteit "
    "of expertbesluit, vermeng de betekenislagen niet als alternatief en geef één "
    "voorlopige kandidaat voor de door context en bronnen best ondersteunde "
    "lezing, zonder melding, toelichting of tweede lezing in de zin; de "
    "ESS-02-beoordeling blijft dan nog te beoordelen."
)
