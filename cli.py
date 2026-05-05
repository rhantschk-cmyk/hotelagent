"""HotelAgent — CLI (Typer + InquirerPy + Rich)."""

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="hotelagent",
    help="HotelAgent — Dein KI-Hotelassistent.",
    no_args_is_help=True,
)

console = Console()

EXPECTED_COMMANDS = ["doctor", "start", "config", "gui", "memory", "chat", "voice", "upload", "check-web", "check-mails"]


@app.command()
def doctor():
    """Projektstruktur und Abhaengigkeiten pruefen."""
    from scripts.doctor import run_all

    success = run_all()
    raise typer.Exit(code=0 if success else 1)


@app.command()
def start():
    """Agent starten (interaktiver Modus)."""
    console.print(Panel("HotelAgent", subtitle="Dein KI-Hotelassistent", style="bold cyan"))
    chat()


@app.command()
def config():
    """Konfiguration anzeigen und bearbeiten."""
    from InquirerPy import inquirer
    from scripts.config_manager import load_config, save_config
    import yaml

    action = inquirer.select(
        message="Was moechtest du tun?",
        choices=[
            "Konfiguration anzeigen",
            "LLM-Modell aendern",
            "Temperatur aendern",
            "Zurueck",
        ],
    ).execute()

    cfg = load_config()

    if action == "Konfiguration anzeigen":
        console.print(Panel(yaml.dump(cfg, default_flow_style=False, allow_unicode=True).strip(), title="settings.yaml"))
    elif action == "LLM-Modell aendern":
        model = inquirer.text(
            message="Neues Modell:",
            default=cfg["llm"]["model"],
        ).execute()
        cfg["llm"]["model"] = model
        save_config(cfg)
        console.print(f"[green]Modell auf '{model}' gesetzt.[/green]")
    elif action == "Temperatur aendern":
        temp = inquirer.number(
            message="Neue Temperatur (0.0 - 2.0):",
            default=cfg["llm"]["temperature"],
            float_allowed=True,
            min_allowed=0.0,
            max_allowed=2.0,
        ).execute()
        cfg["llm"]["temperature"] = float(temp)
        save_config(cfg)
        console.print(f"[green]Temperatur auf {temp} gesetzt.[/green]")


@app.command()
def gui():
    """Grafische Oberflaeche starten."""
    from gui import launch_gui
    console.print("[bold cyan]Starte HotelAgent GUI...[/bold cyan]")
    launch_gui()


@app.command()
def memory():
    """Konversationsspeicher verwalten."""
    from InquirerPy import inquirer
    from scripts.memory import list_conversations, delete_conversation, delete_all_conversations
    from rich.table import Table

    action = inquirer.select(
        message="Konversationsspeicher:",
        choices=[
            "Konversationen auflisten",
            "Konversation loeschen",
            "Alle loeschen",
            "Zurueck",
        ],
    ).execute()

    if action == "Konversationen auflisten":
        convos = list_conversations()
        if not convos:
            console.print("[dim]Keine Konversationen gespeichert.[/dim]")
            return
        table = Table(title="Konversationen")
        table.add_column("ID", style="cyan")
        table.add_column("Erstellt", style="dim")
        table.add_column("Nachrichten", justify="right")
        table.add_column("Vorschau")
        for c in convos:
            table.add_row(c["id"], c["created_at"][:16], str(c["messages"]), c["preview"])
        console.print(table)

    elif action == "Konversation loeschen":
        convos = list_conversations()
        if not convos:
            console.print("[dim]Keine Konversationen vorhanden.[/dim]")
            return
        choices = [f"{c['id']} — {c['preview']}" for c in convos] + ["Zurueck"]
        choice = inquirer.select(message="Welche loeschen?", choices=choices).execute()
        if choice != "Zurueck":
            cid = choice.split(" — ")[0]
            if delete_conversation(cid):
                console.print(f"[green]Konversation '{cid}' geloescht.[/green]")

    elif action == "Alle loeschen":
        confirm = inquirer.confirm(message="Wirklich ALLE Konversationen loeschen?", default=False).execute()
        if confirm:
            count = delete_all_conversations()
            console.print(f"[green]{count} Konversation(en) geloescht.[/green]")


@app.command()
def chat():
    """Text-Chat im Terminal."""
    from datetime import datetime
    from agents.hotel_agent import HotelAgent
    from scripts.memory import save_conversation

    conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    agent = HotelAgent(conversation_id=conversation_id)

    console.print("[bold cyan]HotelAgent Chat[/bold cyan] (/exit zum Beenden)")
    console.print()

    while True:
        try:
            user_input = console.input("[bold green]Du:[/bold green] ")
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.strip().lower() in ("/exit", "/quit", "/q"):
            break

        if not user_input.strip():
            continue

        console.print("[bold blue]Agent:[/bold blue] ", end="")
        agent.send(user_input)

        # Nach jeder Nachricht speichern
        save_conversation(conversation_id, agent.history)

    console.print("\n[dim]Chat beendet.[/dim]")


@app.command()
def voice():
    """Sprach-Chat im Terminal."""
    from datetime import datetime
    from agents.hotel_agent import HotelAgent
    from scripts.memory import save_conversation
    from scripts.voice import VoiceRecorder, SpeechToText, TextToSpeech

    conversation_id = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    agent = HotelAgent(conversation_id=conversation_id)
    recorder = VoiceRecorder()
    tts = TextToSpeech()

    console.print("[bold cyan]HotelAgent Voice-Chat[/bold cyan]")
    console.print("Druecke [bold]Enter[/bold] um Aufnahme zu starten/stoppen. /exit zum Beenden.\n")

    while True:
        try:
            cmd = console.input("[bold green]Enter = Aufnahme starten >[/bold green] ")
            if cmd.strip().lower() in ("/exit", "/quit", "/q"):
                break
        except (KeyboardInterrupt, EOFError):
            break

        console.print("[red]Aufnahme laeuft... Enter zum Stoppen[/red]")
        try:
            audio = recorder.record_until_enter()
        except RuntimeError as e:
            console.print(f"[red]{e}[/red]")
            continue

        if audio is None or len(audio) < SAMPLE_RATE * 0.3:
            console.print("[dim]Zu kurz, uebersprungen.[/dim]")
            continue

        console.print("[dim]Transkribiere...[/dim]")
        try:
            stt = SpeechToText()
            user_text = stt.transcribe(audio)
        except Exception as e:
            console.print(f"[red]Transkription fehlgeschlagen: {e}[/red]")
            continue

        console.print(f"[bold green]Du:[/bold green] {user_text}")
        console.print("[bold blue]Agent:[/bold blue] ", end="")
        response = agent.send(user_text, stream=False)

        # Vorlesen
        tts.speak(response)

        save_conversation(conversation_id, agent.history)

    console.print("\n[dim]Voice-Chat beendet.[/dim]")


# Minimale Konstante fuer Voice-Check
SAMPLE_RATE = 16000


@app.command()
def upload(
    datei: str = typer.Argument(None, help="Pfad zur Datei"),
):
    """Dokument hochladen und analysieren."""
    from scripts.documents import upload_file, analyze_document, save_to_knowledge
    from pathlib import Path

    if not datei:
        from InquirerPy import inquirer
        datei = inquirer.filepath(
            message="Datei auswaehlen:",
            validate=lambda p: Path(p).is_file(),
            invalid_message="Datei nicht gefunden.",
        ).execute()

    console.print(f"[dim]Lade '{datei}' hoch...[/dim]")
    try:
        dest = upload_file(datei)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=1)

    console.print(f"[green]Gespeichert: {dest}[/green]")
    console.print("[dim]Analysiere Dokument...[/dim]")

    try:
        analysis = analyze_document(dest)
    except Exception as e:
        console.print(f"[red]Analyse fehlgeschlagen: {e}[/red]")
        raise typer.Exit(code=1)

    console.print(Panel(analysis, title=f"Analyse: {Path(datei).name}"))

    save_to_knowledge(Path(datei).name, analysis)
    console.print("[green]Wissen in KNOWLEDGE.md gespeichert.[/green]")


@app.command()
def check_web(
    url: str = typer.Argument("https://hotel-oedhof.de", help="URL der Hotel-Website"),
    max_pages: int = typer.Option(30, help="Maximale Anzahl zu crawlender Seiten"),
):
    """Hotel-Website crawlen und Wissen extrahieren."""
    from scripts.web_scraper import crawl_site, analyze_website
    from scripts.documents import save_to_knowledge

    console.print(f"[bold cyan]Crawle {url}...[/bold cyan]\n")
    pages = crawl_site(url, max_pages=max_pages)

    if not pages:
        console.print("[red]Keine Seiten gefunden.[/red]")
        raise typer.Exit(code=1)

    console.print(f"\n[green]{len(pages)} Seiten gecrawlt.[/green]")
    console.print("[dim]Analysiere Website...[/dim]\n")

    analysis = analyze_website(pages)
    console.print(Panel(analysis, title=f"Website-Analyse: {url}"))

    save_to_knowledge(f"Website: {url}", analysis)
    console.print("[green]Wissen in KNOWLEDGE.md gespeichert.[/green]")


@app.command()
def check_mails():
    """E-Mails pruefen und automatisch Entwuerfe aus Vorlagen erstellen."""
    from scripts.email_processor import process_inbox
    from rich.table import Table

    console.print(Panel("E-Mail-Verarbeitung", subtitle="Anfragen erkennen & Entwuerfe erstellen", style="bold cyan"))

    results = process_inbox()

    if not results:
        console.print("\n[dim]Keine E-Mails verarbeitet.[/dim]")
        return

    # Zusammenfassung
    table = Table(title="\nZusammenfassung")
    table.add_column("Betreff", style="cyan", max_width=40)
    table.add_column("Von", max_width=30)
    table.add_column("Status")
    table.add_column("Details", style="dim")

    created = 0
    for r in results:
        status_style = "green" if r["status"] == "entwurf_erstellt" else "dim"
        detail = r.get("template_used", r.get("reason", ""))
        table.add_row(
            r["subject"][:40],
            r["from"][:30],
            f"[{status_style}]{r['status']}[/{status_style}]",
            detail[:40],
        )
        if r["status"] == "entwurf_erstellt":
            created += 1

    console.print(table)
    console.print(f"\n[bold green]{created}[/bold green] Entwurf/Entwuerfe erstellt, "
                  f"[dim]{len(results) - created} uebersprungen[/dim]")


if __name__ == "__main__":
    app()
