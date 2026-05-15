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

EXPECTED_COMMANDS = ["doctor", "start", "config", "gui", "memory", "chat", "voice", "upload", "check-web", "check-mails", "email-setup", "agents", "automations", "scheduler"]

DISCLAIMER = "Hinweis: KI-generierte Antworten koennen fehlerhaft sein. Keine Haftung durch den Entwickler. Nutzung auf eigene Verantwortung."


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
    console.print(f"[dim]{DISCLAIMER}[/dim]")
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
    console.print(f"[dim]{DISCLAIMER}[/dim]")
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


@app.command()
def email_setup():
    """E-Mail-Provider einrichten (Gmail, Outlook, GMX, Web.de, IMAP/SMTP, ...)."""
    from InquirerPy import inquirer
    from scripts.email_provider import (
        KNOWN_PROVIDERS, get_provider_display_name, get_provider,
        setup_imap_provider, setup_gmail_oauth, is_any_provider_configured,
    )

    current = get_provider_display_name()
    configured = is_any_provider_configured()
    status = "[green]konfiguriert[/green]" if configured else "[yellow]nicht konfiguriert[/yellow]"
    console.print(Panel(f"Aktueller Provider: {current} ({status})",
                        title="E-Mail-Provider", style="bold cyan"))

    # Provider-Auswahl
    choices = ["Gmail (OAuth2 API)"]
    provider_map = {"Gmail (OAuth2 API)": "gmail_oauth"}
    for key, val in KNOWN_PROVIDERS.items():
        label = f"{val['name']}"
        if val.get("note"):
            label += f" — {val['note'][:50]}"
        choices.append(label)
        provider_map[label] = key
    choices.append("Benutzerdefiniert (IMAP/SMTP)")
    provider_map["Benutzerdefiniert (IMAP/SMTP)"] = "custom"
    choices.append("Zurueck")

    choice = inquirer.select(message="Provider waehlen:", choices=choices).execute()
    if choice == "Zurueck":
        return

    key = provider_map.get(choice, "")

    if key == "gmail_oauth":
        setup_gmail_oauth()
        console.print("[green]Gmail OAuth2 als Provider konfiguriert.[/green]")
        console.print("[dim]Stelle sicher dass config/credentials.json vorhanden ist.[/dim]")
        return

    # IMAP/SMTP — Zugangsdaten abfragen
    username = inquirer.text(message="E-Mail-Adresse / Benutzername:").execute()
    password = inquirer.secret(message="Passwort / App-Passwort:").execute()

    if not username or not password:
        console.print("[red]E-Mail und Passwort sind erforderlich.[/red]")
        return

    if key == "custom":
        imap_host = inquirer.text(message="IMAP-Server:").execute()
        imap_port = int(inquirer.text(message="IMAP-Port:", default="993").execute())
        smtp_host = inquirer.text(message="SMTP-Server:").execute()
        smtp_port = int(inquirer.text(message="SMTP-Port:", default="587").execute())

        setup_imap_provider(
            imap_host=imap_host, imap_port=imap_port,
            smtp_host=smtp_host, smtp_port=smtp_port,
            username=username, password=password,
        )
    else:
        setup_imap_provider(preset_key=key, username=username, password=password)

    console.print(f"[green]E-Mail-Provider konfiguriert![/green]")

    # Verbindung testen?
    test = inquirer.confirm(message="Verbindung jetzt testen?", default=True).execute()
    if test:
        console.print("[dim]Teste Verbindung...[/dim]")
        provider = get_provider()
        success, msg = provider.test_connection()
        if success:
            console.print(f"[green]{msg}[/green]")
        else:
            console.print(f"[red]{msg}[/red]")


@app.command()
def agents():
    """Agents verwalten: erstellen, auflisten, bearbeiten, loeschen."""
    from InquirerPy import inquirer
    from scripts.agent_manager import (
        create_agent, list_agents, get_agent_config_by_name,
        update_agent, delete_agent, load_agent, get_all_tool_names,
    )
    from scripts.memory import save_conversation
    from rich.table import Table

    action = inquirer.select(
        message="Agent-Verwaltung:",
        choices=[
            "Agents auflisten",
            "Agent erstellen",
            "Agent starten (Chat)",
            "Agent bearbeiten",
            "Agent loeschen",
            "Zurueck",
        ],
    ).execute()

    if action == "Agents auflisten":
        custom = list_agents()
        table = Table(title="Agents")
        table.add_column("Name", style="cyan")
        table.add_column("Beschreibung")
        table.add_column("Tools", style="dim")
        table.add_column("Modell", style="dim")

        # Hotel-Agent immer anzeigen
        table.add_row("hotel_agent", "Standard Hotel-Assistent (fest)", "alle", "(default)")
        for a in custom:
            table.add_row(
                a["name"],
                a.get("description", ""),
                ", ".join(a.get("tools", [])) or "keine",
                a.get("model") or "(default)",
            )
        console.print(table)

    elif action == "Agent erstellen":
        name = inquirer.text(message="Name des Agents:").execute()
        if not name.strip():
            console.print("[red]Name darf nicht leer sein.[/red]")
            return

        description = inquirer.text(message="Beschreibung:").execute()
        system_prompt = inquirer.text(
            message="System-Prompt:",
            default="Du bist ein hilfreicher Assistent.",
        ).execute()

        all_tools = get_all_tool_names()
        tools = inquirer.checkbox(
            message="Tools auswaehlen (Leertaste = an/aus):",
            choices=all_tools,
        ).execute()

        knowledge = inquirer.text(
            message="Wissensdatenbank-Pfad (leer = keine):",
            default="",
        ).execute()

        model = inquirer.text(
            message="LLM-Modell (leer = Standard aus settings.yaml):",
            default="",
        ).execute()

        try:
            cfg = create_agent(
                name=name,
                description=description,
                system_prompt=system_prompt,
                tool_names=tools,
                knowledge_path=knowledge or None,
                model=model or None,
            )
            console.print(f"[green]Agent '{cfg['name']}' erstellt.[/green]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")

    elif action == "Agent starten (Chat)":
        custom = list_agents()
        choices = ["hotel_agent (Standard)"] + [f"{a['name']} — {a.get('description', '')}" for a in custom]
        if len(choices) == 1:
            console.print("[dim]Nur der Standard-Agent vorhanden. Erstelle zuerst einen neuen Agent.[/dim]")
            return

        choice = inquirer.select(message="Agent auswaehlen:", choices=choices).execute()
        agent_name = choice.split(" — ")[0].split(" (")[0].strip()

        from datetime import datetime
        conversation_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            agent = load_agent(agent_name, conversation_id=conversation_id)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            return

        console.print(f"[bold cyan]{agent_name} Chat[/bold cyan] (/exit zum Beenden)")
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
            save_conversation(conversation_id, agent.history)

        console.print("\n[dim]Chat beendet.[/dim]")

    elif action == "Agent bearbeiten":
        custom = list_agents()
        if not custom:
            console.print("[dim]Keine Custom-Agents vorhanden.[/dim]")
            return

        choices = [f"{a['name']} — {a.get('description', '')}" for a in custom] + ["Zurueck"]
        choice = inquirer.select(message="Agent auswaehlen:", choices=choices).execute()
        if choice == "Zurueck":
            return

        agent_name = choice.split(" — ")[0].strip()
        cfg = get_agent_config_by_name(agent_name)
        if not cfg:
            console.print("[red]Agent nicht gefunden.[/red]")
            return

        field = inquirer.select(
            message="Was aendern?",
            choices=["Beschreibung", "System-Prompt", "Tools", "Modell", "Zurueck"],
        ).execute()

        if field == "Beschreibung":
            val = inquirer.text(message="Neue Beschreibung:", default=cfg.get("description", "")).execute()
            update_agent(agent_name, description=val)
        elif field == "System-Prompt":
            val = inquirer.text(message="Neuer System-Prompt:", default=cfg.get("system_prompt", "")).execute()
            update_agent(agent_name, system_prompt=val)
        elif field == "Tools":
            all_tools = get_all_tool_names()
            current = cfg.get("tools", [])
            val = inquirer.checkbox(
                message="Tools auswaehlen:",
                choices=[{"name": t, "value": t, "enabled": t in current} for t in all_tools],
            ).execute()
            update_agent(agent_name, tools=val)
        elif field == "Modell":
            val = inquirer.text(message="Neues Modell (leer = Standard):", default=cfg.get("model") or "").execute()
            update_agent(agent_name, model=val or None)
        else:
            return

        console.print(f"[green]Agent '{agent_name}' aktualisiert.[/green]")

    elif action == "Agent loeschen":
        custom = list_agents()
        if not custom:
            console.print("[dim]Keine Custom-Agents vorhanden.[/dim]")
            return

        choices = [f"{a['name']} — {a.get('description', '')}" for a in custom] + ["Zurueck"]
        choice = inquirer.select(message="Welchen Agent loeschen?", choices=choices).execute()
        if choice == "Zurueck":
            return

        agent_name = choice.split(" — ")[0].strip()
        confirm = inquirer.confirm(message=f"Agent '{agent_name}' wirklich loeschen?", default=False).execute()
        if confirm:
            try:
                delete_agent(agent_name)
                console.print(f"[green]Agent '{agent_name}' geloescht.[/green]")
            except ValueError as e:
                console.print(f"[red]{e}[/red]")


@app.command()
def automations():
    """Automationen verwalten: erstellen, auflisten, ausfuehren, loeschen."""
    from InquirerPy import inquirer
    from scripts.automation_manager import (
        create_automation, list_automations, get_automation,
        enable_automation, disable_automation,
        run_automation, delete_automation, get_run_log,
        AVAILABLE_ACTIONS, TRIGGER_TYPES, AVAILABLE_EVENTS,
    )
    from rich.table import Table

    action = inquirer.select(
        message="Automationen:",
        choices=[
            "Automationen auflisten",
            "Automation erstellen",
            "Automation ausfuehren",
            "Automation aktivieren/deaktivieren",
            "Ausfuehrungs-Log",
            "Automation loeschen",
            "Zurueck",
        ],
    ).execute()

    if action == "Automationen auflisten":
        autos = list_automations()
        if not autos:
            console.print("[dim]Keine Automationen vorhanden.[/dim]")
            return
        table = Table(title="Automationen")
        table.add_column("Name", style="cyan")
        table.add_column("Aktion")
        table.add_column("Trigger")
        table.add_column("Status")
        table.add_column("Letzte Ausfuehrung", style="dim")
        table.add_column("Runs", justify="right")
        for a in autos:
            trigger = a.get("trigger", {})
            t_type = trigger.get("type", "?")
            if t_type == "schedule":
                t_info = f"{', '.join(trigger.get('schedule_days', [])) or 'taeglich'} {trigger.get('schedule_time', '')}"
            elif t_type == "event":
                t_info = f"Event: {trigger.get('event', '?')}"
            else:
                t_info = "manuell"
            status = "[green]aktiv[/green]" if a.get("enabled") else "[dim]inaktiv[/dim]"
            last = (a.get("last_run") or "—")[:16]
            table.add_row(a["name"], a["action"], t_info, status, last, str(a.get("run_count", 0)))
        console.print(table)

    elif action == "Automation erstellen":
        name = inquirer.text(message="Name:").execute()
        if not name.strip():
            console.print("[red]Name darf nicht leer sein.[/red]")
            return

        description = inquirer.text(message="Beschreibung:").execute()

        # Aktion waehlen
        action_choices = [f"{k} — {v['description']}" for k, v in AVAILABLE_ACTIONS.items()]
        action_choice = inquirer.select(message="Aktion:", choices=action_choices).execute()
        action_name = action_choice.split(" — ")[0].strip()

        # Aktions-Parameter abfragen
        action_params = {}
        params_def = AVAILABLE_ACTIONS[action_name].get("params", [])
        for p in params_def:
            val = inquirer.text(
                message=f"{p['description']}:",
                default=str(p.get("default", "")),
            ).execute()
            if val.strip():
                action_params[p["name"]] = val.strip()

        # Trigger-Typ waehlen
        trigger_choices = [f"{k} — {v}" for k, v in TRIGGER_TYPES.items()]
        trigger_choice = inquirer.select(message="Trigger-Typ:", choices=trigger_choices).execute()
        trigger_type = trigger_choice.split(" — ")[0].strip()

        schedule_time = None
        schedule_days = []
        event_name = None

        if trigger_type == "schedule":
            schedule_time = inquirer.text(message="Uhrzeit (HH:MM):", default="08:00").execute()
            all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            schedule_days = inquirer.checkbox(
                message="Wochentage (leer = taeglich):",
                choices=all_days,
            ).execute()

        elif trigger_type == "event":
            event_choices = [f"{k} — {v}" for k, v in AVAILABLE_EVENTS.items()]
            event_choice = inquirer.select(message="Event:", choices=event_choices).execute()
            event_name = event_choice.split(" — ")[0].strip()

        try:
            cfg = create_automation(
                name=name,
                description=description,
                action=action_name,
                trigger_type=trigger_type,
                schedule_time=schedule_time,
                schedule_days=schedule_days,
                event_name=event_name,
                action_params=action_params,
            )
            console.print(f"[green]Automation '{cfg['name']}' erstellt.[/green]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")

    elif action == "Automation ausfuehren":
        autos = list_automations()
        if not autos:
            console.print("[dim]Keine Automationen vorhanden.[/dim]")
            return
        choices = [f"{a['name']} — {a['action']}" for a in autos] + ["Zurueck"]
        choice = inquirer.select(message="Welche ausfuehren?", choices=choices).execute()
        if choice == "Zurueck":
            return
        auto_name = choice.split(" — ")[0].strip()
        console.print(f"[dim]Fuehre '{auto_name}' aus...[/dim]")
        result = run_automation(auto_name)
        console.print(f"[green]Ergebnis: {result}[/green]")

    elif action == "Automation aktivieren/deaktivieren":
        autos = list_automations()
        if not autos:
            console.print("[dim]Keine Automationen vorhanden.[/dim]")
            return
        choices = [
            f"{a['name']} — {'aktiv' if a.get('enabled') else 'inaktiv'}"
            for a in autos
        ] + ["Zurueck"]
        choice = inquirer.select(message="Welche umschalten?", choices=choices).execute()
        if choice == "Zurueck":
            return
        auto_name = choice.split(" — ")[0].strip()
        auto = get_automation(auto_name)
        if auto and auto.get("enabled"):
            disable_automation(auto_name)
            console.print(f"[yellow]'{auto_name}' deaktiviert.[/yellow]")
        else:
            enable_automation(auto_name)
            console.print(f"[green]'{auto_name}' aktiviert.[/green]")

    elif action == "Ausfuehrungs-Log":
        log = get_run_log(limit=20)
        if not log:
            console.print("[dim]Kein Ausfuehrungs-Log vorhanden.[/dim]")
            return
        table = Table(title="Letzte Ausfuehrungen")
        table.add_column("Zeitpunkt", style="dim")
        table.add_column("Automation", style="cyan")
        table.add_column("Status")
        table.add_column("Nachricht")
        for entry in log:
            status_style = "green" if entry.get("status") == "ok" else "red"
            table.add_row(
                entry.get("timestamp", "")[:16],
                entry.get("automation", ""),
                f"[{status_style}]{entry.get('status', '?')}[/{status_style}]",
                entry.get("message", "")[:60],
            )
        console.print(table)

    elif action == "Automation loeschen":
        autos = list_automations()
        if not autos:
            console.print("[dim]Keine Automationen vorhanden.[/dim]")
            return
        choices = [f"{a['name']} — {a['action']}" for a in autos] + ["Zurueck"]
        choice = inquirer.select(message="Welche loeschen?", choices=choices).execute()
        if choice == "Zurueck":
            return
        auto_name = choice.split(" — ")[0].strip()
        confirm = inquirer.confirm(message=f"'{auto_name}' wirklich loeschen?", default=False).execute()
        if confirm:
            delete_automation(auto_name)
            console.print(f"[green]'{auto_name}' geloescht.[/green]")


@app.command()
def scheduler():
    """Scheduler starten — fuehrt zeitgesteuerte Automationen aus."""
    from scripts.scheduler import start
    console.print(Panel("Scheduler", subtitle="Zeitgesteuerte Automationen", style="bold cyan"))
    start(background=False)


if __name__ == "__main__":
    app()
