# ESS-05 — beperkt bewijscontract `ess05-bewijsregels/5` (DEF-768): delta op v4

**Status:** mechanisme voor een begrensde mechanismeproef, niet actief in de standaard ESS-05-keten. Geen appgarantie.

Dit is uitsluitend een delta. Alles wat hier niet staat, is gelijk aan [v4](ess05-bewijsregels-contract-v4.md). v4 blijft ongewijzigd als historie (sha256 `c67a487abf5bb7b70b49bf7f515926cc0f1733533bf84b31cd9ce8c773e78030`).

**Grondslag:** `logs/def768/bewijsregels-r16-herstelreview-result-v1.md`, bevinding R16-H-01 (Important, fix nu). De naamrestrictie van v4 had twee problemen:
- zij weigerde een geldige overlappassage die beide begrippen noemt ("een werknemer kan ook lener zijn");
- zij verwarde een samengestelde begripsnaam ("Uitleenovereenkomst") met een kortere ("uitleen") via prefixmatching.

| Onderdeel | Versie |
|---|---|
| Regelversie | `/4` → `ess05-bewijsregels/5` |
| Prompt | `/2` → `ess05-interpretatie-prompt/3` |
| Schema, render, lokale controle (R15-gepind) | ongewijzigd |

## Gewijzigd: §3 punt 2, onderwerpbinding (tekstanker)

- Noemt een bron (`source:…`) meer dan één geregistreerd begrip, dan bevat een broncitaat voor onderwerp X de naam van X als **heel woord** (hoofdletterongevoelig). Anders volgt een `onderwerpfout`.
- **Vervallen:** het v4-verbod op een andere geregistreerde begripsnaam in het citaat. Een tweede begripsnaam mag erbij staan.
- **Vervallen:** prefixmatching. "uitleen" telt niet als vermelding in "Uitleenovereenkomst", en omgekeerd blijft "Uitleenovereenkomst" een geldig anker voor zichzelf.
- **Ongewijzigd:**
  - precies één letterlijke vindplaats (`citaatfout` gaat voor);
  - toegestaan materiaal per onderwerp;
  - volledige bronscope en context in de controlepakketten (v4 §5);
  - een Verhuur-passage zonder het woord "uitleen" blijft geweigerd als Uitleenbewijs.

**Garantiebeperking.** De naam is uitsluitend een tekstanker. Dat een citaat het woord X bevat, bewijst niet dat het inhoudelijk over X gaat. Een passage die beide begrippen noemt, gaat daarom door naar de semantische controle. Of die controle verkeerde toeschrijving herkent, is modelafhankelijk en niet bewezen. Verbuigingen zoals een meervoud tellen niet als vermelding. Een bron die een begrip alleen verbogen noemt, kan zo onder de drempel "meer dan één begrip" blijven, waardoor de ankereis daar niet geldt.

## Gewijzigd: prompt /3

- **Vervallen:** "en zonder de naam van een ander begrip".
- **Nieuw:** de passage bevat de naam van het onderwerp als heel woord en gaat inhoudelijk over dat onderwerp; de naam alleen is geen bewijs.
- De overige instructies van /2 blijven gelijk: bepaling, precies één keer, verwijzingszin meenemen, niet inkorten tot woorden die elders staan.

## §7: aanvulling op de garantietabel

| Wat | Hoe | Garantie |
|---|---|---|
| Citaat noemt het eigen onderwerp als heel woord (bron met meerdere begrippen) | vaste code | deterministisch, alleen als tekstanker |
| Citaat gaat inhoudelijk over dat onderwerp; een tweede genoemd begrip is niet het bedoelde onderwerp | geïsoleerde LLM-controle | niet bewezen |

**Historie.** De R16-proef (v3) blijft 0/3 mislukt; invoer, uitvoer, freeze en grootboek zijn ongewijzigd. Gedrag van het model onder prompt /3 is niet getest.
