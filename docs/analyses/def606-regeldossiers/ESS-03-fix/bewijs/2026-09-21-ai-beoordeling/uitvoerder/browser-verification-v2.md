# ESS-03 — browsercontrole correctieronde 1

Coördinator bediende de echte app met cua_repl op21september2026, circa12:09–12:17. Verse Streamlitstart op http://127.0.0.1:8544, exec28327, log browser-app-v2-start2.log. De eerste sandboxstart mislukte door bind PermissionError; reguliere escalatie voor localhoststart slaagde. Oudere server8543 is niet gebruikt. Alleen synthetische lokale recordID3, geen productiegegevens. Tab2 is na controle gesloten; server blijft voorlopig aan.

Bronstand in browser-v2-input-and-source-seal.json. Controle na browserproef: nul hashafwijkingen in de10 opgenomen bronbestanden.

## Waargenomen geslaagde delen

1. Heropen kleurpasta(ID3) met eerder opgeslagen fase1-NA: de app toont dit expliciet als historisch en niet toegepast, met reden promptversie ess03-assess/1 tegenover actuele ess03-assess/2. Geen modelcall.
2. Via normale editor begrip meetobject, definitie Meetobject herkenbaar aan zijn registratienummer., toelichting Synthetische test: bedoeld zijn afzonderlijke meetobjecten. De registratieconventie is niet aangeleverd. Organisatiecontext NP bleef de bestaande selecteerbare context. ESS03-verduidelijking leeg, geen bronnen. Voorafverwachting insufficient_information vastgelegd in seal. Valideren toont expliciet Onvoldoende informatie, één gerichte vraag naar de registratieconventie, grond en gecontroleerde citaten, geen cijfer. Opslaan bevestigt actuele AI-beoordeling. SQLite-readback: assessed/insufficient_information, bewaard in browser-v2-insufficient-saved.json.
3. Vul de vooraf vastgelegde aanvulling uit browser-v2-clarification-input.md in het aparte verduidelijkingsveld. Die geeft fysieke eenheid, namespaceR, toekenning, geen hergebruik, identiteit bij onderdelenvervanging. Definitietekst ongewijzigd. Eerste hertoets faalt technisch door connection; zie afzonderlijke bevinding hieronder. Eén expliciete handmatige herkansing slaagt met pass. De app noemt de verduidelijking als bewijs en geeft geen automatische tekstwijziging. Opslaan bevestigt beoordeling; SQLite bevat assessed/pass en niet-lege ess03_verduidelijking (browser-v2-pass-saved.json).
4. Annuleren/sluiten editor, opnieuw zoeken op meetobject, opnieuw Bewerk: verduidelijking is behouden. Open opgeslagenAI-beoordeling: hetzelfde pass en onderbouwing als actueel zichtbaar. Geen extra AI-call.
5. Wis het verduidelijkingsveld bewust en klik Opslaan zonder hertoets. SQLite bevestigt expliciete sleutel ess03_verduidelijking met lege string (browser-v2-cleared-saved.json). De opgeslagenAI-sectie toont oudpass expliciet historisch en niet actueel. Sluit en heropen: veld blijft leeg.

## Bevestigde resterende UI-fout

Na stap5 toont het normale validatieblok bovenaan nog ESS03 Voldoet, met de oude grond en bewijs uit de gewiste verduidelijking. De afzonderlijke opgeslagenAI-sectie noemt hetzelfde oordeel wel historisch. Ook na Annuleren, opnieuw zoeken/openen blijft het bovenste blok Voldoet tonen. Er is geen nieuwe modelcall geweest en de database heeft de verduidelijking correct leeg opgeslagen. Dit is een concrete inconsistentie in het huidige resultatenblok, niet een vermoeden over SQLite. Bij dezelfde proef staat de definitie nog Meetobject herkenbaar aan zijn registratienummer.; de grond voor pass is bewust weggenomen. Nodig: actuele formulier-/recordbinding ook voor het normale edit-validatieresultaat, inclusief opgeslagen/hervatte state. Oude resultaten mogen als historie getoond worden, niet als actuele pass. Dit sluit aan opR1/R5.

## Verbindingsfout — oorzaak nog onbekend

De eerste editorcall was HTTP200 op12:11:17.899. De volgende hertoets gaf op12:12:48.999 onmiddellijk Anthropic connectionerror; de bridge logt API call failed after1attempts. De UI toonde Technisch probleem en expliciet geen inhoudelijk oordeel. Eén handmatige herkansing gaf daarna pass. Geen SDK Retryings in de v2-log gezien. De directe fout bij hergebruik van de appclient verdient gericht onderzoek naar eventloop/clientlevensduur; dat is een hypothese, geen bewezen oorzaak. Geef technische fout niet als inhoudelijke modelmisser weer. Het ruwe provider-exceptionoorzaakpad staat niet in deze UI-log.

## Reikwijdte en budget

Deze fase gebruikte3 beoordelingsaanroepen: insufficient-success, connection-error, handmatige pass-success. Samen met de eerdere23 conservatief26transportpogingen. Met30geplande eindcalls komt de som op56;4ruimte binnen60 blijft voor noodzakelijke verdere browsercontrole. Geen onafhankelijke eindsetdata gebruikt.

Niet in deze browserfase bewezen: negatieveESS03 met daadwerkelijke finalize/exportactie. De gekoppelde technische actieproef heeft4geslaagdetests. Andere regels geven voor dit korte synthetische geval eigen blokkades; dat bewijst geenESS03-blokkade. NA/generatiepad hadden browserbewijs uitfase1; correctie-browserfase2 bewijst bovengenoemde specifieke routes.

De bestaande ontbrekende tabel definitie_drafts blijft autosavefouten geven; handmatig opslaan slaagt. Geen schemafix of verwijdering uitgevoerd. De uitvoerder heeft eerder een eigen TXT-testartefact proberen op te ruimen; de file-protectionhook blokkeerde rm. Dat opruimen is niet nodig voor acceptatie en er is geen toestemming voor gevraagd of omweg toegepast.
