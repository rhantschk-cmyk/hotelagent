"""HotelAgent — Standard-Hotel-Agent (erbt von BaseAgent)."""

from pathlib import Path
from agents.base_agent import BaseAgent, ALL_TOOLS, execute_tool
from scripts.config_manager import get_agent_config

# Fuer Rueckwaertskompatibilitaet: TOOLS als Liste exportieren
TOOLS = list(ALL_TOOLS.values())


class HotelAgent(BaseAgent):
    """Hotel-spezifischer Agent mit allen Tools und Hotel-Wissensdatenbank."""

    def __init__(self, conversation_id: str = None):
        agent_config = get_agent_config()

        # System-Prompt laden
        prompt_path = Path(agent_config.get("system_prompt_path", "config/system_prompt.txt"))
        if not prompt_path.is_absolute():
            prompt_path = Path(__file__).parent.parent / prompt_path
        if prompt_path.is_file():
            system_prompt = prompt_path.read_text(encoding="utf-8").strip()
        else:
            system_prompt = "Du bist ein hilfreicher Hotel-Assistent."

        # Knowledge-Pfad
        knowledge_path = agent_config.get("knowledge_path", "KNOWLEDGE.md")

        super().__init__(
            system_prompt=system_prompt,
            tool_names=["create_gmail_draft", "search_knowledge", "check_mails", "calculate_price"],
            knowledge_path=knowledge_path,
            max_history=agent_config.get("max_history", 50),
            conversation_id=conversation_id,
        )
