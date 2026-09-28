# Q1 — correcties F1–F3 door oorspronkelijke Claude-uitvoerder

Jij bent dezelfde Claude Code CLI-uitvoerder (sessie585f02d8-1256-466a-a2ac-ae45d7cbc746). Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Lees je oorspronkelijke q1-opdracht-claude-v1.md voor scope/regels.

Je vorige turn is door de coördinator gericht met SIGINT onderbroken na de groene controle omdat de onafhankelijke review drie echte blokkers heeft bewezen. Geen bronwerk is teruggedraaid. Je mutatiecontrole meldde11gedode mutaties; bewaar dat bewijs maar doe geen nieuwe algemene mutatietestronde. Maak nu de noodzakelijke correcties en een compact uitvoeringsverslag.

Werkboom /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2, branch feature/DEF-835-int02-o2; basisf9bb9e697. Exacte drie bron-/testbestanden uit Q1 blijven de scope. Geen nieuwe dependency, livecall, goldsetlezing, schemawijziging, gitstage/commit of activering.

LET OP: coördinator heeft inmiddels goldset-voorbereiding/ aangelegd. Lees die map NIET. Het bevat mogelijk toekomstige hold-outs. Gebruik uitsluitend je bestaande technische fixture.

## Bevestigde review, alle drie fix nu

Lees U/q1-codex-review-v1.md en U/bewijs/q1-codex-probe-v1.py/.log volledig (U is het oorspronkelijke o2-dossier). De probe is van de onafhankelijke reviewer; pas zijn bewaarde bewijs niet aan. Neem relevante regressies over in jouw bestaande testfile.

F1 — Geen exclusief slot voor vervolgfasen.
Twee gelijktijdige ontwikkelruns op hetzelfde mandaat bereiken elk24calls nadat de3regressies klaar zijn:51inferenties en51tokenmetingen. Beide lazen dezelfde grootboekstand vóór fase_start. Achteraf FileExistsError/ongeldigboek voorkomt kosten niet.
Correctiedoel: exclusief processlot per mandaat/proefmap vóór lezen en beoordelen van actuele stand, vasthouden tot duurzame afronding. Tweede proces weigert vóór transport. Geen verwijderen van bewijs/slotbestanden; een standaardbibliotheekslot met automatisch vrijgeven bij procesafloop is mogelijk. Test werkelijk twee processen of een bewijsbaar equivalent van de twee onafhankelijke descriptors; geen alleen in-process mutex. Raceveilige eerste fase behouden. Geen nieuwe dependency.

F2 — p95 wordt wel gerapporteerd, niet gehandhaafd.
16goedeholdoutantwoorden met gesimuleerde91seconden leveren mechanisch_geslaagd=true en holdout=true.
Correctiedoel: p95≤90000ms als vastgelegd criterium; vóór succesvolle grootboekafronding beoordelen. Ontbrekende/onvolledige/ongeldige metingen geven geen succes. Grens90000toegestaan,90001geweigerd; mocktijd, geen echte wachttijd.

F3 — fase_einde=true vóór bewijsopslag.
OSError op regressie-resultaat.json laat alleen grootboek achter met regressie=true; ontwikkeling verstuurt dan24calls.
Correctiedoel: beschikbare request/response/resultaatartefacten duurzaam bewaren vóór succesvol fase_einde. Op opslagfout geen vervolgcalls; fase blijft geblokkeerd. Bewaar wat al veilig vastgelegd kan worden, geen overwrite of verwijderen. Foutinjectie op beide artefacten en grootboekafronding; geen misleidende status. Houd grootboekslot gedurende publicatie vast.

Coördinator heeft de codepaden gelezen en de onafhankelijke probe-uitvoer gecontroleerd; deze drie punten volgen rechtstreeks uit het geaccordeerde protocol. Geen nieuw akkoord nodig.

## Aanpak/bewijs

1. Nieuwe tests eerst rood; bewaar U/bewijs/q1-F123-red-v1.log. Onderscheid nieuwe gerichte failures van de eerdere156groene tests.
2. Kleinste correcties, één samenhangend veiligheidsherstel binnen dezelfde runner. Maak unieke herstelkopieën vóór wijzigingen.
3. Groen op alle Q1-tests en relevante lint. Bewaar q1-F123-green-v1.log en lint-v1.log plus diff/hashmanifest.
4. Geen extra polish, algemene onderzoek-/mutatierondes of volledige suite. Als een actie3keer werkelijk faalt, stop die actie en rapporteer oorzaak en alternatief.
5. Schrijf U/q1-uitvoering-v1.md als die nog niet bestaat, anders vrijev2. Vermeld gekozen interface,3fixes, oorspronkelijke RED/GREEN en delta-bewijs, bronhashes, resterende concrete beperkingen.
6. Eindig met concrete resultaten. Dezelfde Codex-reviewer controleert daarna de delta.

Prompts zijn volledig in U opgeslagen; Prompt Forge-fallback blijft geldig. Geen securitybypass.

