**LOW-T08 gesloten; bronvrijgave voor deze correctie. Geen nieuwe bevestigde bevindingen.**

- In `src/domain/int01/zinsgrenzen.py:664–723` vervalt uitsluitend de extra onzekerheid bij een expliciet aangekondigd, afsluitend voorbeeldgetal na `bijv.`. De oorspronkelijke T08 behoudt exact dezelfde zekere grens, passage en reden na `12.`.
- Eigen schrijfvrije probes bevestigen: `bv. 12.`, `q.z. 12.`, `enz. 12.` en getallen met vervolgwoorden blijven onzeker. Voorbeeldcodes, citaatslot met komma/puntkomma zonder spatie, lijstcontext en kleineletteronzekerheid blijven behouden. De betrokken citaat- en lijstfuncties zijn AST-gelijk aan de base.
- `/1` tot en met `/9` worden niet-actueel; `/10` wordt toegepast bij passende tekst. Tekstwijziging maakt de uitkomst niet-actueel. De skillsdelta wijzigt uitsluitend de contractverwijzing.

Gelezen bewijs: RED **9/17**, GREEN **534**, regressie **1087 geslaagd**, integratie **27 geslaagd/1 skip**, gepinde Ruff/Black en make lint exit **0**. Zelf uitsluitend 16 gerichte probes, currentnesscontroles en AST-/hash-/patchcontroles uitgevoerd; geen suite herhaald.

De patches reconstrueren exact alle zeven manifestbestanden vanaf de opgegeven bases. Hashes vóór/na gelijk, geen drift:

| Artefact | SHA256 |
|---|---|
| Apppatch v4 | `42a0af26c21eacb00ed3fe9bce4f481a8caff07b895989bb352c4a4ae7c50489` |
| Skillspatch v4 | `c547c9e0aad507c3f245dce9e3d05dab0eabeed3f73eb2639fac6b6ef14dee44` |
| Manifest v4 | `c8276bd22ba88513dca563dce11801b2221963e893691f172468e6f66bfc84c8` |

**Begrenzing:** finale volledige gate blijft open. T17/T24 en hun historische referentie-afbakening blijven ongewijzigd open. Dit is bronvrijgave, geen acceptatie- of effectvrijgave. Geen edits.