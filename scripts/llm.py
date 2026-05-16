"""HotelAgent — LLM-Client: Multi-Provider (OpenAI, Claude, OpenRouter debug)."""

import os
from scripts.config_manager import get_llm_config


# ---------------------------------------------------------------------------
# Provider-Definitionen
# ---------------------------------------------------------------------------

PROVIDERS = {
    "openai": {
        "name": "OpenAI API",
        "env_key": "OPENAI_API_KEY",
        "base_url": None,
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "o3-mini",
        ],
    },
    "claude": {
        "name": "Anthropic Claude API",
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": None,
        "models": [
            "claude-sonnet-4-6",
            "claude-opus-4-6",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250514",
        ],
    },
    "openrouter": {
        "name": "OpenRouter (Debug/CLI)",
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-6",
            "deepseek/deepseek-v4-flash",
            "google/gemini-2.5-flash",
        ],
    },
}


def get_provider_name() -> str:
    """Aktuellen Provider-Namen zurueckgeben."""
    config = get_llm_config()
    return config.get("provider", "openrouter")


def get_provider_display_name() -> str:
    """Anzeigenamen des aktuellen Providers zurueckgeben."""
    provider = get_provider_name()
    return PROVIDERS.get(provider, {}).get("name", provider)


def get_api_key(provider: str = None) -> str:
    """API-Key fuer den angegebenen Provider laden."""
    if provider is None:
        provider = get_provider_name()
    env_key = PROVIDERS.get(provider, {}).get("env_key", "OPENROUTER_API_KEY")
    key = os.getenv(env_key, "")
    if not key:
        raise ValueError(
            f"API-Key nicht gesetzt: {env_key}\n"
            f"Bitte in .env eintragen oder in den Einstellungen konfigurieren."
        )
    return key


# ---------------------------------------------------------------------------
# Client-Erstellung
# ---------------------------------------------------------------------------

def get_client(provider: str = None):
    """LLM-Client fuer den konfigurierten Provider erstellen.

    Fuer OpenAI und OpenRouter: OpenAI-Client.
    Fuer Claude: Anthropic-Client.
    """
    if provider is None:
        provider = get_provider_name()

    api_key = get_api_key(provider)

    if provider == "claude":
        from anthropic import Anthropic
        return Anthropic(api_key=api_key)
    else:
        from openai import OpenAI
        base_url = PROVIDERS.get(provider, {}).get("base_url")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)


# ---------------------------------------------------------------------------
# Unified Chat-Interface
# ---------------------------------------------------------------------------

def chat(messages: list[dict], stream: bool = None) -> str:
    """Nachricht an LLM senden und Antwort zurueckgeben.

    Funktioniert einheitlich fuer alle Provider.
    """
    config = get_llm_config()
    provider = config.get("provider", "openrouter")

    if stream is None:
        stream = config.get("streaming", False)

    if provider == "claude":
        return _chat_claude(config, messages, stream)
    else:
        return _chat_openai(config, messages, stream, provider)


def _chat_openai(config: dict, messages: list[dict], stream: bool, provider: str) -> str:
    """Chat via OpenAI-kompatible API (OpenAI, OpenRouter)."""
    client = get_client(provider)

    if stream:
        return _chat_openai_stream(client, config, messages)
    else:
        response = client.chat.completions.create(
            model=config.get("model", "gpt-4o-mini"),
            messages=messages,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048),
        )
        return response.choices[0].message.content


def _chat_openai_stream(client, config: dict, messages: list[dict]) -> str:
    """OpenAI-Chat mit Streaming."""
    response_stream = client.chat.completions.create(
        model=config.get("model", "gpt-4o-mini"),
        messages=messages,
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 2048),
        stream=True,
    )

    full_response = []
    for chunk in response_stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            full_response.append(delta.content)
    print()

    return "".join(full_response)


def _chat_claude(config: dict, messages: list[dict], stream: bool) -> str:
    """Chat via Anthropic Claude API."""
    client = get_client("claude")

    # System-Prompt extrahieren (Claude braucht ihn separat)
    system_prompt = ""
    chat_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_prompt += msg["content"] + "\n"
        else:
            chat_messages.append(msg)

    if not chat_messages:
        chat_messages = [{"role": "user", "content": "Hallo"}]

    kwargs = {
        "model": config.get("model", "claude-sonnet-4-6"),
        "messages": chat_messages,
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 2048),
    }
    if system_prompt.strip():
        kwargs["system"] = system_prompt.strip()

    if stream:
        return _chat_claude_stream(client, kwargs)
    else:
        response = client.messages.create(**kwargs)
        return response.content[0].text


def _chat_claude_stream(client, kwargs: dict) -> str:
    """Claude-Chat mit Streaming."""
    full_response = []
    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response.append(text)
    print()
    return "".join(full_response)


# ---------------------------------------------------------------------------
# Einfacher LLM-Aufruf (fuer Scripts die nicht den vollen Agent brauchen)
# ---------------------------------------------------------------------------

def llm_call(messages: list[dict], temperature: float = 0.7, max_tokens: int = 2048) -> str:
    """Einmaliger LLM-Aufruf — Provider-unabhaengig.

    Fuer Scripts wie documents.py, web_scraper.py, price_manager.py, email_processor.py
    die nur einen simplen Chat-Call brauchen (ohne Tools, ohne Streaming).
    """
    config = get_llm_config()
    provider = config.get("provider", "openrouter")
    model = config.get("model", "gpt-4o-mini")

    if provider == "claude":
        client = get_client("claude")

        system_prompt = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt += msg["content"] + "\n"
            else:
                chat_messages.append(msg)

        if not chat_messages:
            chat_messages = [{"role": "user", "content": "Hallo"}]

        kwargs = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_prompt.strip():
            kwargs["system"] = system_prompt.strip()

        response = client.messages.create(**kwargs)
        return response.content[0].text
    else:
        client = get_client(provider)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
