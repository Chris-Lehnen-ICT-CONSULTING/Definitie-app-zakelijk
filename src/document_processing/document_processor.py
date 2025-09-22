"""
Document Processor - Verwerk geüploade documenten voor context enrichment.
"""

import hashlib  # Hash functionaliteit voor unieke document identifiers
import json  # JSON verwerking voor metadata opslag
import logging  # Logging faciliteiten voor debug en monitoring
from dataclasses import (  # Dataklassen voor gestructureerde document data
    asdict,
    dataclass,
)
from datetime import (  # Datum en tijd functionaliteit voor timestamps
    UTC,
    datetime,
)
from pathlib import Path  # Object-georiënteerde pad manipulatie
from typing import Any  # Type hints voor betere code documentatie

from .document_extractor import (  # Importeer tekst extractie functionaliteit
    extract_text_from_file,
    get_file_info,
)

logger = logging.getLogger(__name__)  # Logger instantie voor document processing module


@dataclass
class ProcessedDocument:
    """Gegevens van een verwerkt document."""

    id: str  # Unieke identifier
    filename: str  # Originele bestandsnaam
    mime_type: str  # MIME type
    size: int  # Bestandsgrootte in bytes
    uploaded_at: datetime  # Upload tijdstip
    extracted_text: str  # Geëxtraheerde tekst
    text_length: int  # Lengte van geëxtraheerde tekst
    keywords: list[str]  # Geëxtraheerde keywords
    key_concepts: list[str]  # Belangrijke concepten
    legal_references: list[str]  # Juridische verwijzingen
    context_hints: list[str]  # Context hints voor definitie generatie
    processing_status: str  # Status van verwerking
    error_message: str | None = None  # Error bericht indien van toepassing

    def to_dict(self) -> dict[str, Any]:
        """Converteer ProcessedDocument naar dictionary voor JSON opslag."""
        data = asdict(self)  # Converteer dataclass naar dictionary
        data["uploaded_at"] = (
            self.uploaded_at.isoformat()
        )  # Converteer datetime naar ISO string
        return data  # Retourneer serialiseerbare dictionary

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProcessedDocument":
        """Maak ProcessedDocument instantie van dictionary data."""
        data["uploaded_at"] = datetime.fromisoformat(
            data["uploaded_at"]
        )  # Converteer ISO string terug naar datetime
        return cls(**data)  # Retourneer nieuwe ProcessedDocument instantie


class DocumentProcessor:
    """Processor voor geüploade documenten met tekstextractie en analyse."""

    def __init__(
        self, storage_dir: str = "data/uploaded_documents"
    ):  # Standaard opslag directory
        """
        Initialiseer document processor.

        Args:
            storage_dir: Directory voor opslag van document metadata
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_dir / "documents_metadata.json"
        self._documents_cache = {}
        self._load_metadata()

    def process_uploaded_file(
        self, file_content: bytes, filename: str, mime_type: str | None = None
    ) -> ProcessedDocument:
        """
        Verwerk een geüpload bestand.

        Args:
            file_content: Binaire inhoud van het bestand
            filename: Originele bestandsnaam
            mime_type: MIME type (optioneel)

        Returns:
            ProcessedDocument object
        """
        try:
            # Genereer unieke ID voor document
            doc_id = self._generate_document_id(file_content, filename)

            # Check of document al verwerkt is
            if doc_id in self._documents_cache:
                logger.info(f"Document {filename} al eerder verwerkt, hergebruik cache")
                return self._documents_cache[doc_id]

            # Krijg bestandsinfo
            file_info = get_file_info(filename, len(file_content))

            # Extraheer tekst
            extracted_text = extract_text_from_file(file_content, filename, mime_type)

            if extracted_text is None:
                # Fout bij extractie
                doc = ProcessedDocument(
                    id=doc_id,
                    filename=filename,
                    mime_type=file_info["mime_type"] or "unknown",
                    size=len(file_content),
                    uploaded_at=datetime.now(UTC),
                    extracted_text="",
                    text_length=0,
                    keywords=[],
                    key_concepts=[],
                    legal_references=[],
                    context_hints=[],
                    processing_status="error",
                    error_message="Tekst extractie gefaald",
                )
            else:
                # Analyseer geëxtraheerde tekst
                keywords = self._extract_keywords(extracted_text)
                key_concepts = self._extract_key_concepts(extracted_text)
                legal_refs = self._extract_legal_references(extracted_text)
                context_hints = self._generate_context_hints(
                    extracted_text, keywords, key_concepts
                )

                doc = ProcessedDocument(
                    id=doc_id,
                    filename=filename,
                    mime_type=file_info["mime_type"] or "unknown",
                    size=len(file_content),
                    uploaded_at=datetime.now(UTC),
                    extracted_text=extracted_text,
                    text_length=len(extracted_text),
                    keywords=keywords,
                    key_concepts=key_concepts,
                    legal_references=legal_refs,
                    context_hints=context_hints,
                    processing_status="success",
                )

            # Sla document op in cache en metadata
            self._documents_cache[doc_id] = doc
            self._save_metadata()

            logger.info(f"Document {filename} succesvol verwerkt (ID: {doc_id})")
            return doc

        except Exception as e:
            logger.error(f"Fout bij verwerken van document {filename}: {e}")

            # Return error document
            doc_id = self._generate_document_id(file_content, filename)
            return ProcessedDocument(
                id=doc_id,
                filename=filename,
                mime_type=mime_type or "unknown",
                size=len(file_content),
                uploaded_at=datetime.now(UTC),
                extracted_text="",
                text_length=0,
                keywords=[],
                key_concepts=[],
                legal_references=[],
                context_hints=[],
                processing_status="error",
                error_message=str(e),
            )

    def get_processed_documents(self) -> list[ProcessedDocument]:
        """Krijg alle verwerkte documenten."""
        return list(self._documents_cache.values())

    def get_document_by_id(self, doc_id: str) -> ProcessedDocument | None:
        """Krijg document op basis van ID."""
        return self._documents_cache.get(doc_id)

    def remove_document(self, doc_id: str) -> bool:
        """Verwijder document uit cache."""
        if doc_id in self._documents_cache:
            del self._documents_cache[doc_id]
            self._save_metadata()
            logger.info(f"Document {doc_id} verwijderd")
            return True
        return False

    def get_aggregated_context(
        self, selected_doc_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Krijg geaggregeerde context van geselecteerde documenten.

        Args:
            selected_doc_ids: IDs van geselecteerde documenten (None = alle)

        Returns:
            Dictionary met geaggregeerde context informatie
        """
        documents = self._documents_cache.values()

        if selected_doc_ids:
            documents = [doc for doc in documents if doc.id in selected_doc_ids]

        # Filter alleen succesvolle documenten
        successful_docs = [
            doc for doc in documents if doc.processing_status == "success"
        ]

        if not successful_docs:
            return {
                "document_count": 0,
                "total_text_length": 0,
                "aggregated_keywords": [],
                "aggregated_concepts": [],
                "aggregated_legal_refs": [],
                "aggregated_context_hints": [],
                "document_sources": [],
            }

        # Aggregeer gegevens
        all_keywords = []
        all_concepts = []
        all_legal_refs = []
        all_context_hints = []
        document_sources = []
        total_text_length = 0

        for doc in successful_docs:
            all_keywords.extend(doc.keywords)
            all_concepts.extend(doc.key_concepts)
            all_legal_refs.extend(doc.legal_references)
            all_context_hints.extend(doc.context_hints)
            document_sources.append(
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "size": doc.size,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                }
            )
            total_text_length += doc.text_length

        # Dedupliceer en sorteer
        unique_keywords = list(set(all_keywords))
        unique_concepts = list(set(all_concepts))
        unique_legal_refs = list(set(all_legal_refs))
        unique_context_hints = list(set(all_context_hints))

        return {
            "document_count": len(successful_docs),
            "total_text_length": total_text_length,
            "aggregated_keywords": sorted(unique_keywords),
            "aggregated_concepts": sorted(unique_concepts),
            "aggregated_legal_refs": sorted(unique_legal_refs),
            "aggregated_context_hints": sorted(unique_context_hints),
            "document_sources": document_sources,
        }

    def _generate_document_id(self, content: bytes, filename: str) -> str:
        """Genereer unieke ID voor document."""
        # Gebruik hash van content + filename voor unique ID
        hasher = hashlib.sha256()
        hasher.update(content)
        hasher.update(filename.encode("utf-8"))
        return hasher.hexdigest()[:16]

    def _extract_keywords(self, text: str) -> list[str]:
        """Extraheer keywords uit tekst."""
        if not text or len(text.strip()) < 10:
            return []

        # Simpele keyword extractie (kan later vervangen door NLP)
        words = text.lower().split()

        # Filter op lengte en verwijder stopwords
        stopwords = {
            "de",
            "het",
            "een",
            "van",
            "en",
            "in",
            "op",
            "met",
            "voor",
            "door",
            "aan",
            "bij",
            "naar",
            "uit",
            "om",
            "over",
            "onder",
            "tussen",
            "tegen",
            "tot",
            "als",
            "dat",
            "die",
            "dit",
            "deze",
            "zijn",
            "wordt",
            "worden",
            "is",
            "was",
            "waren",
            "heeft",
            "hebben",
            "had",
            "kan",
            "moet",
            "zal",
        }

        keywords = []
        for word in words:
            # Schoon woord op
            clean_word = "".join(char for char in word if char.isalnum())
            if (
                len(clean_word) >= 4
                and clean_word not in stopwords
                and clean_word.isalpha()
            ):
                keywords.append(clean_word)

        # Tel frequentie en return top keywords
        from collections import Counter

        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(20)]

    def _extract_key_concepts(self, text: str) -> list[str]:
        """Extraheer belangrijke concepten uit tekst."""
        if not text:
            return []

        # Zoek naar patronen die juridische concepten kunnen zijn
        concepts = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Zoek naar lijnen met hoofdletters en/of cijfers (mogelijk definities)
            if ":" in line and len(line) < 100:
                parts = line.split(":")
                if len(parts) >= 2:
                    concept = parts[0].strip()
                    if len(concept) > 3 and len(concept) < 50:
                        concepts.append(concept)

            # Zoek naar gekapitaliseerde termen
            import re

            capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", line)
            for cap in capitalized:
                if len(cap) > 3 and len(cap) < 50 and cap not in concepts:
                    concepts.append(cap)

        return concepts[:15]  # Beperk tot top 15

    def _extract_legal_references(self, text: str) -> list[str]:
        """Extraheer juridische verwijzingen uit tekst."""
        if not text:
            return []

        # Probeer domeinpatronen; val terug op regex wanneer niets gevonden of bij fouten
        try:
            from domain.juridisch.patronen import JuridischePatronen

            gevonden = JuridischePatronen.zoek_alle_verwijzingen(text)

            # Converteer naar leesbare weergave
            refs: list[str] = []
            for v in (gevonden or []):
                try:
                    parts: list[str] = []
                    if getattr(v, "wet", None):
                        parts.append(str(v.wet))
                    if getattr(v, "boek", None):
                        parts.append(f"Boek {v.boek}")
                    if getattr(v, "artikel", None):
                        parts.append(f"artikel {v.artikel}")
                    if getattr(v, "lid", None):
                        parts.append(f"lid {v.lid}")
                    if getattr(v, "sub", None):
                        parts.append(f"onder {v.sub}")
                    label = ", ".join(parts) if parts else str(getattr(v, "herkend_via", "")).strip()
                    if label:
                        refs.append(label)
                except Exception:
                    # Veilig overslaan van onverwachte vormen
                    continue

            # Dedupliceer en beperk aantal
            refs = list(dict.fromkeys(refs))[:10]
            if refs:
                return refs

        except Exception:
            # Domeinmodule niet beschikbaar of faalde; ga door naar regex fallback
            pass

        # Fallback: simpele regex patterns voor juridische verwijzingen
        try:
            import re

            patterns = [
                r"artikel\s+\d+[a-z]*",
                r"art\.\s+\d+[a-z]*",
                r"lid\s+\d+",
                r"wetboek\s+van\s+\w+",
                r"wet\s+[\w\-]+",
                r"besluit\s+\w+",
                r"verordening\s+\w+",
            ]

            references: list[str] = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                references.extend(matches)

            # Dedupliceer, normaliseer en limiteren
            cleaned = [ref.strip() for ref in references if ref and ref.strip()]
            unique_cleaned = list(dict.fromkeys(cleaned))[:10]
            return unique_cleaned
        except Exception:
            # Als zelfs fallback faalt, geef leeg resultaat terug
            return []

    def _generate_context_hints(
        self, text: str, keywords: list[str], concepts: list[str]
    ) -> list[str]:
        """Genereer context hints voor definitie generatie."""
        hints = []

        # Hint op basis van document lengte
        if len(text) > 10000:
            hints.append("Uitgebreid document - mogelijk veel achtergrondcontext")
        elif len(text) > 1000:
            hints.append("Middelgroot document - relevante context informatie")
        else:
            hints.append("Compact document - specifieke context")

        # Hints op basis van keywords
        if any(word in ["definitie", "betekenis", "omschrijving"] for word in keywords):
            hints.append("Document bevat definities")

        if any(word in ["proces", "procedure", "stappen"] for word in keywords):
            hints.append("Document beschrijft processen")

        if any(
            word in ["wet", "wetgeving", "artikel", "juridisch"] for word in keywords
        ):
            hints.append("Juridische context aanwezig")

        # Hints op basis van concepten
        if concepts:
            hints.append(f"Bevat {len(concepts)} geïdentificeerde concepten")

        return hints

    def _load_metadata(self):
        """Laad document metadata uit bestand."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, encoding="utf-8") as f:
                    data = json.load(f)

                for doc_data in data.get("documents", []):
                    doc = ProcessedDocument.from_dict(doc_data)
                    self._documents_cache[doc.id] = doc

                logger.info(
                    f"Metadata geladen voor {len(self._documents_cache)} documenten"
                )
            except Exception as e:
                logger.error(f"Fout bij laden metadata: {e}")
                self._documents_cache = {}

    def _save_metadata(self):
        """Sla document metadata op in bestand."""
        try:
            data = {
                "documents": [doc.to_dict() for doc in self._documents_cache.values()],
                "last_updated": datetime.now(UTC).isoformat(),
            }

            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Fout bij opslaan metadata: {e}")


# Global document processor instance
_document_processor = None


def get_document_processor() -> DocumentProcessor:
    """Krijg globale document processor instance."""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor
