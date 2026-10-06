"""Herkennen of een tekst een begrip noemt (DEF-620).

Gedeeld door de webzoekactie (contextfilter) en de bronbibliotheek (RAG):
één definitie van "noemt het begrip", zodat beide kanalen dezelfde
relevantiepoort hanteren.

Regels (hoofdletterongevoelig):
- het begrip moet aan het begin van een woord staan;
- een (deel)woord van minder dan vijf tekens moet een heel woord zijn
  (zodat "om" niet in "omstandigheden" treft); een langer woord mag een
  achtervoegsel hebben (meervoud, samenstelling, vervoeging);
- een begrip van meer woorden telt als genoemd als de hele term voorkomt,
  of als elk woord van minstens vier tekens voorkomt (alleen bij twee of
  meer zulke woorden).
"""

from __future__ import annotations

import re


def _patroon(woord: str) -> re.Pattern[str]:
    einde = r"(?!\w)" if len(woord) < 5 else ""
    return re.compile(r"(?<!\w)" + re.escape(woord) + einde, re.IGNORECASE)


def _schoon(term: str | None) -> str:
    return " ".join((term or "").split()).lower()


def noemt_term(tekst: str | None, term: str | None) -> bool:
    """True als ``tekst`` het begrip ``term`` noemt volgens de moduleregels."""
    return tel_treffers(tekst, term) > 0


def tel_treffers(tekst: str | None, term: str | None) -> int:
    """Aantal keren dat ``tekst`` het begrip noemt (0 = niet genoemd).

    Voor de terugval bij meerwoordige termen (alle lange woorden los aanwezig)
    telt het minimum van de losse woordtellingen.
    """
    begrip = _schoon(term)
    inhoud = tekst or ""
    if not begrip or not inhoud:
        return 0
    heel = len(_patroon(begrip).findall(inhoud))
    if heel:
        return heel
    woorden = [w for w in begrip.split() if len(w) >= 4]
    if len(woorden) < 2:
        return 0
    return min(len(_patroon(w).findall(inhoud)) for w in woorden)


_MIN_STAM = 6


def zoekvormen(term: str | None) -> list[str]:
    """Het begrip plus een lichte stamvorm voor naamwoorden op ``-ing``.

    Wetteksten gebruiken vaak het werkwoord in plaats van het zelfstandig
    naamwoord ("zich onttrekt", "onttrekken" bij het begrip "onttrekking").
    Voor een (laatste) woord op ``-ing`` komt de stam erbij: ``-ing`` eraf en
    een verdubbelde slotmedeklinker enkel ("onttrekking" → "onttrek",
    "inbeslagneming" → "inbeslagnem", "dagvaarding" → "dagvaard"). Alleen als
    de stam minstens zes tekens heeft, zodat korte, brede stammen ("regel",
    "toets") niet ontstaan. Alleen bedoeld voor de bronbibliotheek; het
    webfilter gebruikt ``noemt_term`` op het begrip zelf.
    """
    begrip = _schoon(term)
    if not begrip:
        return []
    vormen = [begrip]
    woorden = begrip.split()
    laatste = woorden[-1]
    if laatste.endswith("ing"):
        stam = laatste[:-3]
        if len(stam) >= 2 and stam[-1] == stam[-2] and stam[-1] not in "aeiou":
            stam = stam[:-1]
        if len(stam) >= _MIN_STAM:
            vormen.append(" ".join([*woorden[:-1], stam]))
    return vormen
