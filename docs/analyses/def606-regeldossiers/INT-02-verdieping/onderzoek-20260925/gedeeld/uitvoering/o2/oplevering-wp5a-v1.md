# DEF-835 — WP5a en typecorrecties: technische deeloplevering

28 september 2026. Branch feature/DEF-835-int02-o2. Beoordeelde bronidentiteit: bewijs/wp5a-reviewmanifest-v5.json (tien bestanden). Basis d769276041e619103ace7bc66e65419d480dae99.

## Geleverd

Optionele O2-injectie in de validatieketen, uitsluitend bij expliciete O2-regelconfiguratie. Onafhankelijke volledige configuratiesnapshot vóór beoordeling en hercontrole vóór publicatie. Documentbinding en verse invoer moeten overeenkomen. Ontbrekende, ongeldige, falende of gewijzigde configuratie geeft error zonder inhoudelijk oordeel. Caller-assessments worden genegeerd. De oorspronkelijke kern blijft behouden; O2 blijft scoreloos.

De oude containertekstguard is gedragsmatig herijkt, met behoud van het testgeval. Geen automatische constructie of modelcall; expliciete factory vraagt profiel en budget. De13typefouten in eigen WP1/WP2 zijn aansluitend gecorrigeerd zonder contract- of gedragswijziging.

## Review en uitvoering

- WP5a: Claude CLI914fccdd-7899-4d5c-8aa0-1c9ab334d7d4; Codex CLI01a0e7dd-2c5e-79a0-b228-3e468c198944. F1–F4gesloten in wp5a-codex-F24-herreview-v1.md, met eerder bewijs behouden.
- WP1typecorrectie: Claude177f1484-4e5c-482e-b431-450befdab835; Codex01a0dfa6-a610-7100-a66e-e3fefc051d4c. Akkoord in typefix-wp1-codex-review-v1.md.
- WP2typecorrectie: Claude99ef6e30-cc76-445a-932d-8c8bd578b835; Codex01a0e1e2-3d37-7111-bc1d-805954a52a16. Akkoord in typefix-wp2-codex-review-v1.md.
- CLIversies: Claude2.1.283; Codex0.158.0. Hoofdsessie coördineerde en verifieerde; geen software zelf geschreven. Volledige opdrachten opgeslagen naast dit verslag, CLIstreams eenmaal onder bewijs. Dossierfallback voor Prompt Forge gehandhaafd.

## Bewijs

- F2/F3RED:32failed/8passed; GREEN221passed. F2restpunt/F4RED:12failed/2passed; GREEN14passed. Eerste GREENv1 met exit127 was een padfout, geen testrun; bewaard.
- Brede gerichte regressie vóór de typecorrecties:2966passed,0skipped. Geen volledige-appsuiteclaim.
- Gecombineerde eindcontrole na beide typecorrecties:526passed, exit0; mypy src/ --check-untyped-defs --no-incremental: geen fouten in411bronbestanden, exit0; Ruff/Black op10bestanden, exit0. Bronhashes vóór/na gelijk: bewijs/wp5a-eindcontrole-v1.json en volledige uitvoer in .log.
- Reviewers herhaalden de concrete foutrepros. Typefixreview:177WP1tests;191WP2tests plus38vergelijkende normproeven, alle exit0.

## Grenzen en vervolg

O1 blijft actief: INT-02.json kiest judgment_review. GitHub Actions op28september opnieuw uitgelezen: enabled=false. Geen push, merge, activering of extra liveappcalls. De review bewijst configuratiecontrole direct vóór publicatie; geen providerattestatie of detectie van een volledig teruggedraaide tussentijdse wijziging.

Geheel O2 blijft open: onafhankelijke goldset/hold-out en modelkwalificatie (C107/C112 niet geslaagd in de driecallproef), gedeelde opslag/historie/herladen/C118, UI/export en ketenlogging, finale oplevering en afzonderlijke activering. DEF-626 is viaLinear opnieuw gelezen en staat Backlog; geen parallelle opslagroute gebouwd. De twee eerder op de basis aangetoonde performance_tracker-fouten blijven benoemd; deze deeloplevering claimt geen volledige groene testsuite. Het driecallmandaat voor de eerdere modelproef is opgebruikt.
