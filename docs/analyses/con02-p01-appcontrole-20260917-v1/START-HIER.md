# P01 — appcontrole 17 september 2026

**Uitkomst: niet geslaagd; P01 en CON-02 blijven open.** De inhoudelijke deelakkoorden van Chris blijven geldig. De positieve appketen is geblokkeerd door ontbrekende bronmetadata-invoer (DEF-808) en niet behouden hervalidatiebewijs in de uitgevoerde opslagroute (DEF-809).

## Omgeving en afbakening

- App uit git-archive van commit `29d8176b32e2fe11c62fbb58d5fe087d0b229e62` (DEF-806, PR 460); geen broncodewijzigingen tijdens deze proef.
- Geïsoleerde runtime `/private/tmp/CON02-P01-runtime-20260917`, localhost:8519, gestart met de bestaande Python 3.13-venv.
- SQLite-backup van de eerdere DEF-806-testdatabase; uitsluitend record 5 in deze nieuwe kopie via UI bewerkt. Originele records 4/5 en productiedatabase blijven behouden.
- Uitvoering: Codex-coördinator, CUA-browser/Playwright en onafhankelijke read-only SQLite-controle. Geen nieuwe implementatie- of CLI-reviewopdracht nodig voor deze test.
- Verwachting: C02-P01 uit het bestaande acceptatiedossier; bron S-AWB13, versie 2026-08-15, artikel 1:3 lid 1 Awb, vastgelegde wetten.overheid.nl-artikelhyperlink. Geen nieuwe norminterpretatie of hyperlinkbereikbaarheidstest.
- Menselijke akkoorden: zie `../con02-deskundige-beoordeling-20260917-v1/START-HIER.md`. Geen appreview namens Chris of verwijzingsuitzondering ingediend.

## Uitvoering en resultaten

| Stap | Waargenomen resultaat | Uitkomst |
|---|---|---|
| Upload vaste Awb-fixture | `awb-1-3-20260815.txt`, 708 tekens, 20 keywords; selecteerbaar in context | Geslaagd |
| Bronmetadata invoeren | Upload, documentbeheer en editor bieden geen URL/bronversie-invoer; bronreview biedt oordeelcorrectie/citaat/vindplaats, geen URL/bronversie-aanvulling | DEF-808 |
| Exacte tekst invoeren en handmatig opslaan | `schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling` | Geslaagd, SQL bevestigt |
| Opnieuw valideren | Nieuwe AI-beoordeling om 21:16:46 UTC: brongezag pass, betekenissteun pass, verwijskwaliteit review_required wegens ontbrekende URL | Uitgevoerd; juiste blokkade ontbrekende URL |
| Status review, opslaan, openen in Expert Review | Exacte tekst behouden; oude bronbeoordeling van 14:43:02 UTC teruggelezen, historisch/verouderd | DEF-809 |
| Bronversie, exacte locator en hyperlink teruglezen | Bronkaart toont versie/vindplaats onbekend, geen hyperlink; bron-JSON bevat URL null en geen versie/locator | Geblokkeerd |

De beoordeling van 21:16:46 gebruikte `anthropic / claude-opus-4-8`, prompt `con02-assess/2`. Het is een echte UI-hervalidatie, geen nieuw gegenereerde definitie. Alle drie kenmerken werden als gesteund getoond: schriftelijke beslissing, van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling. De AI vermeldde onzekerheid over bronversie/peildatum. Dit is geen vervanging van menselijke acceptatie.

## Concrete UI-waarnemingen

Deze passages zijn overgenomen uit de tijdens uitvoering gelezen DOM; dit bestand is een testverslag, geen volledige ruwe DOM-export.

- Na tekstwijziging: `Historisch bronbewijs: hoort bij een eerdere tekst/context — bewijs hoort bij een eerdere definitie. Toets opnieuw voor een actuele beoordeling.`
- Na hervalidatie: `AI-bronbeoordeling (anthropic · claude-opus-4-8, prompt con02-assess/2, 2026-09-17T21:16:46.592577+00:00)`.
- Betekenissteun: `De bronpassage geeft exact dezelfde bepalende kenmerken als de te toetsen definitie: schriftelijke beslissing, van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.`
- Verwijskwaliteit: `De vindplaats is exact herleidbaar (Awb, artikel 1:3, lid 1), maar er is geen url-attribuut bij de bron aanwezig; zonder bruikbare hyperlink is 'pass' uitgesloten.`
- Bronkaart: `Bron-id: doc:01e121c20018eed2#7118848e · versie: onbekend · vindplaats: onbekend · profiel (gedeclareerd): onbekend`.
- Na opslaan/openen in review: weer beoordeling `2026-09-17T14:43:02.496597+00:00`, met extra oude kenmerk `resultaat van een besluitvormingsproces` en historische status. Onafhankelijke [SQL-readback](record5-readback.json) bevestigt oude `source_assessment` en `candidate`, terwijl `definitie` wel exact P01 is.

## Bevindingen en beperkingen

1. [DEF-808](https://linear.app/definitie-app/issue/DEF-808): bekende bronversie en hyperlink kunnen in de geteste uploadroute niet worden geregistreerd. REAL_BUG / ontbrekende functionaliteit. De proef bewijst niet dat iedere alternatieve invoerroute ontbreekt. Volgende hertoets moet gecontroleerde invoer, doorvoer en teruglezen aantonen.
2. [DEF-809](https://linear.app/definitie-app/issue/DEF-809): de nieuwe editorbeoordeling ontbreekt na opslaan/openen in review. REAL_BUG voor de waargenomen keten; technische oorzaak nog onbekend. Nieuwe beoordeling alleen als UI-waarneming beschikbaar; JSON-readback bevat juist het oude bewijs.
3. Bekende [DEF-805](https://linear.app/definitie-app/issue/DEF-805) opnieuw gezien: sorteren op datum faalt bij gemengde tijdzones. Via `Begrip A-Z` kon de controle doorgaan.
4. Autosave meldt in deze testomgeving `no such table: definitie_drafts`. Handmatig opslaan bewaart tekst/status wel. Geclassificeerd als ENV_ISSUE/onderzoekspunt; niet bewezen als oorzaak van DEF-809 en niet stilzwijgend opgelost.
5. Overige toetsregels zijn niet inhoudelijk geaccepteerd in deze CON-02-proef. De algemene validatiegate bleef geblokkeerd; geen vaststelling uitgevoerd.

## Bewijs en conclusie

- [Recordreadback](record5-readback.json): echte opgeslagen testdata, niet synthetisch aangepast.
- [Runtimeherkomst](runtime-provenance.json): exact geteste appcommit en databaseherkomst.
- [Manifest](manifest.json): SHA-256 van bewijsbestanden.

Eén casus uitgevoerd: **0 volledig geslaagd, 1 geblokkeerd**, met twee concrete defectbevindingen. No-go voor afsluiten P01/CON-02. DEF-806 voorkomt in deze uitvoering terecht een positieve verwijskwaliteit zonder hyperlink. P01 vereist herstel van DEF-808/DEF-809 en een nieuwe end-to-end-proef; de overige 30 praktijkgevallen blijven afzonderlijk open.
