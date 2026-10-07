# Onafhankelijke Codex CLI-review — INT-02 O2 prompt /2

Dit is een verse, afzonderlijke review van de concrete ongestagede diff op branch `feature/DEF-835-int02-o2` in `/Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2`. Schrijf geen code en start geen andere agents of CLI-sessies. Lees `CLAUDE.md`, toepasselijke `.claude/rules/`, `promptcorrectie-voorstel-v1.md`, `kwalificatie-uitvoeringsverslag-v2.md`, de twee gewijzigde bestanden en hun `git diff`. Chris heeft de promptbuildercorrectie expliciet goedgekeurd.

Review gericht op de volgende bewijsclaims:

1. De nieuwe promptversie is `/2`; de letterlijke `T_TEKST`, norm, schema, contractvalidatie en statusmapping zijn intact.
2. De aanwijzing voor `fail` vraagt zelfstandig dragende grond uit kern, bevestigde bedoeling, context of bronpassage en stuurt bij ontbrekende beslissende grond naar één vraag; zij mag expliciete voorschriften in de kern niet uitsluiten en mag geen onjuiste regelpoort introduceren.
3. Passage- en grondcitaatposities worden als letterlijke, nulgebaseerde en eind-exclusieve Python-codepunten geïnstrueerd; ongeldige posities worden niet lokaal gerepareerd.
4. Tests kwamen eerst rood: `promptcorrectie-rood-coordinator-v1.log` toont 5 failed / 57 passed vóór productiecode. De coördinator liet daarna 452 gerichte offline tests slagen (`promptcorrectie-groen-coordinator-v1.log`). Controleer dat tests betekenisvol zijn en geen testgeval verwijderd is.
5. Geen casushardcoding, live modelaanroep, hold-outlek, dependency, Actions-, O2-activerings-, push- of mergewijziging.

Belangrijk: lees geen hold-outinhoud en geen volledige `kwalificatie-gevallen-v1.json`, `holdout-v1.json`, `kwalificatie-payloads-*.json` of bundels die deze inhoud dragen. Gebruik alleen het reeds samengevatte C107-foutbewijs. Meld bevindingen met bestand en regel, ernst en concrete reparatie; meld ook expliciet als er geen blocker is. Geef een korte Nederlandse reviewconclusie met de grenzen van de offline tests. Geen extra live proef onder het opgebruikte v2-manifest.
