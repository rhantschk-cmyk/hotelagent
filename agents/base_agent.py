"""HotelAgent — Basis-Agent-Klasse mit Konversationsverlauf und Tool-Support."""

import json
from pathlib import Path
from scripts.config_manager import get_agent_config, get_llm_config
from scripts.llm import get_client


# ---------------------------------------------------------------------------
# Globale Tool-Registry: alle verfuegbaren Tools
# ---------------------------------------------------------------------------

ALL_TOOLS = {
    "create_gmail_draft": {
        "type": "function",
        "function": {
            "name": "create_gmail_draft",
            "description": "Erstellt einen E-Mail-Entwurf (Gmail, Outlook, GMX, Web.de, etc.). Nutze dieses Tool wenn der User dich bittet eine E-Mail zu schreiben oder einen Entwurf zu erstellen.",
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
    "search_knowledge": {
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
    "check_mails": {
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
    "calculate_price": {
        "type": "function",
        "function": {
            "name": "calculate_price",
            "description": (
                "Berechnet Hotel-Preise exakt anhand der Preisdatenbank (PRICES.md). "
                "Nutze dieses Tool bei JEDER Frage zu Preisen, Kosten oder Angeboten. "
                "Beschreibe die Anfrage so genau wie moeglich: Zimmertyp, Anzahl Naechte, "
                "Personenzahl, Kinder, gewuenschte Extras/Arrangements."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Preisanfrage, z.B. 'Doppelzimmer, 5 Naechte, 2 Personen' "
                            "oder 'Tennis Paket 1 fuer 2 Personen im Luxus-Zimmer' "
                            "oder 'Einzelzimmer 3 Naechte mit 1 Kind (4 Jahre)'"
                        ),
                    },
                },
                "required": ["query"],
            },
        },
    },
}


def execute_tool(name: str, args: dict) -> str:
    """Tool ausfuehren und Ergebnis zurueckgeben."""
    if name == "create_gmail_draft":
        try:
            from scripts.email_provider import get_provider
            provider = get_provider()
            result = provider.create_draft(args["to"], args["subject"], args["body"])
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
    elif name == "calculate_price":
        try:
            from scripts.price_manager import calculate_price
            result = calculate_price(args["query"])
            return json.dumps({"status": "ok", "result": result}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
    return json.dumps({"status": "error", "message": f"Unbekanntes Tool: {name}"})


def get_tools_by_names(tool_names: list[str]) -> list[dict]:
    """Tool-Definitionen anhand ihrer Namen zurueckgeben."""
    return [ALL_TOOLS[name] for name in tool_names if name in ALL_TOOLS]


class BaseAgent:
    """Basis-Agent mit Konversationsverlauf und Tool-Support."""

    def __init__(
        self,
        system_prompt: str = "Du bist ein hilfreicher Assistent.",
        tool_names: list[str] | None = None,
        knowledge_path: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        max_history: int = 50,
        conversation_id: str = None,
    ):
        self.llm_config = get_llm_config()
        self.client = get_client()

        # LLM-Overrides (Agent-spezifisch, sonst Defaults aus settings.yaml)
        self.model = model or self.llm_config.get("model", "openai/gpt-4o")
        self.temperature = temperature if temperature is not None else self.llm_config.get("temperature", 0.7)
        self.max_tokens = max_tokens or self.llm_config.get("max_tokens", 2048)

        self.system_prompt = system_prompt
        self.knowledge_path = knowledge_path
        self.max_history = max_history
        self.conversation_id = conversation_id

        # Tools
        self.tool_names = tool_names or []
        self.tools = get_tools_by_names(self.tool_names) if self.tool_names else []

        # Konversationsverlauf
        self.history: list[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]

    def _load_knowledge(self) -> str:
        """Wissensdatenbank laden."""
        if not self.knowledge_path:
            return ""
        kpath = Path(self.knowledge_path)
        if not kpath.is_absolute():
            kpath = Path(__file__).parent.parent / kpath
        if kpath.is_file():
            content = kpath.read_text(encoding="utf-8").strip()
            lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#") and l.strip() != "---"]
            if lines:
                return content
        return ""

    def send(self, user_message: str, stream: bool = None) -> str:
        """Nachricht senden und Antwort erhalten. Unterstuetzt Tool-Calls."""
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

        # Loop fuer Tool-Calls
        while True:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            if self.tools:
                kwargs["tools"] = self.tools

            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]

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
                    result = execute_tool(tool_call.function.name, args)

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                    messages.append(tool_msg)
                    self.history.append(tool_msg)

                continue

            text = choice.message.content or ""
            if stream and text:
                print(text, end="", flush=True)
                print()

            self.history.append({"role": "assistant", "content": text})
            self._trim_history()
            return text

    def _trim_history(self) -> None:
        """Max-History einhalten."""
        while len(self.history) > self.max_history * 2 + 1:
            self.history.pop(1)
            self.history.pop(1)

    def get_history(self) -> list[dict]:
        """Konversationsverlauf zurueckgeben (ohne System-Prompt)."""
        return [m for m in self.history if m["role"] != "system"]

    def clear_history(self) -> None:
        """Konversationsverlauf loeschen."""
        self.history = [{"role": "system", "content": self.system_prompt}]
