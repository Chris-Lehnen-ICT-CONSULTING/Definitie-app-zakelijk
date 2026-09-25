# DEF-768 — ESS-05: uitvoercontract, samenvoeging en WP7-runplan (v1)

23 september 2026 · uitvoerder Claude Code CLI · basis `26f2374d3` · branch
`feature/DEF-768-ess05-ai-beoordeling`. Hoort bij het goedgekeurde uitvoeringsplan
v2 (`docs/plans/2026-09-21-DEF-768-ESS-05-uitvoeringsplan-v2.md`, hoofdcheckout,
ongetrackt), besluiten K-1…K-10 en synthese v3 van 23 september. Dit document
legt het uitvoercontract vast vóór de implementatie en beschrijft het runplan
voor de later te autoriseren betaalde proeven. Geen modelcall uitgevoerd, geen
kwaliteitswinst geclaimd.

## 1. Waarom het uitvoercontract afwijkt van plan-§3

Plan-acceptatiecontract 3 vroeg per buur `satisfies_definition: true|false|unclear`
en voegde samen als "één bevestigde buur `true` → voldoet niet". Dat is een
extensievraag (kan een *geval* van de buur aan alle kenmerken voldoen?). K-3b
staat overlap van gevallen toe zolang het onderscheidende kenmerk kenbaar is;
synthese v3 en beide aanvullingen wijzen er onafhankelijk op dat de planregel
toegestane rol-overlap afkeurt:

- **ESS05-E05** — lener = persoon met een actuele lening; werknemer = persoon met
  een arbeidsovereenkomst. Eén persoon kan beide zijn: een werknemer *kan* aan
  "persoon met een actuele lening" voldoen, dus de planregel keurt af. Verwacht:
  **voldoet** (verschillende rolkenmerken).
- **ESS05-E06** — twee omschrijvingen die alleen "persoon die in het systeem is
  geregistreerd" zeggen. Verwacht: **voldoet niet**, met een eigen ESS-05-reden.

De vraag per buur wordt daarom een **kenmerkvraag**: drukt de kern in deze context
een onderbouwd verschil in kenmerken uit ten opzichte van de beschrijving van
de buur? Dat is de minimale wijziging die K-3b naleeft; er komt geen nieuw
ontologisch formalisme bij.

## 2. Modeluitvoer (gesloten; elke afwijking is een technische fout)

```json
{
  "lacks_differentia": false,
  "reason": "korte onderbouwing van het geheel",
  "neighbours": [
    {
      "neighbour_id": "id uit de verzonden burenlijst",
      "distinction": "distinguished | not_distinguished | unclear",
      "distinguishing_feature_quote": "letterlijk uit de definitiekern, of null",
      "missing_feature": "ontbrekend of te ruim kenmerk, of null",
      "reason": "onderbouwing voor deze buur",
      "uncertainty": "resterende onzekerheid, of null"
    }
  ],
  "proposed_neighbours": [
    {"term": "…", "source_id": "bron-id of null", "quote": "citaat of null", "reason": "…"}
  ],
  "question": "precies één vraag, of null"
}
```

| Veld | Herkomst | Motivering |
|---|---|---|
| `neighbour_id`, `reason`, `uncertainty` | plan-§3 | ongewijzigd |
| `distinction` | vervangt `satisfies_definition` | kenmerkvraag i.p.v. extensievraag (K-3b, E05/E06) |
| `distinguishing_feature_quote` | hernoemt `excluding_feature_quote` | het citaat bewijst een onderscheidend kenmerk, geen uitsluiting van gevallen |
| `missing_feature` | toegevoegd | plan-§3 eist bij 'voldoet niet' "buur + ontbrekend/te ruim kenmerk"; zo is dat door code afdwingbaar |
| `lacks_differentia` + top-level `reason` | toegevoegd | K-8: ESS-05 meldt zelf "kan zonder toespitsing geen enkel verwant begrip uitsluiten", naast STR-04, ook zonder buren |
| `proposed_neighbours` (`term`, `source_id`, `quote`, `reason`) | plan `voorgestelde_buren` | apart veld, nooit beoordeeld; elk voorstel is herkomst `model`, altijd onbevestigd (K-1); `source_id` + letterlijk citaat zijn een aparte bronverwijzing die mee gaat in voorstel, overnemen, opslag (`ess05_buren`) en editor, en maken het voorstel geen bronbuur (reviewcorrectie 23-09-2026) |
| `question` | plan `open_question` | ESS-03-naam; optioneel voor het model, de code kiest precies één vraag |
| top-level `status` | vervallen | de uitkomst is een codebeslissing (§4), geen modelclaim |

Codecontroles (fail-closed): exact deze velden en typen; elke verzonden buur precies
één keer, geen onbekende ID; `distinguished` ⇒ citaat, geen `missing_feature`;
`not_distinguished` ⇒ `missing_feature`, geen citaat; `unclear` ⇒ geen citaat;
buur zonder definitie ⇒ uitsluitend `unclear`; het citaat staat letterlijk in de
**definitiekern** (niet in toelichting of context) én niet letterlijk in de
beschrijving van de buur (een gedeelde passage onderscheidt niets — dit maakt E06
in code onmogelijk als 'voldoet'); een voorstel met `source_id` citeert letterlijk
uit die verzonden bronpassage; `question` is null of precies één vraag. Structuurfout
→ `malformed_response`; onverifieerbaar citaat → `unverifiable_evidence`; beide
`error`, nooit pass of afkeur, nooit gecachet. Een voorstel dat een bekende of
afgewezen buur of de term zelf noemt, wordt zichtbaar genegeerd (`rejected`).

## 3. Burenlijst

Transport en opslag: `[{id, term, definitie|null, herkomst, bevestigd}]`, herkomst
`gebruiker | bron | repository | model | ontologie` (`ontologie` gereserveerd, geen
leverancier; DEF-300). Opslag op het record (`generation_prompt_data.ess05_buren`)
voegt per buur `afgewezen`, `actor`, `at`, `grond` toe — nodig voor de expertacties
bevestigen/afwijzen (K-1) en de historie — en bij een overgenomen voorstel met
broncitaat de bronverwijzing `source_id` + `quote` (samen of geen van beide;
anders fail-closed geweigerd). Een buur met herkomst `bron` is een echte bronbuur,
nooit een modelvoorstel. Repository-buren komen bij elke toetsing
vers uit de database (actieve definities met exact dezelfde drie contextlijsten,
ander begrip, niet het record zelf), onbevestigd tenzij een opgeslagen besluit ze
bevestigt of afwijst. Gebruikersinvoer is bevestigd. Afgewezen buren gaan niet mee.

## 4. Samenvoeging (code)

1. Geen term of tekst, of geen context → `not_evaluated` met reden; geen modelcall (K-9).
2. Technische fout (dienst, transport, burenlijst, repository) → `error`.
3. Geen actieve buren én geldige deskundige bevestiging 'vergelijkingsruimte leeg'
   (met grond en actor; gebonden aan term, tekst, context, bedoelde betekenis,
   bronnen en de lege burenlijst) → `pass` 'leeg bevestigd'; geen modelcall (K-2).
4. `lacks_differentia` → `fail` met K-8-reden.
5. Een **bevestigde** buur `not_distinguished` → `fail` (buur + ontbrekend kenmerk).
6. Anders `review_required` met precies één vraag wanneer: een bevestigde buur
   `unclear` is; er een onbevestigde buur met herkomst `model`/`bron`/`ontologie`
   is of het model nieuwe buren voorstelt (K-1); een onbevestigde buur (repository)
   `not_distinguished`/`unclear` is; of er geen bevestigde buur is (K-2).
7. Anders (≥ 1 bevestigde buur, alle `distinguished`) → `pass`.

Alles `no_score`, prioriteit `midden`; een `fail` is een zichtbare, niet-blokkerende
bevinding (`warning`/`medium`, `advisory`). Geen automatische tekstwijziging.

## 5. WP7-runplan (niet uitgevoerd; wacht op budgetbesluit)

Budgetvoorstel binnen maximaal 60 echte calls (synthese v3, B-voorstel): 12
ontwikkelcalls (casusregister A-01/B-02, A-02/B-01, A-05, A-07, A-08, A-12, B-06,
B-07, B-08, A-16, B-09, A-23) + 20 T-eindcalls (onafhankelijk opgestelde, vooraf
gelabelde set) + 8 T-herhalingen (vier vooraf gekozen grensgevallen × 2) + 20
G-calls (5 invoeren × 2 varianten × 2 runs). Geen retries; mislukte calls tellen mee.

Bewijsformat per call (JSONL, `/tmp/def768-ai-<datum>/calls.jsonl`, daarna
publicatie door de coördinator onder `reports/DEF-768-AI-<datum>`): `case_id`,
`set` (ontwikkel/eind/herhaling/G), `variant`, commit-SHA, `prompt_version`,
`norm_sha256`, `prompt_sha256`, provider/model, invoer (kandidaat, term, context,
bedoelde betekenis, bronhashes, burenlijst), ruwe-antwoordhash, parseruitkomst,
per-buur-oordeel, samengevoegde status, getoonde reden/vraag, cache-vlag,
tokens/kosten, duur, fouttype. Rapportage per klasse: correct/onjuist, onterechte
goed-/afkeuring, onnodig open, gedrag bij modelvoorgestelde buren, E05/E06-overlap;
per geval verbeterd/gelijk/verslechterd/onbeslist t.o.v. de oude evaluator (offline).
Acceptatievoorstel: 20/20 juiste status met draagkrachtige reden, nul onterechte
goedkeuringen, geen betekenisverlies. Eindset pas vrijgeven na bevriezen van
prompt/config; bijstelling op de eindset vereist een nieuwe eindset. Een
gebruikersproef (4 deskundigen, 20 gevallen, tegengebalanceerd) is niet
geautoriseerd.
