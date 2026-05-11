"""HotelAgent — Automation-Manager: Automationen erstellen, verwalten, ausfuehren."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).parent.parent
AUTOMATIONS_DIR = PROJECT_ROOT / "data" / "automations"
LOG_PATH = PROJECT_ROOT / "data" / "logs" / "automations.log"


def _ensure_dir():
    AUTOMATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _config_path(name: str) -> Path:
    return AUTOMATIONS_DIR / f"{name}.json"


def _sanitize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Verfuegbare Aktionen
# ---------------------------------------------------------------------------

AVAILABLE_ACTIONS = {
    "check_mails": {
        "description": "Posteingang pruefen und Entwuerfe erstellen",
        "params": [],
    },
    "crawl_website": {
        "description": "Hotel-Website crawlen und Wissen aktualisieren",
        "params": [
            {"name": "url", "description": "URL der Website", "default": "https://hotel-oedhof.de"},
            {"name": "max_pages", "description": "Max. Seiten", "default": 30},
        ],
    },
    "send_report": {
        "description": "Tagesbericht per E-Mail-Entwurf erstellen",
        "params": [
            {"name": "to", "description": "Empfaenger-E-Mail", "default": ""},
            {"name": "subject", "description": "Betreff", "default": "Tagesbericht HotelAgent"},
        ],
    },
    "backup_knowledge": {
        "description": "Wissensdatenbank sichern",
        "params": [],
    },
    "run_agent_task": {
        "description": "Einen Agent mit einer Aufgabe beauftragen",
        "params": [
            {"name": "agent_name", "description": "Name des Agents", "default": "hotel_agent"},
            {"name": "task", "description": "Aufgabe / Nachricht an den Agent", "default": ""},
        ],
    },
}

# ---------------------------------------------------------------------------
# Trigger-Typen
# ---------------------------------------------------------------------------

TRIGGER_TYPES = {
    "schedule": "Zeitgesteuert (z.B. taeglich um 8:00)",
    "event": "Event-basiert (z.B. bei neuer E-Mail)",
    "manual": "Nur manuell auslösbar",
}

# Verfuegbare Events fuer event-basierte Trigger
AVAILABLE_EVENTS = {
    "on_new_email": "Bei neuer E-Mail im Posteingang",
    "on_document_upload": "Nach Dokument-Upload",
    "on_agent_start": "Beim Start eines Agents",
}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_automation(
    name: str,
    description: str,
    action: str,
    trigger_type: str = "manual",
    schedule_time: str | None = None,
    schedule_days: list[str] | None = None,
    event_name: str | None = None,
    action_params: dict | None = None,
    enabled: bool = True,
) -> dict:
    """Neue Automation erstellen."""
    _ensure_dir()
    name = _sanitize_name(name)

    if _config_path(name).exists():
        raise ValueError(f"Automation '{name}' existiert bereits.")
    if action not in AVAILABLE_ACTIONS:
        raise ValueError(f"Unbekannte Aktion: '{action}'. Verfuegbar: {list(AVAILABLE_ACTIONS.keys())}")
    if trigger_type not in TRIGGER_TYPES:
        raise ValueError(f"Unbekannter Trigger-Typ: '{trigger_type}'. Verfuegbar: {list(TRIGGER_TYPES.keys())}")

    config = {
        "name": name,
        "description": description,
        "action": action,
        "action_params": action_params or {},
        "trigger": {
            "type": trigger_type,
            "schedule_time": schedule_time,       # z.B. "08:00"
            "schedule_days": schedule_days or [],  # z.B. ["monday", "wednesday"]
            "event": event_name,                   # z.B. "on_new_email"
        },
        "enabled": enabled,
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "run_count": 0,
    }

    _config_path(name).write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return config


def list_automations() -> list[dict]:
    """Alle Automationen auflisten."""
    _ensure_dir()
    automations = []
    for f in sorted(AUTOMATIONS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            automations.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return automations


def get_automation(name: str) -> dict | None:
    """Automation laden."""
    name = _sanitize_name(name)
    path = _config_path(name)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return None


def update_automation(name: str, **updates) -> dict:
    """Automation aktualisieren."""
    name = _sanitize_name(name)
    path = _config_path(name)
    if not path.is_file():
        raise ValueError(f"Automation '{name}' nicht gefunden.")

    config = json.loads(path.read_text(encoding="utf-8"))

    for key, value in updates.items():
        if key == "trigger" and isinstance(value, dict):
            config["trigger"].update(value)
        elif key in config:
            config[key] = value

    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return config


def enable_automation(name: str) -> dict:
    """Automation aktivieren."""
    return update_automation(name, enabled=True)


def disable_automation(name: str) -> dict:
    """Automation deaktivieren."""
    return update_automation(name, enabled=False)


def delete_automation(name: str) -> bool:
    """Automation loeschen."""
    name = _sanitize_name(name)
    path = _config_path(name)
    if path.is_file():
        path.unlink()
        return True
    return False


# ---------------------------------------------------------------------------
# Aktionen ausfuehren
# ---------------------------------------------------------------------------

def _log_run(name: str, status: str, message: str):
    """Ausfuehrung loggen."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "automation": name,
        "status": status,
        "message": message,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _run_check_mails(params: dict) -> str:
    from scripts.email_processor import process_inbox
    results = process_inbox()
    created = sum(1 for r in results if r["status"] == "entwurf_erstellt")
    return f"{created} Entwurf/e erstellt, {len(results) - created} uebersprungen."


def _run_crawl_website(params: dict) -> str:
    from scripts.web_scraper import crawl_site, analyze_website
    from scripts.documents import save_to_knowledge
    url = params.get("url", "https://hotel-oedhof.de")
    max_pages = int(params.get("max_pages", 30))
    pages = crawl_site(url, max_pages=max_pages)
    if not pages:
        return "Keine Seiten gefunden."
    analysis = analyze_website(pages)
    save_to_knowledge(f"Website: {url}", analysis)
    return f"{len(pages)} Seiten gecrawlt, Wissen gespeichert."


def _run_send_report(params: dict) -> str:
    from scripts.gmail import create_draft
    to = params.get("to", "")
    subject = params.get("subject", "Tagesbericht HotelAgent")
    if not to:
        return "Kein Empfaenger angegeben."

    # Einfachen Report zusammenstellen
    from scripts.agent_manager import load_agent
    agent = load_agent("hotel_agent")
    body = agent.send(
        "Erstelle einen kurzen Tagesbericht ueber den aktuellen Stand. "
        "Fasse zusammen was in der Wissensdatenbank steht.",
        stream=False,
    )
    result = create_draft(to, subject, body)
    return f"Report-Entwurf erstellt (ID: {result['id']})."


def _run_backup_knowledge(params: dict) -> str:
    from scripts.config_manager import get_agent_config
    knowledge_path = PROJECT_ROOT / get_agent_config().get("knowledge_path", "KNOWLEDGE.md")
    if not knowledge_path.is_file():
        return "KNOWLEDGE.md nicht gefunden."
    backup_dir = PROJECT_ROOT / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"KNOWLEDGE_{timestamp}.md"
    shutil.copy2(str(knowledge_path), str(dest))
    return f"Backup erstellt: {dest.name}"


def _run_agent_task(params: dict) -> str:
    from scripts.agent_manager import load_agent
    agent_name = params.get("agent_name", "hotel_agent")
    task = params.get("task", "")
    if not task:
        return "Keine Aufgabe angegeben."
    agent = load_agent(agent_name)
    response = agent.send(task, stream=False)
    return f"Agent '{agent_name}' Antwort: {response[:500]}"


ACTION_RUNNERS = {
    "check_mails": _run_check_mails,
    "crawl_website": _run_crawl_website,
    "send_report": _run_send_report,
    "backup_knowledge": _run_backup_knowledge,
    "run_agent_task": _run_agent_task,
}


def run_automation(name: str) -> str:
    """Automation manuell oder per Scheduler ausfuehren."""
    config = get_automation(name)
    if config is None:
        raise ValueError(f"Automation '{name}' nicht gefunden.")

    action = config["action"]
    params = config.get("action_params", {})

    runner = ACTION_RUNNERS.get(action)
    if not runner:
        msg = f"Keine Runner-Funktion fuer Aktion '{action}'."
        _log_run(name, "error", msg)
        return msg

    try:
        result = runner(params)
        # Config aktualisieren
        update_automation(name, last_run=datetime.now().isoformat(), run_count=config.get("run_count", 0) + 1)
        _log_run(name, "ok", result)
        logger.info(f"Automation '{name}' ausgefuehrt: {result}")
        return result
    except Exception as e:
        msg = f"Fehler: {e}"
        _log_run(name, "error", msg)
        logger.error(f"Automation '{name}' fehlgeschlagen: {e}")
        return msg


def get_run_log(limit: int = 50) -> list[dict]:
    """Letzte Ausfuehrungen aus dem Log lesen."""
    if not LOG_PATH.is_file():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in reversed(lines[-limit:]):
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def get_scheduled_automations() -> list[dict]:
    """Alle aktiven zeitgesteuerten Automationen zurueckgeben."""
    return [
        a for a in list_automations()
        if a.get("enabled") and a.get("trigger", {}).get("type") == "schedule"
    ]


def get_event_automations(event_name: str) -> list[dict]:
    """Alle aktiven Automationen fuer ein bestimmtes Event zurueckgeben."""
    return [
        a for a in list_automations()
        if a.get("enabled")
        and a.get("trigger", {}).get("type") == "event"
        and a.get("trigger", {}).get("event") == event_name
    ]


def fire_event(event_name: str) -> list[str]:
    """Event ausloesen — alle passenden Automationen ausfuehren."""
    results = []
    for auto in get_event_automations(event_name):
        result = run_automation(auto["name"])
        results.append(f"{auto['name']}: {result}")
    return results
