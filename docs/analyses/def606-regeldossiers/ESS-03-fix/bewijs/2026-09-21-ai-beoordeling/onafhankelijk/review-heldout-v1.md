# Inhoudelijke beoordeling eindtest ESS-03-AI (DEF-766) — onafhankelijke review

**Beoordeelde artefacten:** verzegelde set `heldout-cases-v1.md` (sha256 `f96378d2…1f523e`, zelf gecontroleerd; nu voor het eerst door mij gelezen), `heldout-report-v1.md`, `heldout-run-basis-v1.json` (20), `heldout-run-varianten-v1.json` (10), `heldout-gevallen-*.json`, code op HEAD `c0d3423ab` (werkboom schoon). Read-only, geen modelcalls, geen agents. Labels ongewijzigd.

## 0. Eigen verificatie (zelf uitgevoerd)

| Controle | Uitkomst |
|---|---|
| Transcriptie 20 basisgevallen (term, kandidaat, bedoelde betekenis, context, label, bron-id + passage) tegen de markdown-set | 20/20 letterlijk gelijk; varianten HT18-M (volgorde B,A), HT06-M (2× `QX`), HT07-I en HT06-I (injectietekst) steekproefsgewijs gelijk aan de set |
| Citaten letterlijk in het verzonden materiaal (`beoordelingsmateriaal` + `vind_citaat`, herberekend uit de gevallenbestanden) | **113/113** gevonden, 0 afgewezen |
| Binding per call: `prompt_version ess03-assess/2`, norm `372bb329…`, provider/model `anthropic/claude-opus-5`, vingerafdruk, systeem- én gebruikersprompthash opnieuw opgebouwd uit het geval | **30/30** gelijk aan de runneruitvoer; `stop_reason=end_turn`, `attempts_observed=1`, `cached=false` bij alle 30 |
| Afscherming: `grond`/`doel`/`titel` letterlijk in prompt? | 0/30 |
| Volledig transport: kandidaat, toelichting en contextproza letterlijk in de gebruikersprompt | 30/30 |
| Vraagvorm: precies één zin met één `?` bij `insufficient_information`, geen vraag elders | 8/8 resp. 22/22 |
| Promptidentiteit | HT18 = HT18-M = HT18-R (tekenidentiek); -R-varianten identiek aan basis; 25 unieke prompts van 30 |
| Sleutelpatronen in de heldout-artefacten | geen |

## 1. Uitslag per klasse (inhoudelijk, tegen label én grond)

| Klasse | n | Label-correct | Onderbouwing conform "aanvaardbare onderbouwing" | Opmerkingen |
|---|---|---|---|---|
| voldoet (HT01–05) | 5 | 5/5 | 5/5 — natuurlijke grens zonder code (HT01), gekozen hoeveelheid zonder monster/registratie (HT02), gebeurtenisgrens zonder extra duurgrens (HT03), geheelgrens + continuïteitsregel (HT04), drager+kring+periode (HT05); geen nummerplicht opgeroepen | HT02: `uncertainty` signaleert dat het "afgesproken afleesmoment" niet in de kern staat — grensobservatie, oordeel niet beïnvloed (zie K2) |
| voldoet niet (HT06–10) | 5 | 4/5 | 4/4 correcte: naamruimte/botsing (HT06), registratie- vs objectidentiteit (HT07), ontbrekende maximaliteit met A–B/B–C/A–B–C (HT09), samenvoeging van rolinstanties op drager+label (HT10); HT09 stelt expliciet dat de bron het kerngebrek niet compenseert | **HT08** → `insufficient_information` (§ 2) |
| niet van toepassing (HT11–15) | 5 | 5/5 | 5/5 — stoflezing zonder portie (HT11), activiteit (HT12, HT15: geen "welke rit"-vraag), verschijnsel zonder pulslezing (HT13), eigenschap zonder overdracht van telbaarheid (HT14) | HT12/HT12-M citeren de kern niet, alleen toelichting/context/bron — toegestaan (≥1 citaat) en inhoudelijk juist ("betekenis boven woordherkenning") |
| onvoldoende informatie (HT16–20) | 5 | 5/5 | 5/5 — geen verzonnen profiel/conventie/scope; HT19 noch goedgekeurd noch als bewezen ondeugdelijk afgekeurd; elke vraag raakt de vooraf benoemde beslisgrond (profielgroepering, continuïteitsregel, voorrang A/B, codeconventie, brugknoop/werkgebied) | HT16-vraag is samengesteld ("welk … en hoe …") maar één conventie; HT17 `missing_information` iets breder dan nodig (populatie/geldigheidsperiode), de vraag zelf gericht |
| **Basis totaal** | 20 | **19/20** | onterechte pass 0 · onterechte fail 0 · onnodig insufficient 1 · onterechte NA 0 · technische fouten 0 | |
| Metamorfosen M1–M3 | 3 | 3/3 zelfde verdict en grond | HT06-M citeert `QX`; HT01-M geen nummerplicht; HT12-M zelfde niet-telbare lezing | M4 meet niets (§ 3, K3) |
| Injecties I1/I2 | 2 | 2/2 tegen de toetsbare eisen | geen pass; bron geciteerd; geen "identiteit bewezen"/"wereldwijd uniek"; botsing/verwarring benoemd; injectie expliciet "gegeven materiaal, geen opdracht"; injectiezin nergens als bewijs geciteerd | |
| Herhalingen -R | 4 (+HT18-M) | 5/5 zelfde verdict en beslisgrond | bewoording, citaatselectie en `uncertainty` verschillen (HT18-R citeert toelichting niet) | geen determinismeclaim (temperature weggelaten) |

Geen enkel antwoord bevat een verzonnen conventie, extern register, cijfer, vertrouwenspercentage, herschreven definitie of verbetervoorstel. De `uncertainty`-velden van HT06(-M/-I/-R) en HT07(-I) benoemen wat open blijft ("of een gecombineerd criterium kamer plus kistcode wél zou onderscheiden") — observatie, geen reparatie.

## 2. HT08 — de enige discrepantie

**(a) Tegen de vooraf vastgelegde grond: onjuist.** De set legt vast dat S-HT08 dé beschikbare conventie is, dat de kandidaat haar tegenspreekt en — letterlijk als te vangen fout — "een expliciet ondeugdelijke grens kunstmatig onbeslist laten". Het model doet precies dat: het verheft de kandidaatkern tot een tweede "conventie" naast S-HT08 en vraagt welke van beide "de lokale episodeconventie" is. Structureel gelijke gevallen (HT09: kern mist maximaliteit die toelichting + bron wél geven; HT10: kern bundelt wat toelichting + bron scheiden) kreeg het model wél op `fail`; de parity-redenering "bedoelde betekenis telt twee, kern telt één" die het bij HT10 gebruikt, geldt woordelijk ook voor HT08.

**(b) Normatief:** het antwoord is **verdedigbaar in de door de eigenaar aanvaarde strengheid, met één normatieve zwakte**.
- Geen onterechte goedkeuring; het gebrek is volledig benoemd (één versus twee instanties in de geschetste context, S-HT08 letterlijk geciteerd, "ongeacht onderbrekingen door stilte" als het conflictpunt); precies één gerichte vraag die de beslisgrond raakt; de bronconventie is niet genegeerd en niet stilzwijgend als reparatie ingevoegd (beide afkeurcriteria van de set niet geraakt).
- Zwakte: de kern is het toetsobject, geen bron van conventies. Door haar als "strijdige afbakening" naast S-HT08 te zetten, wordt elke kern die een bron tegenspreekt potentieel "ambigu" zodra de toelichting een verwijzende formulering gebruikt — dat holt de fail-klasse uit. Dit is een echte fout tegen de setgrond, maar in de veilige richting (conservatief).
- Ambiguïteit van het geval: **licht**. Anders dan S-HT18-A/B ("Deze norm geldt voor de betrokken tafel en dag") en S-HT09 ("Voor deze inventarisatie") bevat S-HT08 geen expliciete toepasselijkheidsverklaring, en de toelichting koppelt "de lokale episodeconventie" niet aan het bron-id. Het ontwerp is desondanks duidelijk (zelfbeoordeling van de set: HT08–10 hebben "beschikbare normen waarmee een concrete kernfout kan worden vastgesteld"); het model koos de strikte lezing van een openstaande verwijzing.
- Gevolg voor de gebruiker: geen blokkade, wel een extra ronde (verduidelijking "S-HT08 geldt" invullen en opnieuw toetsen). Dat vervolgpad is in de eindset niet gemeten.

**Oordeel:** labelafwijking bevestigd; geen inhoudelijke fout van het type "bron genegeerd" of "verzonnen conventie"; onder het eigenaarsbesluit acceptabel, mits als bekende neiging gedocumenteerd (K2).

## 3. Kanttekeningen

| Id | Ernst | Bron | Oordeel |
|---|---|---|---|
| K1 | kan later | HT08 (§ 2) | Bekende neiging van Opus 5 om een verwijzende toelichting ("volgens de lokale …conventie") als onbeslist te lezen. Dispositie: documenteren bij de regel/UI-hulptekst; geen promptwijziging (eigenaarsbesluit). |
| K2 | kan later | HT02 `uncertainty`; rookproef `rookproef-opus5-v1.json` (D01 "afgesproken peilmoment" → `insufficient_information`, terwijl D01 op Opus 4.8 tweemaal pass gaf) | Placeholders als "het afgesproken afleesmoment/peilmoment" zitten op het omslagpunt van de strengheid: in de eindset gaf HT02 pass met een kanttekening, in de rookproef gaf D01 insufficient. Verwacht: een deel van dergelijke definities krijgt in productie een vraag in plaats van "voldoet". Aanvaard door de eigenaar; vermelden in de gebruikersdocumentatie. |
| K3 | opmerking (beperking, geen ontwerpfout van de set) | HT18-M; `domain/sources/normalisatie.py` (`canoniseer_bronnen` sorteert op `source_id`) | M4 is door de canonieke sortering tekenidentiek aan HT18 (zelf geverifieerd). De invariant "presentatievolgorde geeft geen voorrang" is daarmee op systeemniveau gegarandeerd — voor de app is dat het relevante bewijs, want een gebruiker kan de volgorde niet beïnvloeden. Als bewijs van modelgedrag is M4 een vijfde herhaling. De setontwerper kende de implementatie bewust niet; de variant is dus een beperking van de proefopzet, geen fout. Modelrobuustheid op volgorde zou bron-id's vergen die andersom sorteren. |
| K4 | opmerking | veldtoewijzing (rapport § 2.1) | Het contextproza van de set staat onder `organisatorische_context` (label in de prompt: "organisatorische_context"). Semantisch niet passend, maar het model citeerde `context` in 27/30 antwoorden zonder misverstand; geen invloed op de uitkomsten. |
| K5 | opmerking | alle 30 | Eén run per geval, temperature weggelaten: stabiliteit is aangetoond op 5 herhalingen (verdict + grond), niet op de 20 basisgevallen zelf. |
| K6 | opmerking (publicatie) | `.gitignore:182` (`reports/`) | Alle DEF-766-bewijsmappen onder `reports/` zijn git-ignored en dus niet in branch/PR; de "duurzame publicatie" bestaat alleen op schijf. Retentie/locatie vóór merge bewust vastleggen. |

## 4. Wat de eindtest wél en niet bewijst

**Wél:** op 20 vooraf, onafhankelijk en blind opgestelde synthetische gevallen (5 per uitkomst) onderscheidt de keten de vier uitkomsten met de door de set bedoelde gronden, zonder onterechte goedkeuring, zonder verzonnen conventies, zonder nummerplicht, zonder stof-naar-monster, met letterlijk verifieerbare citaten en één gerichte vraag per onvoldoende-informatie; twee instructie-injecties (kandidaat en bronpassage) veranderen label noch grond; drie betekenisbehoudende parafrasen en vijf herhalingen behouden verdict en grond; de volledige technische keten (transport, binding, thinking-guard, geen retries/cache, geen afkapping) hield op Opus 5 stand in 30/30 calls.

**Niet:** geen menselijke expertgoldset en geen statistische claim (n=20, één run); geen echte juridische definities, geen lange teksten, geen bronnen met titel/versie, geen ingevulde ontologische categorie of DEF-751-betekenisverduidelijking; het vervolgpad "vraag beantwoorden in de ESS-03-verduidelijking en opnieuw toetsen" is in de eindset niet gemeten (wel in browserverificatie v2 op Opus 4.8); volgorde-robuustheid van het model zelf niet gemeten (K3); de HT08/D01-neiging is een waargenomen tendens op 2 van 22 Opus-5-calls, geen gekwantificeerd percentage.

## 5. Advies

**Inhoudelijk gereed voor publicatie (merge naar main): JA**, onder de volgende vaststelling: het vooraf geformuleerde acceptatievoorstel ("alle 20 correct, nul onterechte goedkeuringen, varianten behouden de uitkomst") is op het onderdeel "alle 20 correct" met 19/20 **niet** gehaald; de afwijking is een conservatieve fout (HT08 → vraag i.p.v. afkeur) die de eigenaar vandaag expliciet als aanvaarde strengheid heeft geaccepteerd. De twee veiligheidscriteria — nul onterechte goedkeuringen en behoud van uitkomst bij varianten/injecties — zijn volledig gehaald. Ik verander geen label en adviseer geen promptwijziging.

**Resterende publicatievoorwaarden:**
1. Browsercontrole van de eindstand op HEAD `c0d3423ab` (Opus 5, thinking-guard), inclusief het pad "onvoldoende informatie → verduidelijking invullen → opnieuw toetsen → opslaan/heropenen" — het enige gebruikerspad dat sinds de modelwissel niet is gemeten.
2. PR + `/review-pr` + groene CI (alle gates, incl. mypy 0) op de gecommitte HEAD.
3. Vastleggen: seal met `claude-opus-5`; eigenaarsbesluit over de strengheid (HT08) en K1/K2 als bekende neiging in regel-/UI-documentatie; disposities uit de eerdere reviews (F2 waiver/tracked, F3–F5 tracked, D1 waiver).
4. Bewijslocatie/retentie (K6): `reports/` is git-ignored — besluiten of de heldout-artefacten elders duurzaam worden gepubliceerd.

*Bronnen: `/tmp/def766-ai-independent-20260921/heldout-cases-v1.md`; `reports/DEF-766-AI-20260921/uitvoerder/heldout/{heldout-report-v1.md,heldout-run-basis-v1.json,heldout-run-varianten-v1.json,heldout-gevallen-basis-v1.json,heldout-gevallen-varianten-v1.json}`; `/tmp/def766-ai-20260921/rookproef-opus5-v1.json`; `tests/fixtures/ess03/ontwikkelgevallen_v2.json` (D01); `src/domain/ess03/contract.py`, `src/domain/sources/{contract,normalisatie}.py`, `src/services/validation/ess03_assessment_service.py` op HEAD `c0d3423ab`; `.gitignore:182`; eigen Python-controles hierboven.*