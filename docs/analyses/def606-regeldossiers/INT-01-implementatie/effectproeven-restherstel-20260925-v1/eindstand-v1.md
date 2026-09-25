# DEF-770 — eindstand van de restherstelproef

25 september 2026. **Het generatie-effectcriterium is gehaald; T24-acceptatie nog niet. De PR’s zijn niet mergegereed.**

## Vastgelegd en gepusht

- App: `108f38a3933cfe1335908d77a1aaadf0f8f36cc3`, draft-PR [474](https://github.com/Chris-Lehnen-ICT-CONSULTING/Definitie-app-zakelijk/pull/474).
- Skills: `990ec253067f6a0ef212f8b6b41cc38570acfeb4`, draft-PR [356](https://github.com/ChrisLehnen/claude-global-setup/pull/356).

Losse labels krijgen nu een onderbouwde open beoordeling. De onveilige uitbreiding van titelherkenning is verwijderd; het expliciet goedgekeurde beleid voor nominale titelvervolgen is verwerkt. Contract: `def770-int01/7`.

De generatie-instructies behouden afbakenende voorwaarde-gevolgrelaties en ontkende gevolgen. Eigenschappen die volgens de bron mogen veranderen, worden niet als vaste eisen toegevoegd. App en skills zijn afgestemd. Er is geen extra modelaanroep, dependency, schemawijziging of live skillsactivatie ingevoerd.

## Review en technisch bewijs

Claude Code CLI implementeerde, sessie `442a98fb-a377-403f-996e-433cf4a664fc`. Dezelfde Codex CLI-reviewer controleerde met Astra/high de concrete diffs en correcties, sessie `01a0cfac-ea05-7700-ba73-8b5659751c1c`. Alle concrete bevindingen uit de bron- en testreview zijn gesloten.

De map `technisch-bewijs-v1/` bevat rapporten, patchidentiteit, XML en logs. `bronbinding-v1.json` verbindt de definitieve commits en het bronarchief met de gereviewde bytes.

- Volledige unit-run op identieke productcode: 7.443 geslaagd, 75 overgeslagen, 3 verwachte fouten. Twee daarvan waren tijdelijke beleidsverwachtingen; die zijn daarna vervangen en met 440 gerichte controles geverifieerd. De laatste assertiecorrectie heeft 47 geslaagde controles. De bestaande verwachte fout voor DEF-609 blijft.
- Gepinde Ruff, Black en `make lint`: geslaagd.
- Bundels: 94 tests en 2 subtests geslaagd.
- CI op de broncommits: app 36/36, skills 3/3 geslaagd.

Dit technische bewijs vervangt de inhoudelijke acceptatie niet.

## Onafhankelijke proeven

### T24: 23/24 conform

Alle 19 zekere automatische beslissingen zijn normatief ondersteund. Beide laadpaden en opslag zijn bij alle 24 gevallen consistent; er zijn geen uitvoeringsfouten.

Nieuwe afwijking T17:

> bord met de tekst ‘Ga verder!’ dat tijdens een oefening een vrije doorgang markeert.

Beide onafhankelijke referenties en de adjudicator verwachten een automatische pass; de app vraagt inhoudelijke beoordeling. De dat-bijzin begint ná het citaat en wordt niet veilig automatisch herkend. Dit is een bestaande dekkingsbeperking, geen nieuwe regressie. Dispositie: Important/open binnen DEF-770.

De vraag om een algemene grens voor citaatvervolgen die grammaticale interpretatie vereisen, staat nog open. Het beleid en de historische labels zijn niet stilzwijgend veranderd. Zie `t24-rapport-v1.md` en `t24-onafhankelijke-bewijsreview-v1.md`.

### G24: effectcriterium gehaald in deze kleine AI-proef

Drie paren zijn inhoudelijk beter, negen gelijk. Er is geen waargenomen verslechtering of aangetoonde nieuwe betekenisfout. Ruwe en opgeschoonde teksten krijgen hetzelfde gepaarde oordeel.

Er blijven gedeelde tekortkomingen bij G04 en interpretatieonzekerheid bij G02. Dit bewijst geen volledig juiste definities of algemene betrouwbaarheid. Zie `g24-rapport-v1.md` en de verzegelde adjudicatie.

## Budget en vervolg

Chris heeft het cumulatieve generatieplafond expliciet verhoogd naar US$8,10. Deze 24 aanroepen kosten US$1,818475. Het totaal is US$7,533075; er resteert US$0,566925.

DEF-770 blijft In Progress. De volgende afhankelijke stap is het antwoord op de algemene citaatgrens, gevolgd door passende uitvoering en onafhankelijke toetsing. De PR’s blijven drafts; er is niet gemerged of live geactiveerd.
