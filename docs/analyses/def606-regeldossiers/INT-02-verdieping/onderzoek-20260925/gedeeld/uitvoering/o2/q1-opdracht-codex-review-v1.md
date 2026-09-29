# DEF-835 Q1 — onafhankelijke Codex CLI-review v1

Jij bent de Codex CLI-reviewer. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Wijzig GEEN bronbestanden, tests, configuratie of fixtures. Alleen lezen, gerichte offline verificatie en bevindingen rapporteren. Alles Nederlands.

## Reviewidentiteit

Afzonderlijke reviewwerkboom: /Users/chrislehnen/.codex/worktrees/def835-q1-review/Definitie-app
Base: f9bb9e6973926a3cf768995f5d879f6edfd6322d (HEAD van reviewwerkboom).
Ongecommitteerde diff, exact3bestanden:
- scripts/analysis/def835_int02_modelproef.py — SHA256f4d09238998b1233f888eb1c702fa2334eb84b50dcbfd80f32ac53fd879a7f06
- tests/unit/validation/test_def835_int02_modelproef.py — SHA2564a8960ba544aea15220ba2f31f6c8c9ae05731b30ae3101728bd50c0361a0b30
- tests/fixtures/def835_int02_kwalificatie_runner.json (nieuw) — SHA2562f50c456756614cc35e78b81f57f4c8afc748b79d4cfcd6da053306e6c8fd7a7

De coördinator heeft deze kopieën bytegelijk geverifieerd. Review uitsluitend deze diff; zoek aangrenzende bestaande code alleen voor concrete call-/contractvragen. De nieuwe echte conceptgoldset is bewust NIET gekopieerd. Lees niets uit goldset-voorbereiding/ in de oorspronkelijke werkboom; testfixture is uitsluitend technisch materiaal.

Relatief dossier U in jouw werkboom:
docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2

Lees U/kwalificatieprotocol-v1.md, U/vervolg-akkoord-v1.md, U/q1-opdracht-claude-v1.md en bewijs/q1-coordinator-v1.json/.log. CLAUDE.md en toepasselijke regels. Rol is al toegewezen; geen delegatie. Geen netwerkaanroepen, productiedata, Actions, stage/commit/push of activering.

## Vereisten

- Oude driecasusmodus en oude manifestvalidatie blijven bruikbaar. Het verbruikte oude mandaat autoriseert geen nieuw profiel.
- Extern bevroren gevallenmanifest, juiste40nieuwegevallen/24ontwikkeling/16holdout plus3regressies, expliciete eigenaaracceptatie en hashbinding van input/labels/split/protocol/prompt/norm/model/router/bron.
- Labels en splitsing zijn lokale evaluatiegegevens; geen goldlabels in verzoek aan het model.
- Dezelfde echte AIService/provider/routerketen als bestaande runner; geen parallelle directe providerstack.
- Cumulatief max43calls/43tokenmetingen, input16000/output6000,120s/call/6000s totaal,US$12; standard/global en vastmodelclaude-opus-5.
- Reservering/grootboek vóór transport; herstart of dubbelrun mag budget niet resetten of onzekere call kosteloos opnieuw uitvoeren. Fouten fail-closed. Geen retries/fallback/cache/tools/fast/batch.
- Fasen3→24→16; regressies alle3goed; ontwikkeling21/24 en geen kritieke fouten; holdout4/4fail,7/8pass,3/4RR en14/16totaal. Stop technische/citaatfout/kritieke falsepass; geen volgende fase bij mislukte voorwaarden.
- Ook de vooraf vastgestelde latencygrens (holdoutp95≤90s) en betekenis van inhoudelijke gronden controleren. Geen mechanische statusmatch presenteren als afgeronde expertbeoordeling.
- Geen stille model-/promptwijziging of automatische extra calls bij falen. Volledige synthetische proefartefacten behouden; geen keys in log.
- Offline default; live alleen met nieuw geldig exactmanifest/akkoord en geaccepteerde labels. Geen zelfstandig activeringsbesluit.
- Bestaande testcases behouden; geen onverwachte verandering buiten3bestanden. Veel groter dan raming: beoordeel extra complexiteit alleen op concrete fout/onnodige scope, geen stijl- of LOCrefactor op zichzelf.

## Bewijs en verificatie

RED:79failed/77passed,exit1 op ontbrekende API. GREEN:156passed,exit0. Coördinator herhaalde met expliciet geïnstalleerde tests.offline_bootstrap:156passed23.99s;Ruff/Blackexit0; hashes voor/na gelijk.
Geen volledige-appsuiteclaim en geen semantisch modelkwalificatiebewijs.

Gebruik projectvenv /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python. Voor gerichte uitvoering in deze kopie: installeer tests.offline_bootstrap vóór pytest-import, neutraliseer providerkeys/DEFINITIE_DISABLE_DOTENV=1 en gebruik tijdelijk pytest-basetemp. Schrijf geen nieuwe testcode in repository; eventuele minimale bewijsprobe uitsluitend in eigen tijdelijke map. Hergebruik geldig groenbewijs tenzij een concrete open vraag een nieuwe test verlangt.

Lever per bevinding: ernst, exactbestand/regel, concrete trace/reproduceerbare invoer, geschonden vereiste, kleinste correctie. Geen vermoedelijke bug zonder bewijs; geen codepatch. Sluit af met of Q1 aan het protocol voldoet en concrete resterende leemten. Coördinator geeft bevestigde bevindingen aan dezelfde Claude-uitvoerder; jij reviewt diens delta later.

Het laatste antwoord wordt automatisch opgeslagen als U/q1-codex-review-v1.md in de oorspronkelijke dossiermap; schrijf dat bestand niet zelf.

