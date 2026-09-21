# ESS-04 — toetsbaarheid

11 september 2026 · v1 · basis `d68a98a909630e15db6e1cb9c9c8171f957bff9d`. Onderzoek. [Plan](../../plans/2026-09-11-def606-analyseplan-v3.md).

## 1. Doel

Een beoordelaar moet op basis van de criteria kunnen bepalen of een geval onder het begrip valt. Cijfers zijn noch noodzakelijk noch voldoende; schijnprecisie kan onduidelijkheid verbergen.

## 2. Norm

[Record/hash](ESS-04-bewijs-v1/uitkomsten.json): verplichte ASTRA-regel; sinds DEF-624 menselijke review, buiten score. Goede/foute voorbeelden zijn zinsfragmenten, geen volledige normdefinities. Geen verse ASTRA-bevestiging.

## 3. Toepasselijkheid

Generatie geen willekeurige drempels verzinnen. Toetsing/import criteria bewaren. Review/vaststellen eisen een herhaalbaar oordeel voor de bedoelde context, niet aanwezigheid van een getal.

## 4. Context

Noodzakelijk als maatstaf, meetmoment of populatie daarvan afhangt. Werk-/kalenderdagen, noemer en peildatum expliciteren waar relevant; geen universele metadata-eis voor elk kwalitatief kenmerk.

## 5. Definitiebronnen

Bron/versie kan een drempel of besliscriterium dragen. Een getal zonder onderbouwing niet als objectieve waarheid toevoegen. Toetsbaarheid van een criterium bewijst nog niet dat het juiste begrip ermee is afgebakend.

## 6. Ontologie

Welke kenmerken bepalen lidmaatschap, welke zijn toevallig? Relaties/kwaliteiten helpen meetobject en populatie bepalen. Meetbaarheid is breder dan numerieke meting; abstracte begrippen kunnen kwalitatieve criteria hebben.

## 7. Aanvullingen

Voorbeelden voldoen; praktijkvoorbeelden leveren waarneembaar bewijs; tegenvoorbeelden falen op een criterium; grensgevallen tonen drempel/inclusiviteit. Synoniemen moeten criterium behouden, homoniemen meetobject onderscheiden. Toelichting kan methode uitleggen, maar niet een ontbrekend essentieel criterium verbergen.

## 8. App

Judgment-evaluator vraagt altijd review en gebruikt patronen slechts als signaal. Geen terugkeer naar getal=pass. Signalen/status in bewijs bewaard; volledige UI-reviewregistratie niet opnieuw getest. [Adapterbeperking](../2026-09-11-def606-productonderzoek-bewijs/proeven-v1.json).

## 9. Skills/prompts

Toetsregels-/definitieskill moeten geen numerieke drempels eisen waar een kwalitatief criterium volstaat. Voorbeeldenvaardigheid helpt grensgevallen; ontologie bepaalt relevante eigenschap. Reviewer is geen willekeurige AI-score.

## 10. Status/score

Review_required/excluded_from_score. Signalering, feitelijk uitgevoerde review en afgeronde bewijscontrole afzonderlijk tonen. Lege tekst review_required is geen inhoudelijk oordeel.

## 11. Proeven

[Zeven gevallen](ESS-04-bewijs-v1/gevallen.json), [14 resultaten](ESS-04-bewijs-v1/uitkomsten.json), offline manager/cache gelijk, exitcode 0: beide fragmenten, kwalitatief criterium, ongefundeerd getal, ontbrekende noemer, waarneembare handtekening en leegte allemaal review_required. Geen menselijke normoordelen geautomatiseerd voorgesteld als bewezen.

## 12. Samenhang

ARAI-03 kwalificaties, ESS-03 telcriteria, ESS-05 onderscheidbaarheid. Een reproduceerbaar gemeten eigenschap kan nog niet essentieel zijn. Review die twee vragen apart.

## 13. Voorstel en review

Voorstel: essentieel kenmerk, toetscriterium, bewijsbron en relevante meetcontext; kalibreer reviewers met onafhankelijk gelabelde grensgevallen. [Claude](ESS-04-bewijs-v1/claude-review.json) noemt temporele ankers en interbeoordelaarsbetrouwbaarheid: overgenomen. Zijn voorbeeldberekening ‘65 uur’ is onjuist en niet gebruikt; de algemene tijdzonevraag blijft geldig. Een arbitrair percentage mag niet als oplossing voor ‘substantieel’ worden ingevoerd. Open: bewijsniveau, beoordelingscriteria en methodeverwijzing.

## 14. Acceptatie

Kwalitatief/numeriek, noemer, inclusieve grens, referentietijd, bronconflict, twee reviewers en lege tekst; beide laadpaden en UI houden signalen/review/besluit gescheiden. Onderzoek gereed; volgende ESS-05.
