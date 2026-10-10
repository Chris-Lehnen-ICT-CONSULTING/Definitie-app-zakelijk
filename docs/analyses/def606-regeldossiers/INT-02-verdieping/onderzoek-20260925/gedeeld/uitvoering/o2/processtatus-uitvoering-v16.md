# DEF-835 INT-02 O2 — processtatus uitvoering v16

8 oktober 2026. Vervangt `processtatus-uitvoering-v15.md` (07-10) als actuele processtatus.

## Stand

- O1 (DEF-771) en de O2-beoordelingsdienst (DEF-835, PR #488, 29-09) staan op main. De O2-dienst is niet geactiveerd; de app gebruikt de O1-reviewroute. Geen WP5a-/UI-stap; GitHub Actions blijft uit.
- Werk op `feature/DEF-835-int02-o2` in de werkboom `.claude/worktrees/DEF-835-int02-o2`. HEAD `258d26d89` (manifest v9, akkoord en gitleaks-uitzondering 19) staat gelijk met origin. Geen PR en geen merge.
- **Ongecommit in de werkboom:**
  - de uitslag van v9 (`kwalificatieproef-v9-uitslag-v1.md` en de map `kwalificatieproef-v9/`), besluit 21 en de variatiemeting v9 (script, `live-v1/`, `test_def835_int02_variatiemeting_v9.py`);
  - besluit 22 (R1 + R2, contract `/5`): code, tests, contractdocument v5, ontwerpnotitie, uitslag variatiemeting en uitvoeringsverslag v4.
- **Contract `def835-int02-assessment/5`** (besluit 22), prompt `def835-int02-prompt/6`, schema `d3ad029e…e715` (beide ongewijzigd sinds besluit 19).
- **Testsituatie besluit 22:** de gerichte tests, INT-03/ESS-03, ruff, black, de papieren toets (27/27 met 6/6 review), de mutatiecontrole (24/24 gedood) en de wat-als-replay zijn groen. Rood blijven alleen de 11 tests van het afgeronde v9-meetscript (`ketenbestand_afwijkend`: `contract.py` wijkt nu bewust af van manifest v9). Dat vraagt vóór de commit een keuze van Chris (zie uitvoeringsverslag v4, §4).
- **Hold-out niet gedraaid en niet gelezen.**

## Besluiten 18–22 (in `besluit-chris-promptcorrectie-en-v3-v1.md`)

- **18 — manifest v8, fase 1 en 2 als consistentietoets.** Contract /4 (bronfuncties, besluit 16 en 17), prompt /5, schema `d3ad029e…`, ontwikkeling `max_false_pass` 0. Gitleaks-uitzondering 18.
- **19 — kaal bron-ID en prompt /6.** Na v8: een kaal bron-ID ("B1") geldt als `bron/B1` (G060), binnen /4. Prompt /6: een grondbron die alleen de formulering herhaalt, is geen bewijs voor `criterion` (G045).
- **20 — manifest v9, fase 1 en 2 opnieuw.** Prompt /6; contract /4 en schema ongewijzigd. Gitleaks-uitzondering 19.
- **21 — eerst de variatie meten.** Na v9 (G050 kritieke false pass): de 24 ontwikkelgevallen twee keer extra, buiten het kwalificatieprotocol, zonder reparatie.
- **22 — R1 + R2, contract /5.**
  - R1: een passage met kernvorm `discretion_form` is nooit pass (`discretie_nooit_pass`).
  - R2: een `unclear`-grondbron naast een kenmerkbron is geen pass (`onduidelijk_naast_kenmerk`).
  - Volgorde: gebrek → bestaande reviewgronden → R1 → R2 → besluit 17 → pass. De omzetting is zichtbaar.
  - Versie opgehoogd naar /5 met versiebewuste hercontrole (een /4-document is historisch).
  - Kanttekening: consistentietoets, mede op G050/G060 gemaakt; alleen de hold-out geeft bewijs.

## Proefhistorie

| Ronde | Prompt / contract | Fase | Uitkomst | Kosten |
|---|---|---|---|---|
| v4 | /2 / /1 | regressie | inhoudelijk 3/3, C112 `invalid_citation` | $0,082385 |
| v5 | /3 / /2 | regressie | 2/3; C107 `fail` | $0,07772 |
| variatiemeting C107 | /3 / /2 | buiten kwalificatie | 5/5 juist | — |
| v6 | /3 / /3 | regressie | gestopt na C105: `invalid_output` | $0,02649 |
| v7 | /4 / /3 | regressie | 3/3, geslaagd | $0,10108 |
| v7 | /4 / /3 | ontwikkeling | 18/24, niet geslaagd; 5 false pass | $0,88056 |
| v8 | /5 / /4 | regressie | 3/3 | ± $0,11 |
| v8 | /5 / /4 | ontwikkeling | gestopt na 22/24 (`invalid_citation` G060); 19/22 juist; 1 onterechte pass (G045) | cumulatief v8 $1,07 |
| v9 | /6 / /4 | regressie | 3/3 | ± $0,11 |
| v9 | /6 / /4 | ontwikkeling | gestopt na 17/24 (`kritieke_false_pass` G050); 15/17 juist | cumulatief v9 $0,86 |
| variatiemeting v9 | /6 / /4 | buiten kwalificatie, 2 × 24 | h1 21/24, h2 22/24; 1 à 2 onterechte passes per run (G050, G060) | $2,17 |
| wat-als besluit 22 | /6 / /5 (offline) | 93 bewaarde antwoorden | onterechte passes 5 → 1, kritiek 2 → 0, geen terechte pass verloren; precies 4 wijzigingen (G050 v9, G050 h1, G060 h1, G060 h2) | geen calls |

Onterechte passes per ronde: v7 5, v8 1 (G045), v9 1 (G050), meting 1–2 per run. Uitslagen: `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v8-uitslag-v1.md`, `kwalificatieproef-v9-uitslag-v1.md` en `goldset-voorbereiding/variatiemeting-v9/uitslag-v1.md`.

## Stopafspraak (Chris, 08-10-2026)

**v10 is de laatste run van dit onderdeel.** Na v10 wordt de uitslag vastgelegd en wordt er gestopt. Daarna kiest Chris tussen:
- de hold-out (met een apart akkoord), of
- O2 parkeren.

Er komt na v10 geen nieuwe reparatieronde op de ontwikkelgevallen.

## Huidige keten (na commit van besluit 22)

- Contract `def835-int02-assessment/5` (`src/domain/int02/contract.py`; contractdocument `docs/architectuur/contracts/int02_assessment_contract_v5.md`).
- Prompt `def835-int02-prompt/6`, systeemprompt `a8f701ac…d8e7` (ongewijzigd).
- Antwoordschema `d3ad029e…e715` (ongewijzigd).
- Ketenbestanden ten opzichte van manifest v9: alleen `contract.py` gewijzigd.

## Volgende acties

1. **Korte check** van de diff van besluit 22, inclusief de keuze over de 11 rode tests van het v9-meetscript.
2. **Commit** (na akkoord), met de logs via `git add -f`.
3. **Manifest v10** offline: contractversie /5, nieuwe bestandshash van `contract.py`, prompt en schema ongewijzigd, gevallen ongewijzigd; **gitleaks-uitzondering 20** (verwacht dezelfde bevinding als 18 en 19).
4. **Akkoord** van Chris op v10.
5. **Fase 1 + 2** (regressie, daarna ontwikkeling; consistentietoets 7A).
6. **Uitslag** vastleggen.
7. **Stop** volgens de stopafspraak; daarna kiest Chris: hold-out (apart akkoord) of O2 parkeren.

## Actuele documenten

- `besluit-chris-promptcorrectie-en-v3-v1.md` — besluiten 1–22.
- `goldset-voorbereiding/bronfuncties-ontwerp-v1.md` — ontwerp /4, met de wijzigingsnotitie van besluit 22.
- `docs/architectuur/contracts/int02_assessment_contract_v5.md` — het geldende contract (v4 historisch).
- `goldset-voorbereiding/bronfuncties-v1/uitvoeringsverslag-claude-v4.md` — uitvoering besluit 22, testuitkomsten, wat-als, hashes en wat er nodig is voor v10.
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatie-manifest-v9.json` en `kwalificatie-akkoord-v9.json` — de laatst geldende proef.
- `goldset-voorbereiding/goldset-freeze-v1/kwalificatieproef-v8-uitslag-v1.md`, `kwalificatieproef-v9-uitslag-v1.md`; bewijs in `kwalificatieproef-v8/` en `kwalificatieproef-v9/`.
- `goldset-voorbereiding/variatiemeting-v9/uitslag-v1.md` en `live-v1/samenvatting.md`.
- `takenlijst-v51.md` — laatste takenlijst van de coördinator (30-09).

## Achterhaald (ongewijzigd bewaard)

- `processtatus-uitvoering-v15.md` (07-10): stand na fase 2 van v7, met het besluit over het vervolg als volgende actie; achterhaald door deze v16.
- Eerder als achterhaald benoemd en dat blijft zo: `processtatus-uitvoering-v14.md`, `-v13.md`, `-v12.md`, de akkoorden en manifesten v3–v8, `goldset-voorbereiding/labelronde-v1/takenlijst-v14.md`, `goldset-voorbereiding/herwerking-v1/uitvoeringsstatus-v1.md`.
- `docs/architectuur/contracts/int02_assessment_contract_v4.md`: historisch sinds contract /5.
