# cowork-review-op-codex-v1 — kruisreview op het Codex-onderzoek ESS-04

Claude Cowork, 18 september 2026. Review van het volledige Codex-pakket `codex-reviewpakket-v1/` na opslag van beide eerste versies.
Mijn eigen `cowork-onderzoek-v1.md` (sha256 `7f9138d152d1bd617c4df340bf52ce4c00b3cc1b4cec2bd8d55d9a4a07062708`) blijft ongewijzigd; claims van mij die door de nieuwe bronnen veranderen staan in `cowork-aanvulling-op-eigen-v1.md`.

## 0. Ontvangst en integriteit

Alle 19 bestanden in `codex-reviewpakket-v1/manifest.json` zijn aanwezig, leesbaar en hashgelijk (19/19, door mij herberekend). De vier bestanden van `nalevering2-manifest-v1.json` idem (4/4), commit `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb`.

`codex-eerste-bijdrage-manifest-v1.json` dateert de bevriezing van de vier hoofdstukken op 2026-09-18T13:43:32Z met `before_reading_new_cowork_conclusions: true`; `codex-astra-addendum-manifest-v1.json` op 14:39:00Z. Ik kan die bevriezingsmomenten niet zelfstandig verifiëren — ik zie alleen de bestanden zoals ze mij zijn aangeleverd. Ik neem de verklaring aan en noteer haar als verklaring, niet als door mij vastgesteld feit.

Eén relatieve verwijzing is vanuit de gedeelde kopie niet volgbaar: `bron-bewijsregister-v1.md` verwijst naar `codebasis-4cdb8ea43.tar` en de map `codebasis-4cdb8ea43/`, die niet in deze map staan. `verificatie-v1.json` meldt `archive_hash_ok: true`, maar dat is een controle in de Codex-omgeving. Conform `kruisreview-opdracht-v1.md` zijn de links bewust ongewijzigd gelaten; ik meld dit alleen als grens van mijn eigen verificatie (zie R-31).

**Leeswijzer bij de oordelen.** bevestigd · aangevuld · tegengesproken · onvoldoende bewezen · beleidskeuze. Versie van de beoordeelde claim is steeds `codex-onderzoek-v1.md` of de genoemde bijlage, versie v1 van 18 september 2026.

**Samenvattend oordeel.** Een sterk, methodisch zuiver onderzoek. Het bewijs is eerlijk begrensd, de scheiding bronfeit/besluit/waarneming/voorstel wordt consequent volgehouden, en de codeaanvulling bevat één bevinding die mijn eigen voorstel materieel corrigeert (R-27). Drie punten zijn materieel: de normzin N1 volgt na het eigen ASTRA-addendum nog steeds niet het criteriumgerichte onderwerp (R-02); het regelrecordvoorstel laat de indicatorpatronen ongemoeid terwijl die aantoonbaar defect zijn (R-16); en de poortaanbeveling laat een reeds vastgesteld DEF-630-criterium ongenoemd (R-25). Verder zijn er twee onjuiste of te sterke formuleringen (R-11, R-20) en één onverifieerbaar pad (R-30).

---

## 1. Q1 — norm, betekenis, toepasselijkheid

### R-01 — ASTRA-toegang: achterhaalde bronstatus is correct geactualiseerd
**Claim:** `codex-onderzoek-v1.md` Q1: "De actuele ASTRA-passage was niet toegankelijk (S05)"; `bron-bewijsregister-v1.md` S05: "Directe web-open en raw-poging niet toegankelijk. Actuele originele normpassage/revisie NIET bevestigd."
**Oordeel:** achterhaald in het hoofdstuk, correct hersteld in het addendum.
**Grond:** `codex-astra-addendum-v1.md` actualiseert S05 expliciet. Ik heb de pagina daarnaast zelf geopend (18 september, browser van deze sessie): toegankelijk, veld *Regel*: "Een criterium als onderdeel van een definitie moet toetsbaar zijn."; voetregel "laatst bewerkt op 11 feb 2025 om 09:46"; aangeboden permanente link `oldid=8558`. Mijn waarneming komt op alle velden overeen met `astra-bronobservatie-v2.md`.
**Gevolg:** in de synthese moet het hoofdstuk Q1 op dit punt worden gelezen mét het addendum, zoals het addendum zelf vraagt. Geen correctie nodig aan het addendum. Wel: S05 in het bronregister draagt nog de oude status en is de enige plek waar een lezer die niet doorklikt de verkeerde conclusie trekt — S05 bijwerken bij synthese.

### R-02 — N1 heeft het verkeerde onderwerp en is niet meegegroeid met het eigen addendum
**Claim:** N1 (`codex-onderzoek-v1.md` Q1, herhaald in `instructievoorstellen-v1.md`): "**De definitie** beschrijft kenmerken waarmee binnen de bedoelde betekenis en context navolgbaar kan worden beoordeeld of een geval onder het begrip valt."
**Oordeel:** deels tegengesproken — materieel.
**Grond:** ASTRA stelt het criterium als subject: "Een **criterium** als onderdeel van een definitie moet toetsbaar zijn." Het Codex-addendum erkent dat zelf woordelijk: "De norm is criteriumgericht." N1 is daarna niet aangepast en houdt de definitie als subject. Het verschil is niet redactioneel: met de definitie als subject volstaat het dat de definitie *als geheel* navolgbaar is, en dat is precies de lezing waaronder een zin met één bepaald en twee onbepaalde criteria passeert (`gevallen.json` `unfounded_number`; mijn C04). Met het criterium als subject valt die zin.
**Correctie:** onderwerp verplaatsen naar het criterium en de tweede eis (volledigheid van de beslissing) expliciet maken. Bijvoorbeeld: "Ieder criterium in de definitie is binnen de bedoelde betekenis en context zo bepaald dat navolgbaar kan worden beoordeeld of een geval eraan voldoet, en de criteria samen beslissen of het geval onder het begrip valt." Dit is dicht bij N1 en bij mijn eigen §6.1; de twee voorstellen verschillen daarna nog in woordkeuze, niet in strekking.

### R-03 — De vier afzonderlijke vragen zijn een sterke bijdrage
**Claim:** Q1: toetsbaarheid / numerieke meetbaarheid / juistheid-bronsteun / essentieel onderscheid zijn vier vragen die apart beantwoord moeten worden.
**Oordeel:** bevestigd en overgenomen.
**Grond:** dit valt samen met mijn §3.4 en §4.2 ("een reproduceerbaar gemeten eigenschap hoeft niet begripsbepalend te zijn"), maar de Codex-formulering is scherper doordat zij juistheid/bronsteun als eigen derde as benoemt en aan CON-02 koppelt (N07). Casus N14 (lengte als proxy voor vakbekwaamheid) is het beste losse tegenvoorbeeld tegen getal=kwaliteit dat in beide pakketten voorkomt.
**Gevolg:** overnemen in de synthese, met mijn vier voorwaarden (aanwijsbaarheid, bepaaldheid, volledigheid, verankering) als operationalisering van de eerste vraag. De twee lijsten zijn complementair, geen dubbeling: die van Codex scheidt normdoelen, die van mij ontleedt er één.

### R-04 — VIM3-duiding
**Claim:** Q1 punt 2, met S07: VIM3 §1.30/§2.1 ondersteunen dat "toetsbaar" ruimer is dan "numeriek meetbaar".
**Oordeel:** bevestigd; aangevuld.
**Grond:** zelf gelezen (18 september). §2.1 measurement: "process of experimentally obtaining one or more quantity values that can reasonably be attributed to a quantity". §1.30 NOTE 1: "A nominal property has a value, which can be expressed in words, by alphanumerical codes, or by other means"; annotatie 3 december 2013: nominale eigenschappen zijn onderscheiden van grootheden, "that is, they can be compared in terms of greater or lesser".
**Aanvulling:** één argument ontbreekt bij Codex en is beslissend: ASTRA zet **'meten' zelf tussen aanhalingstekens** in de toelichting. De bron markeert het woord dus als oneigenlijk gebruikt. Samen met "Geldig voor: alle" maakt dat de metrologische lezing intern tegenstrijdig, want die zou nominale kenmerken buiten een regel plaatsen die voor alle definities geldt. Toevoegen aan de synthese als zelfstandige grond naast VIM3.

### R-05 — "Geen universele gegarandeerde beslisbaarheid"
**Claim:** Q1: het ontbreken van bewijs voor een concreet geval maakt een goede definitie niet ontoetsbaar (N17).
**Oordeel:** bevestigd; belangrijke toevoeging ten opzichte van mijn v1.
**Grond:** dit onderscheid — kwaliteit van de begripsbeschrijving tegenover beschikbaarheid van gevalsbewijs — heb ik in §3.3 en §6.3 impliciet gebruikt maar nergens als zelfstandige regel benoemd. Het is precies de as waarop keuze C uit mijn §7.4 ("voldoet niet" of "nog te beoordelen" bij een ontbrekend gegeven) beslist moet worden, en het pleit voor "nog te beoordelen" op het *geval* en "voldoet" op de *definitie*.
**Gevolg:** overnemen; mijn keuze C wordt hierdoor scherper geformuleerd — zie R-26.

### R-06 — Open normen
**Claim:** Q1: "een bedoelde open norm mag niet tot een verzonnen drie dagen worden vernauwd"; eerst vaststellen welke betekenis de bron geeft.
**Oordeel:** bevestigd, en dit is een echte aanvulling op mijn v1.
**Grond:** mijn §2.5 behandelt "definities die een onbepaald begrip definiëren" als open beleidsvraag maar geeft geen richting. Codex geeft die wel, en het sluit aan bij het bestaande ESS-01-beleid ("een definitie van het begrip 'doel' wordt niet op de term afgekeurd").
**Gevolg:** overnemen. Let op de grens die Codex zelf trekt en die ik onderschrijf: dit is geen algemene juridische vrijstelling. `bad_fragment` blijft onvoldoende zodra de bron een harde termijnklasse bedoelt.

### R-07 — Leegte
**Claim:** Q1: "VAL-EMP kan leegte afkeuren; ESS-04 heeft dan geen inhoud om te beoordelen. De historische lege-text review_required is uitvoeringsgedrag, geen bewijs dat een lege definitie inhoudelijk beoordeelbaar is."
**Oordeel:** bevestigd; onafhankelijk herhaald.
**Grond:** mijn casus C07 geeft dezelfde uitkomst met dezelfde duiding (`review_required` met exact dezelfde kale toetsvraag als bij een volle definitie: formeel juist, voor de gebruiker misleidend).
**Gevolg:** beide pakketten stellen een aparte melding voor. Codex' `instructievoorstellen-v1.md` doet dat niet expliciet voor leegte; mijn §6.4 wel ("ESS-04 — Niet beoordeelbaar: er is geen definitietekst om criteria in te beoordelen"). Samenvoegen in de synthese.

---

## 2. Q2 — informatie, bewijs, veldrollen

### R-08 — Drie informatielagen
**Claim:** Q2: betekenisgrond / toepassingsgrond / beoordelingsregistratie, waarbij geen laag stil een andere vervangt.
**Oordeel:** bevestigd; sterker dan mijn eigen indeling.
**Grond:** mijn §3.1 onderscheidt toetsobject, noodzakelijk bewijs, ondersteunende informatie en presentatie. Dat is een indeling naar *rol in de toets*; de Codex-indeling is er een naar *waar het gegeven vandaan komt* en vangt daarmee de vervangingsfout die ik alleen per veld benoem. Ze conflicteren niet.
**Gevolg:** in de synthese beide behouden, met de Codex-lagen als bovenbouw en mijn rollen als invulling per veld.

### R-09 — Veldrolmatrix
**Claim:** `codex-onderzoek-v1.md` Q2, dertien rijen met TO/B/G/P.
**Oordeel:** bevestigd op alle punten waar onze matrices elkaar raken; twee verschillen.
**Grond en verschillen:**
- *Toelichting.* Codex: "essentiale beperking niet uitsluitend hier verstoppen. Niet samengevoegd met kern toetsen." Ik: identiek, met primaire bronsteun die Codex niet gebruikt — NL-SBB §2.4.1.2 zegt bij `definitie` "De definitie moet precies kloppen" en bij `toelichting` dat die "de grenzen van een begrip [verduidelijkt]" en "geen volledige definitie [hoeft] te zijn". Dat is de normatieve grond onder wat beiden stellen. Toevoegen.
- *Meetmetadata.* Codex: "Alleen waar onderscheidend. Geen algemene verplichte checklist." Ik: identiek, met een expliciet criterium ("nodig wanneer twee redelijke beoordelaars zonder dat element tot een ander oordeel over hetzelfde geval zouden kunnen komen") en een tabel per element. De Codex-formulering is juist maar niet operationeel; de mijne is toetsbaar. Samenvoegen.
- *Ontologierelaties.* Codex voegt toe: "Geen verplicht compleet UFO-model voor eenvoudige definitie." Dat staat niet in mijn matrix en is een nuttige begrenzing. Overnemen.
**Gevolg:** één samengevoegde matrix in de synthese, niet twee achter elkaar.

### R-10 — Voorwaardelijke bewijsvereisten: percentage, grenzen, termijnen, versies
**Claim:** Q2, vier blokken met onder meer "'8/10 ontvangen' mag niet stil '8/8 geïnspecteerd' worden", "Lege populatie … 0/0 vraagt een expliciete conventie", "minimaal (≥), meer dan (>), maximaal (≤), minder dan (<)", "Bronrecency is niet vanzelf voorrang".
**Oordeel:** bevestigd; het scherpste deel van het Codex-onderzoek.
**Grond:** dit is materieel rijker dan mijn §3.3-tabel. De noemerverwisseling (N08), de lege populatie (N09) en het gelijktijdige bronconflict zonder voorrangsregel (N13) zijn drie onderscheidende gevallen die ik niet heb. Ik heb ze narekend: 8/10 = 80% (voldoet aan ≥80), 8/8 = 100% (fout); 85/100 = 85% voldoet aan v1 ≥80 en niet aan v2 ≥90; vrijdag 17:00 + 48 uur = zondag 17:00, dus exact op de grens bij gelijke UTC-offset. Alle rekenkundige onderbouwingen kloppen.
**Gevolg:** integraal overnemen. Mijn tabel voegt alleen "werk- of kalenderdagen — altijd bij een dagtermijn" als harde regel toe; Codex houdt dat voorwaardelijk ("uitsluitend waar die de uitkomst veranderen"). Dat verschil is klein en in het voordeel van Codex: bij een termijn van tien werkdagen tegenover veertien kalenderdagen verandert het de uitkomst wél, bij "binnen 3 jaar" niet. Ik trek mijn hardere formulering in — zie `cowork-aanvulling-op-eigen-v1.md` A-06.

### R-11 — "geen productiegegevens hier" bij praktijkvoorbeelden is juist; "gebruik bron/toegang passend" is te vaag
**Claim:** Q2 veldmatrix, rij Praktijkvoorbeelden: "Nodig bij praktijkclaim; gebruik bron/toegang passend, geen productiegegevens hier."
**Oordeel:** onvoldoende bepaald.
**Grond:** de rij vermengt een onderzoeksrandvoorwaarde (in dit onderzoek geen productiegegevens) met een productnorm (wanneer een praktijkvoorbeeld bewijs levert). Voor een instructie die later in een skill belandt, is "gebruik bron/toegang passend" geen uitvoerbaar criterium.
**Correctie:** splitsen in (a) productnorm: een praktijkvoorbeeld telt als bewijs wanneer het geval identificeerbaar is en de gegevens die het criterium beslissen controleerbaar zijn; en (b) onderzoeksrandvoorwaarde: in dit dossier uitsluitend synthetisch. Mijn §3.2 formuleert (a) als "leveren waarneembaar bewijs dat het criterium in het veld vast te stellen is"; dat is ook niet af, dus dit is een punt voor beiden.

---

## 3. Q3 — relaties

### R-12 — ESS-03-relatie krijgt terecht primaire bronsteun
**Claim:** `codex-astra-addendum-v1.md`: "ESS-03 is een expliciet door ASTRA verbonden regel … Deze relatie stond al in Q3, maar krijgt nu directe primaire bronsteun."
**Oordeel:** bevestigd; aangevuld met twee feiten.
**Grond:** ik heb de ESS-03-pagina zelf gelezen. Twee dingen die in het addendum ontbreken en er materieel toe doen:
1. ASTRA geeft ESS-03 "Geldig voor: **telbare zelfstandige naamwoorden**", tegenover "alle" bij ESS-04. De arbeidsdeling is dus ook in bereik vastgelegd: een substantiebegrip ("zand", "recidive" — ASTRA noemt ze zelf) valt buiten ESS-03 en binnen ESS-04.
2. De ESS-03-toelichting bevat letterlijk de tweebeoordelaarsformulering: de definitie "moet eenduidig tellen mogelijk maken" door "verschillende onafhankelijke materiedeskundigen", en divergentie wijst op aanscherping, homoniem of polyseem.
**Gevolg:** feit 2 raakt R-24 rechtstreeks: de tweebeoordelaarsproef is normatief verankerd bij ESS-03, niet bij ESS-04. Beide pakketten bevelen kalibratie aan zonder dit te vermelden; de synthese moet het vermelden, anders wordt een ESS-03-bronnorm stilzwijgend ESS-04-beleid.

### R-13 — Het record mist de enige ASTRA-relatie; niet opgemerkt
**Claim:** `instructievoorstellen-v1.md` N1 geeft nieuwe waarden voor naam, uitleg, toelichting, toetsvraag en voorbeelden.
**Oordeel:** aangevuld — ontbrekend punt.
**Grond:** `src/toetsregels/regels/ESS-04.json` heeft `"relatie": [{"fulltext": "Toetsbaarheid", "fullurl": ".../Toetsbaarheid"}]`, dus een verwijzing naar de eigen pagina. De enige door ASTRA gelegde regelrelatie (ESS-03) staat niet in het record. Ook `"thema": "toepasbaarheid"` wijkt af van ASTRA's "essentie van het begrip". Het Codex-recordvoorstel raakt beide velden niet.
**Correctie:** `relatie` uitbreiden met `Instanties_uniek_onderscheidbaar` en `thema` gelijktrekken met de bron (mijn §6.1). Klein, maar het herstelt de enige bronrelatie die er is en die het addendum zelf belangrijk noemt.

### R-14 — INT-02/06-relatie
**Claim:** Q3: "Methode of procedure niet als uitvoeringsinstructie in kern plakken … Geen woordverbod op 'als' invoeren."
**Oordeel:** bevestigd; niet in mijn v1.
**Grond:** ik behandel INT-02/INT-06 niet. De relatie is reëel: een criterium met een voorwaarde ("indien de aanvraag volledig is") raakt INT-02, en de verleiding om de meetmethode in de kern te zetten raakt INT-06. De begrenzing "geen woordverbod" is juist en past bij het verbod op een stijl-afkeurgrond.
**Gevolg:** overnemen in de relatietabel van de synthese.

### R-15 — Buurregelstatus: de zelfcorrectie is terecht
**Claim:** Q3: "Eerdere globale uitspraak dat 'alle gedeelde voorzieningen ontbreken' zou te breed zijn: CON-01/CON-02 hebben concrete routes en recente resultaatnormalisatie is geleverd."
**Oordeel:** bevestigd; ik kom onafhankelijk tot hetzelfde.
**Grond:** `definition_repository.set_context_review(..., expected_version=...)` (regel 1426) en `set_source_review(...)` (regel 1215), plus `_con01_blokkades`/`_con02_blokkades` in `definition_workflow_service.py`, zijn werkende, versiegebonden routes. Mijn §5.7 gebruikt ze uitdrukkelijk als bestaand, werkend model waar ESS-04 op kan aansluiten, niet als ontbrekende voorziening.
**Gevolg:** geen. Dit is een voorbeeld van een correct begrensde conclusie.

---

## 4. Q4 — appgedrag, en de proefclaims

### R-16 — Het recordvoorstel laat de indicatorpatronen ongemoeid, en die zijn aantoonbaar defect
**Claim:** `instructievoorstellen-v1.md` N1 vervangt naam, uitleg, toelichting, toetsvraag en beide voorbeeldlijsten, en zegt over de rest: "Behouden totdat afzonderlijk besloten: judgment_review, excluded_from_score en huidige ernst." `herkenbaar_patronen` wordt nergens genoemd.
**Oordeel:** materieel onvolledig — het zwaarste punt van deze review.
**Tegenbewijs (eigen proef, `cowork-bewijs-v1/`, offline, commit 4cdb8ea43, exit 0):** van de vijftien patronen in het record zijn er vijf defect.
- Alle vier percentagepatronen (`\btenminste\s+\d+%\b`, `\bminimaal\s+\d+%\b`, `\bmaximaal\s+\d+%\b`, `\b\d+\s+%\b`) eindigen op `\b` direct na `%`. Een woordgrens vereist aan één zijde een woordteken; na `%` volgt in normale tekst een spatie of punt. Ze vuren dus **nooit**. Controlegeval: "Kandidaat die minimaal 80%voldoet." vuurt wél (C14), "Object dat minimaal 80% voldoet." niet (C05).
- `\buiterlijk\s+na\s+\d+\s+(dagen?|weken?)\b` mist "1 week" (`weken?` = "weke" + optionele "n"). `\bbinnen\s+\d+\s+dagen?\b` mist "1 dag".
Twee van ASTRA's drie GOED-voorbeelden — 'tenminste 80% van de …' en 'uiterlijk na 1 week' — worden dus niet herkend door de patronen die ervoor geschreven zijn.
**Bijkomend en direct relevant voor N1:** ik heb de door Codex voorgestelde voorbeelden door de huidige patronen gehaald. **Geen van de vier levert enig signaal**: "Speelkaart waarvan de achterzijde blauw is." (geen), "Partij waarvan minimaal 80% van alle op 18 september 2026 ontvangen exemplaren onbeschadigd is." (geen — de `%`-fout), "Object dat minimaal 80% voldoet." (geen), "Aanvraag die zo snel mogelijk relevant wordt." (geen). Ook het grensvoorbeeld en de casusteksten N06, N10 en N14 leveren niets op.
**Gevolg/correctie:** N1 kan niet worden vastgesteld zonder tegelijk `herkenbaar_patronen` te behandelen. Anders wordt een defect voorbeeldpaar vervangen door een paar dat voor de signaallaag volledig onzichtbaar is, en verliest `example_pair_policy: review_policy` zijn feitelijke grond — het huidige `example_pair_reason` ("de indicatorpatronen vuren op elk getal of elke tijdsaanduiding en missen het eigen foute voorbeeld") beschrijft de situatie bovendien onjuist: de patronen missen vooral hun eigen *goede* voorbeelden. Concreet patroonvoorstel en de correctie van `example_pair_reason` staan in mijn §6.1.

### R-17 — De ene geteste tekst is de smalste plek in de Codex-bewijsbasis
**Claim:** P01 op "Document dat objectief toetsbaar is." levert in beide metadata-varianten `review_required`, score null, signaal `\btoetsbaar\b` (`proef-actueel-uitvoer-v1.log`, exit 0).
**Oordeel:** bevestigd voor wat het aantoont; onvoldoende als basis voor de patroonuitspraken elders.
**Grond:** ik reproduceer de signaaluitkomst voor deze tekst exact. Maar het is de enige tekst die Codex door de evaluator heeft gehaald, en het is toevallig een van de weinige waarop een patroon vuurt. `bron-bewijsregister-v1.md` C01 stelt op basis hiervan dat het record "cijfergerichte uitleg" bevat — dat klopt — maar er is geen enkele meting die de patronen zelf toetst.
**Gevolg:** de metadata-grens die P01 aantoont (een aangeleverd `rule_statuses: {ESS-04: pass}` plus `reviewer` verandert de uitkomst niet) is een waardevolle en door mij bevestigde bevinding die ik zelf níet heb gedaan — ik neem hem over. In ruil levert mijn casusregister de patroonmeting die bij Codex ontbreekt. De registers vullen elkaar hier precies aan.

### R-18 — P02: de transportbevinding en haar eigen correctie zijn juist; er zit een onopgemerkt restdefect in de uitvoer
**Claim:** C03: "Oude legacy-normalisatie verliest reviews; huidige normalisatie bewaart ze en markeert ontbrekende runstatus unknown." Q4: "Oude P02-transportfout is in actuele tegenproef niet aanwezig."
**Oordeel:** bevestigd, met zelfstandige verificatie; **aangevuld met een defect dat in de eigen uitvoer zichtbaar is maar niet is opgemerkt**.
**Grond:** ik heb beide kanten zelf nagegaan. Oud (`werkboom/`, 50d0770): `types.py:601` en `:716` zetten `passed_rules = ["BASIC-001","BASIC-002","BASIC-003"]`, `mappers.py:29` draagt `DEFAULT_PASSED_RULES`, en `neem_contractvelden_over` bestaat er niet — dus de drie contractvelden gingen verloren en er werden geslaagde regels verzonnen. Nieuw (nalevering 1, `result_contract.py:56-66`): `CONTRACTVELDEN` bevat `rule_statuses`, `rule_results`, `review_required` en `evaluation_coverage`; `neem_contractvelden_over` kopieert wat de bron draagt. De correctie is echt en Codex meldt terecht dat de oude bevinding niet als actuele appfout mag worden opgevoerd.
**Aanvulling (nieuw, uit de Codex-uitvoer zelf):** in `proef-actueel-uitvoer-v1.log` draagt `legacy_output` tegelijk `"overall_score": 0.0`, `"is_acceptable": false`, `"validation_status": "validation_unknown"` **en** `"detailed_scores": {"taal": 0.9, "juridisch": 0.9, "structuur": 0.9, "samenhang": 0.9}`. Oorzaak in code: `_convert_legacy_dict_to_unified` vult `detailed_scores` via `_scores_per_categorie(overall_score)` met de invoerscore 0.9, waarna `met_expliciete_runstatus` alleen `overall_score` en `is_acceptable` fail-closed maakt en `detailed_scores` ongemoeid laat. Een resultaat dat expliciet geen uitgevoerde run is, draagt dus vier categoriecijfers van 0,9. Dat is precies het risico dat Codex zelf in Q6 als laatste noemt: "cijfers uit technische contractvelden als kwaliteit tonen".
**Gevolg:** opnemen als nieuwe gezamenlijke bevinding met eigenaar buiten ESS-04 (DEF-624/622-contract). Het is geen ESS-04-defect, maar het raakt de weergave van elke ESS-04-uitkomst in een unknown-resultaat.

### R-19 — P03 en P04
**Claim:** P03: de ESS-04-generatiemapping geeft nog "deadlines/aantallen/percentages". P04: de partijzin behoudt na extractie en cleaning 80%, minimaal, noemer en peildatum; "Geen schadelijke nabewerking aangetoond in dit geval."
**Oordeel:** beide bevestigd; de begrenzingen zijn correct gesteld.
**Grond:** P03 reproduceer ik statisch — `json_based_rules_module.py:331` bevat exact die string, en `feitenbasis/actieve-skills/definitie-toetsregels/reference.md:47` bevat dezelfde tekst in de regeltabel. Die tweede vindplaats noemt Codex in `instructievoorstellen-v1.md` wel; goed. Voor P04 heb ik de cleaningroute statisch gelezen: `opschoning.py` verwijdert uitsluitend vormconstructies aan het *begin* van de zin en dwingt hoofdletter en punt af, en laat sinds DEF-622 betekenisdragende frasen staan. Dat verklaart waarom de partijzin ongeschonden blijft en ondersteunt de uitkomst; het maakt de uitkomst niet algemener dan één geval, zoals Codex zelf aangeeft.
**Aanvulling:** één cleaningverschil dat in geen van beide pakketten staat — opschoning draait bij generatie en **niet** bij import (`definition_import_service.py` roept geen cleaning aan). Dezelfde tekst kan langs twee ingangen dus als twee verschillende strings worden getoetst. Voor ESS-04 is het effect klein (het raakt het zinsbegin) maar het raakt wel de eis "dezelfde norm voor gegenereerde en aangeleverde inhoud".

### R-20 — "Geen aangesloten ESS-04-beoordelingsschrijfroute" is juist, maar de formulering is zwakker dan het bewijs toelaat
**Claim:** C06 (F/I): "In gelezen actuele evaluator/UI is geen aangesloten ESS-04-beoordelingsschrijfroute aangetoond … Afwezigheid van volledige keten blijft begrensde conclusie."
**Oordeel:** bevestigd in uitkomst; de voorzichtigheid is hier onnodig en verzwakt een hard feit.
**Grond:** dit is niet alleen "niet aangetoond in de gelezen bestanden". Het is vast te stellen uit het schema: `src/database/schema.sql`, tabel `definities`, heeft voor validatie uitsluitend `validation_score`, `validation_date` en `validation_issues`. Er is geen kolom en geen JSON-veld waarin een menselijk oordeel per reviewplichtige regel kan worden bewaard — terwijl CON-01 en CON-02 daar wél eigen, versiegebonden opslag voor hebben (`set_context_review`, `set_source_review`, beide met `expected_version`). Een schrijfroute kan dus niet bestaan, niet alleen: is niet gevonden.
**Correctie:** C06 opwaarderen van "niet aangetoond" naar "uitgesloten door het opslagcontract", met het schema als grond. Dat verandert de gevolgtrekking in Q4 en Q5: het is geen bewijsgat dat met meer lezen gedicht kan worden, maar een ontbrekende voorziening.

### R-21 — De routetabel is eerlijk; twee rijen kunnen concreter
**Claim:** Q4-routetabel, acht ingangen met "aangetoond" en "nog open".
**Oordeel:** bevestigd; twee aanvullingen uit de nalevering.
**Grond:**
- *Import.* Codex: "ESS-04-invoer/status/opslag/readback/import-UI niet proefondervindelijk gevolgd", en in `codex-codeaanvulling-v1.md`: "De gelezen opslagroute gebruikt preview.ok niet als aparte ESS-04-poort. Dit bewijst geen fout: conceptimport en formele vaststelling zijn verschillende handelingen." Dat laatste onderschrijf ik. Wat eraan ontbreekt: `import_single` bewaart de validatie-uitkomst in het geheel niet bij het record — geen `validation_score`, geen `validation_issues`, geen reviewregister. Het gevolg is dat het fail-closed-gedrag hier volledig aan de scoregate hangt ("Geen validatieresultaat beschikbaar (eerst (her)valideren)", `definition_workflow_service.py:753`), en dat die bescherming vervalt zodra iemand één keer hervalideert. Dat is een concreter gevolg dan "niet gevolgd".
- *Vaststellen.* Zie R-25.

### R-22 — De eis aan een bruikbaar menselijk oordeel is goed en valt samen met mijn voorstel
**Claim:** Q4: benoem criterium/passage, bedoelde betekenis, context/bronversie, gevalsgegevens/methode, oordeel en motivering, onzekerheid, strijdigheid; bind aan tekst- en normversie plus werkelijke beoordelaar/rol en tijd; invalideer gericht na materiële wijziging. "Caller-strings of model-generated reviewvelden zijn geen vertrouwde actor."
**Oordeel:** bevestigd; onafhankelijk hetzelfde.
**Grond:** mijn §6.7 punt 1 en 2 formuleren dezelfde eisen, met het bestaande CON-01-mechanisme als model (vingerafdruk over tekst + term + context + normversie; herberekening op het record in plaats van hergebruik van een oude runuitkomst). De P01-metadatagrens (R-17) is het empirische bewijs onder de laatste zin.
**Gevolg:** deze twee beschrijvingen samenvoegen; ze verschillen alleen in dat Codex de inhoud van het oordeel specificeert en ik het opslagmechanisme. Codex' terechte waarschuwing "Geen ESS-04-eigen database of CON-02-veld als verborgen ESS-container" blijft daarbij staan.

---

## 5. Q5 — G/T/H en de instructievoorstellen

### R-23 — G1, T1 en H1 zijn bruikbaar; drie inhoudelijke aanvullingen
**Claim:** `instructievoorstellen-v1.md` G1, T1, H1.
**Oordeel:** bevestigd in strekking; aangevuld.
**Grond en aanvullingen:**
1. **G1 mist de dagconventie in de instructie zelf.** G1 zegt "behoud relevante noemer, populatie, inclusie en tijdsbasis". "Tijdsbasis" dekt werk- tegenover kalenderdagen niet herkenbaar, terwijl Codex' eigen casussen N10 en N11 precies daarop draaien. Mijn §6.2 maakt het expliciet ("noem bij een termijn in dagen of het werkdagen of kalenderdagen zijn en vanaf welk moment wordt geteld"). Overnemen.
2. **G1's verduidelijkingsroute is een appvoorwaarde die niet bestaat.** G1 draagt het model op "via de beschikbare verduidelijkingsroute om die grond [te] vragen", en de appvoorwaarde eronder erkent: "als de eindprompt alleen een definitiezin toelaat, moet verduidelijking buiten dat uitvoerveld een ondersteunde route hebben." Dat is juist gezien, maar het betekent dat G1 zoals geformuleerd een niet-aangetoonde voorziening veronderstelt. In de gelezen code is het uitvoerformaat één definitiekandidaat. **Correctie:** G1 formuleren zodat hij ook werkt zonder die route — "lever geen verzonnen afbakening; benoem het ontbrekende gegeven apart bij de kandidaat" (mijn §6.2) — en de verduidelijkingsroute apart als appvoorstel opvoeren, niet als instructievoorwaarde.
3. **H1 mist de scherpste ESS-04-specifieke bescherming.** H1 zegt "Verzin geen drempel, bron, context, actor of goedkeuring." Dat is juist, maar bij deze regel is er één beschermde handeling die alle andere overheerst en die als zodanig benoemd moet worden: er wordt nooit een getal, termijn, percentage, noemer, peildatum of grenswaarde toegevoegd die niet in de aangeleverde bron of bevestigde context staat. Bij ESS-04 is het verschil tussen herstel en verzinnen precies één cijfer. Mijn §6.6 formuleert dat zo; overnemen als eigen zin in H1.
**Verder:** H1's zeven diagnoses en mijn zeven komen inhoudelijk overeen; Codex splitst "betekenisverlies door nabewerking" en ik "schadelijke nabewerking" — zelfde categorie. Eén formulering volstaat in de synthese. Codex' diagnosetabel in Q5 met de kolom "Benodigd onderscheidend bewijs" is beter dan mijn opsomming, omdat zij per diagnose zegt wat je moet zien om haar te mogen stellen. Die kolom overnemen.

### R-24 — Twee beoordelaars: eens, met één ontbrekend bronfeit
**Claim:** Q4: "aanbevolen voor kalibratie van risicovolle/grenscases, niet als universele extra productpoort"; "Een consensuspercentage toont hoogstens overeenstemming, geen juistheid of ESS-04-score."
**Oordeel:** bevestigd; aangevuld met de bronverankering.
**Grond:** ik kom onafhankelijk tot dezelfde aanbeveling en tot dezelfde afwijzing van een universele tweepersoonspoort, met dezelfde grond in `cowork-opdracht-v1.md` (algemene expertbeoordeling en handmatige vaststelling blijven; een verplichte tweede persoon is niet besloten). Wat ontbreekt is R-12 feit 2: de formulering "verschillende onafhankelijke materiedeskundigen" staat letterlijk in ASTRA, maar bij **ESS-03**. Codex' vierdeling van divergentie (betekenis/bron, gevalsbewijs, lees- of toepassingsfout, resterende beoordelingsruimte) is fijner dan mijn tweedeling en beter; ik neem haar over.
**Gevolg:** in de synthese expliciet vermelden dat de tweebeoordelaarsgedachte uit ESS-03 komt, zodat zij niet stilzwijgend ESS-04-norm wordt. Codex' casussen N15 (≥ tegenover >: toepassingsfout) en N16 ("substantieel": betekenisverschil) zijn precies de twee gevallen die dat onderscheid aantoonbaar maken; overnemen.

### R-25 — Poortaanbeveling: verdedigbaar als regellokale keuze, maar een vastgesteld appbreed criterium blijft ongenoemd
**Claim:** Q5, poortkeuze: "aanbeveling is geen nieuwe zelfstandige ESS-04-blokkade of aparte akkoordknop nu afleiden. Houd open/negatief zichtbaar binnen bestaande expertbeoordeling." Q4-routetabel, rij Vaststellen: "Geen ESS-04-poortbesluit afleiden uit excluded_from_score of severity; algemene DEF-630 niet opnieuw opgelost/gebouwd." `bron-bewijsregister-v1.md` B07 noemt DEF-630 als "gedeeld resultaat, gate en herstel".
**Oordeel:** deels tegengesproken — materieel.
**Tegenbewijs:** DEF-630 (`bronnen/linear-DEF-630-20260918.json`), onder "Verplicht regressiegedrag", in een blok dat is ingeleid met "Roadmapcorrectie vastgesteld door Chris op 4 september 2026", bevat letterlijk:
> "Verplichte `review_required`-uitkomsten hebben een versioned menselijke beoordeling; een numerieke score vervangt die niet."
en
> "Ontbrekende context, verplicht bewijs, actor of vereiste review kan niet met alleen een notitie worden opgeheven."
Dat is geen voorstel en geen ESS-04-lokale vraag: het is een vastgesteld, appbreed criterium dat ESS-04 als verplichte `review_required`-regel rechtstreeks raakt. Het is niet uitgevoerd: `_evaluate_gate` in `definition_workflow_service.py` (regels 715-840) kijkt uitsluitend naar context, `validation_score`, issue-severities, `_con01_blokkades` en `_con02_blokkades`; er staat geen verwijzing naar `review_required`, `rule_statuses` of `evaluation_coverage` in. De nu nagekomen `approval_gate_policy.py` bevestigt dat: `DEFAULT_POLICY` kent `min_one_context_required`, `forbid_critical_issues`, `hard_min_score` 0.75, `soft_min_score` 0.65, `allow_hard_override` False — en het woord "review" komt in het hele bestand niet voor. De DEF-630-audit van 15 september noteert bovendien zelf: "twee verse proeven zonder opgeslagen validatiebewijs slagen nog bij handmatige approve … score 0.95 geeft gate pass."
**Wat hiermee wél en niet is weerlegd:** Codex' *aanbeveling* — geen nieuwe ESS-04-eigen blokkade, geen aparte akkoordknop, geen regellokaal besluit nu — blijft verdedigbaar en ik deel haar deels (mijn voorkeur B3 is geen ESS-04-eigen poort maar een generieke poort over de verplichte reviewplichtige regels). Wat niet houdbaar is, is de stelling dat er over vaststelling niets is vastgesteld. Er ligt een eis; zij is open; dat hoort in de besluitnotitie te staan, anders leest Chris "geen poort nodig" waar "bestaand criterium nog niet uitgevoerd" het feit is.
**Correctie:** de poortparagraaf herformuleren in twee delen: (a) uitvoering van het bestaande DEF-630-criterium voor verplichte `review_required`-uitkomsten is achterstallig en vraagt alleen een reikwijdtekeuze; (b) een ESS-04-*eigen* aanvullende blokkade of akkoordknop is een nieuw regellokaal besluit en wordt nu niet aanbevolen. Ik onderschrijf (b).

### R-26 — De vijf keuzes voor Chris zijn goed; twee ontbreken
**Claim:** Q6, vijf keuzepunten.
**Oordeel:** bevestigd; aangevuld.
**Grond:** de vijf overlappen grotendeels met mijn §7.4. Twee keuzes die bij Codex ontbreken en die ik als echte beslispunten zie:
- **De indicatorpatronen** (mijn keuze A): omdraaien naar onbepaaldheidssignalen, of de huidige richting behouden en alleen de defecten repareren. Gezien R-16 kan dit niet onbesproken blijven.
- **Wat "voldoet" betekent bij een ontbrekend gegeven** (mijn keuze C). Codex' N17 en de "geen universele gegarandeerde beslisbaarheid" uit Q1 (R-05) geven hier de sleutel die mijn eigen formulering miste: het onderscheid loopt niet tussen "voldoet niet" en "nog te beoordelen", maar tussen het *definitieoordeel* (kan voldoen) en het *gevalsoordeel* (blijft onbekend). Ik herformuleer keuze C daarop in mijn aanvulling.
Omgekeerd voegt Codex' keuze 5 (uitvoering onder bestaande owners, daarna afzonderlijke opdracht) iets toe dat ik niet expliciet maak.
**Gevolg:** één gezamenlijke keuzelijst van zes tot zeven punten in de besluitnotitie, elk met de onderscheidende casus erbij.

### R-27 — `excluded_from_score` tegenover `no_score`: correct, materieel, en het corrigeert mijn eigen voorstel
**Claim:** `codex-codeaanvulling-v1.md`: gewicht wordt voor beide policies op nul gezet (`:977-994`), maar `geen_cijfer` alleen bij `NO_SCORE` (`:1019`); `_verwerk_uitkomst` (`:1568-1630`) boekt bij PASS/FAIL alsnog een individueel cijfer als `geen_cijfer` false is; `_calculate_category_scores` (`:2034-2071`) middelt ongewogen; `:1168` maakt categorieën met `NO_SCORE` leeg.
**Oordeel:** bevestigd op elk onderdeel, zelfstandig geverifieerd. Dit is de sterkste bijdrage van het Codex-pakket.
**Grond:** ik heb alle vier plaatsen gelezen. `for code, record in state.rule_records.items(): if record.score_policy is not ScorePolicy.SCORED: weights[code] = 0.0` — beide policies, gewicht nul. `zonder_cijfer` filtert op `ScorePolicy.NO_SCORE`. `_verwerk_uitkomst` bij PASS: `if not geen_cijfer: rule_scores[code] = 1.0 if outcome.score is None else outcome.score`. `_calculate_category_scores` bucketeert `rule_scores` op prefix (ESS → juridisch) en middelt ongewogen; de blanking-lus `for code in zonder_cijfer: detailed[category_for_rule(code)] = None` raakt alleen NO_SCORE-regels.
**Gevolg:** zolang ESS-04 `review_required` levert is er geen lek — dat stelt Codex terecht. Maar het raakt mijn eigen §6.7 rechtstreeks: ik stel daar een menselijk oordeel voor met de uitkomsten voldoet / voldoet niet / nog te beoordelen / niet beoordeelbaar. Zou zo'n oordeel in de bestaande PASS/FAIL-vorm worden teruggevoerd terwijl de policy `excluded_from_score` blijft, dan landt er per definitie een 1,0 of 0,0 in `rule_scores`, telt die mee in het ongewogen gemiddelde van de categorie "juridisch", en wordt die categorie niet geblankt. Dat is precies het cijfer dat het besluit van 15 september uitsluit. **Ik neem dit over**: het reviewcontract voor ESS-04 moet expliciet scoreloos worden ontworpen, en `no_score` is daarvoor de te beoordelen kandidaat — met de waarschuwing die Codex er zelf bij zet, dat alleen het policywoord wijzigen de aansluiting (rule_result-structuur, transport, consumers) niet bewijst. Verwerkt in `cowork-aanvulling-op-eigen-v1.md` A-05.

### R-28 — De besluitcorrectie "tijdelijk/voorlopig" is terecht en valt buiten ESS-04
**Claim:** `instructievoorstellen-v1.md`, slot: vervang in de toetsregels-skill de formuleringen over "tijdelijk/voorlopig geen totaalcijfer" door de vastgestelde formulering; "Algemene migratie onder DEF-624/630; geen andere regelrecords stil herschrijven."
**Oordeel:** bevestigd.
**Grond:** `definitie-toetsregels/SKILL.md` draagt inderdaad nog "voorlopig geen totaalcijfer" en "Zolang DEF-624 open is, is de appbrede totaalscore tijdelijk niet beschikbaar", terwijl het besluit van 15 september de totaalscore als kwaliteitscijfer, acceptatiegrond en hersteldriver laat vervallen. De juiste afbakening (appbreed, niet ESS-04) wordt er correct bij gezet.
**Gevolg:** overnemen, met de kanttekening dat het geen ESS-04-voorstel is en dus in de besluitnotitie als apart, niet-ESS-04 punt hoort.

---

## 6. Casusregister

### R-29 — Het casusregister is sterk; drie gerichte punten
**Claim:** `casusregister-v1.md`, zeven historische labels plus 23 nieuwe scenario's.
**Oordeel:** bevestigd, met drie correcties/aanvullingen.
**Grond:**
1. **`good_fragment`: te streng, of althans op de verkeerde grond.** Codex verwacht "geen volledige pass" omdat het fragment "zonder volledig begrip/dagentelling" is. Dat is juist als je het fragment als *definitie* leest — maar het is ASTRA's eigen GOED-voorbeeld voor deze regel, en ASTRA presenteert het uitdrukkelijk als fragment. Een T-verwachting "geen volledige pass" op ASTRA's eigen goede voorbeeld verdient een expliciete grond, anders leest zij als een strengere norm dan de bron. Mijn voorstel: de verwachting scheiden in (a) als fragment beoordeeld tegen ESS-04: het criterium 'binnen 3 dagen nadat het verzoek is ingediend' is bepaald en heeft een startpunt — voldoet; (b) als volledige definitie beoordeeld: onvolledig, maar dat is ESS-01/ESS-05, niet ESS-04. Dat is ook precies het onderscheid dat Codex zelf in Q1 punt 4 maakt.
2. **De fictieve fixtures zijn goed gemarkeerd, en dat moet zo blijven.** F-K, F-P, F-T, F-V zijn expliciet als synthetische testafspraken benoemd. `instructievoorstellen-v1.md` neemt de partijzin echter over als `goede_voorbeelden` in het *regelrecord*, met de aantekening "uitsluitend fictieve bron F-P uit casusregister, geen willekeurig 80%-advies". Een regelrecord is productconfiguratie, geen casusregister: die aantekening reist niet mee en een lezer ziet straks "minimaal 80%" als goedgekeurd voorbeeld in de app. **Correctie:** in het record een goed voorbeeld kiezen dat zelfdragend is zonder fixture — de kaartkleur of "Document waarop de afzender een handtekening heeft geplaatst" — en het percentagegeval in het casusregister houden.
3. **Mijn C12 en C13 ontbreken en zijn onderscheidend.** "Beslissing die binnen drie dagen wordt genomen" (termijn in letters) en "Aanvraag die binnen 3 werkdagen na ontvangst wordt behandeld" (explicieter dan het ASTRA-voorbeeld) zijn inhoudelijk gelijkwaardig aan `good_fragment` en krijgen geen enkel patroonsignaal. Ze scheiden vorm van inhoud en horen in het gezamenlijke register.
**Gevolg:** één geïntegreerd register met behoud van beide ID-reeksen (E04-N01…N23 en ESS04-C01…C14); geen twee matrices achter elkaar, conform beide opdrachten.

---

## 7. Verifieerbaarheid en formele punten

### R-30 — De skillpaden in de voorstellen zijn niet verifieerbaar en wijken af van het enige pad in de opdracht
**Claim:** `instructievoorstellen-v1.md`, §Exacte skillwijzigingen: "Alle onderstaande paden vallen onder `/Users/chrislehnen/.agents/skills/`."
**Oordeel:** onvoldoende bewezen.
**Grond:** ik kan dat pad niet bereiken; alleen de uitwisselingsmap is gemount. Het enige skillpad dat in de gedeelde opdracht voorkomt is `/Users/chrislehnen/.codex/skills/toetsregel-onderzoek/` (`startopdracht.md`), en `feitenbasis/bestanden-v1.json` bindt de skillkopieën aan bronpaden onder `/Users/chrislehnen/Projecten/Definitie-app/...`. Drie verschillende wortels dus, en geen daarvan is `.agents/skills/`.
**Gevolg:** vóór uitvoering de werkelijke installatielocatie van de vijf `definitie-*`-skills verifiëren en in het voorstel vastleggen. Een vervangtekst met een verkeerd pad is niet toepasbaar, en bij deze zes voorstellen is het pad het enige wat de vindplaats bepaalt. Geen inhoudelijk bezwaar tegen de teksten zelf.

### R-31 — Niet-volgbare bijlagen vanuit de gedeelde kopie
**Claim:** `bron-bewijsregister-v1.md` verwijst naar `codebasis-4cdb8ea43.tar` (`archive_sha256` in `codebasis-actueel-v1.json`) en de map `codebasis-4cdb8ea43/`.
**Oordeel:** geen defect; grens van mijn verificatie.
**Grond:** beide ontbreken in de gedeelde map; `kruisreview-opdracht-v1.md` meldt dat de relatieve links bewust ongewijzigd zijn gelaten en dat het codearchief lokaal bij Codex blijft. Ik heb de codeclaims daarom geverifieerd tegen `werkboom-4cdb8ea43/` plus beide naleveringen, die alle hashgebonden zijn aan dezelfde commit `4cdb8ea43`. Alle door mij gecontroleerde regelnummers kwamen overeen.
**Gevolg:** de claim "archive_hash_ok" blijft een Codex-interne controle. Voor de synthese is dat voldoende zolang de gedeelde, hashgebonden selectie de bewijsbasis is; het is het vermelden waard in de bewijsgrenzen.

### R-32 — Dekkingstabel van de veertien onderdelen
**Claim:** `codex-onderzoek-v1.md`, slottabel.
**Oordeel:** bevestigd; alle veertien onderdelen hebben een vindplaats en de vindplaatsen bestaan.
**Grond:** gecontroleerd tegen de genoemde secties en bijlagen. Onderdeel 13 is correct als "eigen voorstel gereed, wederzijdse review nog niet uitgevoerd" gemarkeerd — dat klopte op het moment van bevriezen.
**Gevolg:** geen.

### R-33 — Twee plekken waar het pakket zichzelf tegenspreekt
**Claim/oordeel:** twee interne inconsistenties, beide klein maar verwarrend voor een lezer die niet alles leest.
1. `codex-onderzoek-v1.md` Q1 zegt dat de ASTRA-passage niet toegankelijk was; het addendum zegt het tegendeel; `bron-bewijsregister-v1.md` S05 draagt nog de oude status. Drie bestanden, drie stadia. **Correctie:** bij synthese S05 en de Q1-zin voorzien van een verwijzing naar het addendum, zoals het addendum zelf vraagt ("verwijder het achterhaalde tekort actuele ASTRA-passage").
2. `instructievoorstellen-v1.md` N1 zegt "Bronherkomst bevat straks de exact geverifieerde ASTRA-revisie plus lokale uitwerking; actuele ASTRA-tekst ontbreekt nu, dus niet reconstrueren." Die tekst ontbreekt niet meer: revisie `oldid=8558`, laatst bewerkt 11 februari 2025 09:46, en de volledige veldweergave staat in `astra-bronobservatie-v2.md` en in mijn §2.1. **Correctie:** de revisie kan nu in het record worden opgenomen.

---

## 8. Wat ik overneem, wat ik handhaaf, wat open blijft

**Overgenomen uit het Codex-onderzoek** (verwerkt in `cowork-aanvulling-op-eigen-v1.md`): de scoreloze contractkeuze bij een toekomstig ESS-04-reviewcontract (R-27); het onderscheid definitieoordeel tegenover gevalsoordeel bij ontbrekend bewijs (R-05, R-26); de vierdeling van beoordelaarsdivergentie (R-24); de metadata-grens uit P01 (R-17); de voorwaardelijke bewijsvereisten rond noemer, lege populatie en bronconflict (R-10); de INT-02/06-relatie (R-14); de diagnosekolom "benodigd onderscheidend bewijs" (R-23); en Codex' voorwaardelijke formulering voor werk- tegenover kalenderdagen boven mijn hardere eis (R-10).

**Gehandhaafd tegenover het Codex-onderzoek:** het criteriumgerichte onderwerp van de normzin (R-02); de noodzaak om `herkenbaar_patronen` samen met het recordvoorstel te behandelen (R-16); het schema als grond dat een ESS-04-reviewschrijfroute niet alleen ontbreekt maar is uitgesloten (R-20); en de vaststelling dat DEF-630 een reeds vastgesteld, onuitgevoerd criterium bevat voor verplichte `review_required`-uitkomsten (R-25).

**Open, en voor Chris:** de gezamenlijke keuzelijst uit R-26, inclusief de twee keuzes die Codex niet noemt. Geen van beide onderzoekers heeft hier iets besloten; mijn §7.4-punten zijn en blijven voorstellen.

**Nog ontbrekend in de fase:** de Codex-review op mijn v1, mijn verwerking daarvan, de Codex-verwerking van deze review, en de synthese met mijn controle daarop. Zolang die ontbreken is het onderzoek niet gezamenlijk afgerond.

---

## Bijlage — controles die ik voor deze review heb uitgevoerd

| Controle | Uitkomst |
|---|---|
| Hashes `codex-reviewpakket-v1/manifest.json` | 19/19 gelijk |
| Hashes `nalevering2-manifest-v1.json` | 4/4 gelijk, commit 4cdb8ea43 |
| ASTRA Toetsbaarheid zelf geopend | toegankelijk; velden gelijk aan `astra-bronobservatie-v2.md`; oldid 8558; 11-02-2025 09:46 |
| ASTRA ESS-03 zelf geopend | "Geldig voor: telbare zelfstandige naamwoorden"; tweebeoordelaarsformulering letterlijk aanwezig |
| VIM3 §1.30 en §2.1 zelf gelezen (incl. notes/annotaties) | ondersteunen S07 |
| NL-SBB §2.4.1.1–2.4.1.2 zelf gelezen | ondersteunen de veldscheiding definitie/toelichting/uitleg |
| `get_additional_patterns("ESS-04")` | leeg — geen extra ESS-04-patronen (sluit mijn eigen bewijsgat R9) |
| `registry.py` | expliciet register, geen dynamische import, geen default-pass bij onbekend type |
| `types_internal.py` | `EvaluationContext.from_params` bestaat; `cleaned_text` valt terug op `text` |
| `approval_gate_policy.py` | hard 0.75 / soft 0.65 / `allow_hard_override` False; woord "review" komt niet voor |
| Codeclaims codeaanvulling (`:977-994`, `:1019`, `:1568-1630`, `:2034-2071`, `:1168`) | alle vier geverifieerd |
| Oude normalisatie (`werkboom/`, 50d0770) | `BASIC-001/2/3` op `types.py:601`,`:716`, `mappers.py:29`; geen `neem_contractvelden_over` — C03 bevestigd |
| Nieuwe normalisatie (`result_contract.py:56-66`) | vier contractvelden aanwezig — C03 bevestigd |
| P01-signaal nagerekend | `\btoetsbaar\b` vuurt op de Codex-tekst |
| Negen Codex-teksten (voorstellen + N06/N10/N14) door de huidige patronen | geen enkel signaal — grond onder R-16 |
| Rekenkundige casuscontrole N06, N08, N10, N12 | alle correct |
| Dekkingstabel veertien onderdelen | alle vindplaatsen bestaan |
