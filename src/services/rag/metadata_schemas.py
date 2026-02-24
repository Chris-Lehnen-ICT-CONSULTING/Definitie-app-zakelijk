"""Pydantic metadata-schema's per bron_type (DEF-374).

Elke bekende bron_type heeft een volledig schema — alle velden die de
dict-comprehension in rag_service.py produceert staan expliciet vermeld.

Extensibiliteit: nieuw bron_type toevoegen = nieuw model + registratie in
METADATA_SCHEMAS. Geen andere code-wijzigingen nodig.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WetgevingMetadata(BaseModel):
    artikel_nummer: str | None = None
    lid_nummer: str | None = None
    structuur_type: str | None = None
    bronbestand: str | None = None
    pagina_nummer: int | None = None
    sectie: str | None = None


class WebsiteMetadata(BaseModel):
    # url is optioneel: ChunkMetadata levert dit veld nog niet — zie DEF-374
    url: str | None = None
    domein: str | None = None
    laatst_gescraped: str | None = None
    sectie: str | None = None


class PDFMetadata(BaseModel):
    pagina_nummer: int | None = None
    sectie: str | None = None
    auteur: str | None = None
    bronbestand: str | None = None


METADATA_SCHEMAS: dict[str, type[BaseModel]] = {
    "wetgeving": WetgevingMetadata,
    "website": WebsiteMetadata,
    "pdf": PDFMetadata,
}


def valideer_chunk_metadata(bron_type: str | None, metadata_dict: dict) -> dict:
    """Valideer metadata via Pydantic. Streng voor bekende bron_types.

    Voor bekende bron_types wordt Pydantic-validatie afgedwongen — een
    ValidationError wijst op een programmeerfout in de chunker (ChunkMetadata
    is een getypeerde frozen dataclass, dus dit mag niet voorkomen in productie).

    Voor onbekende of lege bron_types wordt metadata geaccepteerd zonder
    validatie, met een waarschuwing. De aanroeper (store_batch) verzorgt
    de JSON-serialisatie.

    Args:
        bron_type: Brontype van het document (bijv. "wetgeving", "pdf").
        metadata_dict: Metadata-waarden (null-gefilterd door aanroeper).

    Returns:
        Gevalideerde metadata als dict (exclusief None-waarden voor bekende schemas).

    Raises:
        pydantic.ValidationError: Als metadata niet voldoet aan het schema
            voor een bekende bron_type (programmeerfout in chunker).
    """
    schema = METADATA_SCHEMAS.get(bron_type or "")
    if schema is None:
        logger.warning(
            "Geen schema voor bron_type=%r, opgeslagen zonder validatie",
            bron_type,
        )
        return metadata_dict

    validated = schema(**metadata_dict)
    return validated.model_dump(exclude_none=True)
