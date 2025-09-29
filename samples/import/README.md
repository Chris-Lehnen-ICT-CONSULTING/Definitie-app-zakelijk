# CSV Voorbeelden voor Import

Deze map bevat voorbeeldbestanden die je direct kunt uploaden in de app.

- `single_definition.csv` — één definitie; gebruik de CSV-bulkimport (≤100) in de Management tab (enkelvoudige import is legacy)
- `batch_definitions.csv` — meerdere definities (≤100) voor “Kleine batch CSV import (≤100)”

Structuur (kolomnamen exact):
```
begrip,definitie,categorie,organisatorische_context,juridische_context,wettelijke_basis
```

Opmerkingen:
- Contextkolommen ondersteunen komma‑gescheiden lijsten (bijv. `OM, DJI` of `Strafrecht, Civiel recht`).
- Categorie: één van `type`, `proces`, `resultaat`, `exemplaar`.
- Encoding: UTF‑8, delimiter: komma, quoting: dubbele aanhalingstekens bij komma’s in waarden.

Gebruik in de app:
- Management tab → “📥📤 Import/Export” → kies de gewenste import‑expander en upload het CSV‑bestand.
