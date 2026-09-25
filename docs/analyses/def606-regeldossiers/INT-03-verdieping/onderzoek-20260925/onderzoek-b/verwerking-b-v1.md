# Verwerking door B van review A — INT-03 — v1

25 september 2026. Verwerkt: `onderzoek-a/review-a-op-b-v1.md`, SHA-256 `89fcddd3b7fdb30e4fddba13a0aaf372d5150ebecc928b89d5ab2753e08abcf5`. Beoordeeld eigen uitgangspunt: `aanvulling-b-v1.md`, SHA-256 `d791e7f7f216dc9ed04eba475ee781528379ece8e80fbae9f75bce3e2a64bb67`.

Er zijn materiële verduidelijkingen van het advies: kortere G-instructie en expliciete scheiding van uitvoerroute, zichtbare INT-03-reviewhulp en begrenzing van buurregelbewijs. Daarom volgt een volledig herzien `aanvulling-b-v2.md`. Geen v1-bestand, verwachting of gemeten uitkomst is aangepast. Geen nieuwe appproef: gerichte broncontrole op dezelfde commit volstaat.

| Punt A | Verwerking | Grond en aanpassing | Vindplaats in B-v2 |
|---|---|---|---|
| RB-01 | Overgenomen | Gedeelde normkern behouden. Instemming van onderzoekers is nog geen normbesluit; positie-/los-naamwoordeis blijft voorstel tot vervanging. | Q1 N-B1; D1. |
| RB-02 | Overgenomen | Gelezen taalbronnen blijven onderbouwing voor loos het, onbepaalde en ingesloten vormen. C kan B's broncontrole citeren, niet stellen zelf te hebben gelezen. Geen wijziging van vooraf vastgelegde E10/E11. | Q1 uitzonderingen; S9; fase-2-delta. |
| RB-03 | Overgenomen | Lemma plus kern versus kern alleen blijft expliciete keuze. B handhaaft de voorkeur voor zelfstandig leesbare kern; C's ruimere scope niet stil overgenomen. | Q1 Begrip zelf; D1; fase-2-delta. |
| RB-04 | Overgenomen | De INT-01-reactie op E01/E02 is daadwerkelijk gemeten. Gebruik als implementatiewrijving en behoud de verwijzing naar DEF-770; geen nieuw normconflict afleiden. | Q3 INT-01; Q4 B-W1. |
| RB-05 | Gedeeltelijk overgenomen | Terecht: de CON-CIRC-fails van E03/E04 ontstaan door de reeds aanwezige lemmawoorden; zij bewijzen geen door INT-03-herstel veroorzaakte fail. Het label “vervuilde INT-03-gevallen” rechtvaardigt geen schrappen/vervangen: E03 was letterlijk verplicht en beide blijven geldig voor status/signalen. Causaliteit wordt expliciet begrensd. Een latere geïsoleerde herstelproef moet term/kern zo kiezen dat de buurfout niet vooraf aanwezig is, met nieuwe ID en vooraf bevroren verwachting. | Q3 CON-CIRC-001; Q4 “Afbakening buurregelbewijs”; Q6 meetontwerp. |
| RB-06 | Overgenomen | Lege tekst blijft waargenomen review_required naast VAL-EMP-fail; gewenst not_evaluated is nog ontwerp. Technische foutgrens bestaat al los daarvan. | Q4 Statisch S4; T-B1. |
| RB-07 | Gedeeltelijk overgenomen | Korte instruction_map-kern is zinvol; lange uitleg verhuist naar het volledige skillcontract. A's absolute “UI heeft geen vraagroute” is niet met een volledige generatiedoorloop bewezen. Vraagbehoefte bestaat ook bij menselijke review/generatie, dus “uitsluitend T2” niet overgenomen. Vragen mogen niet in de definitiekern worden gestopt; publicatie vereist een afzonderlijk aantoonbaar uitvoercontract voor onvolledige betekenis. | Q5 G-B1-kern, G-B2-uitvoerroute, volledig skillblok; Q6 effectvariant. |
| RB-08 | Overgenomen | Beide opties gaan naar Chris. B kiest smalle contextvrije INT-03-instructie; C's +10K betreft een ongeïsoleerd volledig promptverschil, geen bewezen INT-kosten. Smal toevoegen is niet bewezen een architectuurbreuk. | D2; Q5 promptselectie; verwijzing BC-13. |
| RB-09 | Overgenomen | Geen hit is geen pass. A trekt zijn eigen T-b in; dit verandert B's bestaande norm niet. Voldoet/n.v.t. volgt alleen na inhoudelijke controle van de functie. | T-B1; D4; fase-2-delta. |
| RB-10 | Overgenomen | A's intrekking van zijn speculatieve het-regex raakt A's voorstel, niet een B-regex: B had geen concrete nieuwe regex voorgeschreven. Behoud dekking én ruis als te meten effecten. | T-optie 2; Q6; fase-2-delta. |
| RB-11 | Overgenomen | Bewijscontract blijft voorstel, geen huidige functionaliteit. UI-vastlegging en versiecontrole expliciet gekoppeld aan gedeelde DEF-624/626/627-route; geen schema gewijzigd. | T-B1 bewijscontract en zichtbare reviewroute. |
| RB-12 | Overgenomen | B-v2 bevat een volledig kopieerbaar INT-03-skillblok met G/T/H en adviesstatus; geen onopgeloste verwijzing naar dit onderzoek als geïnstalleerde instructie. Beide reference-vervangteksten blijven exact gegeven. | Q5 G — skillvervangingen, “Volledig te publiceren skillblok”. |
| RB-13 | Overgenomen | Geen correctie nodig: ASTRA via overgedragen raw, directe B-toegang mislukt; Ross DBT §4.3 blijft niet gelezen. Deze review maakt dat bewijs niet compleet. | Status/toegang; S1/S9; Q6 ontbrekend bewijs. |
| RB-14 | Gedeeltelijk overgenomen | Gerichte controle bevestigt codes zonder INT-03-reden in de onderzochte renderer (r. 803–808, 859 e.v.). Daarom is zichtbare UI-hulp een expliciet onderdeel. Absolute afwezigheid van iedere mogelijke opslag/weergave neem ik niet over zonder ketenproef; C erkent zelf het ontbreken van save/reload. | Q4 Review/UI; T-B1 “Zichtbare reviewroute”; Q6 gebruikersproef. |
| RB-15 | Overgenomen | 18 ontwerpgevallen plus ≥6 nieuwe afgeschermde gevallen, herhaalde gepaarde runs en blinde betekeniscontrole blijven. Geen aangetoonde winst; positieve/noisige gevallen moeten expliciet in de gebruikersproef. Eigenaar aanwijzen blijft A/Chris. | Q6 vergelijking en ontbrekend bewijs. |
| RB-16 | Overgenomen | Een generiek expertbesluit bewijst geen INT-03-specifieke, versiegebonden beoordeling. Gedeelde vervolgroute via DEF-624/626/627; feitelijke save/reload/stale-afhandeling blijft te testen. Geen bewezen totaalverlies van alle reviewdata geclaimd. | Q4 conceptopslag; T-B1 bewijscontract; Q6 transport/opslag. |

## Gerichte broncontrole en bewaarde verschillen

Herlezen op `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`: `judgment_review.py` (normale reviewuitkomst, passage-deduplicatie, foutdoorgifte), `modular_validation_service.py:1430–1483` (not_evaluated/error), `validation_view.py:803–808,859–864` (huidige presentatie), `json_based_rules_module.py` (prefixselectie/formatter) en de overgedragen scripts/resultaten. Hashcontrole bindt de versies; er is geen aanleiding de geslaagde normale serviceproeven opnieuw uit te voeren.

Niet weggepoetst door deze verwerking: de lemma-scope, de status zonder verwijzende woorden, smal of breed contextvrij promptbereik, activering van AI/herstel en gedeeld vaststel-/exportbeleid zijn keuzes voor Chris. Aantoonbare ambiguïteit blijft bij B een tekstovertreding ook wanneer de bedoelde referent voor herstel nog onbekend is. Dat is een materieel verschil met C's T-tabel; zie `review-b-op-c-v1.md` BC-08.

## Nieuwe bestanden en volgende overdracht

In deze fase worden opgeleverd: `review-b-op-a-v1.md`, `review-b-op-c-v1.md`, dit `verwerking-b-v1.md`, de volledige `aanvulling-b-v2.md` en `bewijsmanifest-b-v2.json`. Het manifest behoudt alle zes eigen v1-bestanden en bindt de nieuwe bestanden; de zelfhash staat buiten het manifest.

Naar A: eigen correcties verwerken, C-verwerking ontvangen, bron-/normkeuzes zichtbaar synthetiseren. Een latere synthesecontrole is een afzonderlijke overdracht. Geen implementatie, live modelcalls, commits, issues, andere sessies of gezamenlijke afronding.

