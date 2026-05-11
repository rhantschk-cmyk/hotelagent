"""HotelAgent — Agent-Manager: Agents erstellen, laden, bearbeiten, loeschen."""

import json
from pathlib import Path

from agents.base_agent import BaseAgent, ALL_TOOLS

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / "agents"

# Reservierte Namen (duerfen nicht als Custom-Agent erstellt werden)
RESERVED = {"__init__", "base_agent", "hotel_agent", "__pycache__"}


def _config_path(name: str) -> Path:
    """Pfad zur Agent-Config-Datei."""
    return AGENTS_DIR / f"{name}.json"


def _sanitize_name(name: str) -> str:
    """Name bereinigen: Kleinbuchstaben, Leerzeichen zu Unterstrichen."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_agent(
    name: str,
    description: str,
    system_prompt: str,
    tool_names: list[str] | None = None,
    knowledge_path: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Neuen Agent erstellen. Gibt die Config zurueck."""
    name = _sanitize_name(name)
    if name in RESERVED:
        raise ValueError(f"Name '{name}' ist reserviert.")
    if _config_path(name).exists():
        raise ValueError(f"Agent '{name}' existiert bereits.")

    # Nur gueltige Tool-Namen
    valid_tools = [t for t in (tool_names or []) if t in ALL_TOOLS]

    config = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": valid_tools,
        "knowledge_path": knowledge_path,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    _config_path(name).write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return config


def list_agents() -> list[dict]:
    """Alle Custom-Agents auflisten (JSON-Configs in agents/)."""
    agents = []
    for f in sorted(AGENTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            agents.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return agents


def get_agent_config_by_name(name: str) -> dict | None:
    """Agent-Config laden. Gibt None zurueck wenn nicht gefunden."""
    name = _sanitize_name(name)
    path = _config_path(name)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return None


def load_agent(name: str, conversation_id: str = None) -> BaseAgent:
    """Agent aus Config laden und instanziieren.

    Fuer 'hotel_agent' wird der spezielle HotelAgent zurueckgegeben.
    """
    name = _sanitize_name(name)

    if name == "hotel_agent":
        from agents.hotel_agent import HotelAgent
        return HotelAgent(conversation_id=conversation_id)

    config = get_agent_config_by_name(name)
    if config is None:
        raise ValueError(f"Agent '{name}' nicht gefunden.")

    return BaseAgent(
        system_prompt=config.get("system_prompt", "Du bist ein hilfreicher Assistent."),
        tool_names=config.get("tools"),
        knowledge_path=config.get("knowledge_path"),
        model=config.get("model"),
        temperature=config.get("temperature"),
        max_tokens=config.get("max_tokens"),
        conversation_id=conversation_id,
    )


def update_agent(name: str, **updates) -> dict:
    """Agent-Config aktualisieren. Gibt aktualisierte Config zurueck."""
    name = _sanitize_name(name)
    if name in RESERVED:
        raise ValueError(f"Agent '{name}' kann nicht bearbeitet werden.")

    path = _config_path(name)
    if not path.is_file():
        raise ValueError(f"Agent '{name}' nicht gefunden.")

    config = json.loads(path.read_text(encoding="utf-8"))

    for key, value in updates.items():
        if key == "tools":
            config["tools"] = [t for t in (value or []) if t in ALL_TOOLS]
        elif key in config:
            config[key] = value

    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config


def delete_agent(name: str) -> bool:
    """Agent loeschen. Gibt True zurueck wenn erfolgreich."""
    name = _sanitize_name(name)
    if name in RESERVED:
        raise ValueError(f"Agent '{name}' kann nicht geloescht werden.")

    path = _config_path(name)
    if path.is_file():
        path.unlink()
        return True
    return False


def get_all_tool_names() -> list[str]:
    """Alle verfuegbaren Tool-Namen zurueckgeben."""
    return list(ALL_TOOLS.keys())
