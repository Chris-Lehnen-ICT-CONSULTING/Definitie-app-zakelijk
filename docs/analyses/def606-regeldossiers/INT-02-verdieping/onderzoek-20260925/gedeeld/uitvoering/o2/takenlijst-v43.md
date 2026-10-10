# INT-02 O2 — mergevoorbereiding (takenlijst v43)

29 september 2026. Chris vraagt: “waarom bereid je dan niet O2 voor om te mergen?” Dit autoriseert de voorbereiding van een afzonderlijke O2-deeloplevering en de PR; een daadwerkelijke merge of activering is in deze stap niet uitgevoerd.

## Afbakening

De gecommitte O2-code tot ebe9c1b7c26ffe6040bffb66db4937b932406dc8 wordt voorbereid voor merge. O1 blijft actief (`judgment_review`). DEF-835 blijft open voor onafhankelijke goldset/hold-out, modelkwalificatie en verdere appintegratie. DEF-626/S1 is uitgesteld volgens v42: de ongecommitte wijzigingen in de andere werkboom gaan niet mee.

## Taken

- [x] O2-branch en schone getrackte werkstand gecontroleerd; 17 O2-commits boven de oorspronkelijke basis.
- [x] Actuele main opgehaald: e51610461113c1cf90647c9a7662de11293c6f14, inclusief INT-03 PR486.
- [x] Mergeberekening zonder conflicten; berekende boom 8e6b456d6a2fbc96e9011644f790c92df7ce3399. Nog geen branchmerge.
- [x] Bestaande WP5a- en Q1-review/testbewijzen aan de huidige bestanden gebonden: 10+3 bronhashes gelijk.
- [x] Lint op O2-head geslaagd; bron-diffcheck geslaagd. Witruimte in historische ruwe logs/patches blijft bewaard.
- [x] Actions opnieuw uitgelezen: enabled=false; tien vereiste GitHub-statuschecks bekend, geen bescherming gewijzigd.
- [ ] Canonieke offline unitgate afronden en alle fouten classificeren; loopt op O2-head vóór integratie van nieuwe main.
- [ ] Nieuwe main in featurebranch integreren en relevante gecombineerde bron verifiëren.
- [ ] PR-beschrijving met bewijs, reviewherkomst en open scope definitief maken.
- [ ] Normale push met hooks, concept-PR maken en teruglezen.
- [ ] Definitieve mergevoorwaarden rapporteren; geen activering.

Bewijs: `bewijs/mergevoorbereiding-v1/`. Deze lijst is een tussenstand, geen verklaring dat de branch al mergeklaar is. Eerdere v42 blijft leidend voor uitstel van DEF-626.
