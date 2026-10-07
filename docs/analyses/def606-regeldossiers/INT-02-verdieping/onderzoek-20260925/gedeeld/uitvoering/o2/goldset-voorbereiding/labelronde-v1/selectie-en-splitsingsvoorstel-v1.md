# INT-02 O2 — selectie- en splitsingsvoorstel (v1)

30 september 2026. **Besluitvoorstel aan Chris, geen geaccepteerde goldset, geen freeze en geen appkwalificatie.** Het akkoord in `besluit-chris-bundel-v1.md` dekt de voorbereiding en onafhankelijke beoordeling van extra onzekerheidsgevallen, niet deze definitieve selectie of 24/16-splitsing.

## Vaststaande basis en nieuwe beoordelingsvoorstellen

De 40 kandidaatgevallen in `../herwerking-v1/casuspool-kandidaat-v4.json` (SHA-256 `2c1919ee143f11551d9cb643667243ecb610769aa528548286a9fe4c7bbdbe64`) hebben na Chris' bundelbesluit 26 `pass`, 11 `fail` en 3 `review_required`. De familieverdeling is 11 begripscriterium, 15 normatief begrip, 11 actorvoorschrift en 3 ontbrekende/strijdige betekenisgrond. Het protocol `../../kwalificatieprotocol-v1.md` plant 10 per familie: 6 ontwikkeling en 4 hold-out. Labels zijn niet aangepast om die aantallen te halen.

Drie redactionele pogingen leverden achtereenvolgens G057–G063, G064–G069 en G070–G077. G070 ontbrak in poging 2; G078/G079 zijn in poging 3 gemotiveerd niet aangeboden. Alle concepten, prompts, modeluitvoer en manifesten zijn apart bewaard onder `../aanvulling-onzekerheid-v1/`, `-v2/` en `-v3/`. De beoordelaars kregen uitsluitend de gevalobjecten, norm, ontwerpregister, v4-pool en bronhashes; geen redacteursselectiepunten, peerlabels of appuitkomsten.

| Nieuwe kandidaat | A/B-statusvoorstel | Afzonderlijke functiegrens | Selectieadvies |
| --- | --- | --- | --- |
| G057 — transitcontainer | `review_required` / `review_required` | Twee gelijkelijk authentieke taalteksten: wegen als kenmerk of als weegplicht. | Opnemen. A twijfelt over afstand tot ontwerpgevallen, B acht de bronrelatie zelfstandig. |
| G060 — zelfopnemer | `review_required` / `review_required` | Blijvende categorie met maandelijkse plicht versus rapportagecategorie na tijdige doorgifte. | Opnemen. Andere tijd- en statusrelatie dan G076; alleen ontwikkeling. |
| G068 — zichtzending | `review_required` / `review_required` | Retourneren of betalen als kenmerk van de toezending versus verplichting na ontvangst. | Opnemen. Beide achten zelfstandig. |
| G070 — bemiddelingsdossier | `review_required` / `review_required` | Vastgelegd intakegesprek constitueert dossiersoort versus intake als stap ná openen. | Opnemen in ontwikkeling. A vraagt aanpassing wegens overlap met G076, B acht bruikbaar; voor INT-02 is de open functiegrond zichtbaar zonder tekstwijziging. |
| G071 — geannuleerde rondvaart | `review_required` / `review_required` | Beslissing van schipper constitueert annulering versus windmeting constitueert haar en schipper moet daarop handelen. | Opnemen. Beide achten zelfstandig en bruikbaar. |
| G073 — rustperiode | `review_required` / `review_required` | Feitelijk werkvrij interval achteraf afgeleid versus vaste kalenderperiode met werkverbod. | Opnemen. A vraagt aanpassing wegens overlap met G075; B acht bruikbaar. G075 wordt niet geselecteerd. De ontbrekende minimumduur van dertig dagen in de kern is een afzonderlijk betekenis-/volledigheidspunt, geen INT-02-grond. |
| G076 — aanwezig lid | `review_required` / `review_required` | Ondertekening constitueert aanwezigheidsstatus versus ondertekenplicht voor leden die door fysieke deelname al aanwezig zijn. | Opnemen in ontwikkeling. B vraagt eerst een onderscheid tegenover G070; hier handelt het gedefinieerde lid zelf en raakt de status het quorum, terwijl G070 een derde-actorregistratie over een dossier betreft. Beiden blijven uit hold-out. |

De drie onafhankelijke beoordelingsronden zijn inhoudelijk niet als één groot labelonderzoek uitgevoerd: per reeks twee verse sessies. In ronde 1 zijn 44 A-citaten na unieke mechanische positieaanvulling en 30 B-citaten exact; A's oorspronkelijke G058/G061-objecten missen `geschiktheid`, zonder invloed op de zeven hierboven. In ronde 2 zijn 43 A-citaten na unieke positieaanvulling en 30 B-citaten exact. In ronde 3 zijn 57 A-citaten en 32 B-citaten op opgegeven positie exact. Alle oorspronkelijke antwoorden blijven bewaard. De eerste A-aanroep voor ronde 3 eindigde met `ENOTFOUND`; dezelfde opdracht slaagde in een verse herhaling. De twee beoordelaars noemen G075 inhoudelijk onzeker maar bijna dezelfde teststructuur als G073; G059/G061/G074 hebben labelverschillen. Deze gevallen worden niet stilzwijgend als `review_required` meegeteld.

De Claude CLI rapporteerde voor de drie redacteursessies, drie geslaagde A-beoordelingen en de mislukte plus herhaalde A-aanroep samen **US$16,0976768**. Dit betreft voorbereidende CLI-sessies en staat buiten het afzonderlijke US$12-plafond voor de toekomstige appmodelkwalificatie. Codex CLI-gebruik is hierin niet geprijsd. Er zijn nog geen appkwalificatiecalls gedaan.

## Voorgestelde zeven kandidaten buiten de definitieve 40

Deze zeven blijven **ongewijzigd als aanvullend ontwikkelmateriaal** bewaard. Hun bestaande geaccepteerde inhoudelijke labels worden niet ingetrokken; alleen hun plek in de beoogde kwalificatieset verandert na Chris' akkoord.

| Familie | ID | Selectiereden |
| --- | --- | --- |
| Begripscriterium | G003 | A adviseerde aanpassen en stelde eerder `review_required` voor; Chris accepteerde `pass`. Als ontwikkelmateriaal blijft dit moeilijke grensgeval beschikbaar zonder het in de eindkwalificatieset te gebruiken. |
| Normatief begrip | G004 | Eenvoudig basisvoorbeeld van een beding en zijn werking; behoud als ontwikkelvoorbeeld naast de diversere normatieve gevallen. |
| Normatief begrip | G006 | Beide beoordelaars noemen overlap met G014; G021 dekt de beslissing als begrip met eigen bronrelatie. |
| Normatief begrip | G014 | Beide noemen overlap met G006; de eerdere A/B-labelspanning en betekenisvraag blijven nuttig ontwikkelmateriaal. |
| Normatief begrip | G018 | A betwijfelt ontwerpafstand en noemt overlap met G014/G003; de door Chris geaccepteerde `pass` blijft bewaard. |
| Normatief begrip | G029 | A betwijfelt ontwerpafstand en noemt overlap met G017; G046 behoudt een bevoegdheidsgeval in de beoogde 40. |
| Actorvoorschrift | G051 | Beide noemen overlap met G048/G049; de verhouding tussen vaste bedaanwijzing en dagelijkse bedkeuze blijft bovendien een afzonderlijk betekenisprobleem. |

Bij akkoord bevat de beoogde set precies de huidige v4-pool minus deze zeven plus G057/G060/G068/G070/G071/G073/G076. Niets wordt verwijderd. G075 en alle overige niet-geselecteerde nieuwe concepten blijven eveneens als ontwikkelmateriaal bewaard.

## Voorgestelde 24/16-verdeling

**Nog niet delen met apppromptontwikkelaar of implementator.** De procedurele scheiding uit het protocol blijft van kracht; deze repo biedt geen technische toegangsisolatie. Beoordelaars en redacteurs van de casussen zijn uitgesloten van die latere rol.

| Familie | Ontwikkeling (6) | Hold-out (4) |
| --- | --- | --- |
| Begripscriterium en afleiding | G011, G015, G019, G027, G030, G039 | G002, G031, G035, G054 |
| Normatief begrip/verplichting | G007, G021, G037, G041, G046, G055 | G017, G033, G043, G056 |
| Actorvoorschrift/procedure/discretie | G008, G012, G036, G048, G050, G052 | G024, G044, G049, G053 |
| Ontbrekende/strijdige grond | G042, G045, G047, G060, G070, G076 | G057, G068, G071, G073 |

Mechanische controle van dit voorstel: 40 unieke IDs; 24 ontwikkeling, 16 hold-out; per familie exact 6/4; de 40 assignments zijn precies de v4-set minus de zeven genoemde kandidaten plus de zeven nieuwe voorstellen. G070/G076 staan samen in ontwikkeling; G060 staat daar ook, zodat de verwante categorie-versus-handeling-structuren geen ontwikkel/hold-out-paar vormen. De vier onzekere hold-outs toetsen verschillende bronrelaties. De gevraagde kwaliteitsgrenzen, kosten en stopregels van het protocol zijn hierdoor **nog niet bewezen**; dat vergt eerst Chris' inhoudelijke acceptatie, freeze en daarna de begrensde modelproef.

## Besluit gevraagd

Chris kan in één reactie (1) de zeven nieuwe `review_required`-labels en de genoemde inhoudelijke voorbehouden accepteren of corrigeren, (2) de zeven genoemde verschuivingen naar aanvullend ontwikkelmateriaal kiezen of wijzigen, en (3) de voorgestelde 24/16-splitsing accepteren of aanpassen. Pas daarna maakt de coördinator een definitief versie- en hashgebonden freeze-manifest. Dit voorstel autoriseert geen appmodelcall, codewijziging, activering, merge of wijziging van Actions.
