# DEF-770 — herstelanalyse v2 (na implementatie)

Vervangt uit `herstelanalyse-v1.md` alleen §1 punt 6 plus de daar genoemde "bekende grens van 6", en de bestandentabel in §4 (drie bestaande testverwachtingen worden twee). De rest van v1 blijft geldig. v1 blijft ongewijzigd staan.

## 1. Waarom punt 6 uit v1 niet is gebouwd

v1 stelde voor: zeker bij een woord van ≥ 5 letters met een klinker, gevolgd door een persoonsvorm. De coördinator wees terecht op het volgende: lengte en klinker bewijzen niet dat het om een volledig woord gaat. Bij `bericht dat door de voorz. wordt ondertekend` levert die heuristiek een zekere tweede zin op (`voorz` telt vijf letters en een klinker, `wordt` is een persoonsvorm). Dat is een vals `fail` binnen één formulering. Een bewust ingebouwde false-fail is geen herstel, dus v1-punt 6 is verworpen.

## 2. Gebouwde regel: sterker bewijs aan beide kanten

Een punt gevolgd door een kleine letter is alleen een **zekere** grens als beide voorwaarden gelden:

1. **Het woord vóór de punt is aantoonbaar een volledig woord.** Het eindigt op een productief achtervoegsel voor zelfstandige naamwoorden (`-ing`, `-heid`, `-schap`, `-iteit`, `-tie`, `-isme`, met meervoud), met ten minste drie letters ervoor (`_VOLLEDIG_WOORD`). Afkortingen breken een woord gewoonlijk af vóór zo'n achtervoegsel (`afd.`, `voorz.`, `vergad.`). Dit is morfologisch bewijs, geen lengteheuristiek en geen lijst met proefwoorden.
2. **Het vervolg is syntactisch zelfstandig.** Tot het volgende zekere zinsbegin moet het vervolg een persoonsvorm uit een gesloten lijst bevatten, en die persoonsvorm staat **niet** vooraan. Het vervolg heeft dus een eigen onderwerp (`controle … blijft`). Staat de persoonsvorm direct na de punt (`voorz. wordt ondertekend`, `vergadering. wordt ondertekend`), dan kan de tekst vóór de punt het onderwerp of een bijzin daarvan zijn, en blijft één zin mogelijk.

In alle andere gevallen blijft de oude conservatieve uitkomst staan: **onzeker**, met passage en reden.

| Geval | Uitkomst | Grond |
|---|---|---|
| T24 `bundeling. controle volgens zqv. blijft vereist` | 1 zeker, 1 onzeker (`zqv.`) | `-ing` plus eigen onderwerp vóór `blijft` |
| `bundelingen. controle blijft vereist` | zeker | meervoud `-ingen` |
| `veiligheid. toezicht is vereist` | zeker | `-heid` |
| **`bericht dat door de voorz. wordt ondertekend`** | **onzeker** | geen achtervoegsel; persoonsvorm vooraan |
| `strook voor de voorz. controle blijft vereist` | onzeker | geen achtervoegsel (niet lexicaal te scheiden van T24) |
| `bericht dat door de vergadering. wordt ondertekend` | onzeker | persoonsvorm vooraan |
| `Afgebakend object. heeft vaste vorm.` | onzeker (ongewijzigd, bestaande referentie) | geen achtervoegsel |
| `proefwand. controle blijft vereist` | onzeker | geen achtervoegsel |
| `bundeling. controle volgens protocol` | onzeker | geen persoonsvorm |
| `regeling. zie ook de bijlage` | onzeker | geen persoonsvorm uit de lijst |
| `afd. controle blijft vereist` | onzeker | afkortingsvorm |

De bestaande referentie `kleine-letter-na-punt` (`Afgebakend object. heeft vaste vorm.` → onzeker) blijft daardoor ongewijzigd. v1 wilde die referentie omzetten naar zeker; dat gebeurt nu niet.

## 3. Resterende afruil (niet opgelost)

- **Vals onzeker (conservatief, bewust).** Een volledig woord zonder productief achtervoegsel, gevolgd door een zelfstandige zin met kleine beginletter (`proefwand. controle blijft vereist`), blijft onzeker. Het signaal blijft zichtbaar; er is alleen geen zekere afkeur.
- **Resterend vals-`fail`-risico.** Een afkorting die toevallig op zo'n achtervoegsel eindigt, gevolgd door een vervolg met eigen onderwerp en persoonsvorm. Voorbeelden daarvan ken ik niet: gangbare afkortingen breken vóór het achtervoegsel af, en `ing.` staat als titel in de afkortingenlijst. Het risico is daarmee niet bewezen afwezig. Zonder woordenboek of dependency is het niet volledig uit te sluiten; bij een melding tonen passage en reden de grond.
- **Lijstgrenzen.** Het achtervoegsel- en persoonsvormbewijs is taalkundig, niet volledig. `zijn`, `was`, `wil`, `gelden` en `vormen` staan bewust niet in de lijst (dubbelzinnig).

## 4. Bestandenoverzicht (definitief)

| Bestand | Ingreep |
|---|---|
| `src/domain/int01/zinsgrenzen.py` | citaat, opsomming na `:`/`;`/`,`, label met dubbele punt, beletselteken met vervolg, kleine letter (§2), broncitaat ook bij één zin, open melding noemt het citaat, `CONTRACTVERSIE` → `def770-int01/2` |
| `src/services/prompts/modules/prompt_orchestrator.py` | `integrity_rules` altijd actief; `sam_rules` ongewijzigd |
| `src/services/prompts/modules/json_based_rules_module.py` | zonder juridische of wettelijke context alleen INT-01; aanvulling betekenisbehoud in de INT-01-instructie |
| `src/toetsregels/regels/INT-01.json` | toelichting afgestemd op de nieuwe grensregels |
| `tests/unit/validation/test_def770_herstel_zinsgrenzen.py` (nieuw) | zes gevallen met tegenhangers, onder meer `voorz.` |
| `tests/unit/services/prompts/test_def770_herstel_promptdoorwerking.py` (nieuw) | echte PromptServiceV2, vijf contextvarianten, receipt, providergrens |
| `tests/unit/validation/test_def770_int01_zinsgrenzen.py` | `ingesloten-citaat`: (0,1) → (0,0) |
| `tests/unit/services/prompts/test_def743_con02_promptnorm.py` | `integrity_rules` nu actief zonder context |

`test_def770_int01_promptnorm.py` hoefde niet te wijzigen: de splitsing op `🔹 **INT-02` levert zonder INT-02 de rest van de sectie op.

Geen effectclaim: dit document beschrijft regels en testbare uitkomsten, geen kwaliteitswinst in generatie.
