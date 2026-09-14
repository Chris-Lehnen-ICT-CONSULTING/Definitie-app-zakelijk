# DEF-622 — reviewbare skillbronpatch (B-02, CON-01 zonder cijfer)

**Status:** voorstel, niet toegepast. Geen live writes op `~/.claude/skills` en geen
wijziging in de bronrepo `_claude-global-setup`; alleen dit patchbestand in de
DefinitieAgent-repo. Toepassen en syncen is een aparte, bewuste stap van de
coördinator/Chris (`sync-rules.sh --sync` → commit → push in `_claude-global-setup`).

**Patch:** [`DEF-622-skillpatch-v1.patch`](DEF-622-skillpatch-v1.patch)
(unified diff, `-p1` vanuit de map die `skills/` bevat, d.w.z. de root van
`_claude-global-setup`).

## Waarom

De skills beschreven CON-01 nog als een absoluut verbod ("zonder expliciete
benoeming van contextnamen", "Noem context NIET expliciet") en de scoring als
onverkort gewogen (hoog = 1.0, drempels 0,75/0,65). Besluit B-02 van CON-01
maakt het onderscheid tussen **registratiecontext** (hoort niet in de
definitiezin) en een **inhoudelijk noodzakelijke naam** (mag erin staan), en
CON-01 krijgt **geen cijfer** (geen 0/1, geen gewicht; appbrede totaalscore
tijdelijk niet beschikbaar; geen nieuwe formule — de scoreformule is van
DEF-624, de algemene gate van DEF-630). Zonder deze patch sturen de
hoofdinstructies de generator en de beoordelaar naar de oude norm en
suggereren ze een score voor CON-01.

## Wat er verandert (minimaal, alleen de B-02-norm)

| Bestand | Regel(s) | Wijziging |
|---|---|---|
| `skills/definitie-toetsregels/reference.md` | 29 | CON-01-instructie: registratiecontext niet in de zin; naam alleen als inhoudelijk noodzakelijk; prioriteit "**hoog** (geen cijfer)" |
| `skills/definitie-toetsregels/SKILL.md` | na 74 (sectie *Scoring & Weging*) | Nieuwe subsectie *Uitzondering: CON-01 zonder cijfer (DEF-622)*: geen cijfer/weging 0/1; drie inhoudelijke uitkomsten (Voldoet / Voldoet niet / Nog te beoordelen); een technische uitvoeringsfout afzonderlijk herkenbaar (geen inhoudelijke overtreding, verhindert een volledige Voldoet zolang de verplichte controle ontbreekt); totaalscore tijdelijk niet beschikbaar, fail-closed; geen nieuwe formule — scoreformule DEF-624, gate DEF-630 |
| `skills/definitie-nederlandse-definities/reference.md` | 208 | Inleiding *Impliciete Contextverwerking*: registratiecontext niet in de zin; noodzakelijke naam toegestaan |
| idem | 225 | Zelftest: "... zonder dat de registratiecontext genoemd wordt — en is elke naam die wél in de zin staat inhoudelijk noodzakelijk?" |
| idem | 238 | Checklistpunt 10: registratiecontext niet in de zin; contextnaam alleen als noodzakelijk |

De drie mechanismen (vocabulaire, scope, relaties) en alle overige regels/
gewichten blijven ongewijzigd.

## Bronhashes (sha256)

Gemeten op 2026-09-14 op de bronrepo `/Users/chrislehnen/Projecten/_claude-global-setup/skills/`.
De patch is toegepast op ongewijzigde kopieën (`patch -p1`, exit 0) en levert
exact de "na"-hashes op.

| Bestand | Vóór | Na |
|---|---|---|
| `definitie-toetsregels/reference.md` | `b4ef1e5204775ca7023af05c099c0a26582d1706c7b2f5409a4054c4a73860e3` | `606b02f3f38213f82ac17304c06cc8ac34ea67b199e5a7c52af5e848f37f660f` |
| `definitie-toetsregels/SKILL.md` | `ccad07dd20373a3c25b22c3c410239aaa1b61d651761e19ff06b7a4a01d43704` | `8679a5f5987e9fbbf735ff3f155d8632d950c67bf2c935ad6c42ee06136d0465` |
| `definitie-nederlandse-definities/reference.md` | `9de8d90083df1239ec02ece2f4eccea76358462112b0e9eab14a2d94910dd5c5` | `8a616096cf6cffb242ff9f044d075d45eb02de18666ba078f988d4ee137a5d67` |

Wijkt een "vóór"-hash af van de actuele bron, dan is die bron intussen
gewijzigd en moet de patch opnieuw beoordeeld worden (`patch --dry-run`).

## Toepassen (door de coördinator, niet door deze sessie)

```bash
cd /Users/chrislehnen/Projecten/_claude-global-setup
shasum -a 256 skills/definitie-toetsregels/reference.md skills/definitie-toetsregels/SKILL.md skills/definitie-nederlandse-definities/reference.md   # vergelijk met "vóór"
patch -p1 --dry-run < /pad/naar/Definitie-app/docs/analyses/DEF-622-skillpatch-v1.patch
patch -p1 < /pad/naar/Definitie-app/docs/analyses/DEF-622-skillpatch-v1.patch
# daarna: scripts/sync-rules.sh --sync → commit → push (globale setup)
```

## Bronnen

- Besluiten B-01..B-10: `/Users/chrislehnen/.codex/worktrees/ab46/Definitie-app/docs/analyses/def606-regeldossiers/CON-01-verdieping/besluiten-v10.md` (B-02)
- Productnorm in code: `src/toetsregels/regels/CON-01.json` (`score_policy: no_score`), `src/services/prompts/modules/context_awareness_module.py` (`CONTEXTNAAM_NORM`), `src/services/prompts/modules/json_based_rules_module.py` (CON-01), `src/services/prompts/modules/definition_task_module.py` (checklist)
- Tests: `tests/unit/services/prompts/test_def622_con01_promptnorm.py`
