---
id: US-439
epic: EPIC-011
titel: "US-439: - Eén bron van waarheid voor environment; container_manager en config_manager rapporteren dezelfde omgeving."
status: open
prioriteit: P2
story_points: 5
aangemaakt: 2025-09-30
bijgewerkt: 2025-09-30
owner: tbd
applies_to: definitie-app@current
canonical: false
last_verified: 2025-09-30
---

id: US-439
titel: Environment SSOT (container vs config consistentie)

Doel
- Eén bron van waarheid voor environment; container_manager en config_manager rapporteren dezelfde omgeving.

Waarom
- Logs tonen mismatch ('production' vs 'development'); verwarrend en foutgevoelig voor configuratie/flags.

Scope
- Definieer env mapping + validatie; documenteer en test (DEV/PROD/TEST).
- Log één uniforme env string.

Acceptatiecriteria
- Unit tests voor env-detectie/mapping; consistente logregels.

