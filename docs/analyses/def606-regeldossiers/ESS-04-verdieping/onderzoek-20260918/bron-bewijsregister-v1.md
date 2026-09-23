# ESS-04 — bron- en bewijsregister v1

18 september 2026. Alleen ESS-04 actief; centraal [DEF-767](https://linear.app/definitie-app/issue/DEF-767). F = bronfeit; B = geregistreerd besluit; W = waarneming; I = interpretatie; V = voorstel. Registraties van levering zijn geen eigen uitvoeringsbewijs.

## Code- en bewijsbinding

Eigen werk-HEAD **50d0770ded6f4e8337738126d6bc2aa8f169e3de**, detached, schoon bij start; bron van 21 augustus 2026. Historische dossiers: **d68a98a909630e15db6e1cb9c9c8171f957bff9d**, 11 september. Actuele aanvullende lees-/proefbasis: **4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb**, lokale origin/main op 18 september 15:27:24 +0200 (PR464). Deze ref veranderde tijdens onderzoek; alleen de genoemde bevroren commit is bewijsbasis. Geen claim over later main of de draaiende gebruikersapp.

Via `git archive <commit> src config` in de eigen worktree zijn uitsluitend code/config als nieuwe onderzoekskopie bewaard: [manifest](codebasis-actueel-v1.json), [archive](codebasis-4cdb8ea43.tar), map `codebasis-4cdb8ea43/`. Geen checkout, productbestandwijziging of databasekopie. Alle actuele codeverwijzingen hieronder zijn ten opzichte van deze snapshot.

## Bronnen

| ID | Bron / versie / toegang | Soort, bereik en beperking |
|---|---|---|
| S01 | [historisch ESS-04-dossier](feitenbasis/historisch/docs/analyses/def606-regeldossiers/ESS-04-v1.md), 11-09, SHA in bestandenregister | Onderzoeksinterpretatie, geen nieuwe normbeslissing; zeven scenario's en 14 service-uitkomsten |
| S02 | [historische cases en uitkomsten](feitenbasis/historisch/docs/analyses/def606-regeldossiers/ESS-04-bewijs-v1/uitkomsten.json) | W historisch. Recordhash `78537a76…389c` gelijk op alle drie codebasissen. Geen UI of menselijke review bewezen |
| S03 | [historische Claude-review](feitenbasis/historisch/docs/analyses/def606-regeldossiers/ESS-04-bewijs-v1/claude-review.json) | Historisch advies zonder externe bronnen. Geen onafhankelijke nieuwe Cowork-bijdrage. De onjuiste ‘65 uur’ wordt niet hergebruikt |
| S04 | [plan v4](feitenbasis/historisch/docs/plans/2026-09-11-def606-analyseplan-v4.md), overzicht, samenhang en productonderzoek in dezelfde feitenbasis | Onderzoekskader; oude context-/adapterbevindingen niet automatisch actueel |
| B01 | [geen totaalscore, 15-09](feitenbasis/historisch/docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md) | Besloten door Chris; geen totaalcijfer, acceptatiegrond of hersteldriver. Vervangt ‘tijdelijk’. Geen automatische wijziging individuele policy |
| B02 | [DEF-767](bronnen/linear-DEF-767-20260918.json), [DEF-606](bronnen/linear-DEF-606-20260918.json) + comments | Actueel opgehaald 18-09. ESS-04 Backlog, onderzoek/uitvoering/besluit gescheiden; gedeelde owners blijven |
| B03 | [CON-01 / DEF-622](bronnen/linear-DEF-622-20260918.json) | Done + expliciete inhoudelijke acceptatie 17-09. Naamfunctie, context, identiteit en blokkade behouden |
| B04 | [CON-02 / DEF-743](bronnen/linear-DEF-743-20260918.json) | In Progress. Bronbasis/betekenissteun/verwijzing; AI-beoordeling toegestaan voor deze regel, geen algemene ESS-04-autorisatie; deskundige uitzonderingen blijven onderscheiden |
| B05 | [ESS-01 / DEF-745](bronnen/linear-DEF-745-20260918.json), [laatste comments](bronnen/comments-DEF-745-20260918.json) | Normbesluiten behouden: begripsbepalende functie mag; geen extra ESS-01-poort. Statusveld Done versus nieuwste comment ‘blijft open’ is registratieverschil; niet opgelost door ESS-04-onderzoek |
| B06 | [ESS-02 vastgestelde besluiten](bronnen/besluiten-ESS02-20260918.json), [DEF-749](bronnen/linear-DEF-749-20260918.json), DEF-750–754 + comments | Vijf productbesluiten blijven vast. Nieuwste DEF-751-comment registreert PR461-merge; oudere conceptstatus achterhaald. C/D/E-bewijsgrenzen niet op basis van A/B groen verklaren. DEF-752-specificatie is geen bewijs dat ESS-04 is aangesloten |
| B07 | [DEF-624](bronnen/linear-DEF-624-20260918.json), [DEF-630](bronnen/linear-DEF-630-20260918.json), [DEF-638](bronnen/linear-DEF-638-20260918.json) | Gedeeld resultaat, gate en herstel; expert + handmatige vaststelling, geen automatisch besloten tweede persoon. Maximaal één toekomstige gerichte repair; geen activatie hier |
| S05 | [ASTRA Toetsbaarheid](https://www.astraonline.nl/index.php/Toetsbaarheid), 18-09 | Directe web-open en raw-poging niet toegankelijk. Actuele originele normpassage/revisie NIET bevestigd. Lokaal record noemt ASTRA; exacte lokale operationalisering niet als letterlijk ASTRA-citaat gebruiken |
| S06 | [NL-SBB](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/), vastgesteld 10-10-2024, §2.4.1.1–2.4.1.2 | Primaire bron gelezen. Onderscheid termen, definitie, toelichting en voorbeelden. Geen ESS-04-procedurevoorschrift afleiden |
| S07 | [JCGM VIM3 §1.30](https://jcgm.bipm.org/vim/en/1.30.html) en [§2.1](https://jcgm.bipm.org/vim/en/2.1.html), gelezen 18-09 | Primaire terminologische bron: nominale eigenschappen versus metrologische meting. Ondersteunt onderscheid; geen zelfstandige juridische definitiesnorm |
| S08 | [kopieën vijf actieve skills + referenties](feitenbasis/bestanden-v1.json) | Werkelijk gelezen implementatie-instructies, geen normbewijs. Nederlandse definities/toetsregels/UFO bevatten ESS-01/02 en CON-correcties. Toetsregels bevat nog ‘voorlopig’ en cijfergerichte ESS-04; niet overschrijven met oudere kopieën |

Alle Linear-snapshots zijn volledige toolantwoorden, individueel opgehaald; geen issue of comment gewijzigd. Originele Mac-paden en SHA-256 van 36 historische/skillbestanden staan in `feitenbasis/bestanden-v1.json`. Geen volledige ISO-norm gelezen of conformiteit geclaimd.

## Bewijs en claims

| ID | Precieze claim | Bewijs / beperking |
|---|---|---|
| C01 (W) | ESS-04-regelrecord blijft judgment_review/excluded_from_score en bevat cijfergerichte uitleg | S02 + huidige `src/toetsregels/regels/ESS-04.json`; identieke SHA |
| C02 (W) | Nieuw signaal ‘toetsbaar’ en aangeleverd reviewer/pass-label blijven automatisch review_required | P01 op oude én actuele basis; evaluatorfunctie, geen reviewopslagproef |
| C03 (W) | Oude legacy-normalisatie verliest reviews; huidige normalisatie bewaart ze en markeert ontbrekende runstatus unknown | P02; modern/legacy beide expliciet. Oud defect niet opnieuw als actuele appfout melden |
| C04 (W) | ESS-04-generatiemapping geeft nog deadlines/aantallen/percentages als aanwijzing | P03 op beide basissen; modulefunctie, geen eindprompt/modelkwaliteit |
| C05 (W) | Geteste 80%-zin behoudt noemer, grens en peildatum na extractie en cleaning | P04 op beide basissen; geen opslag of algemene cleaninggarantie |
| C06 (F/I) | In gelezen actuele evaluator/UI is geen aangesloten ESS-04-beoordelingsschrijfroute aangetoond | judgment_review.py:53; expert_review_tab.py:604,745,1218,1601; validatieview:730. Aanwezige CON-review en algemene vaststelactie zijn geen ESS-04-oordeel. Afwezigheid van volledige keten blijft begrensde conclusie |
| C07 (F) | Actuele alleen-toetsen-orchestrator documenteert en implementeert behoud zonder cleaning | validation_orchestrator_v2.py:128,174,224. Oude transportbevinding niet als actuele meting gebruiken. Geen nieuwe UI-route uitgevoerd |
| C08 (V) | Kwalitatieve lidmaatschapscriteria en relevante bewijscontext verdienen voorrang boven cijferplicht | S01 + S06/S07 en casussen; eigen voorstel, Cowork/expertbeoordeling nog nodig |

P01–P04: [vooraf oude verwachtingen](proefverwachtingen-v1.md), [verwachtingsactualisatie](proefverwachtingen-actueel-v1.md), [oude resultaten](proefuitkomsten-v1.json), [actueel exact uitvoerlog](proef-actueel-uitvoer-v1.log), [actueel script](proef-actueel-v1.py). Python 3.13.15 uit bestaande venv; imports van actuele proef uitsluitend snapshot-src; PYTHONDONTWRITEBYTECODE=1. Eén eerste fixturefout (detailed_scores ontbrak) bewaard in proef-poging1-v1.log; gecorrigeerde versie exit 0. Geen dependencies toegevoegd.

De zeven historische gevallen × manager/cache zijn niet opnieuw gedraaid. Twee gerichte functiescenario's, een prompttransformatie en een cleaningproef zijn op twee versies uitgevoerd wegens concrete versieverschillen; geen brede suite of live modelcall. Geen daadwerkelijke twee menselijke beoordelaars, opslag/readback of app-UI-doorloop uitgevoerd.
