**Alle zeven C-reviewbevindingen zijn gesloten binnen deze gerichte statische review. Geen resterende concrete P1/P2 gevonden.**

- **#1 gesloten:** iedere positieve claim vereist een bewijsbron; tegenstrijdige `applicable`/`locatable`-oordelen over hetzelfde bron-ID blijven open. Gemengde regressiegevallen behouden negatieve/onbekende feiten; positieve controles blijven toegestaan.
- **#5 gesloten:** replay controleert bronset, exact passageprefix, afkapgrens, hashes, bronversie en afkapmarkering. De readonly serviceproperty levert de werkelijke grens via beide wrappers aan de evaluator.
- **#6 gesloten:** beide wrappers weigeren misvormde aliases en conflicterende lijsten. `None` geldt expliciet als afwezigheid; geldige lijsten en invoerimmutabiliteit blijven behouden.
- **#2, #3, #4 en #7 blijven gesloten.**

**Bewijs:** [hashmanifest v4](/tmp/DEF-743-core-hashes-v4.log) klopt **29/29 bij start én einde**. De geïnspecteerde logs melden **1656 passed, 21 subtests**, exit 0 en schone lint. Ik heb deze tests niet zelf uitgevoerd.

Opgeslagen replay vertrouwt het daadwerkelijk bewaarde beoordelingsdocument; het bewijst geen cryptografische authenticiteit van een volledig herschreven receipt. Historische beoordelingen zonder receipt blijven buiten bewijs van exacte modelinvoer. F-weergave/integratie, de canonieke testgate en modelkwaliteit vallen buiten deze sluiting; **DEF-743 als geheel is hiermee niet afgerond**.