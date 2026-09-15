# DEF-622 — onafhankelijke review van koppelingen

Delta `e9ecf6c09..6b233060f`; verse Codex CLI-reviewer
`01a0a047-7df4-7b12-b5b2-603834446fba`. Read-only, geen delegatie. Alle zes
bevestigde bevindingen zijn **Important**, dispositie **fix nu** naar Claude.
Regelnummers horen bij `6b233060f`.

| ID | Bron | Bewezen gedrag | Herstel |
|---|---|---|---|
| K1 | `ui/components/definition_edit_tab.py:1363` | Reviewversie 2, recordversie 4: editor geeft pass doordat definition_version ontbreekt; met versie is het oordeel open. | Geladen recordversie naast review transporteren. |
| K2 | `services/export_service.py:415` | Additional metadata met versie 2 verandert verlopen opgeslagen review op record 4 van open naar pass; merge kan ook context/id/review vervangen. | Validatiecontext uit opgeslagen record opbouwen en tegen aanvullende exportdata beschermen. |
| K3 | `ui/components/expert_review_tab.py:1267` | Re-validate verliest ID/review/versie; niet-bestaande get_org_list/get_jur_list leveren lege lijsten en een geldige org-contextdefinitie faalt. | Canonieke recordadapter gebruiken met alle contractvelden. |
| K4 | `services/definition_repository.py:881` | Readback splitst Toelichting uit recordtekst maar kopieert review over originele tekst: rechtstreeks pass, als domeinobject open. | Eén expliciete tekstbasis voor binding en beoordeling; oorspronkelijke recordtekst behouden waar nodig. |
| K5 | `ui/components/expert_review_tab.py:626` | Zonder sessie-user wordt review en audit opgeslagen als verzonnen standaardactor 'expert'. | Bestaande geldige sessie-identiteit eisen; ontbreken blokkeert vastlegging. Geen nieuwe loginarchitectuur. |
| K6 | `services/prompts/modules/definition_task_module.py:240` | Actieve finale checklist bevat nog ongeclausuleerd 'Context verwerkt zonder expliciete benoeming'. | Afstemmen op registratiegebruik versus noodzakelijke naam. |

Bewijs: 1196 snapshotbestanden bytegelijk; eigen proeven met productiemethoden
en echte contractlogica, vervangers aan UI/servicegrenzen. Coördinator:18 tests,
nul failures/errors/skips, exit 0; brede Claude-run:3429, nul failures/errors,
13 bestaande skips. Bronbinding/resultaten onder reports/def622/coordinator-connections*.
Export- en expertformtests bewijzen nog niet de volledige productie-UI-keten.

De reeds toegewezen V2a–V2c, uitgebreide AppTests en skillbronpatch zijn niet
opnieuw opgevoerd. K2 bewijst de lokale CON-bindingbreuk, geen geslaagde algemene
exportgate. Volledig lokaal resultaat:
`/private/tmp/DEF-622-codex-connections-review-v1-result.md`.

Na herstel volgen functionele proeven en deltareview door dezelfde reviewer.
