# Startopdracht onderzoeker C — INT-03 — 25 september 2026

Je bent onderzoeker C in een afzonderlijke sessie (Claude Code CLI, headless). Onderzoeker A (Claude in Cowork) coördineert en doet parallel een eigen onderzoek; onderzoeker B (Codex CLI) werkt eveneens parallel en onafhankelijk. Antwoord en schrijf uitsluitend in het Nederlands.

Onderzoek INT-03 (Voornaamwoord-verwijzing duidelijk) in DefinitieAgent, zoals de regel in de app is geïmplementeerd: (1) als toetsingsmechanisme en (2) als instructie voor het genereren van definities, inclusief de skills die daarbij worden gebruikt.

Lees eerst, in deze volgorde:
1. /Users/chrislehnen/.agents/skills/toetsregel-onderzoek/SKILL.md en references/werkcontract.md, references/startopdracht.md, references/genereren-en-toetsen.md (inclusief "Effectevaluatie van de verbeterslag"). Pas die inhoudelijk toe.
2. docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925/gedeeld/feitenbasis-v1.md (sha256 c160479a…) en gedeeld/astra-INT-03-raw-20260925.txt.
3. Het historische dossier en de bronnen die de feitenbasis noemt (INT-03-v1.md + INT-03-bewijs-v1/, §INT-03 van het 7-09-dossier, INT-03.json, judgment_review.py, additional_patterns.py, json_based_rules_module.py, modular_prompt_adapter.py, integrity_rules_module.py, de skills definitie-toetsregels en definitie-nederlandse-definities in ~/.claude/skills/ of ~/.agents/skills/ of ~/Projecten/_claude-global-setup/skills/).

Controleer toegang en meld exact wat niet leesbaar is. Lees code als te onderzoeken implementatie, niet als normbewijs; gebruik geen huidige regex als uitgangspunt voor de norm.

Jouw eerste bijdrage: beantwoord Q1–Q6 uit de skill zelfstandig, met daarin expliciet:
- de gedeelde norm (ASTRA vs lokale toevoegingen in het JSON-record: "dezelfde zin of zinsdeel", "zelfstandig naamwoord", patroonlijst, type/geldigheid), toepasselijkheid en uitzonderingen (bijv. betrekkelijke bijzin "die/dat", vooruitverwijzing, bezittelijk voornaamwoord, verwijzing naar het begrip zelf);
- de veldmatrix (definitiezin, context, bronnen, ontologie, voorbeelden, tegenvoorbeelden, grensgevallen, synoniemen, homoniemen, toelichting);
- G: exacte vervangende generatie-instructietekst met vindplaats (json_based_rules_module.py instruction_map INT-03, JSON uitleg/voorbeelden, skill reference.md regel 64, nederlandse-definities reference.md regel 185);
- T: toetsinstructie/appgedrag: wat het judgment_review-mechanisme voor INT-03 nu werkelijk doet (reden = toetsvraag, signalen = patroonstrings, geen passages), wat het zou moeten opleveren (uitkomsten, meldingstekst met kandidaat-antecedenten, onderscheid overtreding / ontbrekend bewijs / beoordeling nodig / technische fout), en de opties: menselijk oordeel blijven, AI-beoordeling zoals ESS-03/CON-02, of verbeterde signaalhulp;
- H: begrensde terugkoppeling/herstel met betekenisbehoud (herhaling zelfstandig naamwoord vs herformulering; conflicten met INT-01/ARAI-05/CON-CIRC-001);
- één casusregister met stabiele IDs (prefix INT03-C-E, historische IDs niet hernummeren), per geval verwachting voor G/T/H vóór uitvoering;
- effectevaluatie: beoogde kwaliteitswinst, behoudcriteria, vergelijking vóór/na, en wat nu nog niet uitvoerbaar is (eigenaar, volgende actie, afhankelijkheid);
- concrete besluitpunten voor Chris met opties en gevolgen.

Proeven: uitsluitend kleine offline proeven met synthetische invoer en vooraf opgeslagen verwachtingen, via tests/offline_bootstrap.py en de Mac-.venv (`.venv/bin/python`); voorbeeld: docs/analyses/def606-regeldossiers/INT-01-verdieping/onderzoek-20260923/onderzoek-a/proef-v2.py. Minimaal nuttig: (a) actualiseer op commit 26f2374d wat INT-03 via ModularValidationService oplevert voor het ASTRA-paar, "regeling waarbij deze afspraak geldt", een zin met 'het' als enig voornaamwoord, en een zin zonder voornaamwoord (status, reden, signalen); (b) render de live INT-03-promptblok via JSONBasedRulesModule (met en zonder context) en bewaar de exacte tekst. Bewaar commando, commit, invoer, verwachting, werkelijke uitkomst en exitstatus. Geen live modelcalls, geen brede testsuite, geen productiegegevens.

Schrijf alleen in docs/analyses/def606-regeldossiers/INT-03-verdieping/onderzoek-20260925/onderzoek-c/: `aanvulling-c-v1.md` (het onderzoek), `casusregister-c-v1.md`, `proefverwachtingen-c-v1.json`, `proef-c-v1.py`, `proefuitkomsten-c-v1.json` en `bewijsmanifest-c-v1.json` (sha256 van je eigen bestanden). Wijzig niets anders: geen app-, regel-, skill- of configbestanden, geen bestaande onderzoeksbestanden, geen git-commits, geen issues, geen andere sessies. Lees vóór het opslaan van je v1 geen bestanden in onderzoek-a/, onderzoek-b/ of onderzoek-c/ van een ander. Meld aan het eind welke bestanden je hebt opgeleverd, wat ontbreekt en wat de volgende overdracht is. Claim geen gezamenlijke afronding.
