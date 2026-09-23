# Actuele tegenproef op bevroren recentere code

Broncommit `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb` (18 september 15:27:24 +0200), afkomstig uit de Git-objecten van de eigen worktree. De werkboom blijft op 50d0770. Alleen src/config als ongewijzigde onderzoekskopie in codebasis-4cdb8ea43. Geen productiegegevens, netwerk, modelcalls of database.

Concrete reden voor nieuwe uitvoering: judgment_review.py en types.py zijn sinds de oude probe gewijzigd. Hun oude waarnemingen mogen niet als actuele defects worden opgevoerd.

Herhaal uitsluitend P01–P04 op deze bevroren code, met identieke scenario's/IDs. Verwachtingsversie 2: P01 blijft review_required voor beide metadata-varianten; P02 hoort review_required/rule_statuses/evaluation_coverage in beide projectieroutes te bewaren en mag geen BASIC-passes verzinnen (types.py gebruikt neem_contractvelden_over); onvolledig runbewijs blijft validation_unknown. P03 blijft cijfergerichte ESS-04-instructie (geen ESS-04-promptwijziging in de bekeken diff). P04 betekenisbehoud blijft verwacht, opslag niet uitgevoerd. Deze toets gaat niet over reviewopslag of UI.

Een codekopie en geïmporteerde dependencies komen uitsluitend uit de snapshot-src plus de bestaande Python 3.13-omgeving. Geen hybride import van oude projectmodules. Geen cachebestanden schrijven; PYTHONDONTWRITEBYTECODE=1.
