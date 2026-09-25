**T20’s dekkingsblok is correct geadresseerd door Chris’ expliciete beleidsbesluit.** De automatische doorverwijzing is nu gewenst beleid; normatieve pass blijft mogelijk. Geen retroactieve labelaanpassing of taalzekerheidsclaim. R1/T22 en de eerdere generatiebronreview blijven gesloten binnen hun scope.

**Eén LOW-bevinding — fix-nu:** de nieuwe [testassertie op regel 157](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/tests/unit/validation/test_def770_restherstel_zinsgrenzen.py:157) controleert `sentence_status` tegen `REFERENTIE_NORMATIEF`, terwijl de normatieve as `normative_sentence_status` heet. Daardoor zou uitsluitend een gewijzigde normatieve referentie onopgemerkt blijven. Controleer het normatieve veld; behoud desgewenst een afzonderlijke assertie voor het historische automatische label. Dit is een bewijsfout, geen runtimeblocker.

Verder bevestigd:

- Alleen de resthersteltest en toetsregelsreferentie verschillen van v2; productcode, prompts en contract `/7` zijn gelijk.
- Alle 18 historische/producthashes zijn ongewijzigd. Oude labels en de ontwikkeluitslag **23/24** blijven intact.
- Skills scheiden norm en automatische dekkingsbeperking correct.
- Finale gerichte test: **440 passed, geen skips/xfails**; lint groen. Brede v2-gate **7443 passed/75 skipped/3 xfailed** blijft samen met deze gerichte controle bruikbaar.

Bases en volledige patchdekking gecontroleerd; geen drift:

- Appbase: `e38ad95796fea35154482da8d8568e3663be4c36`
- Skillsbase: `a048806c67a441103a2d229d0247f3c8c26f326b`
- Appdiff SHA256: `08ededd2cbbee73ea5f2670136e1abcaf7a5eafe50755a995b691f9c7e1ad256`
- Skillsdiff SHA256: `b02a6276a3e16208e7ed61a0cc7c070bee75ae702f4ec86cde3e1b9408ddaa0f`

Geen nieuwe functionele blocker. Bundelcontrole blijft bij root. Geen acceptatie- of effectvrijgave; geen edits, betaalde calls of nieuwe proefdata gelezen.