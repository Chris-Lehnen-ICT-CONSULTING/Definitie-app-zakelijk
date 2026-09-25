# DEF-770 — resterend herstel en onafhankelijke acceptatie

Leidend vanaf gebruikersbesluit 24 september 2026: “akkoord om het resterende werk: de twee beoordelingsproblemen herstellen en het betekenisverlies bij generatie oplossen, gevolgd door nieuwe onafhankelijke acceptatie … op te pakken”. Dit autoriseert de gerichte software-, test- en bijbehorende prompt-/skillswijzigingen, inclusief noodzakelijke promptbuilderaanpassingen. Geen merge of liveactivatie; geen nieuwe dependency, schemawijziging of API-breuk voorzien.

Basis app7ee7d7d293770dd86f2dd70f1b4945b25ead3c94 (productie c7f5d7dc9), skillsed0fcfdcc169c37058f0436fc92c1e07752366b8. Bestaande werkbomen en conceptPR474/356 blijven leidend. Claude CLI442a98fb-a377-403f-996e-433cf4a664fc implementeert; Codex CLI Astra/high01a0cfac-ea05-7700-ba73-8b5659751c1c reviewt. Coördinator schrijft geen productcode/tests. Geen wijziging historische gevallen, referenties, resultaten of criteria.

## Werkpakket 1 — concrete correcties

T20: expliciete titel met aansluitende betrekkelijke bijzin ondersteunen op algemene structurele gronden, met negatieve tegenhangers. Geen corpuswoorden of ruimer tekstvenster als oplossing.
T24: lokaal verklaarde afkortingspunten niet als zinsgrens opvoeren; bij onduidelijke aansluiting de werkelijke tekststructuur/passsage als onzekerheid melden. Alleen afkortingssignaal verwijderen en pass geven voldoet niet. Behoud duidelijke grenzen en bekende regressies; punt plus kleine letter blijft conservatief onzeker waar een mogelijke buitenste grens bestaat. Contract verhogen zodra beoordeelsemantiek verandert; skillsreferentie/bundels gelijkhouden. RED/GREEN en regressie van bekende sets, beide laadpaden/opslag.

Generatie: onderzoek de feitelijke complete prompt en bronpassages bij verlies van aansluitrelatie, verschuiving van niet-verplicht naar verplicht verschil, en verdwijnen van samen bewaren. Behoud bronhandelingen, relaties en modaliteit bij compact formuleren. Corrigeer aantoonbare instructieconflicten of ontbrekende operationalisering met een beperkte algemene wijziging; geen fixturetermen of ideale antwoorden in productie, geen extra modelcall/harde claim van semantische garantie. Appinstructie en betrokken skills uitlijnen. Tests voor werkelijke promptdoorwerking en relevante conflicten; tekstaanwezigheid bewijst geen generatie-effect.

## Werkpakket 2 — bronreview en technische verificatie

Zelfde reviewer ontvangt concrete diffidentiteit, acceptatiecriteria, RED/GREEN en regressiebewijs. Bevestigde bevindingen terug naar dezelfde uitvoerder; max3pogingen per concrete correctie. Brede unitgate en relevante gepinde lint, bundelcontrole na uiteindelijke bron. Na bronvrijgave commit/archive/hashbinding. Iedere beoordeling blijft aan precies die bron gekoppeld.

## Werkpakket 3 — verse onafhankelijke acceptatie

De vooraf vastgelegde criteria uit effectproeven-herstel-20260924-v1/proefafspraken-v3.md blijven inhoudelijk gelden: T24alle24volledigconform, nul ongefundeerde zekere besluiten, zinvolle automatische pass én fail, dekking/doorverwijzingen rapporteren; service/opslag consistent, geen volledigeINT01pass. Nieuwe maker, onafhankelijke A/B, adjudicator, Astra/high. Referenties vóór uitvoering verzegelen; onderliggende normatieve en automatische as scheiden. Nieuwe set pas na bronbevriezing aan beoordelaars, niet aan uitvoerder/reviewer vóór conclusie.

G24: zes verse synthetische dossiers, oud/nieuw, twee herhalingen; minimaal één inhoudelijke verbetering, geen nieuwe bron-/betekenisfout en geen gepaarde verslechtering. Twee blinde onafhankelijke Astra/high-beoordelaars, adjudicatie vóór deblindering; ruw en opgeschoond afzonderlijk. Zelfde model/settings, ongewijzigde gereviewde runners. Historische baseline26f2374d302fc66fc0b12ed29dc34585f7c0a5c3; rapporteer nieuweproef versusbaseline, geen causale claim over één instructie. Budget: cumulatief3.71545van5gebruikt,rest1.28455. Eerst daadwerkelijke tokenraming op concrete nieuwe dossiers/prompts, daarna zo nodig extra kostenmandaat vóór betaalde calls. Het nieuwe uitvoeringsakkoord wijzigt het eerdere expliciete kostenplafond niet stilzwijgend.

## Werkpakket 4 — oplevering

Bron-/proefbewijs en open bevindingen compact bijwerken in bestaande PRs/DEF770/WIP. Geen vrijgave claimen bij falende criteria; geen criteria achteraf aanpassen of onbegrensde herhaling. Geen merge/liveactivatie zonder latere opdracht.
