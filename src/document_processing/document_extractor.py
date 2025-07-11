"""
Document Text Extraction - Haal tekst uit verschillende bestandsformaten.
"""

import os
import logging
import tempfile
from typing import Optional, Dict, List
from pathlib import Path
import mimetypes

logger = logging.getLogger(__name__)

# Ondersteunde bestandstypen
SUPPORTED_TYPES = {
    'text/plain': 'Tekst bestanden (.txt)',
    'application/pdf': 'PDF documenten (.pdf)',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word documenten (.docx)',
    'application/msword': 'Word documenten (.doc)',
    'text/markdown': 'Markdown bestanden (.md)',
    'text/csv': 'CSV bestanden (.csv)',
    'application/json': 'JSON bestanden (.json)',
    'text/html': 'HTML bestanden (.html)',
    'application/rtf': 'RTF bestanden (.rtf)'
}

def supported_file_types() -> Dict[str, str]:
    """Return ondersteunde bestandstypen."""
    return SUPPORTED_TYPES.copy()

def extract_text_from_file(file_content: bytes, filename: str, mime_type: Optional[str] = None) -> Optional[str]:
    """
    Extraheer tekst uit uploaded bestand.
    
    Args:
        file_content: Binaire inhoud van het bestand
        filename: Originele bestandsnaam
        mime_type: MIME type (optioneel, wordt anders afgeleid)
    
    Returns:
        Geëxtraheerde tekst of None bij fout
    """
    try:
        # Bepaal MIME type als niet gegeven
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type or mime_type not in SUPPORTED_TYPES:
            logger.warning(f"Niet ondersteund bestandstype: {mime_type} voor {filename}")
            return None
        
        # Tekst extractie op basis van type
        if mime_type == 'text/plain':
            return _extract_text_file(file_content)
        elif mime_type == 'application/pdf':
            return _extract_pdf(file_content)
        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
            return _extract_word(file_content, mime_type)
        elif mime_type == 'text/markdown':
            return _extract_markdown(file_content)
        elif mime_type == 'text/csv':
            return _extract_csv(file_content)
        elif mime_type == 'application/json':
            return _extract_json(file_content)
        elif mime_type == 'text/html':
            return _extract_html(file_content)
        elif mime_type == 'application/rtf':
            return _extract_rtf(file_content)
        else:
            logger.warning(f"Geen extractor geïmplementeerd voor {mime_type}")
            return None
            
    except Exception as e:
        logger.error(f"Fout bij tekst extractie uit {filename}: {e}")
        return None

def _extract_text_file(content: bytes) -> str:
    """Extraheer tekst uit plain text bestand."""
    try:
        # Probeer verschillende encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # Als alles faalt, gebruik errors='replace'
        return content.decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Fout bij tekst extractie: {e}")
        return ""

def _extract_pdf(content: bytes) -> Optional[str]:
    """Extraheer tekst uit PDF."""
    try:
        # Probeer PyPDF2 te gebruiken als beschikbaar
        try:
            import PyPDF2
            import io
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []
            
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
            
            return '\n'.join(text_parts)
            
        except ImportError:
            logger.warning("PyPDF2 niet beschikbaar - PDF extractie overgeslagen")
            return "⚠️ PDF extractie vereist PyPDF2 library (pip install PyPDF2)"
            
    except Exception as e:
        logger.error(f"Fout bij PDF extractie: {e}")
        return None

def _extract_word(content: bytes, mime_type: str) -> Optional[str]:
    """Extraheer tekst uit Word document."""
    try:
        # Probeer python-docx voor .docx bestanden
        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            try:
                import docx
                import io
                
                doc = docx.Document(io.BytesIO(content))
                text_parts = []
                
                for paragraph in doc.paragraphs:
                    text_parts.append(paragraph.text)
                
                return '\n'.join(text_parts)
                
            except ImportError:
                logger.warning("python-docx niet beschikbaar - Word extractie overgeslagen")
                return "⚠️ Word extractie vereist python-docx library (pip install python-docx)"
        
        # Voor .doc bestanden
        else:
            logger.warning("Legacy .doc bestanden worden momenteel niet ondersteund")
            return "⚠️ Legacy .doc bestanden vereisen aanvullende libraries"
            
    except Exception as e:
        logger.error(f"Fout bij Word extractie: {e}")
        return None

def _extract_markdown(content: bytes) -> str:
    """Extraheer tekst uit Markdown."""
    try:
        text = content.decode('utf-8')
        
        # Probeer markdown library als beschikbaar voor betere parsing
        try:
            import markdown
            from bs4 import BeautifulSoup
            
            # Convert markdown naar HTML en dan naar plain text
            html = markdown.markdown(text)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(separator='\n')
            
        except ImportError:
            # Simpele fallback - return markdown as-is
            return text
            
    except Exception as e:
        logger.error(f"Fout bij Markdown extractie: {e}")
        return ""

def _extract_csv(content: bytes) -> str:
    """Extraheer tekst uit CSV."""
    try:
        import csv
        import io
        
        text_content = content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(text_content))
        
        text_parts = []
        for row in csv_reader:
            text_parts.append(' | '.join(row))
        
        return '\n'.join(text_parts)
        
    except Exception as e:
        logger.error(f"Fout bij CSV extractie: {e}")
        return ""

def _extract_json(content: bytes) -> str:
    """Extraheer tekst uit JSON."""
    try:
        import json
        
        data = json.loads(content.decode('utf-8'))
        
        # Converteer JSON naar leesbare tekst
        def extract_values(obj, level=0):
            if level > 10:  # Prevent infinite recursion
                return []
            
            values = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and len(value.strip()) > 0:
                        values.append(f"{key}: {value}")
                    else:
                        values.extend(extract_values(value, level + 1))
            elif isinstance(obj, list):
                for item in obj:
                    values.extend(extract_values(item, level + 1))
            elif isinstance(obj, str) and len(obj.strip()) > 0:
                values.append(obj)
            
            return values
        
        return '\n'.join(extract_values(data))
        
    except Exception as e:
        logger.error(f"Fout bij JSON extractie: {e}")
        return ""

def _extract_html(content: bytes) -> str:
    """Extraheer tekst uit HTML."""
    try:
        from bs4 import BeautifulSoup
        
        html_content = content.decode('utf-8')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verwijder script en style tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text(separator='\n')
        
    except ImportError:
        logger.warning("BeautifulSoup niet beschikbaar - HTML extractie overgeslagen")
        return "⚠️ HTML extractie vereist beautifulsoup4 library"
    except Exception as e:
        logger.error(f"Fout bij HTML extractie: {e}")
        return ""

def _extract_rtf(content: bytes) -> str:
    """Extraheer tekst uit RTF."""
    try:
        # Probeer striprtf als beschikbaar
        try:
            from striprtf.striprtf import rtf_to_text
            
            rtf_content = content.decode('utf-8')
            return rtf_to_text(rtf_content)
            
        except ImportError:
            logger.warning("striprtf niet beschikbaar - RTF extractie overgeslagen")
            return "⚠️ RTF extractie vereist striprtf library (pip install striprtf)"
            
    except Exception as e:
        logger.error(f"Fout bij RTF extractie: {e}")
        return ""

def get_file_info(filename: str, file_size: int) -> Dict[str, any]:
    """
    Krijg bestandsinformatie.
    
    Args:
        filename: Bestandsnaam
        file_size: Bestandsgrootte in bytes
    
    Returns:
        Dictionary met bestandsinfo
    """
    mime_type, _ = mimetypes.guess_type(filename)
    file_extension = Path(filename).suffix.lower()
    
    return {
        'filename': filename,
        'extension': file_extension,
        'mime_type': mime_type,
        'size': file_size,
        'size_mb': round(file_size / (1024 * 1024), 2),
        'supported': mime_type in SUPPORTED_TYPES,
        'type_description': SUPPORTED_TYPES.get(mime_type, 'Niet ondersteund')
    }