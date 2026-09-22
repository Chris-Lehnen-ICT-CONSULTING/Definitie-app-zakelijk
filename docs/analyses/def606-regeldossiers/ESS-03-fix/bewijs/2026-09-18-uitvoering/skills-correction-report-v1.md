# DEF-766 / ESS-03 — correctierapport skillteksten, v1

18 september 2026 · uitvoerder: dezelfde Claude Code CLI (Opus 5) als `skills-report-v1.md` · reageert op `skills-review-v1.md` (Codex CLI). Geen agents, reviewers of extra CLI-sessies. Geen commit, merge, push of installatie. Alleen `Edit` op bestaand bestand.

## 1. Dispositie

| Bevinding | Severity | Dispositie | Status |
|---|---|---|---|
| ESS-03 blijft in het entrypoint `skills/definitie-toetsregels/SKILL.md` (regel 39 *Overzicht*, regel 74 *Scoring & Weging*) onder gewogen scoring vallen, terwijl `reference.md:54` en het contract geen ESS-03-cijfer en geen automatische gate voorschrijven | P2 (bevestigd) | **Fix nu** | Gefixt: beide passages noemen ESS-03 als gerichte uitzondering met lokale contractverwijzing |

Bestandsverantwoordelijkheid uitgebreid met uitsluitend `skills/definitie-toetsregels/SKILL.md`. Geen andere bestanden geraakt; de zeven bestanden uit ronde 1 zijn byte-ongewijzigd (zie §4 hashes).

## 2. Wijziging (3 hunks, +3 −3)

Basis: HEAD `9f5ae6f3bb4b990a855bc0969bc4f6067c02c197` (ongewijzigd). Volledige diff: `/tmp/def766-cli/skills-correction-v1.diff` (28 regels, sha256 `9ababb07…5561b4`).

**Hunk 1 — regel 39, *Overzicht*.** In de uitzonderingslijst op "gewogen scoring" tussen ESS-02 en CON-01 ingevoegd:

> ESS-03 (menselijke beoordeling van eenheid en identiteit, [`references/ess03-eenheid-identiteit.md`](references/ess03-eenheid-identiteit.md)),

Rest van de zin (ESS-01, ESS-02, CON-01, CON-02, "leveren geen cijfer (zie Scoring & Weging)", 46/53 generatie-instructies) ongewijzigd.

**Hunk 2 — regel 74, *Scoring & Weging*-blockquote.** Kop: "Geen cijfer voor ESS-01, ESS-02 of CON-02" → "Geen cijfer voor ESS-01, ESS-02, **ESS-03** of CON-02; voorlopig geen totaalcijfer." Direct na de bestaande ESS-02-zin en vóór de CON-02-zin ingevoegd:

> ESS-03 krijgt geen cijfer of 0/1 en kent geen automatische gate: de mens beoordeelt eenheid en identiteit (voldoet / voldoet niet / nog te beoordelen, of bevestigde niet-toepasselijkheid met grond); een naam, nummer of het woord ‘uniek’ geeft geen automatische pass of fail, de prioriteit *hoog* ordent de aandacht, en of een menselijk vastgesteld ernstig telgebrek een vervolghandeling beperkt blijft afzonderlijk open onder DEF-624 — contract: [`references/ess03-eenheid-identiteit.md`](references/ess03-eenheid-identiteit.md).

Alle overige zinnen van de blockquote letterlijk behouden: ESS-01-zin, ESS-02-zin, CON-02-zin, "Productbesluit 15 september 2026 (DEF-743/DEF-624): voorlopig geen totaalcijfer …", "De gewichten en drempels hieronder zijn de bestaande generieke configuratie …", "Dit herschrijft de app-brede scoregate niet … DEF-630." Gewichtstabel, drempels en de CON-01-uitzonderingssectie onaangeroerd (geen algemene scoreopschoning; de achterhaalde tijdelijkheidsformulering blijft DEF-624-scope zoals in `skills-report-v1.md` §6 genoteerd).

**Hunk 3 — versieregel.** "0.6 — DEF-766 (ESS-03 eenheid en identiteit: gerichte uitzondering op gewogen scoring, geen cijfer en geen automatische gate)" vooraan toegevoegd; 0.5/0.4/0.3 behouden. Consistent met de versiebump in `definitie-nederlandse-definities/SKILL.md` uit ronde 1; trivieel te schrappen als de reviewer dit buiten de dispositie vindt.

Niet gedaan (bewust, buiten dispositie): geen nieuw `## ESS-03`-H2-blok naast ESS-01/ESS-02 in SKILL.md; geen wijziging aan *Gerelateerde skills*; geen nieuwe policy of enum.

## 3. Bewijs (exitcodes)

| # | Controle | Commando | Resultaat |
|---|---|---|---|
| 1 | SKILL.md-referentiepointers | `python3 scripts/check-skill-references.py skills/definitie-toetsregels/SKILL.md` | ✅ exit 0 (alle pointers, incl. 2× nieuwe ess03-link, resolven) |
| 2 | Description-format | `python3 scripts/check_skill_description_format.py skills/definitie-toetsregels/SKILL.md` | ✅ exit 0 |
| 3 | Cross-refs "NOT for (use X)" | `bash scripts/validate-skill-crossrefs.sh` | ✅ exit 0 |
| 4 | Gerichte inhoudscheck entrypoint (38 asserts: frontmatter parst + keys ongewijzigd; Overzicht en Scoring noemen ESS-03 met contractlink; dispositie-sleutelbegrippen aanwezig — geen cijfer/0/1, geen automatische gate, bevestigde niet-toepasselijkheid, geen automatische pass/fail, hoog ordent aandacht, DEF-624 open; 12 bestaande scoreteksten/scopegrenzen behouden; alle 9 lokale links resolven; geen ESS-03-H2 toegevoegd) | `/usr/bin/python3 /tmp/def766-cli/check_skillmd_ess03.py` | ✅ exit 0, 38/38 OK |
| 5 | skill-creator `quick_validate.py` | `/usr/bin/python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/definitie-toetsregels` | ❌ exit 1 — **pre-existing, identiek aan baseline en ronde 1** (repo-frontmatterkeys `evalScore, lastReviewed, status, triggerExamples`; YAML parst, zie #4) |
| 6 | Regressie ronde 1: letterlijke tekstvergelijking | `/usr/bin/python3 /tmp/def766-cli/compare_ess03_texts.py` | ✅ "alle checks geslaagd", exit 0 |
| 7 | Regressie ronde 1: links 7 bestanden | `/usr/bin/python3 /tmp/def766-cli/check_links_ess03.py` | ✅ exit 0 |
| 8 | Byte-identieke kopie ess03 | `cmp toetsregels/references/ess03… nederlandse-definities/references/ess03…` | ✅ exit 0 |
| 9 | Werkstaat | `git status --short`, `git diff --stat` | 6 M + 2 ?? ; totaal +20 −8; SKILL.md +3 −3 |

## 4. Identiteit van de beoordeelde staat

| Bestand | sha256 |
|---|---|
| `skills/definitie-toetsregels/SKILL.md` (vóór correctie) | `e184527e8d8cd8f555233d707bfa5afff45948c726e8ec3307a8a13239b9973a` |
| `skills/definitie-toetsregels/SKILL.md` (na correctie) | `e460a96b01626fb8b2eb151ef7909be87e89565ec800e5def901c6ba9a9de9a6` |
| `skills/definitie-toetsregels/reference.md` (ongewijzigd t.o.v. ronde 1) | `86e2d2dd2051429e03d4b80715bc83af4346707d8e4e36895a176285e5fa4932` |
| `skills/definitie-toetsregels/references/ess03-eenheid-identiteit.md` (ongewijzigd) | `529c7ca6e02901fd4eb4d7fa970b3e8ceadda70c3448a45d7c83a1c526d25c6a` |
| `/tmp/def766-cli/skills-correction-v1.diff` | `9ababb079e3972023400cbd6d6592437e423b952b72e8572115e474c0a5561b4` |

HEAD `9f5ae6f3bb4b990a855bc0969bc4f6067c02c197`, branch `bugfix/DEF-766-ess03-skills`, niets gecommit.

## 5. Open grenzen (ongewijzigd)

Geen modelproef; geen appwerking bewezen; distributie/installatie en `.skill`-zips coördinatorbesluit; DEF-624 (NA-mapping, menselijke ernstige-foutgate, coherente totaalscore-opschoning van de resterende tijdelijkheidszinnen en legacy gewichten/drempels) blijft open — deze correctie voegt daar niets aan toe en neemt daar niets van weg.

Bronnen: `skills-review-v1.md` (P2), `skills-report-v1.md` §6, `git diff skills/definitie-toetsregels/SKILL.md`, uitvoer van #1–#9 in deze sessie.
