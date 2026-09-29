**Deze diff is nog niet inhoudelijk gereed: één belangrijke acceptatieleemte in de O1-passageafbakening.** Geen overige nieuwe regressies bevestigd.

**Bevinding R1 — Important, mergeblokker; dispositie: fix nu.**

In [judgment_review.py:154](/Users/chrislehnen/Projecten/Definitie-app/src/services/validation/evaluators/judgment_review.py:154) worden komma’s, puntkomma’s en dubbele punten gevolgd door witruimte zonder verdere functiecontrole als passagegrens gebruikt. Daardoor ontbreekt soms juist de handeling of afbakening die de reviewer moet beoordelen.

Offline gereproduceerd met de echte evaluator en aanwezige context:

| Invoer | Geciteerde passage |
|---|---|
| `Handeling die moet, na toestemming van de rechter, worden verricht.` | `Handeling die moet` |
| `Aanvraag die moet worden beoordeeld op: volledigheid, juistheid en tijdigheid.` | `Aanvraag die moet worden beoordeeld op` |

De posities zijn correcte tekstuitsneden en de status blijft `review_required`. Het citaat is echter geen volledig dragend zinsdeel. De terugval op regel 158 helpt uitsluitend wanneer precies de marker overblijft. Dit schendt B2 en WP3-acceptatiepunt 2; het is een leemte in de nieuwe functionaliteit, geen bewezen achteruitgang tegenover de oude evaluator.

**Minimale correctie:** gebruik bij zulke onzekere grenzen de volledige dragende zin of kern, zoals al toegestaan. Voeg gerichte regressiegevallen voor tussenzinnen en opsommingen toe. Behoud onderscheidbare posities voor herhaalde passages.

Reproductie: [diagnose_passages.py](/private/tmp/def771-codex-review-1ZSCEP/diagnose_passages.py), [feitelijke uitvoer](/private/tmp/def771-codex-review-1ZSCEP/diagnose_passages.json). Uitgevoerd met `apprepo/.venv/bin/python -B`, offline-bootstrap vóór applicatie-imports; exit 0.

**Conclusie per acceptatiegebied**

| Gebied | Conclusie |
|---|---|
| 1. B1–B6, canoniek contract en skills | Akkoord. N/G/T/H, bronannotatie, ASTRA-paar en §6-vervangingen behouden; beide contractkopieën bytegelijk en gebonden aan `def771-int02/2`. Voorbeeldrijen stemmen overeen met register v5. |
| 2. Generatie-instructie | Akkoord. G is letterlijk synthese §3; rendering met/zonder voorbeelden bewezen. Eén-zincontract behouden. DEF-612-conflict blijft benoemd; buurregel ongemoeid. |
| 3. O1-passagehulp | **Niet akkoord wegens R1.** Exacte toetsvraag, neutrale hulp, signaalloze waarschuwing en controleerbare posities zijn aanwezig. Herhaling en raw/cleaned-onderscheid zijn afgedekt. |
| 4. S1-signalen | Akkoord. Zeven oude patronen behouden, exact zes goedgekeurde aanvullingen. C02/C83 treffen; C13/C59/C105 blijven signaalloos. Beschrijvende gevallen krijgen geen automatische afkeur of score. |
| 5. NE en resultaatcontract | Akkoord binnen het geteste bereik. C06/C23/C56 krijgen exacte NE-redenen; serviceguard en evaluator gebruiken dezelfde helpers. Publieke doorgifte, `rule_results`-schema, conversie en bestaande waarschuwingrenderer zijn afgedekt. 2.2.0 is additief. |
| 6. Scopebehoud | Akkoord. Productie-UI wijzigt uitsluitend de RR-tuple, plus commentaar. Geen wijzigingen aan poort, herstel, issues-helper, expertreview-herladen, legacy-evaluatoren, O2 of effectmeting. |
| 7. Tests en proces | Testgevallen behouden; WP4-context en versieassertiecorrecties zijn passend. RED→GREEN-bewijs aanwezig. C25 heeft een NE→RR-statusproef; die probe is geen falende pytest-assertion. Beide featurebranches hebben geen getrackte werkboomwijzigingen of verwijderde bestanden. Historische hookuitvoering is niet volledig onafhankelijk geattesteerd. |
| 8. Dossierproeven en ZIP’s | Akkoord binnen hun bewijsgrenzen. C1-run2: 36/36, exit 0; vastgelegde codehashes passen bij HEAD. WP1-opbouw weigert het huidige `/2`-record vóór schrijven. Beide ZIP’s wijzigen uitsluitend de drie bijbehorende skillbestanden, bytegelijk aan de beheerde bron. |

De [bewijscontrole](/private/tmp/def771-codex-review-1ZSCEP/bewijscontrole.json) bevat de gecontroleerde contract-, ZIP-, replay- en testlogvergelijkingen.

**Bestaande beperkingen en bewijsgrenzen**

Het behouden pakketbewijs vermeldt respectievelijk 18, 6, 146, 437 en 57 geslaagde tests, plus lint. Deze selecties overlappen. De uiteindelijke volledige suite bevat 52 DEF-771-tests zonder failures of skips.

De volledige suite blijft **rood: 67 failed, 8212 passed, 114 skipped, 24 xfailed**. Ik heb de XML’s vergeleken: 66 failures komen terug in de gerichte basisrun; de security-decoratorfailure is afzonderlijk op basis gereproduceerd. Dit is geen identieke volledige baselinevergelijking en geen algemene regressievrijheidsclaim.

De bestaande violation-codes passen nog niet in het volledige schema; de nieuwe schematests bewijzen alleen `rule_results`. Actieve skillpublicatie ontbreekt nog. Modulerendering, onderschepte Streamlit-aanroepen en offline transport bewijzen geen volledige UI-/opslag-/exportdoorloop, inhoudelijk normoordeel of kwaliteitswinst.

**Beoordeelde identiteit**

- App: `0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d` → `5fb535ee45671007e5cb4557509560c793eec290`.
- Skills: `1e27a2da7668437423af3962cce48af5f1bc591b` → `750068253a7389e201daedc5b9aa0afd5c0be032`.
- Beide opgegeven SHA-256-diffidentiteiten exact bevestigd.
- Claude-uitvoerder: `a4b588d6-e4a1-4fd6-8f80-0aac55013d90`.
- Deze Codex-review: `01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`.

Geen bronbestanden gewijzigd, brede tests herhaald of delegatie gestart. **Eindoordeel: eerst R1 corrigeren en gericht in dezelfde reviewsessie laten controleren; de overige beoordeelde onderdelen zijn binnen bovenstaande bewijsgrenzen akkoord.**