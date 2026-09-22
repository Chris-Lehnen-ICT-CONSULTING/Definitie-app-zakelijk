# Tussentijdse inspectie — verifieer op uiteindelijke diff

Deze notities betreffen onvoltooide code van circa 09:28. Niet als vastgestelde eindbevinding kopiëren; lees de uiteindelijke aanroepen en tegenmaatregelen.

- contract._bindingsafwijzing controleerde contract_version, input fingerprint en aanwezigheid modelnaam; geen vergelijking met actuele normhash/promptversie/model. Controleer of latere opslag/UI/evaluator dit alsnog afdoende afhandelt. Plan vereist oude norm/prompt/model niet als actuele beoordeling hergebruiken.
- service na valideer_oordeel zette status assessed, judgment soms None, rejected bewaard en cachede. Contract converteerde dat naar review_required. Controleer op uiteindelijke code of structureel defecte/verzonnen bewijsuitvoer als technische fout zichtbaar is en niet als inhoudelijk onvoldoende informatie of normale afgeronde beoordeling wordt gepresenteerd/gecached.
- parse_modeluitvoer pakte substring eerste { tot laatste }, in plaats van volledig gesloten JSON; controleer ambiguïteit/truncatie/trailing data en consistente strikte foutbehandeling in uiteindelijke keten.
- service geeft timeout_seconds aan AIService door; verifieer werkelijke limitering en retries op transportlaag. Een kwarg alleen bewijst dat niet. Geen conclusies uit deze voorlopige notitie zonder concrete actuele trace.
