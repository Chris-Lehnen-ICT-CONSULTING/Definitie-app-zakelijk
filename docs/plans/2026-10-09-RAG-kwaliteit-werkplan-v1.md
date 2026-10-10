# Werkplan RAG-kwaliteit bronbibliotheek — v1 — TER GOEDKEURING

9 oktober 2026 · opgesteld door Cowork · nog niet goedgekeurd, nog niet gestart.

**Doel:** de bronbibliotheek levert voor een begrip de juiste, geldende en gezaghebbende passages, en we kunnen aantonen dat die passages de definitie beter maken. Dit plan ordent de bevindingen van de RAG-meting van 9 oktober langs de bestaande Linear-lijnen (DEF-613, DEF-368, DEF-614, DEF-612). Het plan voegt geen parallelle backlog toe: waar een issue al bestaat, worden acceptatiecriteria aangevuld.

**Bewijs:** `docs/analyses/2026-10-09-rag-meting/` (`meet-v1.py`, `resultaat-v1.json`): 19 zoekvragen op een kopie van `data/bronnen.db` (22 collecties: 21 regelingen plus de lege uploadcollectie; 6.160 fragmenten) via de echte `RAGService._zoek_hybride`. Overlap met het volledige onderzoek van 7 oktober (E-001…E-005, H-007, J003, K006, R-001; pakket P5) staat hieronder per stap vermeld en wordt niet opnieuw onderzocht.

## 1. Uitgangspunt — bevindingen 9 oktober

| # | Bevinding | Bewijs (resultaat-v1.json) | Bestaand issue |
|---|---|---|---|
| F1 | Huidig en toekomstig recht gemengd: standaard alle collecties geselecteerd, ook "Sv (nieuw, i.w.t. 1-4-2029)"; `peildatum` bestaat in de orchestrator maar niet in retrieval | "voorlopige hechtenis": 5/5 uit nieuw Sv; "verdachte", "inbeslagneming": geldend en nieuw door elkaar | DEF-631 (randgeval "verouderde bronversie buiten effective-datefilter") |
| F2 | Rechtsgebied is één label per collectie en een hard filter: gezaghebbende bron valt weg | "persoonsgegevens" + bestuursrecht → UAVG/Brp, AVG art. 4 ontbreekt (AVG = `europees_recht`) | DEF-631, R-001, E-004 |
| F3 | `RAG_MIN_SCORE=0.3` filtert achter de poort niets | laagste top-5-score 0,346 over 95 fragmenten | — |
| F4 | Geen spreiding: één artikel vult 4–5 van de 5 plekken | politiegegeven, eIDAS, AVG 4, Pbw 1 | — |
| F5 | Rangorde rust op cosine van één los woord; geen voorrang voor de begripsbepaling van precies dit begrip; geen rerank | 1.003 kandidaten bij "verdachte"; "dagvaarding" mist kernartikelen 258/260 | DEF-614 |
| F6 | Definities in lopende tekst ("Onder besluit wordt verstaan") niet als begripsbepaling herkend | Awb 1:1, 1:3 als `artikel` | — |
| F7 | Prompt kapt lange fragmenten vanaf het begin af (600 tokens) | 421 fragmenten > 600 tokens; tot 36 kandidaten per begrip met begrip ná de knip; in de gemeten top 5 geen geval | DEF-632 |
| F8 | Poort herkent alleen het begrip (+ -ing-vormen); geen synoniemen/afkortingen | bewuste keuze (orchestrator-commentaar DEF-620) | DEF-841 (afkortingen) |
| F9 | Meting te smal: kleine, zelfgekozen meetset; lexicaal orakel; geen meting op eindresultaat | `tests/fixtures/rag_meting/*` | DEF-368 (633–635), DEF-612 |
| F10 | Corpus beperkt tot 21 regelingen; geen MvT/Kamerstukken/jurisprudentie | geen collecties van het type Kamerstukken of beleid | DEF-368 corpusgate |

Wat goed is en zo blijft: artikelgewijze chunks uit officiële XML met structuurkopregel, aparte begripsbepalingen, versie/URL/sha256 per collectie, poort + semantische rangorde, bronnen als data in de prompt, kwitantie (DEF-743), brute-force NumPy op deze schaal.

## 2. Besluiten van Chris vóór start

| Besluit | Vraag | Advies |
|---|---|---|
| B1 Peildatum | Wat is standaard: alleen geldend recht op vandaag, of ook toekomstig recht? | Standaard peildatum = vandaag (hard filter op geldigheid); toekomstig recht alleen met expliciete peildatum of bewuste collectiekeuze, en dan zichtbaar gemarkeerd in bronweergave en prompt. |
| B2 Rechtsgebied | DEF-631 kiest harde filters. Hoe voorkomen we dat een algemeen toepasselijke bron (AVG, Awb) wegvalt? | Filter hard laten (DEF-631), maar het label meervoudig maken: per collectie een lijst `toepasselijk_in` (AVG → o.a. bestuursrecht, strafrecht). Alternatief: rechtsgebied alleen laten meewegen in de rangorde — dat botst met DEF-631 en vraagt een expliciet besluit. |
| B3 Goldset | Wie labelt, en welk corpus eerst? (open vraag DEF-368/634) | Strafrecht eerst (DEF-634), aangevuld met de faalgevallen uit §1 (F1, F2, F5) als vaste querys, ook als die buiten strafrecht vallen. Labelen door Chris; adjudicatie bij twijfel apart vastleggen. |
| B4 Prompt builder | F7 raakt `prompt_service_v2` (CLAUDE.md: niet wijzigen zonder overleg) | Akkoord vragen om binnen DEF-632 een venster rond de eerste treffer te nemen i.p.v. afkappen vanaf het begin. |

## 3. Fasen en volgorde

Correctheidsfixes (fase 2) hebben geen goldset nodig en kunnen na B1/B2 starten. Elke wijziging aan selectie of rangorde (fase 3) pas na de baseline van fase 1, met een gepaarde vergelijking ervoor/erna.

```
B1–B4 ─┬─> Fase 1  meetfundament (DEF-633 → 634 → 635)
       └─> Fase 2  correctheid (peildatum, rechtsgebied)   ─┐
                                                            ├─> Fase 3 selectie & rangorde ─> Fase 4 prompt ─> Fase 5 eindresultaat
Fase 1 baseline ────────────────────────────────────────────┘                                                  └─> Fase 6 corpus
```

### Fase 0 — Vastleggen (0,5 dag)

- Dit plan en de meting van 9 oktober op een docs-branch committen; Linear bijwerken (zie §5).
- **Klaar als:** plan goedgekeurd, besluiten B1–B4 genoteerd, issues aangevuld.

### Fase 1 — Meetfundament (DEF-368: 633 → 634 → 635) · 3–5 dagen + labeltijd

1. **DEF-633 schema en metrics.** Offline, deterministisch: Recall@5/10, MRR@10, nDCG@10, context precision, filterviolations. Daarbij, als aanvulling uit deze meting: *versieschending* (passage buiten peildatum), *gezagsmisser* (gelabelde gezaghebbende passage niet in top 5) en *spreiding* (max. fragmenten per artikel in top 5). Bewezen op handberekende fixtures.
2. **DEF-634 labels.** 50 querys met canonical passage-ID, bronversie, geldigheidsdatum, relevante passages en hard negatives. Verplicht opnemen: voorlopige hechtenis / verdachte / inbeslagneming (geldend vs. nieuw Sv), persoonsgegevens met bestuursrecht (AVG 4), dagvaarding (258/260), plus homoniem "onttrekking" (TC-RAG-04).
3. **DEF-635 baseline.** Huidige pijplijn (poort + cosine + drempel) als nulmeting, bevroren met corpus-, chunk- en confighash. `meet-v1.py` dient als vertrekpunt; omzetten naar `scripts/rag_meting.py`-uitbreiding.
- **Klaar als:** baseline-rapport per corpus/rechtsgebied/querytype, zonder LLM-call reproduceerbaar.

### Fase 2 — Correctheid (DEF-613 / DEF-631) · 3–6 dagen

**2a Peildatum en geldigheid (F1).** Per collectie `geldig_vanaf`/`geldig_tot` in `config/bronnenlijst.yaml` en `rag_collections.metadata_json`; retrieval filtert hard op de peildatum (B1); UI-standaard volgt B1; bronweergave en `<bron>`-attributen tonen de geldigheid.
- Tests eerst rood: "voorlopige hechtenis", peildatum vandaag → 0 fragmenten uit nieuw Sv; peildatum 1-4-2029 → nieuw Sv toegestaan, geldend Sv niet meer na vervaldatum.

**2b Rechtsgebied-labelmodel en filtercontract (F2, R-001, E-004).** Volgens B2: `toepasselijk_in` per collectie; filter op doorsnede met de context; geen stille verruiming, abstain met reden (DEF-631); `juridische_context` volledig gebruiken i.p.v. alleen `[0]`.
- Tests eerst rood: "persoonsgegevens" + bestuursrecht → AVG art. 4 in de kandidaten; begrip zonder treffer in scope → verklaarde lege toestand, geen fragment uit ander rechtsgebied.

- **Werkwijze (risico middel):** featurebranch per issue in een eigen worktree, TDD, `make test` + `make lint`, één onafhankelijke review (Codex), Chris merget.

### Fase 3 — Selectie en rangorde · 4–8 dagen · alleen na fase 1-baseline

Elke stap levert een gepaarde delta op de goldset; een stap zonder winst gaat niet mee.

- **3a Begripsbepalingen in lopende tekst herkennen (F6).** Parsers (BWB, officiële publicatie, EU) herkennen "Onder X wordt verstaan", "In deze wet wordt verstaan onder", "Als X wordt aangemerkt". Herindexeren van de geraakte collecties via de bestaande vervang-/verhuisscripts (embeddingkosten: enkele dollars of minder; vooraf ramen).
- **3b Voorrang voor de begripsbepaling van precies dit begrip (F5).** Structurele voorrang vóór de cosine-rangorde; meerdere wetten → elk één begripsbepaling, geordend volgens de bronrangorde (DEF-844).
- **3c Spreiding (F4).** Maximaal 1–2 fragmenten per artikel in de top 5; overige plekken naar andere artikelen/wetten.
- **3d Drempel (F3).** Op de goldset kalibreren, of schrappen voor het poortpad als hij nergens filtert; vastleggen in config met motivatie.
- **3e Hybride/rerank/queryverrijking (F5, F8) → DEF-614.** Alleen als 3a–3d de gezagsmisser niet onder de afgesproken grens brengen. DEF-614 actualiseren: de huidige poort is al een lexicale kandidaatgenerator; omvang is 6.160, niet 1.423 fragmenten. Afkortingen via DEF-841.

### Fase 4 — Prompt (DEF-632, F7) · 1–2 dagen · na B4

Venster rond de eerste vindplaats van het begrip, met de structuurkopregel erboven, binnen het bestaande tokenbudget; kwitantie registreert welk venster is gebruikt. Test: artikel met begrip na 2.400 tekens behoudt de vindplaats in de prompt.

### Fase 5 — Eindresultaat meten (DEF-612, vervolg op DEF-318) · 3–5 dagen + beoordelingstijd

- Gepaarde proef op 20–30 begrippen uit de goldset: definitie met bronnen vs. zonder, blind beoordeeld (Chris of een verse beoordelaar, nooit het model dat genereerde).
- Bronsteun per kenmerk: elk genus/differentia-kenmerk gekoppeld aan een passage of gemarkeerd als niet onderbouwd (sluit aan op CON-02 / DEF-743).
- **Klaar als:** rapport met winst/verlies per begrip; geen totaalcijfer dat zwakke gevallen maskeert.

### Fase 6 — Corpus uitbreiden (F10) · per corpus apart

Alleen via de corpusgate van DEF-368: eigen labels, baseline en toelatingsbesluit per corpusfamilie (bv. memorie van toelichting Sv). Geen uitbreiding op volume.

## 4. Omvang

Ruwe raming, netto werkdagen, exclusief label- en beoordelingstijd van Chris: fase 1 3–5 · fase 2 3–6 · fase 3 4–8 · fase 4 1–2 · fase 5 3–5. Fase 3e en 6 zijn niet geraamd (afhankelijk van uitkomst). Labeltijd DEF-634: naar schatting 1–2 dagdelen voor 50 querys.

## 5. Linear-acties (voorstel, nog niet uitgevoerd)

- **DEF-631:** acceptatiecriteria aanvullen met 2a (peildatum) en 2b (`toepasselijk_in`, testgevallen AVG/voorlopige hechtenis); besluiten B1/B2 als comment.
- **DEF-634:** verplichte querys uit fase 1.2 toevoegen.
- **DEF-633:** extra metrics versieschending, gezagsmisser, spreiding.
- **DEF-614:** beschrijving actualiseren (poort, omvang 6.160); 3a–3d als voorafgaande stappen noemen.
- **Nieuw onder DEF-613 of DEF-614:** stories voor 3a (begripsbepalingen in lopende tekst), 3b+3c (voorrang en spreiding), 3d (drempel).
- **DEF-632:** venster-rond-treffer als acceptatiecriterium (na B4).

## 6. Buiten scope

Ingest/extractie van uploads (E-001…E-003, DEF-659), provenance-doorgifte (E-005, DEF-629), RAG-zoektest-UI (H-007), backup (K006): staan in P5/P9 van het onderzoek van 7 oktober. Geen wissel van vectoropslag of embeddingmodel zonder DEF-614-meetgate.

## 7. Eerste volgende actie

Chris neemt B1–B4. Daarna: fase 0 afronden en parallel starten met DEF-633 (fase 1) en 2a (fase 2).
