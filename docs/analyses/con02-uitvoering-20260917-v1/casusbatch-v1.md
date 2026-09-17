# Eerste casusbatch — technische uitvoering

Uitgevoerd via bestaande validatieservices op appcommit `d17ea9c30915452914e450be315620e314c03468`. Alle 31 scenario-inputhashes zijn gereproduceerd. Dit bewijst invoeridentiteit; de omzetting naar appcontext en bronobjecten kent de hieronder genoemde beperkingen. Geen deskundige oordelen ingevuld.

## Zes echte AI-aanroepen

| Casus | Brongezag | Betekenissteun | Verwijskwaliteit | Technische status |
|---|---|---|---|---|
| C02-P01 | pass | pass | pass | assessed |
| C02-P02 | pass | fail | pass | assessed |
| C02-P04 | pass | pass | pass | assessed |
| C02-P11 | pass | fail | review_required | assessed |
| C02-P16 | — | — | — | error |
| C02-P31 | pass | pass | review_required | assessed |

Dit zijn gerapporteerde modeloordelen, geen definitieve deskundige of casusacceptatie. P16 eindigde na 45 seconden met een timeout; dat is geen semantische afkeuring. Positieve verwijsoordelen zonder link zijn geraakt door DEF-806.

## Reikwijdte van de overige 25 casussen

- 3 hergebruik-/cacheprobes: P25, P26, P27; deze bewijzen geen volledige opslag-, UI- of exportflow.
- 2 validatieprobes: P03 en P28; bronloos/mislukte aanvoer levert geen betekenisacceptatie op.
- 18 transportvoorbereidingen: geen volledige inhoudelijke beoordeling. Voor RAG en andere contractrecords zijn bronobjecten deels uit het dossier samengesteld; dit is geen live retrievalbewijs.
- P13 geblokkeerd: echte indexering en retrieval van het bedoelde lid ontbreken.
- P24 geblokkeerd: een echte deskundige beoordeling van het origineel ontbreekt; een fictief akkoord is niet gebruikt.

## Grenzen

De contexttekst is technisch gemapt op `juridische_context`; het is geen bewijs dat alle oorspronkelijke contextprecondities via de UI zijn ingericht. De uploadroute gebruikt de bestaande documentprocessor en fragmentselectie; een helper roept ook private selectiecode aan. RAG-/contractobjecten zijn deels geconstrueerd. `used_in_prompt` in zo’n object is op zichzelf geen bewijs van een echte generatieprompt. De aparte browserprobe bevat wel een echte generatieprompt en opgeslagen kwitanties.

De volledige casussen vereisen nog de specifieke invoer-/mutatie-/opslag-/readback-/exportstappen en menselijke beoordeling waar voorgeschreven. Geen pass-rate voor de 31 casussen berekend. Ruwe resultaten: `cli-bewijs/runmatrix-ruw.json`.
