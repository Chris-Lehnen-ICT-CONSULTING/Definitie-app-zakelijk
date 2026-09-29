# DEF-835 WP1 — onafhankelijke Codex CLI-review v1

Jij bent de Codex CLI-reviewer. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Wijzig geen bron-, test-, fixture- of contractbestanden. Alleen deze hoofdsessie coördineert en Claude Code CLI implementeert/corrigeert.

Reviewwerkroot: /private/tmp/def835-wp1-review-20260926
Base: 84bdc8c1b060ab50a1bd1428aed778bb2ed6007f
Head: 314b817aabcaaa9f5a00d74a7633155ec74b799c
Diff: git diff base..head. Exact vijf inhoudelijke bestanden nieuw, overige wijzigingen zijn coördinatiedossier:
src/domain/int02/__init__.py
src/domain/int02/contract.py
tests/unit/domain/test_def835_int02_contract.py
tests/fixtures/def835_int02_ontwerpgevallen.json
docs/architectuur/contracts/int02_assessment_contract_v1.md

Leidende opdracht: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/plan-v1.md WP1, akkoord-wp1-v1.md. Lees de toepasselijke projectregels en skill requesting-code-review. Norm: besluiten-chris-v1.md B1–B6, synthese-v5 §2/§4 en casusregister-v5 in het INT-02-onderzoeksdossier. Geen nieuwe norm, geen publieke schemawijziging, geen activering. De 100-regelsgrens is expliciet opgeheven; extra regels alléén zijn geen functionele bevinding.

Bewijs ligt deels in implementatiewerkboom (read-only raadplegen):
/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/bewijs/
wp1-rood-v2.log: 162 failed, 161 NotImplementedError-stubs plus ontbrekend document; geen collectie/setupfout.
wp1-rood-coordinator-v1.log: onafhankelijk 162 failed.
wp1-groen-v1.log:162 passed; tests/fixture bytegelijk aan RED.
wp1-coordinator-groen-v1.log:282 passed inclusief 120 bestaande contract-/O1-/INT-03-service-tests.
wp1-groen-lint-v1.log; wp1-groen-extra-controles-v2.log.
Uitvoerdersrapporten rood/groen staan gecommit in dit dossier. Claude-sessie177f1484-4e5c-482e-b431-450befdab835. Lokale hooksymlink buiten deze commit is geen productcode.

## Reviewdoel
Beoordeel correctheid t.o.v. geaccordeerd intern contract, voldoende betekenisvolle tests, gesloten uitvoervalidatie, echte citaatposities, alle statuspaden, scoreloosheid, metadata/versiebinding, historische afwijzing, behoud exacte input. Bekijk of groene tests wezenlijke fouten missen. Semantische modelkwaliteit, opslag en appintegratie zijn expliciet latere pakketten, rapporteer hun afwezigheid niet als WP1-fout.

Aandachtspunten uit coördinatorlezing (onderzoek onafhankelijk, neem niet als bewezen bevinding over):
1. Kan een grondverwijzing naar een leeg begrip of een lege bron zonder citaat toch een pass/fail dragen? Contract zegt herleidbare grond; toets concrete invoer.
2. Opeenvolgende str.replace voor meldingssjablonen: blijven citaten en vragen letterlijk als invoertekst zelf placeholdertekens bevat (zoals {grond})?
3. Is niet-herleidbare of corrupte replay werkelijk error zonder onverwachte exception; vermijd hypothetische securityclaims over willekeurige in-process objectmanipulatie.

Vul alleen concrete bevindingen met prioriteit, exact bestand/regels, reproducerende invoer/trace, gevolg en gewenste correctie. Geen stijlpolish, onnodige architectuur of algemene heranalyse. Bij geen findings expliciet noemen wat gecontroleerd is en bewijsgrenzen.

Je mag offline tests en eigen tijdelijke probes uitvoeren; schrijf eventuele proefcode alleen in /private/tmp en rapporteer het commando. Geen netwerk, productiedata, .env, CLIdelegatie, gitmutaties of Actions. Testpython:
 /Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python
pytest tests/unit/domain/test_def835_int02_contract.py -o addopts= -q -ra.
tests/conftest.py activeert de offline-bootstrap. Andere probes eveneens offline en zuiver domein.

Controleer je feitelijke toolinventaris: native multi_agent staat uit, agents.enabled=false en alle geconfigureerde MCPservers zijn voor deze sessie uit. Als toch delegatietools beschikbaar zijn, rapporteer dit en gebruik ze niet. Vermeld model/redeneerinstelling indien zichtbaar; verander die niet.

Eindantwoord Nederlands, compacte bevindingen plus oordeel: WP1 gereed of concrete correcties vereist. De coördinator bewaart je volledige antwoord in het dossier; je hoeft niets in de implementatiewerkboom te schrijven. Rapporteer base/head en eigen testuitkomst. Stop na review.
