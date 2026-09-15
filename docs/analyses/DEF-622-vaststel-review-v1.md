# DEF-622 — onafhankelijke vaststelreview

Delta `57fd342cc..c8879ec70`; verse Codex CLI-reviewer
`01a0a033-e7d6-73b1-ac75-cde7c46c09e3`. Read-only, zonder delegatie of providers.
Claude blijft implementer. Eerdere contract-/duplicaatreviews blijven gesloten.

Coördinator: 57 tests, geen failures/errors/skips, exit 0 op exacte geïsoleerde
bron (`reports/def622/coordinator-establish-source.json` en `coordinator-establish.xml`).
Nieuwe batch: 14 tests groen; brede batch: 2239, nul failures/errors, 13 bestaande
skips. Deze dekking mist de onderstaande vier gevallen.

Alle bevindingen zijn **Important**, dispositie **fix nu** naar dezelfde Claude:

| ID | Bron op c8879ec70 | Bewezen gedrag | Herstelrichting |
|---|---|---|---|
| V1 | `database/definitie_crud.py:195` | Vastgesteld 'waarmerk' met synoniem 'certificaat' verhindert vaststelling van het andere begrip 'certificaat'. | Exclusiviteit op hetzelfde begrip begrenzen; lookup houdt bestaande synoniemen. |
| V2 | `services/definition_workflow_service.py:829` | Review zonder versiebinding wordt na wijzigen én terugzetten van tekst weer geldig op versie4; review mét versie wordt na opslaan juist afgewezen. | Beoordeelde versie expliciet binden en de versiebump van reviewopslag consequent verwerken. |
| V3 | `database/definitie_crud.py:248` | Payload zegt actorA, opslaander/audit zegtB; review wordt als A bewaard en goedgekeurd zonder bevestigde herkomst van A. | Reviewactor bij vastlegging aan betrouwbare actorbron binden, inconsistentie vóór mutatie weigeren. Geen eis dat latere vaststeller dezelfde persoon is. |
| V4 | `database/models.py:152` | Meerdere markers: necessary-first geeft pass, registration-first blocked; geldige eerste plus misvormde tweede wordt vastgesteld. | Volledige markerverzameling controleren; dubbelzinnige/misvormde registratie blokkeren. |

Reviewer bevestigde afzonderlijk volledige rollback inclusief audit na een fout
ná kandidaatupdate, geen mutatie bij gateafwijzing, blokkade van conflicterende
generieke begripwijziging en weigering van een verouderd vervangings-ID.
490 bron-/configbestanden bytegelijk aan de commit; eigen proeven met SQLite
in geheugen. Concurrencytest start twee threads zonder gegarandeerde overlap;
coördinator heeft onderscheidend synchronisatiebewijs bij herstel gevraagd.

Algemene DEF-630-gate en batch5-UI blijven buiten dit oordeel. Alle vier punten
zijn lokale garanties van dit pakket. Volledig lokaal resultaat:
`/private/tmp/DEF-622-codex-establish-review-v1-result.md`. Na herstel volgt
functionele verificatie en beperkte deltareview door dezelfde reviewer.
