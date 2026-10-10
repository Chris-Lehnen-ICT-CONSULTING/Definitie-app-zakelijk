**DEF-835 — herreview A/B: akkoord.** Beide bevindingen zijn gesloten. Geen nieuwe concrete bevindingen of regressies in de correctiedelta.

- **A gesloten:** [de bestaande zelfscan](/private/tmp/def835-wp2-review-20260927/scripts/ci/test_secret_scan_metadata.py:254) gebruikt nu een neutraal pad en vereist `scanned_bytes >= len(configtekst.encode("utf-8"))`. Het behouden RED-bewijs toont precies het oorspronkelijke probleem: 12 geslaagd, één gefaald doordat slechts 115 van de vereiste 8.544 bytes waren gelezen. De gecorrigeerde zelfscan slaagt ook onafhankelijk.
- **B gesloten:** configuratiecommentaar en nieuwe testdocstring beschrijven correct dat de geëscapete punt zelfdetectie hier al voorkomt; `[f]` is aanvullend. De geparste scannerconfig is aantoonbaar identiek aan de eerder beoordeelde versie. Detectiebereik en uitzonderingsvoorwaarden blijven gelijk.

**Verificatie**

Zelf beide zelfscantests uitgevoerd met de aangewezen gepinde scanner en project-Python, tegen de actuele configuratie, in een eigen nieuwe fixturemap: **2/2 geslaagd, exit 0**. [Testuitvoer](/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def835-codex-herreview-zan9gey8/zelfscans.log) en [verificatiegegevens](/var/folders/0y/443zs7b950b82xfzg4s_97x00000gn/T/def835-codex-herreview-zan9gey8/verificatie.json).

Het behouden uitvoerdersbewijs toont **35/35 groen, Ruff 0, Black 0**. De coördinatorherhaling bevestigt dezelfde resultaten; diens vijf bestandshashes komen exact overeen met manifest v2. Makefile en runbook zijn ongewijzigd sinds de eerste review. Geen nieuwe mutatiematrix of volledige 105-suite uitgevoerd.

**Identiteit**

Basis: `979ca0585100d94b613829d924c6d8bba4f24f1b`.

- Manifest v2 SHA256: `54b4624dafde86b1814c9cc8cbde9e190a07e808fdc810482826c5f79433b74e`
- Correctiedelta SHA256: `6e469e9c5f35a70f06618262e765406611576d14ffbe91a25ca7f814e93b6bf7`
- Volledige vijfbestandsdiff SHA256: `d579491ccb02aa3ceefec1cb8d1662ae13d33b3667a03391a45740d5314c4dd6`

Beide patches reconstrueren exact de eindbestanden: de delta vanuit de gecontroleerde herstelkopieën, de volledige diff vanuit de basis.

| Bestand | Eind-SHA256 |
|---|---|
| `.gitleaks.toml` | `5e74df0cc7dd29999e11ce4e5ebac0542d729ef4a340933fce88145d81219e1f` |
| `test_secret_scan_def835_metadata.py` | `1a0135c2de16ed7d84fa5f683ca574f76aecee1450cc4fc13ecb1962ab122041` |
| `test_secret_scan_metadata.py` | `f277d92320cf9579c5f08b87c86ba57437a19ec8d712f7594bb67c4832aa3516` |
| `Makefile` | `1083b45bcf7ba358862e887771418cbe3619d966f9132f140c151d4dd35fae49` |
| `def522-secret-scan-runbook.md` | `cd485f28bebcbe705623fa856a77a5c8e2af20be9e672cf61e11608376e1067b` |

Geen bron-/testwijzigingen of herdelegatie uitgevoerd. Eindhashes en reviewwerkboomindex zijn ongewijzigd gebleven. WP5a bleef buiten scope.

**De coördinator kan de gewone staged-gate op de volledige index hervatten.** Dit oordeel is geen full-history-cleanclaim.