# DEF-835 INT-02 O2 — processtatus uitvoering v13

7 oktober 2026. Vervangt `processtatus-uitvoering-v12.md` (28-09) als actuele processtatus.

## Stand

- O1 (DEF-771) en de O2-beoordelingsdienst (DEF-835, PR #488, 29-09) staan op main. De O2-dienst is niet geactiveerd; de app gebruikt de O1-reviewroute.
- Na de merge is in deze werkboom de kwalificatie voorbereid: goldset van 40 synthetische gevallen (24 ontwikkeling, 16 hold-out) met de labelbesluiten van Chris, een eerste technische modelproef (C107 onterecht `fail` en een citaatoffset één codepunt te laat) en de promptcorrectie naar `def835-int02-prompt/2`.
- 07-10-2026: werk gecontroleerd en besluiten van Chris vastgelegd in `besluit-chris-promptcorrectie-en-v3-v1.md`:
  1. code-formulering van prompt /2 geaccepteerd;
  2. één besluitbestand;
  3. aandachtspunt "meerdere passages" volgen in de proef, nu niet herstellen;
  4. commit op `feature/DEF-835-int02-o2`, push als back-up, geen PR/merge;
  5. deze processtatus v13;
  6. akkoord op v3-proef fase 1 (C105/C107/C112, maximaal 3 calls), daarna stoppen.

## Volgende actie

Fase 1 van de v3-proef draaien op de vastgelegde commit; uitkomst met Chris bespreken (inclusief aandachtspunt 3); daarna afzonderlijk akkoord van Chris voor ontwikkeling en hold-out.

## Actuele documenten

- `besluit-chris-promptcorrectie-en-v3-v1.md` — besluiten 07-10.
- `takenlijst-v51.md` — laatste takenlijst van de coördinator (30-09).
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-voorstel-v3.md` en `kwalificatie-manifest-v3.json` — de proef.

## Achterhaald (ongewijzigd bewaard)

- `processtatus-uitvoering-v12.md` (28-09): stand van vóór goldset, labelronde en prompt /2; achterhaald door deze v13.
- `goldset-voorbereiding/labelronde-v1/takenlijst-v14.md` (30-09): het daar gevraagde manifestakkoord is vervangen door het v3-manifest en besluit 6.
- `goldset-voorbereiding/herwerking-v1/uitvoeringsstatus-v1.md` (29-09): de vastgelopen herwerking is later afgerond; G041–G052 staan in het bevroren v3-manifest.
