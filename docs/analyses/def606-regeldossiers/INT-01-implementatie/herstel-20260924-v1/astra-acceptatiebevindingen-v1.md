**Beide nieuwe acceptatieafwijkingen bevestigd. T24 haalt de vastgelegde acceptatie niet.** De eerdere bronvrijgave voor R1/R2 blijft geldig binnen haar scope.

1. **T20 — Important: dekkingsafwijking.**  
   De nominale voortzetting `met de kleurcode van de bijbehorende opdracht` valt buiten het betwiste *waar + voorzetsel*-patroon. De verzegelde automatische `pass` wordt dus niet door het titelbesluit vervangen door onzekerheid.  
   De concrete oorzaak staat in [_voorzetselgroepen:744](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:744): per voorzetselgroep accepteert de code hoogstens een lidwoord en één kernwoord. Daardoor strandt `van de bijbehorende opdracht`; zonder `bijbehorende` accepteert dezelfde helper de voortzetting wel. De volledige tekst reproduceert `review_required` bij het citaatslot. Dit is een aantoonbare herkenningsbeperking, geen vastgesteld referentieconflict.  
   **Dispositie: open blocker binnen DEF-770, geen waiver.**

2. **T22 — Important: onbewezen positieve zinsstructuurclaim.**  
   `schakelblad` levert geen zekere of onzekere grens op. De labelcontrole herkent uitsluitend een afsluitende dubbele punt; vervolgens maakt [_grensdelen:872](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/src/domain/int01/zinsgrenzen.py:872) van het ontbreken van signalen automatisch `zinsstructuur: pass`. Positief bewijs voor een definitieformulering ontbreekt bij dit losse begripslabel.  
   De reproductie bevestigt die deelclaim. **Het totale INT-01-oordeel blijft `review_required`**, met compactheid en begrijpelijkheid open.  
   **Dispositie: open blocker binnen DEF-770, geen waiver.**

De coördinatormapping klopt: **13 pass, 6 fail, 4 review_required, 1 not_evaluated** op de zinsstructuuras; **22/24 statusconform**, **18 van 19 automatische beslissingen normatief ondersteund**. Lege tekst is terecht niet beoordeeld. Beide laadpaden en opgeslagen onderdelen/status zijn voor alle 24 consistent.

Voor de overige 22 gevallen dragen de aanwezige redenen, grenspassages en broncitaatstatus de conformiteit; ik vond geen extra afwijking. Bij T14 is witruimte in de apppassage genormaliseerd, maar blijft dezelfde grens herkenbaar. De twee blockers verhinderen zowel volledige contractconformiteit als de eis van nul onbewezen zekere beslissingen.

Bewijsbinding gecontroleerd: commit `23cc51bfddc5ee9393dea52e6a52a55b3e65615d`, bronarchief, sleutelbestanden en alle verzegelingshashes komen overeen. Basis: [verzegelde adjudicatie](/Users/chrislehnen/.codex/worktrees/ac84/Definitie-app/docs/analyses/def606-regeldossiers/INT-01-implementatie/effectproeven-vervolg-20260924-v1/t24-adjudicatie-v1.json) en ruwe runneruitkomsten. Zelf uitgevoerd: twee classifierreproducties, één lokale helpervergelijking en programmatische hertelling/ketencontrole.

Geen wijzigingen, herstelpoging of nieuwe proef gestart. Geen T24-acceptatievrijgave of G24-effectvrijgave.