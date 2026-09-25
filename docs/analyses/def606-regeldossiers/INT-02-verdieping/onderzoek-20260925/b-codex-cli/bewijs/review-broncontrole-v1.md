# Gerichte broncontrole kruisreview B op A

HEAD 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3. Alleen statische lezing, geen appproef.

## src/toetsregels/regels/INT-10.json

SHA-256 `4ba7fa9865c83f3c1a1eb05759f95e29a2176b99c074463ca4f50ed045c35ff0`

```text
1: {
2:   "id": "INT_10",
3:   "naam": "Geen ontoegankelijke achtergrondkennis nodig",
4:   "uitleg": "Een definitie moet begrijpelijk zijn zonder specialistische of niet-openbare kennis; uitzondering: zeer specifieke verwijzing naar openbare bron (bijv. wet met artikel).",
5:   "toelichting": "Een goede definitie is zelfstandig begrijpelijk en mag niet verwijzen naar impliciete kennis in hoofden van mensen, interne procedures of niet-openbare documenten. Verwijzen naar een openbare bron (zoals een wet met specifiek artikel en hyperlink) is wel toegestaan mits eenduidig en volledig.",
6:   "toetsvraag": "Is de definitie begrijpelijk zonder niet-openbare achtergrondkennis (behalve bij zeer specifieke bronvermelding)?",
7:   "herkenbaar_patronen": [
8:     "\\bzie\\b",
9:     "\\bzoals gedefinieerd in\\b",
10:     "\\bafgekort als\\b",
11:     "\\bzoals bekend binnen\\b",
12:     "\\bvolgens interne richtlijn\\b",
13:     "\\binterne notitie\\b",
14:     "\\bbekend binnen [A-Za-z]+\\b",
15:     "\\bindien\\b",
16:     "benodigde bescheiden"
17:   ],
18:   "goede_voorbeelden": [
19:     "instantie: organisatieonderdeel dat belast is met een bestuurlijke taak"
20:   ],
21:   "foute_voorbeelden": [
22:     "instantie: zie definitie in het beleidsdocument X"
23:   ],
24:   "prioriteit": "hoog",
25:   "aanbeveling": "verplicht",
26:   "geldigheid": "gehele definitie",
27:   "status": "definitief",
28:   "type": "begrijpelijkheid",
29:   "thema": "interne kwaliteit van de definitie",
30:   "brondocument": "ASTRA",
31:   "relatie": [
32:     {
33:       "fulltext": "Geen ontoegankelijke achtergrondkennis nodig",
34:       "fullurl": "https://www.astraonline.nl/index.php/Geen_ontoegankelijke_achtergrondkennis_nodig"
35:     }
36:   ],
37:   "runtime_contract": {
38:     "evaluator": "generic",
39:     "required_inputs": [
40:       "definition_text"
41:     ],
42:     "executability": "deterministic",
43:     "automation_status": "automated",
44:     "score_policy": "scored",
45:     "example_pair_policy": "normative"
46:   }
47: }
```

## src/services/validation/evaluators/generic.py

SHA-256 `9979c752e9175479cb918b85dfa6e3661d358bfa3c5e4c85ef811ea119c162a9`

```text
96:     findings: list[Finding] = []
97: 
98:     # 1) Verboden regexpatronen
99:     treffers: list[str] = []
100:     eerste_patroon: str | None = None
101:     eerste_positie: int | None = None
102:     for patroon in _gecompileerde_patronen(code, record, deps):
103:         for match in patroon.finditer(text):
104:             treffers.append(patroon.pattern)
105:             if eerste_positie is None or match.start() < eerste_positie:
106:                 eerste_positie = match.start()
107:                 eerste_patroon = patroon.pattern
108: 
109:     if treffers and not patronen_zijn_positief:
110:         lijst = ", ".join(sorted(set(treffers)))
111:         findings.append(
112:             Finding(
113:                 message=f"Verboden patroon gedetecteerd: {lijst}",
114:                 reason="forbidden_patterns",
115:                 details=lijst,
116:             )
117:         )
118: 
119:     # 2) Vereiste patronen
120:     vereiste_patronen = list(record.get("required_patterns", []) or [])
```

## src/services/validation/modular_validation_service.py

SHA-256 `f2e777c447ed38cbb754f6d811b3ab5e35ca20a0f67ebda01689ac77506d781b`

```text
1528:             )
1529:         if not outcome.findings:
1530:             return 1.0, None
1531: 
1532:         rule = state.json_rules.get(code, {})
1533:         text = ctx.cleaned_text or ""
1534:         treffers = set(outcome.pattern_hits)
1535:         score = 0.0 if not treffers else max(0.0, 1.0 - 0.3 * len(treffers))
1536:         beschrijving = "; ".join(
1537:             dict.fromkeys(bevinding.message for bevinding in outcome.findings)
1538:         )
1539:         suggesties = [
1540:             self.build_suggestion(
1541:                 code,
1542:                 rule,
1543:                 text,
1544:                 ctx,
1545:                 reason=bevinding.reason,
1546:                 details=bevinding.details,
1547:             )
1548:             for bevinding in outcome.findings
1549:         ]
1550:         violation: dict[str, Any] = {
1551:             "code": code,
1552:             "severity": self.severity_for(rule),
1553:             "severity_level": self.severity_level_for(rule),
1554:             "message": beschrijving,
1555:             "description": beschrijving,
1556:             "rule_id": code,
1557:             "category": category_for_rule(code),
1558:             "suggestion": "; ".join([s for s in suggesties if s]).strip() or None,
1559:         }
1560:         md: dict[str, Any] = {}
1561:         if outcome.first_hit_pattern is not None:
1889:     def _severity_level_for_json_rule(self, rule: dict[str, Any]) -> str:
1890:         """Map JSON aanbeveling/prioriteit naar severity-level (critical/high/medium/low)."""
1891:         aan = str(rule.get("aanbeveling", "")).lower()
1892:         pri = str(rule.get("prioriteit", "")).lower()
1893:         if aan == "verplicht" and pri == "hoog":
1894:             return "critical"
1895:         if aan == "verplicht":
1896:             return "high"
1897:         if pri == "hoog":
1898:             return "medium"
1899:         return "low"
1900: 
1901:     def _severity_for_json_rule(self, rule: dict[str, Any]) -> str:
1902:         """Compatibele severity (error/warning) afgeleid van severity-level."""
1903:         lvl = self._severity_level_for_json_rule(rule)
1904:         return "error" if lvl in ("critical", "high") else "warning"
1905: 
1906:     def _build_suggestion_for_violation(
```

## src/services/definition_workflow_service.py

SHA-256 `5e17dffc6f458f05449d655f9a4604a503d44f3f542a8749a1a01863955622a2`

```text
715:     def _evaluate_gate(self, definition: DefinitieRecord) -> dict[str, Any]:
716:         """Implementeert Option B gate-logica.
717: 
718:         Verwacht DefinitieRecord met velden:
719:         - validation_score (float | None)
720:         - validation_issues (JSON) via get_validation_issues_list()
721:         - organisatorische_context (str)
722:         - juridische_context (str | None)
723:         - wettelijke_basis (list via get_wettelijke_basis_list())
724:         """
725:         policy = self._get_policy()
726: 
727:         reasons: list[str] = []
728: 
729:         # 1) Context aanwezig? (JSON arrays in TEXT voor org/jur; wet via helper)
730:         org_list, jur_list, wb_list = self._gate_contextlijsten(definition)
731: 
732:         if policy.hard_requirements.get("min_one_context_required", True):
733:             if not (org_list or jur_list or wb_list):
734:                 reasons.append("Geen context ingevuld (minimaal één vereist)")
735: 
736:         # 2) Validatiescore en issues
737:         score = getattr(definition, "validation_score", None)
738:         issues: list[dict[str, Any]] = []
739:         if hasattr(definition, "get_validation_issues_list"):
740:             issues = definition.get_validation_issues_list() or []
741:         severities = {str(i.get("severity", "")).lower() for i in issues}
742:         has_critical = "critical" in severities
743:         has_high = "high" in severities and not has_critical
744: 
745:         # 3) Hard conditions
746:         hard_min = policy.hard_min_score
747:         soft_min = policy.soft_min_score
748: 
749:         if score is None:
750:             # DEF-622: ook 'totaalscore niet beschikbaar' (CON-01 zonder
751:             # cijfer) landt hier als None. De blokkade blijft fail-closed;
752:             # de herdefinitie van de scoregate zonder totaalscore is DEF-630.
753:             reasons.append("Geen validatieresultaat beschikbaar (eerst (her)valideren)")
754: 
755:         if (
756:             policy.hard_requirements.get("forbid_critical_issues", True)
757:             and has_critical
758:         ):
759:             reasons.append("Kritieke issues aanwezig")
760: 
761:         if score is not None and float(score) < hard_min:
762:             reasons.append(f"Score onder harde drempel ({hard_min:.2f})")
763: 
764:         # DEF-622 (B-07): het contextcontract is een vaststelvoorwaarde die
765:         # niet met een notitie te overrulen is. Geen context, een open
766:         # naamfunctie, een beoordeling die niet meer bij de huidige tekst/
767:         # context hoort, of registratiegebruik: geen vaststelling. Het concept
768:         # blijft gewoon bewerkbaar. Herberekend op het record zelf, zodat een
769:         # verouderde beoordeling nooit kan doortellen.
770:         niet_overrulebaar: list[str] = []
771:         if not (org_list or jur_list or wb_list):
772:             niet_overrulebaar.append(
773:                 "Geen context vastgelegd bij het record (CON-01, B-01); "
774:                 "vaststellen is niet mogelijk zonder context"
775:             )
776:         else:
777:             niet_overrulebaar.extend(self._con01_blokkades(definition))
778:         # DEF-743 (CON-02): verouderd, technisch mislukt of ontbrekend bronbewijs
779:         # kan niet als goedgekeurd gelden; een geaccepteerde deskundige
780:         # uitzondering wordt als uitzondering herkend. Smalle guard naast de
781:         # bestaande scoregate (die blijft ongewijzigd, incl. de blokkade bij
782:         # `validation_score is None` — DEF-630).
783:         niet_overrulebaar.extend(self._con02_blokkades(definition))
784: 
785:         hard_block = any(
786:             r in reasons
787:             for r in [
788:                 "Geen context ingevuld (minimaal één vereist)",
789:                 "Kritieke issues aanwezig",
790:                 f"Score onder harde drempel ({hard_min:.2f})",
791:                 "Geen validatieresultaat beschikbaar (eerst (her)valideren)",
792:             ]
793:         )
794: 
795:         if niet_overrulebaar:
796:             return {"status": "blocked", "reasons": niet_overrulebaar + reasons}
797: 
798:         if hard_block:
799:             # Optioneel: sta override toe voor hard blocks indien policy dit toestaat
800:             try:
801:                 allow_hard_override = bool(
802:                     getattr(policy, "soft_requirements", {}).get(
803:                         "allow_hard_override", False
804:                     )
805:                 )
806:             except Exception:
807:                 allow_hard_override = False
808: 
809:             if allow_hard_override:
810:                 # Converteer naar override_required met bestaande redenen (UI vereist reden/notities)
811:                 return {"status": "override_required", "reasons": reasons}
812:             return {"status": "blocked", "reasons": reasons}
813: 
814:         # 4) Soft conditions
815:         soft_reasons: list[str] = []
816:         if score is not None and soft_min <= float(score) < hard_min:
817:             soft_reasons.append(
818:                 f"Score onder vaststel-drempel maar ≥ soft-drempel ({soft_min:.2f})"
819:             )
820:         if (
821:             policy.soft_requirements.get("allow_high_issues_with_override", True)
822:             and has_high
823:         ):
824:             soft_reasons.append("Alleen hoge issues aanwezig (geen kritieke)")
825:         if policy.soft_requirements.get("missing_wettelijke_basis_soft", True):
826:             if not wb_list:
827:                 soft_reasons.append("Wettelijke basis ontbreekt")
828: 
829:         if soft_reasons:
830:             return {"status": "override_required", "reasons": soft_reasons}
831: 
832:         return {"status": "pass", "reasons": []}
833: 
834:     @staticmethod
835:     def _gate_contextlijsten(
836:         definition: DefinitieRecord,
```

## src/services/definition_import_service.py

SHA-256 `dc603a3c018108159523eefaf4cab2401b8c775744c83e0f15d9a1ae27cf59c1`

```text
67:     async def validate_single(self, payload: dict[str, Any]) -> SingleImportPreview:
68:         """Valideer één definitie en geef duplicates terug.
69: 
70:         Vereist velden in payload: begrip, definitie, categorie, organisatorische_context(list),
71:         optioneel: juridische_context(list), wettelijke_basis(list).
72:         """
73:         definition = self._payload_to_definition(payload)
74:         validation = await self._validator.validate_definition(definition)
75: 
76:         # Duplicaatcontrole op begrip + context (repository logica)
77:         # Run sync database operation in thread pool to prevent blocking
78:         loop = asyncio.get_event_loop()
79:         duplicates = (
80:             await loop.run_in_executor(
81:                 self._executor, self._repo.find_duplicates, definition
82:             )
83:             or []
84:         )
85: 
86:         ok = True
87:         try:
88:             ok = bool(validation.get("is_acceptable", False))
89:         except (TypeError, AttributeError) as e:
90:             logger.warning(
91:                 "Validatie resultaat kon niet worden geïnterpreteerd",
92:                 extra={"begrip": definition.begrip, "error_type": type(e).__name__},
93:             )
94:             ok = False
95: 
96:         return SingleImportPreview(validation=validation, duplicates=duplicates, ok=ok)
97: 
98:     async def import_single(
99:         self,
100:         payload: dict[str, Any],
101:         *,
102:         allow_duplicate: bool = False,
103:         duplicate_strategy: str | None = None,
104:         created_by: str | None = None,
105:     ) -> SingleImportResult:
106:         """Voer de daadwerkelijke import uit na validatie."""
107:         # Run validation in async context
108:         import asyncio
109: 
110:         # Voor kleine timeout safety, gebruik asyncio.wait_for
111:         try:
112:             preview = await asyncio.wait_for(self.validate_single(payload), timeout=2.0)
113:         except TimeoutError:
114:             return SingleImportResult(
115:                 success=False,
```

## src/ui/components/expert_review_tab.py

SHA-256 `0468c8c423b6543099103a15d1276d959c506d6e7aad518c02bde466b35afc31`

```text
1071:     _ONDERDEELLABEL = {
1072:         "source_authority": "Brongezag/toepasselijkheid",
1073:         "semantic_support": "Betekenissteun",
1074:         "reference_quality": "Verwijskwaliteit",
1075:     }
1076:     _CORRECTIESTATUS = {
1077:         "pass": "voldoet",
1078:         "fail": "voldoet niet",
1079:         "review_required": "nog te beoordelen (bewijs ontbreekt; motiveer)",
1080:     }
1081: 
1082:     def _correctie_invoer(
1083:         self,
1084:         sleutel: str,
1085:         uitkomst: Any,
1086:         canoniek: Any,
1087:         onderdelen: tuple[str, ...],
1088:     ) -> tuple[dict[str, Any] | None, list[str]]:
1089:         """Invoer voor `part_correction` (C §6b): één onderdeel, één oordeel, één
1090:         gebonden bewijsclaim (id/hash/versie uit de bewaarde bron; citaat en
1091:         vindplaats van de deskundige). Toont het oorspronkelijke AI-oordeel
```

## src/ui/components/validation_view.py

SHA-256 `238b6b4a0d1e092d8a1e7ea846402c4d3ed5bbf6e41c3283e4722d3a671b0988`

```text
237: def _statuslijst_regels(
238:     validation_result: dict[str, Any], *, uitgesloten: set[str]
239: ) -> list[str]:
240:     """Regels die open, mislukt of niet gedraaid zijn — als eigen lijnen.
241: 
242:     Zij staan noch bij de violations noch bij de geslaagde regels en zouden
243:     anders onzichtbaar blijven; een regel met gestructureerde uitkomst
244:     (``rule_results``) wordt apart in detail getoond en hier overgeslagen.
245:     """
246:     statussen = validation_result.get("rule_statuses")
247:     if not isinstance(statussen, dict):
248:         return []
249:     lijnen: list[str] = []
250:     for status, label in (
251:         ("review_required", "🟠 Nog te beoordelen"),
252:         ("error", "⚙️ Technisch probleem"),
253:         ("not_evaluated", "⏸️ Niet beoordeeld"),
254:         ("not_applicable", "➖ Niet van toepassing"),
255:     ):
256:         codes = sorted(
257:             (str(code) for code, s in statussen.items() if str(s) == status),
258:             key=_rule_sort_key,
259:         )
260:         codes = [c for c in codes if c not in uitgesloten]
261:         if codes:
262:             lijnen.append(f"{label}: {', '.join(codes)}")
263:     return lijnen
794:     # DEF-746/DEF-750/DEF-767: de open reden van ESS-01, ESS-02 en ESS-04 is
795:     # ook bij ingeklapte details zichtbaar — voor ESS-04 altijd de open
796:     # status plus de reviewvraag (passagevraag of toetsvraag), ook zonder
797:     # treffer. Passages zijn gebruikersinvoer: toon ze letterlijk, niet als
798:     # Markdown of HTML. Dit is de leesbare signaalweergave (A); de menselijke
799:     # beoordeling zelf en haar opslag volgen in C/D (DEF-624/626/627). ESS-03
800:     # staat hier sinds DEF-766 niet meer bij: zijn uitkomst (vier oordelen,
801:     # vraag, fout) komt gestructureerd uit `rule_results` hierboven en zou
802:     # hier dubbel verschijnen.
803:     for review_item in validation_result.get("review_required") or []:
804:         if not isinstance(review_item, dict):
805:             continue
806:         rule_id = review_item.get("rule_id")
807:         if rule_id in ("ESS-01", "ESS-02", "ESS-04"):
808:             st.text(str(review_item.get("reason") or f"{rule_id} — Nog te beoordelen"))
859:     for line in lines:
860:         # Statuslijsten (open/mislukt/niet gedraaid): informatief, geen
861:         # uitleg-expander per regel (het is een opsomming van codes).
862:         if line.startswith(("🟠 Nog te beoordelen:", "⚙️ Technisch probleem:", "⏸️ ")):
863:             st.info(line)
864:             continue
865:         # Color per status
866:         if line.startswith("✅"):
867:             st.success(line)
868:         elif "❌" in line and not line.startswith("📊"):
869:             st.error(line)
870:         elif "⚠️" in line or line.startswith("📊"):
871:             st.warning(line) if not line.startswith("📊") else st.info(line)
872:         else:
873:             st.info(line)
874: 
875:         # Inline explanation per rule (skip pure summary lines)
876:         rid = _extract_rule_id_from_line(line)
877:         if rid:
878:             with st.expander(f"ℹ️ Toon uitleg voor {rid}", expanded=False):
879:                 st.markdown(_build_rule_hint_markdown(rid))
```

## src/services/prompts/modules/json_based_rules_module.py

SHA-256 `307e4c78b55abb748f2f10654425140cd3f23f917934cbf8f9a1fdd6fa42f22b`

```text
340:             "ESS-03": (
341:                 "Bepaal uit de bedoelde betekenis en de beschikbare onderbouwing wat "
342:                 "als één instantie geldt. Maak een noodzakelijke eenheidsgrens "
343:                 "duidelijk met een passend bovenbegrip en begripsbepalende kenmerken. "
344:                 "Gebruik een identifier alleen als zijn referentsoort, scope en "
345:                 "relevante geldigheid zijn onderbouwd; verzin geen nummer, bron of "
346:                 "telconventie. Laat niet-telbare stoffen of kwaliteiten niet stil "
347:                 "veranderen in telbare monsters, porties of registraties. Bij een "
348:                 "noodzakelijke maar onbesliste eenheidsgrens of continuïteitsvraag "
349:                 "waarover bronnen en context elkaar niet werkelijk tegenspreken: "
350:                 "verzin geen grens of conventie en lever één voorlopige kandidaat "
351:                 "binnen de beschikbare grond, zonder melding of toelichting in de "
352:                 "zin; de gerichte verduidelijkingsvraag blijft bij de "
353:                 "ESS-03-beoordeling (uitkomst onvoldoende informatie, met één "
354:                 "gerichte vraag). Spreken bronnen of context "
355:                 "elkaar werkelijk tegen over de teleenheid, maak dan geen stille "
356:                 "keuze en leg geen betwiste telconventie in de kern vast. Een naam "
357:                 "of het woord ‘uniek’ is geen bewijs. "
358:                 "Houd registratiecontext en bronadministratie buiten de kern, maar "
359:                 "behoud inhoudelijk noodzakelijke namen en voorwaarden. Geef uitleg "
360:                 "en synthetische voorbeelden afzonderlijk; ze vervangen geen "
361:                 "ontbrekende kernafgrenzing."
362:             ),
363:             "ESS-04": "Gebruik objectief toetsbare elementen (deadlines, aantallen, percentages, meetbare criteria)",
364:             "ESS-05": "Maak expliciet duidelijk waarin het begrip zich onderscheidt van andere verwante begrippen",
365:             # STR rules (Structuur)
366:             "STR-01": "Start de definitie met een zelfstandig naamwoord of naamwoordgroep, niet met een werkwoord",
367:             "STR-02": "Begin met een breder begrip (genus) en specificeer vervolgens hoe de term daarvan verschilt",
368:             "STR-03": "Geef een volledige definitie, niet alleen een synoniem",
369:             "STR-04": "Volg de algemene opening direct met een toespitsing die het specifieke type verduidelijkt",
370:             "STR-05": "Beschrijf wat het begrip is, niet enkel uit welke onderdelen het bestaat",
371:             "STR-06": "Beschrijf wat het begrip is, niet waarvoor het dient of waarom het nodig is",
372:             "STR-07": "Vermijd dubbele ontkenningen (zoals 'niet zonder', 'onmogelijk om niet te')",
373:             "STR-08": "Gebruik 'en' ondubbelzinnig (maak duidelijk of beide vereist zijn of één van beide)",
374:             "STR-09": "Gebruik 'of' ondubbelzinnig (maak duidelijk of het inclusief of exclusief is)",
375:             # INT rules (Integriteit)
376:             "INT-01": "Formuleer de definitie als één enkele, begrijpelijke zin",
377:             "INT-02": "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'",
```

## docs/analyses/2026-09-15-DEF-606-besluit-geen-totaalscore-v1.md

SHA-256 `3f7ab1ab9ad06bc297c3037d9ae8ce48cfd65fe91098edd6a73cfef2d5791077`

```text
1: # Definitief appbesluit — geen totaalscore als kwaliteitsoordeel
2: 
3: 15 september 2026 · versie 1 · **besloten door Chris; geen softwareoplevering**.
4: 
5: ## Besluit en autorisatie
6: 
7: De totaalscore vervalt appbreed als **kwaliteitscijfer, acceptatiecriterium en stuurmiddel voor hergeneratie**. Dit vervangt de tijdelijke productkeuze ‘totaalscore niet beschikbaar’. Er wordt geen nieuwe formule of vervangend kwaliteitspercentage ingevoerd.
8: 
9: Bron: gesprek ‘Onderzoek DEF-606 en toetsregels’, taak `01a08f9d-a779-7382-b062-d0b38524a42f`. Chris antwoordde op 15 september 2026 **‘ja’** op het concrete voorstel en de vraag: ‘Wil je dit als definitieve appbrede keuze vastleggen, ter vervanging van de tijdelijke keuze “totaalscore niet beschikbaar”?’ Onderstaande onderdelen stonden in dat voorstel.
10: 
11: ## Het vervangende overzicht
12: 
13: | Onderdeel | Vastgelegde richting |
14: |---|---|
15: | Toetsuitkomsten | Per regel het oordeel, de onderbouwing en eventuele vervolgstap. |
16: | Volledigheid | Welke controles daadwerkelijk zijn uitgevoerd, ontbreken of technisch mislukten. |
17: | Benodigde acties | Welke inhoudelijke fouten en open vragen aandacht vragen. |
18: | Expertbeoordeling | Of de actuele definitieversie is beoordeeld en handmatig vastgesteld. |
19: 
20: - Een inhoudelijke overtreding wordt niet gecompenseerd door positieve uitkomsten op andere regels.
21: - Een ontbrekende beoordeling telt niet als geslaagd en niet als inhoudelijke fout.
22: - Een telling van uitkomsten mag het overzicht ondersteunen, maar wordt geen percentage ‘definitiekwaliteit’.
23: - Eventuele interne technische scores krijgen geen zelfstandige beslissingsbevoegdheid.
24: 
25: ## Doorwerking en grenzen
26: 
27: Dit is een **appbrede** keuze onder DEF-606. Het wijzigt niet automatisch de norm, toepasselijkheid, ernst, individuele scorepolicy of reviewplicht van alle afzonderlijke toetsregels. Die blijven per regel te onderzoeken en besluiten. Het besluit betekent ook niet dat iedere bevinding zonder onderscheid alle gebruikershandelingen blokkeert: toegestane conceptopslag, betekenis van adviezen en concrete vaststel-/exportvoorwaarden volgen hun eigen contract.
28: 
29: CON-01 had al een afzonderlijk besluit om geen cijfer te geven (B-06). De nieuwe appbrede keuze vervangt B-01–B-10 niet; zij vult het eerder afzonderlijk gelaten totaalscorebeleid in. Expertbeoordeling en handmatige vaststelling blijven vereist; een positief automatisch overzicht stelt niet vast.
30: 
31: De precieze migratie van bestaande UI-, API-, opslag-, export- en generatieconsumers vraagt een uitvoeringsplan binnen de bestaande eigenaarschappen. Dit besluit is geen opdracht om nu code, schema's, historische gegevens of skills te verwijderen of te veranderen. Het trekt eerder afzonderlijk verleende uitvoeringsopdrachten niet in.
32: 
33: ## Relevante bestaande eigenaren en actualiteit
34: 
35: - [DEF-624 — classificatie en resultaatcontract](https://linear.app/definitie-app/issue/DEF-624): gelezen op 15 september 2026; de issueactualisatie van die dag noemt de totaalscore nog **tijdelijk** niet beschikbaar en houdt score-uitwerking open. Die beleidsomschrijving is met dit latere besluit achterhaald voor de appbrede totaalscore. Classificatie, semantisch bewijs, dekking en consumer-/resultaatcontractwerk blijven relevant; dit besluit voltooit het issue niet.
36: - [DEF-622 — CON-01-contextcontract](https://linear.app/definitie-app/issue/DEF-622): bestaande implementatietaak moet de definitieve richting kennen; geen dubbele implementatie starten.
```

## docs/analyses/def606-regeldossiers/ESS-05-verdieping/onderzoek-20260921/gedeeld/besluiten-v1.md

SHA-256 `6696dab58fa47097662a47f12c52a3bd83e045bc3085208e9e24919e8886d801`

```text
1: # ESS-05 — besluiten van Chris (v1)
2: 
3: 21 september 2026 · DEF-768 · vastgelegd door Cowork na het één-voor-één doorlopen van de keuzes uit [besluitnotitie-chris-v2](besluitnotitie-chris-v2.md) en [gezamenlijke-synthese-v2](gezamenlijke-synthese-v2.md). Dit zijn productbesluiten; uitvoering vergt een afzonderlijke opdracht.
4: 
5: | ID | Besluit | Toelichting / afwijking van het onderzoeksvoorstel |
6: |---|---|---|
7: | K-1 | **Direct O3: LLM-beoordeling per verwant begrip** (contrastieve substitutietoets naar het ESS-03/CON-02-patroon), zonder cijfer. Het model mag zelf kandidaat-buren voorstellen, mits per buur duidelijk is wat de buren zijn en waar ze vandaan komen (repository / ontologie / bron / gebruiker / model, niet bevestigd). Door het model ingebrachte buren houden het oordeel op 'nog te beoordelen' totdat de expert ze bevestigt of afwijst. | Wijkt af van de fasering O2→O3 van de onderzoekers: geen O2-tussenstap; O2-gedrag (open oordeel + vraag) blijft de ingebouwde terugval zonder buren. |
8: | K-2 | Geen verwant begrip bekend → **'nog te beoordelen' met precies één vraag**; een expert kan met grond bevestigen dat de vergelijkingsruimte leeg is → afgerond 'voldoet — leeg bevestigd', gebonden aan kandidaat/context/versie; vervalt bij wijziging; nooit goedkeuring door tijdsverloop. | Conform voorstel. |
9: | K-3a | **Vergelijkingszin is vormoptie**, geen vereiste, geen bewijs; een contrast dat de definitie van het andere begrip nodig heeft hoort in de toelichting (app mag toelichtingsvoorstel aanbieden). | Conform (herstel ASTRA-norm). |
10: | K-3b | **Verwant begrip** = zusterbegrippen onder hetzelfde bovenbegrip; begrippen die in deze context verward kunnen worden of deels dezelfde gevallen dekken; door bron/gebruiker aangewezen begrippen. **Niet**: bovenbegrip, onderbegrippen, synoniemen, homoniemen in een andere context. **Overlap** van gevallen is geen gebrek zolang het onderscheidende kenmerk kenbaar is (rollen; volgens ESS-01 onderbouwd doelkenmerk). Registreren onder DEF-625 als lokale uitwerking. | Conform. |
11: | K-4 | **Prioriteit `midden`** (ASTRA); afwijking sluiten en registreren onder DEF-625. **Geen zelfstandige ESS-05-blokkade** van vaststellen/export; 'voldoet niet' blijft zichtbaar en exporteerbaar. Vocabulaireherstel error/critical in de gate pas ná de evaluatorwijziging. | Conform. |
12: | K-5 | **ASTRA-voorbeeldpaar** onttrekking/ontvluchting in het record (goed: één-zinsvariant met "één van de volgende … : … of …"; fout: letterlijk); grond: ontvluchting voldoet aan alle kenmerken van het foute voorbeeld; letterlijk ASTRA-citaat in de toelichting. Alleen invoeren samen met de nieuwe evaluator. | Conform; geen extra synthetisch paar. |
13: | K-6 | **Buurkanaal uit alle bronnen met herkomst en opslag**: repository (zelfde context), ontologiemodel (is-een-zusters, overlappende klassen), bronpassages, gebruikersinvoer, modelvoorstellen. Per buur herkomst bewaren en tonen; de gebruikte burenlijst wordt met de beoordeling opgeslagen (versiebinding). Transportgat (nesting in `enriched["definition"]`) en ontbrekende persistentie repareren. | Conform; uitvoeringsvoorwaarde voor K-1. |
14: | K-7 | **Geen automatisch herstel.** Toetsen wijzigt nooit tekst. Op verzoek hoogstens één begrensde poging onder DEF-638: alleen bij een ontbrekend kenmerk dat de bron geeft; kenmerk uit bron toevoegen; geen trefwoord, geen contrastzin als enige wijziging, geen vernauwing buiten de bron, geen tweede definitie, geen naam-/contextwijziging; origineel en verschil bewaren; alles hertoetsen; stop na één poging of bij betekenisverlies/bronconflict/onbekende buur. | Conform. |
15: | K-8 | **Elke toetsregel meldt zelf waarom een definitie niet voldoet** — geen onderdrukking. Bij 'Sanctie.' meldt STR-04 'geen toespitsing' én ESS-05 'kan zonder toespitsing geen enkel verwant begrip uitsluiten'. | Wijkt af van B's voorkeur (STR-04 als enige eigenaar); komt overeen met het alternatief in de synthese. |
16: | K-9 | **Context is op appniveau verplicht**: zonder context wordt niet gegenereerd en niet getoetst. Voor ESS-05: `context_lists` als vereiste invoer; ontbreekt hij toch, dan 'niet uitgevoerd' met reden, naast de CON-01-fout. | Wijkt af van het voorstel (ondersteunend). Aandachtspunt bij uitvoering: de app valideert vandaag wél zonder context (proeven A1/B1 liepen zonder context); afdwingen van 'niet toetsen zonder context' raakt CON-01/DEF-622 en de toets-ingangen. |
17: | K-10 | **Naam ongewijzigd** 'Voldoende onderscheidend'; verduidelijking in thema en uitleg. | Conform. |
```
