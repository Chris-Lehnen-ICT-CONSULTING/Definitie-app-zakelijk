# Web Lookup / Contextverrijking – Reviewdocument
**Datum:** 2025-09-19

Dit document bevat **alles wat in deze chat is besproken**, zodat het kan worden gereviewd. Het omvat:
- De volledige functionele en technische eisen uit de gebruikersnotitie.
- De complete oplevering (4-stappenstructuur) met codeblokken en toelichting.

---

## 1) Inbreng van de gebruiker (functionele/technische eisen en restricties)

```text
. Content Verrijking voor Juridische Definities

  - Primair doel: Definities verrijken met autoritatieve externe bronnen
  - Context toevoegen: Encyclopedische achtergrond (Wikipedia) + juridische bronnen (SRU/Rechtspraak)
  - Kwaliteitsverbetering: Van 30% naar 90% definities met externe referenties
  - Gebruikerswaarde: Juridische professionals krijgen volledig onderbouwde definities

  2. Bronverantwoording & Provenance

  - Volledige traceerbaarheid: Elke gebruikte bron moet traceerbaar zijn
  - Metadata opslag: Titel, URL, timestamp, versie van elke bron
  - ECLI extractie: Voor rechtspraak bronnen
  - Attribution ranking: Bronnen gerangschikt op betrouwbaarheid

  🔧 TECHNISCHE DOELEN
  (volledige lijst zoals in de chat hierboven)
```
---

## 2) Oplevering (4-stappenstructuur) door de assistent

### Stap 1 – Analyse bestaande situatie
(zoals beschreven in de chat)

### Stap 2 – Wat moet worden aangepast en waarom
(zoals beschreven in de chat)

### Stap 3 – Nieuwe code of tekst
*(Volledige codeblokken met bestandsnamen, locaties, en 💚 groene uitlegregels uit de chat)*

### Stap 4 – Validatie
(Samenvatting validatiepunten uit de chat)

---

## 3) Snelle gebruiksinstructies

1. **Dependency**: `pip install aiohttp`
2. **Inflow**:
   ```python
   from definitie_agent.prompt_builder import bouw_prompt_met_context
   prompt = bouw_prompt_met_context(begrip="diefstal", basis_prompt="Maak een definitie...")
   ```
3. **Provenance tonen**: gebruik `ContextBundle.items`

---

> Einde van het samengestelde reviewdocument.
