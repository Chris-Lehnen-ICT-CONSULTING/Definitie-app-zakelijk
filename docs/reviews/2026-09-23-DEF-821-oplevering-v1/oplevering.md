# DEF-821 — oplevering en effectevaluatie
23 september 2026

De ESS-04-generatie-instructie en de aparte verduidelijkingsroute zijn samen geïmplementeerd. Bij ontbrekende noodzakelijke betekenisgrond vraagt de app verduidelijking en slaat zij geen definitie op. De technische review is akkoord; de modelproef toont beperkte, concrete kwaliteitswinst binnen de vooraf vastgelegde proefset.

## Uitkomst van de modelproef
32 echte generatieaanroepen: acht synthetische casussen × twee versies × twee herhalingen. Dezelfde modelconfiguratie (Anthropic `claude-opus-5`, temperature 0.1, max_tokens 500), volledige appprompts, antwoordcache uit en tegengebalanceerde versievolgorde. Geen infrastructuurblokkades; precies één aanroep per casus/versie/herhaling. SDK-responsmetadata, ruwe tekst, prompt, appuitkomst, database en readback zijn bewaard.

De onafhankelijke Codex-beoordelaar kreeg per paar geschudde A/B-labels en las de sleutel niet. De uitvoervorm blijft herkenbaar en de beoordelaar kende het normontwerp: dit is geen volledig geblindeerd onderzoek.

| Uitkomst na ontsluiten labels | Aantal paren |
|---|---:|
| Verbeterd | 6 |
| Gelijk | 10 |
| Verslechterd | 0 |
| Onzeker | 0 |

De verbetering betreft D3 (onbepaalde 80%-eis), D4 (onbesliste dagconventie) en H1 (strijdige grenzen 70%/90%), elk tweemaal. De oude versie sloeg verzonnen of onbepaalde kandidaten op; de nieuwe versie vraagt de ontbrekende keuze of grond en slaat niets op. Bij D1, D2, D5, D6 en H2 blijven kwalitatieve criteria, noemer/inclusie, gevalsbewijs, werkdagtermijn en actor/tijdsgrens behouden. H1 en H2 zijn vóór de proef vastgelegd en buiten implementatie/tuning gehouden.

**Resterende beperking:** beide nieuwe D3-antwoorden krijgen ‘deels’: ze vragen naast de terechte criterium/noemer-vraag ook naar een meet-/peilmoment waarvan de noodzaak niet is onderbouwd. Dit is geregistreerd als [DEF-828](https://linear.app/definitie-app/issue/DEF-828). De nieuwe antwoorden zijn beter dan de oude verzinsels, maar niet foutloos.

Dit bewijst een beter modelresultaat op deze kleine synthetische proefset. Het bewijst geen algemene kwaliteitswinst op praktijkdefinities en geen betere oordelen van gebruikers. Een representatieve gebruikersproef en menselijke normannotatie zijn niet uitgevoerd. De app heeft geen nieuwe automatische ESS-04-jury gekregen.

## Wat is gewijzigd
- Exacte G2-v5-instructie in de ESS-04-regelkaart; volledige eindprompt laat beide aparte niet-succesuitkomsten toe.
- Strikt uitvoercontract `BETEKENISGROND ONTBREEKT:` met `ontbrekende_grond` en `vraag`; misvormde/gemengde meldingen falen veilig.
- Aftakking vóór opschoning, verrijking, validatie en opslag; transport en UI tonen de modelmelding apart.
- Expliciet verzonden verduidelijkingen blijven met hun vraagcontext behouden tijdens dezelfde invoergebonden keten. Invoerwijziging maakt de hele keten ongeldig; budget- en aantalgrenzen worden vóór het model gecontroleerd.
- Bestaande ESS-02-conflictroute blijft behouden. ESS-04-record, patronen en `judgment_review/review_required/excluded_from_score` blijven ongewijzigd.

De bestaande skillreferentieblokken bij Claude en Codex zijn bytegelijk (SHA256 `f113e264abc2b8c0519cff8d82536b1317c4f9d3e3c83ac2d383b1b25bb7a3bd`) en dragen dezelfde norm als het apprecord. Zij zijn in deze appwijziging niet opnieuw gewijzigd.

## Acceptatie en verificatie
| Criterium | Bewijs |
|---|---|
| AC1 consistente G2/eindprompt | Exacte-tekst-, volledige-prompt- en budgettests; live gebruikte prompts bewaard |
| AC2 strikt uitvoercontract | Parserproeven plus onafhankelijke beschadigde-kop/payload-proeven |
| AC3 geen definitieopslag bij melding | Echte keten en SQLite: nul opslag vóór downstream; ook live bij alle zes nieuwe verduidelijkingsuitkomsten |
| AC4 UI en hergeneratie | Streamlit AppTest, handler/adapterketen, opeenvolgende vragen en invoerbinding |
| AC5 opslag/readback | Tijdelijke echte repositories, kandidaatregistratie gelijk aan opgeslagen betekenis; live readbacks bewaard |
| AC6 normconsistentie | Regelrecord/patronen ongemoeid; G2 en actieve skills vergeleken |
| AC7 tests en review | 7.091 passed, 75 skipped, 1 xfailed en 21 subtests; make lint en eigen script/testlint groen; reviewbevindingen gesloten |
| AC8 daadwerkelijk effect | 32 echte calls, vooraf vastgelegde cases/verwachtingen, twee heldoutcases, onafhankelijke inhoudelijke beoordeling en bovenstaande beperkte conclusie |

De definitieve unitgate gaf exit 0 op codecommit `7d962a1b9d297c45ce27709aedac906f2a80be0a`; log `tests/integratie-eindcontrole-v1/make-test-coordinator-v2.log` in het bewijsarchief. Een eerdere achtergrondrun werd bij CLI-sessie-einde beëindigd en telt niet als eindbewijs. De oorspronkelijke versie had 7.046 geslaagde tests; alleen het definitieve resultaat hierboven onderbouwt de oplevering.

## Onafhankelijke review en rolverdeling
**Implementatie:** echte Claude Code CLI 2.1.280, sessie `9e8db6b1-7b00-46fa-8c1d-23c9e2fc0f22`. Dezelfde sessie schreef code/tests/prompts en verwerkte correcties. Effectieve tools: Bash, Edit, Glob, Grep, Read, Write; geen Agent/Task of MCP-servers.

**Review en inhoudelijke effectbeoordeling:** afzonderlijke Codex CLI 0.156.1, sessie `01a0ced8-9eb6-7cf2-b267-758d5ca0fd2b`, bron read-only, agentfuncties en MCP-servers uitgeschakeld. Dezelfde reviewer controleerde de correcties en beoordeelde de echte outputs. De coördinator schreef geen applicatiecode/tests/promptwijzigingen; wel specificatie, proefinvoer, orchestratienotities en deze bewijsverantwoording.

De eerste review vond twee Important-bevindingen: beschadigde meldingskop als definitie opgeslagen; eerste antwoord verloren bij een vervolgvraag. Beide zijn hersteld en onafhankelijk opnieuw gereproduceerd: nu nul opslag respectievelijk behoud van beide antwoorden tot validatie/readback. Geen resterende blokkerende codebevindingen.

- [Eerste review](review-eerste-versie.md)
- [Gerichte herreview](review-correcties.md)
- [Inhoudelijke beoordeling van alle 16 paren](effectbeoordeling.md)
- [Ontsloten telling en motivering](effectuitkomst.json)

## Versies en reproduceerbaarheid
Oorspronkelijke uitvoeringsbasis: `b687c1615d4abd30b5b6d38dd55e64f6a758e187`. Tijdens uitvoering kwam PR472/DEF-766 op main; die is zonder conflict via reguliere merge geïntegreerd. Om haar effect niet aan ESS-04 toe te schrijven gebruikt de effectproef **baseline `26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`** tegenover **nieuwe code `7d962a1b9d297c45ce27709aedac906f2a80be0a`**. De werkboom was schoon tijdens de liveproef. Featurecommit: `4af0dc488`.

De oorspronkelijke cases/verwachtingen zijn bij deze basiswijziging niet aangepast. SHA256 volledige caseset: `187dafdfdb38260ca9e68513b9ad144732845a4c4a760da134dab30b368cfa56`. Vooraf apart vastgelegde heldoutset: `7c80f1519a91111d3e48e24369cb6f3f676ec1003d9a2c9a7abecc51669615ae`.

De proef gebruikt de echte orchestrator, promptservice, security/cleaning, validatie en repository. Gelijk uitgeschakeld voor beide varianten: synoniemen, web lookup, RAG, voorbeelden en CON-02 AI-bronbeoordeling. UI/adapter zijn buiten de live-lus en apart technisch beproefd. Geen productiegegevens of productie-DB gebruikt.

Reproduceer met `scripts/testing/def821_effectproef.py`, expliciete `--basis-ref 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3`, de cases uit het archief en een nieuwe uitvoermap. Standaard offline; echte aanroepen vereisen `--live` en eigen appconfiguratie. Scriptdefault blijft om herkomstredenen de oorspronkelijke basis; gebruik voor deze vergelijking dus expliciet bovenstaande basis.

## Bewijsarchief
[bewijs.zip](bewijs.zip) bevat 261 bestanden inclusief manifest: CLI-transcripten, eerste en definitieve tests, protocollen, cases, labelvrije beoordeling/sleutel, volledige liveprompts, ruwe API-uitkomsten, modelinstellingen en tijdelijke databases/readbacks. De oorspronkelijke absolute verwijzingen in de reviewverslagen zijn behouden; het archief bundelt hun bewijs duurzaam onder `cli/`, `tests/` en `evaluatie/`.

SHA256: `e57ce8cb64115216d65378485908d3b685c8f42b22e2c2c0a446c65e6b256f2b`.
Archiefintegriteit en alle inhoudshashes zijn gecontroleerd. Tijdelijke bronkopieën/caches/HMAC-sleutels zijn niet opgenomen; bronidentiteit staat in Git en het proefmanifest. Er zijn geen exacte geheime appconfiguratiewaarden in het opgenomen bewijs gevonden.

Status bij deze notitie: technisch geïmplementeerd en gereviewd op de featurebranch; kwaliteitswinst op de beschreven proefset vastgesteld, met DEF-828 als kwaliteitsvervolg. Merge en activering in de draaiende app zijn afzonderlijke stappen.

