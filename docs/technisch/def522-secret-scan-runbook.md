# Runbook — fail-closed secret-scan (DEF-522)

Gebruiksdocument: hoe je de gate draait en een uitkomst leest. Normatief zijn de
[SSOT — Implementatieplan DefinitieAgent kwaliteitsketen](https://linear.app/definitie-app/document/implementatieplan-definitieagent-kwaliteitsketen-645f1330ac28)
en de [DEF-522-specificatie — Onderzoeksresultaat en testontwerp](https://linear.app/definitie-app/document/def-522-onderzoeksresultaat-en-testontwerp-ac5285cc4e24);
dit runbook voegt daar niets aan toe en overrulet er niets van.

## Vereisten

- **Project-Python 3.13.** De pre-commit-entry start met `python3`; dat moet de
  actieve project-Python zijn. Een oudere Python zonder `tomllib` (< 3.11) kan de
  scanner niet laden en breekt de hook — activeer de project-venv voordat je
  commit.
- **Gitleaks 8.29.1, gepind.** Pre-commit bouwt die zelf via `language: golang`
  en zet hem op `PATH`; de entry vindt hem daar met `shutil.which`. Voor
  `make secret-scan` wijs je het pad expliciet aan. Installeren valt buiten dit
  runbook.

## De verplichte gate draaien

```
make secret-scan \
  SECRET_SCAN_BINARY="<absoluut pad naar de gepinde gitleaks>" \
  SECRET_SCAN_BASE="<volledig base-commit-ID>" \
  SECRET_SCAN_HEAD="<volledig head-commit-ID>" \
  SECRET_SCAN_SOURCE="<absoluut pad naar de checkout>" \
  SECRET_SCAN_CONFIG="<absoluut pad naar .gitleaks.toml>"
```

`SECRET_SCAN_BINARY`, `SECRET_SCAN_BASE` en `SECRET_SCAN_HEAD` zijn verplicht;
ontbreken ze, dan stopt het target. `SOURCE` en `CONFIG` defaulten naar de
checkout en `.gitleaks.toml` daarin, `SECRET_SCAN_TIMEOUT` naar 300 seconden.
Base en head zijn volledige commit-ID's — geen refnamen, geen vlaggen.

De gate doet, in deze volgorde:

1. alle invoer valideren (tool, config, scope, timeout, base, head);
2. vaststellen dat `SOURCE` de root van de werkboom is én op `HEAD` staat;
3. één volledige fetch van `origin`: alle heads naar `refs/remotes/origin/*` en
   alle tags. Geen prune, geen delete, geen terugval op een smaller bereik;
4. scannen: de range `base..head`, de canonieke historie (origin-heads, tags en
   de PR-head) én de actuele werkboom.

Alle vier zijn vereist. Er is geen HEAD-only terugval; een mislukte stap is
nonzero.

## Staged (pre-commit)

Bij een gewone commit scant de hook uitsluitend de index en doet hij geen enkele
uitspraak over de historie. Het is aanvullende lokale feedback en **vervangt de
CI-gate niet**.

## De hook in CI: het refpaar

Een CI-checkout heeft geen index, dus daar zou een indexscan altijd nul bytes
opleveren. Draait pre-commit met `--from-ref <base>` en `--to-ref <head>`, dan
zet het zelf `PRE_COMMIT_FROM_REF` en `PRE_COMMIT_TO_REF`, en draait dezelfde
entry de volledige modus: range, canonieke historie én werkboom. Beide waarden
zijn volledige commit-ID's; `--to-ref` is de werkelijk uitgecheckte HEAD
(`git rev-parse HEAD`), zodat het bereik samenvalt met de boom die de hooks zien.

De keuze hangt alleen aan de omgeving:

| In de omgeving | Modus | Wachttijd |
|---|---|---|
| geen van beide namen | staged (index) | 60 s |
| beide namen, volledige commit-ID's | full (range + historie + boom) | 300 s |
| één naam, of een waarde die geen commit-ID is | geen scan: `error`, nonzero | — |

Die laatste regel is opzet. Aanwezigheid van één van beide namen — ook met een
lege waarde — eist de volledige modus; de gate keurt de grenzen daarna af. Er is
dus geen route waarlangs een half of ongeldig bereik stil terugvalt op een lege
indexscan en groen geeft. Een ongeldig bereik in CI is een fout in de aanroep,
geen reden om de scan over te slaan.

## Een uitkomst lezen

De CLI schrijft één JSON-regel: `status` (`clean`, `blocked`, `error`), een
vaste `code`, plus `finding_count` en `scanned_bytes`. Ruwe rapporten,
tool-stdout en tool-stderr worden bewust niet gepubliceerd: die kunnen
secretinhoud dragen.

- Exitcode 0 hoort alleen bij `clean`, en `clean` vereist ook aantoonbaar
  gelezen bytes en een volledige eindmelding.
- `finding_count` telt **waarnemingen, geen unieke incidenten**: range en
  historie overlappen, dus hetzelfde secret kan meer dan eens meetellen.
- Bij `error` zijn de tellingen géén bewijs dat er niets is gescand: er kunnen al
  deelscans hebben gedraaid waarvan het resultaat niet wordt meegenomen. Wat
  telt is de nonzero exitcode — die blokkeert.

Gebruik voor triage het bestaande incidentproces, met alleen geautoriseerd
materiaal en zonder ruwe secretinhoud te publiceren. Persoonlijke of operationele
gegevens (UI-sessies, `.env`, de database) horen daar niet bij.

## De enige uitzondering in `.gitleaks.toml`

Eén allowlist, met `targetRules = ["aws-access-token"]`, `condition = "AND"`,
exact pad **én** exacte waarde, plus rationale, eigenaar (Chris Lehnen) en
reviewdatum. Valkuil bij wijzigen: een globale allowlist met `paths` wordt
toegepast als pad-skip vóórdat de inhoud wordt bekeken, en `condition` weegt daar
niet mee — het pad alleen zou dan een vrijbrief zijn. Alleen via `targetRules`
hangt de uitzondering aan de regel zelf en geldt de AND-voorwaarde echt.

## Tagconflict

De tag-refspec staat zonder `+`. Wijst een canonieke tag naar een ander commit
dan de lokale tag met dezelfde naam, dan faalt de fetch (`fetch_failed`, nonzero)
en blijft de lokale tag ongewijzigd. Niet forceren: eerst uitzoeken welke tag
klopt.

## Na een history rewrite

Een schone historie mag pas geclaimd worden nadat de hele poort is gedraaid in
een schone, volledige checkout. Nooit op basis van een HEAD-only controle, en
zonder automatische verwijdering van branches, tags of bestanden.

## Een onbekende historische finding

Die blijft blokkeren. Geen fixture-uitzondering en geen rotatieclaim zonder
bewijs. Volg het bestaande incidentproces (DEF-491); Chris Lehnen is
beslissingseigenaar. Providerrotatie en history rewrite vallen buiten deze PR.

Zet nooit credentials in instructies, commando's of logs.
