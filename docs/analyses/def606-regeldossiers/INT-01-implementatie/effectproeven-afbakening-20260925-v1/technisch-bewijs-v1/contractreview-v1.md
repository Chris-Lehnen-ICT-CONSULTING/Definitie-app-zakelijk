**Het referentiecontract vertaalt beide besluiten correct. Vóór de proef resteert één broninconsistentie.**

**Important — fix nu:** `src/toetsregels/regels/INT-01.json:5` zegt nog onbegrensd dat “een mogelijke onbekende afkorting” onzeker blijft. Dat botst met het nieuwe besluit §2 en `referentie-contract-v1.md:13`: onbekendheid aan het teksteinde, zonder vervolg of concrete afbreking, geeft op zichzelf **geen zinsstructuuronzekerheid**. Begrens deze regelrecordpassage overeenkomstig het besluit. Dit is een tekstuele bronafstemming, geen aangetoonde runtimebug of aanleiding voor een nieuwe heuristiek.

Verder sluit de contractdelta aan:

- Regels 7 en 11 beperken het conservatieve citaatbeleid expliciet tot **interne zinseindpunctuatie**; regel 13 bewaart echte grenzen, afbreking en de afzonderlijke beoordeling van gehele-kerncitaten.
- INT-07 (`INT-07.json:4–6`) onderbouwt de toegankelijkheidseis voor afkortingen. Het contract claimt terecht geen automatische herkenning daarvan.
- Normatieve en automatische as blijven gescheiden; compactheid/begrijpelijkheid blijven open. Historische labels worden niet gewijzigd.

Beoordeeld op bewijs-HEAD `659ab505bcba2af6293917dbbcbcbaebc8a5e581`. Contract-SHA256:
`d60b4dbb718101ae6b284f42fd33865e9bfca3d1d70accd81a6bc0ba82e740ea`

**Dispositie:** eerst bovenstaande bronafstemming; contractinhoud verder akkoord. Geen effect- of mergevrijgave. Geen edits of tests uitgevoerd.