# INT-02 O2 — uitslag variatiemeting v9 (v1)

8 oktober 2026. Meting volgens besluit 21: de 24 ontwikkelgevallen twee keer extra met de keten van v9 (contract /4, prompt /6, schema `d3ad029e…`). Buiten het kwalificatieprotocol: geen kwalificatie, geen DEF-815-claim, consistentietoets (7A). Volledige tabel per geval: `live-v1/samenvatting.md`; ruwe calls: `live-v1/calls.jsonl`.

## Uitkomst

- **Calls:** 48 van 48, zonder stopreden. Kosten US$2,17 (conservatief; plafond US$3,00).
- **Juist:** h1 21/24, h2 22/24 (v9-fase 2: 15/17).
- **Onterechte passes:** 1 à 2 per run. h1: G050 en G060; h2: G060; v9-fase 2: G050.
- **Kritieke false passes:** h1 G050 (net als v9-fase 2); h2 geen.
- **Stabiliteit:** 20/24 stabiel (opgave Chris, besluit 22). `samenvatting.md` telt 22/24 gevallen met dezelfde status in alle runs; wisselend zijn G030 (review/review/pass) en G050 (pass/pass/review). Het verschil tussen 20 en 22 is niet uit de samenvatting te herleiden.
- **Wisselende bronfuncties:** 7 gevallen (G011, G015, G030, G048, G050, G052, G076).

## Lezing

De onterechte passes komen uit twee vaste combinaties:
- **G050:** kernvorm `discretion_form`, terwijl het model de bronnen als `derivation`/`criterion` labelt → pass;
- **G060:** B1 `unclear` naast B2 `criterion` → pass (beide herhalingen; "O naast B telt niet").

Een fout op dezelfde plek in elke run, met wisselende bronlabels, wijst op een structureel gat in de beslisregel en niet op incidentele ruis.

## Gevolg

Besluit 22 (R1 + R2, contract /5): `../besluit-chris-promptcorrectie-en-v3-v1.md`. De offline herbeoordeling van alle 93 bewaarde antwoorden (v8, v9 en deze meting) geeft precies vier wijzigingen: G050 v9, G050 h1 (call 17), G060 h1 (call 22) en G060 h2 (call 46) worden review. Zie `../bronfuncties-v1/uitvoeringsverslag-claude-v4.md`.
