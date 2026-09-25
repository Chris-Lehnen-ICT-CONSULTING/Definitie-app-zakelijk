# Bronextracten B — statisch bewijs

HEAD 26f2374d302fc66fc0b12ed29dc34585f7c0a5c3. Regels geteld vanaf 1. Codelezing is geen uitgevoerde ketenproef.

## src/services/cleaning_service.py:54–93

```text
54:     async def clean_definition(self, definition: Definition) -> CleaningResult:
55:         """
56:         Schoon een definitie object op en update metadata.
57: 
58:         Args:
59:             definition: Definition object om op te schonen
60: 
61:         Returns:
62:             CleaningResult met opschoning details
63: 
64:         DEF-232: Now native async (no adapter needed).
65:         """
66:         # Gebruik clean_text voor de daadwerkelijke opschoning
67:         result = await self.clean_text(definition.definitie, definition.begrip)
68: 
69:         # Update de Definition object metadata als preserve_original enabled is
70:         if self.config.preserve_original and result.was_cleaned:
71:             if definition.metadata is None:
72:                 definition.metadata = {}
73: 
74:             definition.metadata.update(
75:                 {
76:                     "cleaning_applied": True,
77:                     "original_definitie": result.original_text,
78:                     "cleaning_timestamp": result.metadata.get("timestamp"),
79:                     "cleaning_rules_applied": result.applied_rules,
80:                 }
81:             )
82: 
83:         # Update de definitie tekst met opgeschoond resultaat
84:         definition.definitie = result.cleaned_text
85: 
86:         if self.config.log_operations and result.was_cleaned:
87:             logger.info(
88:                 f"Definitie opgeschoond voor '{definition.begrip}': {len(result.applied_rules)} regels toegepast"
89:             )
90: 
91:         return result
92: 
93:     async def clean_text(self, text: str, term: str) -> CleaningResult:
```

## src/services/cleaning_service.py:93–188

```text
93:     async def clean_text(self, text: str, term: str) -> CleaningResult:
94:         """
95:         Schoon definitie tekst op met gedetailleerde tracking.
96: 
97:         Args:
98:             text: Te schonen definitie tekst
99:             term: Het begrip dat gedefinieerd wordt
100: 
101:         Returns:
102:             CleaningResult met complete opschoning informatie
103: 
104:         DEF-232: Now native async - uses asyncio.to_thread for CPU-bound opschoning.
105:         """
106: 
107:         original_text = text.strip()
108: 
109:         try:
110:             # Initialiseer tracking lijsten
111:             applied_rules = []
112:             improvements = []
113: 
114:             # Check of we GPT format moeten hanteren
115:             handle_gpt = "ontologische categorie:" in original_text.lower()
116: 
117:             if handle_gpt:
118:                 # Import analyze_gpt_response voor metadata extractie
119:                 from opschoning.opschoning_enhanced import analyze_gpt_response
120: 
121:                 # Extract metadata eerst (CPU-bound, run in thread)
122:                 gpt_metadata = await asyncio.to_thread(
123:                     analyze_gpt_response, original_text
124:                 )
125: 
126:                 # Pas opschoning toe (CPU-bound, run in thread)
127:                 cleaned_text = await asyncio.to_thread(
128:                     opschonen_enhanced,
129:                     original_text,
130:                     term,
131:                     True,  # handle_gpt_format=True
132:                 )
133: 
134:                 # Voeg GPT metadata toe aan applied_rules als het relevant is
135:                 if gpt_metadata.get("ontologische_categorie"):
136:                     applied_rules.append(
137:                         f"extracted_ontology_{gpt_metadata['ontologische_categorie']}"
138:                     )
139:             else:
140:                 # Gebruik ook enhanced voor consistentie, maar zonder GPT format handling
141:                 # CPU-bound, run in thread
142:                 cleaned_text = await asyncio.to_thread(
143:                     opschonen_enhanced,
144:                     original_text,
145:                     term,
146:                     False,  # handle_gpt_format=False
147:                 )
148: 
149:             # Analyseer welke wijzigingen zijn toegepast
150:             if original_text != cleaned_text:
151:                 applied_rules.extend(
152:                     self._analyze_changes(original_text, cleaned_text, term)
153:                 )
154:                 improvements.extend(
155:                     self._generate_improvements(original_text, cleaned_text)
156:                 )
157: 
158:             result = CleaningResult(
159:                 original_text=original_text,
160:                 cleaned_text=cleaned_text,
161:                 was_cleaned=original_text != cleaned_text,
162:                 applied_rules=tuple(applied_rules),  # frozen dataclass needs tuple
163:                 improvements=tuple(improvements),
164:                 metadata={
165:                     "timestamp": datetime.now(UTC).isoformat(),
166:                     "term": term,
167:                     "service_version": "1.0",
168:                 },
169:             )
170: 
171:             if self.config.log_operations and result.was_cleaned:
172:                 logger.debug(
173:                     f"Tekst opgeschoond: '{original_text[:50]}...' -> '{cleaned_text[:50]}...'"
174:                 )
175: 
176:             return result
177: 
178:         except Exception as e:
179:             logger.error(f"Fout bij opschoning van tekst: {e}")
180:             # Return origineel bij fout
181:             return CleaningResult(
182:                 original_text=original_text,
183:                 cleaned_text=original_text,
184:                 was_cleaned=False,
185:                 applied_rules=("error_occurred",),  # frozen dataclass needs tuple
186:                 metadata={"error": str(e)},
187:             )
188: 
```

## src/services/prompts/modules/json_based_rules_module.py:145–197

```text
145:             sections = []
146: 
147:             # Header: ### {emoji} {text}:
148:             sections.append(f"### {self.header_emoji} {self.header_text}:")
149: 
150:             # Load toetsregels on-demand from cached singleton
151:             from toetsregels.cached_manager import get_cached_toetsregel_manager
152: 
153:             manager = get_cached_toetsregel_manager()
154:             all_rules = manager.get_all_regels()
155: 
156:             # Filter alleen regels met dit prefix
157:             filtered_rules = {
158:                 k: v for k, v in all_rules.items() if k.startswith(self.rule_prefix)
159:             }
160: 
161:             # DEF-743: contextgebonden regels alleen tonen als er context is.
162:             has_context = self._has_any_context(context)
163:             rules_skipped = sorted(
164:                 k for k in filtered_rules if not has_context and _is_contextgebonden(k)
165:             )
166:             shown_rules = {
167:                 k: v for k, v in filtered_rules.items() if k not in rules_skipped
168:             }
169: 
170:             # Sorteer regels alfabetisch
171:             sorted_rules = sorted(shown_rules.items())
172: 
173:             # Format elke regel
174:             for regel_key, regel_data in sorted_rules:
175:                 sections.extend(self._format_rule(regel_key, regel_data))
176: 
177:             # Combineer alle secties
178:             content = "\n".join(sections)
179: 
180:             return ModuleOutput(
181:                 content=content,
182:                 metadata={
183:                     "rules_count": len(shown_rules),
184:                     "rules_skipped": rules_skipped,
185:                     "include_examples": self.include_examples,
186:                     "rule_prefix": self.rule_prefix,
187:                 },
188:             )
189: 
190:         except Exception as e:
191:             logger.error(
192:                 f"JSONBasedRulesModule '{self.module_id}' execution failed: {e}",
193:                 exc_info=True,
194:             )
195:             return ModuleOutput(
196:                 content="",
197:                 metadata={"error": str(e)},
```

## src/services/prompts/modules/json_based_rules_module.py:228–281

```text
228:     def _format_rule(self, regel_key: str, regel_data: dict) -> list[str]:
229:         """
230:         Formateer een regel uit JSON data naar markdown lines.
231: 
232:         Format (na DEF-126 + DEF-171):
233:         🔹 **REGEL-KEY - Naam**
234:         - Uitleg tekst
235:         - **Instructie:** imperatieve instructie (voor TOP 10 regels only)
236:           ✅ Goed voorbeeld
237:           ❌ Fout voorbeeld
238: 
239:         DEF-171: Toetsvraag patterns verwijderd (validation → ValidationOrchestratorV2)
240: 
241:         Args:
242:             regel_key: Regel identifier (bijv. "ARAI-01", "CON-02")
243:             regel_data: Regel data uit JSON met keys:
244:                 - naam: Regel naam
245:                 - uitleg: Uitleg tekst
246:                 - goede_voorbeelden: List van goede voorbeelden
247:                 - foute_voorbeelden: List van foute voorbeelden
248: 
249:         Returns:
250:             List van markdown lines voor deze regel
251:         """
252:         lines = []
253: 
254:         # Header met emoji: 🔹 **REGEL-KEY - Naam**
255:         naam = regel_data.get("naam", "Onbekende regel")
256:         lines.append(f"🔹 **{regel_key} - {naam}**")
257: 
258:         # Uitleg
259:         uitleg = regel_data.get("uitleg", "")
260:         if uitleg:
261:             lines.append(f"- {uitleg}")
262: 
263:         # DEF-126: Transform TOP 10 validation questions to instructions
264:         # DEF-171: Removed Toetsvraag fallback (validation handled by ValidationOrchestratorV2)
265:         instruction = self._get_instruction_for_rule(regel_key)
266:         if instruction:
267:             lines.append(f"- **Instructie:** {instruction}")
268: 
269:         # Voorbeelden (indien enabled in config)
270:         if self.include_examples:
271:             # Goede voorbeelden: ✅ tekst
272:             goede_voorbeelden = regel_data.get("goede_voorbeelden", [])
273:             for goed in goede_voorbeelden:
274:                 lines.append(f"  ✅ {goed}")
275: 
276:             # Foute voorbeelden: ❌ tekst
277:             foute_voorbeelden = regel_data.get("foute_voorbeelden", [])
278:             for fout in foute_voorbeelden:
279:                 lines.append(f"  ❌ {fout}")
280: 
281:         return lines
```

## src/services/prompts/modules/json_based_rules_module.py:374–380

```text
374:             "STR-09": "Gebruik 'of' ondubbelzinnig (maak duidelijk of het inclusief of exclusief is)",
375:             # INT rules (Integriteit)
376:             "INT-01": "Formuleer de definitie als één enkele, begrijpelijke zin",
377:             "INT-02": "Vermijd voorwaardelijke formuleringen zoals 'indien', 'mits', 'tenzij', 'alleen als'",
378:             "INT-03": "Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin",
379:             "INT-04": "Maak bepaalde lidwoorden ('de instelling', 'het systeem') expliciet door direct te specificeren welke bedoeld wordt",
380:             "INT-06": "Vermijd toelichtende formuleringen zoals 'bijvoorbeeld', 'zoals', 'dit houdt in', 'namelijk'",
```

## src/services/prompts/modular_prompt_adapter.py:104–117

```text
104:                         module_id="integrity_rules",
105:                         module_name="Integrity Validation Rules (INT)",
106:                         header_emoji="🔒",
107:                         header_text="Integriteit Regels (INT)",
108:                         priority=70,  # Same priority as before
109:                         # mode=ValidationMode.INSTRUCTION,  # ← OPTIONAL: Uncomment to enable compact mode
110:                     ),
111:                     JSONBasedRulesModule(
112:                         rule_prefix="SAM-",
113:                         module_id="sam_rules",
114:                         module_name="Coherence Validation Rules (SAM)",
115:                         header_emoji="🔗",
116:                         header_text="Samenhang Regels (SAM)",
117:                         priority=65,
```

## src/services/prompts/modules/integrity_rules_module.py:140–214

```text
140: 
141:         rules.append("")
142:         return rules
143: 
144:     def _build_int02_rule(self) -> list[str]:
145:         """Bouw INT-02 regel."""
146:         rules = []
147: 
148:         rules.append("🔹 **INT-02 - Vermijd beslisregels**")
149:         rules.append(
150:             "- Vermijd beslisregels of voorwaarden ('indien', 'mits', 'tenzij', 'alleen als')."
151:         )
152: 
153:         if self.include_examples:
154:             rules.append(
155:                 "  ✅ transitie-eis: eis die een organisatie ondersteunt om migratie van de huidige naar de toekomstige situatie mogelijk te maken"
156:             )
157:             rules.append(
158:                 "  ✅ Toegang: toestemming verleend door een bevoegde autoriteit om een systeem te gebruiken"
159:             )
160:             rules.append(
161:                 "  ✅ Beschikking: schriftelijk besluit genomen door een bevoegde autoriteit"
162:             )
163:             rules.append(
164:                 "  ✅ Register: officiële inschrijving in een openbaar register door een bevoegde instantie"
165:             )
166:             rules.append(
167:                 "  ❌ transitie-eis: eis die een organisatie moet ondersteunen om migratie van de huidige naar de toekomstige situatie mogelijk te maken"
168:             )
169:             rules.append(
170:                 "  ❌ Toegang: toestemming verleend door een bevoegde autoriteit, indien alle voorwaarden zijn vervuld"
171:             )
172:             rules.append(
173:                 "  ❌ Beschikking: schriftelijk besluit, mits de aanvraag compleet is ingediend"
174:             )
175:             rules.append(
176:                 "  ❌ Register: officiële inschrijving in een openbaar register, tenzij er bezwaar ligt"
177:             )
178: 
179:         rules.append("")
180:         return rules
181: 
182:     def _build_int03_rule(self) -> list[str]:
183:         """Bouw INT-03 regel."""
184:         rules = []
185: 
186:         rules.append("🔹 **INT-03 - Zorg voor duidelijke voornaamwoord-verwijzing**")
187:         rules.append(
188:             "- Zorg dat voornaamwoorden ('deze', 'dit', 'die') direct verwijzen naar een duidelijk antecedent in dezelfde zin."
189:         )
190: 
191:         if self.include_examples:
192:             rules.append(
193:                 "  ✅ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor die gebeurtenis volledig kan worden begrepen en geanalyseerd"
194:             )
195:             rules.append(
196:                 "  ✅ Voorwaarde: bepaling die aangeeft onder welke omstandigheden een handeling is toegestaan"
197:             )
198:             rules.append(
199:                 "  ❌ Geheel van omstandigheden die de omgeving van een gebeurtenis vormen en die de basis vormen waardoor het volledig kan worden begrepen en geanalyseerd"
200:             )
201:             rules.append(
202:                 "  ❌ Voorwaarde: bepaling die aangeeft onder welke omstandigheden deze geldt"
203:             )
204: 
205:         rules.append("")
206:         return rules
207: 
208:     def _build_int04_rule(self) -> list[str]:
209:         """Bouw INT-04 regel."""
210:         rules = []
211: 
212:         rules.append("🔹 **INT-04 - Maak lidwoord-verwijzingen expliciet**")
213:         rules.append(
214:             "- Maak bepaalde lidwoorden ('de instelling', 'het systeem') expliciet door te specificeren welke bedoeld wordt."
```

## src/services/validation/evaluators/judgment_review.py:62–84

```text
62: 
63:     evaluator_type = EvaluatorType.JUDGMENT_REVIEW
64: 
65:     def evaluate(
66:         self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
67:     ) -> EvaluationOutcome:
68:         code = record.rule_id.upper()
69:         signalen = self._signalen(record, ctx, deps)
70:         toetsvraag = str(record.get("toetsvraag") or record.get("naam") or "").strip()
71:         reden = toetsvraag or "Deze regel vereist een inhoudelijk oordeel."
72:         if code == "ESS-01":
73:             reden = self._ess01_reden(ctx, signalen)
74:         elif code == "ESS-02":
75:             reden = self._ess02_reden(ctx, signalen)
76:         elif code == "ESS-04":
77:             reden = self._ess04_reden(record, ctx, signalen)
78:         return EvaluationOutcome.review_required(reden, signals=signalen)
79: 
80:     @classmethod
81:     def _ess01_reden(cls, ctx: EvaluationContext, signalen: tuple[str, ...]) -> str:
82:         """A: citeer passages in het bestaande redenveld; geen inhoudelijk oordeel."""
83:         return cls._reden_met_passages(
84:             "ESS-01 — Nog te beoordelen: welke kenmerken bepalen de betekenis van "
```

## src/services/validation/evaluators/judgment_review.py:198–216

```text
198:     ) -> tuple[str, ...]:
199:         code = record.rule_id.upper()
200:         sleutel = f"__judgment__{code}"
201:         gecompileerd = deps.pattern_cache.get(sleutel)
202:         if gecompileerd is None:
203:             patronen = list(record.get("herkenbaar_patronen", []) or [])
204:             extra = get_additional_patterns(code)
205:             if extra:
206:                 patronen = list(dict.fromkeys([*patronen, *extra]))
207:             # Zie generic.py: compileerbaarheid is bij het laden afgedwongen;
208:             # een fout hier is een contractbreuk die naar de ERROR-grens moet
209:             # doorlopen in plaats van de signalen stil weg te laten (DEF-667).
210:             gecompileerd = [re.compile(p, re.IGNORECASE) for p in patronen]
211:             deps.pattern_cache[sleutel] = gecompileerd
212: 
213:         tekst = ctx.cleaned_text or ""
214:         return tuple(
215:             patroon.pattern for patroon in gecompileerd if patroon.search(tekst)
216:         )
```

## src/services/validation/modular_validation_service.py:876–922

```text
876: 
877:         # 2) Cleaning (optioneel, éénmaal)
878:         cleaned = text
879:         if self.cleaning_service is not None and hasattr(
880:             self.cleaning_service, "clean_text"
881:         ):
882:             try:
883:                 clean_result = self.cleaning_service.clean_text(text)
884:                 # clean_text kan sync of async zijn
885:                 if hasattr(clean_result, "__await__"):
886:                     clean_result = await clean_result  # type: ignore[func-returns-value]
887:                 # Ondersteun zowel string als object met cleaned_text attribuut
888:                 if isinstance(clean_result, str):
889:                     cleaned = clean_result
890:                 elif hasattr(clean_result, "cleaned_text"):
891:                     cleaned = clean_result.cleaned_text
892:             except (RuntimeError, TypeError, AttributeError, UnicodeError) as e:
893:                 # DEF-231: Bij cleaning-fout: ga verder met raw text (geen crash)
894:                 logger.warning(
895:                     f"Tekst cleaning gefaald, validatie met ruwe tekst: {type(e).__name__}: {e}",
896:                     extra={
897:                         "component": "modular_validation_service",
898:                         "operation": "text_cleaning",
899:                         "correlation_id": correlation_id,
900:                         "text_length": len(text) if text else 0,
901:                         "cleaning_service_type": type(self.cleaning_service).__name__,
902:                     },
903:                 )
904:                 cleaned = text
905: 
906:         # 3) Context opbouwen (tokens slechts op aanvraag; hier niet nodig)
907:         # DEF-244: begrip now passed via context instead of instance variable
908:         eval_ctx = EvaluationContext.from_params(
909:             text=text,
910:             cleaned=cleaned,
911:             begrip=begrip,  # DEF-244: Thread-safe begrip passing
912:             locale=(context or {}).get("locale") if isinstance(context, dict) else None,
913:             profile=(
914:                 (context or {}).get("profile") if isinstance(context, dict) else None
915:             ),
916:             correlation_id=correlation_id,
917:             tokens=(),
918:             metadata=dict(context or {}),
919:         )
920: 
921:         # DEF-251: Log validation start with begrip for observability
922:         # DEF-249 FIX: Deduplicate calculations (were computed twice before)
```

## src/services/validation/modular_validation_service.py:1430–1515

```text
1430:         """Resolveer de evaluator en bewaak de vereiste invoer.
1431: 
1432:         Fail-closed op drie manieren: ontbrekende vereiste invoer levert
1433:         `not_evaluated`, een onbekende evaluator of een fout tijdens uitvoeren
1434:         levert `error`. Geen van die uitkomsten telt als pass.
1435:         """
1436:         beschikbaar = self._available_inputs(ctx)
1437:         ontbrekend = missing_inputs(record, beschikbaar)
1438:         if ontbrekend:
1439:             namen = ", ".join(sorted(item.value for item in ontbrekend))
1440:             return EvaluationOutcome.not_evaluated(
1441:                 f"vereiste invoer ontbreekt: {namen}"
1442:             )
1443: 
1444:         deps = EvaluationDeps(
1445:             support=self,
1446:             available_inputs=beschikbaar,
1447:             repository=self._repository,
1448:             pattern_cache=state.pattern_cache,
1449:         )
1450:         try:
1451:             evaluator = self._registry.resolve(record.evaluator)
1452:             return evaluator.evaluate(record, ctx, deps)
1453:         except RuleContractError as exc:
1454:             logger.error(
1455:                 "Regel %s heeft geen uitvoerbare evaluator: %s",
1456:                 record.rule_id,
1457:                 exc,
1458:                 extra={
1459:                     "component": "modular_validation_service",
1460:                     "rule_id": record.rule_id,
1461:                     "correlation_id": ctx.correlation_id,
1462:                 },
1463:             )
1464:             return EvaluationOutcome(
1465:                 status=ResultStatus.ERROR, reason=f"contractfout: {exc}"
1466:             )
1467:         except Exception as exc:
1468:             logger.error(
1469:                 "Evaluator voor regel %s faalde: %s: %s",
1470:                 record.rule_id,
1471:                 type(exc).__name__,
1472:                 exc,
1473:                 extra={
1474:                     "component": "modular_validation_service",
1475:                     "rule_id": record.rule_id,
1476:                     "correlation_id": ctx.correlation_id,
1477:                 },
1478:             )
1479:             return EvaluationOutcome(
1480:                 status=ResultStatus.ERROR,
1481:                 reason=f"{type(exc).__name__}: {exc}",
1482:             )
1483: 
1484:     def _available_inputs(self, ctx: EvaluationContext) -> frozenset[RequiredInput]:
1485:         """Welke gedeclareerde invoer is voor deze validatie beschikbaar?
1486: 
1487:         Beschikbaarheid gaat over het bestaan van het invoerkanaal, niet over
1488:         de inhoud: een lege definitietekst is nog steeds een aangeleverde
1489:         tekst, anders zou VAL-EMP-001 zichzelf uitschakelen.
1490:         """
1491:         metadata = ctx.metadata or {}
1492:         beschikbaar: set[RequiredInput] = {RequiredInput.DEFINITION_TEXT}
1493:         if (ctx.begrip or "").strip():
1494:             beschikbaar.add(RequiredInput.TERM)
1495:         if any(
1496:             metadata.get(veld)
1497:             for veld in (
1498:                 "organisatorische_context",
1499:                 "juridische_context",
1500:                 "wettelijke_basis",
1501:             )
1502:         ):
1503:             beschikbaar.add(RequiredInput.CONTEXT_LISTS)
1504:         if self._repository is not None:
1505:             beschikbaar.add(RequiredInput.DEFINITION_REPOSITORY)
1506:         if metadata.get("synoniemen"):
1507:             beschikbaar.add(RequiredInput.SYNONYMS)
1508:         if metadata.get("voorkeursterm"):
1509:             beschikbaar.add(RequiredInput.PREFERRED_TERM)
1510:         if metadata.get("categorie") or metadata.get("ontologische_categorie"):
1511:             beschikbaar.add(RequiredInput.ONTOLOGICAL_CATEGORY)
1512:         if metadata.get("gerelateerde_begrippen"):
1513:             beschikbaar.add(RequiredInput.RELATED_CONCEPTS)
1514:         return frozenset(beschikbaar)
1515: 
```

## src/services/validation/modular_validation_service.py:1580–1640

```text
1580:         review_items: list[dict[str, Any]],
1581:         rule_results: dict[str, dict[str, Any]] | None = None,
1582:         geen_cijfer: bool = False,
1583:     ) -> None:
1584:         """Boek één regeluitkomst in score, violations en dekking.
1585: 
1586:         Kern van DEF-624: alleen `pass` en `fail` belanden in `rule_scores` en
1587:         wegen dus mee in de kwaliteitsscore. `review_required`,
1588:         `not_evaluated` en `error` vallen uit de noemer — ze worden nooit
1589:         stil als 1,0 meegeteld en verschijnen apart in de evaluatiedekking.
1590: 
1591:         DEF-622: een regel zonder cijfer (`geen_cijfer`) boekt nooit een
1592:         score, ook niet bij pass of fail; haar gestructureerde uitkomst
1593:         (`metadata["rule_result"]`) landt in `rule_results`. Een technische
1594:         fout op zo'n regel krijgt daar een apart herkenbaar foutonderdeel,
1595:         zonder interne details als normuitleg (B-08).
1596:         """
1597:         rule_statuses[code] = outcome.status.value
1598: 
1599:         if rule_results is not None and geen_cijfer:
1600:             self._boek_rule_result(code, outcome, rule_results)
1601: 
1602:         if outcome.status is ResultStatus.PASS:
1603:             if not geen_cijfer:
1604:                 rule_scores[code] = 1.0 if outcome.score is None else outcome.score
1605:             passed_rules.append(code)
1606:             return
1607: 
1608:         if outcome.status is ResultStatus.FAIL:
1609:             score, violation = self._outcome_naar_violation(code, ctx, outcome, state)
1610:             if not geen_cijfer:
1611:                 rule_scores[code] = score
1612:             if violation is not None:
1613:                 violations.append(violation)
1614:             else:
1615:                 passed_rules.append(code)
1616:             return
1617: 
1618:         if outcome.status is ResultStatus.REVIEW_REQUIRED:
1619:             review_items.append(
1620:                 {
1621:                     "rule_id": code,
1622:                     "category": category_for_rule(code),
1623:                     "reason": outcome.reason or "",
1624:                     "signals": list(outcome.metadata.get("signals", [])),
1625:                 }
1626:             )
1627:             return
1628: 
1629:         if outcome.status is ResultStatus.NOT_APPLICABLE:
1630:             # DEF-766: een afgeronde, gemotiveerde niet-toepasselijkheid. Geen
1631:             # score, geen violation, geen reviewpunt en géén passed_rule: zij
1632:             # is zichtbaar via `rule_statuses`, de dekking en — voor een regel
1633:             # zonder cijfer — het gestructureerde `rule_results`-blok.
1634:             return
1635: 
1636:         if outcome.status is ResultStatus.ERROR:
1637:             logger.warning(
1638:                 "Regel %s leverde een evaluatorfout: %s",
1639:                 code,
1640:                 outcome.reason,
```

## src/services/validation/result_contract.py:49–68

```text
49: #: Contractvelden die een conversie doordraagt wanneer de bron ze werkelijk
50: #: draagt (DEF-624, AC 2): (veld, geldig type of None voor "elke waarde",
51: #: nullable). `validation_status` reist ruw mee, ook als hij ongeldig is:
52: #: `met_expliciete_runstatus` bepaalt daarna zelf ontbrekend/ongeldig en
53: #: vervangt hem door de canonieke waarde. `source_assessment` is nullable:
54: #: een expliciete None is de vastlegging "geen bronbeoordeling" en mag niet
55: #: verdwijnen; ontbreekt het veld, dan wordt het niet verzonnen.
56: CONTRACTVELDEN: tuple[tuple[str, type | None, bool], ...] = (
57:     ("validation_status", None, False),
58:     ("unknown_reason", str, False),
59:     ("validation_readiness", dict, False),
60:     ("rule_statuses", dict, False),
61:     ("rule_results", dict, False),
62:     ("review_required", list, False),
63:     ("evaluation_coverage", dict, False),
64:     ("source_assessment", dict, True),
65:     ("acceptance_gate", dict, False),
66: )
67: 
68: #: De contractuele redenen; een andere waarde in `unknown_reason` telt niet
```

## src/services/orchestrators/validation_orchestrator_v2.py:121–149

```text
121: 
122:     Afhankelijkheden worden via de constructor geïnjecteerd. De orchestrator
123:     zelf bevat geen businessregels; die leven in de onderliggende service/validator.
124: 
125:     Story 2.2: Core Implementation
126:     - Concrete implementatie van ValidationOrchestratorInterface
127:     - Dunne orchestration laag bovenop bestaande services
128:     - Sequentiële batch processing (parallelisme in latere story)
129:     - Geen cleaning tijdens toetsen; constructorparameter behouden voor compatibiliteit
130:     """
131: 
132:     def __init__(
133:         self,
134:         validation_service: ValidationServiceInterface,
135:         cleaning_service: CleaningServiceInterface | None = None,
136:         source_assessment_service: Any | None = None,
137:         ess03_assessment_service: Any | None = None,
138:     ) -> None:
139:         if validation_service is None:
140:             msg = "validation_service is vereist"
141:             raise ValueError(msg)
142:         self.validation_service = validation_service
143:         self.cleaning_service = cleaning_service
144:         # DEF-743: de AI-bronbeoordeling (CON-02) is standaard onderdeel van
145:         # elke validatie met bronnen; deze wrapper verkrijgt haar zelf.
146:         self.source_assessment_service = source_assessment_service
147:         # DEF-766: de AI-telbaarheidsbeoordeling (ESS-03) is standaard
148:         # onderdeel van elke validatie met term en tekst; idem.
149:         self.ess03_assessment_service = ess03_assessment_service
```

## src/services/orchestrators/validation_orchestrator_v2.py:150–197

```text
150: 
151:     async def validate_text(
152:         self,
153:         begrip: str,
154:         text: str,
155:         ontologische_categorie: str | None = None,
156:         context: ValidationContext | None = None,
157:     ) -> ValidationResult:
158:         """Valideer exact de aangeleverde tekst zonder opschoning.
159: 
160:         Args:
161:             begrip: Het begrip waarvoor de tekst wordt gevalideerd
162:             text: Te valideren tekst (mag leeg zijn)
163:             ontologische_categorie: Optionele categorie voor contextuele regels
164:             context: Optionele validatiecontext
165: 
166:         Returns:
167:             ValidationResult: Schema-conform resultaat
168:         """
169:         # Extract correlation ID from context
170:         correlation_id = (
171:             str(context.correlation_id)
172:             if context and context.correlation_id
173:             else str(uuid.uuid4())
174:         )
175: 
176:         # DEF-198: Clean architecture - import from utils/, callback registered by UI
177:         from utils.progress_callback import operation_progress
178: 
179:         with operation_progress("validating_definition"):
180:             try:
181:                 # DEF-747/624: uitsluitend toetsen gebruikt exact de invoer.
182:                 # Cleaning hoort bij een expliciete generatie-/voorstelstap.
183:                 # Geen verrijking met 'definition' hier: die is in validate_text
184:                 # niet beschikbaar. Context (incl. de drie lijsten) komt via
185:                 # ValidationContext.metadata.
186:                 # DEF-622: CON-01 bindt bewijs en beoordeling aan de exacte
187:                 # invoertekst — onvoorwaardelijk uit het `text`-argument, ook
188:                 # zonder cleaning en ongeacht wat een aanroeper in metadata
189:                 # onder `record_text` meegeeft. Anders kon een aanroeper de
190:                 # binding spoofen en een oude beoordeling laten gelden voor
191:                 # een nieuwe tekst (reviewbevinding R3).
192:                 context_dict = dict(self._context_dict(context) or {})
193:                 context_dict["record_text"] = text
194:                 # DEF-766: het afzonderlijke categorieargument is de expliciete
195:                 # betekenisclaim van deze toetsing en hoort in dezelfde context
196:                 # als de recordroute die zet. Zonder dit bereikte een gewijzigde
197:                 # categorie de beoordelaar noch de vingerafdruk, en leverde een
```

## src/services/orchestrators/definition_orchestrator_v2.py:1147–1238

```text
1147:                 logger.warning(
1148:                     f"Generation {generation_id}: Voorbeelden generation failed: {type(e).__name__}: {e}",
1149:                     exc_info=True,
1150:                 )
1151:                 if DEBUG_ENABLED and "debug_gen_id" in locals():
1152:                     debugger.log_error(debug_gen_id, "C", e)
1153:                 # Continue without voorbeelden
1154: 
1155:             # =====================================
1156:             # PHASE 6: Text Cleaning & Normalization
1157:             # =====================================
1158:             # V2 cleaning service (always available through adapter)
1159:             raw_gpt_output = (
1160:                 generation_result.text
1161:                 if hasattr(generation_result, "text")
1162:                 else str(generation_result)
1163:             )
1164:             cleaning_result = await self.cleaning_service.clean_text(
1165:                 raw_gpt_output,
1166:                 sanitized_request.begrip,
1167:             )
1168:             cleaned_text = cleaning_result.cleaned_text
1169: 
1170:             # Extract clean definition for "origineel" display
1171:             # Uses full cleaning to remove ALL unwanted patterns:
1172:             # - "Ontologische categorie:" metadata header
1173:             # - "[term]:" prefix (e.g., "Vervoersverbod:")
1174:             # - Forbidden words, circular definitions, etc.
1175:             from opschoning.opschoning_enhanced import (
1176:                 extract_definition_from_gpt_response,
1177:                 opschonen_enhanced,
1178:             )
1179: 
1180:             definitie_zonder_header = opschonen_enhanced(
1181:                 raw_gpt_output, sanitized_request.begrip, handle_gpt_format=True
1182:             )
1183:             # DEF-622 (besluit tekstvergelijking): de echte definitiekern vóór
1184:             # nabewerking — alleen de GPT-kop eraf, niets opgeschoond. Het al
1185:             # opgeschoonde `definitie_origineel` hierboven is géén vóórtekst.
1186:             definitie_kern_geextraheerd = extract_definition_from_gpt_response(
1187:                 raw_gpt_output
1188:             )
1189: 
1190:             logger.info(f"Generation {generation_id}: Text cleaned with V2 service")
1191: 
1192:             # =====================================
1193:             # PHASE 6: Validation
1194:             # =====================================
1195:             # Tolerant correlation_id: als generation_id geen geldige UUID is, genereer er één
1196:             try:
1197:                 corr = uuid.UUID(generation_id)
1198:             except ValueError:
1199:                 # DEF-229: UUID.parse only raises ValueError for invalid strings
1200:                 corr = uuid.uuid4()
1201:             # Voeg opties toe aan metadata zodat validator context flags kan lezen
1202:             meta: dict[str, Any] = {"generation_id": generation_id}
1203:             try:
1204:                 if sanitized_request.options:
1205:                     # Expliciet doorgeven van force_duplicate voor duplicate-escalatie
1206:                     if bool(
1207:                         safe_dict_get(
1208:                             sanitized_request.options, "force_duplicate", False
1209:                         )
1210:                     ):
1211:                         meta["force_duplicate"] = True
1212:                     # Bewaar volledige options voor toekomstig gebruik (niet verplicht)
1213:                     meta["options"] = dict(sanitized_request.options)
1214:             except (TypeError, AttributeError) as e:
1215:                 # DEF-229: Log options extraction failures
1216:                 logger.debug(f"Could not extract generation options for metadata: {e}")
1217:             # DEF-743: dezelfde bronset (gekoppeld aan de kwitantie) gaat
1218:             # naar de validatie; de wrapper verkrijgt daar de bronbeoordeling
1219:             # voor exact de getoetste kandidaat en geeft haar terug.
1220:             bronmeta = {
1221:                 "provenance_sources": deepcopy(provenance_sources),
1222:                 "source_receipt": deepcopy(source_receipt),
1223:                 "source_review": None,
1224:                 "peildatum": peildatum,
1225:                 # DEF-766 (R4): de door de gebruiker opgegeven bedoeling
1226:                 # (DEF-751) hoort bij de ESS-03-beoordeling van de kandidaat.
1227:                 "betekenisverduidelijking": (
1228:                     sanitized_request.betekenisverduidelijking or None
1229:                 ),
1230:             }
1231:             validation_context = ValidationContext(
1232:                 correlation_id=corr,
1233:                 metadata={**meta, **bronmeta},
1234:             )
1235:             # DEF-622: de getoetste kandidaat is exact de kandidaat die wordt
1236:             # getoond en opgeslagen. De validatie-orchestrator schoont een
1237:             # Definition in-place; daarom gaat een kopie mee en wordt, als de
1238:             # validatie de tekst tóch wijzigt, die tekst de kandidaat en
```

## src/services/orchestrators/definition_orchestrator_v2.py:1850–1910

```text
1850: 
1851:         DEF-622/747: uitsluitend toetsen wijzigt het Definition-object niet.
1852:         De mutatieguard blijft als vangnet: wijzigt de validatie toch de tekst,
1853:         dan is dát de
1854:         kandidaat die getoond en opgeslagen wordt, en die wordt opnieuw
1855:         getoetst (wijziging na toetsing vereist hertoetsing). Zo is de
1856:         opgeslagen tekst altijd exact de getoetste tekst.
1857: 
1858:         DEF-743: de bronset uit `validation_context.metadata` gaat elke
1859:         poging ongewijzigd mee; de wrapper verkrijgt per kandidaattekst een
1860:         eigen bronbeoordeling en geeft haar terug in
1861:         `raw_validation["source_assessment"]` — die hoort dus altijd bij
1862:         exact de definitieve tekst.
1863: 
1864:         DEF-766 (R1): de kandidaat draagt zelf de bedoelde betekenis mee, in
1865:         dezelfde vorm als het record dat straks wordt opgeslagen.
1866:         """
1867:         kandidaat = tekst
1868:         raw_validation: Any = None
1869:         for poging in (1, 2):
1870:             kopie = Definition(
1871:                 begrip=request.begrip,
1872:                 definitie=kandidaat,
1873:                 organisatorische_context=request.organisatorische_context or [],
1874:                 juridische_context=request.juridische_context or [],
1875:                 wettelijke_basis=request.wettelijke_basis or [],
1876:                 ontologische_categorie=request.ontologische_categorie,
1877:                 created_by=request.actor,
1878:                 metadata=self._kandidaatregistratie(request),
1879:             )
1880:             raw_validation = await self.validation_service.validate_definition(
1881:                 definition=kopie, context=validation_context
1882:             )
1883:             if kopie.definitie == kandidaat:
1884:                 return (
1885:                     kandidaat,
1886:                     raw_validation,
1887:                     self._bronbeoordeling_uit(raw_validation),
1888:                 )
1889:             if poging == 2:
1890:                 # Aanhoudende mutatie: het oordeel hoort bij een andere tekst
1891:                 # dan de kandidaat. Fail-closed — geen oordeel koppelen aan een
1892:                 # tekst die niet exact getoetst is, en niets opslaan.
1893:                 raise KandidaatNietStabielError(
1894:                     "de nabewerking in de validatie blijft de kandidaattekst "
1895:                     "wijzigen; de definitie is niet stabiel te toetsen en wordt "
1896:                     "niet opgeslagen"
1897:                 )
1898:             logger.info(
1899:                 f"Generation {generation_id}: validatie wijzigde de kandidaattekst; "
1900:                 "hertoetsing op de definitieve tekst"
1901:             )
1902:             kandidaat = kopie.definitie
1903:         return (
1904:             kandidaat,
1905:             raw_validation,
1906:             None,
1907:         )  # pragma: no cover - lus eindigt altijd eerder
1908: 
1909:     @staticmethod
1910:     def _kandidaatregistratie(request: GenerationRequest) -> dict[str, Any]:
```

## src/services/orchestrators/definition_orchestrator_v2.py:1974–2005

```text
1974: 
1975:     @staticmethod
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
2001:             overtredingen.append(overtreding)
2002:         return overtredingen
2003: 
2004:     def _create_definition_object(
2005:         self,
```

## src/services/orchestrators/definition_orchestrator_v2.py:2020–2065

```text
2020:             ensure_dict(request.options or {}).get("category_choice")
2021:         )
2022:         if keuze_invoer is not None:
2023:             metadata["category_choice_input"] = keuze_invoer
2024:         return Definition(
2025:             begrip=request.begrip,
2026:             definitie=text,
2027:             organisatorische_context=request.organisatorische_context or [],
2028:             juridische_context=request.juridische_context or [],
2029:             wettelijke_basis=request.wettelijke_basis or [],
2030:             # EPIC-010: domein field verwijderd
2031:             ontologische_categorie=request.ontologische_categorie,  # V2: Properly set
2032:             categorie=request.ontologische_categorie,  # DEF-53 fix: explicit mapping to DB field
2033:             ufo_categorie=getattr(request, "ufo_categorie", None),
2034:             valid=safe_dict_get(validation_result, "is_acceptable", False),
2035:             validation_violations=ensure_list(
2036:                 safe_dict_get(validation_result, "violations", [])
2037:             ),
2038:             metadata=metadata,
2039:             created_by=request.actor,
2040:             created_at=datetime.now(UTC),
2041:         )
2042: 
2043:     async def _safe_save_definition(self, definition: Definition) -> int | None:
2044:         """
2045:         Safely save definition with comprehensive error handling.
2046: 
2047:         Returns:
2048:             Definition ID if successful, None if repository doesn't support save
2049: 
2050:         Raises:
2051:             DuplicateDefinitionError: If definition already exists
2052:             DatabaseConstraintError: If database constraints violated
2053:             DatabaseConnectionError: If database unavailable
2054:             RepositoryError: For other repository errors
2055:         """
2056:         # Check if repository supports save
2057:         if not hasattr(self.repository, "save"):
2058:             logger.error(
2059:                 f"Repository {type(self.repository).__name__} does not have save() method! "
2060:                 f"Available methods: {[m for m in dir(self.repository) if not m.startswith('_')]}"
2061:             )
2062:             return None
2063: 
2064:         # Log save attempt
2065:         logger.info(
```

## src/ui/components/validation_view.py:237–315

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
264: 
265: 
266: def _build_detailed_assessment(validation_result: dict) -> list[str]:
267:     """Build a mixed list of summary, violations and passed rules lines."""
268:     violations = list(validation_result.get("violations") or [])
269:     passed_rules = list(validation_result.get("passed_rules") or [])
270:     stats = _calculate_validation_stats(violations, passed_rules)
271: 
272:     def _severity_emoji(sev: str) -> str:
273:         s = (sev or "").lower()
274:         if s in {"critical", "error", "high"}:
275:             return "❌"
276:         if s in {"warning", "medium", "low"}:
277:             return "⚠️"
278:         return "📋"
279: 
280:     lines: list[str] = []
281:     # Summary first: de dekking, geen 'x/y geslaagd (z%)' (DEF-743, besluit 3).
282:     lines.append(dekkingsregel(bereken_beoordelingsdekking(validation_result)))
283: 
284:     # Violations (sorted)
285:     def _v_key(v: dict[str, Any]) -> tuple[int, int]:
286:         rid = str(v.get("rule_id") or v.get("code") or "")
287:         return _rule_sort_key(rid)
288: 
289:     for v in sorted(violations, key=_v_key):
290:         rid = str(v.get("rule_id") or v.get("code") or "")
291:         sev = str(v.get("severity", "warning")).lower()
292:         desc = v.get("description") or v.get("message") or ""
293:         suggestion = v.get("suggestion")
294:         if suggestion:
295:             desc = f"{desc} · Wat verbeteren: {suggestion}"
296:         emoji = _severity_emoji(sev)
297:         name, explanation = _get_rule_info(rid)
298:         name_part = f" — {name}" if name else ""
299:         expl_labeled = (
300:             f" · Wat toetst: {explanation}" if explanation else " · Wat toetst: —"
301:         )
302:         lines.append(
303:             f"{emoji} {rid}{name_part}: Waarom niet geslaagd: {desc}{expl_labeled}"
304:         )
305: 
306:     # Passed rules (sorted)
307:     for rid in sorted(stats["passed_ids"], key=_rule_sort_key):
308:         name, explanation = _get_rule_info(rid)
309:         name_part = f" — {name}" if name else ""
310:         wat_toetst = f"Wat toetst: {explanation}" if explanation else "Wat toetst: —"
311:         lines.append(f"✅ {rid}{name_part}: OK · {wat_toetst}")
312: 
313:     return lines
314: 
315: 
```

## src/ui/components/validation_view.py:794–879

```text
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
809: 
810:     # Toggle + details
811:     details_key = f"{key_prefix}_show_validation_details"
812:     if show_toggle and st.button(
813:         "📊 Toon/verberg gedetailleerde toetsresultaten", key=f"btn_{details_key}"
814:     ):
815:         current_state = SessionStateManager.get_value(details_key, False)
816:         SessionStateManager.set_value(details_key, not current_state)
817: 
818:     # Default to expanded on first render after validation
819:     if show_toggle and SessionStateManager.get_value(details_key, None) is None:
820:         SessionStateManager.set_value(details_key, True)
821: 
822:     show_details = (
823:         SessionStateManager.get_value(details_key, False) if show_toggle else True
824:     )
825:     if not show_details:
826:         return
827: 
828:     # Summary (blue info bar) + detailed assessment. De samenvatting is de
829:     # dekking (tellingen per status), geen 'x/y geslaagd (z%)' — een
830:     # percentage is een vervangende deelscore (DEF-743, besluit 3). De stats
831:     # blijven de bron van de gefaalde/geslaagde regelcodes hieronder.
832:     _calculate_validation_stats(
833:         list(validation_result.get("violations") or []),
834:         list(validation_result.get("passed_rules") or []),
835:     )
836:     st.info(dekkingsregel(dekking))
837: 
838:     lines = _build_detailed_assessment(validation_result)
839:     # Filter out the summary line if present (we render a styled summary above)
840:     lines = [ln for ln in lines if not ln.startswith("📋 **Beoordelingsdekking**")]
841:     # Regels die open, mislukt of niet gedraaid zijn horen zichtbaar te
842:     # blijven; regels met gestructureerde uitkomst staan al hierboven.
843:     lines.extend(
844:         _statuslijst_regels(
845:             validation_result,
846:             uitgesloten={
847:                 str(code)
848:                 for code, detail in (
849:                     validation_result.get("rule_results") or {}
850:                 ).items()
851:                 if isinstance(detail, dict)
852:             },
853:         )
854:     )
855:     if not lines:
856:         st.warning("⚠️ Geen gedetailleerde toetsresultaten beschikbaar.")
857:         return
858: 
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

## src/ui/components/expert_review_tab.py:1069–1125

```text
1069:         )
1070: 
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
1092:         apart. Geeft (payload zonder algemene velden, ontbrekende invoer)."""
1093:         onvolledig: list[str] = []
1094:         onderdeel = st.selectbox(
1095:             "Onderdeel",
1096:             options=list(onderdelen),
1097:             format_func=lambda o: self._ONDERDEELLABEL.get(o, o),
1098:             key=f"{sleutel}_corr_onderdeel",
1099:         )
1100:         origineel = next((p for p in uitkomst.parts if p.id == onderdeel), None)
1101:         if origineel is not None:
1102:             st.info(
1103:                 f"Oorspronkelijk oordeel over {self._ONDERDEELLABEL.get(onderdeel, onderdeel)}"
1104:                 f" ({'AI' if origineel.field == 'source_assessment' else origineel.field or 'geen basis'}):"
1105:                 f" {self._CORRECTIESTATUS.get(origineel.status, origineel.status)} — "
1106:                 f"{origineel.reason}"
1107:             )
1108:         status = st.selectbox(
1109:             "Deskundig oordeel over dit onderdeel",
1110:             options=list(self._CORRECTIESTATUS),
1111:             format_func=lambda o: self._CORRECTIESTATUS[o],
1112:             key=f"{sleutel}_corr_status",
1113:         )
1114:         bronnen = list(canoniek)
1115:         if not bronnen:
1116:             st.warning(
1117:                 "Geen opgeslagen bronnen: een correctie met bewijs is niet mogelijk; "
1118:                 "alleen 'nog te beoordelen' met motivering."
1119:             )
1120:         keuze = st.selectbox(
1121:             "Bron van het bewijs (stabiel id uit de opgeslagen bronset)",
1122:             options=[b.source_id for b in bronnen],
1123:             format_func=lambda sid: next(
1124:                 (
1125:                     f"{b.source_id} · {b.title or '(zonder titel)'} · versie "
```

## src/services/definition_workflow_service.py:715–835

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
```

## src/services/definition_import_service.py:52–122

```text
52: 
53: class DefinitionImportService:
54:     """Service voor enkelvoudige import (MVP)."""
55: 
56:     def __init__(self, repository: Any, validation_orchestrator: Any) -> None:
57:         """
58:         Args:
59:             repository: DefinitionRepository service
60:             validation_orchestrator: ValidationOrchestratorV2 instance
61:         """
62:         self._repo = repository
63:         self._validator = validation_orchestrator
64:         # Thread pool voor sync database operaties
65:         self._executor = ThreadPoolExecutor(max_workers=2)
66: 
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
116:                 definition_id=None,
117:                 validation=None,
118:                 duplicates=[],
119:                 error="Validatie timeout - probeer opnieuw",
120:             )
121:         except RepositoryError:
122:             # DEF-469: duplicaatcontrole faalde (DB-fout). Fail-closed: NIET
```

## src/ui/components/tabs/import_export_beheer/csv_importer.py:245–276

```text
245:                 # Check duplicaat
246:                 if skip_duplicates:
247:                     # DEF-439: DB-laag DefinitieRepository heet find_definitie
248:                     # (begrip + organisatorische_context), niet find_by_begrip.
249:                     existing = self.repository.find_definitie(begrip, context)
250:                     if existing:
251:                         skipped += 1
252:                         continue
253: 
254:                 # Maak record (DEF-751: leeg = NULL, geen label)
255:                 record = DefinitieRecord(
256:                     begrip=begrip,
257:                     definitie=definitie,
258:                     categorie=categorie or None,
259:                     organisatorische_context=context,
260:                     status=_STATUS_DRAFT,
261:                     validation_score=0.0,
262:                 )
263: 
264:                 # Save (DEF-439: DB-laag heet create_definitie, niet save).
265:                 # DEF-751 B2: herkomst `import` — de persistentielaag bouwt
266:                 # het keuze-event (nooit met actor).
267:                 self.repository.create_definitie(
268:                     record, categoriekeuze={"origin": HERKOMST_IMPORT}
269:                 )
270:                 imported += 1
271: 
272:                 # Auto validatie indien gewenst
273:                 if auto_validate:
274:                     # Auto-validatie wordt in een aparte story geïmplementeerd
275:                     pass
276: 
```

## src/services/definition_edit_service.py:700–733

```text
700: 
701:             # Apply updates
702:             updated_definition = self._apply_updates(current, updates)
703: 
704:             # DEF-809: de sessiebeoordeling als actueel bewijs, uitsluitend bij
705:             # exacte binding aan de kandidaat die nu wordt opgeslagen.
706:             beoordeling_bewaard, beoordeling_reden = _neem_sessiebeoordeling_op(
707:                 source_assessment, updated_definition, current.metadata
708:             )
709:             # DEF-766: idem voor de ESS-03-beoordeling van de laatste toetsing.
710:             ess03_bewaard, ess03_reden = _neem_ess03_beoordeling_op(
711:                 ess03_assessment, updated_definition, ess03_binding
712:             )
713: 
714:             # Validate if requested
715:             validation_results = None
716:             if validate and self.validation_service:
717:                 validation_results = self._validate_definition(updated_definition)
718:                 if validation_results and not validation_results.get("valid", True):
719:                     # Still save but mark validation issues
720:                     if not updated_definition.metadata:
721:                         updated_definition.metadata = {}
722:                     updated_definition.metadata["validation_issues"] = (
723:                         validation_results.get("issues", [])
724:                     )
725: 
726:             # Save with history (DEF-751: mét keuze via het expliciete commando)
727:             saved_id = self.repository.save_with_history(
728:                 updated_definition,
729:                 wijziging_reden=reason,
730:                 gewijzigd_door=user,
731:                 categoriekeuze=categoriekeuze,
732:             )
733: 
```

## src/services/definition_edit_service.py:1074–1150

```text
1074:     def _validate_definition(
1075:         self,
1076:         definition: Definition,
1077:         geladen_metadata: Mapping[str, Any] | None = None,
1078:     ) -> dict[str, Any] | None:
1079:         """Validate definition using injected validation service (sync only).
1080: 
1081:         Async validation is not executed here. If only an async API is available,
1082:         return None and let the UI call validation via async_bridge.
1083: 
1084:         DEF-743: de kandidaat is de ACTUELE bewerkte tekst/term/drie contexten;
1085:         `geladen_metadata` (het ID-only geladen record) levert dezelfde
1086:         bronset, recordversie en vastgelegde beoordelingen als het async pad
1087:         (`bouw_validatiecontext`). Zonder `geladen_metadata` wordt
1088:         `definition.metadata` gebruikt (een via de repository geladen record
1089:         draagt die sleutels zelf).
1090:         """
1091:         if not self.validation_service:
1092:             return None
1093: 
1094:         try:
1095:             import inspect
1096: 
1097:             vs = self.validation_service
1098: 
1099:             # Eén contextdict voor sync én async (pariteit): bewerkte lijsten
1100:             # altijd expliciet (ook leeg), bronset/versie/beoordeling uit het
1101:             # geladen record.
1102:             context_dict: dict[str, Any] = bouw_validatiecontext(
1103:                 definition,
1104:                 (
1105:                     geladen_metadata
1106:                     if geladen_metadata is not None
1107:                     else (definition.metadata or {})
1108:                 ),
1109:             )
1110: 
1111:             if hasattr(vs, "validate_text"):
1112:                 fn = vs.validate_text
1113:                 # Sla async API over (UI moet async_bridge gebruiken)
1114:                 if inspect.iscoroutinefunction(fn):
1115:                     return None
1116:                 results = fn(
1117:                     begrip=definition.begrip,
1118:                     text=definition.definitie,
1119:                     ontologische_categorie=getattr(
1120:                         definition, "ontologische_categorie", None
1121:                     )
1122:                     or definition.categorie,
1123:                     context=context_dict,
1124:                 )
1125:             else:
1126:                 # Try generic validate_definition
1127:                 try:
1128:                     fn = vs.validate_definition
1129:                 except AttributeError:
1130:                     fn = getattr(vs, "validate", None)
1131:                 if fn is None:
1132:                     return None
1133:                 if inspect.iscoroutinefunction(fn):
1134:                     return None
1135:                 # Support both signatures
1136:                 try:
1137:                     results = fn(definition)
1138:                 except TypeError:
1139:                     results = fn(
1140:                         begrip=definition.begrip,
1141:                         text=definition.definitie,
1142:                         ontologische_categorie=getattr(
1143:                             definition, "ontologische_categorie", None
1144:                         )
1145:                         or definition.categorie,
1146:                         context=context_dict,
1147:                     )
1148: 
1149:             # Normalize result to UI format
1150:             # Case 1: dict schema (ModularValidationService/Orchestrator ensure_schema)
```

## src/services/export_service.py:400–472

```text
400:         msg = f"Export formaat {format} nog niet geïmplementeerd"
401:         raise NotImplementedError(msg)
402: 
403:     async def export_definitie_async(
404:         self,
405:         definitie_id: int | None = None,
406:         definitie_record: DefinitieRecord | None = None,
407:         additional_data: dict[str, Any] | None = None,
408:         format: ExportFormat = ExportFormat.TXT,
409:     ) -> str:
410:         """Asynchrone export met optionele validatiegate."""
411:         # DEF-622 (K2): één recordlezing — dezelfde snapshot voor aggregatie,
412:         # validatie én uitvoer. Een tweede lezing kon een tussentijds gewijzigd
413:         # record toetsen terwijl de export de eerdere versie bevatte.
414:         record = definitie_record
415:         if record is None and definitie_id is not None:
416:             record = self.repository.get_definitie(definitie_id)
417:             if record is None:
418:                 msg = f"Definitie met ID {definitie_id} niet gevonden"
419:                 raise ValueError(msg)
420:         export_data = self.data_aggregation_service.aggregate_definitie_for_export(
421:             definitie_id=definitie_id,
422:             definitie_record=record,
423:             additional_data=additional_data,
424:         )
425:         # Optionele async validatiegate
426:         if self.enable_validation_gate and self.validation_orchestrator is not None:
427:             # DEF-622 (K2): de gate oordeelt op het opgeslagen record. De
428:             # contractvelden (drie contextlijsten, id, recordversie en de
429:             # vastgelegde CON-01-beoordeling) komen uitsluitend van het record;
430:             # de aggregatie borgt dezelfde velden in de uitvoer, zodat
431:             # validator en export exact dezelfde gegevens gebruiken.
432:             # Tekstbasis (K4): de definitiezin — van het record, of van een
433:             # expliciet meegegeven aangepaste tekst (door de aggregatie op
434:             # dezelfde conventie gesplitst; een andere zin laat een beoordeling
435:             # via de vingerafdruk vervallen). Of de gate daarna slaagt
436:             # (totaalscore, algemene exportvoorwaarden) blijft DEF-630.
437:             from services.validation.interfaces import ValidationContext
438: 
439:             if record is None:
440:                 msg = "Validatie vóór export vereist een opgeslagen definitie"
441:                 raise ValueError(msg)
442:             text_for_validation = (
443:                 export_data.definitie_aangepast or record.get_definitie_tekst()
444:             )
445:             metadata: dict[str, Any] = record.get_contractvelden()
446:             try:
447:                 result = await self.validation_orchestrator.validate_text(
448:                     begrip=record.begrip,
449:                     text=text_for_validation,
450:                     ontologische_categorie=None,
451:                     context=ValidationContext(metadata=metadata),
452:                 )
453:             except Exception as e:  # pragma: no cover - defensive
454:                 msg = f"Validatie mislukt vóór export: {e!s}"
455:                 raise ValueError(msg) from e
456:             # DEF-624: alleen een uitgevoerde run (`validated`) kan de gate
457:             # openen; een resultaat zonder geldige status is geen runbewijs,
458:             # ongeacht `is_acceptable`. Welke voorwaarden de gate verder
459:             # stelt blijft DEF-630.
460:             from services.validation.result_contract import is_uitgevoerde_run
461: 
462:             if (
463:                 not isinstance(result, dict)
464:                 or not is_uitgevoerde_run(result)
465:                 or not result.get("is_acceptable", False)
466:             ):
467:                 msg = "Export geblokkeerd: definitie niet acceptabel volgens validatiegate"
468:                 raise ValueError(msg)
469: 
470:         # Export uitvoeren
471:         if format == ExportFormat.TXT:
472:             return self._export_to_txt(export_data)
```

## src/database/models.py:137–165

```text
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
163: 
164: 
165: #: De tekststadia van de kandidaat die het bewijs zelfstandig meedraagt
```

## src/services/definition_generator_enhancement.py:235–286

```text
235: class CompletenessEnhancer(EnhancementStrategy):
236:     """Enhancement voor volledigheid van definities."""
237: 
238:     def __init__(self) -> None:
239:         # Aspecten die vaak missen in definities
240:         self.completeness_aspects = {
241:             "doel": ["doel", "bedoeling", "functie", "nut"],
242:             "scope": ["omvang", "bereik", "toepassingsgebied"],
243:             "voorwaarden": ["voorwaarde", "vereiste", "criteria"],
244:             "proces": ["stap", "procedure", "methode", "proces"],
245:             "verantwoordelijk": ["verantwoordelijk", "bevoegd", "eigenaar"],
246:         }
247: 
248:     def enhance(self, definition: Definition) -> list[EnhancementResult]:
249:         """Verbeter volledigheid van definitie."""
250:         results = []
251:         text = definition.definitie.lower()
252: 
253:         # Check missing aspects
254:         missing_aspects = []
255:         for aspect, keywords in self.completeness_aspects.items():
256:             if not any(keyword in text for keyword in keywords):
257:                 missing_aspects.append(aspect)
258: 
259:         # Only suggest if significantly incomplete
260:         if len(missing_aspects) >= 2:
261:             enhanced_text = self._add_completeness_hints(
262:                 definition.definitie, missing_aspects, definition.begrip
263:             )
264:             if enhanced_text != definition.definitie:
265:                 results.append(
266:                     EnhancementResult(
267:                         enhancement_type=EnhancementType.COMPLETENESS,
268:                         original_text=definition.definitie,
269:                         enhanced_text=enhanced_text,
270:                         confidence=0.6,
271:                         explanation=f"Volledigheid verbeterd (ontbrekende aspecten: {', '.join(missing_aspects)})",
272:                     )
273:                 )
274: 
275:         return results
276: 
277:     def _add_completeness_hints(
278:         self, text: str, missing_aspects: list[str], begrip: str
279:     ) -> str:
280:         """Voeg volledigheid hints toe."""
281:         if not text.endswith("."):
282:             text += "."
283: 
284:         # Add generic completeness improvement
285:         if "doel" in missing_aspects and "proces" in missing_aspects:
286:             addition = f" Het {begrip.lower()} heeft een specifiek doel en volgt een bepaalde procedure."
```

## src/toetsregels/regels/ARAI-04SUB1.json:1–45

```text
1: {
2:   "id": "ARAI04SUB1",
3:   "naam": "Beperk gebruik van modale werkwoorden",
4:   "uitleg": "Definities vermijden modale werkwoorden zoals ‘kan’, ‘mag’, ‘moet’, omdat deze onduidelijkheid scheppen over de essentie van het begrip.",
5:   "toelichting": "Modale werkwoorden drukken mogelijkheid, toestemming of verplichting uit. In een definitie hoort objectieve beschrijving centraal te staan, niet potentie of wenselijkheid. Modale hulpwerkwoorden kunnen leiden tot interpretatieverschillen over of iets een kenmerk of een randvoorwaarde is.",
6:   "toetsvraag": "Bevat de definitie modale werkwoorden die verwarring kunnen veroorzaken over wat het begrip is?",
7:   "herkenbaar_patronen": [
8:     "\\bkan\\b",
9:     "\\bkunnen\\b",
10:     "\\bmag\\b",
11:     "\\bmogen\\b",
12:     "\\bmoet\\b",
13:     "\\bmoeten\\b"
14:   ],
15:   "goede_voorbeelden": [
16:     "proces dat persoonsgegevens verwerkt"
17:   ],
18:   "foute_voorbeelden": [
19:     "proces dat gegevens *kan* verwerken"
20:   ],
21:   "prioriteit": "midden",
22:   "aanbeveling": "optioneel",
23:   "geldigheid": "gehele definitie",
24:   "status": "conceptueel",
25:   "type": "formulering",
26:   "thema": "interne kwaliteit van de definitie",
27:   "subsidieregel_van": "ARAI04",
28:   "brondocument": "Afgeleide AI-regel op basis van ASTRA",
29:   "relatie": [
30:     {
31:       "fulltext": "Geen beslisregel",
32:       "fullurl": "https://www.astraonline.nl/index.php/Geen_beslisregel"
33:     }
34:   ],
35:   "runtime_contract": {
36:     "evaluator": "generic",
37:     "required_inputs": [
38:       "definition_text"
39:     ],
40:     "executability": "deterministic",
41:     "automation_status": "automated",
42:     "score_policy": "excluded_from_score",
43:     "example_pair_policy": "normative"
44:   }
45: }
```

## src/toetsregels/regels/STR-06.json:1–46

```text
1: {
2:   "id": "STR_06",
3:   "naam": "Essentie ≠ informatiebehoefte",
4:   "uitleg": "Een definitie geeft de aard van het begrip weer, niet de reden waarom het nodig is.",
5:   "toelichting": "De definitie beschrijft wat het begrip *is*, niet waarvoor het nodig is. Formuleringen als 'om te kunnen...' of 'ten behoeve van...' beschrijven een behoefte of gebruik en horen niet thuis in de definitie zelf.",
6:   "toetsvraag": "Bevat de definitie uitsluitend wat het begrip is, en niet waarom het nodig is of waarvoor het gebruikt wordt?",
7:   "herkenbaar_patronen": [
8:     "\\bom te\\b",
9:     "\\bzodat\\b",
10:     "\\bten behoeve van\\b",
11:     "\\bvoor het verkrijgen van\\b",
12:     "\\bmet het oog op\\b",
13:     "\\bgericht op\\b"
14:   ],
15:   "goede_voorbeelden": [
16:     "beveiligingsmaatregel: voorziening die ongeautoriseerde toegang voorkomt"
17:   ],
18:   "foute_voorbeelden": [
19:     "beveiligingsmaatregel: voorziening om ongeautoriseerde toegang te voorkomen"
20:   ],
21:   "prioriteit": "hoog",
22:   "aanbeveling": "verplicht",
23:   "geldigheid": "alle",
24:   "status": "definitief",
25:   "type": "gehele definitie",
26:   "thema": "structuur van de definitie",
27:   "brondocument": "ASTRA",
28:   "relatie": [
29:     {
30:       "fulltext": "Essentie ≠ informatiebehoefte",
31:       "fullurl": "https://www.astraonline.nl/index.php/Essentie_≠_informatiebehoefte"
32:     }
33:   ],
34:   "runtime_contract": {
35:     "evaluator": "judgment_review",
36:     "required_inputs": [
37:       "definition_text"
38:     ],
39:     "executability": "judgment",
40:     "automation_status": "review_required",
41:     "score_policy": "excluded_from_score",
42:     "example_pair_policy": "review_policy",
43:     "example_pair_reason": "essentie versus informatiebehoefte is een inhoudelijk oordeel; het patroon deelt zijn markers met ESS-01 en mist de gesplitste om-te-constructie.",
44:     "example_pair_issue": "DEF-624"
45:   }
46: }
```

## src/toetsregels/regels/INT-08.json:1–45

```text
1: {
2:   "id": "INT_08",
3:   "naam": "Positieve formulering",
4:   "uitleg": "Een definitie wordt in principe positief geformuleerd, dus zonder ontkenningen te gebruiken; uitzondering voor onderdelen die de definitie specifieker maken (bijv. relatieve bijzinnen).",
5:   "toelichting": "Negatieve formuleringen kunnen verwarrend zijn of leiden tot onduidelijkheid. Een definitie moet helder en direct aangeven wat iets *wel* is, in plaats van wat het *niet* is. Elementen die een definitie specifieker maken, bijvoorbeeld via een relatieve bijzin, mogen wél in ontkennende vorm worden geformuleerd.",
6:   "toetsvraag": "Is de definitie in principe positief geformuleerd en vermijdt deze negatieve formuleringen, behalve om specifieke onderdelen te verduidelijken?",
7:   "herkenbaar_patronen": [
8:     "\\bniet\\b",
9:     "\\bgeen\\b",
10:     "\\bzonder\\b",
11:     "\\buitgezonderd\\b",
12:     "\\bniet geschikt voor\\b",
13:     "\\bmag niet\\b",
14:     "\\bvermijdt\\b"
15:   ],
16:   "goede_voorbeelden": [
17:     "bevoegd persoon: medewerker met formele autorisatie om gegevens in te zien"
18:   ],
19:   "foute_voorbeelden": [
20:     "bevoegd persoon: iemand die niet onbevoegd is"
21:   ],
22:   "prioriteit": "midden",
23:   "aanbeveling": "verplicht",
24:   "geldigheid": "gehele definitie",
25:   "status": "definitief",
26:   "type": "formulering",
27:   "thema": "interne kwaliteit van de definitie",
28:   "brondocument": "ASTRA",
29:   "relatie": [
30:     {
31:       "fulltext": "Positieve formulering",
32:       "fullurl": "https://www.astraonline.nl/index.php/Positieve_formulering"
33:     }
34:   ],
35:   "runtime_contract": {
36:     "evaluator": "generic",
37:     "required_inputs": [
38:       "definition_text"
39:     ],
40:     "executability": "deterministic",
41:     "automation_status": "automated",
42:     "score_policy": "scored",
43:     "example_pair_policy": "normative"
44:   }
45: }
```

## src/toetsregels/runtime_contract.py:1–150

```text
1: """Typed runtimecontract voor de JSON-toetsregels (DEF-606 / ADR-001).
2: 
3: `config/toetsregels/toetsregels_config.yaml` is de gezaghebbende root-SSOT;
4: de 53 JSON-bestanden onder `src/toetsregels/regels/` zijn de versioned
5: uitvoerbare regelrecords daaronder. Deze module maakt dat contract
6: afdwingbaar:
7: 
8: - iedere regel wijst precies één bekende evaluatorstrategie aan;
9: - iedere regel declareert expliciet welke invoer die strategie vereist;
10: - iedere regel draagt een uitvoerbaarheidsklasse, automatiseringsstatus en
11:   scorepolicy;
12: - afwijking tussen rootconfig, record en runtime faalt zichtbaar
13:   (`RuleContractError`) in plaats van stil een tweede waarheid te maken.
14: 
15: Bewust géén onderdeel van deze module: de evaluatorimplementaties zelf
16: (die leven achter het register in `services.validation.evaluators`) en de
17: promptmetadata in de records (uitleg, toelichting, voorbeelden) — die
18: blijven ongemoeid naast het uitvoerbare deel bestaan.
19: """
20: 
21: from __future__ import annotations
22: 
23: import functools
24: import json
25: import re
26: from collections.abc import Iterable, Mapping
27: from dataclasses import dataclass
28: from enum import StrEnum
29: from pathlib import Path
30: from typing import Any
31: 
32: import yaml
33: 
34: __all__ = [
35:     "REGEX_PATROONVELDEN",
36:     "AutomationStatus",
37:     "EvaluatorType",
38:     "ExamplePairPolicy",
39:     "Executability",
40:     "RequiredInput",
41:     "ResultStatus",
42:     "RootContractPolicy",
43:     "RuleContractError",
44:     "RuleRecord",
45:     "ScorePolicy",
46:     "build_rule_record",
47:     "build_rule_records",
48:     "canonical_rule_id",
49:     "lees_regelbestand",
50:     "load_root_contract_policy",
51:     "missing_inputs",
52:     "root_contract_policy",
53:     "status_for_missing_inputs",
54:     "valideer_regelset",
55: ]
56: 
57: CONTRACT_BLOCK = "runtime_contract"
58: PROVENANCE_BLOCK = "provenance"
59: 
60: # De gezaghebbende root-SSOT (ADR-001). Niet alleen documentatie: de
61: # waardesets hieronder worden bij laden tegen de Python-enums gelegd, zodat
62: # YAML en runtime niet stil uit elkaar kunnen lopen.
63: ROOT_CONFIG_PATH: Path = (
64:     Path(__file__).resolve().parents[2]
65:     / "config"
66:     / "toetsregels"
67:     / "toetsregels_config.yaml"
68: )
69: 
70: _NIET_ALFANUMERIEK = re.compile(r"[^A-Z0-9]")
71: 
72: # De recordvelden die een evaluator als regex compileert. Compileerbaarheid
73: # hoort bij het contract en niet bij de evaluatie: de evaluators vingen
74: # `re.error` eerder zelf af met een lege patroonlijst, waardoor één
75: # onbruikbaar patroon álle patronen van de regel uitzette en de regel van
76: # falend naar geslaagd ging (DEF-667). Wie hier een veld bijzet, moet de
77: # verwachting in `test_rule_loader_failclosed.TestPatrooncontract`
78: # meebewegen; die lijst is bewust onafhankelijk opgeschreven.
79: REGEX_PATROONVELDEN: tuple[str, ...] = (
80:     "herkenbaar_patronen",
81:     "herkenbaar_patronen_particulier",
82:     "herkenbaar_patronen_proces",
83:     "herkenbaar_patronen_resultaat",
84:     "herkenbaar_patronen_type",
85:     "redundancy_patterns",
86:     "required_patterns",
87: )
88: 
89: 
90: class RuleContractError(ValueError):
91:     """Een regelrecord voldoet niet aan het runtimecontract."""
92: 
93: 
94: class EvaluatorType(StrEnum):
95:     """Gesloten set evaluatorstrategieën; één per regelrecord."""
96: 
97:     GENERIC = "generic"
98:     POSITIVE_INDICATOR = "positive_indicator"
99:     ABBREVIATION = "abbreviation"
100:     LEMMA_MORPHOLOGY = "lemma_morphology"
101:     DEFINITION_GRAMMAR = "definition_grammar"
102:     QUALIFICATION = "qualification"
103:     DEFINITION_OVERLAP = "definition_overlap"
104:     COMPOUND = "compound"
105:     DEFINITION_GRAPH = "definition_graph"
106:     PREFERRED_TERM = "preferred_term"
107:     SYNONYM_CONSISTENCY = "synonym_consistency"
108:     CONTEXT_METADATA = "context_metadata"
109:     ONTOLOGICAL_CATEGORY = "ontological_category"
110:     DUPLICATE_DETECTION = "duplicate_detection"
111:     JUDGMENT_REVIEW = "judgment_review"
112:     # DEF-743: broninhoudelijke beoordeling (AI + code + deskundige), CON-02.
113:     SOURCE_EVIDENCE = "source_evidence"
114:     # DEF-766: AI-beoordeling van telbaarheid en onderscheidbaarheid (code
115:     # toetst binding en citaatbestaan), ESS-03.
116:     COUNTABILITY_ASSESSMENT = "countability_assessment"
117: 
118: 
119: class ExamplePairPolicy(StrEnum):
120:     """Hoe het gedocumenteerde goed/fout-paar als regressiecase telt."""
121: 
122:     NORMATIVE = "normative"
123:     REQUIRES_REPOSITORY = "requires_repository"
124:     REVIEW_POLICY = "review_policy"
125:     SOURCE_DEFECT = "source_defect"
126: 
127: 
128: class RequiredInput(StrEnum):
129:     """Gesloten set invoernamen die een evaluator kan vereisen."""
130: 
131:     DEFINITION_TEXT = "definition_text"
132:     TERM = "term"
133:     CONTEXT_LISTS = "context_lists"
134:     ONTOLOGICAL_CATEGORY = "ontological_category"
135:     DEFINITION_REPOSITORY = "definition_repository"
136:     SYNONYMS = "synonyms"
137:     PREFERRED_TERM = "preferred_term"
138:     RELATED_CONCEPTS = "related_concepts"
139: 
140: 
141: class Executability(StrEnum):
142:     """Hoe een regel überhaupt beoordeeld kán worden."""
143: 
144:     DETERMINISTIC = "deterministic"
145:     REPOSITORY = "repository"
146:     JUDGMENT = "judgment"
147:     NOT_AUTOMATABLE = "not_automatable"
148: 
149: 
150: class AutomationStatus(StrEnum):
```

## src/services/validation/evaluators/countability_assessment.py:1–99

```text
1: """ESS-03 — telbaarheid en onderscheidbaarheid van instanties (DEF-766).
2: 
3: De regel toetst niet langer een woordpatroon en is niet langer een
4: permanent open reviewpunt: sinds DEF-766 beoordeelt de app zelf, via
5: `domain.ess03.contract.beoordeel_telbaarheid`, of de kandidaat bij de
6: bedoelde betekenis duidelijk maakt wat als één, dezelfde of een andere
7: instantie geldt. Deze evaluator is synchroon en zuiver; de AI-beoordeling
8: wordt door de async wrapper verkregen (`ValidationOrchestratorV2` →
9: `Ess03AssessmentService`) en reist mee in `metadata["ess03_assessment"]`.
10: 
11: - lege definitietekst → `not_evaluated` (geen toetsobject; de basisfout
12:   blijft bij VAL-EMP-001);
13: - geen (toepasbare) beoordeling → `review_required` met de reden — nooit
14:   pass: een directe service-aanroep zonder voorbereide beoordeling blijft
15:   expliciet niet beoordeeld;
16: - gevalideerde beoordeling → `pass` / `fail` / `not_applicable`, of
17:   `review_required` mét precies één gerichte vraag (onvoldoende informatie);
18: - technische fout in de beoordeling → `error` (nooit pass, nooit afkeur);
19: - nooit een cijfer: `score` blijft `None`, de regel declareert
20:   `score_policy: no_score`.
21: 
22: Een negatieve uitkomst is zichtbaar (violation met de AI-onderbouwing) maar
23: geen blokkade: de ernst wordt expliciet op `warning`/`medium` gezet, zodat
24: noch de acceptatiegate (critical-telling) noch de vaststelgate (kritieke/hoge
25: issues) erdoor verandert, en `metadata.advisory` markeert dat. Toetsen
26: wijzigt de tekst niet en start geen herstel (besluit 21 september 2026).
27: """
28: 
29: from __future__ import annotations
30: 
31: from typing import Any
32: 
33: from domain.ess03.contract import (
34:     STATUS_ERROR,
35:     STATUS_FAIL,
36:     STATUS_NOT_APPLICABLE,
37:     STATUS_PASS,
38:     Beoordelingsbinding,
39:     Ess03Uitkomst,
40:     beoordeel_telbaarheid,
41:     intentie_uit_context,
42: )
43: from services.validation.evaluators.base import (
44:     EvaluationDeps,
45:     EvaluationOutcome,
46:     bouw_violation,
47: )
48: from services.validation.types_internal import EvaluationContext
49: from toetsregels.runtime_contract import EvaluatorType, ResultStatus, RuleRecord
50: 
51: __all__ = [
52:     "ADVISORY_SEVERITY",
53:     "ADVISORY_SEVERITY_LEVEL",
54:     "CountabilityAssessmentEvaluator",
55: ]
56: 
57: #: De niet-blokkerende ernst van een negatieve ESS-03-uitkomst (besluit 21-09-2026).
58: ADVISORY_SEVERITY = "warning"
59: ADVISORY_SEVERITY_LEVEL = "medium"
60: 
61: 
62: class CountabilityAssessmentEvaluator:
63:     """Telbaarheid van ESS-03: eenheid, onderscheid en toepasselijkheid, zonder cijfer."""
64: 
65:     evaluator_type = EvaluatorType.COUNTABILITY_ASSESSMENT
66: 
67:     def evaluate(
68:         self, record: RuleRecord, ctx: EvaluationContext, deps: EvaluationDeps
69:     ) -> EvaluationOutcome:
70:         metadata = ctx.metadata or {}
71:         # Zelfde tekstbasis als CON-01/CON-02: de exacte recordtekst, niet de
72:         # opgeschoonde variant, zodat de vingerafdruk bij het record hoort.
73:         recordtekst = metadata.get("record_text")
74:         tekst = recordtekst if isinstance(recordtekst, str) else (ctx.raw_text or "")
75:         if not tekst.strip():
76:             # DEF-766 (casus H-empty): zonder toetsobject is er niets te
77:             # beoordelen — geen open vraag over een lege kern en geen
78:             # inhoudelijke afkeur; de basisfout blijft bij VAL-EMP-001.
79:             return EvaluationOutcome.not_evaluated(
80:                 "vereiste invoer ontbreekt: definition_text (lege definitietekst, "
81:                 "geen toetsobject voor ESS-03)"
82:             )
83:         bronnen = metadata.get("provenance_sources")
84:         if bronnen is None:
85:             bronnen = metadata.get("sources")
86:         uitkomst = beoordeel_telbaarheid(
87:             ctx.begrip or "",
88:             tekst,
89:             metadata,
90:             bronnen,
91:             intentie=intentie_uit_context(metadata),
92:             assessment=metadata.get("ess03_assessment"),
93:             # R1: de actuele beoordelingsbinding zoals de wrapper haar van de
94:             # dienst kreeg; zonder binding is geen beoordeling actueel.
95:             binding=_binding_uit(metadata.get("ess03_binding")),
96:         )
97:         return _naar_outcome(record, deps, uitkomst)
98: 
99: 
```
