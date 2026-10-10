**Oordeel: akkoord op de exact begrensde uitzondering en het behoud van de bestaande regressietests.** Geen blokkerende bevinding in de vierbestandsdiff. A en B zijn bevestigd; beide krijgen dispositie **fix nu**, zonder verruiming van de uitzondering. Review zelfstandig uitgevoerd, zonder herdelegatie.

**Bevinding A — LOW, vooraf bestaande vacuüme zelfscan.**  
Locatie: [test_secret_scan_metadata.py:251](/private/tmp/def835-wp2-review-20260927/scripts/ci/test_secret_scan_metadata.py:251).

De test scant configuratietekst onder `.gitleaks.toml`. De standaardconfig van de gepinde scanner sluit paden met `gitleaks\.toml` uit; `sources/common.go` past die uitsluiting vóór inhoudsdetectie toe. Het controlebestand laat de bestaande eis `scanned_bytes > 0` alsnog slagen. Het uitvoerdersverslag rapporteert hierbij 14 gelezen bytes tegenover 8.558 op een neutraal pad.

De nieuwe module scant terecht op een neutraal pad en vereist minstens de volledige configuratieomvang. Die test slaagt in mijn eigen run; de behouden mutatieproef laat hem daadwerkelijk falen bij herkenbare configuratie-inhoud.

**Minimale correctie:** laat dezelfde uitvoerder de bestaande zelfscan eveneens een neutraal pad en passende bytecontrole gebruiken, met feitelijk juiste toelichting. Dit is het voorgestelde vijfde bestand. Geen detectieregel wijzigen. Niet blokkerend voor deze uitzondering, omdat de nieuwe test de gehele actuele configuratietekst al controleert.

**Bevinding B — LOW, te stellige commentaarreden.**  
Locaties: [.gitleaks.toml:98](/private/tmp/def835-wp2-review-20260927/.gitleaks.toml:98) en [test_secret_scan_def835_metadata.py:279](/private/tmp/def835-wp2-review-20260927/scripts/ci/test_secret_scan_def835_metadata.py:279).

Het commentaar verwijst voor `[f]` naar de noodzaak zelfdetectie te voorkomen. De brongebonden mutatieproef bewijst echter: zonder tekenklasse blijven alle 22 tests groen zolang `async_api\.py` behouden blijft. Pas zonder escape én tekenklasse faalt de neutrale zelfscan.

**Minimale correctie:** behoud `[f]` conform de opdracht, maar beschrijf dit als aanvullende schrijfwijze overeenkomstig de bestaande constructie, niet als noodzakelijke voorwaarde onder deze scanner/configuratie. Verduidelijk dat de zelfscan configuratietekst op een neutraal pad betreft. Geen stilistische blocker.

**Contractcontrole**

- `targetRules = ["generic-api-key"]` koppelt de uitzondering daadwerkelijk aan die detectieregel; de gepinde scannerbron bevestigt de AND-evaluatie van pad en inhoud.
- Beide volledige, verankerde manifestpaden stemmen exact overeen met het voorstel.
- De inhoudsregex stemt exact overeen met de geaccordeerde regel: zes spaties, dubbele quotes, volledige bronhash en afsluitende komma. Alleen één optionele voorafgaande LF is toegestaan.
- Geen nieuwe padskip, wildcard, prefix-/suffixuitzondering, disablement of generieke regelversoepeling.
- De bronhash is onafhankelijk opnieuw gelijk bevonden aan `src/utils/async_api.py`.
- Chris Lehnen en herreviewdatum **2026-12-28**, of eerder bij gewijzigde bronhash/manifestroute, staan vastgelegd. Geen credentialrotatieclaim.
- Na weglaten van uitsluitend de derde allowlist is de geparste configuratie gelijk aan de basisconfiguratie.
- Makefile behoudt alle eerdere suites en vlaggen; uitsluitend het nieuwe testpad en de telling zijn toegevoegd.
- Het runbook behoudt beide eerdere uitzonderingen en alle gatevoorwaarden. De nieuwe beschrijving suggereert geen ruimere werking.

**Verificatie en bewijs**

Zelf uitgevoerd: **22/22 canaries geslaagd, exit 0**, tegen de actuele projectconfig en de aangewezen binary, met de aangewezen project-Python. Getest zijn beide exacte combinaties, eerste regel/voorafgaande newline, afwijkende paden, gewijzigde hash, extra tekst, synthetische credential op hetzelfde pad, extra credential op een andere regel, neutrale configuratiescan en twee staged-fixturegevallen.

Eigen nieuwe fixturemap en uitvoer: [canaries.log](/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def835-codex-exact-review-aqox45gx/canaries.log). Log-SHA256: `01e3b2da0775c420fd53cba35eb07bcbce6bb36f8627e4b66278f20e9b10eddd`.

Gebruikte binary-SHA256: `234799752bba02184d76b3014958966da01cede3a081bbd84e0497c27e197b7a`. De bijbehorende broncheckout staat op pin `fb5d707e08fe0d2578b155458fdd53b6782dcab2`; de binary geeft bij `version` de buildplaceholder terug.

Behouden bewijs gecontroleerd:

- Gedragsmatige RED: acht falende tests, exit 1, tegen de oorspronkelijke projectconfig.
- Definitieve mutatieproef zonder uitzondering: dezelfde acht failures op de definitieve testmodule; de configuratie zonder derde uitzondering is inhoudelijk gelijk aan de basis.
- Definitieve GREEN: 22 geslaagd, exit 0.
- Vaste suite: 105 geslaagd, exit 0. Config-, Makefile- en modulehashes komen overeen; bestaande suites, scanneronderdelen en testconfiguratie zijn gelijk aan uitvoerderswerkboom en basis.

Geen volledige suite of mutatiematrix opnieuw gedraaid.

**Exacte reviewidentiteit**

Basis: `979ca0585100d94b613829d924c6d8bba4f24f1b`.

Manifest-SHA256: `d7b2796f4491a93cd14be35a2d49ba4bca4eede1ff7edb0e323e2765e040a3e0`.

Patch-SHA256: `b8c64722488fef4f85f47baf5e8599bca406a35fe89bda0ee38c61e61e058047`.

| Bestand | Gecontroleerde SHA256 |
|---|---|
| `.gitleaks.toml` | `8bb3a2799b485b7798f88bd6c96848f7e1075a99723e3832a7be3c53e821d812` |
| `Makefile` | `1083b45bcf7ba358862e887771418cbe3619d966f9132f140c151d4dd35fae49` |
| `docs/technisch/def522-secret-scan-runbook.md` | `cd485f28bebcbe705623fa856a77a5c8e2af20be9e672cf61e11608376e1067b` |
| `scripts/ci/test_secret_scan_def835_metadata.py` | `77d803cca30840e51cef895374c5c07230e0781453e46e97c9105d2eabb29aaa` |

De patch reconstrueert vanuit de basis exact deze vier bestanden. WP5a is buiten deze review gehouden. Geen bronbestanden of tests gewijzigd; de reviewwerkboomindex is byte-identiek gebleven. Fixturehandelingen vonden uitsluitend in nieuwe synthetische repositories plaats.

De coördinator laat A/B gericht corrigeren en hervat daarna de normale staged-gate op de volledige index. Deze review en lokale canaries vormen **geen full-history-cleanclaim**.