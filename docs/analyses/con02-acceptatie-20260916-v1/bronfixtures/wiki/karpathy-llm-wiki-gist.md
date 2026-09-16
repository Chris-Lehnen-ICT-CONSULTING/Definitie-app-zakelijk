---
title: Karpathy — LLM Wiki (gist, april 2026)
type: source
tags: [llm-wiki, primaire-bron]
sources: [2026-07-08-karpathy-llm-wiki-gist, 2026-07-08-praneybehl-llm-wiki-plugin-readme, 2026-07-08-archcheck-wiki-economie, 2026-07-08-kritiek-llm-wiki-collapse, 2026-07-08-stale-benchmark, 2026-08-03-gist-comment-confident-fabrication, 2026-08-03-praneybehl-llm-wiki-plugin-v2.0.7-readme, 2026-08-03-praneybehl-llm-wiki-plugin-v2.0.7-changelog]
last_updated: 2026-08-03
last_reviewed: 2026-08-03
confidence: high
lifecycle: reviewed
status: actueel
---

# Karpathy — LLM Wiki (gist)

## Samenvatting

Het oorspronkelijke "idea file" van het [[LLM-Wiki-patroon]]: een taalmodel bouwt en onderhoudt
incrementeel een persistente markdown-wiki bovenop onveranderlijke bronnen, als alternatief voor
RAG-herafleiding per vraag. Beschrijft drie lagen, drie operaties, twee navigatiebestanden,
optionele tooling en de rolverdeling mens/model. Bewust abstract: de agent van de lezer bouwt de
specifieke variant.

## Kernclaims

- **bronpositie** — RAG accumuleert niets; de wiki is "a persistent, compounding artifact" (zie [[Wiki-vs-RAG]]).
- **bronpositie** — Drie lagen: [[Raw-laag]] (immutable, source of truth), [[Wiki-laag]] (volledig model-eigendom),
  [[Onderhoudscontract]] ("the key configuration file").
- **bronpositie** — Drie operaties: [[Ingest]] (één bron raakt 10–15 pagina's), [[Query]]
  (antwoorden met citaties, terug te filen als pagina's), [[Lint]] (contradicties, verouderde
  claims, orphans, gaten). ^[2026-07-08-karpathy-llm-wiki-gist: "A single source might touch 10-15 wiki pages."]
- **bronpositie** — [[Index]] (inhoudelijk) en [[Logboek]] (chronologisch, parseerbaar voorvoegsel)
  als navigatie; index-eerst werkt volgens de auteur tot ~100 bronnen / ~honderden pagina's zonder
  zoekinfrastructuur. ^[2026-07-08-karpathy-llm-wiki-gist: "This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure."]
- **bronpositie** — Onderhoud is de reden dat kennisbanken sterven; het taalmodel maakt de
  onderhoudskosten volgens de gist "near zero". Het idee wordt verwant genoemd aan de Memex
  (1945). ^[2026-07-08-karpathy-llm-wiki-gist: "The wiki stays maintained because the cost of maintenance is near zero."] ^[2026-07-08-karpathy-llm-wiki-gist: "The idea is related in spirit to Vannevar Bush's Memex (1945)"]
- **bronpositie** — Tooling optioneel: [[Qmd]] voor hybride zoeken; Obsidian (Web Clipper, graph view, Dataview,
  Marp); git voor gratis geschiedenis.

## Belangrijke citaten

> "the LLM is rediscovering knowledge from scratch on every question. There's no accumulation." — over RAG
> "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase." — rolverdeling
> "good answers can be filed back into the wiki as new pages" — het compounding-inzicht bij [[Query]]
> "The part he couldn't solve was who does the maintenance. The LLM handles that." — over de Memex
> "This document is intentionally abstract. It describes the idea, not a specific implementation." — status van de gist

## Connections

- [[LLM-Wiki-patroon]] · [[LLM-wiki]] · [[Andrej-Karpathy]] · [[Qmd]] · [[Wiki-vs-RAG]]

## Contradicties

- **gevolgtrekking** — **"Cost of maintenance is near zero"** staat op gespannen voet met de A/B-meting in
  [[archcheck-wiki-economie]] (spiegelpagina's zijn "pure maintenance debt"; 8 van 28 pagina's
  dezelfde dag al stale) en met [[kritiek-llm-wiki-collapse]] ("maintenance without pruning ...
  that's a slower death, not a cure"). De gist claimt lage *uitvoerings*kosten; de tegenbronnen tonen dat de
  *totale* onderhoudseconomie een grensvoorwaarde heeft (zie [[Wiki-economie]]).
  ^[2026-07-08-karpathy-llm-wiki-gist: "The wiki stays maintained because the cost of maintenance is near zero."] ^[2026-07-08-archcheck-wiki-economie: "The 28-page wiki also decayed immediately: the staleness lint flagged 8 pages the same day, after unrelated commits touched files the pages cited."] ^[2026-07-08-kritiek-llm-wiki-collapse: "maintenance without pruning, without invalidation, without a mechanism to distinguish what has crystallized from what is merely accumulated — that's a slower death, not a cure."]
- **gevolgtrekking** — De gist geeft geen [[Kennislevenscyclus]] (invalidatie/dormancy) — het centrale verwijt van
  [[kritiek-llm-wiki-collapse]].
