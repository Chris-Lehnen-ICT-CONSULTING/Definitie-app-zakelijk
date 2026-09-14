# DEF-622 — onafhankelijke review van de vervolgcriteria

Historisch reviewcheckpoint vóór correcties. Reviewer: Codex CLI-taak `01a0a1e3-3a72-76f3-9a3e-2158b01d57e7`, read-only, alle MCP-servers uitgeschakeld, native agents uitgeschakeld. Claude CLI implementeerde; desktop verifieerde. Geen extra delegatie.

Reviewhead: `117e435b5795e733e0cae0bd22c7eac6aaa9a58d`, delta vanaf `be9ddfb75a38ad157727e1c274a070f456191c3b`.

**Vier bevindingen; advies: herstellen vóór oplevering.**

1. **Hoog — cleaner verwijdert betekenisdragende samenstellingen.**  
   [opschoning.py:176](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/opschoning/opschoning.py:176): bij begrip `controle` wordt `Controle- en toezichtshandeling die een bevoegd ambtenaar verricht.` gewijzigd naar `En toezichtshandeling die een bevoegd ambtenaar verricht.` De echte generatieroute retourneert succes en slaat die beschadigde tekst op. Onderscheid een losse termprefix van een koppelteken binnen een samenstelling.

2. **Middel — editor toont oude vergelijking bij gewijzigde tekst.**  
   [definition_edit_tab.py:950](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/ui/components/definition_edit_tab.py:950) vergelijkt met het geladen record, niet met de actuele editorwaarde. Echte Streamlit AppTest bevestigt: na handmatig herschrijven blijft de waarschuwing met de oude eindtekst zichtbaar. Gebruik de actuele, recordgebonden widgetwaarde voor de bewijscontrole.

3. **Middel — inhoudelijke toelichting niet meer bewerkbaar in expertweergave.**  
   [expert_review_tab.py:1031](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/ui/components/expert_review_tab.py:1031) splitst de toelichting af, maar biedt alleen `Bewerk definitie` aan. Bij [opslaan:1248](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/src/ui/components/expert_review_tab.py:1248) wordt uitsluitend de oorspronkelijke toelichting teruggezet. Renderproeven bevestigen het ontbrekende bewerkveld. Voeg afzonderlijke bewerking en opslag van de bestaande inhoudelijke toelichting toe.

4. **Middel — vier classificatieregressietests stranden op de nieuwe contextpoort.**  
   [test_classification_single_path.py:119](/Users/chrislehnen/.codex/worktrees/855d/Definitie-app/tests/unit/test_classification_single_path.py:119), eveneens regels 163, 208 en 447 op deze head: lege context verhindert dat de bedoelde classificatieroute wordt bereikt. Alle vier fouten onafhankelijk gereproduceerd met testbron uit de exacte commit. Geef deze classificatieproeven inhoudelijke context mee; behoud de contextpoort.

Gecontroleerd: de delta van 26 bestanden, criteria, casusmapping, XML/logs, **84 geslaagde gerichte tests**, aanvullende SQLite-proeven en echte Streamlit AppTest. Het afgeronde coördinatorlog meldt **4 failed, 5171 passed**.

Bewijsgrenzen: volledig offline, met bevroren modeluitvoer en synthetische opslag. Latere werkstaatwijzigingen vallen buiten deze review; daarom zijn de vier classificatietests opnieuw vanuit de commit uitgevoerd. Zelf geen bronbestanden gewijzigd en geen agents gestart.

## Dispositie door coördinator

Alle vier bevindingen: **fix nu**. Eigen RED-bewijs bevestigt cleaner (4 van 8 directe proeven en beide generatie/readbackproeven), actuele editorbinding (1 van 4), experttoelichting (5 van 6). De vier classificatietests zijn met geldige contextinvoer hersteld; alle12tests in dat bestand slagen. De contextpoort en oorspronkelijke classificatieassertions blijven behouden. De verdere productcorrecties en beperkte herbeoordeling volgen in een nieuw brongebonden verslag.

De eerste volledige integrationgate vond daarnaast12 oude testgevallen zonder canonieke context (559geslaagd). Ook deze krijgen inhoudelijke testinvoer, zonder productieguard of doelassertions af te zwakken. Acceptance-smoke21geslaagd,5skips; contract36geslaagd,6skips. Dit verslag verklaart het pakket nog niet opgeleverd.
