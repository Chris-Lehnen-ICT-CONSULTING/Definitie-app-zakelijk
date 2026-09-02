"""Readiness van de toetsregelset (DEF-621).

De volledigheidsbepaling in `toetsregels.rule_cache` vergelijkt het aantal
geladen regels met het aantal bestanden op schijf. Die vergelijking is
tautologisch zodra bestanden ontbreken: verdwijnen er 46 van de 53, dan geldt
`7 == 7` en meldt de cache volledigheid. Bij nul bestanden geldt `0 == 0` en
presenteert een lege regelset zich als compleet.

Deze module vervangt die telling door een **verzamelingsvergelijking** tegen de
contractuele regel-ID-set uit de root-SSOT. Alleen als de geladen ID's exact
gelijk zijn aan de verwachte ID's — en die verwachting niet leeg is — mag een
validatie een oordeel produceren.

Daarnaast levert deze module de fingerprint waarmee `ModularValidationService`
per aanroep beide overgangen ziet: compleet→incompleet én incompleet→hersteld.
De fingerprint dekt zowel de regelbestanden als de contract-SSOT, omdat juist
die laatste de verwachte ID-set bepaalt.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.validation.interfaces import UNKNOWN_REASON_RULESET_INCOMPLETE
from toetsregels.runtime_contract import RuleRecord, canonical_rule_id

__all__ = [
    "RuntimeSnapshot",
    "ValidationReadiness",
    "bepaal_readiness",
    "bereken_fingerprint",
    "veilige_degradatiereden",
]


# Een absoluut pad van minstens twee segmenten, als vangnet voor paden die
# alleen in vrije tekst voorkomen. De lookbehind eist een scheidingsteken
# ervóór, zodat een relatief pad niet half wordt opgegeten: in `mapé/a/b.json`
# mag `/a/b.json` niet los matchen. Een lijst van verboden voorlopers volstond
# daar niet, want die was ASCII-only.
_ABSOLUUT_PAD = re.compile(r"(?<![^\s'\"(\[:,=])(?:/[^/\s'\"]+){2,}")


def _basisnaam(pad: str) -> str:
    """De bestandsnaam, ongeacht of het pad POSIX- of Windows-scheiders heeft."""
    return re.split(r"[\\/]", pad)[-1] or pad


def _foutketen(oorzaak: BaseException) -> Iterable[BaseException]:
    """De fout zelf plus de fouten waarin zij verpakt zit.

    Het laadpad vangt een `OSError` en gooit een `RuleContractError` met het
    pad in de boodschap. Die buitenste fout draagt geen `filename`, dus wie
    alleen daarnaar kijkt vindt niets en laat het pad staan. De oorspronkelijke
    fout draagt het pad wél gestructureerd; die is via `__cause__` bereikbaar.

    De `gezien`-set is geen overdaad: `__context__` kan naar een fout wijzen
    die zelf al eerder in de keten voorkwam, en dan loopt een naïeve wandeling
    rond.
    """
    gezien: set[int] = set()
    huidig: BaseException | None = oorzaak
    while huidig is not None and id(huidig) not in gezien:
        gezien.add(id(huidig))
        yield huidig
        huidig = huidig.__cause__ or huidig.__context__


@dataclass(frozen=True)
class ValidationReadiness:
    """Of de geladen regelset het contract dekt.

    `expected_rule_ids` en `loaded_rule_ids` staan in genormaliseerde vorm
    (zie `canonical_rule_id`); `missing_rule_ids` en `unexpected_rule_ids`
    dragen de oorspronkelijke schrijfwijze, zodat een melding leesbaar blijft.
    """

    ready: bool
    expected_rule_ids: frozenset[str]
    loaded_rule_ids: frozenset[str]
    missing_rule_ids: tuple[str, ...]
    unexpected_rule_ids: tuple[str, ...]
    reason: str | None

    def als_dict(self) -> dict[str, object]:
        """De vorm die in `ValidationResult.validation_readiness` landt."""
        return {
            "ready": self.ready,
            "expected_total": len(self.expected_rule_ids),
            "loaded_total": len(self.loaded_rule_ids),
            "missing_rule_ids": list(self.missing_rule_ids),
            "unexpected_rule_ids": list(self.unexpected_rule_ids),
        }


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Alle ruleset-afhankelijke gegevens van een generatie, in een object.

    Het evaluatiepad leest naast `rule_records` ook de interne regelvolgorde,
    de gewichten, de ruwe JSON-regels, de patrooncache en de contractuele
    ID-set. Stonden die als losse velden op de service, dan kon een
    herlaadpoging een mengsel van twee generaties opleveren: nieuwe records
    met oude gewichten. Een snapshot maakt dat onmogelijk - hij wordt in zijn
    geheel gepubliceerd met een enkele attribuuttoewijzing.

    `frozen=True` bevriest de verwijzingen, niet de inhoud. Daarom zijn
    `contract_rule_ids` en `internal_rules` tuples, en zijn de drie mappings
    alleen-lezen views over dictionaries die alleen deze snapshot bezit. Een
    schrijfpoging faalt met `TypeError` in plaats van stil een gepubliceerde
    generatie te wijzigen.

    `pattern_cache` is de enige bewust muteerbare collectie: elke generatie
    krijgt een eigen dict, zodat een herbouwde regelset nooit gecompileerde
    patronen van een inmiddels verdwenen regel erft. Hij wordt met de
    snapshot weggegooid.

    Buiten deze snapshot blijven registry, repository, thresholds en
    cleaning-service: die hangen niet aan de regelset.
    """

    fingerprint: str | None
    readiness: ValidationReadiness
    contract_rule_ids: tuple[str, ...]
    internal_rules: tuple[str, ...]
    rule_records: Mapping[str, RuleRecord]
    json_rules: Mapping[str, dict[str, Any]]
    default_weights: Mapping[str, float]
    pattern_cache: dict[str, Any]
    rules_loaded_count: int
    rules_expected_count: int
    is_degraded_mode: bool
    degradation_reason: str | None


def _index(ids: Iterable[str]) -> dict[str, str]:
    """Canonieke ID -> oorspronkelijke schrijfwijze."""
    return {canonical_rule_id(rid): str(rid) for rid in ids if str(rid).strip()}


def bepaal_readiness(
    expected: Iterable[str], loaded: Iterable[str]
) -> ValidationReadiness:
    """Vergelijk verzamelingen, niet aantallen.

    Een lege verwachte set betekent dat het contract niet gelezen kon worden.
    Dat is nooit "compleet": zonder verwachting valt volledigheid niet vast te
    stellen, en stil doorgaan zou precies de tautologie herhalen die deze
    module vervangt.
    """
    # Eén keer materialiseren: de invoer mag een generator zijn, en zowel de
    # index als de cardinaliteitsvergelijking hebben hem nodig.
    verwachte_ids = [str(rid) for rid in expected if str(rid).strip()]
    geladen_ids = [str(rid) for rid in loaded if str(rid).strip()]

    verwacht = _index(verwachte_ids)
    geladen = _index(geladen_ids)

    ontbreekt = tuple(verwacht[k] for k in sorted(set(verwacht) - set(geladen)))
    onverwacht = tuple(geladen[k] for k in sorted(set(geladen) - set(verwacht)))

    # Verzamelingen én aantallen. `_index` klapt twee schrijfwijzen van
    # hetzelfde ID samen (`ARAI-01` en `ARAI_01` worden allebei `ARAI01`), dus
    # een zuivere setvergelijking ziet 53 == 53 terwijl er 54 ID's zijn en
    # niemand weet welke van de twee geldt. Alleen de cardinaliteit ontmaskert
    # die botsing; `rule_cache.get_stats()` hanteert dezelfde eis.
    ready = (
        bool(verwacht)
        and set(verwacht) == set(geladen)
        and len(geladen_ids) == len(verwachte_ids)
    )

    return ValidationReadiness(
        ready=ready,
        expected_rule_ids=frozenset(verwacht),
        loaded_rule_ids=frozenset(geladen),
        missing_rule_ids=ontbreekt,
        unexpected_rule_ids=onverwacht,
        reason=None if ready else UNKNOWN_REASON_RULESET_INCOMPLETE,
    )


def veilige_degradatiereden(oorzaak: BaseException | None) -> str | None:
    """De reden van degradatie, met absolute paden teruggebracht tot hun naam.

    `degradation_reason` is geen logveld: `get_health_status`, het
    `validation_unknown`-resultaat en uiteindelijk de banner in
    `definition_generator_tab` dragen hem naar het scherm. Een OS-fout geeft
    daar het volledige pad mee, en dat begint op een gebruikersmachine met de
    accountnaam.

    In de log blijft het pad juist wél staan — DEF-580 haalde paden bewust uit
    de redactieregels omdat tracebacks anders onleesbaar worden. Deze functie
    dicht daarom alleen het schermpad, niet de logketen.

    De bestandsnaam blijft behouden: weten dát `ARAI-01.json` ontbreekt is de
    bruikbare helft van de melding, de mappen erboven zijn dat niet.
    """
    if oorzaak is None:
        return None

    tekst = str(oorzaak)

    # Een OS-fout draagt zijn pad gestructureerd mee. Een letterlijke
    # vervanging daarvan is exacter dan welk patroon over vrije tekst ook: een
    # spatie in een mapnaam (`/Volumes/Team Share/...`) breekt een regex
    # halverwege en laat juist het staartstuk met de accountnaam staan, en een
    # Windows-pad ontsnapt volledig omdat het geen schuine strepen heeft.
    # `OSError.__str__` zet het pad er met `repr()` in, dus backslashes staan
    # er verdubbeld in terwijl `filename` ze enkel draagt. Beide vormen
    # vervangen, anders glipt juist het Windows-pad er ongeschonden door.
    for fout in _foutketen(oorzaak):
        for attribuut in ("filename", "filename2"):
            pad = getattr(fout, attribuut, None)
            if isinstance(pad, bytes):
                pad = os.fsdecode(pad)
            if not isinstance(pad, str) or not pad:
                continue
            basisnaam = _basisnaam(pad)
            for variant in {pad, repr(pad)[1:-1]}:
                tekst = tekst.replace(variant, basisnaam)

    return _ABSOLUUT_PAD.sub(lambda treffer: Path(treffer.group(0)).name, tekst)


def bereken_fingerprint(bronnen: Iterable[Path]) -> str:
    """Goedkope wijzigingsdetector over regelbestanden én contract-SSOT.

    Per bron `(pad, grootte, mtime_ns)`, gesorteerd, naar één hash. Een
    ontbrekende bron krijgt een eigen markering, zodat verdwijnen én
    terugkomen allebei een andere fingerprint opleveren.

    Bekende grens, bewust: een bestand dat corrupt raakt met identieke grootte
    én mtime ontsnapt hieraan. Dit is een wijzigingsdetector; de contract-
    validatie bij het herlezen blijft de inhoudelijke autoriteit. Een
    inhoudshash per validatie zou niet in verhouding staan tot dat randgeval.
    """
    delen: list[str] = []
    for pad in sorted({Path(p) for p in bronnen}, key=str):
        try:
            st = pad.stat()
        except OSError:
            delen.append(f"{pad}|-|-")
        else:
            delen.append(f"{pad}|{st.st_size}|{st.st_mtime_ns}")

    return hashlib.sha256("\n".join(delen).encode("utf-8")).hexdigest()
