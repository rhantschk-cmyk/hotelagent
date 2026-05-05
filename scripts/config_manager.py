"""HotelAgent — Config-Manager: Laden, speichern, validieren."""

from pathlib import Path
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"
ENV_PATH = PROJECT_ROOT / ".env"

# .env laden falls vorhanden
load_dotenv(ENV_PATH)


def load_config() -> dict:
    """Konfiguration aus settings.yaml laden."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config: dict) -> None:
    """Konfiguration in settings.yaml speichern."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def get_llm_config() -> dict:
    """LLM-Sektion der Konfiguration zurueckgeben."""
    return load_config().get("llm", {})


def get_agent_config() -> dict:
    """Agent-Sektion der Konfiguration zurueckgeben."""
    return load_config().get("agent", {})
