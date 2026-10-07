# DEF-835 — gerichte hercontrole, beoordelaar A

Vervolg op jouw eigen onafhankelijke herbeoordeling. Je blijft zelfstandig documentbeoordelaar; geen agents, herdelegatie, codewijzigingen of netwerk/appcalls. Alleen lezen en één JSON-slotantwoord. Je bent niet alleen in de repository; schrijf geen bestanden.

Alleen G003, G006, G018, G030 zijn na de eerste beoordeling veranderd. De coördinator heeft de objecten vergeleken: de overige 36 gevallen zijn exact gelijk aan kandidaat-v1. Beoordeel uitsluitend deze vier nieuwe versies. Geen nieuwe algemene ronde of herbeoordeling van de overige23.

Lees /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/../herwerking-v1/casuspool-kandidaat-v2.json voor deze vier gevallen en /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/../herwerking-v1/manifest-kandidaat-v2.json. Vergelijk zo nodig met hun vorige tekst in casuspool-kandidaat-v1.json. Hergebruik jouw geldige normkennis uit /Users/chrislehnen/Projecten/Definitie-app/.claude/worktrees/DEF-835-int02-o2/docs/analyses/def606-regeldossiers/INT-02-verdieping/onderzoek-20260925/gedeeld/uitvoering/o2/goldset-voorbereiding/labelronde-v1/invoer/normcontract.md en besluiten-chris.md; deze bronnen zijn ongewijzigd. Ontwerpregister en oorspronkelijke casuspool blijven alleen relevante referentiebronnen. Lees GEEN conclusie van de andere beoordelaar of de redacteur. Aanleiding van correctie is geen gewenst label. Leg een zelfstandig oordeel vast.

Vragen per geval:
- Is de eerdere bronafwijking weg (G003: afzonderlijke registratie-/intrekkingsmomenten; G006: vaststelling versus reeds aanvaard; G018: volgende dag versus zodra; G030: losse nominale zin midden in imperatieven)?
- Welke functie draagt de gehele huidige kern op basis van de concrete bronnen? Aanvullende passages niet automatisch als bronconflict behandelen; evenmin de functie uit de documenttitel afleiden. Geen zelfstandig bewezen gebrek maskeren met onzekerheid. Geen labelquota, familie- of selectiebesluit namens Chris.
- Nog concrete bronfouten, betekenisverschuivingen of kunstmatige onzekerheid? Meld ze precies; wijzig geen tekst.

Geef één geldig JSON-object zonder fences:
beoordelaar="A", status="voorstel_niet_geaccepteerd", normversie="def771-int02/2", bronhashes uit manifest-kandidaat-v2.json,
gevallen=[precies G003,G006,G018,G030].
Per geval dezelfde velden als eerder: id, voorstel, familie, passages, gronden, motivering, vraag, zekerheid, afstand_ontwerp, redundantie_met, geschiktheid, opmerkingen.
Geef letterlijke citaatstrings met hun veld/bron_id en passagefunctie; start/end mag je WEGLATEN. De coördinator leidt tekenposities deterministisch af uit de unieke exacte citaattekst en controleert die mechanisch. Kies per bron een uniek citaat, niet een te kort herhaald fragment. Besteed geen tijd aan handmatig tekens tellen. Dit verandert de eis van exacte, herleidbare citaten niet.
Voeg dispositie_per_geval toe: id, bronpunt_opgelost (ja|nee|deels), reden, resterend_open. Geef geen lange samenvatting van ongewijzigde bronnen. Alle labels blijven voorstellen voor Chris.
