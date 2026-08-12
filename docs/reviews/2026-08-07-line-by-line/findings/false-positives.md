# False positives, deduplicatie en afbakening

De review heeft alleen unieke root causes als finding geteld. Herhaalde
symptomen, reeds bekende oorzaken en signalen zonder aantoonbare impact zijn in
batch-evidence als dedupe, nuance of false positive vastgelegd.

## Belangrijkste deduplicatieklassen

| Klasse | Canonieke voorbeelden | Niet opnieuw geteld |
|---|---|---|
| SQLite transacties, connection ownership en WAL-backups | `PILOT-001`, `B010-001`, `B012-004`, `B097-002` | ResourceWarnings, afgeleide backup- en cachemeldingen |
| URL-/bronvertrouwen en weblookup-dedup | `B007-002`, `B035-006` | extra substringspoofs en URL-fixtureblinde vlekken |
| Ruwe exception- of persoonsgegevens in UI/logs | `B012-001`, `B016-002`, `B045-004` | dezelfde oorzaak op aanvullende callsites |
| Testpad-, marker- en sys.path-schuld | `B052-002`, `B105-002`, `B137-001` | historische of gearchiveerde kopieën |
| Destructieve maintenance-/Git-runbooks | `B135-004`, `B161-001`, `B172-001` | duplicaatinstructies zonder zelfstandige actieve root |
| OntoUML-model- en encodingdefecten | `INV-ENCODING-D2C4CCDFC47C`, `B110-001`–`B121-001` | dezelfde object-ID-fouten in gesplitste ranges |

## Afgewezen signaaltypen

- placeholders en synthetische voorbeeldgegevens zonder echte secret of PII;
- expliciet historische cijfers in duidelijk gemarkeerde archiefdocumenten;
- codefences die bewust fragmentair zijn en niet als uitvoerbare suite worden
  gepresenteerd;
- externe integraties die zonder credentials bewust skippen, tenzij de gate
  daarover ten onrechte succes rapporteert;
- een ontbrekende testmapping op zichzelf: dit blijft traceability `none`, geen
  automatische defectfinding.

De exacte beslissingen en het niet-geteste oppervlak staan per batch in
`batches/evidence/BATCH-*/review-evidence.md`.
