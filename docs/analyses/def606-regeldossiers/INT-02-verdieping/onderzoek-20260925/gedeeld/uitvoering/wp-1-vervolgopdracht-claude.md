# Vervolg WP1 — dezelfde Claude Code CLI-sessie

Jij bent de Claude Code CLI-uitvoerder. Hervat sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90 zodra toegang beschikbaar is. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Je vorige beurt stopte op de gebruikslimiet (API 429; CLI meldde reset 25-09 om 22:50 Europe/Amsterdam).

Het WP1-akkoord blijft geldig. App en skillwerkboom zijn dezelfde als in wp-1-opdracht-claude-v2.md. Lees voortgang-wp1-verificatie.md en wp1-coordinator-verificatie.log. Geen nieuwe inventarisatie of brede regressieronde: de 14 contracttests en 4 INT-tests zijn groen; exacte N/G/T/H en recordteksten zijn vergeleken. De aanpalende test_no_negative_commands_in_guide faalt identiek op de basiscommit (12 < 10); dit is geen WP1-correctie.

Rond de twee open formatteringen af met de bestaande Black-versie: tests/unit/validation/test_def771_int02_contract.py en gedeeld/uitvoering/wp1-contractopbouw.py (laatste pad onder het INT-02-dossier). Bewaar vooraf unieke herstelkopieën. Draai de gerichte contracttests met DEF771_SKILLS_ROOT expliciet naar de skillwerkboom, Ruff en Black-check opnieuw, met nieuwe logs en exitstatus. Geen tekstuele contractwijzigingen alleen om formattering te halen. Geen bestanden of testgevallen verwijderen.

Rapporteer werkelijke omvang inclusief nieuwe bestanden (git diff --stat mist ongetrackte bestanden), het aanvullende opbouwscript als bewijsartefact, contract-SHA en alle bewijsverwijzingen. Acht beoogde inhoudelijke bestanden zijn nu circa 539 toegevoegde en 10 vervangen oude regels, boven de oorspronkelijke raming; het dossier bevat daarnaast het opbouwscript. Verberg die afwijking niet en breid de scope niet verder uit.

De contracttests slaan zonder DEF771_SKILLS_ROOT tien skillcontroles expliciet over. Alleen een run mét die variabele geldt als volledig WP1-contractbewijs. Houd dit zichtbaar in de oplevering en de latere gate. Let op: de behoudtest voor required_inputs moet in WP3 gericht worden aangepast wanneer context_lists volgens akkoord wordt toegevoegd; doe dat niet nu.

Wijzig geen coördinatiedocumenten waarvan een eerdere update door de hook is geweigerd. Geen WP2, commit, push, PR, Linear-mutatie of actieve skillpublicatie. Meld WP1 terug aan de coördinator.
