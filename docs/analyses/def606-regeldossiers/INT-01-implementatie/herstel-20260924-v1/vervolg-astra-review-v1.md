**Geen bronvrijgave: twee Important-regressies, beide fix-nu.** De oorspronkelijke T20/T24-repro’s zijn hersteld, maar de nieuwe herkenning geeft bij nabije tegenhangers onbewezen zinsstructuur-pass.

1. **T20 — ontbreken van een herkend werkwoord bewijst geen bijzin.**  
   [zinsgrenzen.py:588](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:588) accepteert het vervolg zodra geen werkwoord uit de beperkte lijst vóór het laatste woord staat. Schrijfvrij vergeleken met de base:
   - `kaart met de titel ‘Wie woont hier?’ waarop wacht je.`
   - `kaart met de titel ‘Wie woont hier?’ waarop aanwijzingen staan daarna volgt de controle.`  
   
   Beide veranderen van onzeker naar **zinsstructuur-pass**. Het eerste vervolg heeft vraagzinsvolgorde; het tweede bevat een aanvullende hoofdzin. Ontbrekende correcte interpunctie mag geen bewijs voor één bijzin worden.  
   **Dispositie: fix-nu.** Vereis positieve ondersteuning voor de toegelaten voortzetting; laat onbewezen syntaxis onzeker. Alleen werkwoorden of uitzonderingen toevoegen sluit deze oorzaak niet.

2. **T24 — verklaarde afkorting onderdrukt een mogelijke slotgrens.**  
   [zinsgrenzen.py:458](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:458) retourneert zonder verdere ondersteuning `geen` wanneer een kleine letter volgt. Repro:
   `Bak met vakcode (v.qr. = vakcodering) ingedeeld volgens v.qr. daarna volgt controle`  
   
   De base meldt onzekerheid; nieuw volgt **zinsstructuur-pass zonder grensdeel**. De verklaring bewijst de afkortingsfunctie, maar niet dat de laatste punt onmogelijk ook zinslot is. De nieuwe haakjesaansluitingscontrole vangt deze latere overgang niet.  
   **Dispositie: fix-nu.** Onderscheid interne punten van een mogelijk dubbel functionerende slotpunt; behoud onzekerheid bij onbewezen aansluiting. Verduidelijk overeenkomstig de algemene uitspraak over verklaarde afkortingspunten in de skillsreferentie.

Voor **generatie en skills** geen aanvullende concrete blocker gevonden. De bronvoorrang is begrensd tot bepalende betekenis, maakt bronbijzaken niet tot eisen en presenteert de modale hulpmiddelen niet als vaste equivalenties. Het ARAI-04-record is bytegelijk; de afsluitende betekeniscontrole adresseert het voorbeeldconflict op instructieniveau. Dat bewijst geen generatie-effect. `/5` en de tests voor niet-actuele `/1`–`/4`-uitkomsten zijn aanwezig.

Beoordeeld: classifier, beide promptmodules, de drie opgegeven tests en drie skillteksten uit het [manifest](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/logs/def770-vervolg/review-manifest-v1.json). Patchinhoud gereconstrueerd en vergeleken; alle bron-/loghashes kloppen, geen drift vóór/na.

- Appbase: `7ee7d7d293770dd86f2dd70f1b4945b25ead3c94`
- Skillsbase: `ed0fcfdcc169c37058f0436fc92c1e07752366b8`
- Appdiff SHA256: `9f06519bcb838f38fc61ebe4b7367d803315f7ca21134c451d1b08a9adeed3c0`
- Skillsdiff SHA256: `6566781a77bf3ccc8f4e85b45f3e1b9d14e31c205d11afd49aea220d7d8f0477`

Bewijs: 331 gericht groen; 1127 regressietests geslaagd, vijf skips; gepinde Ruff/Black groen. Eigen verificatie: acht schrijfloze classifiervergelijkingen. De afzonderlijke promptproef stopte bij geblokkeerde cache-directoryaanmaak; daarvoor zijn bestaande PromptServiceV2-tests en de aanroeproute beoordeeld. Geen brede suite, edits, modelcalls of nieuwe acceptatie-inhoud gelezen. Bundels, brede gate en onafhankelijke effectacceptatie blijven afzonderlijk.