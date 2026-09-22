# CON-02 — samengebrachte voorbeoordeling en deskundige beslispunten

16 september 2026. **Klaar om te beoordelen; nog geen menselijke acceptatie.**

## Leesvolgorde

1. [Eerste zes concrete gevallen met Codex-voorstel](codex-voorbeoordeling-v1.md).
2. [Cowork v2: onafhankelijke brongebonden voorbeoordeling](cowork/deskundigenformulier-c02p-v2.md), met [alle 31 machineleesbare beoordelingen](cowork/deskundigenformulier-c02p-v2.json).
3. [Canoniek formulier met alle 31 scenario's en lege menselijke velden](deskundigenformulier.md). Dit formulier en het [acceptatieregister](acceptatie-register.json) bewaren de historische invoer en projectbesluiten.

De voorgestelde startset is **P01, P02, P04, P11, P16 en P31**. Cowork koos zelfstandig een andere startset (P01, P15, P03, P20, P12, P31); beide keuzes staan zichtbaar in hun eigen stukken. Er zijn geen scenario's vervallen of hernummerd.

## Gezamenlijke grondslag

Codex legde zijn voorbeoordeling vast vóór ontvangst van Coworks nieuwe antwoord. Cowork werkte in de bestaande taak `CON-02 independent research and cross-review`, `cse_019rnMHmYzz1sXr4ZYoX8SoN`, met de eerder uitgewisselde bronbasis en de drie inmiddels goedgekeurde productbesluiten. Claude Code CLI bouwde het formulier en de integriteitscontrole; Codex CLI reviewde de pakketcode onafhankelijk.

Beide inhoudelijke beoordelingen zijn AI-voorstellen. Geen van beide is een live modeloordeel uit de Definitie-app, een menselijke goldset of bewijs dat de volledige gebruikersketen is doorlopen. De twee AI-oordelen worden niet gemiddeld en stemmen tellen niet als bewijs.

## Verwerkte concrete correcties op Cowork v1

| Punt | Correctie in v2 |
| --- | --- |
| P31: beschikbare hyperlink | De beschikbare gerichte link moet worden geregistreerd. Een verwijzingsuitzondering voor een bron zonder bruikbare link past hier niet. Een echte uitzondering blijft zichtbaar als uitzondering en wordt geen gewone positieve beoordeling. |
| P04: herkomst versus geen bron gevonden | Onbevestigde herkomst van een upload is niet hetzelfde als het onderbouwd ontbreken van een geschikte bron. De wettelijke locator in de kop blijft erkend; versie, hyperlink en herkomstverificatie ontbreken. Dit is ook verduidelijkt bij P07/P24. |
| Letterlijke citaten | Genormaliseerde tekens en samengevoegde passages zijn vervangen door afzonderlijk controleerbare letterlijke fragmenten. Samengestelde citaten zijn expliciet gelabeld. |
| Volledige invoer | P29–P31 bevatten nu ook de oorspronkelijke velden `citation_display` en `source_hyperlink`. |
| Beoordelingslaag | Elke Cowork-casus onderscheidt de aanwezige fixture/manifestgegevens van de onbewezen doorgifte, opslag en export in de app. |

Cowork v1 blijft ongewijzigd bewaard als herkomst van deze correcties; **gebruik v2 voor de voorbeoordeling**. De redactionele claim dat P15 het enige geval met drie positieve voorstellen is, is eveneens ingetrokken.

## Zelf gecontroleerd aan Cowork v2

- 31 oorspronkelijke invoerobjecten exact gelijk aan het historische register, inclusief de extra verwijzingsvelden.
- Alle menselijke besluitvelden leeg.
- 111 citaatfragmenten letterlijk teruggevonden in de bijbehorende fixturebytes; iedere genoemde fixturehash gecontroleerd.
- JSON SHA-256: `5ed54b674bc7beb99520b4281c7722077030e9a834fde0e690368a6f93053ebf`.
- Markdown SHA-256: `c7e23db0917718b34ee17c6686d44e3a036cbc1388ff23a68e8c66fa87535e4a`.

Dit bewijst tekst- en bronintegriteit. Het bewijst niet dat alle inhoudelijke AI-oordelen juist zijn. De `fixtures/...`-paden in de ongewijzigde Cowork-export verwijzen in dit samengebrachte pakket naar dezelfde relatieve bestanden onder `bronfixtures/`.

## Onderscheid dat bij acceptatie behouden moet blijven

**Een goede verwijzing in het bronmanifest is nog geen goede verwijzing in het app-record.** Cowork stelt bijvoorbeeld P01 positief voor op basis van manifest plus fixture. Codex stelt voor de app-uitvoering de aanvullende voorwaarde dat diezelfde bronversie, locator en gerichte hyperlink daadwerkelijk aankomen. Deze claims zijn verenigbaar als de beoordelingslaag wordt vermeld; ze mogen niet tot één onvoorwaardelijke app-pass worden samengevoegd.

**Bronselectie versus inhoudelijk juist antwoord:** P10 bevat de dierenuitzondering in het corpus, maar niet in de geselecteerde top vijf. De deskundige kan met het volledige dossier weten dat de definitie onjuist is. Dat maakt de ontbrekende passage nog geen door het model ontvangen bewijs. P11 biedt die passage wel aan. Een definitie inhoudelijk afwijzen en een ontoereikende bewijsset melden blijven verschillende waarnemingen.

**Governance versus normoordeel:** P26 kan inhoudelijk dezelfde betekenissteun hebben als P01. Een los `reviewed=true` bewijst desondanks geen menselijke beoordeling. Een positief CON-02-voorstel heft de aparte vaststelpoort van DEF-630 niet op.

## Nog inhoudelijk te beslissen, niet door AI-consensus afgedaan

1. **P14: afgeleide wiki zonder primaire bron.** Cowork stelt drie negatieve deeloordelen voor. Codex heeft de primaire binding als onopgelost aangemerkt. Bepaal afzonderlijk of de beschikbare afgeleide tekst de betekenis steunt en wat het ontbreken van de primaire onderbouwing voor brongezag betekent. Ontbrekende authenticiteitsbinding is op zichzelf geen bewijs dat de definitiezin inhoudelijk onjuist is.
2. **P24: origineel versus gemuteerde bron.** Coworks positieve betekenisvoorstel geldt uitdrukkelijk tegen de oorspronkelijke upload. De daadwerkelijke casusstap vervangt de bron door een mutant. Leg dus het oordeel voor beide versies apart vast; de positieve voorwaarde voor het origineel mag niet als verwachte uitkomst na mutatie gelden.
3. **P30: lange maar precieze citeervorm.** Cowork houdt verwijskwaliteit op `nog te beoordelen`; Codex signaleert een concrete verkortingsactie volgens de vastgelegde toelichting. De deskundige bepaalt de gewenste uitkomst voor het verwijsonderdeel. De juiste betekenis wordt niet vanwege citeerlengte afgekeurd.

Deze punten blijven zichtbaar in de deskundige acceptatie. Ze zijn geen nieuwe productkeuzes en heropenen de drie goedgekeurde besluiten niet.

## Hoe de eerste acceptatie vastleggen

Beoordeel eerst P01: ondersteunt de bewaarde Awb-passage de volledige besluitdefinitie binnen het gekozen Awb-profiel? Noteer afzonderlijk akkoord, afwijzing of aanpassing voor brongezag/toepasselijkheid, betekenissteun en de beschreven verwijzingsvoorwaarden. Vermeld naam, rol, datum, casus-ID en pakketversie. Vervolgens P02, P04, P11, P16 en P31.

Er is nog geen menselijk oordeel ontvangen. Een akkoord om het werk voort te zetten, publicatie van dit pakket of een geslaagde integriteitscontrole vult die velden niet in. Na vaststelling van de verwachtingen kan de appuitvoering ertegen worden afgezet; werkelijk ontvangen passages, uitkomsten en afwijkingen moeten dan per casus worden bewaard.
