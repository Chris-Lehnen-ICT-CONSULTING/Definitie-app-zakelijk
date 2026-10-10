# Matrix wet- en regelgeving × rechtsgebied — concept v1 (DEF-846)

10 oktober 2026 · opgesteld door Cowork · ter review (Codex) en daarna ter vaststelling door Chris. Niet vastgesteld.

## Kader (besluiten Chris, 9–10 oktober 2026; zie Linear DEF-846 en DEF-847)

- Eén lijst: de keuzelijst "wettelijke basis" en de bronbibliotheek gebruiken dezelfde lijst, als uitbreiding van `config/bronnenlijst.yaml`.
- Bronselectie volgt de gekozen context: gekozen wettelijke basis → alleen passages uit die regelingen. Geen wettelijke basis gekozen → de regelingen van het gekozen rechtsgebied volgens deze matrix.
- Een combinatie wettelijke basis × rechtsgebied die niet in de matrix staat, krijgt een waarschuwing (niet blokkeren). Geen derde stand en geen lijst met verboden combinaties.
- Regeling zonder bibliotheekcollectie blijft kiesbaar als context; levert alleen geen bibliotheekpassages.
- Burgerlijk Wetboek per boek kiesbaar; voorlopig Boek 1 en 2.
- De huidige lijst van 15 rechtsgebieden blijft (opschonen in DEF-854): strafrecht, burgerlijk_recht, bestuursrecht, staatsrecht, belastingrecht, ondernemingsrecht, arbeidsrecht, europees_recht, internationaal_recht, migratierecht, jeugdrecht, vreemdelingenrecht, sanctierecht, penitentiair_recht, familierecht. Waar nodig krijgt een regeling zowel het hoofd- als het deelgebied.

Uitgangspunt van dit concept: een regeling krijgt haar hoofdgebied plus elk deelgebied waarvoor zij een eigen, wezenlijk deel bevat.

## In de bibliotheek (collectie in `config/bronnenlijst.yaml`)

| # | Sleutel | Label keuzelijst | Rechtsgebieden | Motivering |
|---|---|---|---|---|
| 1 | sr | Wetboek van Strafrecht | strafrecht, jeugdrecht, sanctierecht | Jeugdstrafrecht (art. 77a e.v.); straffen en maatregelen |
| 2 | sv-geldend | Wetboek van Strafvordering (huidig) | strafrecht, jeugdrecht, sanctierecht | Strafprocesrecht; jeugdzaken; tenuitvoerlegging (Boek 6) |
| 3 | sv-nieuw | Wetboek van Strafvordering (toekomstig) | strafrecht, jeugdrecht, sanctierecht | Idem, nieuw wetboek (Stb. 2026, 56 en 57; beoogd i.w.t. 1-4-2029) |
| 4 | gratiewet | Gratiewet | strafrecht, sanctierecht | Gratie betreft opgelegde straffen |
| 5 | pbw | Penitentiaire beginselenwet | penitentiair_recht, strafrecht, sanctierecht | Tenuitvoerlegging vrijheidsstraffen |
| 6 | reclasseringsregeling | Reclasseringsregeling 1995 | strafrecht, sanctierecht | Reclassering bij strafrechtelijke sancties en toezicht |
| 7 | wet-ro | Wet op de rechterlijke organisatie | staatsrecht, strafrecht | Organisatie rechtspraak; Titel IV Openbaar Ministerie |
| 8 | wpg | Wet politiegegevens | strafrecht, bestuursrecht | Politietaken omvatten ook openbare orde en hulpverlening |
| 9 | wjsg | Wet justitiële en strafvorderlijke gegevens | strafrecht | Volledig strafrechtelijk |
| 10 | uavg | Uitvoeringswet AVG | bestuursrecht, burgerlijk_recht | Geldt voor overheid én private partijen; niet strafrecht |
| 11 | avg | Algemene verordening gegevensbescherming | europees_recht, bestuursrecht, burgerlijk_recht | Niet strafrecht: art. 2 lid 2 onder d AVG |
| 12 | awb | Algemene wet bestuursrecht | bestuursrecht | — |
| 13 | wdo | Wet digitale overheid | bestuursrecht | — |
| 14 | bsdo | Besluit Sturing Digitale Overheid 2022 | bestuursrecht | — |
| 15 | tbdto | Tijdelijk besluit digitale toegankelijkheid overheid | bestuursrecht | — |
| 16 | wet-brp | Wet basisregistratie personen | bestuursrecht | — |
| 17 | wabb | Wet algemene bepalingen burgerservicenummer | bestuursrecht | — |
| 18 | handelsregisterwet | Handelsregisterwet 2007 | ondernemingsrecht, burgerlijk_recht | Inschrijving ondernemingen en rechtspersonen |
| 19 | eidas | eIDAS-verordening | europees_recht, bestuursrecht, burgerlijk_recht | E-identificatie bij overheid; e-handtekening bij contracten |
| 20 | bw1 | BW Boek 1 – Personen- en familierecht | burgerlijk_recht, familierecht, jeugdrecht | Kinderbeschermingsmaatregelen in Boek 1 |
| 21 | bw2 | BW Boek 2 – Rechtspersonen | burgerlijk_recht, ondernemingsrecht | — |

## Kiesbaar zonder bibliotheekbron (nu in `WET_OPTIONS`, zonder collectie)

| # | Label | Rechtsgebieden | Motivering |
|---|---|---|---|
| 22 | Wetboek van Burgerlijke Rechtsvordering | burgerlijk_recht | — |
| 23 | Vreemdelingenwet 2000 | vreemdelingenrecht, migratierecht, bestuursrecht | Overlap vreemdelingen-/migratierecht (DEF-854) |
| 24 | Wet op de identificatieplicht | strafrecht, bestuursrecht | Toonplicht (art. 447e Sr) en identificatie bij overheid |
| 25 | "Uitvoeringswet EU-richtlijnen" | ? | Bestaat niet als één wet; betekenis navragen bij Chris |
| 26 | EVRM | internationaal_recht, strafrecht, bestuursrecht, burgerlijk_recht, staatsrecht | Breed toepasselijk (art. 5, 6, 8) |

## Open punten voor Chris

1. Wat is bedoeld met "Uitvoeringswet EU-richtlijnen" (specifieke wet, of uit de keuzelijst)?
2. Zonder gekozen wettelijke basis mengen huidig en nieuw WvSv weer via het rechtsgebied strafrecht. Voorstel: `sv-nieuw` markeren als "alleen bij expliciete keuze" (telt niet mee via rechtsgebied).
3. Wet RO en EVRM: smal (meer waarschuwingen) of breed (vaker doorzocht zonder gekozen wet)?
