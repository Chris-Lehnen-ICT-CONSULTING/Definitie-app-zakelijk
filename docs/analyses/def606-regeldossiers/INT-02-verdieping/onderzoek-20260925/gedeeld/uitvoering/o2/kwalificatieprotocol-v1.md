# DEF-835 — kwalificatieprotocol en proefmandaat v1

28 september 2026 · **voorstel, nog geen nieuw live-mandaat**. Basis: `f9bb9e6973926a3cf768995f5d879f6edfd6322d`.

## Doel en bewijsgrens

Bepalen of het bestaande scoreloze INT-02-modelprofiel de afgesproken functiegrens voldoende herkent om een afzonderlijk activeringsbesluit te onderbouwen. De eerdere driecallproef is opgebruikt: C107 gaf ten onrechte fail; C112 gaf een ongeldig citaat. Kosten waren US$0,07814 volgens gerapporteerd gebruik. Die proef kwalificeert het model niet.

Leidend: besluiten-chris-v1.md B1–B6, gezamenlijke-synthese-v5.md §2–4 en §8–10; DEF-835 en DEF-815, via Linear opgehaald op 28 september. Geen normwijziging, herstelfunctie of regelpoort.

## 1. Rollen en onafhankelijke gegevens

Chris is acceptatie-eigenaar. Zijn keuze voor beoordelaars staat nog open: twee mensen, of twee onafhankelijke CLI-sessies die uitsluitend voorstellen voorbereiden waarna Chris inhoudelijk alle labels accepteert. CLI-voorstellen zijn zonder die beoordeling geen expertgoldset. Het te kwalificeren appmodel levert nooit zijn eigen goldlabels.

Na vaststelling van dit protocol worden 40 nieuwe synthetische gevallen gemaakt; geen kopieën of oppervlakkige varianten van de 76 ontwerpgevallen. Iedere rij bevat ID, herkomst, exacte kern, begrip, bedoeling, drie contextlijsten, aangeleverde bronnen, verwacht oordeel, relevante passages en normgrond. Geen persoons- of productiedata.

| Familie | Ontwikkeling | Hold-out | Verwachte hoofdgrens |
| --- | ---: | ---: | --- |
| Begripscriterium en deterministische afleiding | 6 | 4 | pass |
| Definitie van een normatief begrip/verplichting | 6 | 4 | pass, geen signaalafkeur |
| Actorvoorschrift, procedure of discretionaire beslissing | 6 | 4 | fail met passage en grond |
| Ontbrekende of strijdige betekenisgrond | 6 | 4 | review_required, één gerichte vraag |
| Totaal | 24 | 16 | 40 nieuwe gevallen |

De verdeling is een selectieplan; labels mogen niet naar deze aantallen worden gedwongen. Beoordelaars labelen onafhankelijk zonder elkaars labels of appuitkomsten. Meningsverschillen worden vóór freeze door Chris beslist of als onbeslist uitgesloten en door nieuwe gevallen vervangen. Uitsluiting blijft verantwoord in het register.

Freeze legt inhoud, norm, labels, beoordelaars, adjudicatie, splitsing en SHA-256 vast. De coördinator bewaart hold-outinvoer en labels afzonderlijk van uitvoerdersbriefings, ontwikkelfixtures en reviewcontext. Dit is procedurele scheiding, geen technische toegangsisolatie op dezelfde Mac. Als een promptontwikkelaar/implementator hold-outinhoud ziet, vervalt die set voor onafhankelijke bevestiging. Een nieuwe set vraagt een nieuw vastgelegd manifest; het bestaande bewijs blijft behouden.

Definitieve labeldocumenten en bewijs worden versiegebonden in dit dossier bewaard. Hold-outlabels gaan nooit in een apprequest. Ontwikkelresultaten mogen alleen vóór de hold-outrun tot een nieuwe expliciet vastgelegde promptversie leiden.

## 2. Vooraf voorgestelde kwaliteitsgrenzen

Deze grenzen moeten vóór labelproductie en evaluatie worden aanvaard. Zij zijn een praktische toelatingsproef op een kleine set, geen statistische garantie.

- Eerst C105, C107 en C112: alle drie juiste uitkomst én mechanisch geldige citaten; anders stoppen en oorzaak behandelen.
- Daarna 24 ontwikkelgevallen: alle gevallen rapporteren; geen technische/citaatfouten en geen onterechte pass op een fail-geval. Minstens 21/24 juiste hoofdstatussen.
- Alleen daarna de 16 bevroren hold-outs, met één onveranderd profiel en zonder tussentijdse promptcorrectie.
- Hold-out: 4/4 overtredingen als fail, 0 onterechte goedkeuringen, minstens 7/8 toegestane gevallen als pass, minstens 3/4 onzekerheidsgevallen als review_required en in totaal minstens 14/16 juiste hoofdstatussen.
- Iedere inhoudelijke uitkomst heeft geldige passage/grond; onzekerheid heeft precies één relevante vraag. Een statusmatch alleen bewijst geen juiste redenering. Chris beoordeelt de inhoudelijke gronden tegen de vooraf geaccepteerde labels.
- Nul geaccepteerde ongeldige citaten, nul technische fouten en nul historische beoordelingen die als actueel worden toegepast. De laatste eis krijgt ook echte save→reload-tests in het opslagpakket.
- False pass, false fail, gemiste overtreding, gepaste onthouding, onterechte onthouding, onzekerheid, technische fout en citaatfout afzonderlijk met teller/noemer rapporteren.
- NE, NA, corrupte payload en historie krijgen deterministische contracttests; deze 40 gevallen claimen geen aparte statistische dekking voor NE/NA.
- Beoogde operationele grens: geen call boven 120 seconden, hold-out-p95 maximaal 90 seconden; werkelijk gemeten waarden rapporteren. Kosten compenseren geen inhoudelijk falen.

Bij een technische/citaatfout stopt de proef meteen. Bij een kritieke onterechte goedkeuring stopt eveneens de proef. Reeds gemaakte calls tellen mee; geen automatische retry. Een falende hold-out wordt ontwikkelmateriaal zodra de foutinhoud voor correctie wordt gebruikt; zij kan daarna niet opnieuw onafhankelijk kwalificeren.

## 3. Concreet voorgesteld live-profiel

| Onderdeel | Voorstel |
| --- | --- |
| Provider/model | Anthropic `claude-opus-5`, bestaand profiel; geen automatische upgrade/fallback |
| Servicetype/regio | standard/global, overeenkomstig de eerdere technische proef |
| App-aanroepen | maximaal 43: 3 bekende regressies + 24 ontwikkeling + 16 hold-out |
| Tokenmetingen | maximaal 43; officiële tokenmeting per exacte request |
| Input/output | maximaal 16.000 inputtokens en 6.000 outputtokens per call |
| Tijd | maximaal 120 s per call, 6.000 s voor alle geautoriseerde fasen samen |
| Kostenplafond | **US$12 cumulatief**, eerdere proef niet inbegrepen; vooraf reserveren, werkelijk gerapporteerd gebruik achteraf afboeken |
| Herhaling/fallback | nul retries, nul herstelcalls, nul alternatieve modellen |
| Privacy | uitsluitend synthetisch materiaal; geen tools, webophaling, productiedb of gebruikersgegevens |
| Opslag | volledige synthetische requests/responses en manifests in dit repo-dossier; geen ruwe inhoud in algemene logs; geen sleutels |
| Bewaartermijn | duurzaam versiegebonden technisch bewijs tot expliciet nieuw bewaarbeleid; niets automatisch verwijderen |

Prijsgrond, gecontroleerd 28 september 2026: [Anthropic Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview), US$5/M input en US$25/M output. Theoretische raming bij de tokenmaxima: 43 × (0,08 + 0,15) = **US$9,89**. Het hogere plafond is geen bestedingsdoel. [Tokenmetingen](https://platform.claude.com/docs/en/build-with-claude/token-counting) zijn kosteloos maar blijven een schatting. Een lokale reservering bewijst geen providerfactuurplafond; werkelijk gebruik en onverklaarde afwijkingen worden apart gemeld.

Bij nieuwe prijs/configuratie, afwijkend model/tier/geo, ontbrekende gebruiksgegevens, ongeldige binding of onvoldoende resterend budget: vóór de volgende call stoppen. Geen modelwissel naar de inmiddels aanbevolen Opus 5.5 onder dit mandaat. DEF-815/DEF-639 en productieactivering blijven afzonderlijke besluiten.

## 4. Offline voorbereidingspakket Q1

Na akkoord op dit protocol schrijft Claude de uitbreiding; Codex CLI reviewt onafhankelijk. Raming 3 software/testbestanden, 250–450 regels; geen nieuwe dependency of publiek API-contract.

Bestanden:
1. `scripts/analysis/def835_int02_modelproef.py`: de bestaande driecasusmodus en oude akkoordmanifesten behouden; een expliciet nieuw profiel voor een bevroren extern gevallenmanifest toevoegen. Geen overschrijven van oude proefuitvoer.
2. `tests/unit/validation/test_def835_int02_modelproef.py`: bestaande gevallen behouden; nieuwe grenzen en weigeringen.
3. `tests/fixtures/def835_int02_kwalificatie_runner.json` (nieuw): uitsluitend niet-goldset technische fixtures.

Eerst rood: ontbrekend akkoord/freeze; gewijzigde invoer/labels/configuratie; labellekkage in request; overschrijding calls/tokens/kosten/deadline; verkeerde fasevolgorde; kritieke fout stopt volgende call; geen hergebruik van oud driecallmandaat; dry-run blokkeert netwerk; geen retries; huidige driecasusmodus blijft gelijk.

Daarna minimale implementatie, groen en Ruff/Black. Commandopatroon vanuit werkboom:
`/Users/chrislehnen/Projecten/Definitie-app/.venv/bin/python -m pytest tests/unit/validation/test_def835_int02_modelproef.py -o addopts= -q -ra`.
Netwerk/productiedb worden met de bestaande offline-bootstrap geblokkeerd; liveproeven gebruiken uitsluitend het afzonderlijk geaccordeerde manifest. Bewaar rood/groen, concrete diff en review. Normale lokale commit met hooks; geen push.

De prompt/T-tekst wordt in Q1 niet gewijzigd. Als C107/C112 opnieuw falen, gaat een concrete correctie met vooraf vastgelegde versie naar dezelfde uitvoerder; geen automatische besteding van extra calls. Een nieuwe proef na uitputting of een extra call vraagt een nieuw begrensd mandaat.

## Aftekenpunten

- [ ] Chris kiest beoordelaars en accepteert dit protocol, de grenzen en het proefmandaat.
- [ ] Q1 offline gebouwd, getest en onafhankelijk gereviewd.
- [ ] 40 nieuwe gevallen onafhankelijk gelabeld; Chris accepteert; manifest bevroren.
- [ ] Exacte request-/bron-/configuratiehashes vastgelegd vóór de eerste call.
- [ ] Drie regressies, ontwikkeling en hold-out in volgorde uitgevoerd binnen hetzelfde plafond.
- [ ] Rapport per geval; kosten/latency; bewijsgrenzen; afzonderlijk besluit over activering.

