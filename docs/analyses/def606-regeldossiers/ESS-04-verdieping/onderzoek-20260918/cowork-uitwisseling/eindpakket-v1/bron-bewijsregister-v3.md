# ESS-04 — bron- en bewijsregister v3

18 september 2026. Dit register actualiseert [v1](bron-bewijsregister-v1.md); historische bronnen, oorspronkelijke proefverwachtingen en hashes blijven daar bewaard. Codebasis vastgezet op `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`; oude `50d0770` alleen ter vergelijking. Niet opnieuw vaststellen wat inmiddels op een andere commit staat.

## Bronnen en geldigheid

| Bron | Status en begrenzing |
|---|---|
| S05 ASTRA [Toetsbaarheid](https://www.astraonline.nl/index.php/Toetsbaarheid) | Actuele pagina rechtstreeks gelezen door beide onderzoekers. Norm: **Een criterium als onderdeel van een definitie moet toetsbaar zijn.** Pagina vermeldt 11-02-2025 09:46 en biedt oldid8558. Geen rechtstreeks gelezen historische URL of oorspronkelijke Politie-norm. [Waarneming](astra-bronobservatie-v2.md). Het oude bewijsgat actuele pagina is gesloten. |
| ASTRA [ESS-03](https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar) | Beide onderzoekers gelezen. Bereik telbare zelfstandige naamwoorden; onafhankelijke deskundigen bij instanties onderscheiden/tellen. Codex-waarneming in [reviewverwerking](codex-reviewverwerking-v1.md). Geen automatische ESS-04-tweepersoonspoort. |
| S06 NL-SBB | Officiële vastgestelde versie 10-10-2024, §§2.4.1.1–2.4.1.2 gelezen; onderbouwt rollen van definitie en toelichting, geen verborgen aanvulling van toetsobject. [Bron](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/). |
| S07 VIM3 | §§1.30 en2.1 gelezen; nominale eigenschap versus grootheidsmeting, ondersteunend aan interpretatie kwalitatieve toetsbaarheid. Geen algemene ISO704/1087-conformiteitsclaim. [VIM](https://jcgm.bipm.org/vim/en/). |
| Besluit geen totaalscore | 15-09-2026, appbreed, niet tijdelijk. Bronkopie in feitenbasis en Linear-snapshots; herstel hoort bij DEF-624/630, geen nieuwe ESS-04-bevoegdheid. |
| DEF-630 | Vastgestelde roadmapcorrectie4 september: verplichte review_required-uitkomsten hebben versiegebonden menselijke beoordeling, ontbrekende vereiste review niet met alleen notitie opheffen. [Snapshot](bronnen/linear-DEF-630-20260918.json). Geen softwareoplevering. |
| Regelspecifieke besluiten | [DEF-745](bronnen/linear-DEF-745-20260918.json) en [ESS-02](bronnen/besluiten-ESS02-20260918.json): geen extra zelfstandig ESS-akkoord/poort; open/negatief blijft zichtbaar. CON-01/02 eigen voorwaarden en routes behouden. Geen toestemming ESS-04-AI-jury afleiden uit CON-02. |
| Skills en dossiers | 36 bevroren kopieën in [herkomstmanifest](feitenbasis/bestanden-v1.json). 22 actieve skillpaden onder `.agents/skills` opnieuw bestaand en hashgelijk: [verificatie](skillvindplaatsen-verificatie-v1.json). Onderzochte implementatietekst, geen zelfstandige normbron. |

## Claims en onderscheidend bewijs

| Claim | Bewijs | Wel/niet bewezen |
|---|---|---|
| C01 cijfergerichte uitleg/prompt | ESS-04-record, P03 daadwerkelijke mappingaanroep | Instructietekst bewezen, verzonnen modeloutput niet uitgevoerd. |
| C02 altijd menselijke review op onderzochte evaluator | P01 normale en vervalste callerreviewmetadata; nieuwe14-evaluatorproef | Beide metadata-varianten en14cases review_required/nullscore. Geen vertrouwde menselijke beoordeling uitgevoerd. |
| C03 huidige normalisatie bewaart reviewvelden | P02 oud/actueel | Huidige legacy/modern behouden review_required/rule_statuses/dekking; onbekende runstatus→validation_unknown, acceptablefalse. Geen volledige UI. |
| C03b categoriecijfers bij onbekende run | Bestaande actuele P02-log legacy_output, bevestigd bij review | Vier detailed_scores0.9 naast unknown/overall0; contractrisico. Geen nieuwe run nodig, geen gemeten weergave. Moderne fixture houdt leeg detailed_scores. |
| C04 één getalszin intact na cleaning | P04 actuele extractie+cleaning | Noemer/grens/peildatum in die ene fixture behouden. Geen opslagtest of algemeen behoudsbewijs. |
| C05 volledige ESS-04-signaalset | Additional_patterns geeft leeg voorESS04; huidige record15 | Vier %-patronen missen normale spatie/punt, twee tijdpatronen missen enkelvoud. Nieuwe14proef bevestigt replica en drie oorspronkelijke verwachtingmissers C05/C08/C11. Geen nieuwe patroonset getest. |
| C06 menselijke opslagroute | Gelezen schema/repository/UI/evaluator | Geen aangesloten versiegebonden ESS-04-reviewroute aangetoond. Geen universeel onmogelijkheidsbewijs uit kolomnamen; geen readbackproef. |
| C07 poort/export | Workflow `_evaluate_gate`, policyklasse én snapshot YAML | Gelezen gate kent geen algemene reviewstatuscheck. YAML allow_hard_override true; actieve overlay onbekend. Exportgate conditioneel. Geen nieuwe bypass-/vaststel-/exportproef. |
| C08 toekomstige scoreloze review | [Codeaddendum](codex-codeaanvulling-v1.md), onafhankelijk geverifieerd door Cowork | excluded_from_score voorkomt huidig reviewcijfer, maar toekomstig PASS/FAIL kan regelcijfer krijgen; no_score-koppeling vereist ontwerp/consumercontrole. ESS-02 draagt no_score en valt ook in juridisch: als ESS-02 in de interne regelset zit, blankt die categorie ná middeling. Dit maskeert een hypothetisch ESS-04-regelcijfer incidenteel; rule_scores zelf blijft dan cijfers dragen. Geen onvoorwaardelijk zichtbaar categorie-lek. |

## Uitvoering en provenance

- [Actuele P01–P04-uitvoer](proef-actueel-uitvoer-v1.log), [script](proef-actueel-v1.py), Python3.13.15, exit0. Oude scriptv1 fixturefout behouden; gecorrigeerde fixture en actuele run apart. Geen claim dat de eerste mislukte run slaagde.
- [Cowork-replica](cowork-uitwisseling/cowork-bewijs-v1/uitkomsten-v1.json), Python3.10.12,14cases, status in replica ingevuld; signalen berekend, geen appimport. [Ontvangsthashes](cowork-proefbestanden-ontvangst-v1.json).
- [Nieuwe echte evaluatorproef](reviewproef-uitvoer-v1.json), [voorafverwachting](reviewproef-verwachting-v1.md), [script](reviewproef-v1.py), Python3.13.15, exit0; [uitvoerbinding](cowork-uitwisseling/reviewproef/uitvoerbinding-v1.json). Exact14 ongewijzigde Cowork-teksten,14identieke signalen, nullscores. Aanvulling uitgevoerd wegens concreet ontbrekend additional_patterns-/replicabewijs.
- Volledig archive/src+config lokaal bij Codex; Cowork controleerde hashgebonden selectie33, naleveringen3+4+1 en19 reviewbestanden. Niet claimen dat Cowork het hele archive controleerde.
- Geen live modelcall, DB-/productiedata, appmutatie of brede suite. Alle37 inhoudelijke scenario’s zijn synthetisch; geen deskundige goldset of juridische praktijkvalidatie.

## Nog nodig vóór implementatieacceptatie

Echte menselijke review met actor-/versiebinding opslaan, herladen, wijzigen en stale maken; alle relevante G/T/import/edit/concept/vaststel/exportingangen; fout-/lege-/conflict-/ongeautoriseerde actorgevallen; volledige eindprompt en verduidelijkingsroute; gecalibreerde signalen en deskundige verwachtingslabels. Dit zijn expliciete vervolgproeven, geen verborgen voorwaarde voor het afronden van het onderzoek.


## C09 — weergave en resterende heuristische teksten

Statisch gecontroleerd op de bevroren commit: validation_view.py:730–739 toont de open reden direct alleen voor ESS-01/02. judgment_review.py heeft voor die twee _reden_met_passages, ESS-04 krijgt nog de kale toetsvraag. validation_renderer.py:353 bevat nog een heuristische passverklaring voor ESS-04; modular_validation_service.py:1938 een numerieke testable-herstelhint. De onderzochte automatische route produceert geen ESS-04-pass/violation: terugvalrisico en concrete aanhechtingspunten, geen gemeten foutieve UI-pass. Zie instructievoorstellen-v5.md voor de exacte voorgestelde aansluiting en teksten. Geen UI-proef uitgevoerd.
