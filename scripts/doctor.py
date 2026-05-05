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
        "data/conversations", "data/uploads", "data/logs",
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
