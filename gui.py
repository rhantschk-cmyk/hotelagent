"""HotelAgent — GUI (CustomTkinter)."""

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from scripts.config_manager import load_config, save_config


# ---------------------------------------------------------------------------
# Theme / Appearance
# ---------------------------------------------------------------------------

# Farb-Palette
COLORS = {
    "bg_dark": "#0f0f1a",
    "bg_sidebar": "#141425",
    "bg_card": "#1c1c35",
    "bg_input": "#1a1a30",
    "accent": "#e94560",
    "accent_hover": "#d63d56",
    "accent_soft": "#2a1a2e",
    "text_primary": "#f0f0f5",
    "text_secondary": "#8888a0",
    "text_muted": "#555570",
    "border": "#2a2a45",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "purple": "#7c3aed",
    "purple_hover": "#6d28d9",
    "cyan": "#06b6d4",
    "cyan_hover": "#0891b2",
    "bubble_user": "#2563eb",
    "bubble_user_hover": "#1d4ed8",
    "bubble_agent": "#252540",
}

ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Chat-Bubble Frame
# ---------------------------------------------------------------------------

class ChatBubble(ctk.CTkFrame):
    """Einzelne Chat-Nachricht (User oder Agent)."""

    def __init__(self, master, role: str, text: str, **kwargs):
        is_user = role == "user"

        super().__init__(master, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)

        # Container fuer Bubble + Meta
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0,
                       sticky="e" if is_user else "w",
                       padx=(80 if is_user else 12, 12 if is_user else 80),
                       pady=4)

        # Rolle-Label
        role_text = "Du" if is_user else "HotelAgent"
        role_color = COLORS["bubble_user"] if is_user else COLORS["accent"]
        ctk.CTkLabel(
            container, text=role_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=role_color,
        ).pack(anchor="e" if is_user else "w", padx=4)

        # Bubble
        bubble_color = COLORS["bubble_user"] if is_user else COLORS["bubble_agent"]
        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=16,
                              border_width=1,
                              border_color=COLORS["border"] if not is_user else bubble_color)
        bubble.pack(anchor="e" if is_user else "w", fill="x")

        label = ctk.CTkLabel(
            bubble,
            text=text,
            wraplength=500,
            justify="left",
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        label.pack(padx=16, pady=10)

        # Timestamp
        time_str = datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            container, text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(anchor="e" if is_user else "w", padx=4, pady=(2, 0))


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(ctk.CTkToplevel):
    """Einstellungen-Dialog: Provider, Modell, Temperatur, Theme."""

    def __init__(self, master, on_save=None):
        super().__init__(master)
        self.title("Einstellungen")
        self.geometry("520x620")
        self.resizable(False, False)
        self.grab_set()

        self._on_save = on_save
        self._cfg = load_config()

        from scripts.llm import PROVIDERS
        self._providers = PROVIDERS

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Einstellungen",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # -- Provider Sektion --
        self._section_label(content, "LLM-Provider")

        ctk.CTkLabel(content, text="Provider", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))

        provider_display = {k: v["name"] for k, v in PROVIDERS.items()}
        self._provider_keys = {v["name"]: k for k, v in PROVIDERS.items()}
        provider_names = [PROVIDERS["openai"]["name"], PROVIDERS["claude"]["name"], PROVIDERS["openrouter"]["name"]]

        current_provider = self._cfg["llm"].get("provider", "openrouter")
        current_display = PROVIDERS.get(current_provider, {}).get("name", "OpenRouter (Debug/CLI)")

        self.provider_menu = ctk.CTkOptionMenu(
            content, values=provider_names,
            fg_color=COLORS["bg_input"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            command=self._on_provider_changed)
        self.provider_menu.set(current_display)
        self.provider_menu.pack(fill="x")

        # API-Key
        ctk.CTkLabel(content, text="API-Key", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.api_key_entry = ctk.CTkEntry(content, height=36,
                                           fg_color=COLORS["bg_input"],
                                           border_color=COLORS["border"],
                                           show="*",
                                           placeholder_text="API-Key eingeben...")
        self.api_key_entry.pack(fill="x")

        # Vorhandenen Key laden
        import os
        env_key = PROVIDERS.get(current_provider, {}).get("env_key", "")
        existing = os.getenv(env_key, "")
        if existing:
            self.api_key_entry.insert(0, existing)

        self.api_key_hint = ctk.CTkLabel(content, text="",
                                          text_color=COLORS["text_muted"],
                                          font=ctk.CTkFont(size=10))
        self.api_key_hint.pack(anchor="w")
        self._update_key_hint(current_provider)

        # -- Modell Sektion --
        self._section_label(content, "Modell")

        ctk.CTkLabel(content, text="Modell auswaehlen", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))

        models = PROVIDERS.get(current_provider, {}).get("models", [])
        self.model_menu = ctk.CTkOptionMenu(
            content, values=models if models else [""],
            fg_color=COLORS["bg_input"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"])
        current_model = self._cfg["llm"].get("model", "")
        if current_model in models:
            self.model_menu.set(current_model)
        elif models:
            self.model_menu.set(models[0])
        self.model_menu.pack(fill="x")

        # Oder manuell eingeben
        ctk.CTkLabel(content, text="Oder manuell eingeben:",
                     text_color=COLORS["text_muted"],
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(6, 2))
        self.model_entry = ctk.CTkEntry(content, height=32,
                                         fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"],
                                         placeholder_text="z.B. gpt-4o-mini")
        self.model_entry.pack(fill="x")

        # -- Parameter --
        self._section_label(content, "Parameter")

        ctk.CTkLabel(content, text="Temperatur", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 2))
        self.temp_slider = ctk.CTkSlider(content, from_=0, to=2, number_of_steps=20,
                                          progress_color=COLORS["accent"],
                                          button_color=COLORS["accent"],
                                          button_hover_color=COLORS["accent_hover"])
        self.temp_slider.set(self._cfg["llm"].get("temperature", 0.7))
        self.temp_slider.pack(fill="x")
        self.temp_label = ctk.CTkLabel(content, text=f"{self._cfg['llm'].get('temperature', 0.7):.1f}",
                                        text_color=COLORS["text_muted"], font=ctk.CTkFont(size=11))
        self.temp_label.pack(anchor="w")
        self.temp_slider.configure(command=lambda v: self.temp_label.configure(text=f"{v:.1f}"))

        ctk.CTkLabel(content, text="Max Tokens", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(12, 2))
        self.tokens_entry = ctk.CTkEntry(content, height=36,
                                          fg_color=COLORS["bg_input"],
                                          border_color=COLORS["border"])
        self.tokens_entry.insert(0, str(self._cfg["llm"].get("max_tokens", 2048)))
        self.tokens_entry.pack(fill="x")

        # -- Theme Sektion --
        self._section_label(content, "Darstellung")

        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_frame = ctk.CTkFrame(content, fg_color="transparent")
        theme_frame.pack(anchor="w", pady=(8, 0))
        ctk.CTkRadioButton(theme_frame, text="Dunkel", variable=self.theme_var,
                           value="Dark", fg_color=COLORS["accent"],
                           hover_color=COLORS["accent_hover"]).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(theme_frame, text="Hell", variable=self.theme_var,
                           value="Light", fg_color=COLORS["accent"],
                           hover_color=COLORS["accent_hover"]).pack(side="left")

        # -- Buttons --
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(btn_frame, text="Speichern", height=36,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self.destroy).pack(side="right")

    def _on_provider_changed(self, display_name: str):
        """Provider gewechselt — Modell-Liste und Key-Hint aktualisieren."""
        import os
        provider_key = self._provider_keys.get(display_name, "openrouter")
        models = self._providers.get(provider_key, {}).get("models", [])
        self.model_menu.configure(values=models if models else [""])
        if models:
            self.model_menu.set(models[0])

        # API-Key aktualisieren
        env_key = self._providers.get(provider_key, {}).get("env_key", "")
        existing = os.getenv(env_key, "")
        self.api_key_entry.delete(0, "end")
        if existing:
            self.api_key_entry.insert(0, existing)
        self._update_key_hint(provider_key)

    def _update_key_hint(self, provider_key: str):
        hints = {
            "openai": "Env: OPENAI_API_KEY — von platform.openai.com/api-keys",
            "claude": "Env: ANTHROPIC_API_KEY — von console.anthropic.com",
            "openrouter": "Env: OPENROUTER_API_KEY — von openrouter.ai/keys (nur Debug/CLI)",
        }
        self.api_key_hint.configure(text=hints.get(provider_key, ""))

    @staticmethod
    def _section_label(parent, text):
        sep = ctk.CTkFrame(parent, fg_color=COLORS["border"], height=1)
        sep.pack(fill="x", pady=(16, 8))
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w")

    def _save(self):
        import os
        from pathlib import Path

        # Provider
        display_name = self.provider_menu.get()
        provider_key = self._provider_keys.get(display_name, "openrouter")
        self._cfg["llm"]["provider"] = provider_key

        # Modell (manuell hat Vorrang)
        manual_model = self.model_entry.get().strip()
        if manual_model:
            self._cfg["llm"]["model"] = manual_model
        else:
            self._cfg["llm"]["model"] = self.model_menu.get()

        # Parameter
        self._cfg["llm"]["temperature"] = round(self.temp_slider.get(), 1)
        try:
            self._cfg["llm"]["max_tokens"] = int(self.tokens_entry.get())
        except ValueError:
            pass

        # API-Key in .env speichern
        api_key = self.api_key_entry.get().strip()
        if api_key:
            env_var = self._providers.get(provider_key, {}).get("env_key", "")
            if env_var:
                os.environ[env_var] = api_key
                env_path = Path(__file__).parent / ".env"
                self._update_env_file(env_path, env_var, api_key)

        ctk.set_appearance_mode(self.theme_var.get())
        save_config(self._cfg)

        if self._on_save:
            self._on_save(self._cfg)
        self.destroy()

    @staticmethod
    def _update_env_file(env_path: Path, key: str, value: str):
        """Key in .env Datei setzen oder aktualisieren."""
        import re
        if env_path.is_file():
            content = env_path.read_text(encoding="utf-8")
            if key in content:
                content = re.sub(rf"{key}=.*", f"{key}={value}", content)
            else:
                content += f"\n{key}={value}\n"
            env_path.write_text(content, encoding="utf-8")
        else:
            env_path.write_text(f"{key}={value}\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Email Setup Dialog
# ---------------------------------------------------------------------------

class EmailSetupDialog(ctk.CTkToplevel):
    """Dialog zum Einrichten eines E-Mail-Providers."""

    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.title("E-Mail-Provider einrichten")
        self.geometry("540x600")
        self.resizable(False, False)
        self.grab_set()
        self._on_saved = on_saved

        from scripts.email_provider import KNOWN_PROVIDERS, get_provider_display_name

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="E-Mail-Provider einrichten",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # Aktueller Provider
        current = get_provider_display_name()
        ctk.CTkLabel(content, text=f"Aktuell: {current}",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=11)).pack(anchor="w")

        # Provider-Auswahl
        ctk.CTkLabel(content, text="Provider waehlen:",
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(12, 4))

        provider_names = ["Gmail (OAuth2 API)"]
        self._provider_keys = {"Gmail (OAuth2 API)": "gmail_oauth"}
        for key, val in KNOWN_PROVIDERS.items():
            name = val["name"]
            provider_names.append(name)
            self._provider_keys[name] = key
        provider_names.append("Benutzerdefiniert (IMAP/SMTP)")
        self._provider_keys["Benutzerdefiniert (IMAP/SMTP)"] = "custom"

        self.provider_menu = ctk.CTkOptionMenu(
            content, values=provider_names, width=460,
            fg_color=COLORS["bg_input"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            command=self._on_provider_changed,
        )
        self.provider_menu.pack(anchor="w")

        # Hinweis-Label
        self.note_label = ctk.CTkLabel(content, text="", text_color=COLORS["warning"],
                                        font=ctk.CTkFont(size=11), wraplength=460)
        self.note_label.pack(anchor="w", pady=(4, 0))

        # IMAP/SMTP-Felder
        self.imap_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.imap_frame.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(self.imap_frame, text="E-Mail-Adresse / Benutzername:",
                     text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.username_entry = ctk.CTkEntry(self.imap_frame, width=460, height=36,
                                            placeholder_text="user@example.com",
                                            fg_color=COLORS["bg_input"],
                                            border_color=COLORS["border"])
        self.username_entry.pack(anchor="w")

        ctk.CTkLabel(self.imap_frame, text="Passwort / App-Passwort:",
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(8, 0))
        self.password_entry = ctk.CTkEntry(self.imap_frame, width=460, height=36,
                                            placeholder_text="Passwort", show="*",
                                            fg_color=COLORS["bg_input"],
                                            border_color=COLORS["border"])
        self.password_entry.pack(anchor="w")

        # Custom IMAP/SMTP Felder
        self.custom_frame = ctk.CTkFrame(self.imap_frame, fg_color="transparent")
        self.custom_frame.pack(fill="x", pady=(8, 0))

        row1 = ctk.CTkFrame(self.custom_frame, fg_color="transparent")
        row1.pack(fill="x")
        ctk.CTkLabel(row1, text="IMAP-Server:", text_color=COLORS["text_secondary"]).pack(side="left")
        self.imap_host_entry = ctk.CTkEntry(row1, width=240, height=32,
                                             placeholder_text="imap.example.com",
                                             fg_color=COLORS["bg_input"],
                                             border_color=COLORS["border"])
        self.imap_host_entry.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(row1, text="Port:", text_color=COLORS["text_secondary"]).pack(side="left", padx=(8, 0))
        self.imap_port_entry = ctk.CTkEntry(row1, width=60, height=32,
                                             fg_color=COLORS["bg_input"],
                                             border_color=COLORS["border"])
        self.imap_port_entry.insert(0, "993")
        self.imap_port_entry.pack(side="left", padx=(4, 0))

        row2 = ctk.CTkFrame(self.custom_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(row2, text="SMTP-Server:", text_color=COLORS["text_secondary"]).pack(side="left")
        self.smtp_host_entry = ctk.CTkEntry(row2, width=240, height=32,
                                             placeholder_text="smtp.example.com",
                                             fg_color=COLORS["bg_input"],
                                             border_color=COLORS["border"])
        self.smtp_host_entry.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(row2, text="Port:", text_color=COLORS["text_secondary"]).pack(side="left", padx=(8, 0))
        self.smtp_port_entry = ctk.CTkEntry(row2, width=60, height=32,
                                             fg_color=COLORS["bg_input"],
                                             border_color=COLORS["border"])
        self.smtp_port_entry.insert(0, "587")
        self.smtp_port_entry.pack(side="left", padx=(4, 0))

        # Initial: Custom-Felder verstecken
        self.custom_frame.pack_forget()

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(btn_frame, text="Verbindung testen", height=36,
                      fg_color=COLORS["purple"], hover_color=COLORS["purple_hover"],
                      command=self._test).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Speichern", height=36,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color=COLORS["success"],
                                          wraplength=460, font=ctk.CTkFont(size=12))
        self.status_label.pack(padx=24, pady=(0, 8))

        # Initial state
        self._on_provider_changed("Gmail (OAuth2 API)")

    def _on_provider_changed(self, name: str):
        from scripts.email_provider import KNOWN_PROVIDERS
        key = self._provider_keys.get(name, "")

        if key == "gmail_oauth":
            self.imap_frame.pack_forget()
            self.note_label.configure(
                text="Gmail OAuth2 nutzt credentials.json aus config/. "
                     "Lade sie von der Google Cloud Console herunter.")
        elif key == "custom":
            self.imap_frame.pack(fill="x", pady=(8, 0))
            self.custom_frame.pack(fill="x", pady=(6, 0))
            self.note_label.configure(text="Trage die IMAP/SMTP-Daten deines Providers ein.")
        elif key in KNOWN_PROVIDERS:
            self.imap_frame.pack(fill="x", pady=(8, 0))
            self.custom_frame.pack_forget()
            note = KNOWN_PROVIDERS[key].get("note", "")
            self.note_label.configure(text=note if note else "")
        else:
            self.imap_frame.pack_forget()

    def _get_selected_key(self) -> str:
        name = self.provider_menu.get()
        return self._provider_keys.get(name, "")

    def _save(self):
        from scripts.email_provider import setup_imap_provider, setup_gmail_oauth

        key = self._get_selected_key()

        if key == "gmail_oauth":
            setup_gmail_oauth()
            self.status_label.configure(text="Gmail OAuth2 als Provider gespeichert.", text_color=COLORS["success"])
            if self._on_saved:
                self._on_saved()
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_label.configure(text="E-Mail und Passwort sind Pflichtfelder.", text_color=COLORS["accent"])
            return

        if key == "custom":
            imap_host = self.imap_host_entry.get().strip()
            smtp_host = self.smtp_host_entry.get().strip()
            if not imap_host or not smtp_host:
                self.status_label.configure(text="IMAP- und SMTP-Server sind Pflichtfelder.", text_color=COLORS["accent"])
                return
            try:
                imap_port = int(self.imap_port_entry.get())
                smtp_port = int(self.smtp_port_entry.get())
            except ValueError:
                self.status_label.configure(text="Ports muessen Zahlen sein.", text_color=COLORS["accent"])
                return
            setup_imap_provider(
                imap_host=imap_host, imap_port=imap_port,
                smtp_host=smtp_host, smtp_port=smtp_port,
                username=username, password=password,
            )
        else:
            setup_imap_provider(preset_key=key, username=username, password=password)

        self.status_label.configure(text="E-Mail-Provider gespeichert!", text_color=COLORS["success"])
        if self._on_saved:
            self._on_saved()

    def _test(self):
        from scripts.email_provider import (
            setup_imap_provider, setup_gmail_oauth,
            ImapSmtpProvider, GmailOAuthProvider, KNOWN_PROVIDERS,
        )

        key = self._get_selected_key()
        self.status_label.configure(text="Teste Verbindung...", text_color=COLORS["text_muted"])
        self.update()

        if key == "gmail_oauth":
            provider = GmailOAuthProvider()
        elif key == "custom":
            imap_host = self.imap_host_entry.get().strip()
            smtp_host = self.smtp_host_entry.get().strip()
            try:
                imap_port = int(self.imap_port_entry.get())
                smtp_port = int(self.smtp_port_entry.get())
            except ValueError:
                self.status_label.configure(text="Ports muessen Zahlen sein.", text_color=COLORS["accent"])
                return
            provider = ImapSmtpProvider(
                imap_host=imap_host, imap_port=imap_port,
                smtp_host=smtp_host, smtp_port=smtp_port,
                username=self.username_entry.get().strip(),
                password=self.password_entry.get().strip(),
            )
        else:
            preset = KNOWN_PROVIDERS.get(key, {})
            provider = ImapSmtpProvider(
                imap_host=preset.get("imap_host", ""),
                imap_port=preset.get("imap_port", 993),
                smtp_host=preset.get("smtp_host", ""),
                smtp_port=preset.get("smtp_port", 587),
                username=self.username_entry.get().strip(),
                password=self.password_entry.get().strip(),
                use_ssl=preset.get("ssl", True),
            )

        def _run_test():
            success, msg = provider.test_connection()
            color = COLORS["success"] if success else COLORS["accent"]
            self.after(0, lambda: self.status_label.configure(text=msg, text_color=color))

        import threading
        threading.Thread(target=_run_test, daemon=True).start()


# ---------------------------------------------------------------------------
# Email Draft Dialog
# ---------------------------------------------------------------------------

class GmailDraftDialog(ctk.CTkToplevel):
    """Dialog zum Erstellen eines E-Mail-Entwurfs (alle Provider)."""

    def __init__(self, master, on_send=None):
        super().__init__(master)
        self.title("E-Mail-Entwurf erstellen")
        self.geometry("500x460")
        self.resizable(False, False)
        self.grab_set()
        self._on_send = on_send

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="E-Mail-Entwurf",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        # Provider-Info
        try:
            from scripts.email_provider import get_provider_display_name
            provider_name = get_provider_display_name()
        except Exception:
            provider_name = "Gmail"
        ctk.CTkLabel(content, text=f"Provider: {provider_name}",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=11)).pack(anchor="w")

        ctk.CTkLabel(content, text="Empfaenger", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(12, 2))
        self.to_entry = ctk.CTkEntry(content, height=36, placeholder_text="empfaenger@example.com",
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.to_entry.pack(fill="x")

        ctk.CTkLabel(content, text="Betreff", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.subject_entry = ctk.CTkEntry(content, height=36, placeholder_text="Betreff...",
                                           fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.subject_entry.pack(fill="x")

        ctk.CTkLabel(content, text="Nachricht", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.body_text = ctk.CTkTextbox(content, height=160,
                                         fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"],
                                         border_width=1)
        self.body_text.pack(fill="x")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(btn_frame, text="Entwurf erstellen", height=36,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._send).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color=COLORS["success"])
        self.status_label.pack(padx=24)

    def _send(self):
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", "end").strip()
        if not to or not subject:
            self.status_label.configure(text="Empfaenger und Betreff sind Pflichtfelder.", text_color=COLORS["accent"])
            return

        try:
            from scripts.email_provider import get_provider
            provider = get_provider()
            result = provider.create_draft(to, subject, body)
            self.status_label.configure(text=f"Entwurf erstellt (ID: {result['id']})", text_color=COLORS["success"])
            if self._on_send:
                self._on_send(to, subject)
        except FileNotFoundError:
            self.status_label.configure(text="E-Mail-Provider nicht konfiguriert.", text_color=COLORS["accent"])
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color=COLORS["accent"])


# ---------------------------------------------------------------------------
# New Agent Dialog
# ---------------------------------------------------------------------------

class NewAgentDialog(ctk.CTkToplevel):
    """Dialog zum Erstellen eines neuen Agents."""

    def __init__(self, master, on_created=None):
        super().__init__(master)
        self.title("Neuer Agent")
        self.geometry("520x580")
        self.resizable(False, False)
        self.grab_set()
        self._on_created = on_created

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Agent erstellen",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(content, text="Name", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 2))
        self.name_entry = ctk.CTkEntry(content, height=36, placeholder_text="z.B. buchungs_agent",
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.name_entry.pack(fill="x")

        ctk.CTkLabel(content, text="Beschreibung", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.desc_entry = ctk.CTkEntry(content, height=36, placeholder_text="Kurze Beschreibung...",
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.desc_entry.pack(fill="x")

        ctk.CTkLabel(content, text="System-Prompt", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.prompt_text = ctk.CTkTextbox(content, height=100,
                                           fg_color=COLORS["bg_input"],
                                           border_color=COLORS["border"],
                                           border_width=1)
        self.prompt_text.insert("1.0", "Du bist ein hilfreicher Assistent.")
        self.prompt_text.pack(fill="x")

        ctk.CTkLabel(content, text="Tools", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self._tool_vars: dict[str, tk.BooleanVar] = {}
        tools_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_input"],
                                    corner_radius=8, border_width=1,
                                    border_color=COLORS["border"])
        tools_frame.pack(fill="x")

        from agents.base_agent import ALL_TOOLS
        for tool_name in ALL_TOOLS:
            var = tk.BooleanVar(value=False)
            self._tool_vars[tool_name] = var
            ctk.CTkCheckBox(tools_frame, text=tool_name, variable=var,
                           fg_color=COLORS["accent"],
                           hover_color=COLORS["accent_hover"]).pack(anchor="w", padx=12, pady=2)

        ctk.CTkLabel(content, text="Wissensdatenbank-Pfad (optional)",
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.knowledge_entry = ctk.CTkEntry(content, height=36,
                                             placeholder_text="z.B. KNOWLEDGE.md",
                                             fg_color=COLORS["bg_input"],
                                             border_color=COLORS["border"])
        self.knowledge_entry.pack(fill="x")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(btn_frame, text="Erstellen", height=36,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._create).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color=COLORS["success"])
        self.status_label.pack(padx=24)

    def _create(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        prompt = self.prompt_text.get("1.0", "end").strip()
        knowledge = self.knowledge_entry.get().strip() or None
        tools = [t for t, var in self._tool_vars.items() if var.get()]

        if not name:
            self.status_label.configure(text="Name ist erforderlich.", text_color=COLORS["accent"])
            return

        try:
            from scripts.agent_manager import create_agent
            cfg = create_agent(
                name=name,
                description=desc,
                system_prompt=prompt,
                tool_names=tools,
                knowledge_path=knowledge,
            )
            self.status_label.configure(text=f"Agent '{cfg['name']}' erstellt!", text_color=COLORS["success"])
            if self._on_created:
                self._on_created(cfg["name"])
            self.after(600, self.destroy)
        except ValueError as e:
            self.status_label.configure(text=str(e), text_color=COLORS["accent"])
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color=COLORS["accent"])


# ---------------------------------------------------------------------------
# Crawl Website Dialog
# ---------------------------------------------------------------------------

class CrawlWebsiteDialog(ctk.CTkToplevel):
    """Dialog zum Crawlen einer Hotel-Website."""

    def __init__(self, master, on_done=None):
        super().__init__(master)
        self.title("Website crawlen")
        self.geometry("520x400")
        self.resizable(False, False)
        self.grab_set()
        self._on_done = on_done
        self._crawling = False

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Website crawlen",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(content, text="Die Hotel-Website wird gecrawlt und das Wissen\n"
                                    "automatisch in die Wissensdatenbank uebernommen.",
                     text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w")

        ctk.CTkLabel(content, text="Website-URL:", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(16, 2))
        self.url_entry = ctk.CTkEntry(content, height=38,
                                       placeholder_text="https://www.mein-hotel.de",
                                       fg_color=COLORS["bg_input"],
                                       border_color=COLORS["border"])
        self.url_entry.pack(fill="x")

        ctk.CTkLabel(content, text="Max. Seiten:", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(12, 2))

        pages_frame = ctk.CTkFrame(content, fg_color="transparent")
        pages_frame.pack(fill="x")

        self.pages_slider = ctk.CTkSlider(pages_frame, from_=5, to=50, number_of_steps=9,
                                           progress_color=COLORS["accent"],
                                           button_color=COLORS["accent"],
                                           button_hover_color=COLORS["accent_hover"])
        self.pages_slider.set(30)
        self.pages_slider.pack(side="left", fill="x", expand=True)

        self.pages_label = ctk.CTkLabel(pages_frame, text="30",
                                         text_color=COLORS["text_primary"],
                                         font=ctk.CTkFont(size=12), width=30)
        self.pages_label.pack(side="right", padx=(8, 0))
        self.pages_slider.configure(command=lambda v: self.pages_label.configure(text=str(int(v))))

        # Progress
        self.progress_label = ctk.CTkLabel(content, text="", text_color=COLORS["text_muted"],
                                            font=ctk.CTkFont(size=11))
        self.progress_label.pack(anchor="w", pady=(12, 0))

        self.progress_bar = ctk.CTkProgressBar(content, progress_color=COLORS["accent"],
                                                fg_color=COLORS["bg_input"])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(4, 0))
        self.progress_bar.pack_forget()

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16)
        self.start_btn = ctk.CTkButton(btn_frame, text="Crawlen starten", height=36,
                                        fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                        command=self._start_crawl)
        self.start_btn.pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color=COLORS["success"])
        self.status_label.pack(padx=24)

    def _start_crawl(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="Bitte URL eingeben.", text_color=COLORS["accent"])
            return
        if not url.startswith("http"):
            url = "https://" + url
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)

        self._crawling = True
        self.start_btn.configure(state="disabled")
        self.progress_bar.pack(fill="x", pady=(4, 0))
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.progress_label.configure(text="Crawle Website...")

        max_pages = int(self.pages_slider.get())
        threading.Thread(target=self._run_crawl, args=(url, max_pages), daemon=True).start()

    def _run_crawl(self, url: str, max_pages: int):
        try:
            from scripts.web_scraper import crawl_site, analyze_website
            from scripts.documents import save_to_knowledge

            self.after(0, lambda: self.progress_label.configure(text=f"Crawle {url}..."))
            pages = crawl_site(url, max_pages=max_pages)

            if not pages:
                self.after(0, lambda: self._finish_crawl(
                    False, "Keine Seiten gefunden. Pruefe die URL."))
                return

            self.after(0, lambda: self.progress_label.configure(
                text=f"{len(pages)} Seiten gefunden. Analysiere..."))

            analysis = analyze_website(pages)
            save_to_knowledge(f"Website: {url}", analysis)

            self.after(0, lambda: self._finish_crawl(
                True, f"{len(pages)} Seiten gecrawlt und in Wissensdatenbank gespeichert."))

            if self._on_done:
                self.after(0, lambda: self._on_done(url, len(pages)))

        except Exception as e:
            self.after(0, lambda: self._finish_crawl(False, f"Fehler: {e}"))

    def _finish_crawl(self, success: bool, msg: str):
        self._crawling = False
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.start_btn.configure(state="normal")
        color = COLORS["success"] if success else COLORS["accent"]
        self.progress_label.configure(text=msg, text_color=color)


# ---------------------------------------------------------------------------
# Automations Dialog
# ---------------------------------------------------------------------------

class AutomationsDialog(ctk.CTkToplevel):
    """Dialog zur Verwaltung von Automationen."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Automationen")
        self.geometry("720x560")
        self.resizable(True, True)
        self.grab_set()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Automationen",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkButton(toolbar, text="+ Neue Automation", width=160, height=32,
                      fg_color=COLORS["purple"], hover_color=COLORS["purple_hover"],
                      command=self._open_new_dialog).pack(side="left")
        ctk.CTkButton(toolbar, text="Ausfuehren", width=100, height=32,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._run_selected).pack(side="left", padx=8)
        ctk.CTkButton(toolbar, text="Aktivieren/Deaktivieren", width=160, height=32,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self._toggle_selected).pack(side="left")
        ctk.CTkButton(toolbar, text="Loeschen", width=80, height=32,
                      fg_color="#dc2626", hover_color="#b91c1c",
                      command=self._delete_selected).pack(side="right")

        # Liste
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_card"],
                                                  corner_radius=8)
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=8)
        self.list_frame.grid_columnconfigure(0, weight=0)
        self.list_frame.grid_columnconfigure(1, weight=1)
        self.list_frame.grid_columnconfigure(2, weight=0)
        self.list_frame.grid_columnconfigure(3, weight=0)
        self.list_frame.grid_columnconfigure(4, weight=0)

        self._selected_name = tk.StringVar(value="")
        self._radio_buttons: list[ctk.CTkRadioButton] = []

        # Log
        ctk.CTkLabel(self, text="Letzte Ausfuehrungen:", font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"]).pack(padx=16, anchor="w")
        self.log_text = ctk.CTkTextbox(self, height=90, font=ctk.CTkFont(size=11),
                                        fg_color=COLORS["bg_card"], border_width=1,
                                        border_color=COLORS["border"])
        self.log_text.pack(fill="x", padx=16, pady=(0, 16))
        self.log_text.configure(state="disabled")

        self._refresh_log()

    def _refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self._radio_buttons.clear()

        from scripts.automation_manager import list_automations
        autos = list_automations()

        # Header
        for col, text in enumerate(["", "Name", "Aktion", "Trigger", "Status"]):
            ctk.CTkLabel(self.list_frame, text=text,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COLORS["text_muted"]).grid(row=0, column=col, sticky="w", padx=8, pady=4)

        if not autos:
            ctk.CTkLabel(self.list_frame, text="Keine Automationen vorhanden.",
                         text_color=COLORS["text_muted"]).grid(row=1, column=0, columnspan=5, padx=8, pady=12)
            return

        for i, a in enumerate(autos, start=1):
            rb = ctk.CTkRadioButton(self.list_frame, text="", variable=self._selected_name,
                                     value=a["name"], width=20,
                                     fg_color=COLORS["accent"],
                                     hover_color=COLORS["accent_hover"])
            rb.grid(row=i, column=0, padx=8, pady=3)
            self._radio_buttons.append(rb)

            ctk.CTkLabel(self.list_frame, text=a["name"],
                         font=ctk.CTkFont(size=12),
                         text_color=COLORS["text_primary"]).grid(row=i, column=1, sticky="w", padx=8, pady=3)

            ctk.CTkLabel(self.list_frame, text=a["action"],
                         text_color=COLORS["text_secondary"]).grid(row=i, column=2, sticky="w", padx=8, pady=3)

            trigger = a.get("trigger", {})
            t_type = trigger.get("type", "?")
            if t_type == "schedule":
                days = trigger.get("schedule_days", [])
                t_info = f"{', '.join(days) or 'taeglich'} {trigger.get('schedule_time', '')}"
            elif t_type == "event":
                t_info = trigger.get("event", "?")
            else:
                t_info = "manuell"
            ctk.CTkLabel(self.list_frame, text=t_info,
                         text_color=COLORS["text_secondary"]).grid(row=i, column=3, sticky="w", padx=8, pady=3)

            status_text = "aktiv" if a.get("enabled") else "inaktiv"
            status_color = COLORS["success"] if a.get("enabled") else COLORS["text_muted"]
            ctk.CTkLabel(self.list_frame, text=status_text,
                         text_color=status_color,
                         font=ctk.CTkFont(size=11, weight="bold")).grid(row=i, column=4, sticky="w", padx=8, pady=3)

    def _refresh_log(self):
        from scripts.automation_manager import get_run_log
        log = get_run_log(limit=10)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        if not log:
            self.log_text.insert("1.0", "Noch keine Ausfuehrungen.")
        else:
            for entry in log:
                ts = entry.get("timestamp", "")[:16]
                name = entry.get("automation", "?")
                status = entry.get("status", "?")
                msg = entry.get("message", "")[:60]
                self.log_text.insert("end", f"{ts}  {name}  [{status}]  {msg}\n")
        self.log_text.configure(state="disabled")

    def _get_selected(self) -> str | None:
        name = self._selected_name.get()
        return name if name else None

    def _run_selected(self):
        name = self._get_selected()
        if not name:
            return
        from scripts.automation_manager import run_automation
        import threading

        def _run():
            result = run_automation(name)
            self.after(0, lambda: self._on_run_done(name, result))

        threading.Thread(target=_run, daemon=True).start()

    def _on_run_done(self, name: str, result: str):
        self._refresh_log()
        self._refresh_list()

    def _toggle_selected(self):
        name = self._get_selected()
        if not name:
            return
        from scripts.automation_manager import get_automation, enable_automation, disable_automation
        auto = get_automation(name)
        if auto and auto.get("enabled"):
            disable_automation(name)
        else:
            enable_automation(name)
        self._refresh_list()

    def _delete_selected(self):
        name = self._get_selected()
        if not name:
            return
        from scripts.automation_manager import delete_automation
        delete_automation(name)
        self._selected_name.set("")
        self._refresh_list()

    def _open_new_dialog(self):
        NewAutomationDialog(self, on_created=lambda: (self._refresh_list(), self._refresh_log()))


class NewAutomationDialog(ctk.CTkToplevel):
    """Dialog zum Erstellen einer neuen Automation."""

    def __init__(self, master, on_created=None):
        super().__init__(master)
        self.title("Neue Automation")
        self.geometry("500x560")
        self.resizable(False, False)
        self.grab_set()
        self._on_created = on_created

        from scripts.automation_manager import AVAILABLE_ACTIONS, TRIGGER_TYPES, AVAILABLE_EVENTS
        self._actions = AVAILABLE_ACTIONS
        self._events = AVAILABLE_EVENTS

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Neue Automation",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=16, padx=24, anchor="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(content, text="Name", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 2))
        self.name_entry = ctk.CTkEntry(content, height=36, placeholder_text="z.B. morgen_mails",
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.name_entry.pack(fill="x")

        ctk.CTkLabel(content, text="Beschreibung", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.desc_entry = ctk.CTkEntry(content, height=36, placeholder_text="Kurze Beschreibung...",
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"])
        self.desc_entry.pack(fill="x")

        ctk.CTkLabel(content, text="Aktion", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        action_names = list(self._actions.keys())
        self.action_menu = ctk.CTkOptionMenu(content, values=action_names,
                                              fg_color=COLORS["bg_input"],
                                              button_color=COLORS["accent"],
                                              button_hover_color=COLORS["accent_hover"])
        self.action_menu.pack(fill="x")

        ctk.CTkLabel(content, text="Trigger-Typ", text_color=COLORS["text_secondary"],
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 2))
        self.trigger_menu = ctk.CTkOptionMenu(
            content, values=["schedule", "event", "manual"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            command=self._on_trigger_changed,
        )
        self.trigger_menu.pack(fill="x")

        # Schedule-Felder
        self.schedule_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.schedule_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(self.schedule_frame, text="Uhrzeit (HH:MM):",
                     text_color=COLORS["text_secondary"]).pack(side="left")
        self.time_entry = ctk.CTkEntry(self.schedule_frame, width=80, height=32,
                                        fg_color=COLORS["bg_input"],
                                        border_color=COLORS["border"])
        self.time_entry.insert(0, "08:00")
        self.time_entry.pack(side="left", padx=8)

        self.days_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.days_frame.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(self.days_frame, text="Tage (leer=taeglich):",
                     text_color=COLORS["text_secondary"]).pack(anchor="w")
        self._day_vars: dict[str, tk.BooleanVar] = {}
        days_row = ctk.CTkFrame(self.days_frame, fg_color="transparent")
        days_row.pack(anchor="w")
        for day in ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]:
            full = {"Mo": "monday", "Di": "tuesday", "Mi": "wednesday", "Do": "thursday",
                    "Fr": "friday", "Sa": "saturday", "So": "sunday"}[day]
            var = tk.BooleanVar(value=False)
            self._day_vars[full] = var
            ctk.CTkCheckBox(days_row, text=day, variable=var, width=50,
                           fg_color=COLORS["accent"],
                           hover_color=COLORS["accent_hover"]).pack(side="left", padx=2)

        # Event-Feld
        self.event_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.event_frame.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(self.event_frame, text="Event:",
                     text_color=COLORS["text_secondary"]).pack(anchor="w")
        event_names = list(self._events.keys())
        self.event_menu = ctk.CTkOptionMenu(self.event_frame, values=event_names or ["(keine)"],
                                             width=300,
                                             fg_color=COLORS["bg_input"],
                                             button_color=COLORS["accent"],
                                             button_hover_color=COLORS["accent_hover"])
        self.event_menu.pack(anchor="w")

        # Initial: schedule sichtbar, event versteckt
        self._on_trigger_changed("schedule")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(btn_frame, text="Erstellen", height=36,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._create).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color=COLORS["success"])
        self.status_label.pack(padx=24)

    def _on_trigger_changed(self, value: str):
        if value == "schedule":
            self.schedule_frame.pack(fill="x", pady=(8, 0))
            self.days_frame.pack(fill="x", pady=(6, 0))
            self.event_frame.pack_forget()
        elif value == "event":
            self.schedule_frame.pack_forget()
            self.days_frame.pack_forget()
            self.event_frame.pack(fill="x", pady=(6, 0))
        else:
            self.schedule_frame.pack_forget()
            self.days_frame.pack_forget()
            self.event_frame.pack_forget()

    def _create(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        action = self.action_menu.get()
        trigger_type = self.trigger_menu.get()

        if not name:
            self.status_label.configure(text="Name ist erforderlich.", text_color=COLORS["accent"])
            return

        schedule_time = None
        schedule_days = []
        event_name = None

        if trigger_type == "schedule":
            schedule_time = self.time_entry.get().strip() or "08:00"
            schedule_days = [d for d, var in self._day_vars.items() if var.get()]
        elif trigger_type == "event":
            event_name = self.event_menu.get()

        try:
            from scripts.automation_manager import create_automation
            cfg = create_automation(
                name=name,
                description=desc,
                action=action,
                trigger_type=trigger_type,
                schedule_time=schedule_time,
                schedule_days=schedule_days,
                event_name=event_name,
            )
            self.status_label.configure(text=f"Automation '{cfg['name']}' erstellt!", text_color=COLORS["success"])
            if self._on_created:
                self._on_created()
            self.after(600, self.destroy)
        except ValueError as e:
            self.status_label.configure(text=str(e), text_color=COLORS["accent"])
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color=COLORS["accent"])


# ---------------------------------------------------------------------------
# Setup Wizard (Erst-Einrichtung)
# ---------------------------------------------------------------------------

class SetupWizardDialog(ctk.CTkToplevel):
    """Erst-Einrichtungs-Assistent fuer HotelAgent."""

    def __init__(self, master, on_complete=None):
        super().__init__(master)
        self.title("HotelAgent — Einrichtung")
        self.geometry("580x560")
        self.resizable(False, False)
        self.grab_set()
        self._on_complete = on_complete
        self._page = 0

        self._build_page_0()

    # --- Seite 0: Willkommen ---

    def _build_page_0(self):
        self._clear()

        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Willkommen bei HotelAgent!",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=(20, 4), padx=30, anchor="w")
        ctk.CTkLabel(header, text="Lass uns die wichtigsten Einstellungen vornehmen.",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(padx=30, anchor="w")

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(frame, text="Schritt 1: OpenRouter API-Key",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(frame, text="Der API-Key wird fuer die KI-Funktionen benoetigt.\n"
                                  "Erstelle einen unter openrouter.ai/keys",
                     text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=11)).pack(anchor="w")

        self.api_entry = ctk.CTkEntry(frame, height=38, placeholder_text="sk-or-...",
                                       fg_color=COLORS["bg_input"],
                                       border_color=COLORS["border"])
        self.api_entry.pack(fill="x", pady=(8, 0))

        # Vorhandenen Key laden
        import os
        existing_key = os.getenv("OPENROUTER_API_KEY", "")
        if existing_key:
            self.api_entry.insert(0, existing_key)
            ctk.CTkLabel(frame, text="API-Key bereits vorhanden",
                         text_color=COLORS["success"], font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(frame, text="Schritt 2: E-Mail-Provider",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", pady=(20, 4))
        ctk.CTkLabel(frame, text="Waehle deinen E-Mail-Anbieter fuer die automatische\n"
                                  "E-Mail-Verarbeitung (kann auch spaeter eingerichtet werden).",
                     text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=11)).pack(anchor="w")

        from scripts.email_provider import KNOWN_PROVIDERS
        provider_names = ["Spaeter einrichten", "Gmail (OAuth2 API)"]
        self._provider_keys = {"Spaeter einrichten": None, "Gmail (OAuth2 API)": "gmail_oauth"}
        for key, val in KNOWN_PROVIDERS.items():
            provider_names.append(val["name"])
            self._provider_keys[val["name"]] = key

        self.provider_menu = ctk.CTkOptionMenu(frame, values=provider_names,
                                                fg_color=COLORS["bg_input"],
                                                button_color=COLORS["accent"],
                                                button_hover_color=COLORS["accent_hover"])
        self.provider_menu.set("Spaeter einrichten")
        self.provider_menu.pack(fill="x", pady=(8, 0))

        # IMAP-Felder (versteckt bis benoetigt)
        self.imap_frame = ctk.CTkFrame(frame, fg_color="transparent")

        ctk.CTkLabel(self.imap_frame, text="E-Mail-Adresse:",
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(8, 2))
        self.email_entry = ctk.CTkEntry(self.imap_frame, height=36,
                                         placeholder_text="user@example.com",
                                         fg_color=COLORS["bg_input"],
                                         border_color=COLORS["border"])
        self.email_entry.pack(fill="x")

        ctk.CTkLabel(self.imap_frame, text="Passwort / App-Passwort:",
                     text_color=COLORS["text_secondary"]).pack(anchor="w", pady=(6, 2))
        self.pass_entry = ctk.CTkEntry(self.imap_frame, height=36,
                                        placeholder_text="Passwort", show="*",
                                        fg_color=COLORS["bg_input"],
                                        border_color=COLORS["border"])
        self.pass_entry.pack(fill="x")

        self.provider_menu.configure(command=self._on_provider_changed)

        # Status
        self.status_label = ctk.CTkLabel(self, text="", text_color=COLORS["success"],
                                          font=ctk.CTkFont(size=12))
        self.status_label.pack(padx=30)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Ueberspringen", height=36,
                      fg_color=COLORS["border"], hover_color=COLORS["text_muted"],
                      command=self._skip).pack(side="left")
        ctk.CTkButton(btn_frame, text="Speichern & Starten", height=36,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._save).pack(side="right")

    def _on_provider_changed(self, name: str):
        key = self._provider_keys.get(name)
        if key and key != "gmail_oauth":
            self.imap_frame.pack(fill="x", pady=(8, 0))
        else:
            self.imap_frame.pack_forget()

    def _save(self):
        import os
        from pathlib import Path

        # API-Key speichern
        api_key = self.api_entry.get().strip()
        if api_key:
            env_path = Path(__file__).parent / ".env"
            if env_path.is_file():
                content = env_path.read_text(encoding="utf-8")
                import re
                if "OPENROUTER_API_KEY" in content:
                    content = re.sub(r"OPENROUTER_API_KEY=.*",
                                     f"OPENROUTER_API_KEY={api_key}", content)
                else:
                    content += f"\nOPENROUTER_API_KEY={api_key}\n"
                env_path.write_text(content, encoding="utf-8")
            else:
                env_path.write_text(f"OPENROUTER_API_KEY={api_key}\n", encoding="utf-8")
            os.environ["OPENROUTER_API_KEY"] = api_key
            self.status_label.configure(text="API-Key gespeichert.", text_color=COLORS["success"])

        # E-Mail-Provider speichern
        provider_name = self.provider_menu.get()
        provider_key = self._provider_keys.get(provider_name)

        if provider_key:
            from scripts.email_provider import setup_imap_provider, setup_gmail_oauth

            if provider_key == "gmail_oauth":
                setup_gmail_oauth()
            else:
                username = self.email_entry.get().strip()
                password = self.pass_entry.get().strip()
                if username and password:
                    setup_imap_provider(preset_key=provider_key,
                                       username=username, password=password)
                    self.status_label.configure(text="E-Mail-Provider gespeichert!", text_color=COLORS["success"])

        # Fertig-Marker setzen
        self._mark_setup_done()

        if self._on_complete:
            self._on_complete()
        self.after(500, self.destroy)

    def _skip(self):
        self._mark_setup_done()
        if self._on_complete:
            self._on_complete()
        self.destroy()

    @staticmethod
    def _mark_setup_done():
        """Marker-Datei erstellen damit der Wizard nicht erneut erscheint."""
        marker = Path(__file__).parent / "data" / ".setup_complete"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("1", encoding="utf-8")

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    @staticmethod
    def is_first_run() -> bool:
        """Pruefen ob die Erst-Einrichtung noch nicht durchgefuehrt wurde."""
        marker = Path(__file__).parent / "data" / ".setup_complete"
        return not marker.is_file()


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class HotelAgentGUI(ctk.CTk):
    """Hauptfenster der HotelAgent GUI."""

    def __init__(self):
        super().__init__()

        self.title("HotelAgent")
        self.geometry("1000x680")
        self.minsize(800, 520)

        ctk.set_appearance_mode("Dark")

        # State
        self._agent = None
        self._conversation_id = None
        self._current_agent_name = "hotel_agent"
        self._voice_recording = False
        self._voice_thread: threading.Thread | None = None
        self._settings_dialog = None
        self._gmail_dialog = None
        self._new_agent_dialog = None
        self._automations_dialog = None
        self._email_setup_dialog = None
        self._crawl_dialog = None
        self._setup_wizard = None

        self._build_ui()
        self._init_agent()

        # Erst-Einrichtung pruefen
        if SetupWizardDialog.is_first_run():
            self.after(500, self._show_setup_wizard)

    # -----------------------------------------------------------------------
    # UI Build
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # Grid: sidebar | main
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -- Sidebar --
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0,
                                     fg_color=COLORS["bg_sidebar"],
                                     border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Logo-Bereich
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        logo_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(20, 4))
        logo_frame.grid_propagate(False)

        ctk.CTkLabel(logo_frame, text="HotelAgent",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="KI-Hotelassistent",
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"]).pack(anchor="w")

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=8)

        # Agent-Sektion
        agent_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        agent_section.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 4))

        ctk.CTkLabel(agent_section, text="AGENT",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 4))

        self._agent_names = self._get_agent_choices()
        self.agent_selector = ctk.CTkOptionMenu(
            agent_section, values=self._agent_names,
            command=self._on_agent_changed,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            height=30,
        )
        self.agent_selector.set(self._agent_names[0] if self._agent_names else "hotel_agent")
        self.agent_selector.pack(fill="x")

        self.new_agent_btn = ctk.CTkButton(
            agent_section, text="+ Neuer Agent", height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color=COLORS["bg_card"],
            text_color=COLORS["purple"], border_width=1,
            border_color=COLORS["purple"],
            command=self._open_new_agent_dialog)
        self.new_agent_btn.pack(fill="x", pady=(4, 0))

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1).grid(
            row=3, column=0, sticky="ew", padx=16, pady=8)

        # Aktionen-Sektion
        actions_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        actions_section.grid(row=4, column=0, sticky="ew", padx=16)

        ctk.CTkLabel(actions_section, text="AKTIONEN",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 6))

        self.new_chat_btn = ctk.CTkButton(
            actions_section, text="Neuer Chat", height=32,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12),
            command=self._new_chat)
        self.new_chat_btn.pack(fill="x", pady=(0, 4))

        self.upload_btn = ctk.CTkButton(
            actions_section, text="Datei hochladen", height=32,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            command=self._upload_file)
        self.upload_btn.pack(fill="x", pady=(0, 4))

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1).grid(
            row=5, column=0, sticky="ew", padx=16, pady=8)

        # E-Mail-Sektion
        email_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        email_section.grid(row=6, column=0, sticky="ew", padx=16)

        ctk.CTkLabel(email_section, text="E-MAIL",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 6))

        self.email_setup_btn = ctk.CTkButton(
            email_section, text="Provider einrichten", height=30,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._open_email_setup_dialog)
        self.email_setup_btn.pack(fill="x", pady=(0, 3))

        self.gmail_btn = ctk.CTkButton(
            email_section, text="Entwurf erstellen", height=30,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._open_gmail_dialog)
        self.gmail_btn.pack(fill="x", pady=(0, 3))

        self.check_mails_btn = ctk.CTkButton(
            email_section, text="Posteingang pruefen", height=30,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._check_mails)
        self.check_mails_btn.pack(fill="x")

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=COLORS["border"], height=1).grid(
            row=7, column=0, sticky="ew", padx=16, pady=8)

        # Tools-Sektion
        tools_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        tools_section.grid(row=8, column=0, sticky="ew", padx=16)

        ctk.CTkLabel(tools_section, text="TOOLS",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 6))

        self.crawl_btn = ctk.CTkButton(
            tools_section, text="Website crawlen", height=30,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._open_crawl_dialog)
        self.crawl_btn.pack(fill="x", pady=(0, 3))

        self.automations_btn = ctk.CTkButton(
            tools_section, text="Automationen", height=30,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._open_automations_dialog)
        self.automations_btn.pack(fill="x", pady=(0, 3))

        self.settings_btn = ctk.CTkButton(
            tools_section, text="Einstellungen", height=30,
            fg_color=COLORS["bg_card"], hover_color=COLORS["border"],
            font=ctk.CTkFont(size=11),
            command=self._open_settings)
        self.settings_btn.pack(fill="x")

        # Spacer
        self.sidebar.grid_rowconfigure(9, weight=1)

        # Footer: Theme toggle
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=10, column=0, sticky="ew", padx=16, pady=(0, 16))

        self.theme_switch = ctk.CTkSwitch(
            footer, text="Dark Mode",
            font=ctk.CTkFont(size=11),
            progress_color=COLORS["accent"],
            button_color=COLORS["text_secondary"],
            button_hover_color=COLORS["text_primary"],
            command=self._toggle_theme, onvalue=1, offvalue=0)
        self.theme_switch.select()
        self.theme_switch.pack(anchor="w")

        # -- Main area --
        main_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        main_frame.grid(row=0, column=1, sticky="nswe")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Chat-Header
        chat_header = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"],
                                    corner_radius=0, height=50)
        chat_header.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        chat_header.grid_propagate(False)
        chat_header.grid_columnconfigure(0, weight=1)

        self._chat_title = ctk.CTkLabel(
            chat_header, text="Chat mit HotelAgent",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"])
        self._chat_title.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        # Chat area (scrollable)
        self.chat_frame = ctk.CTkScrollableFrame(main_frame,
                                                  fg_color=COLORS["bg_dark"],
                                                  scrollbar_button_color=COLORS["border"],
                                                  scrollbar_button_hover_color=COLORS["text_muted"])
        self.chat_frame.grid(row=1, column=0, sticky="nswe", padx=12, pady=(56, 0))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Input-Bereich
        input_container = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"],
                                        corner_radius=12, height=60)
        input_container.grid(row=2, column=0, sticky="we", padx=12, pady=12)
        input_container.grid_columnconfigure(0, weight=1)

        self.msg_entry = ctk.CTkEntry(
            input_container, placeholder_text="Nachricht eingeben...",
            height=42, font=ctk.CTkFont(size=13),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            border_width=1,
            corner_radius=10)
        self.msg_entry.grid(row=0, column=0, sticky="we", padx=(12, 6), pady=9)
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(
            input_container, text="Senden", width=80, height=38,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8,
            command=self._send_message)
        self.send_btn.grid(row=0, column=1, padx=(0, 6), pady=9)

        self.voice_btn = ctk.CTkButton(
            input_container, text="Mikrofon", width=90, height=38,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self._toggle_voice)
        self.voice_btn.grid(row=0, column=2, padx=(0, 12), pady=9)

        # Status-Leiste
        status_bar = ctk.CTkFrame(main_frame, fg_color="transparent", height=28)
        status_bar.grid(row=3, column=0, sticky="we", padx=16, pady=(0, 4))
        status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            status_bar, text="Bereit",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"], anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w")

        # Disclaimer
        ctk.CTkLabel(
            status_bar,
            text="KI-generierte Antworten koennen fehlerhaft sein. Keine Haftung. Nutzung auf eigene Verantwortung.",
            font=ctk.CTkFont(size=9),
            text_color=COLORS["text_muted"], anchor="e"
        ).grid(row=0, column=1, sticky="e")

    # -----------------------------------------------------------------------
    # Agent
    # -----------------------------------------------------------------------

    def _init_agent(self):
        """Agent initialisieren (laedt den aktuell ausgewaehlten Agent)."""
        try:
            from scripts.agent_manager import load_agent
            name = self._current_agent_name
            self._conversation_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._agent = load_agent(name, conversation_id=self._conversation_id)
            self._set_status(f"Agent '{name}' bereit")
            self._chat_title.configure(text=f"Chat mit {name.replace('_', ' ').title()}")
        except Exception as e:
            self._set_status(f"Agent-Fehler: {e}")
            self._agent = None

    # -----------------------------------------------------------------------
    # Chat
    # -----------------------------------------------------------------------

    def _add_bubble(self, role: str, text: str):
        bubble = ChatBubble(self.chat_frame, role=role, text=text)
        bubble.pack(fill="x", pady=2)
        # Auto-scroll
        self.chat_frame.after(50, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def _send_message(self):
        text = self.msg_entry.get().strip()
        if not text or self._agent is None:
            return

        self.msg_entry.delete(0, "end")
        self._add_bubble("user", text)
        self._set_status("Agent denkt nach...")
        self.send_btn.configure(state="disabled")
        self.voice_btn.configure(state="disabled")

        thread = threading.Thread(target=self._agent_reply, args=(text,), daemon=True)
        thread.start()

    def _agent_reply(self, user_text: str):
        """Agent-Antwort in separatem Thread holen."""
        try:
            response = self._agent.send(user_text, stream=False)
        except Exception as e:
            response = f"Fehler: {e}"

        # Zurueck im Main-Thread
        self.after(0, self._handle_response, response)

    def _handle_response(self, response: str):
        self._add_bubble("assistant", response)
        self.send_btn.configure(state="normal")
        self.voice_btn.configure(state="normal")
        self._set_status("Bereit")

        # Konversation speichern
        try:
            from scripts.memory import save_conversation
            save_conversation(self._conversation_id, self._agent.history)
        except Exception:
            pass

    def _new_chat(self):
        """Neuen Chat starten."""
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self._init_agent()

    # -----------------------------------------------------------------------
    # Voice
    # -----------------------------------------------------------------------

    def _toggle_voice(self):
        if self._voice_recording:
            self._stop_voice()
        else:
            self._start_voice()

    def _start_voice(self):
        if self._agent is None:
            return
        self._voice_recording = True
        self.voice_btn.configure(text="Stoppen", fg_color="#dc2626", hover_color="#b91c1c")
        self._set_status("Aufnahme laeuft...")

        self._voice_frames = []
        try:
            import sounddevice as sd
            import numpy as np
            self._voice_stream = sd.InputStream(
                samplerate=16000, channels=1, dtype="float32",
                callback=self._voice_callback,
            )
            self._voice_stream.start()
        except Exception as e:
            self._set_status(f"Mikrofon-Fehler: {e}")
            self._voice_recording = False
            self.voice_btn.configure(text="Mikrofon", fg_color="#16a34a", hover_color="#15803d")

    def _voice_callback(self, indata, frames, time_info, status):
        import numpy as np
        if self._voice_recording:
            self._voice_frames.append(indata.copy())

    def _stop_voice(self):
        import numpy as np
        self._voice_recording = False
        self.voice_btn.configure(text="Mikrofon", fg_color="#16a34a", hover_color="#15803d")

        try:
            self._voice_stream.stop()
            self._voice_stream.close()
        except Exception:
            pass

        if not self._voice_frames:
            self._set_status("Keine Aufnahme erkannt")
            return

        audio = np.concatenate(self._voice_frames, axis=0)
        if len(audio) < 16000 * 0.3:
            self._set_status("Aufnahme zu kurz")
            return

        self._set_status("Transkribiere...")
        self.voice_btn.configure(state="disabled")
        thread = threading.Thread(target=self._transcribe_and_send, args=(audio,), daemon=True)
        thread.start()

    def _transcribe_and_send(self, audio):
        """Audio transkribieren und an Agent senden."""
        try:
            from scripts.voice import SpeechToText, TextToSpeech
            stt = SpeechToText()
            user_text = stt.transcribe(audio)
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Transkription fehlgeschlagen: {e}"))
            self.after(0, lambda: self.voice_btn.configure(state="normal"))
            return

        self.after(0, self._add_bubble, "user", user_text)
        self.after(0, lambda: self._set_status("Agent denkt nach..."))

        try:
            response = self._agent.send(user_text, stream=False)
        except Exception as e:
            response = f"Fehler: {e}"

        self.after(0, self._handle_response, response)
        self.after(0, lambda: self.voice_btn.configure(state="normal"))

        # TTS-Antwort vorlesen
        try:
            from scripts.voice import TextToSpeech
            tts = TextToSpeech()
            tts.speak(response)
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # File Upload
    # -----------------------------------------------------------------------

    def _upload_file(self):
        filetypes = [
            ("Alle unterstuetzten", "*.pdf *.docx *.doc *.txt *.csv *.md"),
            ("PDF", "*.pdf"),
            ("Word", "*.docx *.doc"),
            ("Text", "*.txt *.md"),
            ("CSV", "*.csv"),
        ]
        path = filedialog.askopenfilename(title="Datei auswaehlen", filetypes=filetypes)
        if not path:
            return

        self._set_status(f"Lade '{Path(path).name}' hoch...")
        self.upload_btn.configure(state="disabled")
        thread = threading.Thread(target=self._process_upload, args=(path,), daemon=True)
        thread.start()

    def _process_upload(self, path: str):
        try:
            from scripts.documents import upload_file, analyze_document, save_to_knowledge
            dest = upload_file(path)
            analysis = analyze_document(dest)
            save_to_knowledge(Path(path).name, analysis)

            self.after(0, self._add_bubble, "assistant",
                       f"Datei '{Path(path).name}' analysiert und in Wissensdatenbank gespeichert.\n\n{analysis[:500]}...")
            self.after(0, lambda: self._set_status("Upload abgeschlossen"))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"Upload-Fehler: {e}"))

        self.after(0, lambda: self.upload_btn.configure(state="normal"))

    # -----------------------------------------------------------------------
    # Check Mails
    # -----------------------------------------------------------------------

    def _check_mails(self):
        self._set_status("Pruefe E-Mails...")
        self.check_mails_btn.configure(state="disabled")
        self._add_bubble("assistant", "Pruefe Posteingang auf Gaesteanfragen...")
        thread = threading.Thread(target=self._run_check_mails, daemon=True)
        thread.start()

    def _run_check_mails(self):
        try:
            from scripts.email_processor import process_inbox
            results = process_inbox()
            created = sum(1 for r in results if r["status"] == "entwurf_erstellt")
            skipped = len(results) - created

            if not results:
                msg = "Keine ungelesenen E-Mails gefunden."
            else:
                lines = []
                for r in results:
                    if r["status"] == "entwurf_erstellt":
                        lines.append(f"  Entwurf: {r['subject'][:40]}")
                    else:
                        lines.append(f"  Uebersprungen: {r['subject'][:40]} ({r.get('reason', '')})")
                msg = f"{created} Entwurf/e erstellt, {skipped} uebersprungen:\n" + "\n".join(lines)

            self.after(0, self._add_bubble, "assistant", msg)
            self.after(0, lambda: self._set_status("E-Mail-Pruefung abgeschlossen"))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"E-Mail-Fehler: {e}"))
            self.after(0, self._add_bubble, "assistant", f"Fehler bei E-Mail-Pruefung: {e}")

        self.after(0, lambda: self.check_mails_btn.configure(state="normal"))

    # -----------------------------------------------------------------------
    # Email Setup
    # -----------------------------------------------------------------------

    def _open_email_setup_dialog(self):
        if self._email_setup_dialog is not None and self._email_setup_dialog.winfo_exists():
            self._email_setup_dialog.focus()
            return
        self._email_setup_dialog = EmailSetupDialog(self, on_saved=self._on_email_setup_saved)

    def _on_email_setup_saved(self):
        self._add_bubble("assistant", "E-Mail-Provider wurde konfiguriert.")

    # -----------------------------------------------------------------------
    # Email Draft
    # -----------------------------------------------------------------------

    def _open_gmail_dialog(self):
        if self._gmail_dialog is not None and self._gmail_dialog.winfo_exists():
            self._gmail_dialog.focus()
            return
        self._gmail_dialog = GmailDraftDialog(self, on_send=self._on_gmail_sent)

    def _on_gmail_sent(self, to: str, subject: str):
        self._add_bubble("assistant", f"E-Mail-Entwurf erstellt an {to}: '{subject}'")

    # -----------------------------------------------------------------------
    # Settings
    # -----------------------------------------------------------------------

    def _open_settings(self):
        if self._settings_dialog is not None and self._settings_dialog.winfo_exists():
            self._settings_dialog.focus()
            return
        self._settings_dialog = SettingsDialog(self, on_save=self._on_settings_saved)

    def _on_settings_saved(self, cfg: dict):
        self._set_status("Einstellungen gespeichert — neuer Chat empfohlen")

    # -----------------------------------------------------------------------
    # Theme
    # -----------------------------------------------------------------------

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() else "Light"
        ctk.set_appearance_mode(mode)

    # -----------------------------------------------------------------------
    # Agent Management
    # -----------------------------------------------------------------------

    def _get_agent_choices(self) -> list[str]:
        """Agent-Namen fuer Dropdown zusammenstellen."""
        try:
            from scripts.agent_manager import list_agents
            names = ["hotel_agent"]
            for a in list_agents():
                names.append(a["name"])
            return names
        except Exception:
            return ["hotel_agent"]

    def _refresh_agent_selector(self):
        """Agent-Dropdown aktualisieren."""
        self._agent_names = self._get_agent_choices()
        self.agent_selector.configure(values=self._agent_names)

    def _on_agent_changed(self, name: str):
        """Agent gewechselt — neuen Chat starten."""
        self._current_agent_name = name
        self._new_chat()

    def _open_new_agent_dialog(self):
        if self._new_agent_dialog is not None and self._new_agent_dialog.winfo_exists():
            self._new_agent_dialog.focus()
            return
        self._new_agent_dialog = NewAgentDialog(self, on_created=self._on_agent_created)

    def _on_agent_created(self, agent_name: str):
        """Callback wenn ein neuer Agent erstellt wurde."""
        self._refresh_agent_selector()
        self.agent_selector.set(agent_name)
        self._current_agent_name = agent_name
        self._new_chat()
        self._add_bubble("assistant", f"Agent '{agent_name}' erstellt und aktiviert.")

    # -----------------------------------------------------------------------
    # Automations
    # -----------------------------------------------------------------------

    def _open_automations_dialog(self):
        if self._automations_dialog is not None and self._automations_dialog.winfo_exists():
            self._automations_dialog.focus()
            return
        self._automations_dialog = AutomationsDialog(self)

    # -----------------------------------------------------------------------
    # Crawl Website
    # -----------------------------------------------------------------------

    def _open_crawl_dialog(self):
        if self._crawl_dialog is not None and self._crawl_dialog.winfo_exists():
            self._crawl_dialog.focus()
            return
        self._crawl_dialog = CrawlWebsiteDialog(self, on_done=self._on_crawl_done)

    def _on_crawl_done(self, url: str, page_count: int):
        self._add_bubble("assistant",
                         f"Website '{url}' erfolgreich gecrawlt ({page_count} Seiten). "
                         f"Wissen wurde in die Wissensdatenbank uebernommen.")

    # -----------------------------------------------------------------------
    # Setup Wizard
    # -----------------------------------------------------------------------

    def _show_setup_wizard(self):
        if self._setup_wizard is not None and self._setup_wizard.winfo_exists():
            self._setup_wizard.focus()
            return
        self._setup_wizard = SetupWizardDialog(self, on_complete=self._on_setup_complete)

    def _on_setup_complete(self):
        self._add_bubble("assistant", "Einrichtung abgeschlossen! Du kannst jetzt loslegen.")
        self._init_agent()

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _set_status(self, text: str):
        self.status_label.configure(text=text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def launch_gui():
    """GUI starten (wird von cli.py aufgerufen)."""
    app = HotelAgentGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
