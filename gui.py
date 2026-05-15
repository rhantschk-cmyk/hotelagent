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

ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Chat-Bubble Frame
# ---------------------------------------------------------------------------

class ChatBubble(ctk.CTkFrame):
    """Einzelne Chat-Nachricht (User oder Agent)."""

    def __init__(self, master, role: str, text: str, **kwargs):
        is_user = role == "user"
        fg = "#2563eb" if is_user else "#374151"
        text_color = "#ffffff"
        anchor = "e" if is_user else "w"

        super().__init__(master, fg_color="transparent", **kwargs)

        # Wrapper fuer Ausrichtung
        self.columnconfigure(0, weight=1)
        bubble = ctk.CTkFrame(self, fg_color=fg, corner_radius=12)

        label = ctk.CTkLabel(
            bubble,
            text=text,
            wraplength=480,
            justify="left",
            text_color=text_color,
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        label.pack(padx=12, pady=8)

        sticky = "e" if is_user else "w"
        bubble.grid(row=0, column=0, sticky=sticky, padx=(60 if is_user else 8, 8 if is_user else 60), pady=2)


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(ctk.CTkToplevel):
    """Einstellungen-Dialog: Modell, Temperatur, Theme, Audio."""

    def __init__(self, master, on_save=None):
        super().__init__(master)
        self.title("Einstellungen")
        self.geometry("460x520")
        self.resizable(False, False)
        self.grab_set()

        self._on_save = on_save
        self._cfg = load_config()

        pad = {"padx": 20, "pady": (10, 0)}

        # -- LLM --
        ctk.CTkLabel(self, text="LLM", font=ctk.CTkFont(size=15, weight="bold")).pack(**pad, anchor="w")

        ctk.CTkLabel(self, text="Modell").pack(padx=20, pady=(6, 0), anchor="w")
        self.model_entry = ctk.CTkEntry(self, width=360)
        self.model_entry.insert(0, self._cfg["llm"].get("model", ""))
        self.model_entry.pack(padx=20, anchor="w")

        ctk.CTkLabel(self, text="Temperatur").pack(padx=20, pady=(6, 0), anchor="w")
        self.temp_slider = ctk.CTkSlider(self, from_=0, to=2, number_of_steps=20, width=360)
        self.temp_slider.set(self._cfg["llm"].get("temperature", 0.7))
        self.temp_slider.pack(padx=20, anchor="w")
        self.temp_label = ctk.CTkLabel(self, text=f"{self._cfg['llm'].get('temperature', 0.7):.1f}")
        self.temp_label.pack(padx=20, anchor="w")
        self.temp_slider.configure(command=lambda v: self.temp_label.configure(text=f"{v:.1f}"))

        ctk.CTkLabel(self, text="Max Tokens").pack(padx=20, pady=(6, 0), anchor="w")
        self.tokens_entry = ctk.CTkEntry(self, width=360)
        self.tokens_entry.insert(0, str(self._cfg["llm"].get("max_tokens", 2048)))
        self.tokens_entry.pack(padx=20, anchor="w")

        # -- Theme --
        ctk.CTkLabel(self, text="Darstellung", font=ctk.CTkFont(size=15, weight="bold")).pack(**pad, anchor="w")

        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.pack(padx=20, anchor="w")
        ctk.CTkRadioButton(theme_frame, text="Dunkel", variable=self.theme_var, value="Dark").pack(side="left", padx=(0, 12))
        ctk.CTkRadioButton(theme_frame, text="Hell", variable=self.theme_var, value="Light").pack(side="left")

        # -- Buttons --
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(btn_frame, text="Speichern", command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray", command=self.destroy).pack(side="right")

    def _save(self):
        self._cfg["llm"]["model"] = self.model_entry.get().strip()
        self._cfg["llm"]["temperature"] = round(self.temp_slider.get(), 1)
        try:
            self._cfg["llm"]["max_tokens"] = int(self.tokens_entry.get())
        except ValueError:
            pass

        ctk.set_appearance_mode(self.theme_var.get())
        save_config(self._cfg)

        if self._on_save:
            self._on_save(self._cfg)
        self.destroy()


# ---------------------------------------------------------------------------
# Email Setup Dialog
# ---------------------------------------------------------------------------

class EmailSetupDialog(ctk.CTkToplevel):
    """Dialog zum Einrichten eines E-Mail-Providers."""

    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.title("E-Mail-Provider einrichten")
        self.geometry("520x580")
        self.resizable(False, False)
        self.grab_set()
        self._on_saved = on_saved

        from scripts.email_provider import KNOWN_PROVIDERS, get_provider_display_name

        pad = {"padx": 20, "pady": (10, 0)}

        ctk.CTkLabel(self, text="E-Mail-Provider einrichten",
                      font=ctk.CTkFont(size=16, weight="bold")).pack(**pad, anchor="w")

        # Aktueller Provider
        current = get_provider_display_name()
        self._current_label = ctk.CTkLabel(self, text=f"Aktuell: {current}",
                                            text_color="gray", font=ctk.CTkFont(size=11))
        self._current_label.pack(padx=20, anchor="w")

        # Provider-Auswahl
        ctk.CTkLabel(self, text="Provider waehlen:").pack(padx=20, pady=(12, 0), anchor="w")

        provider_names = ["Gmail (OAuth2 API)"]
        self._provider_keys = {"Gmail (OAuth2 API)": "gmail_oauth"}
        for key, val in KNOWN_PROVIDERS.items():
            name = val["name"]
            provider_names.append(name)
            self._provider_keys[name] = key
        provider_names.append("Benutzerdefiniert (IMAP/SMTP)")
        self._provider_keys["Benutzerdefiniert (IMAP/SMTP)"] = "custom"

        self.provider_menu = ctk.CTkOptionMenu(
            self, values=provider_names, width=440,
            command=self._on_provider_changed,
        )
        self.provider_menu.pack(padx=20, anchor="w")

        # Hinweis-Label
        self.note_label = ctk.CTkLabel(self, text="", text_color="#d97706",
                                        font=ctk.CTkFont(size=11), wraplength=440)
        self.note_label.pack(padx=20, pady=(4, 0), anchor="w")

        # IMAP/SMTP-Felder (fuer Presets und Custom)
        self.imap_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.imap_frame.pack(fill="x", padx=20, pady=(8, 0))

        ctk.CTkLabel(self.imap_frame, text="E-Mail-Adresse / Benutzername:").pack(anchor="w")
        self.username_entry = ctk.CTkEntry(self.imap_frame, width=440,
                                            placeholder_text="user@example.com")
        self.username_entry.pack(anchor="w")

        ctk.CTkLabel(self.imap_frame, text="Passwort / App-Passwort:").pack(anchor="w", pady=(6, 0))
        self.password_entry = ctk.CTkEntry(self.imap_frame, width=440,
                                            placeholder_text="Passwort", show="*")
        self.password_entry.pack(anchor="w")

        # Custom IMAP/SMTP Felder
        self.custom_frame = ctk.CTkFrame(self.imap_frame, fg_color="transparent")
        self.custom_frame.pack(fill="x", pady=(6, 0))

        row1 = ctk.CTkFrame(self.custom_frame, fg_color="transparent")
        row1.pack(fill="x")
        ctk.CTkLabel(row1, text="IMAP-Server:").pack(side="left")
        self.imap_host_entry = ctk.CTkEntry(row1, width=240, placeholder_text="imap.example.com")
        self.imap_host_entry.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(row1, text="Port:").pack(side="left", padx=(8, 0))
        self.imap_port_entry = ctk.CTkEntry(row1, width=60)
        self.imap_port_entry.insert(0, "993")
        self.imap_port_entry.pack(side="left", padx=(4, 0))

        row2 = ctk.CTkFrame(self.custom_frame, fg_color="transparent")
        row2.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(row2, text="SMTP-Server:").pack(side="left")
        self.smtp_host_entry = ctk.CTkEntry(row2, width=240, placeholder_text="smtp.example.com")
        self.smtp_host_entry.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(row2, text="Port:").pack(side="left", padx=(8, 0))
        self.smtp_port_entry = ctk.CTkEntry(row2, width=60)
        self.smtp_port_entry.insert(0, "587")
        self.smtp_port_entry.pack(side="left", padx=(4, 0))

        # Initial: Custom-Felder verstecken
        self.custom_frame.pack_forget()

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16, padx=20, fill="x")
        ctk.CTkButton(btn_frame, text="Verbindung testen", fg_color="#7c3aed",
                       hover_color="#6d28d9", command=self._test).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Speichern", command=self._save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray",
                       command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green",
                                          wraplength=440, font=ctk.CTkFont(size=12))
        self.status_label.pack(padx=20, pady=(0, 8))

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
            self.imap_frame.pack(fill="x", padx=20, pady=(8, 0))
            self.custom_frame.pack(fill="x", pady=(6, 0))
            self.note_label.configure(text="Trage die IMAP/SMTP-Daten deines Providers ein.")
        elif key in KNOWN_PROVIDERS:
            self.imap_frame.pack(fill="x", padx=20, pady=(8, 0))
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
            self.status_label.configure(text="Gmail OAuth2 als Provider gespeichert.", text_color="green")
            if self._on_saved:
                self._on_saved()
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_label.configure(text="E-Mail und Passwort sind Pflichtfelder.", text_color="red")
            return

        if key == "custom":
            imap_host = self.imap_host_entry.get().strip()
            smtp_host = self.smtp_host_entry.get().strip()
            if not imap_host or not smtp_host:
                self.status_label.configure(text="IMAP- und SMTP-Server sind Pflichtfelder.", text_color="red")
                return
            try:
                imap_port = int(self.imap_port_entry.get())
                smtp_port = int(self.smtp_port_entry.get())
            except ValueError:
                self.status_label.configure(text="Ports muessen Zahlen sein.", text_color="red")
                return
            setup_imap_provider(
                imap_host=imap_host, imap_port=imap_port,
                smtp_host=smtp_host, smtp_port=smtp_port,
                username=username, password=password,
            )
        else:
            setup_imap_provider(preset_key=key, username=username, password=password)

        self.status_label.configure(text="E-Mail-Provider gespeichert!", text_color="green")
        if self._on_saved:
            self._on_saved()

    def _test(self):
        from scripts.email_provider import (
            setup_imap_provider, setup_gmail_oauth,
            ImapSmtpProvider, GmailOAuthProvider, KNOWN_PROVIDERS,
        )

        key = self._get_selected_key()
        self.status_label.configure(text="Teste Verbindung...", text_color="gray")
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
                self.status_label.configure(text="Ports muessen Zahlen sein.", text_color="red")
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
            color = "green" if success else "red"
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
        self.geometry("460x420")
        self.resizable(False, False)
        self.grab_set()
        self._on_send = on_send

        pad = {"padx": 20, "pady": (10, 0)}

        # Provider-Info
        try:
            from scripts.email_provider import get_provider_display_name
            provider_name = get_provider_display_name()
        except Exception:
            provider_name = "Gmail"
        ctk.CTkLabel(self, text=f"Provider: {provider_name}",
                      text_color="gray", font=ctk.CTkFont(size=11)).pack(padx=20, pady=(8, 0), anchor="w")

        ctk.CTkLabel(self, text="Empfaenger").pack(**pad, anchor="w")
        self.to_entry = ctk.CTkEntry(self, width=400, placeholder_text="empfaenger@example.com")
        self.to_entry.pack(padx=20, anchor="w")

        ctk.CTkLabel(self, text="Betreff").pack(**pad, anchor="w")
        self.subject_entry = ctk.CTkEntry(self, width=400, placeholder_text="Betreff...")
        self.subject_entry.pack(padx=20, anchor="w")

        ctk.CTkLabel(self, text="Nachricht").pack(**pad, anchor="w")
        self.body_text = ctk.CTkTextbox(self, width=400, height=160)
        self.body_text.pack(padx=20, anchor="w")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16, padx=20, fill="x")
        ctk.CTkButton(btn_frame, text="Entwurf erstellen", command=self._send).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray", command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(padx=20)

    def _send(self):
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", "end").strip()
        if not to or not subject:
            self.status_label.configure(text="Empfaenger und Betreff sind Pflichtfelder.", text_color="red")
            return

        try:
            from scripts.email_provider import get_provider
            provider = get_provider()
            result = provider.create_draft(to, subject, body)
            self.status_label.configure(text=f"Entwurf erstellt (ID: {result['id']})", text_color="green")
            if self._on_send:
                self._on_send(to, subject)
        except FileNotFoundError:
            self.status_label.configure(text="E-Mail-Provider nicht konfiguriert.", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color="red")


# ---------------------------------------------------------------------------
# New Agent Dialog
# ---------------------------------------------------------------------------

class NewAgentDialog(ctk.CTkToplevel):
    """Dialog zum Erstellen eines neuen Agents."""

    def __init__(self, master, on_created=None):
        super().__init__(master)
        self.title("Neuer Agent")
        self.geometry("500x560")
        self.resizable(False, False)
        self.grab_set()
        self._on_created = on_created

        pad = {"padx": 20, "pady": (10, 0)}

        ctk.CTkLabel(self, text="Agent erstellen", font=ctk.CTkFont(size=16, weight="bold")).pack(**pad, anchor="w")

        ctk.CTkLabel(self, text="Name").pack(padx=20, pady=(12, 0), anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=420, placeholder_text="z.B. buchungs_agent")
        self.name_entry.pack(padx=20, anchor="w")

        ctk.CTkLabel(self, text="Beschreibung").pack(padx=20, pady=(8, 0), anchor="w")
        self.desc_entry = ctk.CTkEntry(self, width=420, placeholder_text="Kurze Beschreibung...")
        self.desc_entry.pack(padx=20, anchor="w")

        ctk.CTkLabel(self, text="System-Prompt").pack(padx=20, pady=(8, 0), anchor="w")
        self.prompt_text = ctk.CTkTextbox(self, width=420, height=120)
        self.prompt_text.insert("1.0", "Du bist ein hilfreicher Assistent.")
        self.prompt_text.pack(padx=20, anchor="w")

        ctk.CTkLabel(self, text="Tools").pack(padx=20, pady=(8, 0), anchor="w")
        self._tool_vars: dict[str, tk.BooleanVar] = {}
        tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        tools_frame.pack(padx=20, anchor="w")

        from agents.base_agent import ALL_TOOLS
        for tool_name in ALL_TOOLS:
            var = tk.BooleanVar(value=False)
            self._tool_vars[tool_name] = var
            ctk.CTkCheckBox(tools_frame, text=tool_name, variable=var).pack(anchor="w", pady=1)

        ctk.CTkLabel(self, text="Wissensdatenbank-Pfad (optional)").pack(padx=20, pady=(8, 0), anchor="w")
        self.knowledge_entry = ctk.CTkEntry(self, width=420, placeholder_text="z.B. KNOWLEDGE.md")
        self.knowledge_entry.pack(padx=20, anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16, padx=20, fill="x")
        ctk.CTkButton(btn_frame, text="Erstellen", command=self._create).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray", command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(padx=20)

    def _create(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        prompt = self.prompt_text.get("1.0", "end").strip()
        knowledge = self.knowledge_entry.get().strip() or None
        tools = [t for t, var in self._tool_vars.items() if var.get()]

        if not name:
            self.status_label.configure(text="Name ist erforderlich.", text_color="red")
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
            self.status_label.configure(text=f"Agent '{cfg['name']}' erstellt!", text_color="green")
            if self._on_created:
                self._on_created(cfg["name"])
            self.after(600, self.destroy)
        except ValueError as e:
            self.status_label.configure(text=str(e), text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color="red")


# ---------------------------------------------------------------------------
# Automations Dialog
# ---------------------------------------------------------------------------

class AutomationsDialog(ctk.CTkToplevel):
    """Dialog zur Verwaltung von Automationen."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Automationen")
        self.geometry("700x520")
        self.resizable(True, True)
        self.grab_set()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkButton(toolbar, text="+ Neue Automation", width=160,
                       fg_color="#7c3aed", hover_color="#6d28d9",
                       command=self._open_new_dialog).pack(side="left")
        ctk.CTkButton(toolbar, text="Ausfuehren", width=100,
                       command=self._run_selected).pack(side="left", padx=8)
        ctk.CTkButton(toolbar, text="Aktivieren/Deaktivieren", width=160,
                       fg_color="gray", command=self._toggle_selected).pack(side="left")
        ctk.CTkButton(toolbar, text="Loeschen", width=80,
                       fg_color="#dc2626", hover_color="#b91c1c",
                       command=self._delete_selected).pack(side="right")

        # Liste
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        self.list_frame.grid_columnconfigure(0, weight=0)
        self.list_frame.grid_columnconfigure(1, weight=1)
        self.list_frame.grid_columnconfigure(2, weight=0)
        self.list_frame.grid_columnconfigure(3, weight=0)
        self.list_frame.grid_columnconfigure(4, weight=0)

        self._selected_name = tk.StringVar(value="")
        self._radio_buttons: list[ctk.CTkRadioButton] = []

        # Log
        ctk.CTkLabel(self, text="Letzte Ausfuehrungen:", font=ctk.CTkFont(size=11),
                      text_color="gray").pack(padx=12, anchor="w")
        self.log_text = ctk.CTkTextbox(self, height=100, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="x", padx=12, pady=(0, 12))
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
            ctk.CTkLabel(self.list_frame, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                          text_color="gray").grid(row=0, column=col, sticky="w", padx=6, pady=2)

        if not autos:
            ctk.CTkLabel(self.list_frame, text="Keine Automationen vorhanden.",
                          text_color="gray").grid(row=1, column=0, columnspan=5, padx=6, pady=8)
            return

        for i, a in enumerate(autos, start=1):
            rb = ctk.CTkRadioButton(self.list_frame, text="", variable=self._selected_name,
                                     value=a["name"], width=20)
            rb.grid(row=i, column=0, padx=6, pady=2)
            self._radio_buttons.append(rb)

            ctk.CTkLabel(self.list_frame, text=a["name"],
                          font=ctk.CTkFont(size=12)).grid(row=i, column=1, sticky="w", padx=6, pady=2)

            ctk.CTkLabel(self.list_frame, text=a["action"],
                          text_color="gray").grid(row=i, column=2, sticky="w", padx=6, pady=2)

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
                          text_color="gray").grid(row=i, column=3, sticky="w", padx=6, pady=2)

            status_text = "aktiv" if a.get("enabled") else "inaktiv"
            status_color = "#22c55e" if a.get("enabled") else "#6b7280"
            ctk.CTkLabel(self.list_frame, text=status_text,
                          text_color=status_color).grid(row=i, column=4, sticky="w", padx=6, pady=2)

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
        self.geometry("480x540")
        self.resizable(False, False)
        self.grab_set()
        self._on_created = on_created

        from scripts.automation_manager import AVAILABLE_ACTIONS, TRIGGER_TYPES, AVAILABLE_EVENTS
        self._actions = AVAILABLE_ACTIONS
        self._events = AVAILABLE_EVENTS

        pad = {"padx": 16, "pady": (8, 0)}

        ctk.CTkLabel(self, text="Name").pack(**pad, anchor="w")
        self.name_entry = ctk.CTkEntry(self, width=420, placeholder_text="z.B. morgen_mails")
        self.name_entry.pack(padx=16, anchor="w")

        ctk.CTkLabel(self, text="Beschreibung").pack(**pad, anchor="w")
        self.desc_entry = ctk.CTkEntry(self, width=420, placeholder_text="Kurze Beschreibung...")
        self.desc_entry.pack(padx=16, anchor="w")

        ctk.CTkLabel(self, text="Aktion").pack(**pad, anchor="w")
        action_names = list(self._actions.keys())
        self.action_menu = ctk.CTkOptionMenu(self, values=action_names, width=420)
        self.action_menu.pack(padx=16, anchor="w")

        ctk.CTkLabel(self, text="Trigger-Typ").pack(**pad, anchor="w")
        self.trigger_menu = ctk.CTkOptionMenu(
            self, values=["schedule", "event", "manual"], width=420,
            command=self._on_trigger_changed,
        )
        self.trigger_menu.pack(padx=16, anchor="w")

        # Schedule-Felder
        self.schedule_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.schedule_frame.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(self.schedule_frame, text="Uhrzeit (HH:MM):").pack(side="left")
        self.time_entry = ctk.CTkEntry(self.schedule_frame, width=80)
        self.time_entry.insert(0, "08:00")
        self.time_entry.pack(side="left", padx=8)

        self.days_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.days_frame.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(self.days_frame, text="Tage (leer=taeglich):").pack(anchor="w")
        self._day_vars: dict[str, tk.BooleanVar] = {}
        days_row = ctk.CTkFrame(self.days_frame, fg_color="transparent")
        days_row.pack(anchor="w")
        for day in ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]:
            full = {"Mo": "monday", "Di": "tuesday", "Mi": "wednesday", "Do": "thursday",
                    "Fr": "friday", "Sa": "saturday", "So": "sunday"}[day]
            var = tk.BooleanVar(value=False)
            self._day_vars[full] = var
            ctk.CTkCheckBox(days_row, text=day, variable=var, width=50).pack(side="left", padx=2)

        # Event-Feld
        self.event_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.event_frame.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(self.event_frame, text="Event:").pack(anchor="w")
        event_names = list(self._events.keys())
        self.event_menu = ctk.CTkOptionMenu(self.event_frame, values=event_names or ["(keine)"], width=300)
        self.event_menu.pack(anchor="w")

        # Initial: schedule sichtbar, event versteckt
        self._on_trigger_changed("schedule")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=12, padx=16, fill="x")
        ctk.CTkButton(btn_frame, text="Erstellen", command=self._create).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_frame, text="Abbrechen", fg_color="gray", command=self.destroy).pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="", text_color="green")
        self.status_label.pack(padx=16)

    def _on_trigger_changed(self, value: str):
        if value == "schedule":
            self.schedule_frame.pack(fill="x", padx=16, pady=(4, 0))
            self.days_frame.pack(fill="x", padx=16, pady=(4, 0))
            self.event_frame.pack_forget()
        elif value == "event":
            self.schedule_frame.pack_forget()
            self.days_frame.pack_forget()
            self.event_frame.pack(fill="x", padx=16, pady=(4, 0))
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
            self.status_label.configure(text="Name ist erforderlich.", text_color="red")
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
            self.status_label.configure(text=f"Automation '{cfg['name']}' erstellt!", text_color="green")
            if self._on_created:
                self._on_created()
            self.after(600, self.destroy)
        except ValueError as e:
            self.status_label.configure(text=str(e), text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color="red")


# ---------------------------------------------------------------------------
# Setup Wizard (Erst-Einrichtung)
# ---------------------------------------------------------------------------

class SetupWizardDialog(ctk.CTkToplevel):
    """Erst-Einrichtungs-Assistent fuer HotelAgent.

    Wird beim ersten Start angezeigt oder ueber die GUI aufgerufen.
    Fragt nach API-Key und E-Mail-Provider.
    """

    def __init__(self, master, on_complete=None):
        super().__init__(master)
        self.title("HotelAgent — Einrichtung")
        self.geometry("560x520")
        self.resizable(False, False)
        self.grab_set()
        self._on_complete = on_complete
        self._page = 0

        self._build_page_0()

    # --- Seite 0: Willkommen ---

    def _build_page_0(self):
        self._clear()

        ctk.CTkLabel(self, text="Willkommen bei HotelAgent!",
                      font=ctk.CTkFont(size=20, weight="bold")).pack(padx=30, pady=(30, 8))
        ctk.CTkLabel(self, text="Lass uns die wichtigsten Einstellungen vornehmen.",
                      font=ctk.CTkFont(size=13), text_color="gray").pack(padx=30)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(frame, text="Schritt 1: OpenRouter API-Key",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(frame, text="Der API-Key wird fuer die KI-Funktionen benoetigt.\n"
                                  "Erstelle einen unter openrouter.ai/keys",
                      text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w")

        self.api_entry = ctk.CTkEntry(frame, width=460, placeholder_text="sk-or-...")
        self.api_entry.pack(anchor="w", pady=(8, 0))

        # Vorhandenen Key laden
        import os
        existing_key = os.getenv("OPENROUTER_API_KEY", "")
        if existing_key:
            self.api_entry.insert(0, existing_key)
            ctk.CTkLabel(frame, text="API-Key bereits vorhanden",
                          text_color="#22c55e", font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(frame, text="\nSchritt 2: E-Mail-Provider",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(12, 4))
        ctk.CTkLabel(frame, text="Waehle deinen E-Mail-Anbieter fuer die automatische\n"
                                  "E-Mail-Verarbeitung (kann auch spaeter eingerichtet werden).",
                      text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w")

        from scripts.email_provider import KNOWN_PROVIDERS
        provider_names = ["Spaeter einrichten", "Gmail (OAuth2 API)"]
        self._provider_keys = {"Spaeter einrichten": None, "Gmail (OAuth2 API)": "gmail_oauth"}
        for key, val in KNOWN_PROVIDERS.items():
            provider_names.append(val["name"])
            self._provider_keys[val["name"]] = key

        self.provider_menu = ctk.CTkOptionMenu(frame, values=provider_names, width=460)
        self.provider_menu.set("Spaeter einrichten")
        self.provider_menu.pack(anchor="w", pady=(8, 0))

        # IMAP-Felder (versteckt bis benoetigt)
        self.imap_frame = ctk.CTkFrame(frame, fg_color="transparent")

        ctk.CTkLabel(self.imap_frame, text="E-Mail-Adresse:").pack(anchor="w", pady=(4, 0))
        self.email_entry = ctk.CTkEntry(self.imap_frame, width=460, placeholder_text="user@example.com")
        self.email_entry.pack(anchor="w")

        ctk.CTkLabel(self.imap_frame, text="Passwort / App-Passwort:").pack(anchor="w", pady=(4, 0))
        self.pass_entry = ctk.CTkEntry(self.imap_frame, width=460, placeholder_text="Passwort", show="*")
        self.pass_entry.pack(anchor="w")

        self.provider_menu.configure(command=self._on_provider_changed)

        # Status
        self.status_label = ctk.CTkLabel(self, text="", text_color="green",
                                          font=ctk.CTkFont(size=12))
        self.status_label.pack(padx=30)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Ueberspringen", fg_color="gray",
                       command=self._skip).pack(side="left")
        ctk.CTkButton(btn_frame, text="Speichern & Starten",
                       fg_color="#e94560", hover_color="#c73e54",
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
            self.status_label.configure(text="API-Key gespeichert.", text_color="green")

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
                    self.status_label.configure(text="E-Mail-Provider gespeichert!", text_color="green")

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
        self.geometry("920x640")
        self.minsize(720, 480)

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
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -- Sidebar --
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        # (row weight set below after all buttons)

        logo = ctk.CTkLabel(self.sidebar, text="HotelAgent", font=ctk.CTkFont(size=20, weight="bold"))
        logo.grid(row=0, column=0, padx=20, pady=(20, 4))
        subtitle = ctk.CTkLabel(self.sidebar, text="KI-Hotelassistent", font=ctk.CTkFont(size=12), text_color="gray")
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 10))

        # Agent-Auswahl
        ctk.CTkLabel(self.sidebar, text="Agent:", font=ctk.CTkFont(size=11), text_color="gray").grid(
            row=2, column=0, padx=16, pady=(0, 0), sticky="w")
        self._agent_names = self._get_agent_choices()
        self.agent_selector = ctk.CTkOptionMenu(
            self.sidebar, values=self._agent_names,
            command=self._on_agent_changed,
        )
        self.agent_selector.set(self._agent_names[0] if self._agent_names else "hotel_agent")
        self.agent_selector.grid(row=3, column=0, padx=16, pady=(0, 4), sticky="ew")

        self.new_agent_btn = ctk.CTkButton(self.sidebar, text="+ Neuer Agent", height=28,
                                            font=ctk.CTkFont(size=11),
                                            fg_color="#7c3aed", hover_color="#6d28d9",
                                            command=self._open_new_agent_dialog)
        self.new_agent_btn.grid(row=4, column=0, padx=16, pady=(0, 12), sticky="ew")

        self.new_chat_btn = ctk.CTkButton(self.sidebar, text="Neuer Chat", command=self._new_chat)
        self.new_chat_btn.grid(row=5, column=0, padx=16, pady=4, sticky="ew")

        self.upload_btn = ctk.CTkButton(self.sidebar, text="Datei hochladen", command=self._upload_file)
        self.upload_btn.grid(row=6, column=0, padx=16, pady=4, sticky="ew")

        self.email_setup_btn = ctk.CTkButton(self.sidebar, text="E-Mail einrichten",
                                               fg_color="#0891b2", hover_color="#0e7490",
                                               command=self._open_email_setup_dialog)
        self.email_setup_btn.grid(row=7, column=0, padx=16, pady=4, sticky="ew")

        self.gmail_btn = ctk.CTkButton(self.sidebar, text="E-Mail-Entwurf", command=self._open_gmail_dialog)
        self.gmail_btn.grid(row=8, column=0, padx=16, pady=4, sticky="ew")

        self.check_mails_btn = ctk.CTkButton(self.sidebar, text="E-Mails pruefen",
                                              fg_color="#7c3aed", hover_color="#6d28d9",
                                              command=self._check_mails)
        self.check_mails_btn.grid(row=9, column=0, padx=16, pady=4, sticky="ew")

        self.automations_btn = ctk.CTkButton(self.sidebar, text="Automationen",
                                               fg_color="#d97706", hover_color="#b45309",
                                               command=self._open_automations_dialog)
        self.automations_btn.grid(row=10, column=0, padx=16, pady=4, sticky="ew")

        self.settings_btn = ctk.CTkButton(self.sidebar, text="Einstellungen", fg_color="gray", command=self._open_settings)
        self.settings_btn.grid(row=11, column=0, padx=16, pady=4, sticky="ew")

        self.sidebar.grid_rowconfigure(12, weight=1)

        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self._toggle_theme, onvalue=1, offvalue=0)
        self.theme_switch.select()  # Default dark
        self.theme_switch.grid(row=13, column=0, padx=16, pady=(4, 20), sticky="sw")

        # -- Main area --
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nswe", padx=0, pady=0)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Chat area (scrollable)
        self.chat_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        self.chat_frame.grid(row=0, column=0, sticky="nswe", padx=8, pady=(8, 0))
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Status bar
        self.status_label = ctk.CTkLabel(main_frame, text="Bereit", font=ctk.CTkFont(size=11), text_color="gray", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="we", padx=16, pady=(2, 0))

        # Input bar
        input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="we", padx=8, pady=8)
        input_frame.grid_columnconfigure(0, weight=1)

        self.msg_entry = ctk.CTkEntry(input_frame, placeholder_text="Nachricht eingeben...", height=40,
                                       font=ctk.CTkFont(size=13))
        self.msg_entry.grid(row=0, column=0, sticky="we", padx=(0, 6))
        self.msg_entry.bind("<Return>", lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(input_frame, text="Senden", width=80, height=40, command=self._send_message)
        self.send_btn.grid(row=0, column=1, padx=(0, 6))

        self.voice_btn = ctk.CTkButton(input_frame, text="Mikrofon", width=90, height=40,
                                        fg_color="#16a34a", hover_color="#15803d",
                                        command=self._toggle_voice)
        self.voice_btn.grid(row=0, column=2)

        # Disclaimer-Leiste
        disclaimer_bar = ctk.CTkLabel(
            main_frame,
            text="Hinweis: KI-generierte Antworten koennen fehlerhaft sein. Keine Haftung durch den Entwickler. Nutzung auf eigene Verantwortung.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="center",
            height=20,
        )
        disclaimer_bar.grid(row=3, column=0, sticky="we", padx=8, pady=(0, 4))

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
        # Alte Bubbles entfernen
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
