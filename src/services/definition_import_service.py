"""
DefinitionImportService - Enkelvoudige import (MVP)

Biedt een kleine serviceschil voor:
- Validatie van één definitie (V2 orchestrator)
- Duplicaatcontrole via DefinitionRepository
- Opslag als Draft met herkomstmetadata (source_type=imported)
- Eenvoudige import logging

Let op: Batch/queue/mapping horen NIET bij dit MVP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import pandas as pd

from services.interfaces import Definition
from services.validation.interfaces import ValidationResult


@dataclass
class SingleImportPreview:
    """Resultaat van de validatie/preview stap."""

    validation: ValidationResult
    duplicates: list[Definition]
    ok: bool


@dataclass
class SingleImportResult:
    """Resultaat van de import stap."""

    success: bool
    definition_id: int | None
    validation: ValidationResult | None
    duplicates: list[Definition]
    error: str | None = None


class DefinitionImportService:
    """Service voor enkelvoudige import (MVP)."""

    def __init__(self, repository, validation_orchestrator):
        """
        Args:
            repository: DefinitionRepository service
            validation_orchestrator: ValidationOrchestratorV2 instance
        """
        self._repo = repository
        self._validator = validation_orchestrator

    async def validate_single(self, payload: Dict[str, Any]) -> SingleImportPreview:
        """Valideer één definitie en geef duplicates terug.

        Vereist velden in payload: begrip, definitie, categorie, organisatorische_context(list),
        optioneel: juridische_context(list), wettelijke_basis(list).
        """
        definition = self._payload_to_definition(payload)
        validation = await self._validator.validate_definition(definition)

        # Duplicaatcontrole op begrip + context (repository logica)
        duplicates = self._repo.find_duplicates(definition) or []

        ok = True
        try:
            ok = bool(validation.get("is_acceptable", False))
        except Exception:
            ok = False

        return SingleImportPreview(validation=validation, duplicates=duplicates, ok=ok)

    async def import_single(
        self,
        payload: Dict[str, Any],
        *,
        allow_duplicate: bool = False,
        duplicate_strategy: str | None = None,
        created_by: str | None = None,
    ) -> SingleImportResult:
        """Voer de daadwerkelijke import uit na validatie."""
        preview = await self.validate_single(payload)

        # Bepaal strategie: 'skip' (default) of 'overwrite'
        strategy = (duplicate_strategy or ("overwrite" if allow_duplicate else "skip")).lower()

        if preview.duplicates and strategy == "skip":
            return SingleImportResult(
                success=False,
                definition_id=None,
                validation=preview.validation,
                duplicates=preview.duplicates,
                error=(
                    "Definitie bestaat al voor deze context. Schakel overschrijven in om door te gaan."
                ),
            )

        # Maak definitie met metadata voor import
        definition = self._payload_to_definition(payload)
        # Zet status/metadata voor import herkomst
        md = dict(definition.metadata or {})
        md.setdefault("status", "imported")
        md.setdefault("source_type", "imported")
        md.setdefault("imported_from", "single_import_ui")
        if created_by:
            md.setdefault("created_by", created_by)
        definition.metadata = md

        # Sla op via DefinitionRepository
        # Overwrite: update eerste duplicaat in plaats van nieuw record aan te maken
        if preview.duplicates and strategy == "overwrite":
            try:
                target = preview.duplicates[0]
                if getattr(target, "id", None):
                    definition.id = int(target.id)
            except Exception:
                # Fallback: laat id None → create
                pass
        new_id = self._repo.save(definition)

        # Sla synoniemen en voorkeursterm op in voorbeelden tabel
        if new_id:
            try:
                legacy = getattr(self._repo, "legacy_repo", None)
                if legacy:
                    voorbeelden_dict = {}

                    # Voorkeursterm (als eerste synoniem met is_voorkeursterm=True)
                    voorkeursterm = definition.metadata.get('voorkeursterm') if definition.metadata else None
                    if voorkeursterm:
                        voorbeelden_dict['synonyms'] = [voorkeursterm]

                    # Andere synoniemen
                    if definition.synoniemen:
                        if 'synonyms' in voorbeelden_dict:
                            voorbeelden_dict['synonyms'].extend(definition.synoniemen)
                        else:
                            voorbeelden_dict['synonyms'] = definition.synoniemen

                    # AI toelichting
                    if definition.toelichting:
                        voorbeelden_dict['explanation'] = [definition.toelichting]

                    # Sla voorbeelden op als ze bestaan
                    if voorbeelden_dict:
                        # Sla alle voorbeelden op, inclusief voorkeursterm met is_voorkeursterm=True
                        legacy.save_voorbeelden(
                            new_id,
                            voorbeelden_dict,
                            generation_model="import",
                            gegenereerd_door=created_by or "import",
                            voorkeursterm=voorkeursterm
                        )

            except Exception as e:
                # Voorbeelden opslag is best-effort, hoofddefinitie is al opgeslagen
                pass

        # Eenvoudige logging naar import_export_logs (bestemming=single_import_ui)
        try:
            # Gebruik legacy repo logging (beschikbaar onder water)
            legacy = getattr(self._repo, "legacy_repo", None)
            if legacy and hasattr(legacy, "_log_import_export"):
                legacy._log_import_export(
                    "import", "single_import_ui", 1, 1, 0
                )  # type: ignore[attr-defined]
        except Exception:
            # Logging is best-effort
            pass

        return SingleImportResult(
            success=bool(new_id),
            definition_id=int(new_id) if new_id else None,
            validation=preview.validation,
            duplicates=preview.duplicates,
            error=None,
        )

    # -------- intern --------
    def _payload_to_definition(self, payload: Dict[str, Any]) -> Definition:
        begrip = str(payload.get("begrip", "")).strip()
        definitie = str(payload.get("definitie", "")).strip()
        categorie = payload.get("categorie") or None
        org = payload.get("organisatorische_context") or []
        jur = payload.get("juridische_context") or []
        wet = payload.get("wettelijke_basis") or []

        # Normalize naar lijsten van strings
        def _as_list(v: Any) -> list[str]:
            if v is None:
                return []
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
            if isinstance(v, str):
                # split op comma
                return [s.strip() for s in v.split(",") if s.strip()]
            return []

        # Helper om tekst te normaliseren (verwijder triple quotes en taal-tags)
        def _clean_text(text: str | float | None) -> str:
            # Handle NaN, None, and other non-string values
            if text is None or (isinstance(text, float) and pd.isna(text)):
                return ""
            # Convert to string if not already
            text = str(text).strip() if text else ""
            if not text:
                return ""
            # Verwijder @nl tags
            text = text.replace("@nl", "")
            # Verwijder triple quotes
            text = text.strip('"""')
            return text.strip()

        org_list = _as_list(org)
        jur_list = _as_list(jur)
        wet_list = _as_list(wet)

        # Nieuwe velden mapping
        ufo_categorie = _clean_text(payload.get("UFO_Categorie", payload.get("ufo_categorie", "")))
        voorkeursterm = _clean_text(payload.get("Voorkeursterm", payload.get("voorkeursterm", "")))

        # Synoniemen (komma-gescheiden naar lijst)
        synoniemen_field = _clean_text(payload.get("Synoniemen", payload.get("synoniemen", "")))
        synoniemen_list = _as_list(synoniemen_field) if synoniemen_field else []

        # Procesmatige toelichting: merge beide velden indien aanwezig
        toelichting_1 = _clean_text(payload.get("Toelichting", ""))
        toelichting_optioneel = _clean_text(payload.get("Toelichting (optioneel)", ""))

        # Bepaal welke toelichting waar hoort:
        # - "Toelichting" uit CSV is vaak de AI-toelichting op de definitie
        # - "Toelichting (optioneel)" is meestal procesmatige notities
        toelichting_definitie = ""  # Voor AI-gegenereerde toelichting op definitie
        toelichting_proces = ""  # Voor procesmatige notities

        # Als beide aanwezig zijn, behandel eerste als definitie-toelichting, tweede als proces
        if toelichting_1 and toelichting_optioneel:
            toelichting_definitie = toelichting_1
            toelichting_proces = toelichting_optioneel
        elif toelichting_optioneel:
            # Als alleen optioneel veld, gebruik voor proces
            toelichting_proces = toelichting_optioneel
        elif toelichting_1:
            # Als alleen hoofdveld, bepaal op basis van inhoud (heuristiek)
            # Als het lijkt op procesnotities (bevat woorden als "validatie", "review", etc.)
            proces_keywords = ["validatie", "review", "controle", "opmerking", "nota", "proces"]
            if any(keyword in toelichting_1.lower() for keyword in proces_keywords):
                toelichting_proces = toelichting_1
            else:
                toelichting_definitie = toelichting_1

        definition = Definition(
            begrip=begrip,
            definitie=definitie,
            organisatorische_context=org_list,
            juridische_context=jur_list,
            wettelijke_basis=wet_list,
            categorie=str(categorie) if categorie else None,
            ufo_categorie=ufo_categorie if ufo_categorie else None,
            synoniemen=synoniemen_list if synoniemen_list else None,  # Tijdelijk, wordt later naar voorbeelden geschreven
            toelichting=toelichting_definitie if toelichting_definitie else None,
            toelichting_proces=toelichting_proces if toelichting_proces else None,
        )

        # Store voorkeursterm temporarily in metadata for later processing
        if voorkeursterm:
            if not definition.metadata:
                definition.metadata = {}
            definition.metadata['voorkeursterm'] = voorkeursterm

        return definition
