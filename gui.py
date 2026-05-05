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
# Gmail Draft Dialog
# ---------------------------------------------------------------------------

class GmailDraftDialog(ctk.CTkToplevel):
    """Dialog zum Erstellen eines Gmail-Entwurfs."""

    def __init__(self, master, on_send=None):
        super().__init__(master)
        self.title("Gmail-Entwurf erstellen")
        self.geometry("460x400")
        self.resizable(False, False)
        self.grab_set()
        self._on_send = on_send

        pad = {"padx": 20, "pady": (10, 0)}

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
            from scripts.gmail import create_draft
            result = create_draft(to, subject, body)
            self.status_label.configure(text=f"Entwurf erstellt (ID: {result['id']})", text_color="green")
            if self._on_send:
                self._on_send(to, subject)
        except FileNotFoundError:
            self.status_label.configure(text="credentials.json fehlt — Gmail nicht konfiguriert.", text_color="red")
        except Exception as e:
            self.status_label.configure(text=f"Fehler: {e}", text_color="red")


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
        self._voice_recording = False
        self._voice_thread: threading.Thread | None = None
        self._settings_dialog = None
        self._gmail_dialog = None

        self._build_ui()
        self._init_agent()

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
        self.sidebar.grid_rowconfigure(7, weight=1)

        logo = ctk.CTkLabel(self.sidebar, text="HotelAgent", font=ctk.CTkFont(size=20, weight="bold"))
        logo.grid(row=0, column=0, padx=20, pady=(20, 4))
        subtitle = ctk.CTkLabel(self.sidebar, text="KI-Hotelassistent", font=ctk.CTkFont(size=12), text_color="gray")
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 16))

        self.new_chat_btn = ctk.CTkButton(self.sidebar, text="Neuer Chat", command=self._new_chat)
        self.new_chat_btn.grid(row=2, column=0, padx=16, pady=4, sticky="ew")

        self.upload_btn = ctk.CTkButton(self.sidebar, text="Datei hochladen", command=self._upload_file)
        self.upload_btn.grid(row=3, column=0, padx=16, pady=4, sticky="ew")

        self.gmail_btn = ctk.CTkButton(self.sidebar, text="Gmail-Entwurf", command=self._open_gmail_dialog)
        self.gmail_btn.grid(row=4, column=0, padx=16, pady=4, sticky="ew")

        self.check_mails_btn = ctk.CTkButton(self.sidebar, text="E-Mails pruefen",
                                              fg_color="#7c3aed", hover_color="#6d28d9",
                                              command=self._check_mails)
        self.check_mails_btn.grid(row=5, column=0, padx=16, pady=4, sticky="ew")

        self.settings_btn = ctk.CTkButton(self.sidebar, text="Einstellungen", fg_color="gray", command=self._open_settings)
        self.settings_btn.grid(row=6, column=0, padx=16, pady=4, sticky="ew")

        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self._toggle_theme, onvalue=1, offvalue=0)
        self.theme_switch.select()  # Default dark
        self.theme_switch.grid(row=8, column=0, padx=16, pady=(4, 20), sticky="sw")

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

    # -----------------------------------------------------------------------
    # Agent
    # -----------------------------------------------------------------------

    def _init_agent(self):
        """Agent initialisieren."""
        try:
            from agents.hotel_agent import HotelAgent
            self._conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._agent = HotelAgent(conversation_id=self._conversation_id)
            self._set_status("Agent bereit")
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
    # Gmail
    # -----------------------------------------------------------------------

    def _open_gmail_dialog(self):
        if self._gmail_dialog is not None and self._gmail_dialog.winfo_exists():
            self._gmail_dialog.focus()
            return
        self._gmail_dialog = GmailDraftDialog(self, on_send=self._on_gmail_sent)

    def _on_gmail_sent(self, to: str, subject: str):
        self._add_bubble("assistant", f"Gmail-Entwurf erstellt an {to}: '{subject}'")

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
