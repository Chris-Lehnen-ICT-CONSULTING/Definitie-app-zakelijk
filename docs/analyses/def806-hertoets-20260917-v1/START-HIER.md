# DEF-806 — herstel en hertoets

## Uitkomst

De gewone positieve CON-02-verwijskwaliteit vereist nu voor iedere dragende bewijsbron een bruikbare HTTP(S)-link. Een link van een andere bron, een exacte vindplaats of ongeldige linktekst heft een ontbrekende link niet op. Intranetlinks blijven toegestaan; publieke bereikbaarheid wordt niet gecontroleerd. De bestaande deskundige uitzondering blijft expliciet en afzonderlijk toepasbaar. Brongezag, betekenissteun en definitietekst worden hierdoor niet automatisch afgekeurd of gewijzigd.

Dezelfde controle geldt bij oude opgeslagen AI-beoordelingen, gewone menselijke correcties, uitzonderingen en de kandidatenlijst in de expertinterface. Beoordelingsprompt is `con02-assess/2`; contractschema blijft `con02/1`.

## Verificatie

| Controle | Werkelijk resultaat |
| --- | --- |
| Gerichte regressies op uiteindelijke bestanden | 48 geslaagd; `41-tests-final.log` |
| Canonieke `make test`-unitgate | 6.073 geslaagd, 75 overgeslagen, 722 buiten selectie, 1 verwachte fail, 21 subtests; exit 0 |
| `make lint` | Ruff/Black schoon; `39-make-lint-final.log` |
| Ruff op alle gewijzigde code/tests | Schoon; `40-ruff-final.log` |
| Oorspronkelijk foutrecord 4 | pass/pass/pass wordt pass/pass/review_required; vingerafdruk klopt, definitie ongewijzigd |
| Nieuwe echte generatie record 5 | Prompt /2; verwijskwaliteit open wegens ontbrekende link; vier bronfragmenten gecontroleerd in opgeslagen generatieprompt |
| Schone appherstart en editorreadback | Beide records tonen de ontbrekende-linkmelding en concrete vervolgactie |
| Onafhankelijke Codex CLI-review | P1 en P2 gesloten; geen resterende bevinding op correctiediff |

De volledige unitgate en review zijn gebonden aan `review-diff-identiteit-v4.json`. Daarna verwijderde Claude uitsluitend een ongebruikte `noqa`-comment. De coördinator controleerde dat alleen dit bestand verschilt en dat de volledige Python-AST exact gelijk blijft; zie `review-testbinding-commentcorrectie.json`. Finale hashes: `finale-code-identiteit.json`. Gerichte tests en lint zijn daarna opnieuw uitgevoerd. De bestaande waarschuwingen/skips/xfail zijn niet weggepoetst; dit is geen claim over de volledige integration-suite of de CI-coveragegate.

## CLI-rolverdeling en bewijs

- Implementatie, tests en alle correcties: Claude Code CLI 2.1.270, sessie `ee7ba796-2443-4800-af5c-d5bde77f8197`.
- Onafhankelijke read-only review: Codex CLI 0.154.0, sessie `01a0aefc-3e11-7862-9ba6-bdbab5499215`; base `d17ea9c30915452914e450be315620e314c03468`.
- Coördinator: echte browserprobe, replay, testuitvoering na de correcties, resultaatcontrole en oplevering; geen productiecode of tests geschreven.
- `codex-review-v1.md`: twee gevonden gaten; `codex-review-v2.md`: P1 gesloten, ongeldige poort nog open; `codex-review-v3.md`: laatste P2 gesloten.
- `02-RED-def806.log`: oorspronkelijke bug faalt vóór herstel. `poortcorrectie-red-green-bewijs.json`: exacte Claude-tooluitvoer met vier falende regressies vóór de poortfix en 48 geslaagde tests erna.
- `lokale-cli-logverwijzingen.json`: lokale logpaden, sessies en SHA-256. `volledige-testcontrole.json`: exacte volledige-testsamenvatting en loghash.

Bij de uitvoersessie blokkeerde logredirectie; na de pogingslimiet nam de coördinator testuitvoering en bewijsopslag over. Formatterautorisatie bleek aanvankelijk op een andere commandonaam te staan; na de exacte koppeling voerde Claude zelf Black uit. Beschermingshooks bleven actief. De vroegere lintfout en mislukte pogingen blijven in de lokale logs bewaard.

## Praktijkbewijs en grenzen

Zie `browser-hertoets-v1.md`, beide opgeslagen generatierecords, `37-replay-record4-final.json`, `38-replay-record5-final.json`, `record5-kwitantiecontrole.json` en `readback-databasecontrole.json`.

De generatie liep met de eerste patch; readback na schone herstart met de per-bron- en syntaxcorrecties. De latere poortdelta is afzonderlijk met regressies en replay op de finale code gecontroleerd. De prompt bleef tijdens alle correcties bytegelijk. Er is geen nieuwe modelcall gebruikt om de opgeslagen recordreplays te laten slagen. De oorspronkelijke AI-pass blijft als historisch, expliciet gelabeld AI-oordeel zichtbaar onder de canonieke open uitkomst; de reviewer heeft dit niet als extra blocker beoordeeld.

Tijdens recordwissel trad een autosave-RepositoryError op in de geïsoleerde testomgeving. De definitietekst en opgeslagen brondata van beide records zijn daarna exact met de uitgangsrecords vergeleken en ongewijzigd. Autosave is niet met deze fix opgelost. De tijdelijke app is gestopt; testdatabase en bewijs blijven bewaard.

## P01 en CON-02 blijven afzonderlijk open

P01 betreft de vaste zin ‘schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling’ in de context Awb/Nederlands bestuursrecht. De vraag aan Chris over betekenissteun staat nog open; er is geen deskundigenoordeel, functie of acceptatie verzonnen of opgeslagen. Brongezag en verwijzing volgen als afzonderlijke beoordelingsstappen.

Deze technische hertoets accepteert niet alle 31 casussen. DEF-743/CON-02 en acceptatie-PR455 blijven open; PR455 blijft concept. Dit dossier betreft uitsluitend DEF-806.
