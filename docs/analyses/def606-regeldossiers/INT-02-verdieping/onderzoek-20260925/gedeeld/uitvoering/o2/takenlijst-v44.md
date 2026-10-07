# INT-02 O2 — deeloplevering gemergd (takenlijst v44)

29 september 2026. Vervangt v43 als procesingang; het uitstel van DEF-626 uit v42 blijft gelden.

## Afgerond

- [x] Kleine cwd-testfout door oorspronkelijke Claude Code CLI-uitvoerder gecorrigeerd; oorspronkelijke Codex CLI-reviewer akkoord. Productiecode bleef bij die correctie ongewijzigd.
- [x] Nieuwste main met INT-03 PR486 conflictvrij in de O2-featurebranch geïntegreerd.
- [x] Bronbinding gecontroleerd: 1.379 bestanden gelijk tussen geteste combinatie en featurebranch.
- [x] Bewijs bewaard en gecommit. Brede gecombineerde unitrun: 8.775 passed, 5 failed, 7 errors, 75 skipped, 1 xfailed; exit 2. De twaalf foutnodes waren testomgevingsproblemen (verkeerd skillpad en Git-loze bronkopie). Gerichte hercontrole op dezelfde bron in de juiste omgeving: 16 passed, exit 0; machinecontrole bevestigt dat alle twaalf foutnodes zijn gedekt. Geen claim van één volledig groene unitrun.
- [x] Gecombineerde gerichte selectie: 936 passed, 11 aanvankelijke skill-skips; skillcontract daarna volledig getoetst. Cwd-correctie: 177 passed, RED→GREEN en mutatiebewijs. Lint groen; normale commit-/pushcontroles incl. Gitleaks en dependency-audit geslaagd.
- [x] PR488 gepubliceerd en exacte body/head teruggelezen.
- [x] Door Chris geautoriseerde reguliere beheerdersmerge uitgevoerd voor de ontbrekende Actions-checks. Geen squash/rebase, branchverwijdering of wijziging van branchbescherming.
- [x] GitHub bevestigt MERGED; mergeboom is exact gelijk aan de gecontroleerde PR-head.
- [x] Actions na merge nog steeds uit; INT-02 blijft judgment_review (O1), O2 niet geactiveerd.

## Identiteit

- Branch: feature/DEF-835-int02-o2.
- Testcorrectie: 2c07bbd95.
- Integratie actuele main: 7c9936dc95e42517225b9a824b24c12b59522d3d.
- PR-head met bewijs: a9fb4a0b7444d073813182b662056e7c3265fc7c.
- PR: https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/488.
- Mergecommit en opgehaalde origin/main: edd148ab7df95a2782e2b8867e989a1242618fd8.
- Merge-/headboom: 7a5ff5a5aaa216a35a26c84461ca85b528235494.

Bewijs: bewijs/mergevoorbereiding-v1/na-merge-verificatie.json, foutsluiting.json, finale-bronbinding.json, bewaarde logs en beide CLI-verslagen. Geen CLI- of testproces meer actief.

## Open binnen DEF-835

- [ ] Onafhankelijke goldset/hold-out met expertlabels accepteren en bevriezen.
- [ ] Modelkwalificatie binnen eerder verleende autorisatie en budget uitvoeren na labels/freeze.
- [ ] Verdere appintegratie en eindverificatie afronden met expliciete grens voor DEF-626.
- [ ] Afzonderlijk besluit over productieactivering na geaccepteerd bewijs.

DEF-626/S1 blijft apart en uitgesteld, inclusief alle ongecommitte wijzigingen in zijn eigen werkboom. Niets daarvan is meegepubliceerd of verwijderd. DEF-835 is met deze technische deeloplevering niet volledig afgerond; geen Linear-acceptatiecriterium of status is stil gewijzigd. Werkbomen en lokale bewijsstukken blijven behouden.
