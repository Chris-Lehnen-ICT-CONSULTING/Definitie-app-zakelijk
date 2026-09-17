**Akkoord met deze metadatawijziging; geen bevindingen.**

- Alle 116 entries behouden keys, volgorde, comparisons, status en reason. Alleen precies 10 `source_sha256` en `source_commit` wijzigen.
- Eigen actuele AST-inventaris bevestigt alle hashes en vergelijkingen; ratchet: **116 locaties, 0 afwijkingen**.
- Echte logs bevestigen dezelfde 10 afwijkingen vóór correctie, ratchet exit 0 erna en **11 selftests geslaagd**, zowel vóór als na.
- De tien eerder goedgekeurde correctiebestanden zijn bytegelijk gecommit. Geen nieuwe uitzonderingen, gewijzigde prestatiegrenzen of bronafwijkingen.

Actuele gitdiff is bij begin en einde bytegelijk aan de aangeleverde patch.

**Basis:** `48b6ad75482f97132db1e5b7e078edfb2819587d`  
**Diff-SHA256:** `2fdc7726e95a45f6c9f798cf9cb9c7b4fae458f2c232ad164b41044136a1408e`

Geen volledige testsuites herhaald. Merge blijft afhankelijk van groene CI op de uiteindelijke commit. DEF-624 blijft gedeeltelijk open.