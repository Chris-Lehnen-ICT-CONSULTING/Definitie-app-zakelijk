# INT-02 O2 — uitslag kwalificatieproef v7, fase 1 (regressie)

7 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v7/` (`regressie-resultaat.json`, `regressie-bundel.json`, `grootboek.jsonl`, `regressie-afronding.voltooid`) en het runlog. Er is geen nieuwe call gedaan en er is niets opnieuw gedraaid. De run gebeurde op HEAD `6551a6345`; de API-sleutel kwam via de shell uit de `.env` van de hoofdcheckout en is niet getoond.

## Kader

- Manifest `kwalificatie-manifest-v7.json`, SHA-256 `872482f4f201b2c5a7e04e3a0dd6589f088518adb7af99f395da08f89ccfc84b` (zelf nagerekend); identiteit `1ba9794ff9432b5c05ad7cf123f086a1c53b84756c4d32bdcc3163cc83a426a3`.
- Akkoord `kwalificatie-akkoord-v7.json`, SHA-256 `d3c6ac8ca8b6f291fd8f301b14d2a2aade1832c9fa82b3c28800af869d399c45` (zelf nagerekend); gevallen `af1ab46c…6953`.
- Anthropic `claude-opus-5` (gerapporteerd model bij alle drie de calls), profiel `def835-kwalificatieproef-opus5-v1`, prompt `def835-int02-prompt/4` (tekst /3 plus de schemaroute), contract `def835-int02-assessment/3` (met de dienstregel van besluit 12). Thinking uitgeschakeld (0 thinking-tokens), `service_tier` standard.
- Uitsluitend fase 1 (C105, C107, C112), volgens besluit 15.
- Start 16:40:35 UTC, einde 16:41:03 UTC, looptijd 28,2 s. Runner exit 0.
- 3 inferenties en 3 telverzoeken; 0 herhalingen en 0 terugval naar een ander model; geen gecachete antwoorden.
- Grootboek: `fase_einde` met `bewijs_opgeslagen: true`, `mechanisch_geslaagd: true`, `stopreden: null`. `regressie-afronding.voltooid` staat er.

## Per geval

| Geval | Verwacht | Model (verdict / functie / onzekerheid / grondveld) | Juist? | Citaten (posities door de dienst afgeleid) | Dienstregel | Uitkomst |
|---|---|---|---|---|---|---|
| C105 | fail | `fail` / `actor_prescription` / `none` / `bedoeling` | ✔ | kern 0–36 ("De medewerker laat de aanvrager toe."); grond bedoeling 0–23 | niet toegepast (`omzetting: null`; bedoeling bekend) | `fail`, geldig |
| C107 | review_required (insufficient_information) | `insufficient_information` / `unclear` / `decisive` / `organisatorische_context` (ref 0) | ✔ | kern 0–86 (de hele kern); grond organisatorische_context[0] 0–28 ("synthetische begrippenstudie") | niet toegepast (`omzetting: null`): het model gaf zelf geen `fail`, dus de regel had niets om te zetten | `review_required` / `insufficient_information`, geldig, coverage `partial`, eigen modelvraag |
| C112 | pass | `pass` / `criterion` / `none` / `bedoeling` | ✔ | kern 0–73; grond bedoeling 0–47 | niet toegepast (`omzetting: null`; geen fail) | `pass`, geldig |

De vraag bij C107 komt van het model zelf, niet de vaste vraag van de dienstregel: of "naar het gemotiveerde oordeel van de beoordelaar voldoende onderbouwd" vastgelegde onderbouwingskenmerken bedoelt of eigen afwegingsruimte van de beoordelaar.

Mechanische telling volgens de runner:

| Teller | Waarde |
|---|---|
| juist | 3/3 |
| juist fail | 1/1 |
| juist review_required | 1/1 |
| juist pass | 1/1 |
| false pass | 0/2 |
| kritieke false pass | 0/1 |
| false fail | 0/2 |
| gemiste overtreding | 0/1 |
| gepaste onthouding | 1/1 |
| onterechte onthouding | 0/2 |
| citaatfout | 0/3 |
| technische fout | 0/3 |

Redenen voor niet geslaagd: geen. **Fase 1 is mechanisch geslaagd (3/3, criterium 3/3 en max_false_pass 0).**

## Schemaroute: door de API geaccepteerd

Deze run was ook de live-rooktest van het schema (besluit 14/15).

- Alle drie de verstuurde payloads in de bundel bevatten `output_config.format` met `type: json_schema`. De SHA-256 van het meegestuurde schema (berekend zoals `response_schema_sha256`: compacte JSON, zonder sortering) is zelf nagerekend: `72adfe7428b67bf0fd999520581f0fc2cbe801101e1e8e6df300179405511f17`, gelijk aan `router.antwoordschema_sha256` in manifest v7 en aan de pin in besluit 14.
- Systeemtekst, berichten, model, `max_tokens` (6000) en thinking zijn byte-gelijk aan de v5-bundel; het enige verschil in de payload is `output_config`.
- De API antwoordde op alle drie de calls met HTTP 200, `stop_reason` `end_turn` en precies één tekstblok; elke antwoordtekst is geldige JSON zonder onbekende velden. Er was geen `structured_output_unsupported`, geen weigering en geen `invalid_output`.
- Een aparte schemabevestiging van de provider bestaat niet: de API stuurt het schema niet terug en de bundel bevat daar dus geen veld voor. De bevestiging is afgeleid uit de bovenstaande punten. De dienst eist volgens besluit 14 dat de AI-laag het verzonden schema bevestigt; alle drie de documenten zijn `completed` zonder foutcategorie, dus die controle is doorlopen.
- Het v6-probleem (extra veld `reason` in een passage bij C105) kwam niet terug.

## Tokens ten opzichte van v5/v6

| Geval | Invoer v5 | Invoer v6 | Invoer v7 | Verschil | Uitvoer v5 | Uitvoer v7 |
|---|---|---|---|---|---|---|
| C105 | 3.543 | 3.543 | 4.842 | +1.299 | 269 | 262 |
| C107 | 3.574 | — | 4.873 | +1.299 | 418 | 583 |
| C112 | 3.567 | — | 4.866 | +1.299 | 285 | 282 |

Het verschil is per call precies gelijk (+1.299 invoertokens). Omdat de rest van de payload byte-gelijk is, komt het geheel door het meegestuurde schema (de 1.636 bytes `output_config` plus wat de provider daarvoor intern toevoegt; die twee zijn uit de usage niet te scheiden). De tokenmeting vooraf (`count_tokens`, met schema) gaf per geval exact het later gemelde aantal invoertokens.

## Kosten en latentie

| Geval | Invoertokens | Uitvoertokens | Kosten | Latentie call | Duur dienst |
|---|---|---|---|---|---|
| C105 | 4.842 | 262 | $0,03076 | 8.212 ms | 8.832 ms |
| C107 | 4.873 | 583 | $0,03894 | 8.002 ms | 8.191 ms |
| C112 | 4.866 | 282 | $0,03138 | 9.858 ms | 10.181 ms |
| **Totaal** | | | **$0,10108** | | |

Kosten zijn gemelde usage × routerprijzen ($5 per 1M invoertokens en $25 per 1M uitvoertokens). Er was geen onzekere call; reservering per call $0,23. Dit is geen providerfactuur. Van het totaal is $0,019 (3 × 1.299 invoertokens) de prijs van het meegestuurde schema.

Latentie maximaal en p95: 9.858 ms (C112). Dat is hoger dan in v5 (maximaal 6.434 ms). Of dat door de schemagrammatica komt of door gewone spreiding, valt uit drie calls niet af te leiden; het blijft ruim onder de hold-outgrens van 90.000 ms.

## C107 over de proefrondes

| Ronde | Prompt / contract | Uitkomst C107 |
|---|---|---|
| v2 | /1 / /1 | `fail` (en een `start` één codepunt te laat) |
| v4 | /2 / /1 | `review_required` / `insufficient_information` (juist) |
| v5 | /3 / /2 | `fail` (`discretionary_decision_rule`, `non_decisive`) |
| variatiemeting | /3 / /2 | 5 van 5 `review_required` / `insufficient_information` (juist; buiten de kwalificatie) |
| v6 | /3 / /3 | niet gedraaid (stop na C105) |
| v7 | /4 / /3 | `review_required` / `insufficient_information` (juist, zonder dienstregel) |

v7 is één call en bewijst op zichzelf geen stabiliteit. Mocht het model bij C107 opnieuw een discretionaire `fail` op alleen de kern geven, dan zet de dienstregel van contract /3 dat zichtbaar om naar `review_required`.

## Runlog

Het log bevat naast de eindregel twee monitoringmeldingen: "High Error Rate 1.000" en "Low Cache Hit Rate 0.000". In de live fase zelf zijn 0 technische fouten geteld en is bewust zonder cache gedraaid. Bij v5 meldde Chris dat de foutmelding uit de dry-run vooraf komt (opgevangen verzoeken die de monitoring als mislukt telt). Of dat hier ook zo is, heb ik niet nagegaan: het log bevat geen tijdstempels of herkomst.

## Aandachtspunt 3 (besluit 3, meerdere passages)

**Niet toetsbaar in deze 3 gevallen.** Alle drie de antwoorden hadden precies één passage. Het punt blijft open voor de ontwikkelfase.

## Open: inhoudelijke beoordeling

De inhoudelijke beoordeling van de passagegronden, de normgrond en de relevantie van de vraag door Chris staat volgens het kwalificatieprotocol in `regressie-resultaat.json` op `open`; de runner vult die niet in. Ter beoordeling bij C107: het model gebruikt "synthetische begrippenstudie" (organisatorische context) als grond voor een passage met functie `unclear`, en noemt in zijn redenering juist dat die context niets beslist.

## Vervolg

Fase 1 is gestopt zoals afgesproken. Ontwikkeling (24 gevallen) en hold-out (16) vragen elk een afzonderlijk akkoord van Chris; zie `../../processtatus-uitvoering-v14.md`. Het v7-bewijs blijft ongewijzigd.
