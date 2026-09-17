# DEF-806 — echte generatie en readback

Uitgevoerd door de coördinator via de Codex in-app browser, 17 september 2026. Geïsoleerde app op http://127.0.0.1:8518; eigen kopie van de testdatabase. Geen productiegegevens gewijzigd. Geen deskundige acceptatie ingevoerd.

## Nieuwe generatie

Invoer: besluit; juridische context Bestuursrecht; wettelijke basis Algemene wet bestuursrecht. Fixture awb-1-3-20260815.txt geüpload en geselecteerd: 708 tekens, 20 trefwoorden. Na duplicaatmelding expliciet een nieuw concept gegenereerd met als reden de DEF-806-hertoets. Generatie d96266b8-5a44-4578-89b2-f54258f51c7c; nieuw record 5, 17 september 2026 16:43 CEST. Bewijsrecord: nieuwe-generatie-record5-v1.json.

Waargenomen: de modelbeoordeling noemt zelf dat de exacte vindplaats geen hyperlink vervangt en laat verwijskwaliteit open. Actie: bruikbare (ook interne) link aanleveren of een deskundige verwijzingsuitzondering vastleggen. De definitietekst hoeft hiervoor niet te veranderen. Vier documentfragmenten hebben URL null; de opgeslagen generatie- en beoordelingskwitanties binden de gebruikte passages. Beoordelingsprompt con02-assess/2; anthropic/claude-opus-4-8.

De nieuwe zin is niet de vaste P01-definitie. Naast de verwijsvraag blijft betekenissteun open omdat het model de toevoeging ‘resultaat van een besluitvormingsproces’ niet aantoonbaar uit het bronbewijs afleidt. Dat is geen terugkeer van DEF-806 en geen deskundigenoordeel.

## Readback na schone herstart

App volledig gestopt en om 16:50 CEST opnieuw gestart. De drie gewijzigde productiebestanden waren bytegelijk aan runtime-final-source-identiteit.json / review-diff-identiteit-v3.json. Editor: zoek besluit, status Concept, lijstweergave, afzonderlijk record 4 en 5 openen, paneel ‘Bronbasis (CON-02) — opgeslagen record’ uitklappen.

Record 4: CON-02 oranje ‘Nog te beoordelen’, zonder cijfer. Brongezag en betekenissteun blijven positief. Verwijskwaliteit open met expliciete reden: de dragende bron heeft geen bruikbare hyperlink; exacte vindplaats vervangt de link niet. Concrete vervolgactie link of deskundige uitzondering. Oorspronkelijke definitietekst behouden. Het historische AI-oordeel wordt lager nog positief getoond met expliciete AI-attributie, prompt con02-assess/1 en ‘geen vaststelling’; bovenaan staat één modelclaim afgewezen. Codex heeft dit onderscheid beoordeeld en niet als extra blocker aangemerkt.

Record 5: opgeslagen nieuwe definitietekst zichtbaar; verwijskwaliteit opnieuw open met dezelfde ontbrekende-linkreden en vervolgactie. Prompt con02-assess/2 zichtbaar. Geen definitiewijziging opgeslagen bij readback. Beide uitkomsten komen overeen met de onafhankelijke replay van dezelfde opgeslagen records.

## Versiebinding en grens

De modelgeneratie liep met de eerste hyperlinkpatch. De readback na herstart liep met de per-bron- en syntaxcorrecties (v3). De daaropvolgende kleine poortcorrectie is apart met regressietests en replay gebonden aan de uiteindelijke code; zij wijzigt niets aan deze gevallen met URL null. De beoordelingsprompt is gedurende de correcties bytegelijk gebleven. Deze hertoets bewijst geen acceptatie van alle 31 casussen of menselijke P01-goedkeuring.
