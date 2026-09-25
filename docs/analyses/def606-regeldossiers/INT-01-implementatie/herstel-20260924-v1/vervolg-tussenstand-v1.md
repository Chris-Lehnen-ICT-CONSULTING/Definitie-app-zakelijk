# DEF-770 — resterend herstel: tussenstand en twee open besluiten

24 september 2026. **Geen classifier- of volledige acceptatievrijgave.** Dit is de actuele uitvoering na het nieuwe gebruikersakkoord op herstel van de twee beoordelingsproblemen, betekenisverlies en onafhankelijke acceptatie.

## Afkortingsbeoordeling T24

Dezelfde Claude CLI-uitvoerder heeft de melding hersteld. Afkortingspunten binnen de verklaring gelden als intern; bij een latere vermelding blijft een mogelijke slotgrens zichtbaar. Onderdrukking en vervangende aansluitingsmelding gebruiken dezelfde concrete overgang. Nul/één/meerdere spaties, tab, newline en dubbele haakjes zijn gecontroleerd. Oorspronkelijke T24 heeft de juiste passage en aansluitingsgrond.

Dezelfde Codex CLI-reviewer (Astra/high) heeft R2 gesloten in [review v3](vervolg-astra-review-v3.md). Deze classifiercorrecties staan nog in de lokale werkboom; zij zijn niet in de afzonderlijke generatiecommit gepubliceerd.

## Titelbeoordeling T20 — echte blokkade

Na drie gerichte correctiepogingen blijft een onbewezen zins-pass mogelijk. Het tegenvoorbeeld `kaart met de titel ‘Klaar?’ waarop het werkt de deelnemers wachten` laat zien dat een lidwoordvorm plus woorduitgang geen voldoende bewijs van woordrollen is. Ook de oorspronkelijke titelzin voldoet nog niet aan de automatische pass-verwachting. Vijf strikte xfail-tests houden dat tekort zichtbaar; dat is geen waiver en geen veranderd referentielabel.

Er volgt volgens AGENTS.md geen vierde heuristische reparatieronde. Het [concrete beslispunt](titelbeoordeling-beslispunt-v1.md) ligt aan Chris voor: de nieuw toegevoegde onbewezen automatische titelherkenning verwijderen en deze gevallen inhoudelijk laten beoordelen (advies), of aanvullende taalkundige ondersteuning onderzoeken. De eerste richting verandert de gewenste automatische afbakening en vereist daarom een expliciet besluit. Historische proefdata/labels blijven onveranderd.

## Generatiecorrectie — onafhankelijk voortgezet

Afzonderlijke appcommit **`ad45a0a8af1026822d5d3ed942ca986edd11988d`** bevat alleen de generatiecorrectie, bijbehorende prompttests en bewijs. De geblokkeerde nieuwe classifier staat hier buiten. De voorrangsregel beschermt bepalende bronbetekenis tegen stijlwijzigingen; de eindcontrole toetst handelingen, relaties/richting en modaliteit. De hypothese en geconstateerde instructiespanning zijn beschreven in [de diagnose](vervolg-generatie-diagnose-v1.md). De bronreview voor dit deel is ongewijzigd geldig. Dit bewijst nog geen generatie-effect.

Skillscommit **`5c42e404adde2916e6970ac1ac22e4057ba5d62f`** bevat de overeenkomstige Nederlandse-definities-vaardigheid en haar twee bundels. Bron en bundelpayload zijn na commithook gecontroleerd. De toetsregelsreferentie en twee toetsregelsbundels wachten lokaal op het titelbesluit; geen liveactivatie onder ALG-391.

## Technisch bewijs en reikwijdte

- Eerste gecombineerde kandidaat: 7.335 unit-tests geslaagd, 75 skips, 1 xfail, 21 subtests; bronmanifest v1.
- Derde gecombineerde werkbron: **7.363 geslaagd, 75 skips, 6 xfail, 21 subtests**, exit 0. Van die zes xfail zijn er vijf de nog open T20-verwachtingen. Dit bewijs hoort bij werkbronmanifest v3, inclusief de niet-gecommitteerde classifiercorrecties; het is geen brede gate op de afzonderlijke generatiecommit.
- Laatste gerichte set: 359 geslaagd, 5 T20-xfail. Gerichte regressie: 1.179 geslaagd, 5 bestaande skips en 5 T20-xfail.
- Gepinde Ruff0.16.5 en Black groen; skillsbundels94tests en2subtests groen.

Implementatie: echte Claude Code CLI, sessie `442a98fb-a377-403f-996e-433cf4a664fc`, model claude-opus-5-5. Onafhankelijke code-review: Codex CLI gpt-6-astra/high, sessie `01a0cfac-ea05-7700-ba73-8b5659751c1c`. Volledige logs/opdrachten in `logs/def770-vervolg/`; [manifest v3](vervolg-review-manifest-v3.json) en [generatiebronbinding](vervolg-generatie-bronbinding-v1.json). Root schreef geen productcode of tests.

## Nieuwe onafhankelijke proeven

Een nieuwe Astra/high-maker heeft zonder code, eerdere uitslagen of tools 24 verse T24-gevallen en zes G24-brondossiers gemaakt. De T24-set blijft afgeschermd zolang de automatische afbakening en classifier niet vastgesteld zijn. Er is nog geen nieuwe T24-appuitvoer of referentielabeling.

Voor G24 is de afzonderlijke generatiecommit gearchiveerd. De zes nieuwe dossiers zijn bevroren; alle bronpassages zijn in beide armen aantoonbaar volledig opgenomen. Bij alle zes dossiers verschillen de oude en nieuwe prompts. De [voorbereiding](../effectproeven-vervolg-20260924-v1/g24-bronbinding-v1.json), [manifesten](../effectproeven-vervolg-20260924-v1/g24-manifest-v1.json) en [tokenraming](../effectproeven-vervolg-20260924-v1/g24-tokentelling-v1.json) liggen vast vóór uitvoering. Er zijn nog **nul betaalde generatieaanroepen** en dus geen nieuwe effectresultaten.

De 24 aanroepen kosten volgens vooraf getelde tokens en maximaal 1.000 uitvoertokens per call maximaal **US$2,5151**. Al besteed: US$3,71545; resterend onder het bestaande cumulatieve plafond van US$5: US$1,28455. Maximaal cumulatief na de nieuwe proef: **US$6,23055**. Daarom is aan Chris gevraagd het cumulatieve plafond naar US$6,50 te verhogen (US$1,50 extra). [Budgetvoorstel](../effectproeven-vervolg-20260924-v1/g24-budgetvoorstel-v1.json) is nog geen goedkeuring. De manifestwaarde binnen_plafond toetst uitsluitend de losse run aan US$5 en vervangt het cumulatieve mandaat niet.

## Exacte volgende stappen

1. Na het titelbesluit: die afbakening implementeren of het aanvullende onderzoek voorbereiden. Niet stil een vierde variant van de oude heuristiek uitvoeren. Daarna de bijbehorende review, tests, skillsbinding en onafhankelijke T24 op bevroren bron.
2. Na aanvullend kostenakkoord: goedkeuring aan de huidige manifest/count-hashes binden, 24 G24-aanroepen uitvoeren, twee onafhankelijke blinde Astra/high-beoordelingen en adjudicatie vóór deblindering. Geen model/criteria/herhalingen aanpassen om binnen budget te lijken.
3. Beide PR’s blijven concept; geen merge of liveactivatie. Vooraf bestaande G24-mislukkingen en T24-uitslagen blijven historisch bewijs; zij worden niet als uitkomst van deze nieuwe bron gepresenteerd.
