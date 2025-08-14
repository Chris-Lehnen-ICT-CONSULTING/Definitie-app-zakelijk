# Merge Conflicts Overview

## Archief bestanden (49 files)
Deze bestanden zijn door ons verwijderd omdat we de docs structuur hebben gereorganiseerd.
Ze bestaan nog in main branch als we ze nodig hebben.

## Build bestanden (88 files)
Deze zijn coverage reports en kunnen opnieuw gegenereerd worden.
Ze zijn niet essentieel voor de code.

## Toetsregels conflicts
De toetsregels zijn verplaatst van:
- src/config/toetsregels/ (oude locatie in main)
- naar src/toetsregels/ (nieuwe locatie in feature branch)

Ook zijn sommige bestanden hernoemd van - naar _ (bijv. CON-01.json → CON_01.json)

## Aanbeveling
1. Verwijder de archief bestanden (we hebben ze al gereorganiseerd)
2. Verwijder de build bestanden (kunnen opnieuw gegenereerd worden)
3. Behoud de toetsregels op de nieuwe locatie (src/toetsregels/)
EOF < /dev/null