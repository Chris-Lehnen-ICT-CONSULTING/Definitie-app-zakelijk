# INT-01 — besluiten uitgevoerd, nieuwe acceptatie onvoldoende

25 september 2026. Leidend besluit: Chris gaf **“akkoord op beide”** voor inhoudelijke beoordeling van twijfelachtige titelvoortzettingen en een cumulatief proefbudget van US$6,50. Beide besluiten zijn uitgevoerd. **Geen acceptatie-, effect-, merge- of livevrijgave. DEF-770 blijft open.**

## Hersteld en technisch bewezen

De onbewezen positieve titelherkenning is verwijderd. De oorspronkelijke titelgevallen en eerdere vals-positieve tegenvoorbeelden krijgen inhoudelijke beoordeling met passage en reden. De afkortingscorrectie blijft behouden. Contract `/6` maakt eerdere `/1`–`/5`-beoordelingen niet actueel; app en toetsregelsreferentie sluiten op elkaar aan. De oorspronkelijke R1/R2-bevindingen zijn door dezelfde reviewer gesloten onder het expliciete nieuwe beleid.

Appbron **23cc51bfddc5ee9393dea52e6a52a55b3e65615d**, skillsbron **a048806c67a441103a2d229d0247f3c8c26f326b**, beide gepusht naar bestaande concept-PR’s 474 en 356. Generatiecorrectie **ad45a0a8af1026822d5d3ed942ca986edd11988d** is inhoudelijk ongewijzigd in de definitieve appbron; zes volledige prompts, API-verzoeken en bronontvangstbewijzen zijn exact vergeleken.

- 370 gerichte tests geslaagd; gerichte regressie 1.190 geslaagd en 5 bestaande skips.
- Volledige unit-suite: **7.374 passed, 75 skipped, 1 bestaande xfail, 21 subtests**, exit 0; bronhashes gelijk aan de review.
- Gepinde Ruff/Black en make lint geslaagd; skillsbundels 94 tests en 2 subtests geslaagd. Na commithooks beide referentiepayloads gecontroleerd, inclusief bestaande aliasnaamrewrite.
- Claude Code CLI implementeerde: sessie `442a98fb-a377-403f-996e-433cf4a664fc` (claude-opus-5-5). Codex CLI reviewde: sessie `01a0cfac-ea05-7700-ba73-8b5659751c1c` (gpt-6-astra/high). Coördinator schreef geen productcode/tests. Opdrachten, volledige logs en herstelkopieën: `logs/def770-vervolg/`; concrete diffbinding: [reviewmanifest](titelbeleid-review-manifest-v1.json).

## Nieuwe onafhankelijke acceptatie

**T24: 22/24 volledig conform.** Twee nieuwe Important-blockers, door dezelfde reviewer gereproduceerd: een nominale titelvoortzetting met een bijvoeglijk naamwoord wordt onnodig doorverwezen; het losse label schakelblad krijgt een onbewezen zinsstructuur-pass. Dit zijn andere gevallen dan de oorspronkelijke T20/T24. Beide laadpaden en opslag zijn 24/24 consistent. Geen volledige INT-01-pass. [T24-rapport](../effectproeven-vervolg-20260924-v1/t24-rapport-v1.md).

**G24: effectcriteria niet gehaald.** Twaalf paren: twee inhoudelijke verbeteringen, twee compactheidsverbeteringen, drie gelijk, twee verslechteringen en drie onbeslist. Nieuw betekenisverlies: de verplichte onvolledigheidsmarkering uit de bron verdwijnt bij één generatie. De omissie staat al in de ruwe tekst; de bron stond volledig in de prompt. Dezelfde instructies voorkomen betekenisverlies dus nog onvoldoende. [G24-rapport](../effectproeven-vervolg-20260924-v1/g24-rapport-v1.md).

Referenties zijn vóór appuitvoering en blinde generatieoordelen vóór ontblinding vastgelegd. Geen labels, criteria of historische uitslagen zijn aangepast aan de resultaten. Het betreft kleine synthetische AI-proeven, geen menselijke of algemene validatie.

## Kosten en resterend werk

Nieuwe run US$1,99915; cumulatief **US$5,7146**, binnen US$6,50. Resterend US$0,7854. Geen extra generatiecalls of herstelronde na deze proefuitslag.

De concrete restpunten zijn:

1. Positieve automatische zinsstructuurclaims bij losse labels voorkomen.
2. De gemeten beperking bij nominale titelvoortzettingen oplossen zonder opnieuw onbewezen woordrolherkenning toe te voegen.
3. Verlies van bepalende bronkenmerken bij generatie voorkomen of aantoonbaar signaleren; nog een instructietekst alleen heeft nu geen bewezen voldoende effect.

Mijn advies is deze bevindingen als grenzen van de huidige aanpak te behandelen en het vervolg daarop af te bakenen. De huidige bron en proefuitslagen blijven bevroren bewijs. Een gewijzigde kandidaat vraagt eigen passend bewijs; de twee nieuwe toetsbevindingen en het generatie-effect blijven open in DEF-770. Geen merge of skillsactivatie onder ALG-391.

Bronnen: [gebruikersbesluit](titel-en-budgetbesluit-v1.md), [bronreview](astra-titelbeleid-review-v1.md), [acceptatiebevindingen](astra-acceptatiebevindingen-v1.md), [volledige unit-uitvoer](titelbeleid-make-test-root-v1.log), [bronbinding na commit](../effectproeven-vervolg-20260924-v1/titelbeleid-bronbinding-v1.json).
