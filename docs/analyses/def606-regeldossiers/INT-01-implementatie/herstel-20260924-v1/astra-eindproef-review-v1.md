**Geen vrijgave: twee Important-bevindingen blijven open, beide fix-nu.** De vier oorspronkelijke teksten leveren inmiddels de bedoelde uitkomst, maar nabije tegenhangers tonen nog verkeerde zekerheid.

1. **T18 — onterechte zinsstructuur-pass.**  
   [zinsgrenzen.py:348](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:348) sluit éénwoordige haakjesdelen uit. Schrijfvrij gereproduceerd: `register voor proefboekingen (Stop!)` en `(Wacht.)` krijgen `zinsstructuur: pass`, zonder onzekerheidsdeel. Een imperatief kan wel één woord zijn.  
   Daarnaast beschermt [regel 416](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:416) bekende afkortingen categorisch: `register voor deelnemers (De registratie sluit in dec.)` krijgt eveneens zinsstructuur-pass. De afkortingspunt sluit hier ook een zelfstandige zin af.  
   **Herstel:** gebruik woordenaantal of een bekende slotafkorting niet als bewijs tegen zelfstandigheid. Verwijs deze gevallen naar onzekerheid, met passage en positie; behoud aantoonbare bepalingen/getallen/afkortingsfragmenten. Voeg deze tegenhangers gericht toe. De totale INT-01-status blijft overigens open: de fout betreft de positieve deelclaim.

2. **T23 — hoofdletterbeperking laat onterechte zekere afkeur bestaan.**  
   [zinsgrenzen.py:579](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:579) beschermt uitsluitend kleine consonantletters. `register van werken van Chr. Huygens` geeft daardoor `fail`, met “punt gevolgd door een nieuw zinsbegin”; dezelfde tekst met `chr.` wordt onzeker. Ook `Nvr.` tegenover `nvr.` verandert onzeker in fail. Hoofdlettergebruik bewijst hier geen zinsgrens.  
   **Herstel:** laat de generieke afkortingsonzekerheid ook toepasselijke hoofdlettervarianten afdekken, zonder corpuswhitelist. De acroniemredenering uit herstelanalyse-v8 onderbouwt deze gemengde schrijfwijzen niet.

**Overige dispositie:** T17/T20 gesloten binnen deze gerichte controle: de oorspronkelijke teksten passen, de uitbreidingen gebruiken structurele patronen zonder lengtecriterium. Geen aanvullende regressie daarin aangetoond. Kleineletteronzekerheid blijft behouden. `/4` sluit `/1`, `/2` en `/3` correct uit; eigen geheugenproeven bevestigen `applied=false` en uitsluitend open tekstbinding in de weergave voor oude pass én fail. De éénregelige skillsversiewijziging klopt.

Gelezen bewijs: RED **25 failures/239**, definitief GREEN **241/241**, lint exit 0; beide laadpaden en opslag staan groen in de XML. De na RED gewijzigde verwachtingen hebben geen afzonderlijk gemeten RED: dat bewijs claim ik niet. Zelf uitsluitend korte schrijfloze segmentatie- en bindingsproeven uitgevoerd; geen brede suite. Rootgate/bundels zijn hiermee niet vrijgegeven.

Base: `6c18ce7127f0a785fefdd6bc952175a030be8643`. Manifesthashes vóór/na gelijk; actuele diffs bytegelijk aan patches:

- App SHA256: `a47788cb818de4715dfd4f078d8e16a1e5f194c5fe24c485cffee3161263538f`
- Skills SHA256: `8ae7c7c280c916843c2bd6ed60e968b2139eef44e6bc133a4da269153abacdec`

Geen edits, modelcalls of effectclaim; quarantaineset en G24-uitkomsten niet ingezien.