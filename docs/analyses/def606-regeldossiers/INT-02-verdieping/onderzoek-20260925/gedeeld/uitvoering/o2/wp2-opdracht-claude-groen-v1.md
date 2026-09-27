# DEF-835 WP2 — GREEN-opdracht v1

Jij bent dezelfde Claude Code CLI-uitvoerder, sessie 99ef6e30-cc76-445a-932d-8c8bd578b835. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies.

De coördinator bevestigt RED: 158 failed, 3 passed (eigen herhaling 1.46s, exit1), geen collectie/setupfouten. Implementatie van WP2 is door Chris geautoriseerd. Start GREEN binnen de drie bestanden uit wp2-opdracht-claude-rood-v1.md. Alle eerdere grenzen gelden. Geen commit/push. Jij schrijft/corrigeert code en tests zelf; coördinator schrijft die niet.

Leidend U/plan-v1.md WP2, akkoord-wp2-v1.md, oorspronkelijke RED-opdracht; U=docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2. Basis b56e0e225e65eac00ad73239900d2e6c1bfc2422. WP1 blijft read-only. Bewaar RED-tests inhoudelijk; format mag. Aanvullende noodzakelijke tests eerst rood, bewijs daarvan behouden.

API/mapping in wp2-claude-rood-v1.md is binnen WP2 aanvaardbaar, inclusief not_executed/RR voor blokkades vóór transport met expliciete servicereden. Geen stille pass/fail, geen gewijzigde domeincategorieën. Gevraagde model-ID uit router na vergelijking met profiel meegeven aan AIService is een gecontroleerde override, geen hardcoded model.

Besteed aandacht aan concrete beperkingen:
- AIServiceV2 retourneert aangevraagde model-ID; presenteer die NIET als providergerapporteerde modelversie. Unknown is vereist waar bewijs ontbreekt. Een mismatchcontrole op het returnmodel is slechts de gemelde AIService-ID; geen attestatie van echte provider.
- Geen modelkwalificatie verzinnen. Alleen expliciet geïnjecteerd profiel met herleidbare kwalificatiereferentie. Fake-profiel blijft testfixture. Echte smoke nog niet uitvoeren: kostenplafond gevraagd, niet beantwoord; door de gebruiker verleende toestemming voor echte calls blijft geregistreerd.
- Token/duurbudget is niet hetzelfde als monetair budget. Maak de grens in documentatie expliciet, geen kostengarantie uit ontbrekende metingen.
- Bestaande transportexceptionlogging is een concrete beperking buiten de drie bestanden. Wijzig die transportlaag nu niet. Claim uitsluitend wat je service en uitgevoerde tests bewijzen; rapporteer resterende loggingrisico's voor de keten zodat review en activering daarop kunnen beslissen. Log zelf geen ruwe invoer/uitvoer/exceptiontekst.
- Begrens antwoord vóór parsing, weiger dubbele sleutels/NaN/oneindigheden/ongeldige structuur. Parser ValueError/RecursionError leveren foutresultaat, geen ongecontroleerde uitzondering. Geen reparatie van citaatposities.
- Invoersnapshot bevat exacte tekst; privacytest moet loglek onderscheiden van de bewust bewaarde snapshot.
- Cache mag gewijzigd budget/profiel/norm/router/prompt niet passeren. Normsnapshot/dienstlevenscyclus expliciet beschrijven; geen onbewijsbare claim dat een wijziging op schijf automatisch een bestaande instance bijwerkt.

Draai GREEN op beide WP2-testbestanden, en relevante WP1 plus bestaande AI-keten/INT-03 regressies. Bewaar volledige stdout/stderr en exitcode één keer per run onder U/bewijs met nieuwe vrije bestandsnamen. Ruff (ook bestaande hookversie0.16.5 via beschikbare lokale uv-cache) en Black op uitsluitend de drie eigen bestanden. Geen dependencies installeren of upgraden. Relevante tests geen liveproviders.

Schrijf U/wp2-claude-groen-v1.md: exacte wijzigingsscope, testbewijs/commando's, statussen, model-/norm-/cache-/budgetbinding, grenzen van providerattributie en logging, resterende beperkingen. Vermijd volledige opnieuw-inventarisatie. Stop na GREEN zodat coördinator verifieert en onafhankelijke Codex-review start.

