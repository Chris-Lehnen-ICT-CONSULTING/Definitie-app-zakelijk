# DEF-622 — herstel na onafhankelijke implementatiecontrole

15 september 2026. **R1 en R2 zijn gecorrigeerd en binnen de hieronder beschreven proeven geverifieerd. DEF-622 is hiermee niet volledig afgerond.** Deze notitie corrigeert de te ruime conclusie uit de eerdere oplevering: een positief CON-01-resultaat bewijst geen algemeen gesloten vaststel-/exportgate. De gebruiker heeft de twee gaten na merge van PR451 met aanvullende proeven aangetoond.

Basis: `6dc1e6ae87cc8020daf7abd46c6c6aad74bee4ce`, de reguliere merge van PR451 met dezelfde tree als `a2f5f97cf`. De herstelbranch is `bugfix/DEF-622-naamsignaal-zelfduplicaat`. Het [herstelplan](../plans/2026-09-15-DEF-622-naamsignaal-zelfduplicaat.md) verwijst naar de oorspronkelijke controle en de actuele issues. De coördinator heeft de oorspronkelijke domein-/SQLite- en Streamlit-proeven vóór de wijziging opnieuw uitgevoerd: R1, R2 en de aparte R3-afhankelijkheid traden opnieuw op.

## Hersteld gedrag

**R1 — geen contextvermelding.** De expert kan bij bijvoorbeeld gewoon ‘om’ en vastgelegde context ‘OM’ kiezen voor ‘Dit is geen contextvermelding’. De aanleiding beschrijft een teksttreffer, zonder vooraf te stellen dat het een naam is. Een gemotiveerde, actuele beslissing geeft voor die treffer ‘Voldoet’, met de juiste uitleg en zonder noodzakelijke-naamclaim. Actor, reden, inhoudsvingerafdruk en strikte versiebinding gebruiken de bestaande controles. Andere treffers blijven afzonderlijk open of falend. Er is geen automatische hoofdletteruitzondering en geen nieuwe regelstatus. CON-01 houdt een uitkomst zonder cijfer.

De echte Streamlit AppTest kiest de optie, vult actor en reden in, slaat de beoordeling op en hertoetst via de werkelijke orchestrator. SQLite-readback bevat `not_context`, de ingevoerde reden en actor en een beoordeling die aan de nieuwe recordversie is gekoppeld. De definitiezin en concept/reviewstatus blijven behouden. De blijvend zichtbare terugkoppeling toont de beoordelaar en de motivering.

**R2 — eigen record niet als duplicaat.** De evaluator gebruikt nu de door V2 aangeleverde `definition_id`. Alleen aantoonbaar hetzelfde record wordt overgeslagen; daarna gaat de kandidaatvergelijking verder. Beide IDs moeten werkelijke gehele getallen zijn. Bool, float, cijfertekst en ontbrekende ID vormen geen bewijs van identiteit en sluiten niets uit. De bestaande context- en categoriecontrole blijven gelden.

Proeven met echte V2-bedrading en tijdelijke SQLite bewijzen: alleen het eigen record geeft geen DUP_01-bevinding; een tweede werkelijk duplicaat wordt wel gemeld, ook wanneer het eigen record eerst komt; een nieuw voorstel zonder eigen ID blijft met bestaande records vergeleken worden. Dit herstelt uitsluitend de zelfdetectie uit DEF-677, niet de overige onderwerpen van dat issue.

## Uitvoeringsbewijs

Alle proeven gebruiken de bestaande offline-bootstrap en synthetische tijdelijke databases. Geen gebruikersdatabase, live modelaanroep of installatie in de gebruikersomgeving. Claude CLI implementeerde; de desktop voerde de tests en kwaliteitscontroles uit. De laatste tien gewijzigde productie-/testbestanden zijn vóór de brede gates gehasht en na afloop ongewijzigd bevonden.

| Controle | Waargenomen resultaat |
|---|---|
| Nieuwe regressies vóór correctie | 28 tests: 8 bedoelde failures, 20 geslaagd, geen errors/skips |
| Gerichte regressies na correctie | 42 geslaagd, geen failures/errors/skips, exit 0 |
| Volledige unitgate met coverage | 5.222 geslaagd + 21 subtests; 75 bestaande skips, 1 xfail; exit 0 |
| Coverage | 57,10% bij projectvloer 45% |
| Integratiegate | 571 geslaagd; 28 bestaande skips, 15 xfails, 2 niet-strikte xpasses; exit 0 |
| Acceptatiegate | 21 geslaagd; 5 bestaande collectieskips; exit 0 |
| Contractgate | 36 geslaagd; 6 bestaande skips; exit 0 |
| Kwaliteit | Ruff/Black, mypy 0, complexiteit 199 bij grens 201, overrides/pins geslaagd |
| Aanvullende guards | Orphans, silent-except, grep: geen blokkades; alle 400 testbestanden hebben markers |

De eerste run na implementatie had één foutieve nieuwe testverwachting: een tijdelijke succesmelding werd na `st.rerun()` verwacht. Opslag en hertoetsing waren al correct. De test controleert nu de blijvend zichtbare actor en motivering; de functionele assertions zijn behouden. Vier testbestanden zijn met Black 26.5.1 geformatteerd. De brede gates draaien op de uiteindelijke inhoud. Bestaande overslagen zijn niet als uitgevoerde tests geteld.

Lokaal bewijs: `reports/def622/r1-r2/` met baselineproeven, RED/GREEN-JUnit, `unit.log`, `nonunit.log`, de inventarissen/JUnit/coverage onder `final-gates/`, `source-manifest.json` en `final-verification.json`. De formatteropdracht is na afzonderlijke opdrachtgoedkeuring via de normale CLI-controle uitgevoerd; hooks zijn niet uitgezet.

## Onafhankelijke review

Een afzonderlijke Codex CLI-review (`01a0a45d-6a5c-7271-bc8a-193e59e38ea0`) onderzocht de concrete diff, opslag/readback, V2-doorgifte, AppTest-waarnemingen en de bronbinding. Oordeel: **geen bevestigde relevante bevindingen; R1 en R2 binnen de afgesproken grenzen gesloten en inhoudelijk klaar voor een draft-PR**. Dit was een onafhankelijke code-/bewijsreview; de reviewer voerde zelf geen aanvullende tests uit. De coördinator heeft de procesuitkomsten afzonderlijk gelezen en de brede gates daarna volledig zien slagen.

## Wat open blijft

- **DEF-630 / R3:** onder de werkelijke standaardpolicy kan ontbrekend validatiebewijs via een handmatige notitie worden overruled. De baselineproef bevestigt `override_required`, daarna handmatig `established` met null-score. De specifieke CON-01-blokkades voor ontbrekende context/open naamfunctie zijn daarvan te onderscheiden. Dit pakket verandert de algemene policy niet.
- **Globale skills:** de voorbereide definitie-/toetsregelaanpassing is niet geïnstalleerd. De lokale appcorrecties bewijzen geen gelijkgetrokken globale skills.
- **DEF-677:** capabilitydefect, declaratieve blokkeerpolicy, severitybesluit en overige oorspronkelijke criteria blijven afzonderlijk open.
- **DEF-624 / DEF-638:** totaalscore blijft tijdelijk niet beschikbaar; automatisch CON-tekstherstel blijft uitgesteld vervolgwerk.

Geen volledige live-browserronde op een gebruikersinstallatie, juridische praktijkvalidatie of modelbenchmark uitgevoerd. DEF-622 blijft In Progress; deze hersteloplevering is geen volledige productvrijgave.
