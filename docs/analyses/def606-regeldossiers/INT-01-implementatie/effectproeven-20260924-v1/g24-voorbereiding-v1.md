# G24 — voorbereiding en open budgetbesluit

24 september 2026 · DEF-770 · nog **geen generatieaanroepen uitgevoerd**.

## Gereed

- Zes onafhankelijke synthetische brondossiers, vooraf verzegeld.
- Oude app `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`; gemergde nieuwe app `ee13ae1d7ce05482bd61f37dd51099b7ba8d23f0`.
- Twaalf variantprompts opgebouwd via de echte PromptServiceV2, met gelijke bron/context/modelinstellingen per paar en twee geplande herhalingen: totaal 24 generaties.
- Alle passages en doelgroepen zijn aantoonbaar volledig opgenomen. Proefafwijking: verliesloze fragmentering (maximaal 450 tekens) en dezelfde ondersteunde documentinstellingen 200/40000 in beide armen; de productieconfig is niet gewijzigd. Witruimtenormalisatie en reconstructie zijn vastgelegd.
- Claude Code CLI corrigeerde het harnas. Dezelfde onafhankelijke Codex CLI-reviewer (Astra/high) sloot alle vijf scriptbevindingen.
- 19/19 gerichte offline regressietests geslaagd. Tegen de oorspronkelijke scripts faalden 17 tests: 13 gedragsfouten en vier nog ontbrekende hulpfuncties; twee bestaande gedragingen slaagden al.
- Lange synthetische smoke en de echte offline voorbereiding slagen op beide appversies.
- Gratis provider-tokentelling uitgevoerd. Voor 24 generaties met maximaal 1000 uitvoertokens per call is de vooraframing **US$2,4553**, circa **US$2,46**, bij de geverifieerde standaardprijzen van Claude Opus 5 ($5/$25 per miljoen invoer-/uitvoertokens).

## Open

Het aan Chris gevraagde harde API-kostenplafond van **US$5** is nog niet bevestigd. Het runplan vereist vóór generatie een schriftelijk budgetbesluit. Er is daarom geen goedkeuringsbestand aangemaakt en geen betaalde run gestart. Tokentellingen zijn provider-ramingen; de runner bewaart werkelijke usage en stopt bij afwijking boven de tokenbegroting of het kostenplafond, zonder automatische retries.

## Relevante beperking vóór uitvoering

De prompts zijn voor G01, G04 en G05 byte-identiek in oud en nieuw; bij G02, G03 en G06 verschillen ze. Het manifest bevat daarom negen unieke API-verzoeken maar 24 geplande generaties. Variatie binnen de drie paren met identieke prompts mag niet worden toegeschreven aan de INT-01-instructiewijziging. Deze observatie wordt behouden; de verzegelde invoer is niet aangepast om alsnog een verschil af te dwingen.

De beoogde beoordeling is blind door de twee afzonderlijke Astra/high-beoordelaars, met adjudicatie bij verschillen. Dit blijft AI-beoordeling van een kleine synthetische set, zonder menselijke validatie of algemene kwaliteitswinstclaim. Zolang de generatie en beoordeling ontbreken is er geen G24-effectresultaat.

## Bewijs en vervolgstap

- [Bronnen, vooraf vastgelegde criteria en versies](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/bronmanifest-v1.json)
- [Verzegelde G24-invoer](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-invoer.json)
- [G24-manifest met alle prompts en 24 call-ID’s](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-manifest-v1.json)
- [Gratis provider-tokentelling en raming](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-20260924-v1/g24-tokentelling-v1.json)
- [Astra/high-vrijgave van de scriptcorrecties](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/logs/def770-effectproeven/astra-g24-herreview.md)
- [Gerichte regressie-uitkomsten](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/logs/def770-effectproeven/g24-regressie-groen-v1/uitslag.json)
- [Prijsbron, geraadpleegd 24 september 2026](https://platform.claude.com/docs/en/about-claude/pricing)
- [Tokentelling: gratis en een raming](https://platform.claude.com/docs/en/build-with-claude/token-counting)

Na het budgetantwoord: dat besluit binden aan de hashes van het bovenstaande manifest en de telling, vervolgens de 24 begrensde generaties uitvoeren, beide varianten met hun eigen appcode nabewerken, blind beoordelen en alle resultaten publiceren. De bestaande app-/skills-merges en T24-uitkomsten blijven behouden.
