"""HotelAgent — Memory: Persistenter Konversationsspeicher."""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONVERSATIONS_DIR = PROJECT_ROOT / "data" / "conversations"


def _ensure_dir():
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def save_conversation(conversation_id: str, history: list[dict]) -> Path:
    """Konversation speichern."""
    _ensure_dir()
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    data = {
        "id": conversation_id,
        "updated_at": datetime.now().isoformat(),
        "messages": [m for m in history if m["role"] != "system"],
    }
    # created_at beibehalten falls vorhanden
    if filepath.is_file():
        existing = json.loads(filepath.read_text(encoding="utf-8"))
        data["created_at"] = existing.get("created_at", data["updated_at"])
    else:
        data["created_at"] = data["updated_at"]

    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath


def load_conversation(conversation_id: str) -> list[dict] | None:
    """Konversation laden. Gibt None zurueck wenn nicht gefunden."""
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    if not filepath.is_file():
        return None
    data = json.loads(filepath.read_text(encoding="utf-8"))
    return data.get("messages", [])


def list_conversations() -> list[dict]:
    """Alle gespeicherten Konversationen auflisten."""
    _ensure_dir()
    conversations = []
    for f in sorted(CONVERSATIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            msg_count = len(data.get("messages", []))
            # Erste User-Nachricht als Preview
            preview = ""
            for m in data.get("messages", []):
                if m["role"] == "user":
                    preview = m["content"][:60]
                    break
            conversations.append({
                "id": data.get("id", f.stem),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "messages": msg_count,
                "preview": preview,
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return conversations


def delete_conversation(conversation_id: str) -> bool:
    """Konversation loeschen."""
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    if filepath.is_file():
        filepath.unlink()
        return True
    return False


def delete_all_conversations() -> int:
    """Alle Konversationen loeschen. Gibt Anzahl geloeschter zurueck."""
    _ensure_dir()
    count = 0
    for f in CONVERSATIONS_DIR.glob("*.json"):
        f.unlink()
        count += 1
    return count
