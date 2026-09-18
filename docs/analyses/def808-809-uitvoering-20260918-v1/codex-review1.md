**Eindoordeel voor `1183af7d`: één P2 / Important-bevinding, herstellen vóór goedkeuring.** Review uitgevoerd op exact `29d8176b..1183af7d`.

1. **Upload meldt opgeslagen bronmetadata terwijl de opslag is mislukt.**  
   In [document_processor.py:260](/private/tmp/DEF-808-809-p01-20260917/src/document_processing/document_processor.py:260) wordt eerst het document in geheugen gewijzigd. `_save_metadata()` vangt schrijffouten af en zet `_persistence_failed=True`, maar de nieuwe methode controleert dat niet en retourneert succes. Daardoor toont [document_upload_renderer.py:219](/private/tmp/DEF-808-809-p01-20260917/src/ui/renderers/document_upload_renderer.py:219) ten onrechte “Bronmetadata vastgelegd”.

   **Reproductie/bewijs:** met een geïnjecteerde `PermissionError` bij de daadwerkelijke opslagaanroep: één schrijfpoging, `_persistence_failed=True`, metadata uitsluitend in geheugen, **één succesmelding en nul fouten/waarschuwingen**. Bij herstart ontbreekt de nieuwe opgave.

   **Dispositie: fix nu.** Geef de opslagfout door aan de UI. Voeg een gerichte regressietest toe die bij een schrijffout een zichtbare afwijzing en géén succesmelding vereist; de nieuwe tests missen dit foutpad.

Verder geen onderbouwde blokkerende bevindingen. Aanvullende controles bevestigen dat gewijzigde bronmetadata/peildatum oude beoordelingen afwijzen en status-/versiewijzigingen zonder inhoudelijke verandering de binding behouden. De aangeleverde groene testlogs zijn gecontroleerd; de volledige suite is niet opnieuw gedraaid.

Expert Review’s eigen hervalidatie en de ontbrekende `definitie_drafts`-tabel zijn **aparte vervolgen**: zij blokkeren de onderzochte handmatige editor-P01-opslagroute niet. De echte browser-P01-proef blijft open.

Geen bestanden gewijzigd; werkboom blijft schoon op de opgegeven head.