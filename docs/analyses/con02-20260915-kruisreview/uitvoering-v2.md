# DEF-743 — uitvoeringscheckpoint na de keuzes

15 september 2026. Deze versie volgt op uitvoering-v1.md. Alle drie keuzes zijn goedgekeurd in besluiten-20260915-v3.md; Chris gaf daarna opdracht tot implementatie. De onderzoekscyclus met Cowork blijft afgerond. De volledige implementatie is nog in uitvoering, zonder commit/push/merge.

## Stand

- A/B: bestaande bronselectie/-overdracht en neutrale weergave waren geverifieerd met 5255 geslaagde unittests; dat is bewijs vóór de lopende vervolgwijzigingen.
- C: bronnormalisatie, inhoudelijke AI-beoordeling, runtime/evaluator, wrappers en DI worden gebouwd door Claude Code CLI.
- D: bronbewijs, historie, versiegebonden uitzonderingen, atomaire voorstelstappen en exports worden gebouwd door Claude Code CLI.
- F: editorpariteit, regel-/dekkingweergave, deskundigenbediening en handmatige voorstellen worden gebouwd door Claude Code CLI.
- E: eerste promptimplementatie had 398 passed, 31 skipped, 6 xfailed en gerichte Ruff/Black exit 0. Onafhankelijke Codex CLI-review vond drie verbeterpunten; Claude verwerkt die nu. De genoemde groene run is geen bewijs voor de daaropvolgende correcties.

## Bevestigde E-reviewbevindingen

1. Ontvangstregistratie mist identiteit van de oorspronkelijke passage vóór inkorten/opschonen; document-ID of URL kan bij meerdere passages gelijk zijn.
2. De bestaande sanitizer verwijdert vergelijkingen/voorwaarden uit gewone tekst. Codex vond dit via code-inspectie; Codex-coördinatie riep daarna de werkelijke sanitizer aan: `geldig als 0 < waarde < 10 en leeftijd > 18` wordt `geldig als 0 18`.
3. De contextloze uitbreiding neemt ook CON-CIRC-001 mee, terwijl alleen CON-02 nieuw moest worden geactiveerd.

Codex CLI controleerde dezelfde tien E-bestandshashes vóór en na review. Zijn afzonderlijke uitvoeringsdiagnose slaagde niet (beperkte schrijfomgeving/importbijwerking en invoerfout); hij claimt daarvoor geen testbewijs. Rapport: `/tmp/DEF-743-codex-prompt-review-result.md`. Correctiebrief: `/tmp/DEF-743-prompt-review-fix-brief.md`. De correctie omvat ook het door de implementer gevonden vaste confidence-label in de actieve contextbronweergave.

## Gedeelde interface vastgezet

Leidend voor C/D/F: `/tmp/DEF-743-CONTRACT-FREEZE.md`.

- `source_review` is een platte, getypeerde registratie met actor, motivering, expliciete acceptatie, vingerafdruk en recordversie; geen concurrerende exceptions-dict.
- Een verwijzingsuitzondering blijft herkenbaar als uitzondering en wordt geen gewone positieve AI-uitkomst.
- De inhoudelijke bronbeoordeling gebeurt standaard bij actieve async validatie; uitsluitend herstel is op verzoek.
- De vingerafdruk omvat relevante bronmetadata, naast kandidaat, term, drie contextlijsten, peildatum en broninhoud.
- Volledige `source_assessment` reist mee met het validatieresultaat (additief contract 1.4.0).
- Voorstellen hebben een duurzame reservering vóór de AI-aanroep, een afzonderlijke uitkomst en een atomaire toepassing met echte volledige hertoetsing en versiecontrole.

Twee gekruiste conceptpublicaties zijn door één expliciete freeze opgelost. Dezelfde CLI-sessies zijn hervat met die instructie. Zij kregen geen opdracht tot een nieuwe onderzoekscyclus.

## Actieve sessies en bewijsbestanden

| Pakket | Claude-sessie | Exec | Actueel log |
| --- | --- | --- | --- |
| C | 93e4fe9d-5c65-42ce-b693-2ff52cc2966a | 88402 | /tmp/DEF-743-core-resume-v3.jsonl |
| D | fbae79f1-73f5-4e0c-9bbf-62e52d11737f | 18562 | /tmp/DEF-743-persistence-resume-v3.jsonl |
| F | 3e4e2d44-3076-4ec5-8a0a-20131f5e5f6d | 30195 | /tmp/DEF-743-ui-manual-resume-v2.jsonl |
| E-correctie | ec860e59-2963-4d38-bd53-be2971a1da72 | 6681 | /tmp/DEF-743-prompt-fix-v2.jsonl |

Alle Claude-initinventories: Bash/Edit/Glob/Grep/Read/Write, MCP-lijst leeg, geen subdelegatie. Codex-reviewersessie voor hercontrole E: `01a0a5b8-5bf8-7093-98e5-79a5301da373` (eerste review afgerond).

C kreeg geen schrijfrecht op de gedeelde WIP; verdere WIP-writes door implementers zijn gestopt en expliciet buiten hun ownership geplaatst. App-/testwerk gaat binnen de eigen bestandsgrenzen door. Hooks en beveiligingsconfiguratie zijn niet aangepast.

## Nog uit te voeren

- C/D/F voltooien, onafhankelijke CLI-reviews en gerichte correcties.
- De E-correcties hercontroleren en het verbeterde passagecontract werkelijk in C koppelen; ook verschillende passages uit hetzelfde document moeten correct blijven.
- De deskundige correctie van afzonderlijke AI-deeloordelen is nog een expliciete integratiebehoefte; de twee uitzonderingen leveren die functie niet.
- Bron-/kandidaatketens, echte tijdelijke SQLite-opslag, ID-only herladen/export en Streamlit-bediening integraal verifiëren; daarna volledige unit-/lintgate.
- Bijbehorende skillteksten aanpassen in de geïsoleerde werkboom `/Users/chrislehnen/Projecten/_claude-global-setup/.worktrees/DEF-743-con02-skills`, branch `feature/DEF-743-con02-skills`, basis `7ab73dc`. Alleen voorbereid: 15 baselinecontroles geslaagd, exit 0. Brief `/tmp/DEF-743-skills-implementation-brief.md`; nog geen implementer gestart en geen livesync.

## Bewijsgrenzen

Geen volledige feature-, productie-, geïnstalleerde-release- of deskundige-goldsetclaim. De 94 onderzoeksscenario’s blijven ontwerpen/historische gevallen. De bestaande score-afhankelijke vaststelpoort blijft apart onder DEF-630; geen stilzwijgende omzeiling om zonder totaalcijfer te kunnen vaststellen. Geen automatische CON-02-herstelactivatie of wijziging van de afgesproken DEF-606-volgorde.
