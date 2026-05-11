# HotelAgent — KI-Hotelassistent

Ein KI-gestützter Hotelassistent mit CLI, GUI, Sprach-Chat, Gmail-Integration und automatischer E-Mail-Beantwortung. Gebaut mit Python, OpenRouter (LLM) und CustomTkinter.

## Features

- **Text-Chat** — Interaktiver Chat im Terminal mit Streaming
- **Sprach-Chat** — Spracheingabe (Mikrofon) + Sprachausgabe (TTS)
- **GUI** — Grafische Oberfläche mit Dark/Light Mode (CustomTkinter)
- **Gmail-Integration** — Entwürfe erstellen, Posteingang lesen, automatische Antworten
- **Dokument-Upload** — PDF, Word, TXT analysieren und Wissen extrahieren
- **Website-Crawling** — Hotel-Website crawlen und Wissen aufbauen
- **Automatische E-Mail-Beantwortung** — Gästeanfragen erkennen, Vorlagen zuordnen, Entwürfe erstellen

## Voraussetzungen

- Python 3.10 oder höher
- Ein [OpenRouter](https://openrouter.ai/) API-Key
- (Optional) Google Cloud Credentials für Gmail-Funktionen
- (Optional) Mikrofon für Sprach-Chat

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/<dein-username>/hotelagent.git
cd hotelagent
```

### 2. Virtuelle Umgebung erstellen und aktivieren

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. `.env`-Datei erstellen

Erstelle eine `.env`-Datei im Projektroot (eine `.env.example` liegt als Vorlage bei):

```bash
cp .env.example .env
```

Öffne die `.env` und trage deinen OpenRouter API-Key ein:

```env
OPENROUTER_API_KEY=dein-openrouter-api-key-hier
GOOGLE_APPLICATION_CREDENTIALS=config/credentials.json
```

Den API-Key bekommst du unter [openrouter.ai/keys](https://openrouter.ai/keys).

### 5. (Optional) Gmail einrichten

Damit die Gmail-Funktionen (Entwürfe, E-Mail-Prüfung) funktionieren:

1. Erstelle ein Projekt in der [Google Cloud Console](https://console.cloud.google.com/)
2. Aktiviere die **Gmail API**
3. Erstelle OAuth 2.0 Credentials (Desktop-App)
4. Lade die `credentials.json` herunter und lege sie unter `config/credentials.json` ab
5. Beim ersten Aufruf einer Gmail-Funktion öffnet sich ein Browser-Fenster zur Authentifizierung — danach wird automatisch ein `config/token.json` erstellt

Für die automatische E-Mail-Beantwortung (`check-mails`):
- Erstelle in Gmail ein Label namens **"Vorlagen"**
- Verschiebe deine E-Mail-Antwortvorlagen in dieses Label

## Nutzung

### Projekt prüfen (Doctor)

Prüft ob alles korrekt eingerichtet ist:

```bash
python main.py doctor
```

### Text-Chat starten

```bash
python main.py chat
```

### Sprach-Chat starten

```bash
python main.py voice
```

### GUI starten

```bash
python main.py gui
```

### Konfiguration bearbeiten

```bash
python main.py config
```

### Dokument hochladen und analysieren

```bash
python main.py upload <pfad-zur-datei>
```

### Hotel-Website crawlen

```bash
python main.py check-web https://hotel-beispiel.de
```

### E-Mails prüfen und automatisch Entwürfe erstellen

```bash
python main.py check-mails
```

### Konversationen verwalten

```bash
python main.py memory
```

## Konfiguration

Die Konfiguration liegt in `config/settings.yaml`:

| Einstellung | Beschreibung | Standard |
|---|---|---|
| `llm.model` | LLM-Modell (OpenRouter) | `deepseek/deepseek-v4-flash` |
| `llm.temperature` | Kreativität (0.0–2.0) | `0.7` |
| `llm.max_tokens` | Max. Antwortlänge | `2048` |
| `llm.streaming` | Token-Streaming | `true` |
| `gmail.credentials_path` | Pfad zur credentials.json | `config/credentials.json` |
| `email_processing.template_label` | Gmail-Label für Vorlagen | `Vorlagen` |
| `voice.tts_engine` | Text-to-Speech Engine | `pyttsx3` |

Die Einstellungen lassen sich auch über `python main.py config` oder die GUI (Einstellungen-Button) ändern.

## Projektstruktur

```
hotelagent/
├── main.py                  # Einstiegspunkt
├── cli.py                   # CLI mit allen Befehlen (Typer)
├── gui.py                   # GUI (CustomTkinter)
├── agents/
│   └── hotel_agent.py       # KI-Agent mit Tool-Calls
├── scripts/
│   ├── llm.py               # OpenRouter LLM-Client
│   ├── gmail.py             # Gmail API (Entwürfe, Posteingang, Vorlagen)
│   ├── email_processor.py   # Automatische E-Mail-Beantwortung
│   ├── voice.py             # Spracheingabe & -ausgabe
│   ├── documents.py         # Dokument-Upload & Analyse
│   ├── web_scraper.py       # Website-Crawling
│   ├── memory.py            # Konversationsspeicher
│   ├── config_manager.py    # YAML-Config laden/speichern
│   └── doctor.py            # Projektprüfung
├── config/
│   ├── settings.yaml        # Konfiguration
│   ├── system_prompt.txt    # System-Prompt für den Agent
│   ├── credentials.json     # Google OAuth Credentials (nicht im Repo)
│   └── token.json           # Google OAuth Token (nicht im Repo)
├── data/
│   ├── conversations/       # Gespeicherte Chat-Verläufe
│   ├── uploads/             # Hochgeladene Dokumente
│   └── logs/                # Log-Dateien
├── KNOWLEDGE.md             # Wissensdatenbank (extrahiertes Wissen)
├── requirements.txt         # Python-Abhängigkeiten
├── pyproject.toml           # Build-Konfiguration
├── .env.example             # Vorlage für Umgebungsvariablen
└── .gitignore
```
