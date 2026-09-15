# DEF-622 — contractreview gesloten

Dit sluit de zes bevindingen uit `DEF-622-contract-review-v1.md`; geen
volledige oplevering van DEF-622. De overige planstappen zijn nog in uitvoering.

Claude herstelde R1–R6 in `3715241af`. Dezelfde onafhankelijke Codex CLI-reviewer
(`01a09ffd-ef32-7cd3-a3b1-7d4380d45f4a`) sloot R1, R2, R4, R5 en R6 op basis
van synthetische proeven op de bevroren commit. Coördinatorverificatie:
52 tests, nul failures/errors/skips, exit 0
(`reports/def622/coordinator-contract-fix.xml`).

R3 bleef open: bij `validate_text` zonder veranderende cleaner kon caller-metadata
de recordtekst bepalen. Claude herstelde dat in `ddb94d1bf`. Dezelfde reviewer
bevestigde daarna dat zonder cleaner én met onveranderende cleaner de echte
tekst voorgaat; gespoofte oude tekst/review blijft open, fingerprint verandert
en `applied=False`. Actuele review blijft geldig; evidence en posities volgen de
oorspronkelijke tekst. Coördinatorverificatie: 66 tests, nul failures/errors/skips,
exit 0 (`reports/def622/coordinator-record-text-fix.xml`).

| Bevinding | Dispositie | Sluiting |
|---|---|---|
| R1 casefold/Unicode-detectie | fix nu | `3715241af`; gelijke context geeft gelijke signalen en juiste posities |
| R2 misvormde actor/reden | fix nu | `3715241af`; verkeerde typen blijven open |
| R3 exacte tekstbinding | fix nu | `ddb94d1bf`; drie regres­siegevallen via echte service en onafhankelijke proeven |
| R4 verlies delen bij fout | fix nu | `3715241af`; pass/fail/error/open en fingerprint blijven behouden |
| R5 nullable score/uitkomsttransport | fix nu | `3715241af`; dict, to_dict, UI-response en opslag behouden None |
| R6 crash in gedeelde weergave | fix nu | `3715241af`; niet beschikbaar plus Nederlandse uitleg vóór detailtoggle |

Geen bevestigde regressies binnen deze fixes. Review is begrensd tot de
genoemde delta's; geen garantie over nog onvoltooide UI-, vaststel- of exportroutes.
Volledige lokale reviewresultaten staan eenmaal onder
`/private/tmp/DEF-622-codex-contract-deltareview-v1-result.md` en
`/private/tmp/DEF-622-codex-record-text-deltareview-v1-result.md`.
