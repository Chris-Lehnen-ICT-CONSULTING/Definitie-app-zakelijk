# DEF-743 — eindstatus van de acceptatievoorbereiding

16 september 2026. Dit is de actuele overdracht; [v1](overdracht-v1.md) blijft behouden als eerdere momentopname.

## Afgerond

- Het brongebonden pakket bevat 31 praktijkgevallen, alle 94 historische scenario-ID's, 13 fixtures en zeven byte-identieke basissnapshots. De [synthese](synthese-en-beslispunten-v1.md) verbindt de afzonderlijke Codex- en Cowork-voorbeoordelingen en bewaart de inhoudelijke verschillen.
- Cowork v2: alle 31 invoerobjecten gelijk aan de oorspronkelijke invoer; 111 citaatfragmenten onafhankelijk gecontroleerd. Menselijke velden blijven leeg.
- Claude Code CLI schreef de pakketcode. Codex CLI sloot beide concrete reviewbevindingen: casusverwisseling en meerregelige menselijke motivering. [Laatste sluitreview](bewijs/pakket-review-v3.md): **PASS**.
- Verifier: ongewijzigd pakket groen, **11 negatieve zelftests rood**. Herbouw naar een bestaand gevuld pakket wordt vóór schrijven geweigerd; de overschrijfoptie bestaat niet meer. Een lege doelmap is toegestaan. [Bewijs](bewijs/pakket-zelftest-v2.txt).
- Ruff en Black: schoon voor de twee pakketbouw-/verificatiescripts. Geen productiecode gewijzigd en geen volledige app-regressierun voor deze documentatievoorbereiding geclaimd.
- Git-diffcontrole signaleert alleen eindspaties in Markdown: bewaarde Cowork-hardbreaks en lege formuliervelden. Deze zijn bewust behouden voor bronintegriteit en formulierweergave; dit is geen claim van een volledig waarschuwingsvrije diff.

## Skills daadwerkelijk gemerged

[PR #331](https://github.com/ChrisLehnen/claude-global-setup/pull/331), mergecommit `1d1b8f89ac06c18ca6453a045a5831c22ce27f78`, regulier gemerged op 16 september om 10:22:17 UTC. De merge bevat exact dezelfde inhoud als de geteste PR-head `cf650a3980aeef30bff219c3ed6a70489331169d`.

CON-01 en CON-02 zijn beide behouden in de drie definitie-skills en hun ZIPs. 80 gerichte controles, volledige suite **2.847 passed / 2 skipped / 17 xfailed**, onafhankelijke review PASS; GitHub lint en Python 3.13/3.14 groen. Volledige bewijsgrenzen en mergeboom staan in [v1](overdracht-v1.md).

## Nog nodig

**Menselijke inhoudelijke acceptatie:** er is nog geen deskundig oordeel ontvangen. Begin met P01, P02, P04, P11, P16 en P31; P14/P24/P30 hebben daarnaast expliciete inhoudelijke beslispunten. De gestelde P01-vraag is een verzoek om een concreet oordeel, geen reeds verleende acceptatie. Een algemeen akkoord op voortgang accepteert geen overige gevallen.

**Volledige appuitvoering:** na vaststelling van de verwachtingen moeten werkelijke invoer, passages, uitvoer en afwijkingen per geval worden vastgelegd. Het bestaande technische bewijs van [app-PR #454](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/454) blijft daarvan onderscheiden. DEF-630 is niet omzeild.

**Live skillactivatie:** ALG-391 houdt de lokale installatie nog tegen. De freeze is intact; publicatie bewijst geen geladen skill of clientgedrag. [Concrete activatievoorwaarden](skills-activatievoorwaarden-v1.md).

[DEF-743](https://linear.app/definitie-app/issue/DEF-743/story-implementeer-con-02-bronbasis-betekenissteun-en-herleidbare) blijft In Progress. [Linear-dossier](https://linear.app/definitie-app/document/con-02-deskundige-acceptatie-en-skillpublicatie-16-september-2026-e93cb95a0b75).
