# Claude Code CLI — DEF-771, uitsluitend WP3

Jij bent de Claude Code CLI-uitvoerder, dezelfde sessie a4b588d6-e4a1-4fd6-8f80-0aac55013d90. Voer deze opdracht zelf uit; start geen agents, reviewers of extra CLI-sessies. Coördinator verifieert; een afzonderlijke verse Codex CLI-sessie reviewt later de volledige concrete diff. Alle rapportage Nederlands.

## Akkoord en geldige basis

Chris heeft op 25-09 na de drie concrete akkoordpunten “akkoord” gegeven: bestaande WP2-diff van 133 regels geaccepteerd, WP3 met twaalf inhoudelijke bestanden en circa 330–560 gewijzigde regels goedgekeurd, zes concrete S1-markers goedgekeurd inclusief de gewijzigde C02-verwachting. Heropen die besluiten niet. Een nieuw inhoudelijk bestand, dependency, schema/API-wijziging of wezenlijke uitbreiding van de beschreven functies vraagt wel vooraf akkoord via de coördinator. Meld een verwachte overschrijding van de raming vóór verdere uitbreiding; herhaal de WP2-fout niet. Tel nieuwe bestanden mee.

App: /Users/chrislehnen/Projecten/Definitie-app, feature/DEF-771-int02-contract-o1, basis 0d26f0f4f5b2ebebe1c7d71fbff5e4ddb66b8c0d plus ongecommitte WP1/WP2. Skillwerkboom: /Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-771-int02-skills, gelijknamige branch, basis 1e27a2da7668437423af3962cce48af5f1bc591b plus WP1. Behoud andere wijzigingen. Jij bent alleen schrijver van de toegewezen inhoudelijke bestanden; coördinator beheert werkstaat en opdrachten.

Dossier relatief aan app: docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/. Alle nieuwe opdrachten, logs, replay en resultaten onder gedeeld/uitvoering/. Prompts staan volledig in het dossier; Prompt Forge is geen blokkade. Niet aan beveiligingsinstellingen komen. Geen bestand, testgeval of dode code verwijderen. Maak vooraf unieke herstelkopieën. Geen live toepassingsmodelcalls, productiedata, nieuwe dependency, commit, push, PR of Linear-mutatie. Maximaal drie pogingen per actie; dan stoppen en concrete fout melden.

## Lees gericht

Lees gedeeld/uitvoering/wp3-s1-en-omvang-ter-akkoord.md: ondanks de historische titel/status is dit voorstel nu volledig goedgekeurd. De daarin genoemde twaalf bestanden vormen jouw scope. Lees waar nodig de al onderzochte synthese v5 §4/§6, besluiten B2/B3/B4 en het casusregister voor de exacte teksten en casussen. Geen nieuwe brede inventarisatie. Eerdere bronlezing en geldig bewijs blijven bruikbaar.

Pas test-driven-development toe: eerst echte, inhoudelijk falende tests; bewaar RED-uitvoer en exitstatus vóór productieaanpassing. Tests die behoud bewaken mogen direct groen zijn; maak die niet kunstmatig rood. Geen broncode verwijderen om TDD te reconstrueren. Gebruik pytest in de bestaande .venv en de bestaande offline-bootstrap.

## Te realiseren gedrag

1. JudgmentReviewEvaluator krijgt een INT-02-tak met _int02_reden. Reden bevat de exacte nieuwe toetsvraag; per passage de volledige exacte neutrale O1-vraag uit synthese §4, met het volledige dragende zinsdeel/de zin en een controleerbare positie. Zonder treffer de exacte signaalloze waarschuwing. RR blijft RR, geen pass/fail of score op grond van patronen.
2. Citeer de ongewijzigde kern en bepaal posities in diezelfde tekst; geen positie in cleaned_text labelen als raw-positie. Gebruik nulgebaseerde start en exclusief einde, vermeld de conventie. Herhaalde gelijke passages op verschillende posities blijven onderscheidbaar; meerdere markers op dezelfde passage mogen één vraag delen. Bij onzekere zinsdeelgrenzen de volledige kern citeren in plaats van een los of afgekapt markerwoord. Geen algemene taalparser of nieuwe dependency bouwen. Behoud de werking van ESS-01/02/04 en andere regels.
3. Lege kern, alleen een termlabel (C23) of ontbrekende vereiste context geeft not_evaluated met exact “INT-02 — Niet uitgevoerd: {kern/context} ontbreekt. Er is geen inhoudelijk oordeel.” Maak de ontbrekende grond duidelijk. Dek zowel de echte service als directe evaluatorwerking af waar toepasselijk. Context staat expliciet als context_lists in INT-02 required_inputs. De gerichte servicewijziging levert alleen voor INT-02 de exacte reden; wijzig de generieke contracten van andere regels niet.
4. Behoud de zeven bestaande patronen bytegelijk en voeg exact de zes goedgekeurde regexen uit wp3-s1-en-omvang-ter-akkoord.md toe. Markeer patronen in het record expliciet als leeshulp, niet normatief. Hun aanwezigheid/afwezigheid beslist nooit een inhoudelijk oordeel. C02 krijgt nu door moet passagehulp; C83 treft naar eigen inzicht/redelijk acht; C13 en C105 blijven zonder signaal. Dient als/tot is geen dient te-marker.
5. UI alleen: INT-02 toevoegen aan de bestaande tuple (ESS-01, ESS-02, ESS-04) voor zichtbare reden. Geen overige UI, issues-helper of expertreview-herlaadroute wijzigen.
6. Publiceer de goedgekeurde markerlijst, contractversie def771-int02/2 en juiste uitvoeringsstatus in het canonieke skillcontract en maak de tweede kopie bytegelijk. Record en contracttest krijgen dezelfde versie; beide SKILL.md-verwijzingen gaan naar /2. N/G/T/H-teksten blijven letterlijk dezelfde norm. De verwijzing naar /1 in de WP2-codecomment betreft de ongewijzigde G-norm; raak die module nu niet opnieuw aan. WP1-opbouwscript blijft historisch WP1-bewijs en mag niet over het nieuwe contract worden uitgevoerd.

## RED-casussen en acceptatie

- Met context: C04/C50/C54 RR met signaal, exacte neutrale vraag, volledige passage en positie; nooit INT-02-violation of score.
- C02 volgens de goedgekeurde moet-marker; C83 met S1; C105 exacte waarschuwing zonder signaal.
- C06/C23/C56 NE met exacte melding, geen reviewvraag over ontbrekende kern/context.
- C13 geen valse S1-claim; C59 geen automatische afkeur. Neem de drie synthetische beschrijvende/functiegevallen uit het goedgekeurde voorstel mee. Test markergrenzen voor kan … besluiten en dient te gericht.
- Controleer passage==kern[start:einde], identieke herhaalde passages op andere posities en een bron/cleaned-verschil zonder fictieve broncitaten. Toetsen verandert de aangeleverde tekst nooit.
- UI-reden blijft zichtbaar bij ingeklapte details; gebruik een bestaande functionele UI-testaanpak, geen snapshot van alleen broncode.
- Pas de WP1-contracttest gericht aan voor context_lists en versie /2; verwijder geen controles. Voer de contracttests expliciet met DEF771_SKILLS_ROOT naar de skillwerkboom uit; zonder die variabele zijn tien tests geen contractbewijs.

## Nieuwe C1-replay

Maak uitsluitend de afgesproken nieuwe proef-c1-uitvoering-na-o1.py en proef-c1-uitvoering-na-o1.json in gedeeld/uitvoering/. Gebruik het historische script en proef-c1-verwachtingen.json als bron, maar voer geen code uit die het oude resultaat overschrijft. Gebruik synthetische context voor RR en aparte contextloze NE-varianten. Neem C06/C23/C56 en de genoemde S1-casussen expliciet mee. Bij de promptrendering is juridische context nodig om INT-02 werkelijk te tonen; de historische proef gaf die niet mee.

Installeer de bestaande offline-bootstrap vóór applicatie-imports. Bewaar originele én nieuwe verwachtingen, werkelijke status/reden/signalen, citaten/posities, bron-/codehashes vóór de run, commando, tijden en exitstatus. Een bestaande resultaatnaam niet overschrijven: kies bij herhaling een nieuwe pogingnaam en rapporteer de geldige uitkomst. Geen claim “historische statussen ongewijzigd” voor gevallen waarvan de context bewust is veranderd. Geen live model of productiegegevens.

## Verificatie en terugmelding

Voer gerichte GREEN-tests voor WP3, de contracttests en relevante behoudtests uit, plus Ruff/Black op de gewijzigde Pythonbestanden. Bewaar volledige logs. WP4 krijgt daarna de twee bestaande C24/C25-regressiefixtures met lege context; verander die nog niet. Een daardoor verwachte tijdelijke failure eerlijk benoemen. De reeds bewezen basisfailure test_no_negative_commands_in_guide (12 < 10) blijft buiten scope en hoeft niet opnieuw breed onderzocht.

Lever aan de coördinator: twaalf paden, werkelijke diffstat inclusief ongetrackte bestanden, hashes, RED→GREEN-bewijs, replay-uitkomst, casusdekking, letterlijke tekst-/bytegelijkheidscontrole en alle open beperkingen. Stop bij een betekenisvol dossier/codeconflict of wanneer een exacte tekst niet in het bestaande contract past; citeer en stel een oplossing voor. Geen WP4 starten totdat de coördinator het pakket heeft gecontroleerd.
