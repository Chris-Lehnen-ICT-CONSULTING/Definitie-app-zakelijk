---
id: US-237
epic: EPIC-004
titel: "US-237: - In de Expert Review‑tab een knop aanbieden waarmee de reviewer alle voorbeelden (voorbeeldzinnen, praktijkvoorbeeld..."
status: open
prioriteit: P2
story_points: 5
aangemaakt: 2025-09-30
bijgewerkt: 2025-09-30
owner: tbd
applies_to: definitie-app@current
canonical: false
last_verified: 2025-09-30
---

id: US-237
titel: Expert Review – Reset naar DB‑versie (voorbeelden)

Doel
- In de Expert Review‑tab een knop aanbieden waarmee de reviewer alle voorbeelden (voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden, synoniemen, antoniemen, toelichting) kan resetten naar de laatst opgeslagen versie in de database, waarbij de huidige sessie‑aanpassingen worden overschreven.

Waarom
- Reviewers willen snel kunnen terugvallen op de laatst bekende ‘goede’ (of reeds beoordeelde) voorbeelden wanneer tussentijdse mutaties of experimenten onwenselijk blijken.

Scope
- Locatie: Expert Review‑tab, sectie “📋 Definitie Details” → expander “✏️ Bewerk Voorbeelden”.
- Actie: “↩️ Reset naar DB‑versie”
  - Haalt voorbeelden op via repository (`get_voorbeelden_by_type(definitie_id)`).
  - Schrijft de opgehaalde waarden naar de sessie (SessionState), vervangt de in‑memory bewerkvelden.
  - Ververst de weergave zodat de gebruiker direct de DB‑versie ziet.
- Geen extra opslag naar DB bij reset (alleen laden); opslag blijft expliciet via “💾 Voorbeelden opslaan”.

UI/UX
- Knop: “↩️ Reset naar DB‑versie” naast “💾 Voorbeelden opslaan”.
- Confirm dialoog (optioneel): waarschuwt dat niet‑opgeslagen wijzigingen verloren gaan.
- Na reset: info‑melding “DB‑versie hersteld (niet opgeslagen)”.

Technisch
- Hergebruik van shared resolver is prima, maar reset forceert altijd `repository.get_voorbeelden_by_type()` → sessie overschrijven.
- Keys/structuur aansluiten op bestaande editor:
  - voorbeeldzinnen, praktijkvoorbeelden, tegenvoorbeelden: list[str]
  - synoniemen, antoniemen: list[str] (UI toont comma‑separated)
  - toelichting: str (optioneel — kan leeg zijn)

Acceptatiecriteria
- AC1: Reset haalt de huidige DB‑voorbeelden op en toont ze direct in de invoervelden.
- AC2: Niet‑opgeslagen sessiewijzigingen worden verworpen (alleen sessie, DB blijft ongewijzigd).
- AC3: Opslaan na reset schrijft de herstelde waarden naar de database.
- AC4: Bij afwezigheid van DB‑voorbeelden blijft de editor leeg en toont een informatieve melding (geen crash).

Out‑of‑scope
- Versiebeheer van voorbeelden (audit op recordniveau) – valt buiten deze US.
- Massaal terugdraaien in DB (harde revert) – blijft handmatig of toekomstige US.

Risico’s / Randgevallen
- Editor met ongeldige input → reset verliest die input; confirm dialoog minimaliseert verrassingen.
- DB en sessie out‑of‑sync – reset forceert juistheid vanuit DB.

Testcases
- TC1: Na lokale bewerking klik op reset → velden tonen DB‑waarden (geen writes naar DB).
- TC2: Reset gevolgd door “Opslaan” → DB bevat nieuwe set gelijk aan getoonde velden.
- TC3: Lege DB‑set → velden worden leeg; melding zichtbaar.

Implementatiestappen (kort)
1) Expert Review‑tab: voeg knop “↩️ Reset naar DB‑versie” toe in voorbeelden‑editor.
2) Handler: `db_examples = repository.get_voorbeelden_by_type(definitie.id)` → map naar editor‑vorm → `SessionStateManager.set_value(ex_key, mapped)`.
3) UI refresh met melding.

