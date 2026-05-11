"""HotelAgent — Doctor: Inkrementelle Projektprüfung.

Wächst mit dem Projekt. Jede Phase fügt ihre eigenen Checks hinzu.
"""

import importlib
import subprocess
import sys
from pathlib import Path
from rich.console import Console

console = Console()

PROJECT_ROOT = Path(__file__).parent.parent

OK = "[green]OK[/green]"
FAIL = "[red]FAIL[/red]"


def _check(description: str, condition: bool) -> bool:
    """Einzelnen Check ausführen und Ergebnis ausgeben."""
    status = OK if condition else FAIL
    console.print(f"  [{status}] {description}")
    return condition


def check_phase_1() -> tuple[int, int]:
    """Phase 1: Projektstruktur & Setup."""
    console.print("\n[bold cyan]Phase 1: Projektstruktur & Setup[/bold cyan]")
    passed = 0
    total = 0

    # Ordner prüfen
    dirs = [
        "scripts", "config", "agents", "data",
        "data/conversations", "data/uploads", "data/logs", "data/automations",
    ]
    for d in dirs:
        total += 1
        if _check(f"Ordner {d}/", (PROJECT_ROOT / d).is_dir()):
            passed += 1

    # Root-Dateien prüfen
    files = [
        "main.py", "cli.py", "gui.py",
        "requirements.txt", ".gitignore", "KNOWLEDGE.md",
    ]
    for f in files:
        total += 1
        if _check(f"Datei {f}", (PROJECT_ROOT / f).is_file()):
            passed += 1

    # Config-Dateien prüfen
    config_files = ["config/settings.yaml"]
    for f in config_files:
        total += 1
        if _check(f"Datei {f}", (PROJECT_ROOT / f).is_file()):
            passed += 1

    return passed, total


def check_phase_2() -> tuple[int, int]:
    """Phase 2: CLI-Grundgeruest."""
    console.print("\n[bold cyan]Phase 2: CLI-Grundgeruest[/bold cyan]")
    passed = 0
    total = 0

    # Bibliotheken importierbar?
    for lib in ["typer", "InquirerPy", "rich"]:
        total += 1
        try:
            importlib.import_module(lib)
            if _check(f"{lib} importierbar", True):
                passed += 1
        except ImportError:
            _check(f"{lib} importierbar", False)

    # CLI-Befehle registriert?
    from cli import app, EXPECTED_COMMANDS

    registered = [cmd.name or cmd.callback.__name__.replace("_", "-") for cmd in app.registered_commands]
    for cmd_name in EXPECTED_COMMANDS:
        total += 1
        if _check(f"Befehl '{cmd_name}' registriert", cmd_name in registered):
            passed += 1

    # --help funktioniert?
    total += 1
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py"), "--help"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    if _check("'python main.py --help' funktioniert", result.returncode == 0):
        passed += 1

    return passed, total


def check_phase_3() -> tuple[int, int]:
    """Phase 3: LLM-Integration (OpenRouter)."""
    console.print("\n[bold cyan]Phase 3: LLM-Integration (OpenRouter)[/bold cyan]")
    passed = 0
    total = 0

    # openai importierbar?
    total += 1
    try:
        importlib.import_module("openai")
        if _check("openai importierbar", True):
            passed += 1
    except ImportError:
        _check("openai importierbar", False)

    # Module existieren?
    for module_path in ["scripts/llm.py", "scripts/config_manager.py"]:
        total += 1
        if _check(f"Datei {module_path}", (PROJECT_ROOT / module_path).is_file()):
            passed += 1

    # Config hat LLM-Sektion?
    total += 1
    try:
        from scripts.config_manager import get_llm_config
        llm_cfg = get_llm_config()
        if _check("settings.yaml hat LLM-Sektion", bool(llm_cfg)):
            passed += 1
    except Exception:
        _check("settings.yaml hat LLM-Sektion", False)

    # LLM-Config hat benoetigte Felder?
    for field in ["model", "temperature", "max_tokens"]:
        total += 1
        if _check(f"LLM-Config: '{field}' vorhanden", field in llm_cfg):
            passed += 1

    # API-Key gesetzt?
    import os
    total += 1
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        if _check("OPENROUTER_API_KEY gesetzt", True):
            passed += 1
    else:
        _check("OPENROUTER_API_KEY gesetzt (in .env eintragen!)", False)

    # LLM-Client instanziierbar? (nur wenn Key vorhanden)
    total += 1
    if api_key:
        try:
            from scripts.llm import get_client
            get_client()
            if _check("LLM-Client instanziierbar", True):
                passed += 1
        except Exception as e:
            _check(f"LLM-Client instanziierbar ({e})", False)
    else:
        _check("LLM-Client instanziierbar (uebersprungen, kein API-Key)", False)

    return passed, total


def check_phase_4() -> tuple[int, int]:
    """Phase 4: Chat-Funktion & Memory."""
    console.print("\n[bold cyan]Phase 4: Chat-Funktion & Memory[/bold cyan]")
    passed = 0
    total = 0

    # Module existieren?
    for module_path in ["agents/hotel_agent.py", "scripts/memory.py"]:
        total += 1
        if _check(f"Datei {module_path}", (PROJECT_ROOT / module_path).is_file()):
            passed += 1

    # Agent instanziierbar?
    import os
    total += 1
    if os.getenv("OPENROUTER_API_KEY"):
        try:
            from agents.hotel_agent import HotelAgent
            agent = HotelAgent()
            if _check("HotelAgent instanziierbar", True):
                passed += 1
        except Exception as e:
            _check(f"HotelAgent instanziierbar ({e})", False)
    else:
        _check("HotelAgent instanziierbar (uebersprungen, kein API-Key)", False)

    # Memory speichern/laden?
    total += 1
    try:
        from scripts.memory import save_conversation, load_conversation, delete_conversation
        test_id = "__doctor_test__"
        test_history = [
            {"role": "system", "content": "test"},
            {"role": "user", "content": "hallo"},
            {"role": "assistant", "content": "hi"},
        ]
        save_conversation(test_id, test_history)
        loaded = load_conversation(test_id)
        delete_conversation(test_id)
        if _check("Memory speichern/laden/loeschen", loaded is not None and len(loaded) == 2):
            passed += 1
    except Exception as e:
        _check(f"Memory speichern/laden/loeschen ({e})", False)

    # Conversations-Ordner existiert?
    total += 1
    if _check("Ordner data/conversations/", (PROJECT_ROOT / "data" / "conversations").is_dir()):
        passed += 1

    return passed, total


def check_phase_5() -> tuple[int, int]:
    """Phase 5: Voice-I/O."""
    console.print("\n[bold cyan]Phase 5: Voice-I/O[/bold cyan]")
    passed = 0
    total = 0

    # Modul existiert?
    total += 1
    if _check("Datei scripts/voice.py", (PROJECT_ROOT / "scripts" / "voice.py").is_file()):
        passed += 1

    # Audio-Bibliotheken importierbar?
    for lib in ["sounddevice", "soundfile", "pyttsx3", "numpy"]:
        total += 1
        try:
            importlib.import_module(lib)
            if _check(f"{lib} importierbar", True):
                passed += 1
        except ImportError:
            _check(f"{lib} importierbar", False)

    # Mikrofon erkannt?
    total += 1
    try:
        from scripts.voice import get_microphone_info
        mic = get_microphone_info()
        if mic:
            if _check(f"Mikrofon erkannt: {mic['name']}", True):
                passed += 1
        else:
            _check("Mikrofon erkannt (keins gefunden)", False)
    except Exception:
        _check("Mikrofon erkannt (Fehler)", False)

    # TTS-Engine funktioniert?
    total += 1
    try:
        from scripts.voice import test_tts
        if _check("TTS-Engine (pyttsx3) funktioniert", test_tts()):
            passed += 1
    except Exception:
        _check("TTS-Engine (pyttsx3) funktioniert", False)

    return passed, total


def check_phase_6() -> tuple[int, int]:
    """Phase 6: Gmail-Integration."""
    console.print("\n[bold cyan]Phase 6: Gmail-Integration[/bold cyan]")
    passed = 0
    total = 0

    # Modul existiert?
    total += 1
    if _check("Datei scripts/gmail.py", (PROJECT_ROOT / "scripts" / "gmail.py").is_file()):
        passed += 1

    # Google-Bibliotheken importierbar?
    for lib in ["googleapiclient", "google_auth_oauthlib"]:
        total += 1
        try:
            importlib.import_module(lib)
            if _check(f"{lib} importierbar", True):
                passed += 1
        except ImportError:
            _check(f"{lib} importierbar", False)

    # Agent hat Gmail-Tool?
    total += 1
    try:
        from agents.hotel_agent import TOOLS
        tool_names = [t["function"]["name"] for t in TOOLS]
        if _check("Agent-Tool 'create_gmail_draft' registriert", "create_gmail_draft" in tool_names):
            passed += 1
    except Exception:
        _check("Agent-Tool 'create_gmail_draft' registriert", False)

    # credentials.json vorhanden? (Warnung, kein Fehler)
    total += 1
    try:
        from scripts.gmail import has_credentials
        if has_credentials():
            if _check("config/credentials.json vorhanden", True):
                passed += 1
        else:
            console.print("  [yellow]WARN[/yellow] config/credentials.json fehlt (Gmail nicht nutzbar)")
            passed += 1  # Warnung, kein Fehler
    except Exception:
        _check("config/credentials.json vorhanden", False)

    return passed, total


def check_phase_7() -> tuple[int, int]:
    """Phase 7: Dokument-Upload & Wissensextraktion."""
    console.print("\n[bold cyan]Phase 7: Dokument-Upload & Wissensextraktion[/bold cyan]")
    passed = 0
    total = 0

    # Modul existiert?
    total += 1
    if _check("Datei scripts/documents.py", (PROJECT_ROOT / "scripts" / "documents.py").is_file()):
        passed += 1

    # Dokument-Bibliotheken importierbar?
    for lib in ["PyPDF2", "docx"]:
        total += 1
        try:
            importlib.import_module(lib)
            if _check(f"{lib} importierbar", True):
                passed += 1
        except ImportError:
            _check(f"{lib} importierbar", False)

    # KNOWLEDGE.md existiert?
    total += 1
    if _check("Datei KNOWLEDGE.md", (PROJECT_ROOT / "KNOWLEDGE.md").is_file()):
        passed += 1

    # data/uploads/ existiert?
    total += 1
    if _check("Ordner data/uploads/", (PROJECT_ROOT / "data" / "uploads").is_dir()):
        passed += 1

    # Agent hat search_knowledge-Tool?
    total += 1
    try:
        from agents.hotel_agent import TOOLS
        tool_names = [t["function"]["name"] for t in TOOLS]
        if _check("Agent-Tool 'search_knowledge' registriert", "search_knowledge" in tool_names):
            passed += 1
    except Exception:
        _check("Agent-Tool 'search_knowledge' registriert", False)

    # Text-Extraktion funktioniert? (TXT-Test)
    total += 1
    try:
        from scripts.documents import extract_text
        test_file = PROJECT_ROOT / "KNOWLEDGE.md"
        text = extract_text(test_file)
        if _check("Text-Extraktion funktioniert (TXT)", len(text) > 0):
            passed += 1
    except Exception as e:
        _check(f"Text-Extraktion funktioniert ({e})", False)

    # --- Preis-System ---

    # PRICES.md existiert?
    total += 1
    if _check("Datei PRICES.md", (PROJECT_ROOT / "PRICES.md").is_file()):
        passed += 1

    # price_manager.py existiert?
    total += 1
    if _check("Datei scripts/price_manager.py", (PROJECT_ROOT / "scripts" / "price_manager.py").is_file()):
        passed += 1

    # price_manager importierbar?
    total += 1
    try:
        from scripts.price_manager import extract_prices_from_text, save_to_prices, calculate_price, load_prices
        if _check("price_manager importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"price_manager importierbar ({e})", False)

    # Agent-Tool 'calculate_price' registriert?
    total += 1
    try:
        from agents.hotel_agent import TOOLS
        tool_names = [t["function"]["name"] for t in TOOLS]
        if _check("Agent-Tool 'calculate_price' registriert", "calculate_price" in tool_names):
            passed += 1
    except Exception:
        _check("Agent-Tool 'calculate_price' registriert", False)

    return passed, total


def check_phase_8() -> tuple[int, int]:
    """Phase 8: GUI (CustomTkinter)."""
    console.print("\n[bold cyan]Phase 8: GUI (CustomTkinter)[/bold cyan]")
    passed = 0
    total = 0

    # customtkinter importierbar?
    total += 1
    try:
        importlib.import_module("customtkinter")
        if _check("customtkinter importierbar", True):
            passed += 1
    except ImportError:
        _check("customtkinter importierbar", False)

    # gui.py ist nicht nur Stub?
    total += 1
    gui_path = PROJECT_ROOT / "gui.py"
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("gui.py implementiert (nicht Stub)", "HotelAgentGUI" in content):
            passed += 1
    else:
        _check("gui.py existiert", False)

    # GUI-Klasse importierbar?
    total += 1
    try:
        from gui import HotelAgentGUI
        if _check("HotelAgentGUI importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"HotelAgentGUI importierbar ({e})", False)

    # launch_gui Funktion vorhanden?
    total += 1
    try:
        from gui import launch_gui
        if _check("launch_gui() vorhanden", callable(launch_gui)):
            passed += 1
    except Exception:
        _check("launch_gui() vorhanden", False)

    # UI-Elemente in der Klasse vorhanden (Quellcode-Check)?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        elements = ["chat_frame", "msg_entry", "send_btn", "voice_btn", "upload_btn",
                     "gmail_btn", "settings_btn", "theme_switch"]
        missing = [e for e in elements if e not in content]
        if _check(f"Alle UI-Elemente vorhanden ({len(elements) - len(missing)}/{len(elements)})", len(missing) == 0):
            passed += 1
        if missing:
            console.print(f"    [dim]Fehlend: {', '.join(missing)}[/dim]")
    else:
        _check("UI-Elemente (gui.py fehlt)", False)

    # CLI gui-Befehl startet GUI (nicht Stub)?
    total += 1
    try:
        cli_path = PROJECT_ROOT / "cli.py"
        cli_content = cli_path.read_text(encoding="utf-8")
        if _check("CLI 'gui' startet GUI (kein Stub)", "launch_gui" in cli_content):
            passed += 1
    except Exception:
        _check("CLI 'gui' startet GUI", False)

    # SettingsDialog vorhanden?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("SettingsDialog implementiert", "class SettingsDialog" in content):
            passed += 1
    else:
        _check("SettingsDialog implementiert", False)

    # GmailDraftDialog vorhanden?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GmailDraftDialog implementiert", "class GmailDraftDialog" in content):
            passed += 1
    else:
        _check("GmailDraftDialog implementiert", False)

    return passed, total


def check_phase_9() -> tuple[int, int]:
    """Phase 9: Automatische E-Mail-Beantwortung (check-mails)."""
    console.print("\n[bold cyan]Phase 9: Automatische E-Mail-Beantwortung[/bold cyan]")
    passed = 0
    total = 0

    # email_processor.py existiert?
    total += 1
    if _check("Datei scripts/email_processor.py", (PROJECT_ROOT / "scripts" / "email_processor.py").is_file()):
        passed += 1

    # Gmail Scopes erweitert (readonly)?
    total += 1
    try:
        from scripts.gmail import SCOPES
        has_readonly = any("readonly" in s for s in SCOPES)
        if _check("Gmail-Scope 'gmail.readonly' vorhanden", has_readonly):
            passed += 1
    except Exception:
        _check("Gmail-Scope 'gmail.readonly' vorhanden", False)

    # email_processor importierbar?
    total += 1
    try:
        from scripts.email_processor import process_inbox
        if _check("email_processor importierbar", callable(process_inbox)):
            passed += 1
    except Exception as e:
        _check(f"email_processor importierbar ({e})", False)

    # CLI-Befehl check-mails registriert?
    total += 1
    from cli import app, EXPECTED_COMMANDS
    registered = [cmd.name or cmd.callback.__name__.replace("_", "-") for cmd in app.registered_commands]
    if _check("Befehl 'check-mails' registriert", "check-mails" in registered):
        passed += 1

    # Agent-Tool check_mails registriert?
    total += 1
    try:
        from agents.hotel_agent import TOOLS
        tool_names = [t["function"]["name"] for t in TOOLS]
        if _check("Agent-Tool 'check_mails' registriert", "check_mails" in tool_names):
            passed += 1
    except Exception:
        _check("Agent-Tool 'check_mails' registriert", False)

    # settings.yaml hat email_processing-Sektion?
    total += 1
    try:
        from scripts.config_manager import load_config
        cfg = load_config()
        ep = cfg.get("email_processing", {})
        if _check("settings.yaml hat email_processing-Sektion", bool(ep)):
            passed += 1
    except Exception:
        _check("settings.yaml hat email_processing-Sektion", False)

    # GUI hat check-mails Button?
    total += 1
    gui_path = PROJECT_ROOT / "gui.py"
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: 'E-Mails pruefen'-Button vorhanden", "check_mails_btn" in content):
            passed += 1
    else:
        _check("GUI: 'E-Mails pruefen'-Button", False)

    return passed, total


def check_phase_10() -> tuple[int, int]:
    """Phase 10: Agent-Erstellung."""
    console.print("\n[bold cyan]Phase 10: Agent-Erstellung[/bold cyan]")
    passed = 0
    total = 0

    # base_agent.py existiert?
    total += 1
    if _check("Datei agents/base_agent.py", (PROJECT_ROOT / "agents" / "base_agent.py").is_file()):
        passed += 1

    # agent_manager.py existiert?
    total += 1
    if _check("Datei scripts/agent_manager.py", (PROJECT_ROOT / "scripts" / "agent_manager.py").is_file()):
        passed += 1

    # BaseAgent importierbar?
    total += 1
    try:
        from agents.base_agent import BaseAgent, ALL_TOOLS
        if _check("BaseAgent importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"BaseAgent importierbar ({e})", False)

    # agent_manager importierbar?
    total += 1
    try:
        from scripts.agent_manager import create_agent, list_agents, load_agent, delete_agent
        if _check("agent_manager importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"agent_manager importierbar ({e})", False)

    # CLI-Befehl 'agents' registriert?
    total += 1
    from cli import app, EXPECTED_COMMANDS
    registered = [cmd.name or cmd.callback.__name__.replace("_", "-") for cmd in app.registered_commands]
    if _check("Befehl 'agents' registriert", "agents" in registered):
        passed += 1

    # Agent CRUD funktioniert?
    total += 1
    try:
        from scripts.agent_manager import create_agent, get_agent_config_by_name, delete_agent
        test_name = "__doctor_test_agent__"
        # Aufraeumen falls vorhanden
        try:
            delete_agent(test_name)
        except Exception:
            pass

        cfg = create_agent(
            name=test_name,
            description="Test-Agent fuer Doctor",
            system_prompt="Test",
            tool_names=["search_knowledge"],
        )
        loaded = get_agent_config_by_name(test_name)
        delete_agent(test_name)

        if _check("Agent erstellen/laden/loeschen", loaded is not None and loaded["name"] == test_name):
            passed += 1
    except Exception as e:
        _check(f"Agent erstellen/laden/loeschen ({e})", False)

    # HotelAgent erbt von BaseAgent?
    total += 1
    try:
        from agents.hotel_agent import HotelAgent
        from agents.base_agent import BaseAgent
        if _check("HotelAgent erbt von BaseAgent", issubclass(HotelAgent, BaseAgent)):
            passed += 1
    except Exception as e:
        _check(f"HotelAgent erbt von BaseAgent ({e})", False)

    # GUI hat NewAgentDialog?
    total += 1
    gui_path = PROJECT_ROOT / "gui.py"
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: NewAgentDialog implementiert", "class NewAgentDialog" in content):
            passed += 1
    else:
        _check("GUI: NewAgentDialog implementiert", False)

    # GUI hat Agent-Selector?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: Agent-Selector vorhanden", "agent_selector" in content):
            passed += 1
    else:
        _check("GUI: Agent-Selector vorhanden", False)

    return passed, total


def check_phase_11() -> tuple[int, int]:
    """Phase 11: Automationen."""
    console.print("\n[bold cyan]Phase 11: Automationen[/bold cyan]")
    passed = 0
    total = 0

    # data/automations/ existiert?
    total += 1
    if _check("Ordner data/automations/", (PROJECT_ROOT / "data" / "automations").is_dir()):
        passed += 1

    # automation_manager.py existiert?
    total += 1
    if _check("Datei scripts/automation_manager.py", (PROJECT_ROOT / "scripts" / "automation_manager.py").is_file()):
        passed += 1

    # scheduler.py existiert?
    total += 1
    if _check("Datei scripts/scheduler.py", (PROJECT_ROOT / "scripts" / "scheduler.py").is_file()):
        passed += 1

    # automation_manager importierbar?
    total += 1
    try:
        from scripts.automation_manager import (
            create_automation, list_automations, run_automation,
            enable_automation, disable_automation, delete_automation,
            AVAILABLE_ACTIONS, TRIGGER_TYPES,
        )
        if _check("automation_manager importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"automation_manager importierbar ({e})", False)

    # scheduler importierbar?
    total += 1
    try:
        from scripts.scheduler import start, stop, load_scheduled_jobs
        if _check("scheduler importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"scheduler importierbar ({e})", False)

    # schedule Bibliothek importierbar?
    total += 1
    try:
        importlib.import_module("schedule")
        if _check("schedule importierbar", True):
            passed += 1
    except ImportError:
        _check("schedule importierbar", False)

    # CLI-Befehle registriert?
    from cli import app
    registered = [cmd.name or cmd.callback.__name__.replace("_", "-") for cmd in app.registered_commands]
    for cmd_name in ["automations", "scheduler"]:
        total += 1
        if _check(f"Befehl '{cmd_name}' registriert", cmd_name in registered):
            passed += 1

    # Automation CRUD funktioniert?
    total += 1
    try:
        from scripts.automation_manager import create_automation, get_automation, delete_automation
        test_name = "__doctor_test_auto__"
        try:
            delete_automation(test_name)
        except Exception:
            pass

        cfg = create_automation(
            name=test_name,
            description="Test-Automation fuer Doctor",
            action="backup_knowledge",
            trigger_type="manual",
        )
        loaded = get_automation(test_name)
        delete_automation(test_name)

        if _check("Automation erstellen/laden/loeschen", loaded is not None and loaded["name"] == test_name):
            passed += 1
    except Exception as e:
        _check(f"Automation erstellen/laden/loeschen ({e})", False)

    # Verfuegbare Aktionen vorhanden?
    total += 1
    try:
        from scripts.automation_manager import AVAILABLE_ACTIONS
        expected = ["check_mails", "crawl_website", "send_report", "backup_knowledge", "run_agent_task"]
        missing = [a for a in expected if a not in AVAILABLE_ACTIONS]
        if _check(f"Alle Aktionen registriert ({len(expected) - len(missing)}/{len(expected)})", len(missing) == 0):
            passed += 1
        if missing:
            console.print(f"    [dim]Fehlend: {', '.join(missing)}[/dim]")
    except Exception:
        _check("Alle Aktionen registriert", False)

    # GUI hat AutomationsDialog?
    total += 1
    gui_path = PROJECT_ROOT / "gui.py"
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: AutomationsDialog implementiert", "class AutomationsDialog" in content):
            passed += 1
    else:
        _check("GUI: AutomationsDialog implementiert", False)

    # GUI hat Automationen-Button?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: Automationen-Button vorhanden", "automations_btn" in content):
            passed += 1
    else:
        _check("GUI: Automationen-Button vorhanden", False)

    return passed, total


def check_phase_12() -> tuple[int, int]:
    """Phase 12: Multi-Provider E-Mail & EXE-Build."""
    console.print("\n[bold cyan]Phase 12: Multi-Provider E-Mail & EXE-Build[/bold cyan]")
    passed = 0
    total = 0

    # email_provider.py existiert?
    total += 1
    if _check("Datei scripts/email_provider.py", (PROJECT_ROOT / "scripts" / "email_provider.py").is_file()):
        passed += 1

    # email_provider importierbar?
    total += 1
    try:
        from scripts.email_provider import (
            EmailProvider, GmailOAuthProvider, ImapSmtpProvider,
            get_provider, KNOWN_PROVIDERS,
        )
        if _check("email_provider importierbar", True):
            passed += 1
    except Exception as e:
        _check(f"email_provider importierbar ({e})", False)

    # KNOWN_PROVIDERS hat genug Eintraege?
    total += 1
    try:
        from scripts.email_provider import KNOWN_PROVIDERS
        count = len(KNOWN_PROVIDERS)
        if _check(f"Provider-Presets vorhanden ({count} Provider)", count >= 10):
            passed += 1
    except Exception:
        _check("Provider-Presets vorhanden", False)

    # GmailOAuthProvider ist EmailProvider?
    total += 1
    try:
        from scripts.email_provider import GmailOAuthProvider, EmailProvider
        if _check("GmailOAuthProvider erbt von EmailProvider", issubclass(GmailOAuthProvider, EmailProvider)):
            passed += 1
    except Exception:
        _check("GmailOAuthProvider erbt von EmailProvider", False)

    # ImapSmtpProvider ist EmailProvider?
    total += 1
    try:
        from scripts.email_provider import ImapSmtpProvider, EmailProvider
        if _check("ImapSmtpProvider erbt von EmailProvider", issubclass(ImapSmtpProvider, EmailProvider)):
            passed += 1
    except Exception:
        _check("ImapSmtpProvider erbt von EmailProvider", False)

    # get_provider() funktioniert?
    total += 1
    try:
        from scripts.email_provider import get_provider, EmailProvider
        provider = get_provider()
        if _check("get_provider() liefert EmailProvider", isinstance(provider, EmailProvider)):
            passed += 1
    except Exception as e:
        _check(f"get_provider() funktioniert ({e})", False)

    # settings.yaml hat email-Sektion?
    total += 1
    try:
        from scripts.config_manager import load_config
        cfg = load_config()
        email_cfg = cfg.get("email", {})
        if _check("settings.yaml hat email-Sektion", bool(email_cfg) and "provider" in email_cfg):
            passed += 1
    except Exception:
        _check("settings.yaml hat email-Sektion", False)

    # CLI-Befehl email-setup registriert?
    total += 1
    from cli import app, EXPECTED_COMMANDS
    registered = [cmd.name or cmd.callback.__name__.replace("_", "-") for cmd in app.registered_commands]
    if _check("Befehl 'email-setup' registriert", "email-setup" in registered):
        passed += 1

    # email_processor nutzt Provider?
    total += 1
    ep_path = PROJECT_ROOT / "scripts" / "email_processor.py"
    if ep_path.is_file():
        content = ep_path.read_text(encoding="utf-8")
        if _check("email_processor nutzt email_provider", "get_provider" in content):
            passed += 1
    else:
        _check("email_processor nutzt email_provider", False)

    # GUI hat EmailSetupDialog?
    total += 1
    gui_path = PROJECT_ROOT / "gui.py"
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: EmailSetupDialog implementiert", "class EmailSetupDialog" in content):
            passed += 1
    else:
        _check("GUI: EmailSetupDialog implementiert", False)

    # GUI hat email_setup_btn?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: E-Mail-Setup-Button vorhanden", "email_setup_btn" in content):
            passed += 1
    else:
        _check("GUI: E-Mail-Setup-Button vorhanden", False)

    # --- EXE-Build ---

    # build_exe.py existiert?
    total += 1
    if _check("Datei build_exe.py", (PROJECT_ROOT / "build_exe.py").is_file()):
        passed += 1

    # gui_launcher.py existiert?
    total += 1
    if _check("Datei gui_launcher.py", (PROJECT_ROOT / "gui_launcher.py").is_file()):
        passed += 1

    # PyInstaller importierbar?
    total += 1
    try:
        importlib.import_module("PyInstaller")
        if _check("PyInstaller importierbar", True):
            passed += 1
    except ImportError:
        _check("PyInstaller importierbar (pip install pyinstaller)", False)

    return passed, total


def check_phase_13() -> tuple[int, int]:
    """Phase 13: Installer & Setup Wizard."""
    console.print("\n[bold cyan]Phase 13: Installer & Setup Wizard[/bold cyan]")
    passed = 0
    total = 0

    # installer.py existiert?
    total += 1
    if _check("Datei installer.py", (PROJECT_ROOT / "installer.py").is_file()):
        passed += 1

    # build_installer.py existiert?
    total += 1
    if _check("Datei build_installer.py", (PROJECT_ROOT / "build_installer.py").is_file()):
        passed += 1

    # gui_launcher.py existiert?
    total += 1
    if _check("Datei gui_launcher.py", (PROJECT_ROOT / "gui_launcher.py").is_file()):
        passed += 1

    # SetupWizardDialog in GUI?
    total += 1
    gui_path = PROJECT_ROOT / "gui.py"
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: SetupWizardDialog implementiert", "class SetupWizardDialog" in content):
            passed += 1
    else:
        _check("GUI: SetupWizardDialog implementiert", False)

    # is_first_run in GUI?
    total += 1
    if gui_path.is_file():
        content = gui_path.read_text(encoding="utf-8")
        if _check("GUI: Erst-Einrichtungs-Pruefung vorhanden", "is_first_run" in content):
            passed += 1
    else:
        _check("GUI: Erst-Einrichtungs-Pruefung vorhanden", False)

    # Installer importierbar (grundlegende Syntax)?
    total += 1
    try:
        # Nur pruefen ob die Datei parsbar ist
        installer_path = PROJECT_ROOT / "installer.py"
        if installer_path.is_file():
            compile(installer_path.read_text(encoding="utf-8"), str(installer_path), "exec")
            if _check("installer.py ist syntaktisch korrekt", True):
                passed += 1
        else:
            _check("installer.py ist syntaktisch korrekt", False)
    except SyntaxError as e:
        _check(f"installer.py Syntax-Fehler: {e}", False)

    # Installer hat alle Schritte?
    total += 1
    if installer_path.is_file():
        content = installer_path.read_text(encoding="utf-8")
        steps = ["_step_clone_repo", "_step_create_venv", "_step_install_deps",
                 "_step_build_exe", "_step_create_shortcut", "_step_launch_setup"]
        missing = [s for s in steps if s not in content]
        if _check(f"Installer: Alle Schritte vorhanden ({len(steps) - len(missing)}/{len(steps)})",
                  len(missing) == 0):
            passed += 1
        if missing:
            console.print(f"    [dim]Fehlend: {', '.join(missing)}[/dim]")
    else:
        _check("Installer: Alle Schritte vorhanden", False)

    return passed, total


# Alle Phasen in Reihenfolge — wird mit jeder Phase erweitert
ALL_PHASES = [
    check_phase_1,
    check_phase_2,
    check_phase_3,
    check_phase_4,
    check_phase_5,
    check_phase_6,
    check_phase_7,
    check_phase_8,
    check_phase_9,
    check_phase_10,
    check_phase_11,
    check_phase_12,
    check_phase_13,
]


def run_all() -> bool:
    """Alle registrierten Phasen-Checks ausführen."""
    console.print("[bold]HotelAgent Doctor[/bold]")
    console.print("=" * 40)

    total_passed = 0
    total_checks = 0

    for phase_fn in ALL_PHASES:
        passed, total = phase_fn()
        total_passed += passed
        total_checks += total

    # Zusammenfassung
    console.print("\n" + "=" * 40)
    if total_passed == total_checks:
        console.print(
            f"[bold green]Alles OK: {total_passed}/{total_checks} Checks bestanden[/bold green]"
        )
    else:
        failed = total_checks - total_passed
        console.print(
            f"[bold yellow]{total_passed}/{total_checks} bestanden, "
            f"{failed} fehlgeschlagen[/bold yellow]"
        )

    return total_passed == total_checks
