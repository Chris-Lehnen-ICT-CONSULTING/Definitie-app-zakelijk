**T17 is een bevestigde Important-dekkingsafwijking. T24-acceptatie blijft open binnen DEF-770; geen waiver.** De eerdere bronvrijgave blijft geldig binnen haar beoordeelde scope.

- **Bewijs:** beide onafhankelijke referenties en de [adjudicatie](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-restherstel-20260925-v1/t24-adjudicatie-v1.json:215) verwachten normatief én automatisch `pass` voor:  
  “bord met de tekst ‘Ga verder!’ dat tijdens een oefening een vrije doorgang markeert.”  
  Beide laadpaden en opslag leveren `review_required`, met passage “tekst ‘Ga verder!’ dat tijdens een oefening”.
- **Oorzaak:** [zinsgrenzen.py:599](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:599) beschermt een citaatvoortzetting via voorzetselgroepen of een **vóór** het citaat geopende bijzin. T17 voldoet aan geen van beide; de dat-bijzin begint erna. Daardoor volgt de onzekerheidsroute op regel 610. De eerdere beleidsbesluiten dekken deze constructie niet.
- **Afbakening:** schrijfvrije reproductie bevestigt dit. Zonder het interne uitroepteken volgt zinsstructuur-`pass`. Dezelfde afwijking bestaat op base `e38ad957…`; de uitvoerbare citaatslotlogica is AST-gelijk. Dit is dus nieuw aangetoonde ontbrekende dekking, geen nieuwe regressie door het laatste herstel.

**Herstelrichting:** een kleine, aantoonbaar veilige correctie is hiermee nog niet vastgesteld. Alleen `dat` herkennen volstaat niet: “... ‘Ga verder!’ dat markeert tijdens een oefening een vrije doorgang” kan juist een zelfstandig vervolg zijn. Het onderscheid vraagt bewijs van de bijzinstructuur; woorduitgangen of veronderstelde grammaticale correctheid lossen dat niet op. Geen nieuwe ad-hocheuristiek aanbevolen. T17 blijft open totdat herstel voldoende is onderbouwd of Chris afzonderlijk beleid vaststelt; historische labels blijven intact.

De overige **23 gevallen** sluiten ook inhoudelijk aan: redenen, relevante grenspassages en broncitaatstatus gecontroleerd, geen aanvullende afwijking gevonden. T14 behoudt dezelfde grens met genormaliseerde regelomloop; T19 houdt broncitaat afzonderlijk open. Onafhankelijk nagerekend:

- 23/24 zinsstatussen conform: 12 pass, 7 fail, 4 review, 1 niet beoordeeld.
- 19/19 automatische pass/fail-beslissingen normatief ondersteund.
- Beide laadpaden en opslag 24/24 consistent; tekstbinding behouden.
- Geen uitvoeringsfouten of volledige INT-01-passes; compactheid en begrijpelijkheid afzonderlijk open.

Beide seals, bronfreeze, bronbinding en archiefbinding kloppen. Bronhashes zijn na controle onveranderd. Beoordeelde commit: `108f38a3933cfe1335908d77a1aaadf0f8f36cc3`.

Classifier-SHA256: `7f1216d3825caec0beca7f405a0931ecf9e7dbd26f8f41b3630e984665574bb0`  
T24-resultaat-SHA256: `14ddebf0ef32544d9a816d640090ebb59e54a6ec1849ec6fe4773b037ebb054e`

Alleen gerichte schrijfvrije probes uitgevoerd; geen suite herhaald of bestanden gewijzigd. Geen effectvrijgave. G24 is niet ingezien en blijft onafhankelijk open.