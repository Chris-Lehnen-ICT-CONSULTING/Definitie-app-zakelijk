# WP5 — R1 gesloten door dezelfde onafhankelijke reviewer

26 september 2026. Actualiseert wp5-reviewdispositie-v1.md voor R1; O2 is inmiddels DEF-835.

R1 is gecorrigeerd door dezelfde Claude Code CLI-sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90, binnen de opdrachtgrens: twee bestanden, +28/-10, commit 9ff3eac199c3eb6e77a44ee47220f91226ffed44. Geen invoergeval verwijderd. De coördinator heeft de concrete diff en logs gecontroleerd: 6 failed/28 passed vóór productieaanpassing, daarna 149 passed, lint/make lint exit 0, C1-run3 36/36 en exit 0. De C1-metadata vermeldt de toenmalige 5fb-HEAD met twee werkboomwijzigingen; de vastgelegde hashes zijn gelijk aan de gecommitte code in 9ff.

Dezelfde Codex CLI-reviewer 01a0dc44-26c6-7de3-b2f9-b0f79e5a27ff heeft uitsluitend de correctiediff gecontroleerd en R1 expliciet gesloten, zonder nieuwe bevinding. Rapport wp5-codex-review-r1.md; opdracht wp-5-r1-correctiereview-codex.md; procesexit 0. Base 5fb535ee45671007e5cb4557509560c793eec290, head 9ff3eac199c3eb6e77a44ee47220f91226ffed44, binaire diff-SHA bae61e43834952859e64ddf5eaef4535dd2c0ca24ea4350f0facd5fd2dd3babc. De eerdere volledige review blijft geldig voor ongewijzigde onderdelen en de skill-HEAD 750068253a7389e201daedc5b9aa0afd5c0be032.

De oorspronkelijke reviewerproeven uit zijn afzonderlijke werkroot zijn bytegelijk in dit dossier overgenomen:

- wp5-review-diagnose-passages.py — door de reviewer geschreven diagnostische proef, geen productiecode of correctie van de coördinator.
- wp5-review-diagnose-passages-voor-r1.json — oorspronkelijke afkappingen.
- wp5-review-diagnose-passages-na-r1.json — volledige dragende citaten en correcte offsets na R1.
- wp5-review-bewijscontrole.json — oorspronkelijke controle van contract, bundels en behouden bewijs.

Alle inhoudelijke reviewbevindingen zijn afgehandeld. De volledige pytest-run na R1 loopt nog op 9ff, met --randomly-seed=20260926; geen definitieve suite-uitkomst bij schrijven. De eerdere suite was rood en de 67 failures zijn ook op basis gereproduceerd. Dat vervangt het nieuwe eindresultaat niet. Actieve skilluitrol en kwaliteitswinst blijven onbewezen. Nog geen PR of merge.
