# WP5a — concrete correctie F2 en gebundelde scope-uitbreiding

28 september 2026. De onafhankelijke review wp5a-codex-review-v1.md bewijst F2: een dienst voor fake-new-model kan een coherent document voor fake-int02-model teruggeven en de wrapper noemt het pass/current. De verwachting komt nu uit het ontvangen document zelf. Rechtstreekse toetsing tegen de actuele dienstconfiguratie noemt hetzelfde document historical. Dit moet vóór oplevering worden hersteld.

## Gevraagde uitbreiding

Naast de zeven eerder geaccordeerde WP5a-bestanden zijn twee bestaande bestanden nodig (totaal negen):

1. src/services/validation/int02_assessment_service.py: een additieve publieke leesmethode voor een onafhankelijke, volledige WP1-Configuratie-snapshot van de dienst. Zij gebruikt de actuele norm-, prompt-, profiel-, budget- en routeringsgegevens van de dienst, zonder modelaanroep of ontvangen document als bron. De wrapper legt deze snapshot vóór assess vast en controleert het teruggegeven document tegen die volledige verwachting én de verse invoer. Een mismatch, ontbrekende/ongeldige snapshot of fout wordt error zonder oordeel. Een wijziging gedurende de aanroep mag nooit stil pass/current worden. Geen private attribuutinspectie door de wrapper.
2. tests/unit/validation/test_def835_int02_assessment_service.py: tests voor die publieke leesmethode, en de eerder voorgelegde herijking van de bestaande WP2-containertekstguard (F3). De test blijft bestaan en bewijst geen automatische constructie of modelcall; expliciete factory met verplicht profiel/budget blijft toegestaan.

Raming: circa 40–100 extra productie-/testregels, aangevuld met gerichte mismatchtests in de al geaccordeerde nieuwe wrappertests. Geen dependency, schemawijziging of wijziging van het publieke validatieresultaatcontract 2.3.0/WP1-document. Wel een additieve dienst-API: daarom vraagt deze uitbreiding volgens de oorspronkelijke opdracht expliciet akkoord.

## Uitvoering

Dezelfde Claude CLI-uitvoerder corrigeert met gedragsmatige RED/GREEN; dezelfde Codex CLI-reviewer beoordeelt alleen de correctiediff en open F1–F3. Volledige binding testen op norm/prompt/routering/provider/model, inclusief het concrete reviewerrepro. Nul livecalls, O1 blijft actief, Actions uit, geen merge/activering.

Dit voorstel omvat tevens de nog onbeantwoorde achtste-bestandsvraag uit wp5a-testguard-aanvulling-v1.md. Eén akkoord op dit gecombineerde voorstel dekt beide extra bestanden en de beschreven API-uitbreiding.

F1 (het O2-pad bij ontbrekende context) valt al binnen de geaccordeerde modular-integratie en wordt onafhankelijk hiervan gecorrigeerd. Dat vraagt geen nieuw mandaat.
