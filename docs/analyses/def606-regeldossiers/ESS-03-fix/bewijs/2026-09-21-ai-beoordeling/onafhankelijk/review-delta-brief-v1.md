Jij bent de onafhankelijke technische reviewer voor DEF-766 (ESS-03 AI-beoordeling). Je bent een verse sessie en hebt de code niet geschreven. Voer deze opdracht zelf uit; start geen agents, subagents of extra CLI-sessies. Blijf strikt read-only: wijzig geen broncode, tests, prompts, configuratie of andere repositorybestanden en maak geen commits. Doe geen echte modelcalls (geen API-aanroepen naar Anthropic/OpenAI); pytest-runs met fakes zijn toegestaan. Antwoord in het Nederlands.

## Context

Werkboom: /Users/chrislehnen/.codex/worktrees/2075/Definitie-app (je cwd). Branch feature/DEF-766-ess03-ai-beoordeling.
Base: 2c9a6e3a13afa4ecbe39163cc418e2b0f8c41644 (main na PR #465).
Te reviewen diff: `git diff 2c9a6e3a1..HEAD` — twee commits:
- 6c71bf128 feat(DEF-766): checkpoint van de implementatie (fase 1 + correctieronden 1 en 2 door een Claude Code CLI-uitvoerder), plus drie kleine coördinatorcorrecties om de pre-commit-hooks te laten slagen: hernoeming `ESS03_VERDUIDELIJKING_KEY` → `ESS03_VERDUIDELIJKING_VELD` (gitleaks-vals-alarm; JSON-veldnaam ongewijzigd), twee docstrings zonder de letterlijke tekst `asyncio.run()`, haakjes om twee f-strings (ruff ISC004).
- 0ec86aced chore(DEF-766): app-default van claude-opus-4-8 naar claude-opus-5 in ModelRouter._DEFAULT_CONFIG (opdracht van de eigenaar).

Leidende specificatie: docs/plans/2026-09-21-DEF-766-ess03-ai-beoordeling-v1.md — lees vooral het Acceptatiecontract (10 punten) en de werkpakketten. Het ongetrackte-inmiddels-gecommitte docs/adr/ADR-002-menselijke-regelbeoordeling-v1.md is een NIET-leidend, verworpen eerder voorstel.

Bewijs van de uitvoerder en eerdere reviews staat onder reports/DEF-766-AI-20260921/:
- uitvoerder/phase1-report-v1.md, correction-report-v1.md, correction-report-v2.md (rapporten van de uitvoerder; claims, geen bewijs op zichzelf)
- uitvoerder/correction-manifest-v2.json (61 bestandshashes van de staat vóór de drie coördinatorcorrecties)
- uitvoerder/exitcodes-*.json, wp*-red/green.log (RED/GREEN-logs), ontwikkelrun-v1.json en -v2.json (echte modelantwoorden op 12 resp. 8 synthetische ontwikkelgevallen, model claude-opus-4-8)
- onafhankelijk/review-phase1-v1.md (eerdere onafhankelijke Codex-review van fase 1, bevindingen R1–R9), onafhankelijk/review-development-v2.md (onafhankelijke inhoudelijke review van de 8 ontwikkelantwoorden), onafhankelijk/review-criteria-v1.md (reviewcriteria).
Volledige make-test-logs staan in /tmp/def766-ai-20260921/ (c2-make-test-2.log e.d.); je mag ze lezen.

Er bestaat een vooraf verzegelde onafhankelijke eindset van 20 testgevallen. Die is NIET aan jou of aan de uitvoerder vrijgegeven; zoek er niet naar en lees /tmp/def766-ai-independent-20260921/heldout-cases-v1.md en codex-heldout-v1.jsonl NIET.

Vaste afspraken uit het plan die je toetst: ESS-03 beoordeelt telbaarheid/identiteit op alleen aangeleverde informatie (kandidaat, bedoelde betekenis, context, bronnen); vier uitkomsten voldoet / voldoet niet / niet van toepassing / onvoldoende informatie (met precies één gerichte vraag); alle uitkomsten scoreloos (no_score); technische fout is error, nooit pass; negatieve uitkomst blokkeert vaststellen/export niet en triggert geen automatische herschrijving; geen hardcoded model, één call via AIServiceV2/ModelRouter; gesloten parser met citaatcontrole tegen werkelijk verzonden materiaal; volledige binding (kandidaat/term/context/bronnen/norm/prompt/model) bij opslag en replay; verouderde beoordeling nooit stil actueel; opslag via bestaande JSON-opslag zonder schemamigratie.

## Opdracht

1. Lees plan en acceptatiecontract. Lees de diff volledig (src/, config/, tests/, scripts/, docs/architectuur). Gebruik `git diff 2c9a6e3a1..HEAD --stat` en daarna per bestand.
2. Controleer elk van de 10 acceptatiepunten met concrete vindplaats (bestand:regel) en welk bewijs (test + log) het dekt. Label per punt: bewezen / deels bewezen / niet bewezen, met wat ontbreekt.
3. Controleer R1–R9 uit onafhankelijk/review-phase1-v1.md en A/B/C uit uitvoerder/correction-report-v2.md tegen de actuele code: opgelost of nog open, met bronplaats.
4. Controleer de uitvoeringsketen: normale generatie, losse toetsing en editor-herbeoordeling lopen alle drie door dezelfde Ess03AssessmentService (container-injectie, orchestrators, evaluatorregistratie, beide regel-laadpaden). Directe service-aanroep zonder voorbereide beoordeling → expliciet niet-beschikbaar, nooit default-pass.
5. Controleer fail-closed: parserafwijzing, ongeldige status, ontbrekende reden, verzonnen citaat/bron-id, afgekapt materiaal, caller-supplied beoordeling, stale binding, timeout, verbindingsfout. Welke test dekt elk pad?
6. Controleer niet-blokkeren op de echte policies/actieroutes (src/services/policies/approval_gate_policy.py en gedeelde actieroutes), niet alleen op een advisory-vlag; andere regels behouden hun blokkades.
7. Controleer opslag/heropenen/invalidatie met echte tijdelijke SQLite-repository: gewijzigde term/tekst/context/bron/betekenis/verduidelijking/norm/prompt/model maakt een oude beoordeling historisch, dezelfde binding maakt haar weer actueel.
8. Controleer de modelwissel (0ec86aced): is de default consequent claude-opus-5 op alle routes, wordt temperature niet meegestuurd (DEF-441/731-guard), klopt de prijstabel, en maakt de wissel opgeslagen beoordelingen met modelbinding claude-opus-4-8 correct historisch (niet stil actueel)? Zijn er nog hardcoded modelnamen in src/?
9. Controleer promptopbouw: komen verwachte labels of gronden uit fixtures nooit in de prompt terecht; is ongestructureerde inhoud als data ingekaderd (injectiebescherming); wordt het volledige materiaal (kandidaat, betekenis, context, bronnen, verduidelijking) getransporteerd.
10. Voer zelf gerichte tests uit ter verificatie waar een claim anders niet controleerbaar is, met de project-venv: `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest <pad> -q -p no:cacheprovider -o addopts=""`. Alle test_def766_*-bestanden en de golden ESS-tests zijn relevant. Draai NIET de volledige suite; de eindstandlogs volstaan als je ze plausibel vindt.
11. Maak onderscheid tussen syntactische uitvoercontrole en semantische kwaliteit: zeg expliciet wat de tests wél en niet bewijzen.

## Rapport

Lever het volledige rapport als je eindantwoord, markdown, met:
- Per bevinding: id, ernst (blokkerend / moet vóór publicatie / kan later / opmerking), vindplaats bestand:regel, trigger, impact, bewijs of ontbrekend bewijs, en dispositie-advies (fix nu / tracked issue / waiver met reden).
- Tabel acceptatiepunten 1–10 met status en bewijsverwijzing.
- Tabel R1–R9 + A/B/C met status.
- Expliciet advies: is deze code technisch gereed om de verzegelde onafhankelijke eindset (30 echte calls op claude-opus-5) te draaien — ja / nee, en welke concrete acceptatiebewijzen daarna nog ontbreken voor publicatie (merge naar main).
- Wat je zelf hebt uitgevoerd (commando's + uitkomst) en wat je alleen uit rapporten hebt overgenomen.
Geen speculatieve architectuurvoorkeuren; alleen concrete, onderbouwde bevindingen. Ontbrekend bewijs is geen bewezen runtimebug. Stop na het rapport.
