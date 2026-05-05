"""HotelAgent — Dokument-Verarbeitung: Upload, Extraktion, Analyse."""

import csv
import io
import shutil
from datetime import datetime
from pathlib import Path

from scripts.config_manager import get_agent_config

PROJECT_ROOT = Path(__file__).parent.parent
UPLOADS_DIR = PROJECT_ROOT / "data" / "uploads"


def _ensure_dir():
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def extract_text(file_path: Path) -> str:
    """Text aus Dokument extrahieren. Unterstuetzt PDF, DOCX, TXT, CSV."""
    suffix = file_path.suffix.lower()

    if suffix in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8")

    elif suffix == ".csv":
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            lines = [", ".join(row) for row in reader]
        return "\n".join(lines)

    elif suffix == ".pdf":
        from PyPDF2 import PdfReader
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    elif suffix in (".docx", ".doc"):
        from docx import Document
        doc = Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs)

    else:
        raise ValueError(f"Nicht unterstuetztes Format: {suffix}")


def upload_file(source_path: str) -> Path:
    """Datei in uploads-Ordner kopieren."""
    _ensure_dir()
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {source}")
    dest = UPLOADS_DIR / source.name
    shutil.copy2(str(source), str(dest))
    return dest


def analyze_document(file_path: Path) -> str:
    """Dokument durch LLM analysieren lassen."""
    from scripts.llm import get_client
    from scripts.config_manager import get_llm_config

    text = extract_text(file_path)
    if not text.strip():
        return "Dokument ist leer oder Text konnte nicht extrahiert werden."

    # Text kuerzen falls zu lang
    max_chars = 12000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... gekuerzt ...]"

    client = get_client()
    config = get_llm_config()

    response = client.chat.completions.create(
        model=config.get("model", "openai/gpt-4o"),
        messages=[
            {"role": "system", "content": (
                "Analysiere das folgende Dokument. Erstelle eine strukturierte Zusammenfassung mit:\n"
                "1. Dokumenttyp und Zweck\n"
                "2. Wichtigste Informationen und Schluesseldetails\n"
                "3. Relevante Daten, Namen, Zahlen\n"
                "Antworte auf Deutsch."
            )},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=2048,
    )

    return response.choices[0].message.content


def save_to_knowledge(file_name: str, analysis: str) -> None:
    """Analyse-Ergebnis in KNOWLEDGE.md speichern."""
    knowledge_path = PROJECT_ROOT / get_agent_config().get("knowledge_path", "KNOWLEDGE.md")

    entry = (
        f"\n## {file_name}\n"
        f"**Analysiert am:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{analysis}\n\n---\n"
    )

    with open(knowledge_path, "a", encoding="utf-8") as f:
        f.write(entry)


def search_knowledge(query: str) -> str:
    """Wissensdatenbank durchsuchen (einfache Textsuche)."""
    knowledge_path = PROJECT_ROOT / get_agent_config().get("knowledge_path", "KNOWLEDGE.md")
    if not knowledge_path.is_file():
        return "Keine Wissensdatenbank vorhanden."

    content = knowledge_path.read_text(encoding="utf-8")
    query_lower = query.lower()

    # Sektionen finden die den Suchbegriff enthalten
    sections = content.split("\n## ")
    matches = []
    for section in sections[1:]:  # Erste Sektion ist Header
        if query_lower in section.lower():
            matches.append("## " + section.strip())

    if not matches:
        return f"Keine Treffer fuer '{query}'."

    return "\n\n".join(matches)
