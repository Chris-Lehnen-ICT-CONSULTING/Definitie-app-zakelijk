# DEF-770 — beslispunt na drie gerichte herstelpogingen

## Uitkomst

De herstelronde is niet vrijgegeven. Claude Code CLI implementeerde (sessie442a98fb-a377-403f-996e-433cf4a664fc); dezelfde onafhankelijke Codex CLI-reviewer (sessie01a0cfac-ea05-7700-ba73-8b5659751c1c, Astra/high) controleerde de oorspronkelijke diff en correcties. Laatste appdiffSHA256:551ea1fad26bc7c20fe7fce062c458367c7ab79d3defec522247572491743a10. De derde gerichte poging laat R1 Important open. De projectregel maximaal drie pogingen betekent: stoppen en rapporteren. Geen vierde codecorrectie uitgevoerd.

## Wat gereed is

- INT-01 komt via de echte promptketen ook bij niet-juridische context in de generatieprompt; andere INT-regels blijven hun eerdere selectie volgen.
- Generatie-instructies beschermen modaliteit, voorwaarden, negaties en antecedenten. Dit is nog geen bewezen generatie-effect.
- Oorspronkelijke regressiegevallen zijn afgedekt. De onafhankelijke review sloot de gemelde citaatfout en de IndexError bij een afgebroken vervolg binnen de gecontroleerde scope.
- Twee skillreferenties en vier distributiebundels: conceptPR356, commit0e2b5e914483800d14bdffc90be0af2a98bd999d; onafhankelijke review zonder zelfstandige skillsbevindingen,94 bundeltests,3/3CIgroen. Activatie blijft bevroren onder ALG-391.

## Concrete blokkade

`regeling. opnieuw volgens protocol wordt toegepast` en `regeling. daarna volgens protocol wordt toegepast` krijgen fail met de reden zelfstandige zin. Het vervolg bevat geen bewezen onderwerp. De helper behandelt één woord met een voorzetselgroep als onderwerp en neemt daarvoor grammaticaal correcte invoer aan. Een validator mag die aanname hier niet als bewijs gebruiken. Zie astra-correctiereview-v3.md en herstelanalyse-v5.md. Dit is een open fout onder DEF-770, geen geaccepteerde uitzondering.

## Aanbevolen vervolgbesluit

Eerst de vereiste zekerheid en de taalkundige bewijsbron expliciet ontwerpen, daarna een nieuwe implementatieopdracht. Geen volgende reeks losse uitzonderingswoorden. Twee concrete richtingen vragen een keuze:

1. **Conservatieve beoordeling:** kleine-lettergrenzen zonder aantoonbare zinsstructuur blijven review_required. Daarmee verdwijnt de te stellige afkeur, maar T24 kan dan voor sommige bestaande referenties onvoldoende herkennen. Dat blijft een gemist acceptatiecriterium totdat een expliciet nieuw besluit is genomen; geen historische referentie aanpassen.
2. **Meer taalkundige ondersteuning:** onderzoek een Nederlandse woordsoort-/zinsstructuuranalyse als bron van bewijs, inclusief fouten en terugval naar onzekerheid. Dit is een grotere architectuur-/dependencykeuze waarvoor de huidige opdracht geen invoeringsbesluit geeft. Een parser is op zichzelf ook geen zekerheid of bewezen verbetering.

Mijn voorkeur: eerst richting1 als veilig begrensd productcontract bespreken, met de huidige T24-afwijking zichtbaar. Richting2 alleen wanneer automatische afkeur van zulke gevallen werkelijk vereist blijft. Geen van beide richtingen is hier stilzwijgend geïmplementeerd.

## Bewijsgrenzen

99 gerichte regressietests en lint zijn op de laatste bron groen. Brede test-v1 had7179geslaagde tests vóór uitsluitend opmaakcorrecties; brede test-v2 op de eindbron werd beëindigd met signaal15 en bevat een nog niet geïdentificeerde F. De coördinator voert een laatste ongewijzigde hertest uit; zie de eindstatus naast dit document. De teststatus sluit R1 inhoudelijk niet.

De nieuwe onafhankelijke T24/G24-proef is niet gestart. Er zijn geen nieuwe betaalde generatiecalls gedaan. Eerdere proefbestanden en acceptatiecriteria zijn intact. De twee eerder gemergde PRs473/355 zijn niet teruggedraaid; skillsPR356 is een concept en niet gemerged.
