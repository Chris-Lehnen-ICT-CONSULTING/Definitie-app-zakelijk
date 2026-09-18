---
title: LLM-wiki
type: begrip
tags: [llm-wiki, architectuur]
ontologie_id: llmwiki:LLMWiki
genus: Kennisbank
classificatie: artefact-tak — TYPE
sources: [2026-07-08-karpathy-llm-wiki-gist, 2026-07-08-praneybehl-llm-wiki-plugin-readme]
last_updated: 2026-08-03
last_reviewed: 2026-08-03
confidence: high
lifecycle: reviewed
status: actueel
---

# LLM-wiki

## Definitie

kennisbank van onderling gelinkte markdown-pagina's die door een taalmodel wordt geschreven en onderhouden op basis van een verzameling onveranderlijke bronnen

## Classificatie

llmwiki:LLMWiki — topbegrip van het domein; artefact (TYPE). Het "persistent, compounding artifact" uit de gist: kruisverwijzingen liggen er al, contradicties zijn al geflagd, de synthese weerspiegelt alles wat is gelezen.

## Relaties

- **is-een** → Kennisbank
- **bestaat-uit** → [[Raw-laag]], [[Wiki-laag]], [[Onderhoudscontract]]
- **hangt-af-van** → [[Operatie]] *(opbouw en onderhoud verlopen via vaste operaties)*
- **tegenover** → RAG *(herafleiding per vraag zonder accumulatie — zie [[Wiki-vs-RAG]])*

## Voorbeelden

- Karpathy's eigen onderzoekswiki (~100 artikelen, ~400K woorden zonder zoekinfrastructuur) ^[2026-07-08-praneybehl-llm-wiki-plugin-readme: "Karpathy's own wiki was about 100 articles and 400K words working fine"]
- Toepassingscontexten uit de gist: persoonlijk (doelen, gezondheid), onderzoek, boek-companion, team-wiki uit Slack/transcripten, due diligence, reisplanning.

## Toelichting

De mens cureert bronnen en stelt vragen; het taalmodel doet al het bijhoudwerk (samenvatten, kruisverwijzen, archiveren). Verwant aan Vannevar Bush' Memex (1945) — het onopgeloste onderhoudsprobleem daarvan wordt hier door het taalmodel gedragen.

## Connections

- [[Raw-laag]] · [[Wiki-laag]] · [[Onderhoudscontract]] · [[LLM-Wiki-patroon]] · [[karpathy-llm-wiki-gist]] · [[praneybehl-llm-wiki-plugin]]
