# INT-02 — review van de coördinator (A/Cowork) op onderzoeker C (Codex in de ChatGPT-app) — v1

25 september 2026 · DEF-771 · beoordeeld: `c-codex-app/onderzoek-c-v1.md`, `casusregister-c-v1.md`, `manifest-c-v1.json`, `bewijs/` (proefopzet, proeven-c-v1.py, proefuitkomsten, exitstatus 0, uitvoering-en-grenzen). C is op verzoek van Chris later gestart (08:33 UTC) met dezelfde feitenbasis, geïsoleerd van A/B en van de gedeelde conclusies; C's v1 is opgeslagen vóór het lezen van A, B of de synthese. Deze review vergelijkt C met de gezamenlijke synthese v2 (A+B) en benoemt wat C toevoegt. Formaat: punt → claim/sectie van C → oordeel → bron/tegenbewijs → gevolg.

**RA-C-01** → C §Q1 norm N1 (breed) met N0 (eng) als K1; "gebonden handelingsopdracht is niet enkel door haar determinisme een afleidingsregel"; kwalitatief criterium ≠ beslisregel; beschrijving van verplichting/bevoegdheid/procedure/rechtsgevolg ≠ overtreding → **bevestigd; onafhankelijk gelijk aan A/B/CO** → dezelfde functiegrens, dezelfde uitzonderingen, dezelfde variantkeuze; C's zin over determinisme is een nuttige precisering (voorkomt dat "deterministisch" als vrijbrief voor een gebonden procedure wordt gelezen) → **gevolg:** zin opnemen in de normtekst (v3).

**RA-C-02** → C §Q5 strategie: O1 voorkeur, O2 apart, O3 ondersteunend; zes technische statussen incl. `not_applicable`; geen NA-klasse voor afleiding/leegte; onderscheid "review niet uitgevoerd" ↔ "onvoldoende informatie"; K4 expliciet product­besluit, niet afgeleid uit de gatelek → **bevestigd; gelijk aan synthese v2 §4** → geen wijziging.

**RA-C-03** → C P5 (UI-helper `_statuslijst_regels` met geïnjecteerd resultaat: alleen "Nog te beoordelen: INT-02", geen reden/signaal/expander) → **aangevuld: nieuw functioneel bewijs** → A/B hadden dit alleen als codelezing; C voert de helper werkelijk uit (geen Streamlit-schermtest) → **gevolg:** bewijsniveau in synthese §1 opwaarderen naar "functieproef (C-P5), geen schermtest".

**RA-C-04** → C P6 (`_evaluate_gate` als echte bronfunctie met gestubde CON-01/02-hulp: bij score .9 pass ongeacht INT-02-reviewitem; bij score None blocked) → **aangevuld: nieuw functioneel bewijs** → bevestigt A's/B's codelezing "gate leest geen INT-02-reviewlijst" en B's "score None kan blokkeren" op functieniveau; geen DB/bevoegdheid/echte vaststelling → **gevolg:** opnemen in §1 keten; K4-tekst ongewijzigd.

**RA-C-05** → C §Q4 "Review na herladen: `expert_review_tab._v2_uit_opgeslagen_validatie` bouwt violations uit legacy issues, geen rule_statuses/review_required; bij lege issues None" → **aangevuld: nieuw ketenfeit (codelezing)** → verscherpt B's issues-helper-bevinding: ook bij herladen van de expertreview reconstrueert de fallback geen open INT-02-oordeel → **gevolg:** toevoegen aan §1 keten en aan "geparkeerd/DEF-626" in de besluitnotitie (uitvoeringsacceptatie).

**RA-C-06** → C §Q4 export: `export_service.py:531` JSON bevat toetsresultaten; gate standaard uit → **aangevuld** → concreter dan B's "optionele async gate"; geen exportproef → **gevolg:** §1 keten preciseren ("JSON-export bevat toetsresultaten; welke INT-02-velden meereizen is niet bewezen").

**RA-C-07** → C P4 (cleaning: label van C100 weg, afleiding en `indien` intact; C03 ongewijzigd) → **bevestigd; gelijk aan B-P3** → twee extra inputs; geen algemene garantie → geen wijziging.

**RA-C-08** → C §Q4 "P3 las runstatus per abuis onder `status`" → **bevestigd als correcte zelfcorrectie** → INT-02-velden juist gelezen; runstatus niet geclaimd → geen gevolg.

**RA-C-09** → C keuzestructuur K1–K5 (C-K2 "criteria en grensgevallen" als aparte keuze; C-K3 evaluator; C-K4 uitkomst/poort; C-K5 herstel) → **beleidskeuze-indeling verschilt, inhoud gelijk** → de synthese vouwt C-K2 in K1 (uitzonderingen zijn onderdeel van de normkeuze); C-K3 = K2, C-K4 = K4, C-K5 = K5 → **gevolg:** concordantie C toevoegen aan de besluitnotitie; geen nieuwe keuze.

**RA-C-10** → C casussen C100–C118 → **aangevuld; geen tegenspraak met register v2** → nieuwe onderscheidende gevallen: C105 ("De medewerker laat de aanvrager toe." — voorschrift met nul signaalwoorden, VN onder N-breed), C107 (constitutief oordeel "naar het gemotiveerde oordeel van de beoordelaar" → O bij onduidelijke functie; niet elk menselijk criterium is discretie), C112 (definitie van een *verplichting* zelf → V), C113 (negatief lidmaatschapscriterium → V), C116 (afgeleide grootheid "dagtotaal" → V; spanning met ESS-04 "rekenmethode naar toelichting" te benoemen), C106 (paar mét bevestigde equivalentie → beide V; toont dat C57 een tegenvoorbeeld is, geen regel), C108 (bronconflict → O), C109 (nabewerking verliest grens → transportdiagnose), C114 (gezaghebbende bron met voorschrift, aangeboden als definitie → VN blijft VN ondanks brongezag), C117 (AI-citaat niet in invoer → error), C118 (versiewissel onder zelfde record-ID → opnieuw beoordelen) → **gevolg:** C100–C118 opnemen in het gezamenlijk casusregister v3 als C-rijen; C105, C107, C112, C114, C116 als extra voorbeelden in het skillcontract (§6).

**RA-C-11** → C §Q5 metadata: brondocument "ASTRA; aldaar verwijzing naar DBT §4.2" met afzonderlijke normprovenance en lokale uitwerking (DEF-625) → **bevestigd; gelijk aan B** → geen wijziging.

**RA-C-12** → C §Q5 meldingen (Nog te beoordelen / passagehulp / geen treffer / V / VN / O / NB / Error) → **bevestigd; inhoudelijk gelijk aan B3 V06** → C's "geen treffer"-melding is korter; synthese houdt de B-tekst (met expliciete waarschuwing dat een voorschrift zonder signaalwoord voorkomt) → geen wijziging.

**RA-C-13** → C §Q1 "ASTRA-revisie: historisch bronrapport noemt oldid 8695; gelijkheid met de raw-snapshot van 25-09 niet bewezen" → **aangevuld** → concreter dan "revisie onbekend" → **gevolg:** bewijsgrens §10 preciseren.

**RA-C-14** → C §Q3/Q5 "spanning ESS-04 'rekenmethode naar toelichting' ↔ afleidingsregel in de kern (C116)" → **aangevuld; open relatiepunt** → onder INT-02/ASTRA hoort de afleiding in de definitie; als de ESS-04-skill rekenmethoden naar de toelichting wil, is dat een buurregelspanning → **gevolg:** opnemen in §7 als te benoemen spanning (eigenaar ESS-04), geen INT-02-besluit.

**Materieel voor v3:** RA-C-01 (normzin), RA-C-03/04/05/06 (bewijsniveau en ketenfeiten), RA-C-10 (casussen), RA-C-14 (relatie ESS-04). **Niet materieel:** RA-C-02, 07, 08, 09, 11, 12, 13. **Geen tegenspraak** tussen C en de synthese v2 op norm, uitzonderingen, evaluatorstrategie, poort, herstel of bestaand beleid; C's onafhankelijke convergentie versterkt de voorstellen maar is, zoals C zelf zegt, geen normbewijs.

Volgende overdracht: C krijgt de synthese v3 (met deze review verwerkt) voor één synthesecontrole (weglating, standpuntweergave, tegenspraak, betekenisverlies); daarna alleen gerichte verwerking.
