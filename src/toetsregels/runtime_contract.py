"""Typed runtimecontract voor de JSON-toetsregels (DEF-606 / ADR-001).

`config/toetsregels/toetsregels_config.yaml` is de gezaghebbende root-SSOT;
de 53 JSON-bestanden onder `src/toetsregels/regels/` zijn de versioned
uitvoerbare regelrecords daaronder. Deze module maakt dat contract
afdwingbaar:

- iedere regel wijst precies één bekende evaluatorstrategie aan;
- iedere regel declareert expliciet welke invoer die strategie vereist;
- iedere regel draagt een uitvoerbaarheidsklasse, automatiseringsstatus en
  scorepolicy;
- afwijking tussen rootconfig, record en runtime faalt zichtbaar
  (`RuleContractError`) in plaats van stil een tweede waarheid te maken.

Bewust géén onderdeel van deze module: de evaluatorimplementaties zelf
(die leven achter het register in `services.validation.evaluators`) en de
promptmetadata in de records (uitleg, toelichting, voorbeelden) — die
blijven ongemoeid naast het uitvoerbare deel bestaan.
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "REGEX_PATROONVELDEN",
    "AutomationStatus",
    "EvaluatorType",
    "ExamplePairPolicy",
    "Executability",
    "RequiredInput",
    "ResultStatus",
    "RootContractPolicy",
    "RuleContractError",
    "RuleRecord",
    "ScorePolicy",
    "build_rule_record",
    "build_rule_records",
    "canonical_rule_id",
    "lees_regelbestand",
    "load_root_contract_policy",
    "missing_inputs",
    "root_contract_policy",
    "status_for_missing_inputs",
    "valideer_regelset",
]

CONTRACT_BLOCK = "runtime_contract"
PROVENANCE_BLOCK = "provenance"

# De gezaghebbende root-SSOT (ADR-001). Niet alleen documentatie: de
# waardesets hieronder worden bij laden tegen de Python-enums gelegd, zodat
# YAML en runtime niet stil uit elkaar kunnen lopen.
ROOT_CONFIG_PATH: Path = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "toetsregels"
    / "toetsregels_config.yaml"
)

_NIET_ALFANUMERIEK = re.compile(r"[^A-Z0-9]")

# De recordvelden die een evaluator als regex compileert. Compileerbaarheid
# hoort bij het contract en niet bij de evaluatie: de evaluators vingen
# `re.error` eerder zelf af met een lege patroonlijst, waardoor één
# onbruikbaar patroon álle patronen van de regel uitzette en de regel van
# falend naar geslaagd ging (DEF-667). Wie hier een veld bijzet, moet de
# verwachting in `test_rule_loader_failclosed.TestPatrooncontract`
# meebewegen; die lijst is bewust onafhankelijk opgeschreven.
REGEX_PATROONVELDEN: tuple[str, ...] = (
    "herkenbaar_patronen",
    "herkenbaar_patronen_particulier",
    "herkenbaar_patronen_proces",
    "herkenbaar_patronen_resultaat",
    "herkenbaar_patronen_type",
    "redundancy_patterns",
    "required_patterns",
)


class RuleContractError(ValueError):
    """Een regelrecord voldoet niet aan het runtimecontract."""


class EvaluatorType(StrEnum):
    """Gesloten set evaluatorstrategieën; één per regelrecord."""

    GENERIC = "generic"
    POSITIVE_INDICATOR = "positive_indicator"
    ABBREVIATION = "abbreviation"
    LEMMA_MORPHOLOGY = "lemma_morphology"
    DEFINITION_GRAMMAR = "definition_grammar"
    QUALIFICATION = "qualification"
    DEFINITION_OVERLAP = "definition_overlap"
    COMPOUND = "compound"
    DEFINITION_GRAPH = "definition_graph"
    PREFERRED_TERM = "preferred_term"
    SYNONYM_CONSISTENCY = "synonym_consistency"
    CONTEXT_METADATA = "context_metadata"
    ONTOLOGICAL_CATEGORY = "ontological_category"
    DUPLICATE_DETECTION = "duplicate_detection"
    JUDGMENT_REVIEW = "judgment_review"


class ExamplePairPolicy(StrEnum):
    """Hoe het gedocumenteerde goed/fout-paar als regressiecase telt."""

    NORMATIVE = "normative"
    REQUIRES_REPOSITORY = "requires_repository"
    REVIEW_POLICY = "review_policy"
    SOURCE_DEFECT = "source_defect"


class RequiredInput(StrEnum):
    """Gesloten set invoernamen die een evaluator kan vereisen."""

    DEFINITION_TEXT = "definition_text"
    TERM = "term"
    CONTEXT_LISTS = "context_lists"
    ONTOLOGICAL_CATEGORY = "ontological_category"
    DEFINITION_REPOSITORY = "definition_repository"
    SYNONYMS = "synonyms"
    PREFERRED_TERM = "preferred_term"
    RELATED_CONCEPTS = "related_concepts"


class Executability(StrEnum):
    """Hoe een regel überhaupt beoordeeld kán worden."""

    DETERMINISTIC = "deterministic"
    REPOSITORY = "repository"
    JUDGMENT = "judgment"
    NOT_AUTOMATABLE = "not_automatable"


class AutomationStatus(StrEnum):
    """Of de regel in runtime daadwerkelijk automatisch wordt beoordeeld."""

    AUTOMATED = "automated"
    REVIEW_REQUIRED = "review_required"
    NOT_EVALUATED = "not_evaluated"


class ScorePolicy(StrEnum):
    """Of de uitkomst meetelt in de kwaliteitsscore."""

    SCORED = "scored"
    EXCLUDED_FROM_SCORE = "excluded_from_score"


class ResultStatus(StrEnum):
    """Uitkomst van één regelevaluatie.

    Alleen `PASS` en `FAIL` zijn werkelijk uitgevoerde, betrouwbare
    beoordelingen; uitsluitend die twee mogen de kwaliteitsscore beïnvloeden.
    """

    PASS = "pass"
    FAIL = "fail"
    REVIEW_REQUIRED = "review_required"
    NOT_EVALUATED = "not_evaluated"
    ERROR = "error"

    @property
    def telt_mee_in_score(self) -> bool:
        return self in (ResultStatus.PASS, ResultStatus.FAIL)


@dataclass(frozen=True)
class RootContractPolicy:
    """De contractpolicy zoals de root-SSOT die vaststelt."""

    contract_required_fields: tuple[str, ...]
    record_required_fields: tuple[str, ...]
    rule_ids: tuple[str, ...]
    evaluators: tuple[str, ...]
    required_inputs: tuple[str, ...]
    executability: tuple[str, ...]
    automation_status: tuple[str, ...]
    score_policy: tuple[str, ...]
    result_status: tuple[str, ...]
    example_pair_policy: tuple[str, ...]


# YAML-sleutel -> (Python-enum, attribuutnaam op RootContractPolicy)
_WAARDESETS: tuple[tuple[str, type[StrEnum], str], ...] = (
    ("evaluators", EvaluatorType, "evaluators"),
    ("required_inputs", RequiredInput, "required_inputs"),
    ("executability", Executability, "executability"),
    ("automation_status", AutomationStatus, "automation_status"),
    ("score_policy", ScorePolicy, "score_policy"),
    ("result_status", ResultStatus, "result_status"),
    ("example_pair_policy", ExamplePairPolicy, "example_pair_policy"),
)

# De velden die `build_rule_record` in het contractblok afdwingt. De
# rootconfig moet exact deze set noemen; noemt zij er meer of minder, dan is
# de config geen bron van waarheid meer maar een afwijkende tweede mening.
_AFGEDWONGEN_CONTRACTVELDEN: frozenset[str] = frozenset(
    {
        "evaluator",
        "required_inputs",
        "executability",
        "automation_status",
        "score_policy",
    }
)


def _lijst(bron: Mapping[str, Any], sleutel: str, pad: Path) -> tuple[str, ...]:
    waarde = bron.get(sleutel)
    if not isinstance(waarde, list) or not waarde:
        msg = (
            f"{pad}: sectie '{CONTRACT_BLOCK}.{sleutel}' ontbreekt of is geen "
            f"niet-lege lijst (gevonden: {waarde!r})"
        )
        raise RuleContractError(msg)
    return tuple(str(item) for item in waarde)


def load_root_contract_policy(pad: Path | None = None) -> RootContractPolicy:
    """Lees en valideer de contractpolicy uit de root-SSOT.

    Faalt zichtbaar wanneer de YAML-waardesets afwijken van de Python-enums.
    Dat is geen formaliteit: zonder deze controle kan de rootconfig een
    evaluator of scorepolicy noemen die de runtime niet kent (of andersom),
    en dan bestaat er weer een tweede waarheid — precies wat ADR-001
    uitsluit.
    """
    pad = pad or ROOT_CONFIG_PATH
    try:
        ruw = yaml.safe_load(pad.read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"{pad}: root-SSOT niet leesbaar: {exc}"
        raise RuleContractError(msg) from exc
    except yaml.YAMLError as exc:
        msg = f"{pad}: root-SSOT bevat ongeldige YAML: {exc}"
        raise RuleContractError(msg) from exc

    if not isinstance(ruw, Mapping):
        msg = f"{pad}: root-SSOT is geen mapping"
        raise RuleContractError(msg)

    sectie = ruw.get(CONTRACT_BLOCK)
    if not isinstance(sectie, Mapping):
        msg = (
            f"{pad}: sectie '{CONTRACT_BLOCK}' ontbreekt; de rootconfig wijst dan "
            f"geen contractpolicy aan"
        )
        raise RuleContractError(msg)

    fouten: list[str] = []
    waarden: dict[str, tuple[str, ...]] = {}
    for sleutel, enum_type, attribuut in _WAARDESETS:
        gedeclareerd = _lijst(sectie, sleutel, pad)
        waarden[attribuut] = gedeclareerd
        bekend = {lid.value for lid in enum_type}
        alleen_yaml = sorted(set(gedeclareerd) - bekend)
        alleen_runtime = sorted(bekend - set(gedeclareerd))
        if alleen_yaml:
            fouten.append(
                f"'{CONTRACT_BLOCK}.{sleutel}' noemt waarden die de runtime niet "
                f"kent: {alleen_yaml}"
            )
        if alleen_runtime:
            fouten.append(
                f"'{CONTRACT_BLOCK}.{sleutel}' mist waarden die de runtime wel "
                f"kent: {alleen_runtime}"
            )

    contractvelden = _lijst(sectie, "required_fields", pad)
    if set(contractvelden) != _AFGEDWONGEN_CONTRACTVELDEN:
        fouten.append(
            f"'{CONTRACT_BLOCK}.required_fields' {sorted(contractvelden)} wijkt af "
            f"van wat de runtime afdwingt {sorted(_AFGEDWONGEN_CONTRACTVELDEN)}"
        )

    recordvelden = _recordvelden(ruw, pad)

    rule_ids = _lijst(sectie, "rule_ids", pad)
    duplicaten = sorted({rid for rid in rule_ids if rule_ids.count(rid) > 1})
    if duplicaten:
        fouten.append(f"'{CONTRACT_BLOCK}.rule_ids' bevat duplicaten: {duplicaten}")

    if fouten:
        msg = f"{pad}: root-SSOT en runtime lopen uiteen:\n- " + "\n- ".join(fouten)
        raise RuleContractError(msg)

    return RootContractPolicy(
        contract_required_fields=contractvelden,
        record_required_fields=recordvelden,
        rule_ids=rule_ids,
        **waarden,
    )


def _recordvelden(ruw: Mapping[str, Any], pad: Path) -> tuple[str, ...]:
    """Verplichte topvelden per regelrecord, uit loading.formats.json."""
    formats = ((ruw.get("loading") or {}).get("formats") or {}).get("json") or {}
    velden = formats.get("required_fields")
    if not isinstance(velden, list) or not velden:
        msg = (
            f"{pad}: 'loading.formats.json.required_fields' ontbreekt of is geen "
            f"niet-lege lijst"
        )
        raise RuleContractError(msg)
    return tuple(str(veld) for veld in velden)


@functools.lru_cache(maxsize=1)
def root_contract_policy() -> RootContractPolicy:
    """Gecachete policy uit de root-SSOT (load-once per proces)."""
    return load_root_contract_policy()


def canonical_rule_id(waarde: str) -> str:
    """Normaliseer een rule-ID tot zijn vergelijkbare vorm.

    De records gebruiken historisch drie schrijfwijzen door elkaar:
    `CON-01` (bestandsnaam), `CON_01` (veld `id`) en `ARAI01` (de negen
    ARAI-records). Voor identiteitsvergelijking tellen alleen de
    alfanumerieke tekens.
    """
    return _NIET_ALFANUMERIEK.sub("", str(waarde or "").upper())


@dataclass(frozen=True)
class RuleRecord:
    """Eén uitvoerbaar regelrecord met zijn gevalideerde contract."""

    rule_id: str
    evaluator: EvaluatorType
    required_inputs: tuple[RequiredInput, ...]
    executability: Executability
    automation_status: AutomationStatus
    score_policy: ScorePolicy
    data: Mapping[str, Any]
    example_pair_policy: ExamplePairPolicy | None = None
    example_pair_reason: str | None = None
    example_pair_issue: str | None = None

    @property
    def has_example_pair(self) -> bool:
        return bool(self.get("goede_voorbeelden")) and bool(
            self.get("foute_voorbeelden")
        )

    @property
    def canonical_id(self) -> str:
        return canonical_rule_id(self.rule_id)

    @property
    def is_automated(self) -> bool:
        return self.automation_status is AutomationStatus.AUTOMATED

    @property
    def counts_toward_score(self) -> bool:
        return self.score_policy is ScorePolicy.SCORED

    def get(self, sleutel: str, standaard: Any = None) -> Any:
        """Leesvenster op de ruwe regeldata (patronen, grenzen, metadata)."""
        return self.data.get(sleutel, standaard)


def _eis_enum(rule_id: str, veld: str, waarde: Any, enum_type: type[StrEnum]) -> Any:
    try:
        return enum_type(waarde)
    except ValueError as exc:
        toegestaan = ", ".join(sorted(lid.value for lid in enum_type))
        msg = (
            f"{rule_id}: veld '{veld}' heeft onbekende waarde {waarde!r}; "
            f"toegestaan: {toegestaan}"
        )
        raise RuleContractError(msg) from exc


def build_rule_record(
    rule_id: str, data: Mapping[str, Any], policy: RootContractPolicy | None = None
) -> RuleRecord:
    """Bouw en valideer één RuleRecord; faalt zichtbaar bij contractbreuk."""
    if not isinstance(data, Mapping):
        msg = f"{rule_id}: regeldata is geen mapping maar {type(data).__name__}"
        raise RuleContractError(msg)

    policy = policy or root_contract_policy()
    ontbrekend = [veld for veld in policy.record_required_fields if veld not in data]
    if ontbrekend:
        msg = (
            f"{rule_id}: verplichte recordvelden ontbreken: {ontbrekend} "
            f"(vastgesteld in de root-SSOT)"
        )
        raise RuleContractError(msg)

    _eis_compileerbare_patronen(rule_id, data)

    gedeclareerd_id = data.get("id")
    if gedeclareerd_id is not None and canonical_rule_id(
        gedeclareerd_id
    ) != canonical_rule_id(rule_id):
        msg = (
            f"{rule_id}: veld 'id' is {gedeclareerd_id!r} — ID/bestandsnaam-drift "
            f"mag niet stil blijven bestaan"
        )
        raise RuleContractError(msg)

    contract = data.get(CONTRACT_BLOCK)
    if not isinstance(contract, Mapping) or not contract:
        msg = (
            f"{rule_id}: blok '{CONTRACT_BLOCK}' ontbreekt of is leeg; zonder "
            f"contract is niet vast te stellen welke evaluator deze regel draait"
        )
        raise RuleContractError(msg)

    ruwe_inputs = contract.get("required_inputs")
    if not isinstance(ruwe_inputs, list):
        msg = (
            f"{rule_id}: '{CONTRACT_BLOCK}.required_inputs' moet een lijst zijn "
            f"(mag leeg), gevonden {ruwe_inputs!r}"
        )
        raise RuleContractError(msg)

    vereist = tuple(
        _eis_enum(rule_id, "required_inputs", naam, RequiredInput)
        for naam in ruwe_inputs
    )
    if len(set(vereist)) != len(vereist):
        msg = f"{rule_id}: 'required_inputs' bevat duplicaten: {list(ruwe_inputs)}"
        raise RuleContractError(msg)

    record = RuleRecord(
        rule_id=rule_id,
        evaluator=_eis_enum(
            rule_id, "evaluator", contract.get("evaluator"), EvaluatorType
        ),
        required_inputs=vereist,
        executability=_eis_enum(
            rule_id, "executability", contract.get("executability"), Executability
        ),
        automation_status=_eis_enum(
            rule_id,
            "automation_status",
            contract.get("automation_status"),
            AutomationStatus,
        ),
        score_policy=_eis_enum(
            rule_id, "score_policy", contract.get("score_policy"), ScorePolicy
        ),
        data=data,
        example_pair_policy=(
            _eis_enum(
                rule_id,
                "example_pair_policy",
                contract.get("example_pair_policy"),
                ExamplePairPolicy,
            )
            if contract.get("example_pair_policy") is not None
            else None
        ),
        example_pair_reason=contract.get("example_pair_reason"),
        example_pair_issue=contract.get("example_pair_issue"),
    )
    _eis_consistente_klasse(record)
    _eis_voorbeeldpaarbeleid(record)
    return record


def _eis_compileerbare_patronen(rule_id: str, data: Mapping[str, Any]) -> None:
    """Elk patroonveld moet een lijst compileerbare regexen zijn.

    Verzamelt álle kapotte patronen van het record in één melding, mét
    veldnaam en index, zodat een migratie niet patroon-voor-patroon hoeft te
    worden uitgevist.
    """
    fouten: list[str] = []
    for veld in REGEX_PATROONVELDEN:
        waarde = data.get(veld)
        if waarde is None:
            continue
        if not isinstance(waarde, list):
            fouten.append(
                f"'{veld}' moet een lijst patronen zijn, gevonden "
                f"{type(waarde).__name__}"
            )
            continue
        for index, patroon in enumerate(waarde):
            try:
                re.compile(patroon, re.IGNORECASE)
            except (re.error, TypeError) as exc:
                fouten.append(
                    f"'{veld}'[{index}] is geen bruikbare regex "
                    f"({patroon!r}): {exc}"
                )
    if fouten:
        msg = f"{rule_id}: " + "; ".join(fouten)
        raise RuleContractError(msg)


def _eis_consistente_klasse(record: RuleRecord) -> None:
    """Uitvoerbaarheidsklasse en automatiseringsstatus mogen niet botsen."""
    if (
        record.executability is Executability.NOT_AUTOMATABLE
        and record.automation_status is AutomationStatus.AUTOMATED
    ):
        msg = (
            f"{record.rule_id}: 'not_automatable' kan niet tegelijk "
            f"'automated' zijn"
        )
        raise RuleContractError(msg)
    if (
        record.executability is Executability.REPOSITORY
        and RequiredInput.DEFINITION_REPOSITORY not in record.required_inputs
    ):
        msg = (
            f"{record.rule_id}: repositoryregel declareert "
            f"'{RequiredInput.DEFINITION_REPOSITORY.value}' niet als vereiste invoer"
        )
        raise RuleContractError(msg)
    if (
        record.automation_status is not AutomationStatus.AUTOMATED
        and record.score_policy is ScorePolicy.SCORED
    ):
        msg = (
            f"{record.rule_id}: status {record.automation_status.value!r} kan niet "
            f"'scored' zijn — een niet-uitgevoerde regel mag de score niet raken"
        )
        raise RuleContractError(msg)


def _eis_voorbeeldpaarbeleid(record: RuleRecord) -> None:
    """Een gedocumenteerd goed/fout-paar is normatief, tenzij onderbouwd anders.

    Afwijken mag, maar nooit stil: iedere niet-normatieve policy draagt een
    reden én een tracker-ID, zodat een datakwestie niet als opgelost
    voorbijgaat (ALG-375, dispositie verplicht).
    """
    if not record.has_example_pair:
        if record.example_pair_policy is not None:
            msg = (
                f"{record.rule_id}: 'example_pair_policy' gezet terwijl het record "
                f"geen goed/fout-paar draagt"
            )
            raise RuleContractError(msg)
        return

    if record.example_pair_policy is None:
        msg = (
            f"{record.rule_id}: record draagt een goed/fout-paar maar declareert "
            f"geen 'example_pair_policy'"
        )
        raise RuleContractError(msg)

    if record.example_pair_policy is ExamplePairPolicy.NORMATIVE:
        return

    if not (record.example_pair_reason or "").strip():
        msg = (
            f"{record.rule_id}: policy {record.example_pair_policy.value!r} vereist "
            f"'example_pair_reason'"
        )
        raise RuleContractError(msg)
    if not re.fullmatch(r"DEF-\d+", str(record.example_pair_issue or "")):
        msg = (
            f"{record.rule_id}: policy {record.example_pair_policy.value!r} vereist "
            f"'example_pair_issue' in de vorm DEF-nnn "
            f"(gevonden: {record.example_pair_issue!r})"
        )
        raise RuleContractError(msg)


def build_rule_records(
    regels: Mapping[str, Mapping[str, Any]],
) -> dict[str, RuleRecord]:
    """Valideer een volledige regelset; verzamelt álle contractfouten.

    Fail-closed en volledig: één foutmelding per kapot record, zodat een
    contractmigratie niet regel-voor-regel hoeft te worden uitgevist.
    """
    # Eerst de rootconfig zelf: wijkt die af van de runtime-enums, dan heeft
    # het geen zin de records ertegen te leggen.
    policy = root_contract_policy()

    records: dict[str, RuleRecord] = {}
    fouten: list[str] = []
    for rule_id, data in regels.items():
        try:
            records[rule_id] = build_rule_record(rule_id, data, policy)
        except RuleContractError as exc:
            fouten.append(str(exc))
    if fouten:
        msg = "Regelcontract geschonden:\n- " + "\n- ".join(sorted(fouten))
        raise RuleContractError(msg)
    return records


def lees_regelbestand(pad: Path) -> dict[str, Any]:
    """Lees één JSON-regelbestand fail-closed.

    Een onleesbaar, ongeldig of niet-object bestand is géén "regel die er
    even niet is": het is een regel die stil uit de validatie zou
    verdwijnen. Beide laders (ToetsregelManager en RuleCache) gebruiken
    daarom deze ene functie, zodat testpad en productiepad niet elk hun
    eigen foutafhandeling krijgen.
    """
    try:
        ruw = pad.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"{pad.stem}: regelbestand niet leesbaar ({pad}): {exc}"
        raise RuleContractError(msg) from exc

    try:
        data = json.loads(ruw)
    except json.JSONDecodeError as exc:
        msg = f"{pad.stem}: regelbestand bevat ongeldige JSON ({pad}): {exc}"
        raise RuleContractError(msg) from exc

    if not isinstance(data, dict):
        msg = (
            f"{pad.stem}: regelbestand is geen JSON-object maar "
            f"{type(data).__name__} ({pad})"
        )
        raise RuleContractError(msg)
    return data


def valideer_regelset(
    regels: Mapping[str, Mapping[str, Any]],
    *,
    verwachte_ids: Iterable[str] | None = None,
    bron: str,
) -> dict[str, RuleRecord]:
    """Valideer een complete regelset: volledig én contractueel geldig.

    Alles of niets. Een gedeeltelijke set is gevaarlijker dan geen set: de
    validatie draait dan gewoon door met minder regels, de kwaliteitsscore
    gaat omhoog en er is niets zichtbaar mis.

    `verwachte_ids` komt standaard uit het `rule_ids`-manifest in de
    root-SSOT. Dat is bewust een onafhankelijke bron: leidde de verwachting
    zich af uit de bestanden die er toevallig staan, dan zou een verdwenen
    regelbestand ook niet meer verwacht worden en bleef de controle groen.

    De invoer moet het ónbewerkte bronrecord zijn — vóór defaults of
    normalisatie. Een default die een verplicht veld invult, verbergt
    precies het gat dat deze controle moet vinden.
    """
    verwacht = (
        set(verwachte_ids)
        if verwachte_ids is not None
        else set(root_contract_policy().rule_ids)
    )
    ontbrekend = sorted(verwacht - set(regels))
    if ontbrekend:
        msg = (
            f"{bron}: regelset onvolledig — {len(regels)} van {len(verwacht)} "
            f"regels geladen; ontbrekend: {ontbrekend}"
        )
        raise RuleContractError(msg)

    onverwacht = sorted(set(regels) - verwacht)
    if onverwacht:
        msg = f"{bron}: regelset bevat onbekende regels: {onverwacht}"
        raise RuleContractError(msg)

    return build_rule_records(regels)


def missing_inputs(
    record: RuleRecord, beschikbaar: Iterable[RequiredInput | str]
) -> tuple[RequiredInput, ...]:
    """Welke vereiste invoer ontbreekt voor deze regel?"""
    aanwezig = {canonical_rule_id(str(item)) for item in beschikbaar}
    return tuple(
        vereist
        for vereist in record.required_inputs
        if canonical_rule_id(vereist.value) not in aanwezig
    )


def status_for_missing_inputs(
    ontbrekend: Iterable[RequiredInput], *, strict: bool = False
) -> ResultStatus | None:
    """Uitkomst bij ontbrekende invoer — nooit `PASS`.

    `strict=True` geldt voor paden waar de invoer per contract beschikbaar
    hóórt te zijn (opslaan, vaststellen, exporteren): daar is ontbrekende
    invoer een contractfout, geen ontbrekende meting.
    """
    if not tuple(ontbrekend):
        return None
    return ResultStatus.ERROR if strict else ResultStatus.NOT_EVALUATED
