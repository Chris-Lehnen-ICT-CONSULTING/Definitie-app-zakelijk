# DEF-835 — dossiercommit geblokkeerd door twee metadatawaarnemingen

28 september 2026. Code/eindreview blijven geldig op `979ca0585100d94b613829d924c6d8bba4f24f1b`. Dit gaat uitsluitend over de daarna uitgevoerde lokale commit van 38 opdracht-, verslag-, manifest- en bewijsbestanden.

De normale commitpoging `docs(DEF-835): Leg gereviewde modelproef en integratievoorstel vast` is niet voltooid. De lokale gitleaks-hook meldde:

`{"code": "findings_present", "finding_count": 2, "scanned_bytes": 252917, "status": "blocked"}`

De andere lokale controles slaagden. Geen hookskip, allowlistwijziging, smaller scanbereik of alternatieve commitroute gebruikt. De 38 bestanden blijven staged; nieuwe afsluitnotities blijven lokaal. Geen push/merge.

## Diagnose zonder secretinhoud te publiceren

Het DEF-522-runbook en de gedeelde scanner zijn gelezen. Een tijdelijke, alleen lezende diagnose gebruikte dezelfde staged-gate, dezelfde gepinde gitleaks 8.29.1 en ongewijzigde scanconfiguratie. Alleen RuleID/File/StartLine/EndLine werden zichtbaar gemaakt; het oorspronkelijke beoordelingsresultaat bleef blocked, gate-exit 1. Geen ruwe Match/Secret of stderr gepubliceerd.

| Bestand onder bewijs/ | Regel | Regel-ID | Gecontroleerde inhoud |
| --- | --- | --- | --- |
| `modelproef-manifest-v1.json` | 65 | generic-api-key | Waarde van JSON-sleutel `src/utils/async_api.py`: 64-hex SHA-256, exact gelijk aan de hash van dat bronbestand |
| `modelproef-manifest-v2.json` | 106 | generic-api-key | Dezelfde bronhash, opnieuw exact met bronbestand vergeleken |

Beide waarnemingen zijn dus onderbouwde false positives op technische metadata, geen aangetroffen credentials. Dat bewijs is geen toestemming om de beveiligingsconfiguratie te wijzigen. Het runbook beperkt uitzonderingen tot exact pad én exacte inhoud, met eigenaar Chris en regressiebewijs. Een eventuele nieuwe uitzondering voor deze twee metadataregels vraagt een afzonderlijk besluit; er is niets toegepast. De manifesten zijn niet herschreven of uit de scan gehaald om de blokkade te ontwijken.

Dit blokkeert het afronden van de dossiercommit/publicatie; niet de reeds gecommitte runnercode, offline verificatie, onafhankelijke herreview of het lezen van de concrete proef-/integratievoorstellen. Alle dossierbestanden staan blijvend op de aangewezen repositorylocatie. De open profiel-/budget- en WP5a-vragen zijn ongewijzigd.
