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
