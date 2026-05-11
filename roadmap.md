# HotelAgent — Roadmap

Dieses Dokument definiert die Bauphasen des Projekts. Jede Phase baut auf der vorherigen auf.
Der CLI-Befehl `doctor` wächst mit dem Projekt — nach jeder Phase werden die Checks dafür ergänzt.

---

## Phase 1: Projektstruktur & Setup

**Ziel:** Grundgerüst des Projekts anlegen + Doctor-Grundgerüst.

- [x] Ordnerstruktur erstellen: `scripts/`, `config/`, `agents/`, `data/`
- [x] `main.py` — Einstiegspunkt
- [x] `cli.py` — CLI-Modul mit Stubs
- [x] `gui.py` — GUI-Modul (Stub)
- [x] `requirements.txt` mit allen Abhängigkeiten
- [x] `.gitignore`
- [x] `config/settings.yaml` — zentrale Konfigurationsdatei
- [x] `.env.example` — Template für Umgebungsvariablen
- [x] Virtual Environment anlegen & Abhängigkeiten installieren
- [x] `scripts/doctor.py` — Doctor-Grundgerüst mit Phase-1-Checks

**Doctor prüft (ab jetzt):**
- Ordner `scripts/`, `config/`, `agents/`, `data/`, `data/conversations/`, `data/uploads/`, `data/logs/` existieren
- Root-Dateien `main.py`, `cli.py`, `gui.py`, `requirements.txt`, `.gitignore`, `KNOWLEDGE.md` existieren
- `config/settings.yaml` existiert

---

## Phase 2: CLI-Grundgerüst

**Ziel:** Typer-basierte CLI mit allen Befehlen als Stubs, InquirerPy für interaktive Menüs.

- [x] `cli.py` — Typer-App mit folgenden Befehlen:
  - `doctor` — Projektprüfung (funktional)
  - `start` — Agent starten (Stub)
  - `config` — Konfiguration anzeigen/bearbeiten (InquirerPy-Menü)
  - `gui` — GUI starten (Stub)
  - `memory` — Konversationsspeicher verwalten (InquirerPy-Menü, Stub)
  - `chat` — Text-Chat im Terminal (Stub)
  - `voice` — Sprach-Chat im Terminal (Stub)
  - `upload` — Dokument hochladen & analysieren (Stub)
- [x] `main.py` ruft `cli.py` auf
- [x] Farbige Ausgabe mit `rich` für bessere UX

**Doctor prüft (ab jetzt):**
- `typer`, `InquirerPy`, `rich` importierbar
- Alle 8 CLI-Befehle sind registriert
- `python main.py --help` liefert Ausgabe

---

## Phase 3: LLM-Integration (OpenRouter)

**Ziel:** Verbindung zu OpenRouter über die OpenAI-Bibliothek herstellen.

- [x] `scripts/llm.py` — LLM-Client-Klasse
  - OpenAI-Client mit `base_url="https://openrouter.ai/api/v1"`
  - API-Key aus `.env` laden
  - Modellauswahl konfigurierbar via `config/settings.yaml`
  - Streaming-Support
- [x] `scripts/config_manager.py` — Config laden/speichern/validieren
- [x] `cli.py: config` — Konfiguration anzeigen, Modell und Temperatur ändern

**Doctor prüft (ab jetzt):**
- `openai` importierbar
- `scripts/llm.py` und `scripts/config_manager.py` existieren
- `settings.yaml` hat LLM-Sektion mit model, temperature, max_tokens
- `OPENROUTER_API_KEY` in `.env` gesetzt
- LLM-Client instanziierbar

---

## Phase 4: Chat-Funktion & Memory

**Ziel:** Vollfunktionaler Text-Chat mit Konversationsverlauf.

- [x] `agents/hotel_agent.py` — Hotel-Agent-Klasse
  - System-Prompt aus `config/system_prompt.txt`
  - Wissensdatenbank aus `KNOWLEDGE.md` als Kontext
  - Konversationsverlauf mit Max-History
  - Streaming-Support
- [x] `scripts/memory.py` — Persistenter Konversationsspeicher
  - Speichern/Laden von Chats in `data/conversations/` (JSON)
  - Konversationen auflisten, löschen, alle löschen
- [x] `cli.py: chat` — Interaktiver Chat-Loop mit Streaming
- [x] `cli.py: memory` — Konversationen verwalten (InquirerPy-Menü)
- [x] `cli.py: start` — Startet Chat mit Banner

**Doctor prüft (ab jetzt):**
- `agents/hotel_agent.py` und `scripts/memory.py` existieren
- HotelAgent instanziierbar
- Memory speichern/laden/löschen funktioniert
- `data/conversations/` existiert

---

## Phase 5: Voice-I/O

**Ziel:** Sprachein- und -ausgabe für den Agenten.

- [x] `scripts/voice.py` — Voice-Modul
  - **VoiceRecorder:** Mikrofon-Aufnahme via `sounddevice` (Push-to-Talk mit Enter)
  - **SpeechToText:** Transkription via Whisper API
  - **TextToSpeech:** Sprachausgabe via `pyttsx3` (offline, deutsche Stimme wenn verfügbar)
- [x] `cli.py: voice` — Sprach-Chat-Loop im Terminal
  - Enter zum Starten/Stoppen der Aufnahme
  - Antwort wird vorgelesen

**Doctor prüft (ab jetzt):**
- `scripts/voice.py` existiert
- `sounddevice`, `soundfile`, `pyttsx3`, `numpy` importierbar
- Mikrofon erkannt
- TTS-Engine funktioniert

---

## Phase 6: Gmail-Integration

**Ziel:** Gmail-Entwürfe erstellen können.

- [x] `scripts/gmail.py` — Gmail-Modul
  - OAuth2-Authentifizierung (Google API)
  - `credentials.json` in `config/` (von Google Cloud Console)
  - Token-Speicherung in `config/token.json`
  - Entwurf erstellen (Empfänger, Betreff, Text)
  - Entwürfe auflisten
- [x] Agent-Tool: `create_gmail_draft` — Agent kann im Chat Entwürfe erstellen
- [x] Tool-Call-Loop im Agent (automatische Tool-Ausführung + Antwort)

**Doctor prüft (ab jetzt):**
- `scripts/gmail.py` existiert
- `googleapiclient`, `google_auth_oauthlib` importierbar
- Agent-Tool `create_gmail_draft` registriert
- `config/credentials.json` vorhanden (Warnung wenn nicht)

---

## Phase 7: Dokument-Upload & Wissensextraktion

**Ziel:** Dokumente hochladen, analysieren und Wissen in KNOWLEDGE.md speichern.

- [x] `scripts/documents.py` — Dokument-Verarbeitung
  - Unterstützte Formate: PDF, DOCX, TXT, CSV, MD
  - Text-Extraktion (via `PyPDF2`, `python-docx`, etc.)
  - Analyse durch LLM (Zusammenfassung, Schlüsselinformationen)
- [x] `KNOWLEDGE.md` — Wissensdatenbank im Root
  - Strukturiertes Format (Quelle, Datum, Inhalt)
  - Wird vom Agenten als Kontext genutzt
- [x] `cli.py: upload` — Datei-Upload mit Analyse und Wissensspeicherung
- [x] Agent-Tool: `search_knowledge` — Agent kann Wissensdatenbank durchsuchen

**Doctor prüft (ab jetzt):**
- `scripts/documents.py` existiert
- `PyPDF2`, `docx` importierbar
- `KNOWLEDGE.md` existiert
- `data/uploads/` existiert
- Agent-Tool `search_knowledge` registriert
- Text-Extraktion funktioniert

---

## Phase 8: GUI (CustomTkinter)

**Ziel:** Grafische Oberfläche mit allen Funktionen.

- [ ] `gui.py` — CustomTkinter-Anwendung
  - Chat-Fenster mit Nachrichtenverlauf
  - Texteingabe + Senden-Button
  - Voice-Button (Mikrofon an/aus)
  - Datei-Upload-Button
  - Gmail-Entwurf-Panel
  - Einstellungen-Dialog (Modell, API-Keys, Audio-Geräte)
  - Dunkles/Helles Theme
- [ ] `cli.py: gui` — Startet die GUI

**Doctor ergänzt:**
- CustomTkinter ist importierbar
- GUI-Klasse kann instanziiert werden
- Alle UI-Elemente sind vorhanden

---

## Phase 9: Automatische E-Mail-Beantwortung (check-mails)

**Ziel:** Agent liest Posteingang, erkennt Anfragen, wählt passende Gmail-Vorlage aus, passt sie an und erstellt automatisch Entwürfe.

### Kernprinzipien

1. **Vorlagen sind heilig:** Die Gmail-Vorlagen werden 1:1 übernommen — Formulierungen, Struktur, Tonfall bleiben exakt erhalten. Der Agent darf nichts umschreiben, ergänzen oder in eigenen Worten formulieren.
2. **Nur anpassen, nicht neu schreiben:** Was der Agent tut:
   - Platzhalter ersetzen (z.B. "Herr / Frau ..." → "Herr Schmidt")
   - Nicht angeforderte Optionen entfernen (z.B. bei Preisanfrage für 5 Nächte: nur 5-Nächte-Preis + 7-Nächte-Preis wegen Rabatt zeigen, restliche Preisstufen entfernen)
   - Datumsangaben einsetzen wo nötig
3. **Keine Ausreden oder Verweise:** Der Agent darf niemals schreiben "hierfür sollten Sie einen Mitarbeiter kontaktieren" oder "hier bin ich mir nicht sicher". Wenn eine Anfrage nicht zu einer Vorlage passt → überspringen (kein Entwurf), nicht improvisieren.
4. **Jahr-Filter:** Vorlagen enthalten ein Jahr im Namen. Vorlagen mit Jahr < 2025 werden automatisch ignoriert (veraltet).

### Ablauf

1. **Posteingang lesen** — Ungelesene/neue E-Mails abrufen via Gmail API
2. **Anfragen erkennen** — LLM klassifiziert: Ist das eine Gästeanfrage? Wenn nein → überspringen
3. **Vorlage zuordnen** — Aus den ~20 Gmail-Vorlagen die passende auswählen (LLM-gestützt)
4. **Vorlage anpassen** — Platzhalter ersetzen, irrelevante Abschnitte entfernen (z.B. nicht angefragte Aufenthaltsdauern/Preise), angeforderte Daten einsetzen. 7-Tage-Option immer beibehalten (Rabatthinweis).
5. **Entwurf erstellen** — Gmail-Entwurf als Antwort auf die Original-E-Mail erstellen

### Implementierung

- [ ] `scripts/gmail.py` erweitern:
  - Posteingang lesen (ungelesene E-Mails)
  - Gmail-Vorlagen (Templates/Drafts) abrufen und cachen
  - Entwurf als Antwort auf eine bestehende E-Mail erstellen (In-Reply-To / Thread)
- [ ] `scripts/email_processor.py` — E-Mail-Verarbeitungs-Pipeline
  - Anfrage-Erkennung (LLM-Klassifikation)
  - Vorlagen-Zuordnung (LLM wählt aus Vorlagenliste die passende)
  - Vorlagen-Anpassung (LLM füllt Platzhalter, entfernt nicht-relevante Optionen, behält 7-Tage-Rabatt)
  - Validierung: Ergebnis muss strukturell der Vorlage entsprechen
- [ ] `cli.py: check-mails` — CLI-Befehl zum Starten der E-Mail-Verarbeitung
- [ ] Agent-Tool: `check_mails` — Agent kann im Chat E-Mails verarbeiten
- [ ] GUI: Button "E-Mails prüfen" in Sidebar

**Doctor prüft (ab jetzt):**
- `scripts/email_processor.py` existiert
- Gmail Posteingang-Lesezugriff (Scope erweitert)
- Gmail-Vorlagen abrufbar
- CLI-Befehl `check-mails` registriert
- Agent-Tool `check_mails` registriert

---

## Phase 10: Agent-Erstellung

**Ziel:** Benutzer können eigene Agents erstellen, bearbeiten und verwalten. Agent-Dateien werden im Ordner `agents/` gespeichert.

### Konzept

Jeder Agent ist eine eigenständige Python-Datei in `agents/` mit eigenem System-Prompt, eigener Tool-Auswahl und optionaler Wissensdatenbank. Der bestehende `hotel_agent.py` bleibt als Standard-Agent erhalten. Neue Agents können über CLI oder GUI erstellt werden.

### Agent-Struktur

Jeder Agent wird als JSON-Konfiguration + Python-Klasse gespeichert:
- `agents/<name>.json` — Konfiguration (Name, Beschreibung, System-Prompt, aktivierte Tools, Wissenspfad, LLM-Einstellungen)
- `agents/<name>.py` — Wird automatisch generiert aus der JSON-Config, erbt von einer Basis-Agent-Klasse

### Ablauf

1. **Agent erstellen** — Name, Beschreibung, System-Prompt, Tools auswählen
2. **Agent konfigurieren** — LLM-Modell, Temperatur, Max-Tokens, Wissensdatenbank zuweisen
3. **Agent testen** — Direkt im Chat testen
4. **Agent bearbeiten** — Bestehende Agents nachträglich anpassen
5. **Agent löschen** — Agent-Dateien entfernen

### Implementierung

- [ ] `agents/base_agent.py` — Basis-Agent-Klasse (gemeinsame Logik aus `hotel_agent.py` extrahieren)
- [ ] `scripts/agent_manager.py` — Agent-Verwaltung
  - `create_agent(name, description, system_prompt, tools, ...)` — Agent-Config + Datei erstellen
  - `list_agents()` — Alle Agents in `agents/` auflisten
  - `load_agent(name)` — Agent laden und instanziieren
  - `update_agent(name, ...)` — Agent-Config aktualisieren
  - `delete_agent(name)` — Agent-Dateien löschen
- [ ] `cli.py: agents` — CLI-Befehl mit InquirerPy-Menü
  - Agent erstellen (interaktiver Wizard: Name → Beschreibung → System-Prompt → Tools wählen → LLM-Settings)
  - Agents auflisten
  - Agent starten (Chat mit ausgewähltem Agent)
  - Agent bearbeiten
  - Agent löschen
- [ ] `gui.py` — Agent-Verwaltung in der GUI
  - Agent-Auswahl in Sidebar (Dropdown oder Liste)
  - "Neuer Agent"-Dialog (Formular mit allen Feldern)
  - Agent-Einstellungen bearbeiten
- [ ] `cli.py: chat` und GUI — Agent-Auswahl vor Chat-Start (Standard: hotel_agent)

**Doctor prüft (ab jetzt):**
- `agents/base_agent.py` existiert
- `scripts/agent_manager.py` existiert
- CLI-Befehl `agents` registriert
- Agent erstellen/laden/löschen funktioniert
- Mindestens `hotel_agent` ist als Agent verfügbar

---

## Phase 11: Automationen

**Ziel:** Wiederkehrende Aufgaben automatisieren — zeitgesteuert oder event-basiert. Verwaltung über CLI und GUI.

### Konzept

Automationen sind konfigurierbare Tasks, die automatisch ausgeführt werden. Jede Automation hat einen Trigger (wann), eine Aktion (was) und optionale Bedingungen (wenn). Automationen werden als JSON in `data/automations/` gespeichert.

### Automation-Typen

1. **Zeitgesteuert (Cron):** Regelmäßige Ausführung nach Zeitplan
   - z.B. "Jeden Morgen um 8:00 Uhr E-Mails prüfen"
   - z.B. "Jeden Montag Website crawlen und Wissen aktualisieren"
2. **Event-basiert:** Auslösung durch bestimmte Ereignisse
   - z.B. "Bei neuer E-Mail automatisch klassifizieren"
   - z.B. "Nach Dokument-Upload automatisch analysieren"
3. **Manuell auslösbar:** Definierte Abläufe auf Knopfdruck starten
   - z.B. "Morgen-Routine: E-Mails prüfen + Zusammenfassung erstellen"

### Verfügbare Aktionen

- `check_mails` — Posteingang prüfen und Entwürfe erstellen
- `crawl_website` — Hotel-Website crawlen und Wissen aktualisieren
- `send_report` — Tagesbericht per E-Mail-Entwurf erstellen
- `backup_knowledge` — Wissensdatenbank sichern
- `run_agent_task` — Einen bestimmten Agent mit einer Aufgabe beauftragen

### Implementierung

- [ ] `data/automations/` — Ordner für Automation-Configs (JSON)
- [ ] `scripts/automation_manager.py` — Automation-Verwaltung
  - `create_automation(name, trigger, action, config)` — Automation erstellen
  - `list_automations()` — Alle Automationen auflisten
  - `enable_automation(name)` / `disable_automation(name)` — An/Aus schalten
  - `run_automation(name)` — Manuell auslösen
  - `delete_automation(name)` — Automation löschen
- [ ] `scripts/scheduler.py` — Zeitsteuerung
  - Cron-ähnlicher Scheduler (z.B. via `schedule` oder `APScheduler`)
  - Läuft als Hintergrundprozess oder wird per CLI gestartet
  - Logging aller Ausführungen in `data/logs/`
- [ ] `cli.py: automations` — CLI-Befehl mit InquirerPy-Menü
  - Automation erstellen (Wizard: Name → Trigger-Typ → Zeitplan/Event → Aktion wählen → Parameter)
  - Automationen auflisten (mit Status aktiv/inaktiv)
  - Automation aktivieren/deaktivieren
  - Automation manuell ausführen
  - Automation löschen
- [ ] `cli.py: scheduler` — Scheduler starten/stoppen
- [ ] `gui.py` — Automationen in der GUI
  - "Automationen"-Button in Sidebar
  - Übersicht aller Automationen (Tabelle mit Name, Trigger, Status, letzte Ausführung)
  - "Neue Automation"-Dialog
  - Aktivieren/Deaktivieren per Toggle
  - Manuelles Auslösen per Button
  - Log-Ansicht der letzten Ausführungen

**Doctor prüft (ab jetzt):**
- `data/automations/` existiert
- `scripts/automation_manager.py` existiert
- `scripts/scheduler.py` existiert
- CLI-Befehle `automations` und `scheduler` registriert
- Automation erstellen/laden/löschen funktioniert

---

## Phase 12: Multi-Provider E-Mail & EXE-Build

**Ziel:** Unterstuetzung fuer beliebige E-Mail-Provider (nicht nur Gmail) + ausfuehrbare EXE-Datei.

### E-Mail-Provider-Abstraktion

- [x] `scripts/email_provider.py` — Provider-Abstraktion
  - `EmailProvider` abstrakte Basis-Klasse
  - `GmailOAuthProvider` — Wrapper fuer bestehende Gmail OAuth2 API
  - `ImapSmtpProvider` — Generischer IMAP/SMTP-Provider fuer alle anderen Anbieter
  - `get_provider()` Factory-Funktion (liest Provider aus settings.yaml)
  - 17 Provider-Presets mit vorkonfigurierten IMAP/SMTP-Einstellungen:
    - Gmail, Outlook/Hotmail, Yahoo, GMX, Web.de, T-Online
    - AOL, iCloud, Zoho, Fastmail, ProtonMail (Bridge)
    - Mail.de, Posteo, Mailbox.org, IONOS (1&1), Strato, Freenet
  - Benutzerdefinierte IMAP/SMTP-Konfiguration fuer beliebige Provider
- [x] `scripts/email_processor.py` — Nutzt Provider-Abstraktion statt direkter Gmail-Imports
- [x] `agents/base_agent.py` — Tools nutzen Provider-Abstraktion
- [x] `cli.py: email-setup` — CLI-Befehl zum Einrichten des E-Mail-Providers
- [x] `gui.py: EmailSetupDialog` — GUI-Dialog zur Provider-Konfiguration mit Verbindungstest
- [x] `config/settings.yaml` — Neue email-Sektion mit Provider-Konfiguration

### EXE-Build

- [x] `build_exe.py` — PyInstaller Build-Script
- [x] `gui_launcher.py` — Einstiegspunkt fuer die EXE (oeffnet direkt die GUI)
- [x] PyInstaller in requirements.txt

**Doctor prueft (ab jetzt):**
- `scripts/email_provider.py` existiert und ist importierbar
- Provider-Presets vorhanden (mindestens 10)
- GmailOAuthProvider und ImapSmtpProvider erben von EmailProvider
- get_provider() funktioniert
- settings.yaml hat email-Sektion
- CLI-Befehl `email-setup` registriert
- email_processor nutzt Provider-Abstraktion
- GUI hat EmailSetupDialog und Setup-Button
- build_exe.py und gui_launcher.py existieren
- PyInstaller importierbar

---

## Phase 13: Installer & Setup Wizard

**Ziel:** Standalone-Installer-EXE die alles einrichtet + Erst-Einrichtungs-Assistent in der GUI.

### Installer (`installer.py`)

- [x] Standalone-Installer mit tkinter-GUI (dunkel, modern)
- [x] Prueft Voraussetzungen (Python 3.10+, Git)
- [x] Klont Repository von github.com/raphael-cmyk/hotelagent
- [x] Installiert nach `C:/Users/<user>/.hotelagent`
- [x] Erstellt Virtual Environment und installiert Abhaengigkeiten
- [x] Erstellt `.env` Datei mit API-Key
- [x] Baut GUI-EXE mit PyInstaller
- [x] Erstellt Desktop-Verknuepfung
- [x] Fuehrt Doctor-Check aus
- [x] Startet die GUI fuer die Erst-Einrichtung

### Installer-EXE Builder (`build_installer.py`)

- [x] Kompiliert `installer.py` in standalone `HotelAgent_Installer.exe` (--onefile)
- [x] Keine externen Abhaengigkeiten auf dem Zielsystem (ausser Python + Git)

### Setup Wizard (`SetupWizardDialog` in `gui.py`)

- [x] Wird automatisch beim ersten Start der GUI angezeigt
- [x] Fragt nach OpenRouter API-Key
- [x] Fragt nach E-Mail-Provider (alle 17+ Provider verfuegbar)
- [x] Speichert Konfiguration in `.env` und `settings.yaml`
- [x] Erstellt Marker-Datei `data/.setup_complete` (verhindert erneutes Anzeigen)
- [x] Kann uebersprungen werden

**Doctor prueft (ab jetzt):**
- `installer.py`, `build_installer.py`, `gui_launcher.py` existieren
- SetupWizardDialog und is_first_run in GUI vorhanden
- installer.py syntaktisch korrekt und alle Schritte vorhanden

---

## Technologie-Stack

| Komponente | Bibliothek |
|---|---|
| CLI | `typer`, `InquirerPy`, `rich` |
| LLM | `openai` (via OpenRouter) |
| GUI | `customtkinter` |
| Voice STT | `sounddevice`, `whisper` / OpenAI API |
| Voice TTS | `pyttsx3` / OpenAI TTS API |
| Gmail | `google-api-python-client`, `google-auth-oauthlib` |
| Dokumente | `PyPDF2`, `python-docx`, `csv` |
| Config | `pyyaml`, `python-dotenv` |
| Logging | `loguru` |
