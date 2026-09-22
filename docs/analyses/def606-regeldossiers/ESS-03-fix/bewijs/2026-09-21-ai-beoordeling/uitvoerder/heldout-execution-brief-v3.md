Jij bent de Claude Code CLI-uitvoerder voor de onafhankelijke inhoudelijke eindtest van DEF-766 (ESS-03 AI-beoordeling). Voer deze opdracht zelf uit; start geen agents, subagents of extra CLI-sessies. Dit is uitsluitend UITVOERING en RAPPORTAGE: geen wijziging van broncode, prompt, norm, tests of verwachtingen. Geen commits, push of PR; niets verwijderen. Antwoord in het Nederlands.

## Vrijgave en verzegeling

Werkboom /Users/chrislehnen/.codex/worktrees/2075/Definitie-app (je cwd), branch feature/DEF-766-ess03-ai-beoordeling, HEAD `c0d3423ab` (schoon; controleer met `git rev-parse HEAD` en `git status --short` — bij een andere HEAD of ongecommitte wijzigingen: STOP en meld).
Verzegelde binding waarop de eindtest geldt (controleer ze zelf vóór en na de run, zoals `scripts/ess03/run_ess03_gevallen.py` ze berekent en in zijn uitvoer zet):
- prompt_version `ess03-assess/2`
- system_prompt_sha256 `e51d06cb3c878d78f2a66135c248e5e8d2a4e95cc589a4fed816c411b125c758`
- norm_sha256 `372bb329fa6630191cc13aaed20c715613043a4790ccb6a5dd9e01949e41e028`
- provider anthropic, model `claude-opus-5` (via ModelRouter, taak `validation`; thinking expliciet uit, temperature weggelaten)
De onafhankelijke eindset is nu aan jou vrijgegeven: `/tmp/def766-ai-independent-20260921/heldout-cases-v1.md` (sha256 `f96378d2cc5ffefe8f9db67f9d52e8a1f177747377b66726e077761d0f1f523e` — controleer met `shasum -a 256`; wijkt hij af: STOP). Bewaar het origineel onaangeroerd; kopieer het naar `/tmp/def766-ai-20260921/heldout/heldout-cases-v1.md`.

Technische rookproef vandaag op Opus 5 (2 calls, `/tmp/def766-ai-20260921/rookproef-opus5-v1.json`): antwoorden komen heel terug (`attribution.stop_reason=end_turn`, 1 poging, geldige JSON). Inhoudelijk oordeelde Opus 5 op D01 strenger dan Opus 4.8 (onvoldoende informatie i.p.v. voldoet, met een vraag naar de conventie voor het peilmoment). De eigenaar heeft besloten die strengheid te accepteren en de prompt NIET aan te passen; de eindset draait dus ongewijzigd. Verwachte labels blijven staan; jij verandert er niets aan.

## Opdracht

1. Lees `heldout-cases-v1.md` volledig. Zet de 20 gevallen HT01–HT20 zonder betekenisverlies om naar een gevallenbestand in het formaat van `tests/fixtures/ess03/ontwikkelgevallen_v2.json` (schema `def766-ess03-ontwikkelgevallen/1`; per geval: `id`, `begrip`, `tekst`, `toelichting`, `categorie`, `context` met de drie lijsten, `bronnen` met id/titel/vindplaats/versie/passage zoals het schema en de runner het verwachten — inspecteer `_bouw_aanroep`/de fixture-lezer in de runner, `verwacht` (pass/fail/not_applicable/insufficient_information), `grond`, `doel`). De exacte kandidaat, term, bedoelde betekenis, context en iedere bronpassage moeten volledig beschikbaar zijn voor het model; ontbrekende brondata niet zelf aanvullen. `verwacht`, `grond`, `doel` en test-ID's gaan NOOIT in de prompt — de runner bewaakt dat (`_controleer_afscherming`); controleer het zelf ook op de eerste gebouwde prompt vóór je calls doet.
2. Maak daarnaast: de 4 metamorfose-varianten (exact zoals de set ze voorschrijft, zelfde verwachte label, id-suffix `-M`), de 2 injectievarianten (id-suffix `-I`; verwachting: geen gefingeerd pass — leg vast wat de set als toetsbare eis stelt) en 4 ongecachete herhalingen van HT01, HT06, HT12 en HT18 (id-suffix `-R`, identieke invoer). Totaal precies 30 calls. Schrijf alles naar `/tmp/def766-ai-20260921/heldout/heldout-gevallen-v1.json` (+ een apart bestand met alleen de 20 basisgevallen als je de runner per deelset wilt draaien; het totaal blijft 30).
3. Voer uit met de productieklassen via de runner, zonder retries en zonder cache, per call max 60 s:
   `/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python scripts/ess03/run_ess03_gevallen.py --gevallen /tmp/def766-ai-20260921/heldout/<bestand>.json --uit /tmp/def766-ai-20260921/heldout/heldout-run-v1.json --max-calls 30` (of per deelset met passende --max-calls, samen ≤ 30). Draai NIET opnieuw bij tegenvallende uitkomsten. Eén technische fout (timeout, verbinding, afkapping `truncated_response`, `malformed_response`) niet als inhoudelijke fout of succes wegboeken: apart tellen. Stop bij een structurele transport-/configfout met bewijs en meld het exacte bereik. Budget: vóór deze run zijn 28 transportpogingen gedaan; met 30 is de som 58 van maximaal 60. Niet overschrijden.
4. Rapporteer in `/tmp/def766-ai-20260921/heldout/heldout-report-v1.md` en gestructureerd `heldout-results-v1.json`:
   - per klasse (pass / fail / not_applicable / insufficient_information) van de 20 basisgevallen: aantal correct, onterechte pass, onterechte fail, onnodig insufficient, technische fouten;
   - voor iedere discrepantie letterlijk: verwacht, gekregen, korte modelonderbouwing, gestelde vraag, de relevante geleverde input en de vooraf vastgelegde `grond` — zonder eigen herlabeling;
   - controle per antwoord: precies één gerichte vraag bij insufficient, citaten letterlijk aanwezig in het verzonden materiaal (de dienst controleert dit; rapporteer `rejected`/fouten), geen impliciete herschrijving van de definitie;
   - metamorfosen (stabiliteit t.o.v. het basisgeval), injecties en herhalingen apart;
   - per call: `attribution.stop_reason`, `attempts_observed`, duur, tokens/kosten waar de runner ze meldt, cached-vlag; geen sleutels;
   - hercontrole van prompt-/norm-/modelbinding uit de runneruitvoer tegen de verzegeling hierboven;
   - dit is een beperkte synthetische eindset: geen expertgoldset, geen statistische claim.
   Laat ambiguïteit van een geval door de onafhankelijke reviewer beoordelen; verander het label niet zelf.
5. Geef het volledige rapport ook als eindantwoord en stop. Geen commit/push/PR.
