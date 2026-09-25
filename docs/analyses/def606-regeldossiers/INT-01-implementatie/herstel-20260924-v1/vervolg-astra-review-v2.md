**Geen bronvrijgave: R1 en R2 blijven Important, beide fix-nu.**

1. **R1/T20 — dezelfde bewijsfout blijft bestaan.**  
   Repro: `kaart met de titel ‘Wie woont hier?’ waarop staan aanwijzingen` krijgt **zinsstructuur-pass**, zonder onzekerheidsdeel. [zinsgrenzen.py:624](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:624) accepteert `aanwijzingen` als werkwoord vanwege de uitgang `-n`; [regel 651](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:651) accepteert `staan` als naamwoordkern. Daarmee is geen betrekkelijke bijzin bewezen.  
   **Dispositie:** open, fix-nu. De eerdere exacte repro’s zijn hersteld, maar de morfologische vervanging sluit de oorzaak niet. De gedocumenteerde beperking is geen waiver. Met dit bewijs kan positieve T20-herkenning niet verantwoord worden vrijgegeven; historische labels blijven intact. Vereist is onderscheidend bewijs voor de woordrollen, niet nog een uitgang of uitzondering.

2. **R2/T24 — onderdrukking en vervangende melding hebben verschillende voorwaarden.**  
   Repro:  
   `Bak voor onderdelen met een vakcode (v.qr. = vakcodering voor quicksortering)v.qr. bepaalt het sorteervak`  
   
   Zonder spatie na `)` ontstaat **zinsstructuur-pass**, ook via `bouw_beoordeling`. [Regel 475](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:475) onderdrukt de afkortingsmelding; de vervangende detectie op [regel 493](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:493) vereist echter `\s+`. Er dekt dus geen melding de overgang.  
   **Dispositie:** open, fix-nu. Onderdruk uitsluitend wanneer dezelfde concrete overgang daadwerkelijk door een vervangende onzekerheidsmelding wordt gedekt. Met spatie behoudt oorspronkelijke T24 nu correct één aansluitingsmelding; de eerdere latere-afkortingsrepro blijft onzeker en de gecontroleerde duidelijke grens blijft fail.

Beoordeeld: uitsluitend classifier, vervolgtest en toetsregelsreferentie. Generatie en andere skillteksten zijn bytegelijk; hun eerdere beoordeling blijft gelden. De skillsformulering over positieve herkenning onderbouwt de foutieve codebeslissing niet.

Bewijs gelezen: **10 RED/344; GREEN 344/344; regressie 1164 geslaagd, vijf skips; gepinde Ruff/Black groen.** Zelf negen korte classifierproeven en één opslagvormproef uitgevoerd. Geen brede suite; de brede v1-gate geldt niet als v2-gate.

Bases en patchinhoud gecontroleerd; manifesthashes vóór/na gelijk:

- Appbase: `7ee7d7d293770dd86f2dd70f1b4945b25ead3c94`
- Skillsbase: `ed0fcfdcc169c37058f0436fc92c1e07752366b8`
- Appdiff: `96a55efa472ebbafa65ba0db28fd794fddbff1cd0783ae648470f64408862fb6`
- Skillsdiff: `5254352510e5dfb8f271e69d745e73c64c4e3c095982008440e8926ea4d30de0`

Geen edits, nieuwe proefinhoud, modelcalls of effectclaim.