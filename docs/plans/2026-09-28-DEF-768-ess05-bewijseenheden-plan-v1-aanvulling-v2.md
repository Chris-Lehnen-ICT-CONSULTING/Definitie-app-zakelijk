# DEF-768 — aanvulling v2 op het plan bewijseenheden (correctie na de Codex-hercontrole, B2-rest)

> **Aanvulling op** `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1.md` (sha256 `4b7dec58bed0479163c72ccf75d4d3af1df9213deca7ce4a37c1ecb4fb06c0e3`) en op aanvulling v1, `docs/plans/2026-09-28-DEF-768-ess05-bewijseenheden-plan-v1-aanvulling-v1.md` (sha256 `a81e6af1314e7a01b9773c30ca87ca54069a0e333f192f370002d0a6d1324f3b`). Het plan en aanvulling v1 blijven ongewijzigd. Waar deze aanvulling afwijkt, gaat zij voor. C1 en C3 uit aanvulling v1 blijven volledig gelden. Deze aanvulling vervangt de definitie van "behouden" in C2 en het E-orakel en de invoer uit C3.
>
> **Aanleiding:** de Codex-hercontrole, `logs/def768/bewijseenheden-b-v1/codex-hercontrole-result-v1.md`, geeft NO-GO op HEAD `53b5335c5`. B1, B3 en B4 zijn opgelost. Eén blocker blijft over (B2-rest). Een bevestigd M-kenmerk met waarde "onafhankelijk van storing", "storing is irrelevant" of "storing is optioneel" kreeg `behouden` en `geslaagd`. Drie zulke E-runs maakten de hele proef 12/12 geslaagd. Het ontwerpbesluit staat in de vervolgopdracht van de coördinator (28-09).
>
> **Grenzen ongewijzigd:**
> - geen wijziging aan de norm, het bewijsregels-productiepad (`src/`), de prompt, de lokale controle, skills of config;
> - geen budgetbesluit, geen freeze en geen netwerk- of betaalde aanroep.

---

## C2 v2 — automatisch "behouden" alleen via het schemaveld

**Wat er mis was.** C2 (v1) accepteerde twee routes naar "behouden": (a) een doelvoorwaarde en (b) een voor het doel bevestigd M-kenmerk. Beide keken alleen of de frase aanwezig was en of een bekend ontkenningswoord ontbrak. Of de tekst werkelijk een voorwaarde uitdrukt, werd niet gecontroleerd. Een langere woordenlijst dicht dat structurele gat niet.

**Regel 1 — behouden.** Een E-run krijgt alleen automatisch `behouden` als aan alle vier voorwaarden is voldaan:
- **Frase in een doelvoorwaarde.** Een element van `voorwaarden` van een doelantwoord (`onderwerp` = doel) bevat de frase.
- **Voorwaardelijke aanhef.** Dat element begint, na witruimte en zonder hoofdletteronderscheid, met een van deze aanheffen: "bij ", "alleen bij ", "uitsluitend bij ", "in geval van ", "als ", "wanneer ", "indien ", "mits " (`bewijsscorer.AANHEF`).
- **Geen markering.** Het element bevat geen ontkennende of opheffende markering, en het doelantwoord is niet opgeheven door een onvoorwaardelijk gelijk doelantwoord (zoals in C2 v1).
- **Juiste uitkomst.** De deterministische uitkomst van `bepaal` is `error/buiten_bereik`.

Alleen zo'n run telt als M-d-succes.

**Markeringen.** De lijst uit C2 v1 wordt uitgebreid met "onafhankelijk", "irrelevant" en "optioneel" (`bewijsscorer.MARKERINGEN`). De complete lijst:
- zonder, niet, geen, ongeacht;
- ook zonder, ook buiten, altijd, ongeacht of;
- onafhankelijk, irrelevant, optioneel.

Verder blijft de telling ongewijzigd: hele woorden, zonder hoofdletteronderscheid, in dezelfde tekstwaarde als de frase.

**Regel 2 — het M-kenmerkpad geeft nooit automatisch behouden.** Staat de frase in `kenmerk` of `waarde` van een `buiten_kern`-kenmerk, dan hangt de status af van een markering:
- **zonder markering:** `handmatig_beoordelen`. Dat is niet geslaagd, niet automatisch kritiek, stopt niet en wordt apart gerapporteerd.
- **met markering:** `ontkend`, zoals in C2 v1.

Dit geldt ongeacht of het kenmerk voor het doel bevestigd is. Het geldt ook als een doelvoorwaarde tegelijk aan regel 1 voldoet. Dat is conservatief: twee routes tegelijk zijn twijfel, geen bewijs.

**Regel 3 — overige vermeldingen:**
- **Nergens:** staat de frase nergens, dan is de status `weggevallen` (kritiek).
- **Doelvoorwaarde die niet aan regel 1 voldoet:** `handmatig_beoordelen`, of `ontkend` bij een markering. Dat gebeurt bij een ontbrekende aanhef ("storing", "tijdens een storing"), bij opheffing, of bij een andere uitkomst dan `error/buiten_bereik`.
- **Alleen elders:** een vermelding alleen elders (bijvoorbeeld `buiten_bereik`) blijft `handmatig_beoordelen`. Een markering daar ontkent niet (zoals in C2 v1).

**Volgorde in de scorer:**
1. een markering in een doelvoorwaarde of M-kenmerk geeft `ontkend`;
2. anders geeft een vermelding in een M-kenmerk `handmatig_beoordelen`;
3. anders geeft regel 1 `behouden`;
4. anders geeft een vermelding `handmatig_beoordelen`;
5. anders is de status `weggevallen`.

**Runoordeel bij E.** De tabel uit C2 v1 blijft staan:
- **ontkend:** kritiek, tenzij de uitkomst `error/buiten_bereik` is. In dat geval is de run `niet_geslaagd`.
- **weggevallen:** kritiek.
- **handmatig_beoordelen:** geen kritiek. De run is apart, telt niet voor M-d en stopt niet.

"Behouden" kan nu alleen nog samengaan met `error/buiten_bereik`.

**Proefoordeel.** Dit blijft zoals in C2 v1, met twee aanvullingen:
- Een handmatige run telt niet mee voor 11/12 en niet voor "E 3/3 behouden".
- De proef kan alleen `geslaagd` zijn als alle E-runs automatisch behouden zijn volgens regel 1.

Met handmatige runs wordt het oordeel hoogstens `wacht_op_handmatige_beoordeling`.

## E-orakel en invoer v3

**E-orakel.**
- `uitkomst` = `["error/buiten_bereik"]`.
- `voorwaarde_vereist_voor` = `["error/buiten_bereik"]`.
- De toelichting volgt deze aanvulling.

`review_required` is voor E geen juiste uitkomst meer. Het was dat onder C2 v1 alleen met een behouden voorwaarde. Na regel 1 kan die combinatie niet meer voorkomen. `review_required` zou hooguit handmatig kunnen zijn, en handmatig telt niet.

**Invoer.**
- **Schema.** Het invoerschema wordt `def768-ess05-bewijsregel-invoer/4`.
- **Nieuw bestand.** De invoer wordt opnieuw gemaakt als nieuw bestand `reports/DEF-768-AI-20260928-R18/bewijsregel-invoer-v3.json`. `-v1.json` en `-v2.json` worden niet overschreven.
- **Maker.** De maker pint deze aanvulling (v2) op sha256 en legt haar vast in `herkomst.aanvulling`.
- **Runner.** De runner pint `-v3`. Hij weigert `-v2` op de invoerhash en op het schema (`/3`), en `-v1` zoals voorheen.

## Afwijkingen van de vervolgopdracht (open punten voor de coördinator)

1. **De drie Codex-voorbeelden in een M-kenmerk zijn `ontkend`, niet `handmatig_beoordelen`.**
   - **Waarom.** De drie voorbeelden bevatten de markeringen die regel 1 toevoegt ("onafhankelijk", "irrelevant", "optioneel"). Regel 2 maakt ze daarom `ontkend`. Met uitkomst `review_required` is dat kritiek.
   - **Wat de opdracht zei.** De opdracht noemde voor deze voorbeelden "handmatig_beoordelen, niet geslaagd".
   - **Waarop het neerkomt.** Beide lezingen leiden tot "niet geslaagd" en "proef niet geslaagd"; ontkend is strenger.
   - **Structureel bewijs.** De tests zetten `MARKERINGEN` terug op de lijst van v1. Dan zijn de drie voorbeelden `handmatig_beoordelen` en nooit behouden. Het proefoordeel met drie zulke E-runs is dan `wacht_op_handmatige_beoordeling`.
2. **"onafhankelijk van storing" in `voorwaarden` is ontkend, maar niet kritiek.**
   - **Wat er gebeurt.** Een doelvoorwaarde levert de uitkomst `error/buiten_bereik` op (gemeten in de tests). Volgens de ongewijzigde C2-regel ("ontkend is kritiek tenzij `error/buiten_bereik`") is de run dan `niet_geslaagd`, niet `kritiek`. Zo'n run telt niet voor M-d en haalt "E behouden" niet.
   - **Wat de opdracht zei.** De opdracht noemde "ontkend/kritiek".
   - **Open besluit.** Een run die hier toch kritiek (en dus een stop) moet opleveren, vraagt een wijziging van de C2-regel. Dat besluit ligt bij de coördinator.
3. **Conservatieve voorrang van het M-kenmerk.**
   - **Wat er gebeurt.** Een M-kenmerk met de frase maakt de run handmatig, ook naast een correcte doelvoorwaarde.
   - **Gevolg.** Een terecht geslaagde run kan zo op handmatige beoordeling wachten. Een onterecht succes kan zo niet ontstaan.
4. **Lexicaal risico, zoals in C2 v1.** Aanhef en markering worden lexicaal herkend:
   - "alleen bij storing, niet daarbuiten" is ontkend;
   - "bij\tstoring" (tab) of "zodra storing" is handmatig;
   - een woord dat de frase bevat (bv. "storingsdienst") is een vermelding.

   Al deze fouten zijn conservatief: ze leveren geen onterecht succes op.

## Wat ongewijzigd blijft

- **C1 en C3.** Stop en duurzaamheid (C1), en de orakels A, C en D (C3), blijven zoals in aanvulling v1.
- **Budget.** 18 aanroepen, cumulatief 399 → maximaal 417 binnen 427. Kostenplafond USD 6,03 binnen de kaderrest USD 21,798865.
- **R18B.** `lokale-invoer-v1.json` (sha `a36172a0…5b81`) blijft gelijk.
- **Contract.** `ess05-bewijsregels/6`, prompt /4.
- **Uitvoering.** Geen retry, geen cache, geen technische herhaling. Een betaalde stap alleen na een "go" van Chris met een eigen budgetbesluit, en pas nadat Codex deze correctie heeft gecontroleerd.
