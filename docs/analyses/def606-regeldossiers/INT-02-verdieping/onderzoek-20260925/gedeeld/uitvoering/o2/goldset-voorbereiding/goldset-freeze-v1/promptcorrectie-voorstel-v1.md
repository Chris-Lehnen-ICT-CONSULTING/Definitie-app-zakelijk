# INT-02 O2 — voorstel promptversie /2 na C107 (v1)

30 september 2026. **Voorstel ter bespreking, geen codewijziging en geen nieuw proefmandaat.** Basis: `kwalificatie-uitvoeringsverslag-v2.md` en de bewaarde v2-bundel. De projectregel in `CLAUDE.md` verbiedt een wijziging aan prompt builders zonder overleg.

## Twee zelfstandige fouten

1. De ruwe modeluitvoer voor C107 koos `fail` terwijl de bevestigde bedoeling `null` is en de beschikbare context geen handelingsvoorschrift of discretionaire afwegingsopdracht bevestigt. Zij leidde de voorschrijvende functie uit de kwalitatieve formulering zelf af. Dat overschrijdt de T-grens: een kwalitatief criterium dat beoordeling vergt is niet alleen daarom een discretionaire beslisregel; ontbrekende of strijdige betekenisgrond vraagt één gerichte vraag.
2. Het citaat uit de kern is letterlijk aanwezig, maar het opgegeven interval begint één codepunt te laat. Het strikte resultaatcontract moet dit als `invalid_citation` blijven afwijzen. Een lokale reparatie van modelposities zou het versiegebonden contract veranderen en wordt niet voorgesteld.

## Voorgestelde gerichte aanvulling

Laat de oorspronkelijke Claude Code CLI-uitvoerder een **nieuwe** promptversie `def835-int02-prompt/2` maken in `src/services/validation/int02_assessment_service.py`. De letterlijke T-tekst, de norm, het schema en de contractvalidatie blijven gelijk. Voeg in de systeemprompt na de bestaande invoerduiding twee expliciete, algemeen toepasbare instructies toe:

- Voor `fail` moet de aangeleverde betekenisgrond de functie als handelingsvoorschrift of discretionaire beslisregel zelfstandig dragen. Is de bedoeling onbekend en kan de actorpassage zowel begripskenmerk als voorschrift zijn, kies bij ontbrekende beslissende grond `insufficient_information` met precies één vraag. Leid `fail` niet enkel af uit een kwalitatief of modaal woord of uit het feit dat een actor een oordeel vormt.
- Neem elk passage- en grondcitaat letterlijk over uit het opgegeven veld, bepaal `start` nulgebaseerd, zet `end = start + len(quote)` in Python-codepunten en controleer vóór verzending dat de exacte veldtekst op `[start:end]` gelijk is aan `quote`. Als dat niet lukt, verzin geen citaat of positie.

Eerst offline rode tests voor de ontbrekende prompttekst en versie; daarna groene promptrendering en onveranderde strikte contracttests. Gebruik C105/C107/C112 alleen als bekende regressievoorbeelden; geen van de 16 hold-outs in opdrachten, promptontwikkeling of reviews. Laat een verse, aparte Codex CLI-sessie de concrete diff tegen T-tekst, norm, contract en v2-foutbewijs reviewen. Bewaar de volledige CLI-opdrachten en reviewprompt in het dossier. Geen live extra calls binnen het opgebruikte v2-manifest.

Na geaccepteerde code en review: nieuwe profiel-/promptversie, nieuw offline manifest met bron- en payloadhashes, nieuwe proefmap en **nieuw exact menselijk akkoord** binnen een afzonderlijk begrensd budget. Het v2-bewijs blijft ongewijzigd. Een volgende regressie moet eerst alle C105/C107/C112 inhoudelijk juist én met geldige citaten afronden voordat ontwikkeling mag starten.
