# Deterministische batchindeling

## Trust anchors

- Review-base: `b958ddb139b4754d1644ca4b4f22b1683d8ad108`
- Scopefreeze: `5d2e2e839833487d07f2840b43d6d77fdc085b51`
- Inventorytooling: `c514f81d517dac0471bbf4c1a302a5be406193bf`

## Resultaat

- 184 batchmanifesten: `BATCH-001` t/m `BATCH-184`;
- 1.884 unieke tracked bestanden;
- 1.904 exacte line-owner-ranges;
- 10.581 exacte symbol-owner-rijen;
- 12.485 membershiprijen totaal;
- geen line- of symbolgaten en geen overlap;
- maxima: 29 bestanden, 6.000 regels en 150 symbolen per batch.

Codebatches met tier A, B of C blijven binnen 20 bestanden en 4.000 regels.
Data-/documentatiebatches met uitsluitend tier D, E of F blijven binnen 30
bestanden en 6.000 regels. Iedere batch blijft binnen 150 Python-symbolen.

## Volgorde

Na de expliciete pilot worden bestanden deterministisch gesorteerd op:

1. reviewgroep uit het uitvoeringsplan (1 t/m 18);
2. codeklasse (A–C vóór D–F);
3. scope-tier A t/m F;
4. de ruwe Git-padbytes uit `path_b64`.

Greedy packing start een nieuwe batch bij een groeps-/codeklassewissel of zodra
toevoegen een file-, regel- of symboollimiet zou overschrijden. Grote
tekstbestanden worden in aaneengesloten bereiken van maximaal 4.000 of 6.000
regels gesplitst. Een symbool wordt primair eigendom van de batch die zijn
`start_line` bezit; de onveranderlijke volledige symboolrange blijft in de
symbol-owner-rij staan.

## Pilot

`BATCH-001` is vooraf en expliciet vastgezet op acht representatieve bestanden:

- `src/main.py`;
- `src/services/service_factory.py`;
- `src/database/db_connection.py`;
- `src/ui/components/definition_generator_tab.py`;
- `tests/smoke/test_critical_paths.py`;
- `tests/unit/database/test_transactie_atomiciteit.py`;
- `tests/unit/services/test_service_factory_caching.py`;
- `tests/unit/ui/test_definition_generator_tab_generation_details.py`.

De pilot bevat 2.581 fysieke regels en 119 Python-symbolen.

## Bewijscontract

`scope/batch-membership.csv` is de primaire eigendomstabel.
`scope/batch-index.csv` bevat voor iedere gebruikte batch precies één rij en
pint zowel de SHA-256 van het manifest als de canonieke, volgorde-onafhankelijke
SHA-256 van alle membershiprijen. `scope/line-coverage.csv` is gesplitst op
dezelfde line-owner-ranges en bevat het bijbehorende batch-ID.

De non-final inventoryvalidator heeft alle batchregels, object-ID's,
linepartities, symbolpartities, limieten, manifestheadings en beide hashes
zonder batchgerelateerde fout geaccepteerd.
