**De oorspronkelijke P2 is gesloten voor `d6be2ccd`.** De gerichte correctie voorkomt de onterechte succesmelding en herstelt de metadata in geheugen.

Bewijs: RED/GREEN-logs gecontroleerd (75 tests groen; 22 na formattering). Zelf de `PermissionError`-reproductie herhaald: **nul succesmeldingen, één foutmelding, eerdere metadata behouden**.

Eén **LOW, niet-blokkerende bevinding — voorstel: fix nu**:
- [document_processor.py:278](/private/tmp/DEF-808-809-p01-20260917/src/document_processing/document_processor.py:278) belooft “de eerdere opgave blijft gelden”. Bij een geïnjecteerde `ENOSPC` tijdens `json.dump` herstelt alleen het geheugen; de bestaande schrijver heeft het bestand al afgekapt. Mijn reproductie hield onleesbare JSON (`{`) over, naast die geruststellende melding. De drie regressies testen uitsluitend falen bij **openen**.
- Beperk de melding tot herstel **in geheugen**, zonder garantie over de schijf. Het bestaande niet-atomaire opslaggedrag verdient afzonderlijke opvolging; daarvoor vraag ik geen uitbreiding van deze correctie.

**Eindoordeel:** geen resterende blokker uit mijn oorspronkelijke P2. Volledige `make test` en browser-P01 blijven open; geen app-pass vastgesteld. Geen bestanden gewijzigd; head en schone werkboom bevestigd.