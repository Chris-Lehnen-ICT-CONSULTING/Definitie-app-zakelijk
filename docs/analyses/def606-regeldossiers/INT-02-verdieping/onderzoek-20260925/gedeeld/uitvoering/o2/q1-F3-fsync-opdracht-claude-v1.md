# Q1 — resterende F3-correctie: fout bij fsync na flush

Jij bent de oorspronkelijke Claude Code CLI-uitvoerder, sessie 585f02d8-1256-466a-a2ac-ae45d7cbc746. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Zelfde werkboom/branch en dezelfde drie bestanden; geen livecalls, goldsetlezing, nieuwe dependencies of gitstage/commit.

Dezelfde Codex-reviewer sloot F1 (processlot) en F2 (p95). Bewaar die correcties. F3 is voor beide artefactfouten gesloten, maar de grootboekafronding faalt nog op een preciezer foutmoment. Coördinator heeft rapport en code gelezen; fix nu binnen bestaand mandaat.

Lees q1-codex-herreview-v1.md en bewijs/q1-codex-herprobe-v1.py/.log in U. Bewaarde probe niet wijzigen; die verwijst naar de aparte reviewwerkboom. Geen nieuw algemeen onderzoek.

## Exact defect
Na drie correcte regressies schrijft Grootboek.schrijf een fase_einde met succes en doet flush. Geïnjecteerde os.fsync geeft daarna OSError(EIO). De run breekt af, maar een volgende run leest de al geschreven regel als succes/open_fase=None en verstuurt24ontwikkelcalls.

De bestaande test injecteert vóór het schrijven. Dat test dit concrete geval niet. Maak dus eerst een gerichte rode regressietest met fsync-fout ná flush, plus bewijs van nul vervolgcalls na een nieuwe grootboeklezing/nieuwe runnerinstantie.

## Herstelcriterium
Een mislukte afronding moet blijvend blokkeren vóór nieuw transport, ook als al een succesregel leesbaar is. Borg dit via een vooraf vastgelegde blokkadetoestand of een aantoonbaar even veilige kleine oplossing, die niet door die succesregel wordt opgeheven. Hef blokkering uitsluitend op wanneer de noodzakelijke afrondingsstappen geslaagd zijn. Beoordeel foutmomenten rond de gekozen blokkade zelf; een onbewezen best-effort write na de fout is onvoldoende als enige borging.

Geen historie, bewijs, slotbestanden of testcases verwijderen. Geen claim van gegarandeerde stroomuitvalbestendigheid toevoegen: lokaal proces-/IOfoutgedrag is het concrete te sluiten gebrek. Blijvende metadata naast het append-only grootboek is mogelijk binnen de bestaande runner/proefmap; geen nieuwe projectbestanden/dependencies/APIcontracten buiten scope. Houd slot vast gedurende afronding. Geen hervatfunctie of extra modelcall.

Bewaar unieke herstelkopieën en de volledige delta. Rood in bewijs/q1-F3-fsync-red-v1.log, groen in q1-F3-fsync-green-v1.log, lint/hashmanifest met eigen vrije namen. Test alle Q1-tests eenmaal na de gerichte fix en lint op twee Pythonbestanden. Geen algemene mutatietestronde of polish. Rapporteer de concrete oplossing en beperkingen in q1-uitvoering-v2.md (v1 blijft intact).

Dit is de volgende gerichte correctie van dezelfde F3-afronding. Respecteer de grens van maximaal3pogingen per actie; bij herhaald falen geen verdere autonome herstelronde starten. Lever bewijs zodat dezelfde reviewer F3 gericht kan sluiten.

