# DEF-808 / DEF-809 — herstel en P01-hertoets

## Uitkomst

De twee gemelde fouten zijn hersteld. De exacte P01 slaagt voor de drie CON-02-onderdelen en de nieuwe beoordeling blijft beschikbaar na handmatig opslaan en openen in een nieuwe Expert Review-sessie. Dit is geen afronding van de volledige CON-02-acceptatieset en geen formele vaststelling van de definitie.

Geteste en gereviewde code: `503bbe04d0804e774748784166a93f82c21c873c`. Basis: DEF-806 `29d8176b32e2fe11c62fbb58d5fe087d0b229e62` (PR #460, nog open). De herstel-PR bouwt daarop voort.

## Herstel

- DEF-808: invoer en behoud van hyperlink, bronversie en exacte vindplaats bij upload en bestaande documentbronnen. Opgave blijft herkenbaar als opgegeven metadata, met afzonderlijke inhoudelijke bronbeoordeling.
- DEF-809: nieuwe editor-hervalidatie wordt bij handmatig opslaan alleen overgenomen als tekst, context en bronnen bij de beoordeling passen. Oude of gewijzigde bindingen worden afgewezen; historisch bewijs blijft bewaard.
- Tijdens review: een mislukte metadatabestandopslag levert geen onterechte succesmelding meer op; de oude waarde wordt in geheugen hersteld. De foutmelding garandeert geen herstel van een mogelijk beschadigd bestand.
- Tijdens browserproef: een conditioneel naamveld verloor zijn waarde door Streamlit-widgetcleanup. Dit is hersteld en met echte AppTest-reruns rood/groen aangetoond.

## P01 — echte uitvoering op 18 september 2026

Geïsoleerde runtime `/private/tmp/DEF-808-809-runtime-20260918-v2`, poort 8521, gekopieerde SQLite-testdatabase. Tracked `src/` en `config/` zijn met de geteste commit vergeleken; zie herkomstbewijs. Geen productiegegevens aangepast.

Term: **besluit**. Definitie, exact zonder eindpunt:

> schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling

Context: Bestuursrecht / Algemene wet bestuursrecht. Fixture `awb-1-3-20260815.txt`, 708 tekens, SHA-256 `7be6c298370590a6ca51e82d9f6e9f066274e86adc3051037748beb2078e3ec8`. Bronversie `2026-08-15`, vindplaats `artikel 1:3 lid 1 Awb`. De exacte opgegeven hyperlink staat in het readbackbestand.

| Stap | Waarneming |
|---|---|
| Ongeldige URL `intern.example/awb` vastleggen | Zichtbare afwijzing; database bevatte nog vier bronnen zonder URL/bronversie. |
| Reviewer naam → andere velden → reruns | Naam `Codex — P01-uitvoeringscontrole` blijft behouden. Dit is uitvoerprovenance, geen menselijke deskundigenverklaring. |
| Juiste bronmetadata opslaan | Record 5, versie 4; alle vier passages bevatten URL, bronversie en vindplaats. |
| Oude beoordeling na metadatawijziging | Zichtbaar historisch/ongeldig; drie onderdelen nog te beoordelen, totdat opnieuw gevalideerd wordt. |
| Valideren | Werkelijke Anthropic-aanroep, model `claude-opus-4-8`, prompt `con02-assess/2`, niet uit cache. |
| CON-02 | Brongezag/toepasselijkheid **pass**, betekenissteun **pass**, verwijskwaliteit **pass**. |
| Handmatig Opslaan | Record 5, versie 5, status `review`; nieuwe beoordeling `2026-09-18T05:42:50.557664+00:00`, exact dezelfde kandidaat. |
| Nieuwe browsersessie → Expert Review | Zelfde definitie, drie onderdelen `Voldoet`, zelfde beoordelingstijdstip, gebonden beoordelingskwitantie zichtbaar. |
| Uploadroute | Fixture werkelijk geüpload (708 tekens), daarna metadata ingevoerd en succesmelding; onafhankelijk JSON-bestand op schijf bevat alle drie velden. |

De browsertool liep tijdens upload zeer lang vast; de uiteindelijke upload en vervolgcontroles zijn wel uitgevoerd. De oorspronkelijke beoordeling is niet vervangen door een mock. Er is geen no-linkuitzondering of menselijke goedkeuring aangemaakt.

### Grenzen van dit resultaat

- De bestaande P01-recordinvoer heeft geen peildatum (`null`). De AI meldt die onzekerheid expliciet. De bronversie is vastgelegd; overeenstemming met een beoogde peildatum is hiermee niet bewezen.
- Hyperlinks worden op vorm gecontroleerd, niet via een netwerkbezoek. De formulering van het model over een werkende/bereikbare hyperlink is geen gemeten bereikbaarheidsbewijs.
- Het totaal over alle 53 regels blijft geblokkeerd: 30 voldoet, 7 voldoet niet, 12 nog te beoordelen en 4 niet beoordeeld. Deze hertoets betreft CON-02/P01.
- Expert Review heeft de bestaande datum-sorteringsfout DEF-805; de readback is uitgevoerd met sortering `Begrip A-Z`.
- Automatische draftopslag blijft een apart defect; de geteste herstelroute gebruikt handmatig Opslaan.

## Tests en onafhankelijke CLI-review

Implementatie en alle correcties: **Claude Code CLI**, sessie `d6f8992f-4582-4145-8a6a-4e6a5203815e`, echte binary `~/.local/bin/claude`. Hoofdsessie schreef geen applicatiecode of tests.

Onafhankelijke diffreview: **Codex CLI**, sessie `01a0b147-0028-75a3-b3f3-179205f876bc`. Eerste review vond één P2; delta-review sloot deze. De kleine foutmeldingcorrectie en de latere formuliercorrectie zijn door dezelfde reviewer afzonderlijk gesloten. Geen resterende bevinding binnen de beoordeelde herstelcode.

- Volledige unit-suite op `503bbe04d`: **6143 passed, 75 skipped, 722 deselected, 1 xfailed, 21 subtests passed**, exitcode 0 (279,56 s).
- `make lint`: Ruff schoon; Black 390 bestanden ongewijzigd; exitcode 0.
- Vooraf rode regressies; na correctie gerichte tests groen. De echte AppTest toont rood naamverlies en niet-opgeslagen metadata, daarna groen naambehoud, opslag/readback en voorrang van een ingelogde identiteit.
- Volledige CLI-logs staan onder `/private/tmp/DEF-808-809-uitvoering-20260917/` (`claude-run1` t/m `claude-run6.jsonl`, `codex-review*.jsonl`, `final-make-test-v2.log`). Beknopte review- en testbewijzen staan naast dit document.

## Afzonderlijk vastgelegde vervolgen

- [DEF-810](https://linear.app/definitie-app/issue/DEF-810): ontbrekende `definitie_drafts`-tabel bij autosave.
- [DEF-811](https://linear.app/definitie-app/issue/DEF-811): Expert Reviews eigen hervalidatie blijft volgens code-review in de sessie; aparte browserreproductie nog nodig.
- [DEF-812](https://linear.app/definitie-app/issue/DEF-812): bestaande niet-atomaire documentmetadataopslag kan bij een schrijffout het bestand beschadigen.
- [DEF-813](https://linear.app/definitie-app/issue/DEF-813): vergelijkbaar conditioneel naamveld in de afzonderlijke bestaande voorstelsectie; aparte reproductie nog nodig.

## Bewijsbestanden

- `p01-readback-v1.json`: onafhankelijke SQLite-readback met kandidaat, bronnen, AI-beoordeling en kwitantie.
- `upload-readback-v1.json`: metadata uit het daadwerkelijke uploadbestand.
- `herkomst-en-historie-v1.json`: runtimevergelijking en bewaarde bronbewijshistorie.
- `tests-finale-v1.txt`, `final-lint.log`: testuitkomst en lint.
- `codex-review1.md`, `codex-reviewdelta1.md` t/m `codex-reviewdelta3.md`: eerste oordeel en sluiting van concrete bevindingen.
- `apptest-red-c18a7ec3-waarnemingen.json`, `apptest-green-waarnemingen.json`: echte rerunobservaties.

Het eerdere uitvoerdersrapport beschrijft het eerste implementatiemoment; dit document bevat de definitieve code- en testidentiteit.
