# DEF-622 — onafhankelijke contractreview

Beoordeelde delta: `3d4b98507..9a4caf674`. Onafhankelijke Codex CLI-sessie
`01a09ffd-ef32-7cd3-a3b1-7d4380d45f4a`; reviewer heeft zelf beoordeeld, zonder
delegatietools, in read-only sandbox. Claude CLI blijft implementer.

Coördinatorverificatie op dit pakket: 480 tests, nul failures/errors/skips,
exit 0 (`reports/def622/coordinator-contract.xml`). Brede implementersubset:
1480 tests, nul failures/errors, twee skips (echte API-key vereist en ontbrekende
golden-fixture), exit 0 (`reports/def622/batch2-junit.xml`). Deze proeven vervangen
de hieronder genoemde ontbrekende regressiedekking niet.

## Bevestigde bevindingen

Regelnummers horen bij `9a4caf674`. Elke bevinding is **Important** en krijgt
dispositie **fix nu**. Opdracht voor herstel is aan dezelfde Claude-sessie gegeven.

| ID | Bron | Bewezen gedrag | Vereist herstel |
|---|---|---|---|
| R1 | `src/domain/context/contract.py:230` | Context `OM`/`om` of `Stichting Straße`/`Stichting STRASSE` geeft bij dezelfde fingerprint verschillende naamdetectie. | Detectie gelijk aan bestaande casefoldvergelijking; originele matchposities behouden; naamfunctie blijft menselijk oordeel. |
| R2 | `src/domain/context/contract.py:271,296` | Actor en reden met waarde `True` of `[""]` worden strings en leveren geldige noodzakelijke-naamreview. | Betekenisvolle strings vereisen; verkeerde typen laten review open. |
| R3 | `src/services/validation/evaluators/context_metadata.py:75` | Twee beginspaties toevoegen aan raw_text wijzigt fingerprint niet als cleaned_text gelijk blijft; oude review blijft geldig, positie wijkt af. | Fingerprint en posities aan dezelfde exacte beoordeelde recordtekst binden. |
| R4 | `src/domain/context/contract.py:435`; service `:1605` | Foutinjectie bij tweede naamdeel wist eerder opgebouwd fail-deel; alleen generieke uitvoeringsfout blijft over. | Fouten per onderdeel afvangen; afgeronde delen en bewezen overtreding behouden naast technische fout. |
| R5 | `src/services/service_factory.py:305,480` | Actieve generatieadapter maakt van overall_score None een 0.0 en verwijdert rule_results. | Nullable score en gestructureerde uitkomsten intact transporteren. |
| R6 | `src/ui/components/validation_view.py:266` | Renderer werpt TypeError bij float(None), vóór de afzonderlijke regeluitkomsten. | Niet-beschikbaar expliciet tonen en regeluitkomsten blijven renderen. |

Reviewer heeft synthetische reproducties op code uit `git show` in geheugen
uitgevoerd. Geen gebruikersdatabase of bestanden gewijzigd. De expliciete
scorefixture is alleen rekenmechanica; de echte manager/cache-matrix blijft
behouden. Geen bevinding op die fixture.

Volledige lokale opdracht, transcript en resultaat staan eenmaal onder
`/private/tmp/DEF-622-codex-contract-review-v1*`. Volgende checkpoint: fixcommit
door Claude, functionele verificatie door coördinator, gerichte deltareview door
dezelfde reviewer. Dit document legt het oorspronkelijke oordeel vast en claimt
geen gesloten bevindingen.
