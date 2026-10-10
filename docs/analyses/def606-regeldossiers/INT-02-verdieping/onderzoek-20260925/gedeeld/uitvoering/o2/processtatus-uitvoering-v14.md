# DEF-835 INT-02 O2 — processtatus uitvoering v14

7 oktober 2026. Vervangt `processtatus-uitvoering-v13.md` (07-10) als actuele processtatus.

## Stand

- O1 (DEF-771) en de O2-beoordelingsdienst (DEF-835, PR #488, 29-09) staan op main. De O2-dienst is niet geactiveerd; de app gebruikt de O1-reviewroute. Geen WP5a-/UI-stap; GitHub Actions blijft uit.
- Werk op `feature/DEF-835-int02-o2` in de werkboom `.claude/worktrees/DEF-835-int02-o2`, gepusht als back-up. Geen PR en geen merge.
- **Fase 1 (regressie) van kwalificatieproef v7 is mechanisch geslaagd: C105, C107 en C112 3/3 juist**, 0 false pass, 0 citaatfouten, 0 technische fouten, US$0,10108, 3 calls. Het meegestuurde antwoordschema is door de API geaccepteerd. Details: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v7-uitslag-v1.md`.
- De inhoudelijke beoordeling van de passagegronden door Chris staat volgens het protocol nog open (onder meer de grond van C107 uit de organisatorische context).

## Besluiten 07-10 (in `besluit-chris-promptcorrectie-en-v3-v1.md`)

1. Code-formulering van prompt /2 geaccepteerd; een expliciet actorvoorschrift in de kern blijft een fail-grond.
2. Eén besluitbestand.
3. Aandachtspunt "meerdere passages" volgen in de proef, nu niet herstellen.
4. Commit op de feature-branch, push als back-up, geen PR/merge.
5. Processtatus v13 (nu vervangen door deze v14).
6. Akkoord v3-proef fase 1 (vervangen door 8).
7. Gitleaks-blokkade: exacte uitzonderingen voor false positives; hook niet omzeild.
8. Manifest v4 (SDK `anthropic` 0.116.0) en fase 1.
9. Citaatposities door de dienst: contract `/2`, prompt `/3`.
10. Manifest v5 en fase 1.
11. Variatiemeting C107 (5 losse calls, buiten de kwalificatie).
12. Smalle dienstregel `discretie_zonder_bedoeling`: contract `/3`.
13. Manifest v6 en fase 1.
14. Antwoordschema via de API (`output_config.format`): prompt `/4`.
15. Manifest v7 (`872482f4…`) en fase 1, tevens live-rooktest van het schema.

## Proefhistorie fase 1

| Ronde | Prompt / contract | Uitkomst | Kosten | Vervolg |
|---|---|---|---|---|
| v4 | /2 / /1 | inhoudelijk 3/3, maar C112 `invalid_citation` (model telde `end` te kort) | $0,082385 | besluit 9: posities door de dienst |
| v5 | /3 / /2 | 2/3; C107 `fail` in plaats van `review_required`; 0 citaatfouten | $0,07772 | besluit 11: variatiemeting |
| variatiemeting C107 | /3 / /2 | 5/5 juist (samen met v5: 5 van 6) | buiten de kwalificatie | besluit 12: dienstregel |
| v6 | /3 / /3 | gestopt na C105: `invalid_output` door extra veld `reason` | $0,02649 | besluit 14: schema via API |
| v7 | /4 / /3 | **3/3 juist, mechanisch geslaagd** | $0,10108 | akkoord fase 2 gevraagd |

## Huidige keten

- **Prompt `def835-int02-prompt/4`**: systeemtekst gelijk aan /3 (`da4a4112…`), plus de schemaroute. Commit `2081899ea`.
- **Schemaroute**: het antwoordschema (`ANTWOORDSCHEMA` in `src/domain/int02/contract.py`, SHA-256 `72adfe74…511f17`) gaat mee als `output_config.format`. De dienst controleert de schemahash vóór de aanroep en eist bevestiging en precies één tekstblok; een niet-ondersteunde combinatie wordt zonder verzending gemeld (`structured_output_unsupported`). Kost per call 1.299 extra invoertokens (circa $0,0065). Verslag: `goldset-voorbereiding/schemaroute-v1/uitvoeringsverslag-claude-v1.md`.
- **Contract `def835-int02-assessment/3`**: citaatposities door de dienst afgeleid (besluit 9) en de dienstregel `discretie_zonder_bedoeling` (besluit 12): een `fail` die alleen gedragen wordt door discretionaire passages met de kern als enige grond, bij onbekende bedoeling, wordt zichtbaar `review_required` / `insufficient_information` met een vaste vraag. In v7 is de regel niet nodig geweest (`omzetting: null` bij alle drie). Contractdocument: `docs/architectuur/contracts/int02_assessment_contract_v3.md`; verslag `goldset-voorbereiding/dienstregel-v1/uitvoeringsverslag-claude-v1.md`.

## Volgende actie

**Akkoord van Chris op fase 2 (ontwikkeling)**, binnen manifest v7 en akkoord v7 (kader 43 calls en US$12):

- 24 ontwikkelgevallen, maximaal 24 calls; na v7-fase 1 resteren in dit akkoord 40 calls en circa US$11,90 (conservatieve reservering $0,23 per call, dus hooguit $5,52 voor fase 2).
- Criterium volgens manifest v7: minimaal 21/24 juist.
- **Let op, max_false_pass:** manifest v7 legt voor ontwikkeling `max_false_pass: null` vast; alleen regressie en hold-out hebben `max_false_pass: 0`. De runner handhaaft in fase 2 dus geen false-pass-grens. Wil Chris max_false_pass 0 ook voor ontwikkeling, dan kan dat als procesafspraak (handmatig toetsen aan de runnertelling) of via een nieuw manifest met nieuw akkoord. Die keuze ligt bij Chris vóór de run.
- Daarna stoppen en bespreken, inclusief aandachtspunt 3 (meerdere passages) en de inhoudelijke beoordeling van fase 1.

Daarna de **hold-out** (16 gevallen; minimaal 14/16 met minimum per label, max_false_pass 0, p95 ≤ 90 s) met een apart akkoord van Chris.

## Actuele documenten

- `besluit-chris-promptcorrectie-en-v3-v1.md` — besluiten 1–15 (07-10).
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v7.json` en `kwalificatie-akkoord-v7.json` — de geldende proef.
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v7-uitslag-v1.md` en `kwalificatieproef-v7/` — uitslag en bewijs fase 1.
- Eerdere uitslagen: `kwalificatieproef-v4-uitslag-v1.md`, `-v5-`, `-v6-` (zelfde map) en `goldset-voorbereiding/variatiemeting-c107-v1/uitslag-v1.md`.
- `takenlijst-v51.md` — laatste takenlijst van de coördinator (30-09).

## Achterhaald (ongewijzigd bewaard)

- `processtatus-uitvoering-v13.md` (07-10): stand vóór de v3/v4-proef, met prompt /2 en akkoord op fase 1 van v3; achterhaald door deze v14.
- De akkoorden en manifesten v3–v6: elk vervangen door het volgende besluit (8, 10, 13, 15).
- Eerder als achterhaald benoemd in v13 en dat blijft zo: `processtatus-uitvoering-v12.md`, `goldset-voorbereiding/labelronde-v1/takenlijst-v14.md`, `goldset-voorbereiding/herwerking-v1/uitvoeringsstatus-v1.md`.
