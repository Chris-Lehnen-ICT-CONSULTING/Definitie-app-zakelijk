# DEF-835 — actuele takenlijst v15

28 september 2026. Vervolg op v14 en Chris' opdracht om door te gaan. Werkboom `.claude/worktrees/DEF-835-int02-o2`, branch `feature/DEF-835-int02-o2`, uitgangscommit `558b50c3f161f819cda6c445f7f81b70888918ac`.

- [x] WP1–WP3 afgerond; 555 gerichte regressietests en onafhankelijke WP3-review, zie wp3-oplevering-v1.md.
- [x] Actuele DEF-626/815/835 en bestaande providerroute gericht gecontroleerd.
- [x] Technische proef afgebakend in technische-modelproef-voorstel-v1.md: drie synthetische gevallen, bestaand Opus5-model, voorgesteld USD1-plafond, geen kwalificatieclaim.
- [x] Opdracht aan Claude CLI vastgelegd en gestart; twee nieuwe softwarebestanden, geen productiecodewijzigingen.
- [ ] Proefrunner: RED → GREEN, offline dry-run en lint (in uitvoering).
- [ ] Onafhankelijke Codex CLI-review in aparte bestaande werkroot.
- [ ] Concreet proefprofiel/kostenplafond en akkoordmanifest vaststellen; algemene toestemming voor modelcalls bestaat al.
- [ ] Technische echte modelproef uitvoeren, gebruik/kosten/uitkomsten rapporteren.
- [x] WP5a-aansluiting concreet voorgesteld: zeven bestanden plus optionele API-injectie; zie wp5a-integratievoorstel-v1.md.
- [ ] WP5a-bereik/API-uitbreiding accorderen en vervolgens implementeren.
- [ ] WP4: onafhankelijke goldset/hold-out en inhoudelijke modelkwalificatie.
- [ ] WP5 vervolg: gedeelde opslag DEF-626, historisch herladen, UI/export en ketenlogging.
- [ ] WP6: finale verificatie/PR en afzonderlijke activering.

Claude CLI-uitvoerder: sessie `57f4b3fa-7776-4a45-bdee-732da1344d2f`, echte binary 2.1.283, claude-opus-5-5. Dit CLI-ontwikkelmodel is niet het aangevraagde app-proefmodel. Effectieve tools: Read, Glob, Grep, Edit, Write, Bash; geen MCP/Agent/Task. Codex CLI 0.157.1 beschikbaar, reviewwerkroot `/private/tmp/def835-wp2-review-20260927` schoon op de basis gezet.

Prompts volledig in dit dossier; eerder vastgestelde Prompt Forge-fallback blijft gelden. Actions blijven uit. Geen push/merge/activering. Deze versie registreert lopend werk, geen voltooide modelproef.
