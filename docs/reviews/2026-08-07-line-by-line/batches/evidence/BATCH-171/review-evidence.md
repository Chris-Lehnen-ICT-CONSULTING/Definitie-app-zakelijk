# BATCH-171 — reviewbewijs

- Reviewbasis: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Vastgelegde reviewer: `codex-galileo`
- Onafhankelijke verifier: `codex-hypatia`
- Scope: 17/17 bereiken, 5872/5872 fysieke regels en 0/0 Python-symbolen

Alle regels zijn rechtstreeks uit immutable Git-objecten gelezen; de bronbestanden zijn niet gewijzigd.

## Verificatie

- Alle immutable bronnen en symbolen zijn gelezen; import-, config-, CI-context-, Git-policy-, fuzzy-duplicate- en gerichte pytestreproducties zijn uitgevoerd.
- Object-ID, range, line owner en reviewerpair matchten het batchmanifest exact.

## Bevindingen

### B171-001 — P2 — Canonieke TDD-naar-deploymentworkflow kan niet worden doorlopen tegen de actuele repository

**Bewijs:** De SSoT-workflow vereist een afwezig master-storybestand, EA/SA/TA-uitvoer, docs/test-coverage.md, PR_TEMPLATE.md en andere ontbrekende documenten; hij eist ook volledige integratietests en 80% coverage met 60% minimum. De echte Makefile/CI-gate is bewust unit-only met 45% ratchet. De voorbeeldpipeline gebruikt bovendien rebase en git add -A, in strijd met de actuele merge- en wijzigingsgrenzen.

**Reproductie:** Controleer de genoemde artefactpaden uit regels 66-285 en 469-499 met git cat-file -e; ze ontbreken. Vergelijk regels 199-215 en 275-285 met Makefile:87-95, waar test-cov-ci unit-only --cov-fail-under=45 uitvoert.

**Aanbevolen oplossing:** Herschrijf de workflow vanuit de actuele issue-, architectuur-, merge- en CI-contracten; link naar bestaande artefacten, gebruik de expliciete 45%-ratchet en supported testtargets, en laat een CI-doctest ieder command/pad plus de coveragewaarde verifiëren.

### B171-002 — P2 — Actieve cleanupworkflow behandelt Git als volledige backup en stage/pusht repositorybreed

**Bewijs:** De workflow noemt git history een automatische backup, verlangt toestemming alleen bij meer dan vijf bestanden of canonieke wijzigingen, voert git add -A uit en pusht rechtstreeks naar main. De quickstart herhaalt DELETE-beslissingen en dezelfde >5-approvalgrens op regels 730-773. Ontracked/ignored gegevens zitten niet in Git en repositorybrede staging kan ongerelateerde gebruikerswijzigingen meenemen; de instructie botst met actuele toestemming-, scope- en PR-regels.

**Reproductie:** Lees de prerequisites en commit/pushblokken op 244-275 en 333-410 plus de quickstart op 730-773. Voeg conceptueel een untracked bestand en een ongerelateerde tracked wijziging toe: git history bevat het eerste niet en git add -A neemt het tweede wel mee; geen stap controleert de exacte staged set voor de push.

**Aanbevolen oplossing:** Vereis expliciete toestemming voor iedere verwijdering, een externe/gevalideerde backup waar nodig en een schone, exact gescoped featurebranch. Stage expliciete paden, inspecteer de staged diff, gebruik PR/review/required checks en bied een geteste herstelprocedure voor untracked en tracked inhoud.

### B171-003 — P2 — Branch-protectiongids laat niet-bestaande stepnamen als verplichte statuschecks configureren

**Bewijs:** De gids zegt exacte checks 'CI / Run Grep Gate (enforced for services)' en 'CI / Run smoke test with coverage' verplicht te maken. In .github/workflows/ci.yml zijn dit alleen step-namen binnen job `tests`; de gepubliceerde context is normaliter de jobcheck `CI / tests`, niet iedere step. Geen workflow bevat de voorgeschreven volledige contextnamen. De documentatie/configuratiefout is bewezen; feitelijke externe branch-protection en een PR die op Expected blijft staan zijn zonder netwerk niet getest.

**Reproductie:** Zoek de twee exacte strings onder .github/workflows: er is geen match. Zoek zonder de 'CI /'-prefix: beide labels staan uitsluitend onder '- name:' in ci.yml:33 en :39. Configureer een vereiste context die geen job/check-run produceert en een PR blijft geblokkeerd in Expected/Waiting state.

**Aanbevolen oplossing:** Documenteer en pin de daadwerkelijke job/check-run-namen uit een recente PR of automatiseer branch rules via versiebeheer. Voeg een periodieke API-check toe die vereiste contexts vergelijkt met werkelijk gerapporteerde checks en verwijder instructies om protections tijdelijk te omzeilen.

### B171-004 — P2 — Actieve multi-agentquickstart bestaat volledig uit ontbrekende helpercommando's

**Bewijs:** De current/active quickstart stelt expliciet dat scripts/multiagent.sh in de repository staat en baseert init, status, review en teardown daarop; integratie verwijst tevens naar scripts/agent_scoreboard.sh en scripts/agent_quick_checks.sh. Alle drie paden ontbreken op de immutable base. De canonieke codex-multi-agent-gebruikgids verwijst naar dezelfde helper, zodat alle aanbevolen quickstartflows vóór enige agentactie stoppen.

**Reproductie:** Voer voor elk van de drie paden git cat-file -e b958ddb:<pad> uit; elk commando eindigt niet-nul. Een credentialvrije shellinvocatie van bash scripts/multiagent.sh status zou daarom exit 127/No such file geven.

**Aanbevolen oplossing:** Verwijder de helperworkflow of herstel één onderhouden scriptlocatie met safe defaults, clean-tree checks en tests. Laat de quickstart in CI minimaal ieder genoemd commando op --help/status uitvoeren en laat ontbrekende scripts de documentatiegate blokkeren.

## Deduplicaties en afwijzingen

- De drie procesveiligheidsdocumenten relateren onderling maar hebben onderscheiden cleanup-, CI- en quickstart-impact.

## Niet getest

- Geen live AI/netwerk/credentials, externe GitHub-protection, destructive Gitflows, productiedata of Streamlit/browser/a11y-runtime.
