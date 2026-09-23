**Beide Important-bevindingen zijn gesloten. Geen nieuwe blokkerende bevindingen in de gerichte delta.**

- **Beschadigde meldingskop:** onafhankelijk bevestigd dat ontbrekende/spatiërende/Unicode-dubbele punten, underscores en kale meldingspayloads worden afgewezen. Ketenproef: `modelantwoord_ongeldig`, geen opschoning, geen validatie, **nul opgeslagen definities**.
- **Opeenvolgende verduidelijkingen:** beide antwoorden blijven in de derde prompt aanwezig. De volledige keten is identiek in `_kandidaatregistratie` en database-readback. Vragen blijven herkenbaar modelcontext; antwoorden zijn gebruikersbedoeling, geen bronfeit.
- **Binding en limieten:** invoerwijziging verwijdert de hele keten. Tekstbudget en maximumaantal antwoorden blokkeren vóór het model, met behoud van de herstelbare invoer.

Bewijs: [54 gerichte tests](/tmp/def821-bewijs/integratie-eindcontrole-v1/beide-gedragingen.log), [783 regressietests](/tmp/def821-bewijs/integratie-eindcontrole-v1/regressie-2.log) en [make lint](/tmp/def821-bewijs/integratie-eindcontrole-v1/make-lint.log) groen. De offline effectproef gebruikt de juiste basis en gelijke instellingen.

**Technische vrijgave voor de maximaal 32-call effectproef zodra de lopende volledige eindgate groen eindigt.** De oorspronkelijke run is afgebroken; de [vervangende run](/tmp/def821-bewijs/integratie-eindcontrole-v1/make-test-coordinator-v2.log) stond bij eindcontrole rond 19%, zonder getoonde failures. Bij ongewijzigde code vereist alleen dat eindresultaat nog verificatie, geen nieuwe reviewcyclus.

Oordeel gebonden aan:
- HEAD `7d962a1b9d297c45ce27709aedac906f2a80be0a`
- Basis `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`
- Werkboom bij eindcontrole schoon.

Gebruik voor de effectproef expliciet die basis via `--basis-ref`; de scriptdefault verwijst nog naar de oorspronkelijke basis. **AC8-kwaliteit blijft open** tot beoordeling van de daadwerkelijke outputs. Geen livecalls uitgevoerd of heldoutcases gelezen.