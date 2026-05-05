"""HotelAgent — LLM-Client: OpenRouter via OpenAI-Bibliothek."""

import os
from openai import OpenAI
from scripts.config_manager import get_llm_config


def get_client() -> OpenAI:
    """OpenAI-Client fuer OpenRouter erstellen."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY ist nicht gesetzt. Bitte in .env eintragen.")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def chat(messages: list[dict], stream: bool = None) -> str:
    """Nachricht an LLM senden und Antwort zurueckgeben."""
    client = get_client()
    config = get_llm_config()

    if stream is None:
        stream = config.get("streaming", False)

    if stream:
        return _chat_stream(client, config, messages)
    else:
        return _chat_sync(client, config, messages)


def _chat_sync(client: OpenAI, config: dict, messages: list[dict]) -> str:
    """Synchroner Chat ohne Streaming."""
    response = client.chat.completions.create(
        model=config.get("model", "openai/gpt-4o"),
        messages=messages,
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 2048),
    )
    return response.choices[0].message.content


def _chat_stream(client: OpenAI, config: dict, messages: list[dict]) -> str:
    """Chat mit Streaming — gibt Tokens live aus und gibt Gesamtantwort zurueck."""
    stream = client.chat.completions.create(
        model=config.get("model", "openai/gpt-4o"),
        messages=messages,
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 2048),
        stream=True,
    )

    full_response = []
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            full_response.append(delta.content)
    print()  # Zeilenumbruch am Ende

    return "".join(full_response)
