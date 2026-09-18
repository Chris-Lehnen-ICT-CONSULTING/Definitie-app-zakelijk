# DEF-743 — deskundige acceptatie voorbereid, skills gepubliceerd

16 september 2026. Dit pakket vervolgt de reeds gemergede CON-02-implementatie; het is geen nieuwe productiecodewijziging.

## Resultaat

- 31 concrete praktijkgevallen met ongewijzigde invoer, 13 bewaarde bronfixtures, zeven historische basissnapshots en een overzicht dat alle 94 scenario-ID's behoudt.
- Onafhankelijke voorbeoordelingen van Codex en Claude Cowork, met verwerkte concrete correcties en drie zichtbare inhoudelijke beslispunten. Begin bij [de samengebrachte beoordeling](synthese-en-beslispunten-v1.md).
- Een leeg [deskundigenformulier](deskundigenformulier.md) en [machineleesbaar register](acceptatie-register.json). Er is **geen menselijke acceptatie** vastgelegd.
- Een integriteitscontrole met acht negatieve zelftests. De gevonden P01/P02-casusverwisseling wordt nu gedetecteerd. Deze controle bewijst de integriteit van het voorbereidende pakket, geen modelkwaliteit of appketenuitvoering.

Claude Code CLI schreef de pakketcode en loste de concrete reviewbevinding op; Codex CLI reviewde die code. Het inhoudelijke onderzoek bleef bij Codex en Claude Cowork.

## Skills gepubliceerd

[PR #331](https://github.com/ChrisLehnen/claude-global-setup/pull/331) is op 16 september 2026 om 10:22:17 UTC **regulier gemerged**:

- mergecommit `1d1b8f89ac06c18ca6453a045a5831c22ce27f78`;
- geteste PR-head `cf650a3980aeef30bff219c3ed6a70489331169d`;
- gelijke inhoudsboom `b6d3806a5012b6470d7a3963175cd2a47504fdc3`;
- beide ouders aanwezig: `3d8dd6609d9db7dd57c0edd86b1130eaede615ee` en de PR-head.

De drie skills en ZIPs behouden zowel CON-01 als CON-02. Alle negen oorspronkelijke CON-02-artefacten waren vóór samenvoeging identiek aan de eerdere review. De nieuwe integratie kreeg een onafhankelijke [PASS](bewijs/skills-review.md), met 16 geldige lokale links inclusief ankers.

### Verificatie

- 80 gerichte skillchecks geslaagd.
- Volledige CI-equivalente suite onder Python 3.13.15: **2.847 passed, 2 skipped, 17 xfailed**, exit 0, 445,76 seconden.
- GitHub CI: lint, Python 3.13 en Python 3.14 alle geslaagd; [run 35084174912](https://github.com/ChrisLehnen/claude-global-setup/actions/runs/35084174912).
- De normale pre-commit-hook vernieuwde ZIP-containerbytes. Een [controle na commit](bewijs/skills-zipinhoud-na-commit.json) bevestigt dat alle bestandspaden en uitgepakte bytes exact gelijk bleven aan het gereviewde pakket en de bron.

De eerdere volledige testpoging met systeem-Python 3.9 strandde op niet-ondersteunde typesyntaxis; die poging geldt niet als opleverbewijs. Er is geen testgrens verlaagd of test verwijderd.

## Wat nog openstaat

1. **Deskundige acceptatie:** wie beoordeelt de gevallen en welke uitkomsten worden per bronversie geaccepteerd? Eerste voorgestelde set: P01, P02, P04, P11, P16 en P31. Een algemeen voortgangsakkoord accepteert niet automatisch alle gevallen.
2. **Uitvoering tegen vastgestelde verwachtingen:** de 31 praktijkgevallen zijn niet als volledige appketen gedraaid. De bestaande technische bewijsvoering van [app-PR #454](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/454) blijft afzonderlijk geldig binnen de destijds vastgelegde grenzen.
3. **Live skillactivatie:** de lokale ALG-391-freeze is nog actief. Er is geen nieuwe installatie of clientgedragsproef uitgevoerd. De exacte verschillen en vervolgstappen staan in [activatievoorwaarden](skills-activatievoorwaarden-v1.md).
4. **Algemene vaststelling:** de aparte DEF-630-poort is niet omzeild. Een positieve CON-02-beoordeling is geen algemene toestemming voor vaststelling of niet-draft-export.

DEF-743 blijft daarom **In Progress**. De technische appimplementatie en skillpublicatie zijn gemerged; inhoudelijke deskundige acceptatie en live activatie zijn daarmee niet automatisch voltooid.
