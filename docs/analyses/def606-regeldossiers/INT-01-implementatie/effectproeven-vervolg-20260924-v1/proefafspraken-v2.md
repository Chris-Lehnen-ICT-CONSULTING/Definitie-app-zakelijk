# Nieuwe onafhankelijke acceptatie na resterend herstel

Uitvoeringsakkoord van Chris op 24 september 2026: twee beoordelingsproblemen herstellen en betekenisverlies bij generatie oplossen, gevolgd door nieuwe onafhankelijke acceptatie. Leidende uitvoering: ../herstel-20260924-v1/vervolg-uitvoeringsplan-v1.md.

Leidende aanvulling: Chris heeft op 25 september 2026 met “akkoord op beide” de titelafbakening en US$6,50 cumulatief goedgekeurd, vastgelegd in ../herstel-20260924-v1/titel-en-budgetbesluit-v1.md.

De inhoudelijke criteria uit ../effectproeven-herstel-20260924-v1/proefafspraken-v3.md blijven ongewijzigd. De historische datasets, labels en uitslagen blijven behouden. Bekende gevallen worden alleen voor ontwikkeling/regressie gebruikt. De nieuwe maker kent geen code, eerdere proeven of resultaten; de makeruitvoer blijft afgeschermd tot bronbevriezing en gaat niet vooraf naar uitvoerder/code-reviewer.

## T24

Precies 24 verse synthetische gevallen, vier per bestaand stratum. Nieuwe onafhankelijke maker, referentie A, referentie B en adjudicator op Astra/high. Beide assen afzonderlijk: normatieve zinsstructuur en verwachting van conservatieve automatisering. Referentie-contract-v2.md voegt het expliciete titelbesluit toe vóór onafhankelijke labeling; normatieve labels staan los van de beperktere automatische zekerheid. De v1-contracten en historische labels blijven ongewijzigd. Referenties en bron worden vóór appuitvoering verzegeld.

Acceptatie: alle 24 eenduidig conform het volledige automatische contract, nul onjuiste zekere beslissingen tegenover normatieve referentie, betekenisvolle automatische pass én fail, correcte reden/passage, beide laadpaden en opslag consistent, geen volledige INT-01-pass. Automatische dekking en doorverwijzingen met normatieve verdeling rapporteren. Een onbesliste referentie blijft zichtbaar buiten de conformiteitsnoemer; dan geen 24/24-claim. Geen labels achteraf veranderen.

## G24

Zes verse synthetische brondossiers × twee armen × twee herhalingen = 24 calls. Oude bron26f2374d302fc66fc0b12ed29dc34585f7c0a5c3; nieuwe bron wordt vóór uitvoering exact aan de gereviewde commit gebonden. Zelfde modelclaude-opus-5 en API-instellingen, bestaande bronrepresentatie met documentlimieten200fragmenten/40000tekens, fragmentmax450, maxoutput1000. Normale productieconfiguratie blijft ongewijzigd. De eerder gereviewde runners zijn bytegelijk en worden hergebruikt.

Acceptatie: minimaal één inhoudelijke verbetering, geen nieuwe bron-/betekenisfout en geen verslechtering per gepaarde invoer. Twee onafhankelijke blinde Astra/high-beoordelaars; adjudicatie vóór deblindering. Ruw en opgeschoond afzonderlijk. Geen menselijke validatie, geen algemene betrouwbaarheidsclaim en geen causale toeschrijving aan één promptzin. Wijzig de vooraf vastgelegde paren en criteria niet na het zien van uitvoer.

## Kosten en uitvoering

Goedgekeurd cumulatief plafondUS$6,50; reeds besteedUS$3,71545; restantUS$2,78455. Nieuwe run maximaalUS$2,5151; binding in g24-budgetbinding-v1.json. De maker- en referentiesessies lopen via de bestaande CLI-aanmeldingen. Voor betaalde generatiecalls: eerst concrete manifests en count_tokens-raming; alleen uitvoeren binnen het restant of na expliciet aanvullend kostenmandaat. Geen verlaging van model, herhalingen of criteria om dit plafond te omzeilen. Goedkeuring wordt apart aan de definitieve manifest- en count-hashes gebonden.

Geen merge of live skillsactivatie binnen deze proefopdracht. Als de bron wijzigt nadat de referentie/uitvoer bekend is, blijven de resultaten bewijs voor die bron; geen score overhevelen naar de correctie.
