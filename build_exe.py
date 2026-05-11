"""HotelAgent — EXE-Builder mit PyInstaller.

Erstellt eine ausfuehrbare Datei die direkt die GUI oeffnet.

Nutzung:
    python build_exe.py

Das Ergebnis liegt in dist/HotelAgent/HotelAgent.exe
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def build():
    """EXE mit PyInstaller erstellen."""
    print("=" * 50)
    print("HotelAgent — EXE Build")
    print("=" * 50)

    # PyInstaller pruefen
    try:
        import PyInstaller
        print(f"PyInstaller Version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller nicht installiert. Installiere mit:")
        print("  pip install pyinstaller")
        sys.exit(1)

    # Daten-Dateien sammeln
    data_files = [
        ("config/settings.yaml", "config"),
        ("config/system_prompt.txt", "config"),
        ("KNOWLEDGE.md", "."),
    ]

    # Optional: PRICES.md
    if (PROJECT_ROOT / "PRICES.md").is_file():
        data_files.append(("PRICES.md", "."))

    # Optional: pricing_rules.md
    if (PROJECT_ROOT / "config" / "pricing_rules.md").is_file():
        data_files.append(("config/pricing_rules.md", "config"))

    # PyInstaller-Kommando zusammenbauen
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "HotelAgent",
        "--windowed",                   # Kein Konsolen-Fenster
        "--noconfirm",                  # Ohne Nachfrage ueberschreiben
        "--clean",                      # Clean Build
    ]

    # Daten hinzufuegen
    for src, dest in data_files:
        src_path = PROJECT_ROOT / src
        if src_path.is_file():
            cmd.extend(["--add-data", f"{src}{';' if sys.platform == 'win32' else ':'}{dest}"])

    # Daten-Ordner
    data_dirs = [
        ("data/conversations", "data/conversations"),
        ("data/uploads", "data/uploads"),
        ("data/logs", "data/logs"),
        ("data/automations", "data/automations"),
    ]
    for src, dest in data_dirs:
        src_path = PROJECT_ROOT / src
        if src_path.is_dir():
            cmd.extend(["--add-data", f"{src}{';' if sys.platform == 'win32' else ':'}{dest}"])

    # Hidden imports (Module die PyInstaller nicht automatisch erkennt)
    hidden_imports = [
        "customtkinter",
        "typer",
        "rich",
        "openai",
        "yaml",
        "dotenv",
        "loguru",
        "scripts.config_manager",
        "scripts.llm",
        "scripts.gmail",
        "scripts.email_provider",
        "scripts.email_processor",
        "scripts.memory",
        "scripts.documents",
        "scripts.voice",
        "scripts.web_scraper",
        "scripts.price_manager",
        "scripts.agent_manager",
        "scripts.automation_manager",
        "scripts.scheduler",
        "agents.base_agent",
        "agents.hotel_agent",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Einstiegspunkt: GUI direkt starten
    # Wir verwenden das spezielle gui_launcher.py
    launcher = PROJECT_ROOT / "gui_launcher.py"
    if not launcher.is_file():
        launcher.write_text(
            '"""HotelAgent — GUI Launcher (Einstiegspunkt fuer EXE)."""\n\n'
            'import sys\n'
            'import os\n\n'
            '# Sicherstellen dass das Projektverzeichnis im Path ist\n'
            'if getattr(sys, "frozen", False):\n'
            '    base_path = sys._MEIPASS\n'
            '    os.chdir(os.path.dirname(sys.executable))\n'
            'else:\n'
            '    base_path = os.path.dirname(os.path.abspath(__file__))\n\n'
            'sys.path.insert(0, base_path)\n\n'
            '# .env laden falls vorhanden\n'
            'try:\n'
            '    from dotenv import load_dotenv\n'
            '    load_dotenv()\n'
            'except Exception:\n'
            '    pass\n\n'
            'from gui import launch_gui\n\n'
            'if __name__ == "__main__":\n'
            '    launch_gui()\n',
            encoding="utf-8",
        )
        print("gui_launcher.py erstellt.")

    cmd.append(str(launcher))

    print(f"\nBuild-Kommando:")
    print(f"  {' '.join(cmd)}\n")
    print("Starte Build...\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        exe_path = PROJECT_ROOT / "dist" / "HotelAgent" / "HotelAgent.exe"
        print("\n" + "=" * 50)
        print("Build erfolgreich!")
        print(f"EXE: {exe_path}")
        print("=" * 50)
    else:
        print("\nBuild fehlgeschlagen!")
        sys.exit(1)


if __name__ == "__main__":
    build()
