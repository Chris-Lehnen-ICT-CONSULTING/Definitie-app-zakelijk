# DEF-746 — technische specificatie ESS-01 A
Datum: 16 september 2026. Basis: origin/main 29b0900d4a7f501849d0963616b3f78106299aa3, vers opgehaald.
Werkboom: /Users/chrislehnen/.codex/worktrees/9415/Definitie-app.
Branch: feature/DEF-746-ess01-instructies.

Leidend: [vastgestelde besluiten en uitvoering](https://linear.app/definitie-app/document/ess-01-vastgestelde-besluiten-en-uitvoeringsspecificatie-16-september-b9d7124c361e). Gebruikersopdracht autoriseert pakket A, inclusief promptbuilders en meer dan vijf bestanden. K1–K4 blijven besloten; geen modelcalls of herstelactivatie.

## Technische antwoorden
1. Het bestaande ReviewRequirement-contract bevat reason en signals (list[str]); signals zijn regexpatronen. A voegt de echte, hoofdlettergetrouwe gevonden passages toe aan reason en toont die via de gedeelde validation_view vóór de detailtoggle. De regexlijst blijft compatibel. Geen nieuwe publieke spanvelden, evaluator, score of blokkade.
2. De beheerde skillbron is _claude-global-setup/skills; de actieve kopieën en de bestaande syncroute worden vóór schrijven vergeleken. Recente CON-01/02-besluiten blijven behouden. Een geblokkeerde live-sync wordt afzonderlijk gerapporteerd en niet omzeild.

## Concrete wijzigingen en bewijs
- ESS-01.json: N-norm, toelichting/toetsvraag en primaire requirementvoorbeelden; bron en expliciete projectkeuze afzonderlijk in dit dossier. Runtimecontract en patroonlijst ongewijzigd.
- json_based_rules_module: één centrale G-instructie in de bestaande mapping. Vier overige modules verwijzen naar ESS-01 en vervangen de aangewezen tegenstrijdige doeltemplates en universele grensvoorbeelden. Eén-zin-uitvoer blijft gelden; grond en toelichtingsvoorstellen worden niet aan de definitiekern toegevoegd.
- judgment_review: specifieke ESS-redentekst met geciteerde treffers of expliciete afwezigheid. Hit, geen hit, gezaghebbende bron en vermeende inputreview blijven review_required.
- validation_view: bestaande reason zichtbaar bij open beoordeling, zonder extra akkoordknop.
- Gerichte regressies met echte manager én cache, evaluator/service en renderer; werkelijke module-uitvoer voor alle categorieën. Daarna make test en make lint. Onafhankelijke diffreview. Geen semantische modelkwaliteit geclaimd.

## Bron en projectkeuze
ASTRA: https://www.astraonline.nl/index.php?title=Essentie,_niet_doel&oldid=8543.
Norm: “De definitie moet de essentie van het gedefinieerde begrip weergeven en niet een doel.”
De lokale bronnotitie en het ontvangen brononderzoek van 16 september bewaren revisie 8543 en het requirementpaar: behoefte/eis van belanghebbende, met/zonder vervolggebruik als brug naar systeemontwerp. Deze bron werkt geen functie-uitzondering uit.
Projectbesluit 16 september: herleidbaar begripsbepalende functie/rol/bestemming mag blijven. Overig doel buiten de kern. Vorm beslist niet. Brongezag geeft geen vrijstelling, negatief oordeel geen automatische wijziging. Toezicht blijft grensgeval; “in het kader van” blijft signaal. Registratiecontext/noodzakelijke namen volgen CON-01; CON-02-afspraken behouden.
Generieke versie-/driftinfrastructuur blijft DEF-625. STR-06/ESS-05-conflicten vallen buiten deze normwijziging en worden bij DEF-637/625 benoemd.

## Overdracht B en C
Actuele code heeft geen gedeeld validation_snapshot-model/repository. DEF-626 en DEF-627 staan Backlog; de concrete append-only, atomaire snapshotdeellevering ontbreekt. B mag bestaande toetsroutes zonder tekstmutatie herstellen, maar geen ESS-only opslag bouwen. Gedeelde benodigdheden: vertrouwde actor-/input-/normbinding (DEF-624), atomaire snapshots (DEF-626), toepasselijkheid na wijzigingen (DEF-627), consumer/exportaansluiting (DEF-630). Geen volledige wederzijdse issueblokkades toevoegen.
C (DEF-748/638) blijft uitgesteld: pas na afzonderlijke opdracht en bovenstaande bewijsvoorzieningen een begrensde kandidaat met origineel/diff/hertoetsing; geen automatische activatie.
