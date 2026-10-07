# INT-02 O2 — uitslag kwalificatieproef v7, fase 2 (ontwikkeling)

7 oktober 2026. Vastgelegd door Claude uit de bewaarde proefbestanden in `kwalificatieproef-v7/` (`ontwikkeling-resultaat.json`, `ontwikkeling-bundel.json`, `grootboek.jsonl`, `ontwikkeling-afronding.voltooid`). Er is geen nieuwe call gedaan en er is niets opnieuw gedraaid. Alleen regressie- en ontwikkelgegevens zijn gelezen; de hold-out is niet gedraaid en niet ingezien.

## Kader

- Manifest v7 (`872482f4…`), akkoord v7 (`d3c6ac8c…`), identiteit `1ba9794f…`, gevallen `af1ab46c…6953`; dezelfde keten als fase 1: `claude-opus-5`, prompt `def835-int02-prompt/4` (met schemaroute), contract `def835-int02-assessment/3`, thinking uit.
- Start 16:47:03 UTC, einde 16:49:45 UTC, looptijd 161,9 s. 24 inferenties en 24 telverzoeken; geen gecachete antwoorden, geen onzekere calls, `stopreden: null`.
- Grootboek: `fase_einde` voor ontwikkeling met `bewijs_opgeslagen: true` en `mechanisch_geslaagd: false`.
- De ruwe antwoorden in de bundel komen bij alle 24 gevallen overeen met het oordeel in het resultaat (verdict, onzekerheid en passagefuncties; zelf nagelopen).

## Uitslag

**Fase 2 is mechanisch niet geslaagd: 18/24 juist, criterium minimaal 21/24 (reden runner: `te_weinig_juist`).**

| Teller | Waarde |
|---|---|
| juist | 18/24 |
| juist pass | 12/12 |
| juist fail | 6/6 |
| juist review_required | 0/6 |
| false pass | 5/12 |
| kritieke false pass | 0/6 |
| false fail | 1/18 |
| gemiste overtreding | 0/6 |
| gepaste onthouding | 0/6 |
| onterechte onthouding | 0/18 |
| technische fout | 0/24 |
| citaatfout | 0/24 |

- De dienstregel `discretie_zonder_bedoeling` is nergens toegepast (`omzetting: null` bij alle 24).
- Het model gaf in geen enkel geval `insufficient_information`; elk antwoord was `pass` of `fail`.
- **max_false_pass:** manifest v7 legt voor ontwikkeling `max_false_pass: null` vast, dus de runner telt de vijf onterechte passes niet als reden. De procesafspraak met Chris (maximaal 0 voor ontwikkeling, zie processtatus v14) is daarmee **geschonden**: 5 false passes.

## De zes foute gevallen

Alle zes hebben label `review_required` en twee of drie bronnen. Duiding (zie Patroon): **a** = bij bronnen die verschillende kanten op wijzen kiest het model één kant; **b** = het model beslist "criterium of plicht" op de zinsvorm van de kern; **c** = het model leunt op een bron die letterlijk met de kern overeenkomt.

| Geval | Begrip | Label | Uitkomst | Functie(s) | Onzekerheid | Grond | Duiding |
|---|---|---|---|---|---|---|---|
| G042 | afgeschermd proefvlak | review_required | `pass` | criterion | none | B2 (legenda veldkaart) | **a, b** — de kern volgt de plichtformulering van B1 art. 6 ("wordt … afgeschermd"); het model leest de passieve vorm als eigenschap en grondt op de classificerende legenda in B2. |
| G045 | aanvullend stuk | review_required | `pass` | criterion, criterion | non_decisive | B1 art. 9 (beide passages) | **b, c** — "is in te dienen" in een betrekkelijke bijzin gelezen als typerend kenmerk; grond is de letterlijk overeenkomende plichtbepaling B1. B2 toont dezelfde zinsvorm als plicht in andere artikelen; het model noemt geen twijfel als beslissend. |
| G047 | afmelding | review_required | `fail` (false fail) | criterion, actor_prescription | non_decisive | B2 (maandcijfers) resp. B1 §8.2 | **a, c** — het model splitst de kern: het eerste deel als criterium op B2, het tweede deel als letterlijk overgenomen protocolplicht van de coördinator uit B1, en concludeert een actorvoorschrift. |
| G060 | zelfopnemer | review_required | `pass` | criterion | none | B2 (maandrapportage) | **a, b** — B1 art. 6 formuleert het doorgeven als verplichting met gevolg bij te laat; het model kiest de tellende lezing van B2 en leest "doorgeeft" als kenmerk. |
| G070 | bemiddelingsdossier | review_required | `pass` | criterion | none | B1 §2 (registratiehandleiding) | **a, b, c** — de kern staat letterlijk in B1 als dossiersoort; de werkprocesbeschrijving B2 maakt het vastleggen tot een stap voor de coördinator. Het model kiest B1 en wijst op de "voltooide, beschrijvende vorm". |
| G076 | aanwezig lid | review_required | `pass` | criterion | non_decisive | B1 art. 2 (stemreglement) | **a, c** — de kern staat letterlijk in B1; B2 hanteert een andere maatstaf (aanwezig = in de zaal) en B3 laat het verschil zien (31 handtekeningen tegen 34 geteld). Het model ziet het betekenisverschil, maar acht het niet relevant voor INT-02. |

De false passes zijn niet kritiek: geen van de vijf heeft label `fail`.

## Patroon

1. **Strijdige bronnen (a, 5 van 6).** In vijf gevallen wijzen de bronnen verschillende kanten op (plicht tegenover classificatie, of twee verschillende maatstaven). Het model kiest steeds één bron als grond en vat het verschil niet op als reden voor `review_required`. Bij G076 benoemt het het verschil zelfs uitdrukkelijk en passeert het toch. Bij G045 is er geen tweede lezing in de bronnen; daar laat B2 zien dat dezelfde zinsvorm in de regeling als plicht dient.
2. **Zinsvorm beslist (b, 4 van 6).** "Criterium of plicht" wordt beslist op de grammatica van de kern (passief, betrekkelijke bijzin, voltooide vorm), niet op de functie van de zin in de bronnen.
3. **Letterlijke overeenkomst (c, 4 van 6).** Een bron die woordelijk met de kern overeenkomt, wordt als doorslaggevend behandeld. Dat werkt beide kanten op: bij G070 en G076 leidt het tot `pass`, bij G047 tot `fail`.
4. **Onzekerheid wordt niet beslissend.** Bij G045, G047 en G076 staat de onzekerheid op `non_decisive`; bij de andere drie op `none`. Nergens `decisive` en nergens `insufficient_information`. Contract /3 laat `non_decisive` het oordeel niet veranderen, en de dienstregel grijpt alleen in bij discretionaire `fail`-passages met de kern als enige grond, wat hier niet speelde.

Wat wel werkte: alle 12 passes en alle 6 fails juist, 0 citaatfouten en 0 technische fouten. Ook de schemaroute hield stand bij 24 calls.

**Aandachtspunt 3 (meerdere passages)** is nu wel toetsbaar: 8 van de 24 antwoorden hebben twee passages (G015, G037, G041, G046, G048, G050, G045, G047). Zeven daarvan zijn juist; G047 is fout, maar door de functietoekenning en niet door de passagemechaniek. Citaatposities en gronden waren bij alle acht geldig.

## Kosten en latentie

| | Waarde |
|---|---|
| Kosten fase 2 | US$0,88056 (24 calls, gemiddeld US$0,03669 per call) |
| Invoertokens per call | 4.979–5.570 |
| Uitvoertokens per call | 251–587 |
| Latentie p95 | 9.634 ms (G048) |
| Latentie max | 11.395 ms (G008) |
| Cumulatief v7 (fase 1 + 2) | US$0,98164, 27 calls |
| Resterend in akkoord v7 | 16 calls en circa US$11,02 (kader 43 calls en US$12) |

Kosten zijn gemelde usage × routerprijzen; geen providerfactuur. Er was geen onzekere call; reservering $0,23 per call.

## Conclusie

- **3 juist te weinig** (18 tegen minimaal 21) en **5 onterechte passes** (afspraak: 0). Fase 2 voldoet op beide punten niet.
- Het tekort zit volledig in het label `review_required` (0/6). Pass en fail zijn foutloos onderscheiden.
- De oorzaak lijkt niet technisch of contractueel-mechanisch, maar inhoudelijk: de huidige prompt en het contract geven het model geen stap om strijdige bronnen als grond voor `review_required` te behandelen.
- De hold-out is niet gedraaid. Het `.voltooid`-bestand van ontwikkeling staat er; of de runner een hold-outrun na een niet-geslaagde ontwikkelfase technisch tegenhoudt, heb ik niet nagegaan. De hold-out vraagt hoe dan ook een apart akkoord.

## Vervolgopties (ter beslissing door Chris)

1. **Prompt /5 met een bronconflictstap.** Het model eerst laten nagaan of de bronnen de kern verschillend inzetten (als plicht en als kenmerk, of met een andere maatstaf) en dat dan als `review_required` met een vraag laten melden. Raakt de promptbuilder (overleg vereist), vraagt een nieuw manifest, een nieuwe regressieronde en daarna opnieuw ontwikkeling.
2. **Contract /4 met gestructureerde bronfuncties en een mechanische review-regel.** Het model per gebruikte bron laten vastleggen welke functie die bron de kernzin geeft; de dienst zet een `pass` of `fail` om naar `review_required` als twee bronnen verschillende functies aangeven. Dat maakt de beslissing controleerbaar in plaats van afhankelijk van de modelafweging, maar vergroot het schema en de dienst.
3. **Labelherziening G047/G070 via een nieuwe freeze.** Mocht Chris de modelredenering bij G047 (actorvoorschrift) of G070 (letterlijke definitie in de registratiehandleiding) inhoudelijk juist vinden, dan kan dat alleen via een nieuwe freeze, niet in v7. Let op: herzien ná het zien van de modeluitkomst kan de labels naar het model toe trekken; dat vraagt een vooraf vastgelegde motivering. Ook met beide herzien blijft het 20/24, dus onder 21.
4. **max_false_pass 0 in het volgende manifest** voor ontwikkeling, zodat de runner de afspraak zelf handhaaft in plaats van een handmatige toets achteraf.

De opties zijn combineerbaar; 4 past bij elk vervolg.

## Open: inhoudelijke beoordeling

De inhoudelijke beoordeling van passagegronden, normgrond en relevantie van de vraag staat in `ontwikkeling-resultaat.json` op `open`; de runner vult die niet in. Dat geldt ook nog voor fase 1 (zie `kwalificatieproef-v7-uitslag-v1.md`).
