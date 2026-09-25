# Gerichte broncontrole bij verwerking RA-B

HEAD 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3. Statische controle, geen nieuwe runtimeproef. P3 van A volledig gelezen; geen herhaling nodig voor dezelfde claim.

## src/services/prompts/modules/json_based_rules_module.py

SHA-256 307e4c78b55abb748f2f10654425140cd3f23f917934cbf8f9a1fdd6fa42f22b

```text
330:             # DEF-766: één norm voor genereren en toetsen (G). De oude
331:             # instructie "noem criteria voor unieke identificatie (zoals
332:             # serienummer, kenteken, ID, registratienummer)" is vervallen: een
333:             # nummer is geen bewijs van individuatie en de opdracht liet een
334:             # model identifiers, bronnen en telconventies verzinnen of een stof
335:             # tot monster maken. De gerichte verduidelijkingsvraag uit de
336:             # onderzoekstekst loopt binnen het bestaande uitvoercontract (één
337:             # zin, alleen de definitiekern) via de ESS-03-beoordeling; de
338:             # conflictmelding van DEF-751 blijft beperkt tot de ESS-02-
339:             # betekenislaag en wordt hier niet stil verbreed.
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
```

## src/services/prompts/modules/output_specification_module.py

SHA-256 780ce7f555f366e4904ec73439dfbe3adfd6aabc405db2a5923efc72e95b9f8e

```text
139:     def _build_basic_format_requirements(self) -> str:
140:         """Bouw basis format vereisten."""
141:         return """### 📏 OUTPUT FORMAT VEREISTEN:
142: - Definitie in één enkele zin
143: - Geen punt aan het einde
144: - Geen haakjes BEHALVE voor afkortingen (bijv. DJI, AVG)
145: - Geen voorbeelden in de definitie
146: - Volg ESS-01: begripsafbakening, met onderbouwde begripsbepalende functies; overig doel of gebruik alleen als afzonderlijk voorstel buiten deze definitiekern"""
```

## src/services/orchestrators/definition_orchestrator_v2.py

SHA-256 ec44f5eb4fc6bd7d413902869ff3c342a5f2b8176d22d7fdab9e22d96a9d7259

```text
1263:             herstelbare_overtredingen = self._herstelbare_overtredingen(
1264:                 validation_result
1265:             )
1266:             if (
1267:                 herstelbare_overtredingen
1268:                 and self.config.enable_enhancement
1269:                 and self.enhancement_service
1270:             ):
1271:                 enhanced_text = await self.enhancement_service.enhance_definition(
1272:                     cleaned_text,
1273:                     herstelbare_overtredingen,
1274:                     context=sanitized_request,
1275:                 )
1276: 
1976:     def _herstelbare_overtredingen(validation_result: Any) -> list[Any]:
1977:         """Overtredingen die de bestaande enhancement mogen bereiken.
1978: 
1979:         Uitgesloten: regels zonder cijfer (`rule_results`, i.e. CON-01): hun
1980:         uitkomst vraagt een expertbeoordeling of een bewuste gebruikersactie,
1981:         geen automatisch tekstherstel (DEF-622; herstelontwerp is DEF-638).
1982: 
1983:         Runtimecontract ongewijzigd: net als vóór DEF-622 gaan de
1984:         schema-conforme violation-dicts van het validatieresultaat door
1985:         (`list[Any]`, zoals `ensure_list` ze leverde); de interface annoteert
1986:         de dataclass `ValidationViolation` — die bestaande discrepantie wordt
1987:         hier niet beslist.
1988:         """
1989:         zonder_cijfer = set(
1990:             ensure_dict(safe_dict_get(validation_result, "rule_results", {})).keys()
1991:         )
1992:         overtredingen: list[Any] = []
1993:         for overtreding in ensure_list(
1994:             safe_dict_get(validation_result, "violations", [])
1995:         ):
1996:             if not isinstance(overtreding, dict):
1997:                 continue
1998:             code = overtreding.get("code") or overtreding.get("rule_id")
1999:             if code in zonder_cijfer:
2000:                 continue
```

## src/services/container.py

SHA-256 4868577de9a5a8f60855e39db81ed7458b2a7f2632623521624b54b6fae07666

```text
377:                 prompt_service=None,  # Will be lazy-loaded on first access
378:                 ai_service=ai_service,
379:                 # DEF-90: validation_service=None triggers lazy loading (saves 345ms, 56%!)
380:                 validation_service=None,  # Will be lazy-loaded on first access
381:                 cleaning_service=cleaning_service,
382:                 repository=self.repository(),
383:                 # Optional services
384:                 enhancement_service=None,  # Not implemented yet
385:                 security_service=SecurityService(),  # DEF-448: conservatieve sanitization
386:                 monitoring=None,  # Not implemented yet
387:                 feedback_engine=None,  # Not implemented yet
```

## src/database/models.py

SHA-256 b00fec0ed549727ac35851d4d1eadb560f2378d5238d9f607b2372f479e30a55

```text
136: def issues_uit_validatieresultaat(validation: Any) -> list[dict[str, Any]]:
137:     """Vertaal de `violations` van een validatieresultaat naar `validation_issues`.
138: 
139:     Dezelfde itemvorm als de bestaande lezers gebruiken (experttab, gate,
140:     CLI, export): `code`, `rule_id`, `severity`, `description`, plus
141:     `category`/`location`/`suggestions` wanneer aanwezig. Niets wordt
142:     verzonnen: een ontbrekend veld blijft leeg.
143:     """
144:     if not isinstance(validation, dict):
145:         return []
146:     items: list[dict[str, Any]] = []
147:     for violation in validation.get("violations") or []:
148:         if not isinstance(violation, dict):
149:             continue
150:         item: dict[str, Any] = {
151:             "code": violation.get("code") or violation.get("rule_id") or "",
152:             "rule_id": violation.get("rule_id") or violation.get("code") or "",
153:             "severity": violation.get("severity") or "",
154:             "description": (
155:                 violation.get("message") or violation.get("description") or ""
156:             ),
157:         }
158:         for extra in ("category", "location", "suggestions"):
159:             if violation.get(extra) is not None:
160:                 item[extra] = deepcopy(violation[extra])
161:         items.append(item)
162:     return items
```

## src/services/definition_workflow_service.py

SHA-256 5e17dffc6f458f05449d655f9a4604a503d44f3f542a8749a1a01863955622a2

```text
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
```

## src/services/validation/evaluators/judgment_review.py

SHA-256 046ab1df7d2d80997c58f6bf44a482f9dfbed85e08624ae863a0b091ddb278eb

```text
157:     @staticmethod
158:     def _reden_met_passages(
159:         kop: str,
160:         ctx: EvaluationContext,
161:         signalen: tuple[str, ...],
162:         *,
163:         vraag: str,
164:         zonder_signaal: str = (
165:             "Geen patroonsignaal gevonden; inhoudelijke beoordeling blijft nodig."
166:         ),
167:     ) -> str:
168:         """Leesbare reden: de kop plus de letterlijk geciteerde passages.
169: 
170:         De regexpatronen zelf reizen als `signals` mee voor diagnostiek; de
171:         eindgebruiker krijgt uitsluitend de getroffen tekstfragmenten. In
172:         `vraag` wordt een letterlijke `{passage}` vervangen door het fragment
173:         (DEF-767); `zonder_signaal` is de tekst na de kop als geen patroon
174:         vuurt.
175:         """
176:         treffers = sorted(
177:             (hit.start(), hit.group())
178:             for patroon in signalen
179:             for hit in re.finditer(patroon, ctx.cleaned_text or "", re.IGNORECASE)
180:         )
181:         passages = dict.fromkeys(fragment for _, fragment in treffers)
182:         if not passages:
183:             return f"{kop} {zonder_signaal}"
184:         return (
185:             kop
186:             + " "
187:             + " ".join(
188:                 f"Te beoordelen passage: {fragment}. "
189:                 f"{vraag.replace('{passage}', fragment)} Dit signaal geeft nog geen "
190:                 "inhoudelijk oordeel."
191:                 for fragment in passages
192:             )
```
