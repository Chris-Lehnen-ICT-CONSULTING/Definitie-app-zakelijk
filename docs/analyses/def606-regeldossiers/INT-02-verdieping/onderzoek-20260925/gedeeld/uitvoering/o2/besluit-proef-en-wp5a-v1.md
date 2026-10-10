# DEF-835 — akkoord op technische proef en WP5a

28 september 2026. Chris antwoordde in deze chat **“akkoord”** op de expliciet voorgelegde twee besluiten, die in het laatste eindbericht opnieuw waren benoemd:

1. `technische-modelproef-voorstel-v1.md`: bestaand Anthropic/claude-opus-5-profiel, maximaal drie synthetische inferencecalls (C105/C107/C112), maximaal drie voorafgaande tokenmetingen, 6.000 uitvoertokens/16.000 geschatte invoertokens per call, 120 seconden per call/600 seconden totaal, begroting $0,69 en plafond US$1. Geen retries, fallback of activering. De beperkingen van responsecontrole en facturering staan in de gereviewde oplevering.
2. `wp5a-integratievoorstel-v1.md`: zeven beschreven bestanden en optionele API-injectie voor aansluiting op validatieketen, met behoud van actieve O1-route. Geen opslag/schemawijziging of activering in dit pakket.

Het akkoord is voor de modelproef gekoppeld aan ongewijzigd manifest v2 (SHA-256 54c75b43b2b55a132e58a896f2d5d909bebf97b521a26ff0d77bb783a0df35c8) in `bewijs/modelproef-akkoord-v1.json`. De bronhashes zijn vóór koppeling opnieuw gecontroleerd. Dit registreert Chris' echte chatbesluit; de runner heeft geen toestemming gegenereerd.

Volgorde: echte technische proef uitvoeren en rapporteren, daarna WP5a via Claude CLI en onafhankelijke Codex CLI-review. Het profielakkoord bewijst geen inhoudelijke modelkwalificatie. Actions blijven uit; geen push/merge/activering.

De eerdere melding over twee gitleaks-false-positives is geen concreet uitzonderingsvoorstel geweest. Dit akkoord wordt daarom niet gebruikt als toestemming om de beveiligingsconfiguratie te wijzigen of de gate te omzeilen; die afzonderlijke dossiercommitblokkade blijft staan.
