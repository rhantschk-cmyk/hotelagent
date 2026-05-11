"""HotelAgent — Price-Manager: Preise extrahieren, speichern, berechnen."""

import re
from datetime import datetime
from pathlib import Path

from scripts.config_manager import get_llm_config
from scripts.llm import get_client

PROJECT_ROOT = Path(__file__).parent.parent
PRICES_PATH = PROJECT_ROOT / "PRICES.md"

# ---------------------------------------------------------------------------
# Preise extrahieren (LLM-gestuetzt)
# ---------------------------------------------------------------------------

EXTRACTION_PROMPT = """\
Du bist ein Preis-Extraktions-System fuer ein Hotel. Analysiere den folgenden Text und extrahiere ALLE Preisinformationen.

Erstelle eine strukturierte Ausgabe im folgenden Markdown-Format. Verwende EXAKT dieses Format:

## Zimmerpreise

| Kategorie | Dauer | Preis pro Person/Nacht | Hinweis |
|-----------|-------|------------------------|---------|
| ... | ... | ... | ... |

## Zuschlaege & Ermaessigungen

| Art | Betrag | Bedingung |
|-----|--------|-----------|
| ... | ... | ... |

## Arrangements & Pakete

| Name | Dauer | Preis ab | Zimmertyp | Enthaltene Leistungen |
|------|-------|----------|-----------|----------------------|
| ... | ... | ... | ... | ... |

## Wellness & Anwendungen

| Anwendung | Dauer | Preis |
|-----------|-------|-------|
| ... | ... | ... |

## Sonstige Preise

| Leistung | Preis | Hinweis |
|----------|-------|---------|
| ... | ... | ... |

REGELN:
- Schreibe NUR Preise die EXPLIZIT im Text stehen. Erfinde keine Preise.
- Alle Betraege mit Waehrungszeichen (z.B. 122 €).
- Wenn eine Kategorie keine Preise hat, lasse die Tabelle weg.
- Pro Person/Nacht, pro Nacht, pauschal — immer die Einheit angeben.
- Bei Arrangements: alle enthaltenen Leistungen auflisten.
"""


def extract_prices_from_text(text: str, source_name: str = "Unbekannt") -> str:
    """Preise aus Text via LLM extrahieren. Gibt strukturiertes Markdown zurueck."""
    if not text.strip():
        return ""

    # Text kuerzen falls zu lang
    max_chars = 25000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... gekuerzt ...]"

    client = get_client()
    config = get_llm_config()

    response = client.chat.completions.create(
        model=config.get("model", "openai/gpt-4o"),
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
        max_tokens=4096,
    )

    return response.choices[0].message.content.strip()


def save_to_prices(source_name: str, extracted_prices: str) -> None:
    """Extrahierte Preise in PRICES.md speichern (ersetzt Eintrag gleicher Quelle oder haengt an)."""
    if not extracted_prices.strip():
        return

    # Bestehende PRICES.md lesen
    if PRICES_PATH.is_file():
        content = PRICES_PATH.read_text(encoding="utf-8")
    else:
        content = "# HotelAgent — Preisdatenbank\n\nHier werden alle Preise strukturiert gespeichert.\n\n---\n\n"

    # Pruefen ob Quelle schon existiert — wenn ja, ersetzen
    marker_start = f"<!-- QUELLE: {source_name} -->"
    marker_end = f"<!-- /QUELLE: {source_name} -->"

    new_entry = (
        f"{marker_start}\n"
        f"## Quelle: {source_name}\n"
        f"**Aktualisiert am:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{extracted_prices}\n\n"
        f"{marker_end}\n\n---\n"
    )

    if marker_start in content:
        # Bestehenden Eintrag ersetzen
        pattern = re.escape(marker_start) + r".*?" + re.escape(marker_end)
        # Auch den trailing --- mitnehmen
        pattern_full = pattern + r"\s*---\s*"
        content = re.sub(pattern_full, new_entry, content, flags=re.DOTALL)
    else:
        # Neuen Eintrag anhaengen
        content += "\n" + new_entry

    PRICES_PATH.write_text(content, encoding="utf-8")


def load_prices() -> str:
    """Komplette PRICES.md als Text laden."""
    if not PRICES_PATH.is_file():
        return ""
    return PRICES_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Preisberechnung (deterministisch)
# ---------------------------------------------------------------------------

PRICING_RULES_PATH = PROJECT_ROOT / "config" / "pricing_rules.md"


def load_pricing_rules() -> str:
    """Berechnungsregeln laden."""
    if PRICING_RULES_PATH.is_file():
        return PRICING_RULES_PATH.read_text(encoding="utf-8").strip()
    return ""


def calculate_price(query: str) -> str:
    """Preisanfrage beantworten.

    Liest PRICES.md + Berechnungsregeln, gibt beides an das LLM weiter,
    und laesst es die exakte Berechnung Schritt fuer Schritt durchfuehren.
    """
    prices_text = load_prices()
    if not prices_text.strip():
        return "Keine Preisdaten vorhanden. Bitte zuerst die Website crawlen oder Preislisten hochladen."

    rules_text = load_pricing_rules()

    client = get_client()
    config = get_llm_config()

    system = (
        "Du bist ein exakter Preisrechner fuer ein Hotel. Dir wird eine Preisdatenbank (PRICES.md), "
        "Berechnungsregeln und eine Anfrage gegeben.\n\n"
        "STRIKTE REGELN:\n"
        "1. Verwende AUSSCHLIESSLICH Preise, Zuschlaege und Ermaessigungen die EXPLIZIT in der "
        "Preisdatenbank stehen. Erfinde KEINE Preise und errechne KEINE eigenen Nachtpreise.\n"
        "2. Befolge die Berechnungsregeln EXAKT.\n"
        "3. Schreibe JEDEN Rechenschritt explizit auf — Zeile fuer Zeile:\n"
        "   Grundpreis: ... €\n"
        "   × Naechte: ...\n"
        "   × Personen: ...\n"
        "   = Zwischensumme: ... €\n"
        "   + Zuschlag XY: ... €\n"
        "   - Ermaessigung XY: ... €\n"
        "   = Gesamtpreis: ... €\n"
        "4. Wenn ein Preis oder Zuschlag NICHT in der Preisdatenbank steht, sage das klar und "
        "empfehle dem Gast, direkt beim Hotel nachzufragen. Schlage KEIN alternatives "
        "Paket oder Arrangement vor, es sei denn der Gast fragt explizit nach Alternativen.\n"
        "5. Bleibe beim angefragten Arrangement/Zimmertyp. Ersetze es NIEMALS durch ein anderes.\n"
        "6. Berechne KEINE Nachtpreise durch Division (z.B. Paketpreis ÷ Naechte). "
        "Nur wenn die Preisdatenbank explizit einen Zuschlag pro zusaetzliche Nacht nennt, "
        "verwende diesen.\n"
        "7. Antworte auf Deutsch.\n"
    )

    user_parts = [f"=== PREISDATENBANK ===\n{prices_text}"]
    if rules_text:
        user_parts.append(f"=== BERECHNUNGSREGELN ===\n{rules_text}")
    user_parts.append(f"=== ANFRAGE ===\n{query}")

    response = client.chat.completions.create(
        model=config.get("model", "openai/gpt-4o"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ],
        temperature=0.0,
        max_tokens=2048,
    )

    return response.choices[0].message.content.strip()
