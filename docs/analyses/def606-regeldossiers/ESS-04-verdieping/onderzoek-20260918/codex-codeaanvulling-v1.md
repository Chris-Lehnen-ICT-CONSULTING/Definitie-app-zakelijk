# Onafhankelijke gerichte codeaanvulling

18 september 2026; bewaard vóór nieuwe Cowork-conclusies. Snapshot 4cdb8ea43. Statische bronlezing, geen aanvullende runtime- of UI-test.

## Import

De juiste dienst is src/services/definition_import_service.py. validate_single :67–96 zet payload om, roept validatie aan en leest is_acceptable als preview.ok. import_single :98–169 behandelt validatietimeout en duplicaten en maakt importmetadata met standaard draft. De gelezen opslagroute gebruikt preview.ok niet als aparte ESS-04-poort. Dit bewijst geen fout: conceptimport en formele vaststelling zijn verschillende handelingen. Geen import-/readback-proef uitgevoerd. Nalevering bevat ook database/definitie_import_export.py; niet iedere importingang is hiermee onderzocht.

## excluded_from_score tegenover no_score

modular_validation_service.py :977–994 zet gewicht voor beide policies op nul, maar geen_cijfer wordt alleen bij NO_SCORE gezet (:1019). _verwerk_uitkomst :1568–1630 boekt bij PASS/FAIL alsnog een individueel cijfer als geen_cijfer false is. REVIEW_REQUIRED krijgt geen cijfer. _calculate_category_scores :2034–2071 middelt de individuele cijfers ongewogen; :1168 maakt categorieën met NO_SCORE vervolgens leeg.

Daarom betekent behouden excluded_from_score in het huidige voorstel alleen: geen ongeautoriseerde contractmigratie in deze onderzoeksfase. Het is geen aanbeveling om bij toekomstige menselijke PASS/FAIL een kwaliteitsscore te introduceren. Bij het ontwerp van de ESS-04-reviewroute moet een expliciete scoreloze contractkeuze worden gemaakt; no_score is daarvoor een te beoordelen kandidaat. De huidige automatische ESS-04-route geeft review_required, dus deze statische toekomstige PASS/FAIL-doorrekening bewijst geen nu gemeten ESS-04-cijferlek. Een migratie vraagt tevens een concrete rule_result-structuur, transport en consumercontroles; alleen het policywoord wijzigen bewijst die aansluiting niet.

Te bespreken bij kruisreview: N1 behouden, toekomstig reviewcontract expliciet scoreloos ontwerpen; ernst, voortgangsvoorwaarden en handmatige vaststelling daarvan scheiden. Het appbrede besluit tegen totaalscore is al vastgesteld, deze concrete ESS-04-contractmapping niet.
