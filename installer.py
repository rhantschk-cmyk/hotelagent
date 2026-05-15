"""HotelAgent — Installer.

Standalone-Installer der alles einrichtet:
1. Prueft Voraussetzungen (Python, Git)
2. Klont das Repository von GitHub
3. Erstellt Virtual Environment & installiert Abhaengigkeiten
4. Erstellt .env Datei
5. Baut die GUI-EXE mit PyInstaller
6. Erstellt Desktop-Verknuepfung
7. Startet den Erst-Einrichtungs-Assistenten

Nutzung:
    python installer.py          (direkt)
    installer.exe                (kompiliert mit build_installer.py)
"""

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

REPO_URL = "https://github.com/raphael-cmyk/hotelagent.git"
DEFAULT_INSTALL_DIR = Path.home() / ".hotelagent"
APP_NAME = "HotelAgent"
VENV_DIR_NAME = "venv"

DISCLAIMER_TEXT = (
    "HAFTUNGSAUSSCHLUSS\n\n"
    "Dieser Assistent nutzt kuenstliche Intelligenz (KI). "
    "Die generierten Antworten koennen fehlerhaft, unvollstaendig "
    "oder veraltet sein.\n\n"
    "Der Entwickler uebernimmt keinerlei Haftung fuer die "
    "Richtigkeit, Vollstaendigkeit oder Aktualitaet der "
    "KI-generierten Inhalte. Die Nutzung erfolgt ausschliesslich "
    "auf eigene Verantwortung des Anwenders.\n\n"
    "Durch die Installation und Nutzung dieser Software erklaeren "
    "Sie sich mit diesen Bedingungen einverstanden."
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def find_python() -> str | None:
    """Python 3.10+ finden."""
    candidates = ["python", "python3", "py"]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, "--version"], capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                # z.B. "Python 3.12.0"
                parts = version.split()
                if len(parts) >= 2:
                    ver = parts[1].split(".")
                    if int(ver[0]) >= 3 and int(ver[1]) >= 10:
                        return cmd
        except Exception:
            continue
    return None


def find_git() -> str | None:
    """Git finden."""
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return "git"
    except Exception:
        pass
    return None


def run_cmd(cmd: list[str], cwd: str = None, env: dict = None) -> tuple[int, str, str]:
    """Kommando ausfuehren und Ausgabe zurueckgeben."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd,
            env=merged_env, timeout=600,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def get_venv_python(install_dir: Path) -> str:
    """Python-Pfad im venv zurueckgeben."""
    venv_dir = install_dir / VENV_DIR_NAME
    if sys.platform == "win32":
        return str(venv_dir / "Scripts" / "python.exe")
    return str(venv_dir / "bin" / "python")


def get_venv_pip(install_dir: Path) -> str:
    """Pip-Pfad im venv zurueckgeben."""
    venv_dir = install_dir / VENV_DIR_NAME
    if sys.platform == "win32":
        return str(venv_dir / "Scripts" / "pip.exe")
    return str(venv_dir / "bin" / "pip")


# ---------------------------------------------------------------------------
# Installer GUI
# ---------------------------------------------------------------------------

class InstallerApp(tk.Tk):
    """HotelAgent Installer — Grafische Oberflaeche."""

    # Installationsschritte
    STEPS = [
        "Voraussetzungen pruefen",
        "Repository klonen",
        "Virtual Environment erstellen",
        "Abhaengigkeiten installieren",
        ".env Datei erstellen",
        "GUI-EXE erstellen (PyInstaller)",
        "Desktop-Verknuepfung erstellen",
        "Einrichtung starten",
    ]

    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} — Installer")
        self.geometry("680x560")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")

        # State
        self._install_dir = DEFAULT_INSTALL_DIR
        self._python_cmd = None
        self._git_cmd = None
        self._current_step = 0
        self._installing = False
        self._api_key = ""

        self._show_disclaimer()

    # -------------------------------------------------------------------
    # Disclaimer Screen
    # -------------------------------------------------------------------

    def _show_disclaimer(self):
        """Haftungsausschluss anzeigen — muss akzeptiert werden."""
        self._clear()

        header = tk.Frame(self, bg="#16213e", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Haftungsausschluss",
                 font=("Segoe UI", 22, "bold"), fg="#e94560", bg="#16213e").pack(pady=20)

        content = tk.Frame(self, bg="#1a1a2e", padx=40, pady=20)
        content.pack(fill="both", expand=True)

        # Disclaimer-Text in einem scrollbaren Textfeld
        disclaimer_frame = tk.Frame(content, bg="#0f3460", bd=2, relief="flat")
        disclaimer_frame.pack(fill="both", expand=True, pady=(0, 16))

        disclaimer_text = tk.Text(disclaimer_frame, font=("Segoe UI", 11),
                                   bg="#0f3460", fg="#e0e0e0", wrap="word",
                                   relief="flat", bd=12, highlightthickness=0,
                                   height=10)
        disclaimer_text.insert("1.0", DISCLAIMER_TEXT)
        disclaimer_text.configure(state="disabled")
        disclaimer_text.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(disclaimer_frame, command=disclaimer_text.yview)
        scrollbar.pack(side="right", fill="y")
        disclaimer_text.configure(yscrollcommand=scrollbar.set)

        # Buttons (pack bottom first so they are always visible)
        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.pack(side="bottom", fill="x")

        # Checkbox
        self._accept_var = tk.BooleanVar(value=False)
        check_frame = tk.Frame(content, bg="#1a1a2e")
        check_frame.pack(side="bottom", fill="x", pady=(0, 12))

        check = tk.Checkbutton(check_frame, text="Ich habe den Haftungsausschluss gelesen und akzeptiere ihn.",
                                variable=self._accept_var,
                                font=("Segoe UI", 11), fg="white", bg="#1a1a2e",
                                selectcolor="#0f3460", activebackground="#1a1a2e",
                                activeforeground="white",
                                command=self._update_accept_btn)
        check.pack(anchor="w")

        tk.Button(btn_frame, text="Ablehnen", command=self.destroy,
                   font=("Segoe UI", 11), bg="#374151", fg="white",
                   relief="flat", padx=20, pady=8, cursor="hand2").pack(side="left")

        self._accept_btn = tk.Button(btn_frame, text="Akzeptieren  →",
                                      command=self._build_welcome,
                                      font=("Segoe UI", 11, "bold"),
                                      bg="#606060", fg="#909090",
                                      relief="flat", padx=24, pady=8,
                                      state="disabled")
        self._accept_btn.pack(side="right")

    def _update_accept_btn(self):
        """Akzeptieren-Button aktivieren/deaktivieren."""
        if self._accept_var.get():
            self._accept_btn.configure(state="normal", bg="#e94560", fg="white",
                                        cursor="hand2", activebackground="#c73e54")
        else:
            self._accept_btn.configure(state="disabled", bg="#606060", fg="#909090",
                                        cursor="")

    # -------------------------------------------------------------------
    # Welcome Screen
    # -------------------------------------------------------------------

    def _build_welcome(self):
        """Willkommens-Bildschirm aufbauen."""
        self._clear()

        # Header
        header = tk.Frame(self, bg="#16213e", height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text=APP_NAME, font=("Segoe UI", 28, "bold"),
                 fg="#e94560", bg="#16213e").pack(pady=(20, 0))
        tk.Label(header, text="KI-Hotelassistent — Installer",
                 font=("Segoe UI", 12), fg="#a0a0b0", bg="#16213e").pack()

        # Content
        content = tk.Frame(self, bg="#1a1a2e", padx=40, pady=20)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Willkommen!",
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#1a1a2e").pack(anchor="w")

        info_text = (
            "Dieser Installer richtet HotelAgent vollstaendig ein:\n\n"
            "  1.  Repository von GitHub herunterladen\n"
            "  2.  Python-Umgebung einrichten\n"
            "  3.  Alle Abhaengigkeiten installieren\n"
            "  4.  Ausfuehrbare GUI-Datei erstellen\n"
            "  5.  Desktop-Verknuepfung anlegen\n"
            "  6.  Erst-Einrichtung starten (API-Key, E-Mail)"
        )
        tk.Label(content, text=info_text, font=("Segoe UI", 11),
                 fg="#c0c0d0", bg="#1a1a2e", justify="left", anchor="w").pack(fill="x", pady=(10, 16))

        # Installationspfad
        path_frame = tk.Frame(content, bg="#1a1a2e")
        path_frame.pack(fill="x", pady=(0, 8))
        tk.Label(path_frame, text="Installationsordner:", font=("Segoe UI", 10),
                 fg="#a0a0b0", bg="#1a1a2e").pack(anchor="w")

        entry_frame = tk.Frame(path_frame, bg="#1a1a2e")
        entry_frame.pack(fill="x")

        self._path_var = tk.StringVar(value=str(self._install_dir))
        self._path_entry = tk.Entry(entry_frame, textvariable=self._path_var,
                                     font=("Consolas", 11), bg="#0f3460", fg="white",
                                     insertbackground="white", relief="flat", bd=8)
        self._path_entry.pack(side="left", fill="x", expand=True)

        browse_btn = tk.Button(entry_frame, text="...", command=self._browse_dir,
                                font=("Segoe UI", 10), bg="#0f3460", fg="white",
                                relief="flat", padx=12, cursor="hand2")
        browse_btn.pack(side="right", padx=(8, 0))

        # API Key
        tk.Label(content, text="OpenRouter API-Key:", font=("Segoe UI", 10),
                 fg="#a0a0b0", bg="#1a1a2e").pack(anchor="w", pady=(8, 0))
        self._api_entry = tk.Entry(content, font=("Consolas", 11), bg="#0f3460",
                                    fg="white", insertbackground="white", relief="flat",
                                    bd=8, show="*")
        self._api_entry.pack(fill="x")
        tk.Label(content, text="(Von openrouter.ai/keys — kann auch spaeter eingetragen werden)",
                 font=("Segoe UI", 9), fg="#606080", bg="#1a1a2e").pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.pack(fill="x", pady=(20, 0))

        tk.Button(btn_frame, text="Abbrechen", command=self.destroy,
                   font=("Segoe UI", 11), bg="#374151", fg="white",
                   relief="flat", padx=20, pady=8, cursor="hand2").pack(side="left")

        tk.Button(btn_frame, text="Installieren  →", command=self._start_install,
                   font=("Segoe UI", 11, "bold"), bg="#e94560", fg="white",
                   relief="flat", padx=24, pady=8, cursor="hand2",
                   activebackground="#c73e54").pack(side="right")

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Installationsordner waehlen")
        if d:
            self._path_var.set(d)

    # -------------------------------------------------------------------
    # Installation Screen
    # -------------------------------------------------------------------

    def _start_install(self):
        self._install_dir = Path(self._path_var.get().strip())
        self._api_key = self._api_entry.get().strip()
        self._build_progress()
        self._installing = True
        threading.Thread(target=self._run_installation, daemon=True).start()

    def _build_progress(self):
        """Fortschritts-Bildschirm aufbauen."""
        self._clear()

        header = tk.Frame(self, bg="#16213e", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{APP_NAME} wird installiert...",
                 font=("Segoe UI", 18, "bold"), fg="white", bg="#16213e").pack(pady=16)

        content = tk.Frame(self, bg="#1a1a2e", padx=40, pady=20)
        content.pack(fill="both", expand=True)

        # Schritte-Liste
        self._step_labels: list[tk.Label] = []
        self._step_indicators: list[tk.Label] = []
        for i, step in enumerate(self.STEPS):
            row = tk.Frame(content, bg="#1a1a2e")
            row.pack(fill="x", pady=3)

            indicator = tk.Label(row, text="○", font=("Segoe UI", 12),
                                  fg="#404060", bg="#1a1a2e", width=3)
            indicator.pack(side="left")
            self._step_indicators.append(indicator)

            lbl = tk.Label(row, text=step, font=("Segoe UI", 11),
                            fg="#606080", bg="#1a1a2e", anchor="w")
            lbl.pack(side="left", fill="x")
            self._step_labels.append(lbl)

        # Fortschrittsbalken
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Red.Horizontal.TProgressbar",
                         troughcolor="#0f3460", background="#e94560",
                         darkcolor="#e94560", lightcolor="#e94560")

        self._progress = ttk.Progressbar(content, length=560, mode="determinate",
                                          maximum=len(self.STEPS),
                                          style="Red.Horizontal.TProgressbar")
        self._progress.pack(pady=(20, 8))

        # Status-Text
        self._status_var = tk.StringVar(value="Starte Installation...")
        self._status_label = tk.Label(content, textvariable=self._status_var,
                                       font=("Consolas", 10), fg="#808090",
                                       bg="#1a1a2e", anchor="w", wraplength=560)
        self._status_label.pack(fill="x")

        # Log
        self._log_text = tk.Text(content, height=6, font=("Consolas", 9),
                                  bg="#0f3460", fg="#a0a0b0", relief="flat",
                                  bd=8, wrap="word")
        self._log_text.pack(fill="x", pady=(8, 0))

    def _set_step(self, index: int, status: str = "active"):
        """Schritt-Anzeige aktualisieren."""
        def _update():
            if status == "active":
                self._step_indicators[index].configure(text="►", fg="#e94560")
                self._step_labels[index].configure(fg="white")
            elif status == "done":
                self._step_indicators[index].configure(text="✓", fg="#22c55e")
                self._step_labels[index].configure(fg="#22c55e")
            elif status == "error":
                self._step_indicators[index].configure(text="✗", fg="#ef4444")
                self._step_labels[index].configure(fg="#ef4444")
            self._progress["value"] = index + (1 if status == "done" else 0.5)
        self.after(0, _update)

    def _log(self, msg: str):
        def _update():
            self._status_var.set(msg)
            self._log_text.insert("end", msg + "\n")
            self._log_text.see("end")
        self.after(0, _update)

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # -------------------------------------------------------------------
    # Installation Steps
    # -------------------------------------------------------------------

    def _run_installation(self):
        """Alle Installationsschritte ausfuehren."""
        try:
            self._step_check_prerequisites()
            self._step_clone_repo()
            self._step_create_venv()
            self._step_install_deps()
            self._step_create_env()
            self._step_build_exe()
            self._step_create_shortcut()
            self._step_launch_setup()

            self.after(0, self._show_done)

        except InstallerError as e:
            self._log(f"\nFEHLER: {e}")
            self.after(0, lambda: messagebox.showerror(
                "Installation fehlgeschlagen", str(e)))

    def _step_check_prerequisites(self):
        """Schritt 1: Voraussetzungen pruefen."""
        step = 0
        self._set_step(step, "active")
        self._log("Pruefe Voraussetzungen...")

        # Python pruefen
        self._python_cmd = find_python()
        if not self._python_cmd:
            self._set_step(step, "error")
            raise InstallerError(
                "Python 3.10+ nicht gefunden.\n\n"
                "Bitte installiere Python von python.org und stelle sicher,\n"
                "dass 'Add Python to PATH' aktiviert ist."
            )
        self._log(f"  Python gefunden: {self._python_cmd}")

        # Git pruefen
        self._git_cmd = find_git()
        if not self._git_cmd:
            self._set_step(step, "error")
            raise InstallerError(
                "Git nicht gefunden.\n\n"
                "Bitte installiere Git von git-scm.com."
            )
        self._log(f"  Git gefunden: {self._git_cmd}")

        self._set_step(step, "done")

    def _step_clone_repo(self):
        """Schritt 2: Repository klonen."""
        step = 1
        self._set_step(step, "active")

        install_dir = self._install_dir

        if install_dir.is_dir() and any(install_dir.iterdir()):
            # Ordner existiert — git pull statt clone
            if (install_dir / ".git").is_dir():
                self._log(f"Aktualisiere bestehendes Repository in {install_dir}...")
                code, out, err = run_cmd(
                    [self._git_cmd, "pull", "--ff-only"],
                    cwd=str(install_dir),
                )
                if code != 0:
                    self._log(f"  Git pull fehlgeschlagen, fahre trotzdem fort: {err.strip()}")
                else:
                    self._log("  Repository aktualisiert.")
            else:
                self._log(f"Ordner {install_dir} existiert bereits (kein Git-Repo).")
                self._log("  Verwende bestehende Dateien.")
        else:
            self._log(f"Klone Repository nach {install_dir}...")
            install_dir.parent.mkdir(parents=True, exist_ok=True)

            code, out, err = run_cmd(
                [self._git_cmd, "clone", REPO_URL, str(install_dir)],
            )
            if code != 0:
                self._set_step(step, "error")
                raise InstallerError(f"Git clone fehlgeschlagen:\n{err.strip()}")
            self._log("  Repository erfolgreich geklont.")

        self._set_step(step, "done")

    def _step_create_venv(self):
        """Schritt 3: Virtual Environment erstellen."""
        step = 2
        self._set_step(step, "active")

        venv_path = self._install_dir / VENV_DIR_NAME

        if venv_path.is_dir():
            self._log(f"Virtual Environment existiert bereits: {venv_path}")
            # Pruefen ob nutzbar
            vpy = get_venv_python(self._install_dir)
            if Path(vpy).is_file():
                self._log("  Verwende bestehendes venv.")
                self._set_step(step, "done")
                return
            else:
                self._log("  Bestehendes venv defekt — erstelle neu...")
                shutil.rmtree(venv_path, ignore_errors=True)

        self._log("Erstelle Virtual Environment...")
        code, out, err = run_cmd(
            [self._python_cmd, "-m", "venv", str(venv_path)],
        )
        if code != 0:
            self._set_step(step, "error")
            raise InstallerError(f"venv-Erstellung fehlgeschlagen:\n{err.strip()}")

        self._log("  Virtual Environment erstellt.")
        self._set_step(step, "done")

    def _step_install_deps(self):
        """Schritt 4: Abhaengigkeiten installieren."""
        step = 3
        self._set_step(step, "active")
        self._log("Installiere Abhaengigkeiten (das kann einige Minuten dauern)...")

        vpy = get_venv_python(self._install_dir)
        vpip = get_venv_pip(self._install_dir)
        req_file = self._install_dir / "requirements.txt"

        if not req_file.is_file():
            self._set_step(step, "error")
            raise InstallerError("requirements.txt nicht gefunden im Repository.")

        # pip upgraden
        self._log("  Aktualisiere pip...")
        run_cmd([vpy, "-m", "pip", "install", "--upgrade", "pip"],
                cwd=str(self._install_dir))

        # Requirements installieren
        self._log("  Installiere Pakete aus requirements.txt...")
        code, out, err = run_cmd(
            [vpip, "install", "-r", str(req_file)],
            cwd=str(self._install_dir),
        )
        if code != 0:
            self._log(f"  Warnung: Einige Pakete konnten nicht installiert werden.")
            self._log(f"  {err.strip()[-200:]}")
        else:
            self._log("  Alle Abhaengigkeiten installiert.")

        self._set_step(step, "done")

    def _step_create_env(self):
        """Schritt 5: .env Datei erstellen."""
        step = 4
        self._set_step(step, "active")

        env_file = self._install_dir / ".env"

        if env_file.is_file():
            self._log(".env existiert bereits — ueberspringe.")
            if self._api_key:
                # API-Key aktualisieren
                content = env_file.read_text(encoding="utf-8")
                if "OPENROUTER_API_KEY" in content:
                    import re
                    content = re.sub(
                        r"OPENROUTER_API_KEY=.*",
                        f"OPENROUTER_API_KEY={self._api_key}",
                        content,
                    )
                else:
                    content += f"\nOPENROUTER_API_KEY={self._api_key}\n"
                env_file.write_text(content, encoding="utf-8")
                self._log("  API-Key aktualisiert.")
        else:
            self._log("Erstelle .env Datei...")
            lines = [
                "# HotelAgent — Umgebungsvariablen",
                f"OPENROUTER_API_KEY={self._api_key}",
                "",
                "# Optional: E-Mail-Passwort (alternativ in settings.yaml)",
                "# EMAIL_PASSWORD=",
                "",
            ]
            env_file.write_text("\n".join(lines), encoding="utf-8")
            self._log("  .env erstellt.")

        # Daten-Ordner sicherstellen
        for d in ["data/conversations", "data/uploads", "data/logs", "data/automations"]:
            (self._install_dir / d).mkdir(parents=True, exist_ok=True)

        self._set_step(step, "done")

    def _step_build_exe(self):
        """Schritt 6: GUI-EXE mit PyInstaller erstellen."""
        step = 5
        self._set_step(step, "active")
        self._log("Erstelle GUI-EXE mit PyInstaller (das dauert 1-3 Minuten)...")

        vpy = get_venv_python(self._install_dir)

        # gui_launcher.py muss existieren
        launcher = self._install_dir / "gui_launcher.py"
        if not launcher.is_file():
            self._log("  gui_launcher.py nicht gefunden — erstelle...")
            launcher.write_text(
                '"""HotelAgent GUI Launcher."""\n\n'
                'import sys, os\n'
                'if getattr(sys, "frozen", False):\n'
                '    os.chdir(os.path.dirname(sys.executable))\n'
                'else:\n'
                '    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n\n'
                'try:\n'
                '    from dotenv import load_dotenv\n'
                '    load_dotenv()\n'
                'except Exception:\n'
                '    pass\n\n'
                'from gui import launch_gui\n'
                'launch_gui()\n',
                encoding="utf-8",
            )

        # PyInstaller ausfuehren
        code, out, err = run_cmd(
            [vpy, str(self._install_dir / "build_exe.py")],
            cwd=str(self._install_dir),
        )

        exe_path = self._install_dir / "dist" / "HotelAgent" / "HotelAgent.exe"
        if exe_path.is_file():
            self._log(f"  EXE erstellt: {exe_path}")
            self._set_step(step, "done")
        else:
            self._log("  EXE-Build fehlgeschlagen — GUI kann trotzdem per Python gestartet werden.")
            self._log(f"  {err.strip()[-300:]}")
            self._set_step(step, "done")  # Kein fataler Fehler

    def _step_create_shortcut(self):
        """Schritt 7: Desktop-Verknuepfung erstellen."""
        step = 6
        self._set_step(step, "active")
        self._log("Erstelle Desktop-Verknuepfung...")

        desktop = Path.home() / "Desktop"
        if not desktop.is_dir():
            desktop = Path(os.path.expanduser("~/Desktop"))

        exe_path = self._install_dir / "dist" / "HotelAgent" / "HotelAgent.exe"

        if sys.platform == "win32" and exe_path.is_file():
            try:
                # Windows-Verknuepfung (.lnk) erstellen
                shortcut_path = desktop / f"{APP_NAME}.lnk"
                self._create_windows_shortcut(exe_path, shortcut_path)
                self._log(f"  Verknuepfung erstellt: {shortcut_path}")
            except Exception as e:
                self._log(f"  Verknuepfung konnte nicht erstellt werden: {e}")
                # Fallback: .bat Datei
                bat_path = desktop / f"{APP_NAME}.bat"
                vpy = get_venv_python(self._install_dir)
                bat_content = (
                    f'@echo off\n'
                    f'cd /d "{self._install_dir}"\n'
                    f'"{vpy}" gui_launcher.py\n'
                )
                bat_path.write_text(bat_content, encoding="utf-8")
                self._log(f"  Batch-Datei erstellt: {bat_path}")
        else:
            # Fallback: .bat Datei
            bat_path = desktop / f"{APP_NAME}.bat"
            vpy = get_venv_python(self._install_dir)
            bat_content = (
                f'@echo off\n'
                f'cd /d "{self._install_dir}"\n'
                f'"{vpy}" gui_launcher.py\n'
            )
            bat_path.write_text(bat_content, encoding="utf-8")
            self._log(f"  Batch-Datei erstellt: {bat_path}")

        self._set_step(step, "done")

    @staticmethod
    def _create_windows_shortcut(target: Path, shortcut_path: Path):
        """Windows .lnk Verknuepfung erstellen via PowerShell."""
        ps_cmd = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{shortcut_path}"); '
            f'$s.TargetPath = "{target}"; '
            f'$s.WorkingDirectory = "{target.parent}"; '
            f'$s.Description = "{APP_NAME} — KI-Hotelassistent"; '
            f'$s.Save()'
        )
        subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, timeout=15,
        )

    def _step_launch_setup(self):
        """Schritt 8: Erst-Einrichtung starten."""
        step = 7
        self._set_step(step, "active")
        self._log("Starte Erst-Einrichtung...")

        vpy = get_venv_python(self._install_dir)

        # Doctor ausfuehren
        self._log("  Fuehre Doctor-Check aus...")
        code, out, err = run_cmd(
            [vpy, "main.py", "doctor"],
            cwd=str(self._install_dir),
        )
        if out:
            for line in out.strip().split("\n")[-8:]:
                self._log(f"    {line.strip()}")

        self._set_step(step, "done")

    # -------------------------------------------------------------------
    # Done Screen
    # -------------------------------------------------------------------

    def _show_done(self):
        """Abschluss-Bildschirm anzeigen."""
        self._clear()

        header = tk.Frame(self, bg="#16213e", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Installation abgeschlossen!",
                 font=("Segoe UI", 22, "bold"), fg="#22c55e", bg="#16213e").pack(pady=20)

        content = tk.Frame(self, bg="#1a1a2e", padx=40, pady=30)
        content.pack(fill="both", expand=True)

        exe_path = self._install_dir / "dist" / "HotelAgent" / "HotelAgent.exe"
        has_exe = exe_path.is_file()

        info = (
            f"HotelAgent wurde erfolgreich installiert.\n\n"
            f"Installationsordner:\n  {self._install_dir}\n\n"
        )
        if has_exe:
            info += (
                f"GUI starten:\n"
                f"  • Desktop-Verknuepfung 'HotelAgent'\n"
                f"  • Oder: {exe_path}\n\n"
            )
        else:
            vpy = get_venv_python(self._install_dir)
            info += (
                f"GUI starten:\n"
                f"  {vpy} gui_launcher.py\n\n"
            )
        info += (
            "CLI nutzen:\n"
            f"  cd {self._install_dir}\n"
            f"  {VENV_DIR_NAME}\\Scripts\\activate\n"
            f"  python main.py --help"
        )

        tk.Label(content, text=info, font=("Consolas", 10),
                 fg="#c0c0d0", bg="#1a1a2e", justify="left", anchor="w").pack(fill="x")

        btn_frame = tk.Frame(content, bg="#1a1a2e")
        btn_frame.pack(fill="x", pady=(24, 0))

        tk.Button(btn_frame, text="Schliessen", command=self.destroy,
                   font=("Segoe UI", 11), bg="#374151", fg="white",
                   relief="flat", padx=20, pady=8, cursor="hand2").pack(side="left")

        tk.Button(btn_frame, text="HotelAgent starten  →",
                   command=lambda: self._launch_app(exe_path if has_exe else None),
                   font=("Segoe UI", 11, "bold"), bg="#e94560", fg="white",
                   relief="flat", padx=24, pady=8, cursor="hand2",
                   activebackground="#c73e54").pack(side="right")

    def _launch_app(self, exe_path: Path | None):
        """HotelAgent starten und Installer schliessen."""
        if exe_path and exe_path.is_file():
            subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
        else:
            vpy = get_venv_python(self._install_dir)
            subprocess.Popen(
                [vpy, "gui_launcher.py"],
                cwd=str(self._install_dir),
            )
        self.destroy()


class InstallerError(Exception):
    """Fehler waehrend der Installation."""
    pass


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
