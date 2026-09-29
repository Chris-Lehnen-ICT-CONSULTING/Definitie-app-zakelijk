# DEF-771 — INT-02-contract, O1-passagehulp en S1-signalen

Uitvoering gereed voor beoordeling in PR; onafhankelijke review afgerond en R1 gesloten. Broncode: 9ff3eac199c3eb6e77a44ee47220f91226ffed44. Geen merge of actieve uitrol.

## Besluiten en scope

Uitvoering van B1–B6 uit het afgeronde INT-02-dossier van 25 september 2026:

- B1: brede lokale norm; begripscriteria, voorwaarden, uitzonderingen en deterministische afleidingen blijven toegestaan. Een woord bewijst geen actorvoorschrift.
- B2: O1-passagehulp nu, scoreloze O2-beoordeling afzonderlijk inplannen.
- B3: zeven bestaande patronen behouden, zes expliciet goedgekeurde S1-markers toegevoegd als leeshulp.
- B4: één versiegebonden contract in beide beheerde skills, met runtimebinding en exacte G/T-teksten.
- B5: geen zelfstandige INT-02-poort; integrale expertbeoordeling en DEF-831 blijven leidend.
- B6: geen INT-02-herstelroute; H specificeert uitsluitend een afzonderlijk toelichtingsvoorstel volgens DEF-832.

## Werkpakketten

- WP1: INT-02-record met exacte norm-/toetsteksten, bronannotatie, behouden ASTRA-paar en herleidbare functievoorbeelden; contractbinding aan `def771-int02/2`. Canonieke en bytegelijke tweede skillkopie staan in de gekoppelde skill-PR.
- WP2: exacte G uit synthese §3 in JSONBasedRulesModule, met renderingbewijs met/zonder voorbeelden binnen het bestaande één-zincontract.
- WP3: volledige passagecitaten met positie, neutrale functievraag, expliciete waarschuwing zonder signaal en NE bij ontbrekende kern/context. RR blijft menselijke beoordeling zonder score. Publieke NE-doorgifte via bestaande rule_results en UI, met afzonderlijk goedgekeurd additief resultaatcontract 2.2.0.
- WP4: bestaande golden-test en runtimeprobe herijkt naar RR voor de functieafhankelijke C24/C25; test hernoemd, geen geval verwijderd.
- WP5: tests eerst rood, daarna groen per pakket; coördinatorcontrole, volledige offline suite en afzonderlijke Codex CLI-review.

## Bewijs

Dossier: `docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/`.

- WP1: RED→18 tests groen en lint.
- WP2: RED→6 tests groen; letterlijke promptrendering met/zonder voorbeelden.
- WP3: 146 tests groen, lint; `proef-c1-uitvoering-na-o1-run3.json` bewijst 36/36 verwachte route-uitkomsten met hashes na formattering.
- WP4: 437 tests groen en lint.
- Laatste versieassertiecorrecties: 57 tests groen en lint.
- Volledige pytest op appcode-HEAD 9ff3eac199c3eb6e77a44ee47220f91226ffed44, seed 20260926: **67 failed, 8215 passed, 114 skipped, 24 xfailed, 3386 warnings, 21 subtests passed in 666.76s; exit 1**. Alle 55 DEF-771-tests slagen, zonder skips. De 67 failure-ID’s zijn exact gelijk aan de vorige volledige run.
- Alle 67 failures zijn ook op basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d gereproduceerd: 66 in een gerichte selectie, de laatste via beide securitytestbestanden (gedeelde toestand/volgorde). `wp5-testbevindingen-v1.md` bevat iedere failure en oorzaak. Dit is geen identieke volledige baselinesuite en de suite blijft rood.

CLI-rollen: Claude Code CLI implementeerde in sessie `a4b588d6-e4a1-4fd6-8f80-0aac55013d90`; afzonderlijke Codex CLI-review uitgevoerd in `01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff`. Volledige prompts, logs en testbewijs staan in het dossier. Volledige review: wp5-codex-review-v2.md. R1 (onvolledige passagegrenzen) is door dezelfde Claude-sessie gecorrigeerd in 38 regels/twee bestanden en door dezelfde reviewer gesloten in wp5-codex-review-r1.md. RED 6 failed → GREEN 149 passed; lint en C1 36/36 groen. Geen open inhoudelijke reviewbevinding. Eindverificatie: wp5-eindverificatie-v1.md.

## Bewijsgrenzen en vervolg

Geen echte modelgeneratie, productiedata, menselijke beoordelaarstest of kwaliteitswinstmeting. Geen volledige UI-/opslag-/vaststel-/exportdoorloop. Het nieuwe rule_results-contractdeel is getest; de bestaande algemene violation-code-schemafout blijft expliciet gemeld.

Bewust niet uitgevoerd: O2, effectmeting, herstelroute (DEF-832), zelfstandige poort (DEF-831), issues-helper/herlaadroute (DEF-626), legacy-opruiming (DEF-830) en DEF-612-voorbeeldconflict. De CON-01-keuze in DEF-831 blijft bij Chris. Het O2-vervolgissue is na afzonderlijk akkoord aangemaakt: [DEF-835](https://linear.app/definitie-app/issue/DEF-835/story-int-02-ai-beoordeling-o2-met-goldset), Backlog; geen bouwstart.

De actieve skillversies zijn gecontroleerd maar nog niet uitgerold; de beheerde contractkopieën en Cowork-ZIP-inhoud zijn gecontroleerd. Contract-SHA-256: `bc16c128c43e247b25db996d25059af48fe56dccea5cdc4012ceb401746b043c`.

Geen merge zonder Chris. Relatie: DEF-771; gekoppelde besluiten DEF-831 en DEF-832.


Gekoppelde skill-PR: [claude-global-setup #358](https://github.com/ChrisLehnen/claude-global-setup/pull/358).

Bewijscommit: `5cf24c12c30f2cb49988b3aa350de6bcc826e354`. De gepubliceerde pytest-XML-kopieën hebben suffix `-publicatie-v1.xml`; uitsluitend verzonnen API-testwaarden in testnamen zijn afgeschermd (wp6-bewijs-publicatieredactie-v1.md). De normale secretscanner is geslaagd.
