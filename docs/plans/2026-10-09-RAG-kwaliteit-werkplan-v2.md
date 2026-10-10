# Werkplan RAG-kwaliteit bronbibliotheek — v2 — TER GOEDKEURING

9 oktober 2026 · opgesteld door Cowork · vervangt v1 na de besluiten van Chris op 9 oktober (§2) · nog niet goedgekeurd, nog niet gestart.

**Doel:** de bronbibliotheek levert voor een begrip de juiste, geldende en gezaghebbende passages, en we kunnen aantonen dat die passages de definitie beter maken. Dit plan ordent de bevindingen van de RAG-meting van 9 oktober langs de bestaande Linear-lijnen (DEF-613, DEF-368, DEF-614, DEF-612). Het plan voegt geen parallelle backlog toe: waar een issue al bestaat, worden acceptatiecriteria aangevuld.

**Bewijs:** `docs/analyses/2026-10-09-rag-meting/` (`meet-v1.py`, `resultaat-v1.json`): 19 zoekvragen op een kopie van `data/bronnen.db` (22 collecties: 21 regelingen plus de lege uploadcollectie; 6.160 fragmenten) via de echte `RAGService._zoek_hybride`. Overlap met het volledige onderzoek van 7 oktober (E-001…E-005, H-007, J003, K006, R-001; pakket P5) staat hieronder per stap vermeld en wordt niet opnieuw onderzocht.

## 1. Uitgangspunt — bevindingen 9 oktober

| # | Bevinding | Bewijs (resultaat-v1.json) | Bestaand issue |
|---|---|---|---|
| F1 | De gekozen context stuurt de bronselectie niet: de contextkeuze "wettelijke basis" en de collectiekiezer (standaard: alle) zijn losse lijsten; daardoor huidig en toekomstig Sv gemengd | "voorlopige hechtenis": 5/5 uit nieuw Sv; "verdachte", "inbeslagneming": geldend en nieuw door elkaar | DEF-631 |
| F2 | Rechtsgebied is één label per collectie en een hard filter: rechtsgebiedoverstijgende regelgeving valt weg | "persoonsgegevens" + bestuursrecht → UAVG/Brp, AVG art. 4 ontbreekt (AVG = `europees_recht`) | DEF-631, R-001, E-004 |
| F3 | `RAG_MIN_SCORE=0.3` filtert achter de poort niets | laagste top-5-score 0,346 over 95 fragmenten | — |
| F4 | Geen spreiding: één artikel vult 4–5 van de 5 plekken | politiegegeven, eIDAS, AVG 4, Pbw 1 | — |
| F5 | Rangorde rust op cosine van één los woord; geen voorrang voor de begripsbepaling van precies dit begrip; geen rerank | 1.003 kandidaten bij "verdachte"; "dagvaarding" mist kernartikelen 258/260 | DEF-614 |
| F6 | Definities in lopende tekst ("Onder besluit wordt verstaan") niet als begripsbepaling herkend | Awb 1:1, 1:3 als `artikel` | — |
| F7 | Prompt kapt lange fragmenten vanaf het begin af (600 tokens) | 421 fragmenten > 600 tokens; tot 36 kandidaten per begrip met begrip ná de knip; in de gemeten top 5 geen geval | DEF-632 |
| F8 | Poort herkent alleen het begrip (+ -ing-vormen); geen synoniemen/afkortingen | bewuste keuze (orchestrator-commentaar DEF-620) | DEF-841 (afkortingen) |
| F9 | Meting te smal: kleine, zelfgekozen meetset; lexicaal orakel; geen meting op eindresultaat | `tests/fixtures/rag_meting/*` | DEF-368 (633–635), DEF-612 |
| F10 | Corpus beperkt tot 21 regelingen; geen MvT/Kamerstukken/jurisprudentie | geen collecties van het type Kamerstukken of beleid | DEF-368 corpusgate |

Wat goed is en zo blijft: artikelgewijze chunks uit officiële XML met structuurkopregel, aparte begripsbepalingen, versie/URL/sha256 per collectie, poort + semantische rangorde, bronnen als data in de prompt, kwitantie (DEF-743), brute-force NumPy op deze schaal.

## 2. Besluiten van Chris (9 oktober)

**B1 — Bronselectie volgt de gekozen context (vervangt het peildatum-advies uit v1).** De gekozen wettelijke basis bepaalt uit welke regelingen de bronbibliotheek put. Kies je het nieuwe WvSv, dan komen alle fragmenten uit het nieuwe WvSv; kies je WvSv én nieuw WvSv, dan uit beide. Geen afzonderlijk peildatumfilter.

**B2 — Matrix van regelgeving × rechtsgebied.** Regelgeving kan rechtsgebiedoverstijgend zijn of voor meerdere rechtsgebieden gelden. Chris beheert daarom één matrix: welke regelingen als wettelijke basis kiesbaar zijn, bij welke rechtsgebieden ze horen, en welke combinaties fout zijn.

**B3 — Goldset: nu overslaan.** Geen goldset van 50 vragen in deze ronde (uitleg in §2a). Gevolg: fase 1 is uitgesteld; rangordewijzigingen (fase 3) worden alleen indicatief gemeten op de bestaande kleine meetsets, aangevuld met de faalgevallen van 9 oktober.

**B4 — Prompt builder.** Een Linear-issue dat een wijziging aan de prompt builder vraagt, geldt als het in CLAUDE.md bedoelde overleg. DEF-632 (venster rond de vindplaats) mag dus.

### 2a. Wat met "goldset" bedoeld wordt (B3)

Een goldset is de antwoordsleutel voor het zoeken: een vaste lijst zoekvragen (begrip + gekozen context) met per vraag welke passages uit de bronbibliotheek de juiste zijn, en welke verleidelijk-maar-fout (bijvoorbeeld hetzelfde woord in een andere betekenis, of de verkeerde wetsversie). Met die sleutel meet je objectief of een wijziging het zoeken beter of slechter maakt, in plaats van op een handvol voorbeelden. DEF-368/634 vraagt 50 vragen voor één afgebakend strafrechtelijk corpus; de huidige meetsets in `tests/fixtures/rag_meting/` zijn een kleine voorloper.

Wat de sleutel inhoudelijk vraagt, is juridisch oordeel: welke passage is gezaghebbend voor dit begrip in deze context. Daarom labelt Chris. Als de goldset later alsnog komt: Cowork stelt per vraag een concept-label op (kandidaat-passages met motivering), Chris bevestigt of corrigeert. Met B1/B2 hoort bij elke vraag ook de gekozen context (wettelijke basis en rechtsgebied), zodat de sleutel de nieuwe bronselectie meet.

### 2b. Uitwerking B1/B2

| Vraag | Besluit / voorstel |
|---|---|
| V1 Geen wettelijke basis gekozen | **Besloten:** rechtsgebied kiest via de matrix de regelingen; ook geen rechtsgebied: alle regelingen, en de bronweergave zegt dat. |
| V2 Gekozen regeling staat niet in de bibliotheek (nu: Rv, Vreemdelingenwet, WID, EVRM, "Uitvoeringswet EU-richtlijnen", of een vrije "Anders…"-invoer) | Voorstel: geen terugval naar andere regelingen (DEF-631): de generatie meldt dat er voor die regeling geen bibliotheekbronnen zijn. |
| V3 Foute combinatie (regeling past niet bij gekozen rechtsgebied) | **Besloten:** waarschuwen in de contextkiezer; niet blokkeren. |
| V4 De aparte collectiekiezer boven "Genereer" | **Besloten:** vervalt voor generatie (de context stuurt); blijft in RAG-beheer voor testen. |
| V5 Geüploade documenten (collectie `user_documents`) | Voorstel: altijd meenemen als eigen bron van de gebruiker, los van de matrix. |

## 3. Fasen en volgorde

Fase 2 heeft geen goldset nodig en kan starten (V2 en V5 volgen het voorstel tenzij Chris anders beslist). Fase 3 meet zonder goldset alleen indicatief: dezelfde kleine meetset vóór en na elke stap.

```
Fase 2 contextgestuurde bronselectie (matrix) ─> Fase 3 selectie & rangorde (indicatief gemeten) ─> Fase 4 prompt ─> Fase 5 eindresultaat
                                                                                                                       └─> Fase 6 corpus
Fase 1 meetfundament (goldset): uitgesteld (B3)
```

### Fase 0 — Vastleggen (0,5 dag)

- Dit plan en de meting van 9 oktober op een docs-branch committen; Linear bijwerken (zie §5).
- **Klaar als:** plan goedgekeurd, besluiten B1–B4 genoteerd, issues aangevuld.

### Fase 1 — Meetfundament (DEF-368: 633 → 634 → 635) · UITGESTELD (B3)

Blijft beschreven voor het moment dat de goldset alsnog komt. In deze ronde vervangen door een kleine regressiemeetset: `tests/fixtures/rag_meting/fase3_begrippen.json` aangevuld met de faalgevallen van 9 oktober (voorlopige hechtenis / verdachte / inbeslagneming per Sv-context, persoonsgegevens met bestuursrecht, dagvaarding, onttrekking), elk met gekozen context. Zelf gekozen verwachtingen, dus indicatief en met overfittingrisico; geen bewijs van algemene winst. Omvang: 1 dag.

Oorspronkelijke opzet:


1. **DEF-633 schema en metrics.** Offline, deterministisch: Recall@5/10, MRR@10, nDCG@10, context precision, filterviolations. Daarbij, als aanvulling uit deze meting: *contextschending* (passage uit een regeling buiten de gekozen context), *gezagsmisser* (gelabelde gezaghebbende passage niet in top 5) en *spreiding* (max. fragmenten per artikel in top 5). Bewezen op handberekende fixtures.
2. **DEF-634 labels.** 50 querys met gekozen context (wettelijke basis, rechtsgebied), canonical passage-ID, bronversie, relevante passages en hard negatives; concept-labels door Cowork, oordeel door Chris (§2a). Verplicht opnemen: voorlopige hechtenis / verdachte / inbeslagneming (geldend vs. nieuw Sv), persoonsgegevens met bestuursrecht (AVG 4), dagvaarding (258/260), plus homoniem "onttrekking" (TC-RAG-04).
3. **DEF-635 baseline.** Huidige pijplijn (poort + cosine + drempel) als nulmeting, bevroren met corpus-, chunk- en confighash. `meet-v1.py` dient als vertrekpunt; omzetten naar `scripts/rag_meting.py`-uitbreiding.
- **Klaar als:** baseline-rapport per corpus/rechtsgebied/querytype, zonder LLM-call reproduceerbaar.

### Fase 2 — Contextgestuurde bronselectie via de matrix (DEF-613 / DEF-631) · 4–7 dagen

**Huidige stand (9 oktober).** De contextkiezer biedt 13 regelingen als wettelijke basis (`WET_OPTIONS` in `enhanced_context_manager_selector.py`); de bibliotheek heeft 21 regelingen (`config/bronnenlijst.yaml`), elk met één rechtsgebied. De lijsten zijn niet gekoppeld: 8 regelingen staan in beide (naamgeving wijkt deels af, bv. "Wet op de politiegegevens" / "Wet politiegegevens"; "Burgerlijk Wetboek" / Boek 1 en 2), 5 zijn kiesbaar zonder bibliotheekbron, 12 staan in de bibliotheek maar zijn niet kiesbaar. De orchestrator geeft `wettelijke_basis` aan prompt en weblookup, niet aan de bronbibliotheek; die filtert alleen op `juridische_context[0]`.

**2a Regelingenregister (de matrix) — DEF-846.** Eén bestand als enige bron, bij voorkeur een uitbreiding van `config/bronnenlijst.yaml`: per regeling een sleutel, het label in de contextkiezer, de collectie(s) en versie, en `rechtsgebieden` (lijst; rechtsgebiedoverstijgend expliciet). Kiesbare regelingen zonder bibliotheekbron staan er ook in, gemarkeerd als "geen bibliotheekbron". `WET_OPTIONS` wordt uit het register afgeleid. Chris beheert de inhoud; Cowork levert een eerste invulling uit de huidige twee lijsten ter controle.
- Tests eerst rood: register en contextkiezer tonen dezelfde regelingen; elke collectie hoort bij precies één registerregel; een regeling zonder rechtsgebied of met onbekend rechtsgebied faalt de laadcontrole.

**2b Bronselectie volgt de context (B1, V1, V2, V5).** Gekozen wettelijke basis → collecties uit het register; geen wettelijke basis → regelingen van het gekozen rechtsgebied (V1); regeling zonder bibliotheekbron → verklaarde lege toestand (V2); uploads apart (V5). Geen stille verruiming (DEF-631, E-004). De collectiekiezer bij generatie vervalt (V4).
- Tests eerst rood: context nieuw WvSv + "voorlopige hechtenis" → uitsluitend fragmenten uit nieuw WvSv; WvSv én nieuw WvSv → beide toegestaan, niets daarbuiten; context bestuursrecht zonder wettelijke basis + "persoonsgegevens" → AVG art. 4 bij de kandidaten (AVG in het register ook onder bestuursrecht); "Vreemdelingenwet" → lege toestand met melding.

**2c Foute combinaties (B2, V3).** De contextkiezer controleert gekozen regelingen tegen gekozen rechtsgebieden volgens het register en waarschuwt bij een combinatie die er niet in staat. Sluit aan op R-001 (contextmatch verwart rechtsgebieden).

- **Werkwijze (risico middel):** featurebranch per issue in een eigen worktree, TDD, `make test` + `make lint`, één onafhankelijke review (Codex), Chris merget. UI-wijzigingen via `SessionStateManager` en key-only widgets.

### Fase 3 — Selectie en rangorde · 4–8 dagen · na fase 2

Elke stap wordt vóór en na gemeten op de regressiemeetset (fase 1, vervanging); een stap die daar iets verslechtert gaat niet mee. Omdat er geen goldset is, is dat een indicatie, geen bewijs.

- **3a Begripsbepalingen in lopende tekst herkennen (F6).** Parsers (BWB, officiële publicatie, EU) herkennen "Onder X wordt verstaan", "In deze wet wordt verstaan onder", "Als X wordt aangemerkt". Herindexeren van de geraakte collecties via de bestaande vervang-/verhuisscripts (embeddingkosten: enkele dollars of minder; vooraf ramen).
- **3b Voorrang voor de begripsbepaling van precies dit begrip (F5).** Structurele voorrang vóór de cosine-rangorde; meerdere wetten → elk één begripsbepaling, geordend volgens de bronrangorde (DEF-844).
- **3c Spreiding (F4).** Maximaal 1–2 fragmenten per artikel in de top 5; overige plekken naar andere artikelen/wetten.
- **3d Drempel (F3).** Op de regressiemeetset kalibreren, of schrappen voor het poortpad als hij nergens filtert; vastleggen in config met motivatie.
- **3e Hybride/rerank/queryverrijking (F5, F8) → DEF-614.** Niet in deze ronde: DEF-614 vereist de goldset (B3). DEF-614 actualiseren: de huidige poort is al een lexicale kandidaatgenerator; omvang is 6.160, niet 1.423 fragmenten. Afkortingen via DEF-841.

### Fase 4 — Prompt (DEF-632, F7) · 1–2 dagen · akkoord via B4

Venster rond de eerste vindplaats van het begrip, met de structuurkopregel erboven, binnen het bestaande tokenbudget; kwitantie registreert welk venster is gebruikt. Test: artikel met begrip na 2.400 tekens behoudt de vindplaats in de prompt.

### Fase 5 — Eindresultaat meten (DEF-612, vervolg op DEF-318) · 3–5 dagen + beoordelingstijd

- Gepaarde proef op 20–30 begrippen (uit de regressiemeetset, aangevuld door Chris): definitie met bronnen vs. zonder, blind beoordeeld (Chris of een verse beoordelaar, nooit het model dat genereerde).
- Bronsteun per kenmerk: elk genus/differentia-kenmerk gekoppeld aan een passage of gemarkeerd als niet onderbouwd (sluit aan op CON-02 / DEF-743).
- **Klaar als:** rapport met winst/verlies per begrip; geen totaalcijfer dat zwakke gevallen maskeert.

### Fase 6 — Corpus uitbreiden (F10) · per corpus apart

Alleen via de corpusgate van DEF-368: eigen labels, baseline en toelatingsbesluit per corpusfamilie (bv. memorie van toelichting Sv). Geen uitbreiding op volume.

## 4. Omvang

Ruwe raming, netto werkdagen, exclusief label- en beoordelingstijd van Chris en het invullen van de matrix: fase 1 (vervanging) 1 · fase 2 4–7 · fase 3 4–8 · fase 4 1–2 · fase 5 3–5. Fase 3e en 6 zijn niet geraamd (afhankelijk van uitkomst). Labeltijd DEF-634: naar schatting 1–2 dagdelen voor 50 querys.

## 5. Linear (uitgevoerd 9 oktober)

Epic **DEF-847** "[EPIC][RAG] RAG-kwaliteit: contextgestuurde bronselectie en betrouwbare rangorde" (onder DEF-610) volgt dit hele werkplan.

| Fase | Issue | Parent |
|---|---|---|
| 2a matrix | DEF-846 | DEF-613 |
| 2b bronselectie volgt context | DEF-631 (comment met besluiten) | DEF-613 |
| 2c waarschuwing foute combinatie | DEF-849 | DEF-847 |
| 1 (vervanging) regressiemeetset | DEF-848 | DEF-847 |
| 3a begripsbepalingen in lopende tekst | DEF-850 | DEF-847 |
| 3b+3c voorrang + spreiding | DEF-851 | DEF-847 |
| 3d drempel | DEF-852 | DEF-847 |
| 4 prompt | DEF-632 (comment met B4) | DEF-613 |
| 5 eindresultaat meten | DEF-853 | DEF-847 |

Comments met besluit B3 op DEF-368 en stand/correcties op DEF-614. Blokkaderelaties staan op de issues.

## 6. Buiten scope

Ingest/extractie van uploads (E-001…E-003, DEF-659), provenance-doorgifte (E-005, DEF-629), RAG-zoektest-UI (H-007), backup (K006): staan in P5/P9 van het onderzoek van 7 oktober. Geen wissel van vectoropslag of embeddingmodel zonder DEF-614-meetgate.

## 7. Eerste volgende actie

Fase 0: plan op een docs-branch, Linear bijwerken (§5). Daarna levert Cowork de eerste invulling van de matrix (2a) ter controle door Chris; dat is de eerste inhoudelijke stap.
