# DEF-622 — onafhankelijke duplicaatreview

Beoordeelde delta: `ddb94d1bf..5191edae1`. Verse onafhankelijke Codex CLI-sessie
`01a0a024-7f72-7e22-b08f-018f419cdae0`, read-only, geen delegatietools. Claude
blijft implementer. De eerdere contractreview is gesloten en niet herhaald.

Bewijs vóór review: brede subset 847 tests; coördinatorcontrole 36 tests inclusief
echte AppTest-klikken. Beide exit 0, nul failures/errors/skips. JUnit:
`reports/def622/batch3-junit.xml` en `coordinator-duplicaat.xml`.

Vier bevestigde bevindingen; regelnummers op `5191edae1`:

| ID | Ernst | Bewezen gedrag | Herstel en dispositie |
|---|---|---|---|
| D1 | Important | Repository vindt hetzelfde vastgestelde record bij dubbele/lege wettelijke basis of Straße/STRASSE; checkerfilter op `definitie_checker.py:173–208` retourneert toch PROCEED zonder record. | **fix nu**: consument deelt volledige canonieke contextvergelijking. |
| D2 | Important | `normalisatie.py:56,66` stringificeert null tot 'None'; dezelfde context wordt niet gevonden in elk van de drie velden. | **fix nu**: null vóór stringconversie wegfilteren volgens bestaande normalisatie. |
| D3 | Important | Handler wijst begrip '123' af vóór try/finally; force_generate, force_duplicate en reden blijven staan en slaan bij volgende aanvraag de duplicaatcontrole over. | **fix nu**: ook vroege afwijzing onder eenmalige consumptie/opruiming. |
| D4 | LOW | Publieke CRUD accepteert bytes als duplicate_reason; nieuw record en audit bevatten reden b'\\x00'. | **fix nu**: betekenisvolle string op deze opslaggrens vereisen. |

Reviewer gebruikte bevroren git-bron in geheugen, echte repository/checker met
SQLite `:memory:` en echte SessionStateManager. Geen providers of gebruikersdata.
Volledige lokale opdracht, transcript en resultaat staan eenmaal onder
`/private/tmp/DEF-622-codex-duplicate-review-v1*`.

Alle vier herstelopdrachten zijn aan dezelfde Claude-sessie gegeven. Batch4-WIP
blijft behouden. Na selectief herstelcommit volgen functionele verificatie en
gerichte deltareview door dezelfde reviewer. Dit oorspronkelijke oordeel claimt
nog geen gesloten bevindingen.
