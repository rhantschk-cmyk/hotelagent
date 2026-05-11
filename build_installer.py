"""HotelAgent — Installer-EXE Builder.

Kompiliert installer.py in eine standalone installer.exe.
Die EXE benoetigt nur Python + Git auf dem Zielsystem.

Nutzung:
    python build_installer.py

Das Ergebnis liegt in dist/HotelAgent_Installer.exe
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def build():
    print("=" * 50)
    print("HotelAgent — Installer-EXE Build")
    print("=" * 50)

    try:
        import PyInstaller
        print(f"PyInstaller Version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller nicht installiert:")
        print("  pip install pyinstaller")
        sys.exit(1)

    installer_script = PROJECT_ROOT / "installer.py"
    if not installer_script.is_file():
        print("installer.py nicht gefunden!")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "HotelAgent_Installer",
        "--onefile",                    # Eine einzige EXE
        "--windowed",                   # Kein Konsolen-Fenster
        "--noconfirm",
        "--clean",
        str(installer_script),
    ]

    print(f"\nBuild-Kommando:")
    print(f"  {' '.join(cmd)}\n")
    print("Starte Build...\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode == 0:
        exe_path = PROJECT_ROOT / "dist" / "HotelAgent_Installer.exe"
        print("\n" + "=" * 50)
        print("Build erfolgreich!")
        print(f"Installer-EXE: {exe_path}")
        print()
        print("Die EXE kann verteilt werden. Voraussetzungen")
        print("auf dem Zielsystem:")
        print("  - Python 3.10+  (python.org)")
        print("  - Git           (git-scm.com)")
        print("=" * 50)
    else:
        print("\nBuild fehlgeschlagen!")
        sys.exit(1)


if __name__ == "__main__":
    build()
