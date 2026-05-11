"""HotelAgent — E-Mail-Verarbeitung: Anfragen erkennen, Vorlagen zuordnen, Entwuerfe erstellen."""

import json
from rich.console import Console

from scripts.config_manager import get_llm_config
from scripts.llm import get_client
from scripts.email_provider import get_provider

console = Console()


# ---------------------------------------------------------------------------
# LLM-Helfer
# ---------------------------------------------------------------------------

def _llm_call(system: str, user: str, temperature: float = 0.2) -> str:
    """Einfacher LLM-Aufruf mit System- und User-Prompt."""
    client = get_client()
    config = get_llm_config()
    response = client.chat.completions.create(
        model=config.get("model", "openai/gpt-4o"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=config.get("max_tokens", 2048),
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Schritt 1: Anfrage erkennen
# ---------------------------------------------------------------------------

def classify_email(email: dict) -> bool:
    """Pruefen ob eine E-Mail eine Gaesteanfrage ist."""
    system = (
        "Du bist ein Klassifikator fuer Hotel-E-Mails. "
        "Bestimme ob die E-Mail eine Gaesteanfrage ist (Reservierung, Preisanfrage, "
        "Verfuegbarkeit, Buchung, Zimmeranfrage, etc.). "
        "Antworte NUR mit 'JA' oder 'NEIN'. Nichts anderes."
    )
    user = f"Betreff: {email['subject']}\nVon: {email['from']}\n\n{email['body'][:3000]}"

    result = _llm_call(system, user)
    return result.strip().upper().startswith("JA")


# ---------------------------------------------------------------------------
# Schritt 2: Vorlage zuordnen
# ---------------------------------------------------------------------------

def match_template(email: dict, templates: list[dict]) -> dict | None:
    """Die passende Vorlage fuer eine Anfrage finden.

    Returns:
        Die passende Vorlage oder None wenn keine passt.
    """
    if not templates:
        return None

    # Vorlagen-Uebersicht fuer LLM erstellen
    template_list = ""
    for i, t in enumerate(templates):
        # Nur Betreff und ersten Teil des Body zeigen
        preview = t["body"][:300].replace("\n", " ")
        template_list += f"\n[{i}] Betreff: {t['subject']}\n    Vorschau: {preview}\n"

    system = (
        "Du bist ein Zuordnungssystem fuer Hotel-E-Mail-Vorlagen. "
        "Dir wird eine Gaesteanfrage und eine Liste von Vorlagen gezeigt. "
        "Waehle die Vorlage die am besten zur Anfrage passt. "
        "Antworte NUR mit der Nummer der Vorlage (z.B. '3'). "
        "Wenn KEINE Vorlage passt, antworte mit 'KEINE'."
    )
    user = (
        f"=== GAESTEANFRAGE ===\n"
        f"Betreff: {email['subject']}\n"
        f"Von: {email['from']}\n\n"
        f"{email['body'][:3000]}\n\n"
        f"=== VERFUEGBARE VORLAGEN ===\n{template_list}"
    )

    result = _llm_call(system, user)

    if "KEINE" in result.upper():
        return None

    # Nummer extrahieren
    import re
    numbers = re.findall(r"\d+", result)
    if not numbers:
        return None

    idx = int(numbers[0])
    if 0 <= idx < len(templates):
        return templates[idx]

    return None


# ---------------------------------------------------------------------------
# Schritt 3: Vorlage anpassen
# ---------------------------------------------------------------------------

def adapt_template(email: dict, template: dict) -> str:
    """Vorlage minimal anpassen: Platzhalter fuellen, irrelevante Optionen entfernen.

    WICHTIG: Die Vorlage wird 1:1 uebernommen. Nur:
    - Anrede personalisieren (Herr/Frau + Name)
    - Nicht angefragte Optionen/Preisstufen entfernen
    - 7-Tage-Option IMMER beibehalten (Rabatt)
    - Datumsangaben einsetzen
    - Keine Umformulierungen, keine eigenen Saetze
    """
    system = (
        "Du passt eine Hotel-E-Mail-Vorlage an eine konkrete Gaesteanfrage an.\n\n"
        "STRIKTE REGELN:\n"
        "1. Uebernimm die Vorlage 1:1 — gleiche Formulierungen, gleiche Struktur, gleicher Tonfall.\n"
        "2. Du darfst NUR folgende Aenderungen vornehmen:\n"
        "   - Anrede personalisieren: 'Herr / Frau ...' → z.B. 'Herr Schmidt'\n"
        "   - Konkrete Daten/Zeitraeume aus der Anfrage einsetzen\n"
        "   - Nicht angefragte Aufenthaltsdauern/Preisstufen ENTFERNEN "
        "(z.B. wenn nur 5 Naechte angefragt: nur 5-Naechte-Preis behalten)\n"
        "   - Die 7-Tage/7-Naechte-Option IMMER beibehalten (Rabatthinweis)\n"
        "   - Offensichtlich irrelevante Abschnitte entfernen\n"
        "3. Du darfst NIEMALS:\n"
        "   - Saetze umformulieren oder in eigenen Worten schreiben\n"
        "   - Neue Saetze oder Absaetze hinzufuegen\n"
        "   - Schreiben 'hierfuer sollten Sie einen Mitarbeiter kontaktieren'\n"
        "   - Schreiben 'hier bin ich mir nicht sicher' oder aehnliches\n"
        "   - Die Grussformel, Signatur oder Formatierung aendern\n"
        "4. Gib NUR den angepassten E-Mail-Text zurueck, keine Erklaerungen."
    )

    user = (
        f"=== GAESTEANFRAGE ===\n"
        f"Von: {email['from']}\n"
        f"Betreff: {email['subject']}\n\n"
        f"{email['body'][:3000]}\n\n"
        f"=== VORLAGE (1:1 uebernehmen, nur minimal anpassen) ===\n"
        f"{template['body']}"
    )

    return _llm_call(system, user, temperature=0.1)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def process_inbox() -> list[dict]:
    """Komplette E-Mail-Verarbeitungs-Pipeline.

    1. Posteingang lesen (ungelesene E-Mails)
    2. Anfragen erkennen
    3. Vorlagen laden und zuordnen
    4. Vorlagen anpassen
    5. Entwuerfe erstellen

    Returns:
        Liste von Ergebnis-Dicts mit Status pro E-Mail.
    """
    results = []
    provider = get_provider()

    # 1. Posteingang lesen
    console.print("[dim]Lese Posteingang...[/dim]")
    try:
        emails = provider.get_inbox_emails(only_unread=True)
    except Exception as e:
        console.print(f"[red]Fehler beim Lesen des Posteingangs: {e}[/red]")
        return results

    if not emails:
        console.print("[dim]Keine ungelesenen E-Mails.[/dim]")
        return results

    console.print(f"[dim]{len(emails)} ungelesene E-Mail(s) gefunden.[/dim]")

    # 2. Vorlagen laden
    console.print("[dim]Lade Vorlagen...[/dim]")
    try:
        templates = provider.get_templates()
    except Exception as e:
        console.print(f"[red]Fehler beim Laden der Vorlagen: {e}[/red]")
        return results

    if not templates:
        console.print("[yellow]Keine Vorlagen gefunden. Pruefe das Gmail-Label.[/yellow]")
        return results

    console.print(f"[dim]{len(templates)} Vorlage(n) geladen.[/dim]")

    # 3. Jede E-Mail verarbeiten
    for email in emails:
        entry = {
            "email_id": email["id"],
            "from": email["from"],
            "subject": email["subject"],
            "status": "uebersprungen",
            "reason": "",
            "draft_id": None,
        }

        console.print(f"\n[bold]Verarbeite:[/bold] {email['subject']}")
        console.print(f"  Von: {email['from']}")

        # Ist es eine Gaesteanfrage?
        console.print("  [dim]Klassifiziere...[/dim]")
        try:
            is_inquiry = classify_email(email)
        except Exception as e:
            entry["reason"] = f"Klassifikation fehlgeschlagen: {e}"
            console.print(f"  [red]{entry['reason']}[/red]")
            results.append(entry)
            continue

        if not is_inquiry:
            entry["reason"] = "Keine Gaesteanfrage"
            console.print(f"  [dim]{entry['reason']} — uebersprungen[/dim]")
            results.append(entry)
            continue

        # Vorlage zuordnen
        console.print("  [dim]Suche passende Vorlage...[/dim]")
        try:
            template = match_template(email, templates)
        except Exception as e:
            entry["reason"] = f"Vorlagen-Zuordnung fehlgeschlagen: {e}"
            console.print(f"  [red]{entry['reason']}[/red]")
            results.append(entry)
            continue

        if not template:
            entry["reason"] = "Keine passende Vorlage gefunden"
            console.print(f"  [yellow]{entry['reason']} — uebersprungen[/yellow]")
            results.append(entry)
            continue

        console.print(f"  [dim]Vorlage: {template['subject']}[/dim]")

        # Vorlage anpassen
        console.print("  [dim]Passe Vorlage an...[/dim]")
        try:
            adapted_body = adapt_template(email, template)
        except Exception as e:
            entry["reason"] = f"Vorlagen-Anpassung fehlgeschlagen: {e}"
            console.print(f"  [red]{entry['reason']}[/red]")
            results.append(entry)
            continue

        # Entwurf als Antwort erstellen
        console.print("  [dim]Erstelle Entwurf...[/dim]")
        try:
            # Absender-Adresse extrahieren
            from_addr = email["from"]
            # E-Mail-Adresse aus "Name <email>" extrahieren
            import re
            match = re.search(r"<([^>]+)>", from_addr)
            reply_to = match.group(1) if match else from_addr

            draft = provider.create_reply_draft(
                thread_id=email["thread_id"],
                message_id=email["message_id"],
                to=reply_to,
                subject=email["subject"],
                body=adapted_body,
            )

            entry["status"] = "entwurf_erstellt"
            entry["draft_id"] = draft["id"]
            entry["template_used"] = template["subject"]
            console.print(f"  [green]Entwurf erstellt (ID: {draft['id']})[/green]")

        except Exception as e:
            entry["reason"] = f"Entwurf-Erstellung fehlgeschlagen: {e}"
            console.print(f"  [red]{entry['reason']}[/red]")

        results.append(entry)

    return results
