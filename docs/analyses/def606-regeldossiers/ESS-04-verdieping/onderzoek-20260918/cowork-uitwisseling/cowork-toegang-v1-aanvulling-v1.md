# cowork-toegang-v1-aanvulling-v1.md — correctie en nalevering

Claude Cowork, 18 september 2026. Aanvulling op `cowork-toegang-v1.md`; dat bestand blijft ongewijzigd.

## 1. Correctie op mijn eigen melding

In `cowork-toegang-v1.md` §4 en §7 meldde ik `src/services/import_service.py` als **ontbrekend** en noemde ik de ingang *import* daardoor onbewijsbaar.
Dat was onjuist. `nalevering-leeswijzer-v1.md` stelt terecht vast dat de betreffende regel in `werkboom-manifest-v1.json` `available=false` draagt
en dat de werkelijke service `src/services/definition_import_service.py` heet. Er ontbrak dus geen bestaand bestand; ik heb een expliciet
als niet-beschikbaar gemarkeerde manifestregel als ontbrekend gelezen. De conclusie die ik eraan verbond — geen codeleesbasis voor de importingang — is met de nalevering vervallen.

Ter controle, de betreffende manifestregel zoals hij er staat:

```json
{
  "path": "src/services/import_service.py",
  "available": false
}
```

## 2. Hashcontrole van de nalevering

Commit in manifest: `4cdb8ea43aa9b750326cbf8d9c8034db77f6eafb` — gelijk aan de bevroren codebasis `werkboom-4cdb8ea43`.

| Pad | SHA-256 (door mij herberekend) | Oordeel |
|---|---|---|
| `src/services/definition_import_service.py` | `dc603a3c018108159523eefaf4cab2401b8c775744c83e0f15d9a1ae27cf59c1` | GELIJK |
| `src/database/definitie_import_export.py` | `52a19a0bde8acadaa90700f500e1b84b8d8822056890e71a315a23b373d4b391` | GELIJK |
| `src/services/validation/result_contract.py` | `88490821672719fc966956a2e6956da79cf8457c86608bd6f132ebebf7d94e9f` | GELIJK |

Drie van drie aanwezig, leesbaar en hashgelijk. Geen bestand buiten het manifest.

- `nalevering-leeswijzer-v1.md` — sha256 `cbdc220a3b2b23535396ac1d7ac8eb4fa263ad4b40572d1a4fcaca7f224ffaa6`
- `nalevering-manifest-v1.json` — sha256 `673546929797fad924374be89b49a3afe6baaa0973518da5fbe25496a84bcf39`
- `astra-bronobservatie-v2.md` — sha256 `53f877563051a1404d5cf58780686c3b7b1385d8f0215888c3012c18794f4e86`

## 3. Wat de nalevering aan het onderzoek toevoegt

- `result_contract.py` **weerlegt** een hypothese die ik op grond van `mappers.py` en `types.py` had opgesteld: `review_required` staat in `CONTRACTVELDEN` en overleeft de resultaatconversies. Zie `cowork-onderzoek-v1.md` §5.3; ik noteer dit uitdrukkelijk als een door bewijs verworpen vermoeden.
- `definition_import_service.py` levert de codeleesbasis voor de ingang *import*: `cowork-onderzoek-v1.md` §5.6. Kern: `import_single` gebruikt `preview.ok` niet en bewaart de validatie-uitkomst niet bij het record.
- `definitie_import_export.py` is gelezen als database-import/exportlaag; geen ESS-04-specifieke logica aangetroffen.

## 4. ASTRA — zelf gelezen

`astra-bronobservatie-v2.md` is een gedeelde bronobservatie. Ik heb de pagina daarna **zelf** rechtstreeks geopend in de browser van deze sessie:
https://www.astraonline.nl/index.php/Toetsbaarheid . Pagina toegankelijk; geen CAPTCHA, geen beveiligingswaarschuwing, geen login.
Voetregel: "Deze pagina is voor het laatst bewerkt op 11 feb 2025 om 09:46." Aangeboden permanente link: `https://www.astraonline.nl/index.php?title=Toetsbaarheid&oldid=8558`.
De historische revisiepagina heb ik niet geopend; de onderliggende Politiebron evenmin. Mijn waarneming komt overeen met de gedeelde observatie;
de volledige veldweergave staat in `cowork-onderzoek-v1.md` §2.1.

Daarnaast zelf gelezen, in dezelfde sessie:
- https://www.astraonline.nl/index.php/Instanties_uniek_onderscheidbaar (ESS-03; de enige door ASTRA gelegde relatie bij ESS-04)
- https://jcgm.bipm.org/vim/en/1.30.html en https://jcgm.bipm.org/vim/en/2.1.html (VIM3 nominal property en measurement, inclusief de uitgeklapte notes en annotaties)
- https://docs.geostandaarden.nl/nl-sbb/nl-sbb/ — NL-SBB, kopregel "Vastgestelde versie 10 oktober 2024", §2.4.1.1 Termen en §2.4.1.2 Notities

## 5. Onafhankelijkheid

Bij het schrijven van `cowork-onderzoek-v1.md` zijn geen Codex-onderzoeksconclusies, kruisreviews of synthese gelezen; die staan niet in deze map.
Gelezen zijn uitsluitend de expliciet als bronmateriaal aangeboden stukken: het startpakket, de nalevering en `astra-bronobservatie-v2.md`.

## 6. Naleving

Alleen nieuwe bestanden geschreven: `cowork-toegang-v1.md`, dit bestand, `cowork-onderzoek-v1.md` en `cowork-bewijs-v1/`.
Geen bestaand bestand gewijzigd of verwijderd, niets extern gedeeld, geen productcode, database of actieve skill aangeraakt, geen issue, PR, automatisering, extra sessie of agent.
