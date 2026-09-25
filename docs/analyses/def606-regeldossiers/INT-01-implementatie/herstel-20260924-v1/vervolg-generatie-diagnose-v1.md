# DEF-770 vervolg — diagnose betekenisverlies bij generatie (G24)

Vastgelegd vóór implementatie. Bronnen: `effectproeven-herstel-20260924-v1/g24-rapport-v1.md`, `g24-invoer-v1.json` (G02–G05 bronpassages), `g24-generaties-v1/G0[2-5]__{oud,nieuw}__h{1,2}.json` (uitvoer) en `logs/def770-eindproeven/g24-voorbereiding-contract4-v1.json`. De volledige G05-prompt staat in `diagnose-prompt-G05-contract4.txt`, uitgepakt met `jq -r '.per_invoer[4].prompt'`. De beoordelaarsvelden stonden niet in de prompt: `beoordelaarsvelden_letterlijk_in_prompt` is leeg, op de bronnamen van G03 en de negatie van G06 na, die ook letterlijk in de bron staan.

## Waargenomen verlies, per dossier (bron → nieuwe uitvoer)

| Dossier | Bron | Nieuwe uitvoer | Soort verlies |
|---|---|---|---|
| G05 | "De twee uitkomsten **worden samen bewaard**." | "**samenhorend**/samenhangend tweetal meetuitkomsten" (h1 en h2) | Een bronhandeling is vervangen door een vagere relatie-eigenschap. |
| G03 | "Die invoertijd **hoeft niet gelijk te zijn** aan die van het oorspronkelijke record." | "eigen invoertijd **die afwijkt van** die van het oorspronkelijke record" (h1) | Een niet-verplichting is een verplicht kenmerk geworden (vernauwing). |
| G02 | "aankomsttijd afhangt van **aansluiting op** een andere … bevestigde rit" | in één herhaling "afhangt van een … bevestigde rit" | Het relatiewoord is weggevallen; de relatie is algemener geworden. |
| G04 | "meerdere **kunnen** tegelijk worden geregistreerd" / "de medewerker vermeldt welke …" | "waarbij elke aangetroffen omstandigheid **afzonderlijk wordt geregistreerd**" (h2, onbeslist) | Een mogelijkheid of werkwijze is als kenmerk-eis in de kern terechtgekomen. |

## Waar werken de instructies tegen betekenisbehoud?

1. **ARAI-04/ARAI-04SUB1 leren letterlijk "mogelijkheid → feit".** De prompt toont onder ARAI-04 ✅ "maatregel die toegang beperkt" en ❌ "maatregel die toegang kan beperken", samen met de instructie "Vermijd modale hulpwerkwoorden zoals 'kan', 'moet', 'mag', 'zal'". Die kaart komt ruim vóór INT-01 en geeft geen aanwijzing wat te doen als de bron zelf modaal is ("hoeft niet", "kan", "mag"). De tegenregel in INT-01 ("maak van een mogelijkheid geen feit …") staat pas in een lange INT-01-instructie. Voor een niet-verplichting ("hoeft niet") zegt die tegenregel niets. G03 en G04 passen precies bij deze spanning: het modale bronwerkwoord verdwijnt en er komt een feit of eis voor in de plaats.
2. **Stijldruk zonder terugkoppeling naar de bron.** "Actieve vorm prefereren", "Gebruik komma's spaarzaam", STR-ORG-001 ("vermijd extreem lange zinnen") en de compactheidsopdracht van INT-01 duwen naar kortere, samengevatte formuleringen. Nergens staat een concrete handeling om, vóór de definitieve zin, de bepalende bronhandelingen en relaties naast de formulering te leggen. De afsluitende KWALITEITSCONTROLE controleert alleen ESS-01 (functie/doel), "behoud de gegeven betekenis" en CON-01. "Behoud de betekenis" is een slogan zonder controlehandeling. G05 (passieve bronhandeling → bijvoeglijk "samenhorend") en G02 (relatiewoord weggelaten) passen hierbij.
3. **Wat níet het probleem is.** Betekenisbehoud wordt al veel genoemd: INT-01, CON-02 "Behoud … bepalende kenmerken, beperkingen en uitzonderingen", KWALITEITSCONTROLE. Nog een synonieme slogan toevoegen lost niets op; zie de opdracht.

## Hypothese en concrete algemene correctie

**Hypothese.** Het verlies komt vooral uit (a) de onopgeloste voorrangsvraag tussen de modaliteitsregel en de bronmodaliteit en (b) het ontbreken van een operationele eindcontrole op drie concrete betekenisdragers: bronhandeling, relatie en modaliteit. De instructies vragen betekenisbehoud, maar zeggen niet welke tekstdelen je tegen de bron moet houden en wat voorgaat bij een conflict met een stijlregel.

**Correctie, beperkt en zonder extra modelcall of domeintermen:**

1. **ARAI-04/ARAI-04SUB1-instructie** in de promptbuilder (`json_based_rules_module`): modale werkwoorden blijven te vermijden, maar met één operationele voorrangsregel. Drukt de bron een mogelijkheid, toestemming of niet-verplichting uit, dan wordt die geen feit of eis. Is zij niet afbakenend, laat haar dan weg. Anders druk je haar zonder modaal werkwoord uit ("-baar", "al dan niet", "ongeacht").
2. **KWALITEITSCONTROLE** (`definition_task_module`): een gerichte controle vóór de definitieve formulering. Leg de zin naast de bepalende bronpassages en controleer:
   - (1) een bepalende bronhandeling blijft een handeling met hetzelfde voorwerp, niet vervangen door een eigenschapswoord;
   - (2) een bepalende relatie behoudt haar relatiewoord en richting;
   - (3) de modaliteit blijft gelijk: geen feit of eis uit een mogelijkheid of niet-verplichting, geen mogelijkheid uit een eis.

   Deze controle gaat vóór stijlvoorkeuren (actieve vorm, modale werkwoorden vermijden, compactheid). Een werkafspraak of mogelijkheid die het begrip niet afbakent, laat je weg in plaats van haar als eis op te nemen. De voorbeelden zijn generiek en komen niet uit G24. De uitvoer blijft uitsluitend de definitiekern.
3. **Skills uitlijnen.** `definitie-toetsregels/reference.md` (ARAI-04-rij en INT-01-normtekst) en `definitie-nederlandse-definities` (tabel "Modale vaagheid" en INT-01-sectie) krijgen dezelfde voorrangsregel en dezelfde eindcontrole, zodat app en skills hetzelfde zeggen.

**Niet gedaan en bewust buiten scope:** ARAI-04.json (regelrecord, voorbeelden) wijzigen; een nieuwe promptsectie of een nieuw ontwerp; evaluatormetadata (`beschermde_kenmerken`, `bedoelde_betekenis`) als productie-invoer; een extra verificatie-modelcall.

## Wat unit-tests wel en niet bewijzen

- **Wel te testen:**
  - dat de nieuwe tekst echt in de volledige prompt van de echte `PromptServiceV2` staat, in elke contextcombinatie, precies één keer, vóór de definitieopdracht-afsluiting;
  - dat de ARAI-04-kaart de voorrangsregel draagt;
  - dat geen G24-fixturetermen of evaluatorvelden in productiecode of prompt staan;
  - dat de uitvoercontracten (één zin, geen toelichting) intact blijven.
- **Alleen via een nieuwe onafhankelijke effectproef te bewijzen:** of het model hierdoor minder betekenisfouten maakt. Of een specifieke zin een specifiek verschil veroorzaakt, is ook met een proef niet causaal toe te wijzen. Promptunittests zijn geen effectbewijs.
