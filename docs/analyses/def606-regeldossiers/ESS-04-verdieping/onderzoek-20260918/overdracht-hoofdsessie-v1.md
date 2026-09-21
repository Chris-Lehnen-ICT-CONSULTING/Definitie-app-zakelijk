# Overdracht nieuwe hoofdsessie — DEF-767

Je bent de nieuwe hoofdsessie/coördinator voor DEF-767 — [REGELDOSSIER] ESS-04 — Toetsbaarheid. Chris vraagt: “open een nieuwe hoofdsessie om dit op te pakken zorg dat de informatie bij het juiste linear issue komt”. Pak het vervolg inhoudelijk op vanuit het afgeronde onderzoek; houd besluiten en vervolgwerk bij het juiste issue bij.

Issue: https://linear.app/definitie-app/issue/DEF-767/regeldossier-ess-04-toetsbaarheid (UUID 9398f374-bc22-48a6-856d-910e97e12f9c, parent DEF-606).
De vorige sessie heeft drie volwaardige Linear-documenten aan DEF-767 gekoppeld en de issuebeschrijving bijgewerkt:
- Besluitnotitie: https://linear.app/definitie-app/document/def-767-ess-04-gecontroleerde-besluitnotitie-en-drie-open-keuzes-18-deb188287c30
- Exacte teksten, 37 casussen en veldrollen: https://linear.app/definitie-app/document/def-767-ess-04-exacte-teksten-37-casussen-en-veldrollen-18-september-09b818f49a32
- Bewijs, reviewverwerking en verificatie: https://linear.app/definitie-app/document/def-767-ess-04-bewijs-reviewverwerking-en-verificatie-18-september-cc36064f4795

Lees eerst het actuele issue en deze documenten. Volledige lokale bron, inclusief beide oorspronkelijke onafhankelijke onderzoeken, wederzijdse reviews en alle logs:
/Users/chrislehnen/.codex/worktrees/6ff5/Definitie-app/docs/analyses/def606-regeldossiers/ESS-04-verdieping/onderzoek-20260918/
Begin lokaal met LEES-EERST-eindpakket.md, besluitnotitie-v1.md, instructievoorstellen-v5.md en synthesecontrole-verwerking-v1.md. Actuele overige bijlagen: casusregister-v2.md, veldrollen-en-keten-v2.md, bron-bewijsregister-v3.md, eindverificatie-v1.json en eindpakket-manifest-v1.json.
Deze bestanden zijn ongetrackt in de vorige werkboom en staan dus niet automatisch in jouw nieuwe werkboom. Lees ze via dit absolute pad; behoud de vorige werkboom en alle bronnen. Beschouw oudere instructievoorstellen v1-v4 niet als actueel.

Onderzoekstatus: afgerond. Twee onafhankelijke onderzoeken, wederzijdse reviews (14 en 33 punten), verwerking door beide partijen en afsluitende Cowork-synthesecontrole zijn uitgevoerd. Herhaal deze onderzoekscyclus niet. De onderzochte codebasis is commit 4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb; controleer uitsluitend relevante verschillen met jouw actuele basis. Er is nog geen ESS-04-implementatie uitgevoerd. DEF-767 blijft open.

Eerste concrete opdracht: bereid op basis van de gecontroleerde besluitnotitie drie heldere beslispunten met aanbeveling en gevolgen voor, leg ze in één samenhangend bericht aan Chris voor en werk onafhankelijk de vervolgspecificatie/acceptatiecriteria uit. Eerdere algemene “ja/akkoord”-reacties vormen geen aantoonbare keuze tussen deze drie inhoudelijke alternatieven. Vraag geen algemene starttoestemming opnieuw. Leg ontvangen keuzes daarna expliciet vast in DEF-767 en de besluitnotitie. Voer beleidsafhankelijke implementatie pas uit wanneer de daarvoor benodigde keuzes en opdracht vaststaan.

De drie open keuzes, inclusief het herziene advies (dit gaat vóór oudere voorlopige §7.4-teksten):
1. Richting indicatorpatronen: aanbevolen neutrale gemengde aandachtssignalen voor vaagheid én kwantitatieve grenzen, zonder automatische pass/fail. Alternatieven: minimaal herstel van zes regexgebreken, of vaste reviewvragen zonder patronen. Nieuwe patronen zijn nog niet gekalibreerd.
2. Reikwijdte review/vaststelpoort: bestaande algemene versiegebonden expertbeoordeling uit DEF-630 is bestaand beleid. Het herziene advies is een integrale geldige review met uitkomsten per regel, zonder afzonderlijke ESS-04-goedkeuringsknop of extra harde poort. De precieze toepassing op ESS-04 is nog een voorstel. Respecteer ESS-01/02-besluiten en afzonderlijke CON-01/02-voorwaarden; ontbrekende verplichte review/bewijs is niet hetzelfde als een gemotiveerd open oordeel en kan niet met een losse notitie worden omzeild. Presenteer de uiteindelijke opties vanuit de actuele besluitnotitie.
3. “Voldoet” bij ontbrekende gegevens: onderscheid ontbrekende criterium-/betekenisbasis van ontbrekend casusbewijs. Een beoordeelbare definitie kan na daadwerkelijke review voldoen terwijl de casus onbeslist blijft. Technisch nog niet beoordeeld blijft een eigen toestand.

Aanbevolen norm N2: “Ieder criterium in de definitie is binnen de bedoelde betekenis en context voldoende bepaald om navolgbaar te beoordelen of een geval eraan voldoet.”

Belangrijk bewijs:
- validation/additional_patterns.py bevat geen extra ESS-04-patronen; dat eerdere bewijsgat is gesloten. Ook registry.py, types_internal.py en approval_gate_policy.py zijn onderzocht.
- Veertien echte offline evaluatoraanroepen leveren review_required met null score; 37 synthetische casussen zijn geen expert-goldset en geen volledige appacceptatietest.
- Zes regexbeperkingen aangetoond; kwantificering is niet noodzakelijk of voldoende voor toetsbaarheid. Kwalitatieve criteria kunnen toetsbaar zijn.
- Totaalscore is definitief afgeschaft beleid, geen tijdelijke pauze. Geen nieuwe ESS-04-AI-jury afleiden uit CON-02; DEF-638-autorepair is apart vervolgbeleid.
- Beperkingen: geen volledige UI/import-opslag-readback/vaststel-exportketen, live LLM-proef of menselijke goldset bewezen. Toekomstig implementatiebewijs moet bij de uiteindelijke code horen.

Coördinatie: bedien Claude Desktop/Cowork niet; Chris heeft gevraagd daarmee te wachten omdat een andere sessie Claude gebruikt. De onderzoeksuitwisseling is al afgerond. Geen nieuwe Cowork-taak starten en geen ESS-05 meenemen. Gebruik toepasselijke skills, waaronder issue-workflow-protocol voor vervolgdocumenten. Analyse en documentvoorbereiding kunnen rechtstreeks. Houd historische issue-inhoud herkenbaar; maak voorstellen niet tot goedgekeurde besluiten. Zet DEF-767 pas Done als ook besluit- en eventueel opgedragen implementatiecriteria aantoonbaar voldaan zijn.

Zodra een programmeertaak is opgedragen geldt het verplichte rolblok uit /Users/chrislehnen/Projecten/_claude-global-setup/templates/task-start-cli.md:
Jij bent de coördinator. Bij deze programmeertaak implementeert Claude Code CLI de softwarewijzigingen, bijbehorende tests en eventuele bijbehorende promptteksten, inclusief correcties na review. Gebruik op deze Mac de echte binary `~/.local/bin/claude`. Codex CLI reviewt de concrete diff in een afzonderlijke sessie en wijzigt zelf geen bronbestanden. Schrijf of corrigeer die bestanden als coördinator niet zelf. Interne subagents gelden niet als vervanging van deze CLI-uitvoering.

Controleer vooraf of beide CLI's beschikbaar en bruikbaar zijn. Geef Claude de opdracht, geïsoleerde werkboom, branch, scope, acceptatiecriteria en relevante besluiten. Laat Claude implementeren en passende tests uitvoeren. Geef Codex CLI de acceptatiecriteria, base, uiteindelijke head/diff-identiteit en testbewijs. Geef bevestigde bevindingen terug aan dezelfde Claude-uitvoerder; laat dezelfde Codex-reviewer de correcties controleren. Controleer zelf dat het bewijs bij de uiteindelijke code hoort.

Alleen jij als coördinator start uitvoerders en reviewers. Neem in iedere uitvoerders-/reviewopdracht op: "Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies." Een toegewezen uitvoerder/reviewer voert zijn eigen rol uit en delegeert niet opnieuw.

Als een vereiste CLI niet beschikbaar is, rapporteer de concrete blokkade. Neem implementatie of review niet stilzwijgend over; afwijking vereist een expliciet gebruikersbesluit. Ga door met onafhankelijk coördinatiewerk. Meld bij oplevering de werkelijk gebruikte CLI's, sessie-/logverwijzingen, testresultaten en beoordeelde commit of diff. Volg AGENTS.md en de toepasselijke skills; algemene delegatieadviezen vervangen deze rolverdeling niet.

Voor oplevering: actuele besluiten, specificatie, acceptatiecriteria en bewijs in Linear; concrete uitvoeringsscope en afhankelijkheden (DEF-624/625/626/630/638) afbakenen zonder die issues ongegrond als opgelost te markeren.

