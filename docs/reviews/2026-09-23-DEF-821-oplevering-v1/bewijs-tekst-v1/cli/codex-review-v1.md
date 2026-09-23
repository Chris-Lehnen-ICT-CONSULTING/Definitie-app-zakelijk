**Geen eindgoedkeuring: twee bevestigde bevindingen, beide Important — fix nu.**

1. **Misvormde meldingskop wordt opgeslagen als definitie.**  
   [modelantwoord.py:239](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-821-ess04-generatie/src/services/modelantwoord.py:239) herkent uitsluitend de exacte sentinel inclusief dubbele punt. Deze invoer wordt daardoor `soort="definitie"`:

   ```text
   BETEKENISGROND ONTBREEKT
   {"ontbrekende_grond":"dagconventie","vraag":"Werkdagen of kalenderdagen?"}
   ```

   Onafhankelijk gereproduceerd via de echte handler, orchestrator, opschoning en tijdelijke SQLite, met model- en validatiedoubles: `success=true`, validatie aangeroepen, opgeslagen ID=3. Readback bevat de meldingskop en JSON als definitietekst. Ook een spatie vóór de dubbele punt omzeilt de parser. Herken zulke beschadigde contractkoppen als **ongeldig**, vóór het definitiepad; voeg regressiebewijs voor nul opslag toe.

2. **Een vervolgvraag verliest eerder aangevulde betekenisgrond.**  
   De nieuwe route gebruikt het eenmalige antwoordmechanisme van [betekenisconflict.py:219](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-821-ess04-generatie/src/ui/helpers/betekenisconflict.py:219), aangeroepen door [definition_generation_handler.py:390](/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-821-ess04-generatie/src/ui/handlers/definition_generation_handler.py:390).

   Met ongewijzigde invoer gereproduceerd: antwoord **“Werkdagen”** staat in prompt 2. Na een vervolgvraag over het startmoment en antwoord **“De ontvangstdag telt niet mee”** bevat prompt 3 uitsluitend dat laatste antwoord. De vastgelegde dagconventie is verdwenen. Bewaar eerdere verduidelijkingen zolang dezelfde invoer en verduidelijkingsketen gelden; toets ook opeenvolgende vragen en het vervallen bij invoerwijziging.

| AC | Beoordeling |
|---|---|
| AC1 | Technisch gedekt: exacte G2, beide uitvoeruitzonderingen, behoudinstructies voor kwantitatieve grenzen en promptbudgettests. Modelnaleving blijft kwaliteitsbewijs. |
| AC2 | **Open:** beschadigde sentinel faalt niet veilig, zie 1. |
| AC3 | Geldige melding correct vóór downstream afgetakt; **open voor misvormde melding**, zie 1. ESS-02 en gewone definities hebben regressiedekking. |
| AC4 | Platte rendering, expliciet verzenden en invoervingerafdruk gedekt; **open bij vervolgvraag**, zie 2. |
| AC5 | Gewone verduidelijking → kandidaat → opslag/readback gedekt. De twee gevonden grensgevallen ontbreken in de tests. |
| AC6 | Gedekt: runtimecontract en patronen ongewijzigd; norm, G2 en geïnstalleerd skillreferentieblok inhoudelijk consistent. Geen nieuwe ESS-04-jury. |
| AC7 | Tests/lint groen; **open totdat bevindingen zijn opgelost en de correctiediff is herbeoordeeld**. |
| AC8 | Harness technisch beoordeeld; **live kwaliteitsvergelijking nog open**, inclusief de twee apart gehouden casussen. |

De harness gebruikt echte oude/nieuwe bronkopieën en volledige appprompts. Verwachtingen worden niet aan het model doorgegeven; caches zijn gescheiden en antwoordcaching staat uit. SDK-retries staan op nul; applicatieretries tellen mee binnen de proxybudgetten, samen maximaal 32. Secret-scrubbing is aanwezig. Offline bewijs toont gelijke instellingen, maar bewijst geen kwaliteits- of gebruikerswinst.

[Make-testbewijs](/tmp/def821-bewijs/make-test-1.log): **7046 passed, 75 skipped, 1 xfailed**. [Make-lintbewijs](/tmp/def821-bewijs/make-lint-1.log): groen. Mijn aanvullende proeven waren offline; geen bronbestanden gewijzigd of andere agents/CLI-sessies gestart.

Basis/HEAD: `b687c1615d4abd30b5b6d38dd55e64f6a758e187`. Patch-SHA256: `2f097d2b970040809ebae661a68a1d694f857e3716ab5cf1d51a0c2b08f2736f`. Alle **20 manifestbestanden** zijn bij de eindcontrole identiek; reverse patch-check slaagt. Geen wijziging tijdens review aangetroffen. Na correctie volstaat gerichte herreview van deze bevindingen, de geraakte keten en het bijbehorende testbewijs; daarna volgt de live kwaliteitsbeoordeling.