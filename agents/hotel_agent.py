"""HotelAgent — Hotel-Agent-Klasse mit Konversationsverlauf und Tool-Support."""

import json
from pathlib import Path
from scripts.config_manager import get_agent_config, get_llm_config
from scripts.llm import get_client

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_gmail_draft",
            "description": "Erstellt einen Gmail-Entwurf. Nutze dieses Tool wenn der User dich bittet eine E-Mail zu schreiben oder einen Entwurf zu erstellen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Empfaenger-E-Mail-Adresse"},
                    "subject": {"type": "string", "description": "Betreff der E-Mail"},
                    "body": {"type": "string", "description": "Inhalt der E-Mail"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Durchsucht die Wissensdatenbank (KNOWLEDGE.md) nach relevanten Informationen aus hochgeladenen Dokumenten.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Suchbegriff"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_mails",
            "description": "Prueft den Posteingang auf Gaesteanfragen, ordnet passende Gmail-Vorlagen zu, passt sie an und erstellt Antwort-Entwuerfe.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def _execute_tool(name: str, args: dict) -> str:
    """Tool ausfuehren und Ergebnis zurueckgeben."""
    if name == "create_gmail_draft":
        try:
            from scripts.gmail import create_draft
            result = create_draft(args["to"], args["subject"], args["body"])
            return json.dumps({"status": "ok", "draft_id": result["id"],
                               "message": f"Entwurf erstellt an {result['to']}: {result['subject']}"})
        except FileNotFoundError as e:
            return json.dumps({"status": "error", "message": str(e)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    elif name == "search_knowledge":
        try:
            from scripts.documents import search_knowledge
            result = search_knowledge(args["query"])
            return json.dumps({"status": "ok", "result": result})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    elif name == "check_mails":
        try:
            from scripts.email_processor import process_inbox
            results = process_inbox()
            created = sum(1 for r in results if r["status"] == "entwurf_erstellt")
            skipped = len(results) - created
            summary = [
                f"{r['subject'][:50]} — {r['status']}"
                + (f" (Vorlage: {r.get('template_used', '')})" if r["status"] == "entwurf_erstellt" else f" ({r.get('reason', '')})")
                for r in results
            ]
            return json.dumps({
                "status": "ok",
                "created": created,
                "skipped": skipped,
                "details": summary,
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    return json.dumps({"status": "error", "message": f"Unbekanntes Tool: {name}"})


class HotelAgent:
    """Zentraler Agent fuer den Hotel-Assistenten."""

    def __init__(self, conversation_id: str = None):
        self.agent_config = get_agent_config()
        self.llm_config = get_llm_config()
        self.client = get_client()
        self.system_prompt = self._load_system_prompt()
        self.history: list[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.conversation_id = conversation_id

    def _load_system_prompt(self) -> str:
        """System-Prompt aus Datei laden."""
        prompt_path = Path(self.agent_config.get("system_prompt_path", "config/system_prompt.txt"))
        if not prompt_path.is_absolute():
            prompt_path = Path(__file__).parent.parent / prompt_path
        if prompt_path.is_file():
            return prompt_path.read_text(encoding="utf-8").strip()
        return "Du bist ein hilfreicher Hotel-Assistent."

    def _load_knowledge(self) -> str:
        """Wissensdatenbank laden und an System-Prompt anhaengen."""
        knowledge_path = Path(self.agent_config.get("knowledge_path", "KNOWLEDGE.md"))
        if not knowledge_path.is_absolute():
            knowledge_path = Path(__file__).parent.parent / knowledge_path
        if knowledge_path.is_file():
            content = knowledge_path.read_text(encoding="utf-8").strip()
            # Nur laden wenn tatsaechlich Wissen vorhanden (nicht nur Header)
            lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#") and l.strip() != "---"]
            if lines:
                return content
        return ""

    def send(self, user_message: str, stream: bool = None) -> str:
        """Nachricht senden und Antwort erhalten. Unterstuetzt Tool-Calls."""
        # Wissen als Kontext einbinden
        knowledge = self._load_knowledge()
        messages = list(self.history)
        if knowledge:
            messages[0] = {
                "role": "system",
                "content": f"{self.system_prompt}\n\n## Wissensdatenbank\n{knowledge}",
            }

        messages.append({"role": "user", "content": user_message})
        self.history.append({"role": "user", "content": user_message})

        if stream is None:
            stream = self.llm_config.get("streaming", False)

        # Loop fuer Tool-Calls (Agent kann mehrere Tools nacheinander aufrufen)
        while True:
            response = self.client.chat.completions.create(
                model=self.llm_config.get("model", "openai/gpt-4o"),
                messages=messages,
                temperature=self.llm_config.get("temperature", 0.7),
                max_tokens=self.llm_config.get("max_tokens", 2048),
                tools=TOOLS,
            )

            choice = response.choices[0]

            # Wenn Tool-Calls vorhanden
            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                messages.append(choice.message)
                self.history.append({
                    "role": "assistant",
                    "content": choice.message.content,
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in choice.message.tool_calls
                    ],
                })

                for tool_call in choice.message.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    result = _execute_tool(tool_call.function.name, args)

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                    messages.append(tool_msg)
                    self.history.append(tool_msg)

                continue  # Nochmal ans LLM mit Tool-Ergebnis

            # Normale Antwort (kein Tool-Call)
            text = choice.message.content or ""
            if stream and text:
                print(text, end="", flush=True)
                print()

            self.history.append({"role": "assistant", "content": text})
            self._trim_history()
            return text

    def _trim_history(self) -> None:
        """Max-History einhalten."""
        max_history = self.agent_config.get("max_history", 50)
        while len(self.history) > max_history * 2 + 1:
            self.history.pop(1)
            self.history.pop(1)

    def get_history(self) -> list[dict]:
        """Konversationsverlauf zurueckgeben (ohne System-Prompt)."""
        return [m for m in self.history if m["role"] != "system"]

    def clear_history(self) -> None:
        """Konversationsverlauf loeschen."""
        self.history = [{"role": "system", "content": self.system_prompt}]
