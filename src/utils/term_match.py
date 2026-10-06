"""Herkennen of een tekst een begrip noemt (DEF-620).

Twee gebruikers, bewust gescheiden:

- ``noemt_term``: het contextfilter van de webzoekactie. Exact de semantiek
  van het oorspronkelijke ``_noemt_begrip`` (DEF-620 web): term en tekst met
  ``str.lower()``, hoofdlettergevoelige regex op de verlaagde tekst, geen
  verdere normalisatie, geen stamvormen.
- ``zoekpatronen`` + ``tel_treffers_rag``: de relevantiepoort van de
  bronbibliotheek (RAG fase 1). Normaliseert term én fragment
  (``normaliseer_zoektekst``: Unicode/ligaturen, zachte afbreekstreepjes,
  pdf-afbrekingen, witruimte) en herkent naast het begrip ook vervoegde
  woordvormen van naamwoorden op ``-ing``, maar alleen als héél woord.

Regels voor het begrip zelf (beide gebruikers):
- het begrip moet aan het begin van een woord staan;
- een woord van minder dan vijf tekens moet een heel woord zijn (zodat "om"
  niet in "omstandigheden" treft); een langer woord mag een achtervoegsel
  hebben (meervoud, samenstelling);
- een begrip van meer woorden telt als genoemd als de hele term voorkomt, of
  als elk woord van minstens vier tekens voorkomt (alleen bij twee of meer
  zulke woorden).
"""

from __future__ import annotations

import re
import unicodedata

# --- webfilter: oorspronkelijke semantiek -----------------------------------


def _staat_erin_web(woord: str, tekst: str) -> bool:
    einde = r"(?!\w)" if len(woord) < 5 else ""
    patroon = r"(?<!\w)" + re.escape(woord) + einde
    return re.search(patroon, tekst) is not None


def noemt_term(tekst: str | None, term: str | None) -> bool:
    """True als ``tekst`` het begrip ``term`` noemt (semantiek webfilter)."""
    begrip = (term or "").strip().lower()
    if not begrip:
        return False
    inhoud = (tekst or "").lower()
    if not inhoud:
        return False
    if _staat_erin_web(begrip, inhoud):
        return True
    woorden = [w for w in begrip.split() if len(w) >= 4]
    return len(woorden) > 1 and all(_staat_erin_web(w, inhoud) for w in woorden)


# --- bronbibliotheek: normalisatie + woordvormen ----------------------------

_ZACHT_AFBREEKSTREEPJE = "­"
# "ont-\ntrekking" (afbreking aan regeleinde, kleine letter erna) → "onttrekking".
_PDF_AFBREKING = re.compile(r"(\w)-[ \t]*\r?\n[ \t]*(?=[a-zà-ÿ])")
_WITRUIMTE = re.compile(r"\s+")
_KLINKERS = "aeiou"
_MIN_STAM = 6
# Herkenningsteken van het (verankerde) terugvalpatroon voor meerwoordige termen.
_TERUGVAL_PREFIX = r"\A"


def normaliseer_zoektekst(tekst: str | None) -> str:
    """Zoekrepresentatie van een tekst (de brontekst zelf blijft ongewijzigd).

    NFKC (ligaturen als "ﬁ" → "fi", samengestelde tekens als "o"+"¨" → "ö",
    harde spatie → spatie), zachte afbreekstreepjes weg, pdf-afbreking aan een
    regeleinde samengevoegd, alle witruimte één spatie, kleine letters. Een
    gewone regelovergang zonder streepje blijft een woordscheiding.
    """
    if not tekst:
        return ""
    t = unicodedata.normalize("NFKC", tekst).replace(_ZACHT_AFBREEKSTREEPJE, "")
    t = _PDF_AFBREKING.sub(r"\1", t)
    return _WITRUIMTE.sub(" ", t).strip().lower()


def _woordvormen_ing(woord: str) -> list[str]:
    """Vervoegde vormen bij een naamwoord op ``-ing`` (alleen hele woorden).

    "onttrekking" → onttrekt, onttrekte(n), onttrekken, onttrekkingen;
    "verklaring" → verklaart, verklaarde(n), verklaren; "dagvaarding" →
    dagvaardt, dagvaardde(n), dagvaarden. Geen kale stam en geen
    voorvoegselmatch, zodat "beschikking" niet "beschikbaar" treft en
    "handeling" niet "handelsregister".
    """
    if not woord.endswith("ing"):
        return []
    basis = woord[:-3]  # "onttrekk", "verklar", "dagvaard"
    stam = basis
    if len(stam) >= 2 and stam[-1] == stam[-2] and stam[-1] not in _KLINKERS:
        stam = stam[:-1]  # "onttrek"
    elif (
        len(stam) >= 3
        and stam[-1] not in _KLINKERS
        and stam[-2] in _KLINKERS
        and stam[-3] not in _KLINKERS
    ):
        stam = stam[:-2] + stam[-2] * 2 + stam[-1]  # "verklar" → "verklaar"
    if len(stam) < _MIN_STAM:
        return []
    t_of_d = "de" if stam[-1] in "dbgvzlmnrjw" or stam.endswith("aa") else "te"
    vormen = {
        stam + ("" if stam.endswith("t") else "t"),
        stam + t_of_d,
        stam + t_of_d + "n",
        basis + "en",
        woord + "en",
    }
    return sorted(vormen - {woord})


def zoekpatronen(term: str | None) -> list[re.Pattern[str]]:
    """Patronen waarmee de bronbibliotheek een vermelding van ``term`` herkent.

    Eerst het (genormaliseerde) begrip met de algemene regels; daarna, voor een
    laatste woord op ``-ing``, de vervoegde vormen als héél woord.
    """
    begrip = normaliseer_zoektekst(term)
    if not begrip:
        return []
    woorden = begrip.split()
    patronen = [_voorvoegsel_patroon(begrip)]
    lange = [w for w in woorden if len(w) >= 4]
    if len(lange) > 1:
        # Verankerd aan het begin van de tekst: treft hooguit één keer (één
        # vindplaats) en wordt niet op elke positie opnieuw geprobeerd.
        patronen.append(
            re.compile(
                _TERUGVAL_PREFIX
                + "".join(f"(?=.*{_voorvoegsel_patroon(w).pattern})" for w in lange),
                re.DOTALL,
            )
        )
    voor = " ".join(woorden[:-1])
    for vorm in _woordvormen_ing(woorden[-1]):
        volledig = f"{voor} {vorm}".strip()
        patronen.append(re.compile(r"(?<!\w)" + re.escape(volledig) + r"(?!\w)"))
    return patronen


def _voorvoegsel_patroon(woord: str) -> re.Pattern[str]:
    einde = r"(?!\w)" if len(woord) < 5 else ""
    return re.compile(r"(?<!\w)" + re.escape(woord) + einde)


def tel_treffers_rag(tekst: str | None, patronen: list[re.Pattern[str]]) -> int:
    """Aantal unieke vindplaatsen (startposities) van de patronen in ``tekst``.

    Patronen van één begrip die op dezelfde plek treffen, tellen één keer.
    De terugval voor meerwoordige termen (alle lange woorden los aanwezig)
    telt alleen als er geen andere vindplaats is, en dan als één.
    """
    inhoud = normaliseer_zoektekst(tekst)
    if not inhoud or not patronen:
        return 0
    posities: set[int] = set()
    terugval = False
    for patroon in patronen:
        if patroon.pattern.startswith(_TERUGVAL_PREFIX):
            terugval = terugval or patroon.search(inhoud) is not None
            continue
        for treffer in patroon.finditer(inhoud):
            posities.add(treffer.start())
    if posities:
        return len(posities)
    return 1 if terugval else 0
