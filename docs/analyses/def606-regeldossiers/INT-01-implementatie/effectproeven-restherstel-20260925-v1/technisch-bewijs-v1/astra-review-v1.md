**Geen bronvrijgave voor deze kandidaat: T20 blijft Important door een aangetoonde nieuwe vals-positieve beslissing. T22 is binnen de afgesproken beperkte scope opgelost.**

1. **T20 — Important, fix-nu; open binnen DEF-770, geen waiver.**  
   Repro: `kaart met de titel ‘Klaar?’ met het regent hard`. Op de base geeft dit een onzekere citaatgrens met passage; de nieuwe code geeft **`zinsstructuur: pass`**, zonder onzekerheidsmelding. Ook `… tijdens de proef wacht` verandert van onzeker naar pass.

   [_groep_met_extra_woord:800](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:800) veronderstelt dat `het` na een voorzetsel noodzakelijk een lidwoord is en dat een ontbrekend onderwerp zekerheid oplevert. Dat vereist grammaticale correctheid, terwijl het contract die juist niet veronderstelt. In `het regent hard` zijn de veronderstelde naamwoordrollen niet bewezen; de voorafgaande `met` maakt daarvan geen bewezen voorzetselgroep. De uitgangscontrole op regel 824 herstelt dat bewijs niet.

   De oorspronkelijke T20 wordt wel herkend, maar de uitbreiding is daarmee niet verantwoord. Dezelfde onbewezen zekerheid staat in de gewijzigde skillsreferentie. Nodig: deze positieve claim corrigeren op oorzaakniveau en bovenstaande regressies onzeker houden; geen losse woorduitzondering.

2. **T22 — gesloten voor het losse label met hooguit één inhoudswoord.**  
   `schakelblad` en `het schakelblad` krijgen `formulering: review_required`, met passage, positie en reden, zonder zinsstructuur-pass. `tijdelijke opslag` behoudt zijn deelpass: geen persoonsvormplicht. Beide laadpaden, opslag/readback en uitsluiting van oude contractversies zijn gericht getest. Contract `/7` is consequent doorgevoerd.

   Meerwoordige labels en `Hij roept ‘Klaar?’ uit het regent` hebben dezelfde uitkomst op base en kandidaat. Dat zijn **bestaande beperkingen, geen nieuwe regressies van deze delta**. De sluiting van T22 is geen algemene vrijgave van alle labels of grensloze teksten; ik verleen daarvoor geen waiver.

**Generatie: een extra semantische modelaanroep is niet als noodzakelijk aangetoond.** De twaalf gelijke verzoekparen en elf verschillende antwoorden bevestigen variatie, maar sluiten een nuttige promptcorrectie niet uit. Acceptatie vraagt gemeten verbetering zonder nieuwe fouten, geen zekerheidsgarantie.

De claim “zonder beslisregel” in [claude-resultaat-v1.md:85](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/logs/def770-restherstel/claude-resultaat-v1.md:85) is bovendien te sterk: de werkelijke ESS-01-instructie sluit **niet-begripsbepalende** effecten uit en behoudt onderbouwde bepalende functies. De finale bronneninstructie verlangt behoud van beperkingen en uitzonderingen, ook wanneer een regel faalt. **LOW verslagbevinding — fix-nu:** corrigeer die onderbouwing voordat zij een grotere architectuurkeuze draagt.

Een kleiner herstel blijft redelijk: expliciteer behoud van afbakenende voorwaarde-gevolgkoppelingen, ontkende gevolgen en bronmatig variabele eigenschappen, en begrens de instructie “Vernauw begrippen” tegenover die bronafbakening. Dat kan zonder ESS-01-normwijziging of extra call. Het effect blijft daarna onafhankelijk te meten. Bronafkapping verklaart deze proefomissie niet: G05 stond volledig in het daadwerkelijke API-verzoek; de 500/800-tekenlimieten zijn een afzonderlijk productieonderwerp.

Bewijs: XML bevestigt RED **25/410**, GREEN **410**, regressie **1240 passed/5 skipped**, aanvullend **54**, integratie **27 passed/1 skipped**; gepinde lint groen. Zelf uitgevoerd: tien vergelijkende classifierprobes op base/kandidaat, patchreconstructie en bron-/bewijscontroles. Geen brede suite herhaald.

Bases: app `e38ad95796fea35154482da8d8568e3663be4c36`, skills `a048806c67a441103a2d229d0247f3c8c26f326b`. Alle manifesthashes voor en na gelijk; patches dekken ook de nieuwe test.

- Appdiff: `65d99ec772b39741702cc0abc7263b7f244034448f5780f86fdfc86b39851835`
- Skillsdiff: `38f483452e5a3d5bc9b5db3aa45e4e907d133941f6d769c1f353965d804c463d`

Geen edits, betaalde calls of afgeschermde acceptatiedata gelezen. Generatie-effect en onafhankelijke acceptatie blijven open.