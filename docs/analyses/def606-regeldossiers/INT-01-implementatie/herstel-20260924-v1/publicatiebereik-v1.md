# Publicatiebereik van de herstel-PR

De normale pre-commitscan blokkeerde de eerste commitpoging op16treffers. Alleen metadata is bij triage gepubliceerd; er is geen gate of uitzondering veranderd.

-13treffers zijn bewijs-hashes:12API-verzoekhashes zijn opnieuw berekend over de canonieke JSON en matchen;1opleverhash matcht het exacte tokentelbestand. Dit zijn geen authenticatiewaarden.
-3treffers komen uit de gegenereerde parameternamen van de PII-redactietests. De testbron tests/unit/utils/test_pii_redaction_api_keys.py verklaart de waarden expliciet verzonnen en stelt ze samen uit vaste fragmenten.

De ongewijzigde oorspronkelijke bestanden blijven in de lokale projectwerkboom, buiten deze publicatieset: effectproeven-20260924-v1/g24-voorbereiding-oud-v1.json, g24-voorbereiding-nieuw-v1.json, g24-opleververificatie-v1.json en herstel-20260924-v1/r4-unit-coordinator-v3.xml. Hun historische binding en inhoud zijn niet aangepast. Verwijzingen naar die ruwe bestanden zijn dus lokaal; de overige proefrapporten, inputs, generaties, beoordelingen en manifesten staan wel in deze PR. Dit is een publicatiebeperking, geen ontbrekende uitvoering.

Voor de laatste unit-suite is r4-unit-coordinator-v3-publicatie.xml meegeleverd. Alleen sleutelvormige verzonnen testwaarden zijn als GEREDIGEERDE_TESTWAARDE weergegeven; testcase-aantal en testsuite-uitkomsten zijn structureel gelijk aan het origineel gecontroleerd. De volledige tekstlog van de geslaagde run is eveneens opgenomen.

De publicatie moet opnieuw door dezelfde ongewijzigde geheimenscanner. Geen allowlist, scanoverslag of wijziging van de beveiligingsconfiguratie.
