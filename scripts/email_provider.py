"""HotelAgent — E-Mail-Provider-Abstraktion: Gmail, IMAP/SMTP und 15+ Provider-Presets."""

import base64
import email as email_lib
import imaplib
import re
import smtplib
import time
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from pathlib import Path

from scripts.config_manager import load_config, save_config

PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Bekannte Provider-Presets (IMAP/SMTP)
# ---------------------------------------------------------------------------

KNOWN_PROVIDERS: dict[str, dict] = {
    "gmail": {
        "name": "Gmail",
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "note": "App-Passwort erforderlich (2FA muss aktiv sein)",
    },
    "outlook": {
        "name": "Outlook / Hotmail / Live",
        "imap_host": "outlook.office365.com",
        "imap_port": 993,
        "smtp_host": "smtp.office365.com",
        "smtp_port": 587,
        "note": "App-Passwort empfohlen",
    },
    "yahoo": {
        "name": "Yahoo Mail",
        "imap_host": "imap.mail.yahoo.com",
        "imap_port": 993,
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "note": "App-Passwort erforderlich",
    },
    "gmx": {
        "name": "GMX",
        "imap_host": "imap.gmx.net",
        "imap_port": 993,
        "smtp_host": "mail.gmx.net",
        "smtp_port": 587,
        "note": "IMAP muss in den GMX-Einstellungen aktiviert werden",
    },
    "webde": {
        "name": "Web.de",
        "imap_host": "imap.web.de",
        "imap_port": 993,
        "smtp_host": "smtp.web.de",
        "smtp_port": 587,
        "note": "IMAP muss in den Web.de-Einstellungen aktiviert werden",
    },
    "t-online": {
        "name": "T-Online",
        "imap_host": "secureimap.t-online.de",
        "imap_port": 993,
        "smtp_host": "securesmtp.t-online.de",
        "smtp_port": 587,
        "note": "E-Mail-Passwort im Kundencenter erstellen",
    },
    "aol": {
        "name": "AOL",
        "imap_host": "imap.aol.com",
        "imap_port": 993,
        "smtp_host": "smtp.aol.com",
        "smtp_port": 587,
        "note": "App-Passwort erforderlich",
    },
    "icloud": {
        "name": "iCloud Mail",
        "imap_host": "imap.mail.me.com",
        "imap_port": 993,
        "smtp_host": "smtp.mail.me.com",
        "smtp_port": 587,
        "note": "App-spezifisches Passwort unter appleid.apple.com erstellen",
    },
    "zoho": {
        "name": "Zoho Mail",
        "imap_host": "imap.zoho.com",
        "imap_port": 993,
        "smtp_host": "smtp.zoho.com",
        "smtp_port": 587,
        "note": "IMAP in Zoho-Einstellungen aktivieren",
    },
    "fastmail": {
        "name": "Fastmail",
        "imap_host": "imap.fastmail.com",
        "imap_port": 993,
        "smtp_host": "smtp.fastmail.com",
        "smtp_port": 587,
        "note": "App-Passwort unter Settings > Privacy & Security erstellen",
    },
    "protonmail": {
        "name": "ProtonMail (Bridge)",
        "imap_host": "127.0.0.1",
        "imap_port": 1143,
        "smtp_host": "127.0.0.1",
        "smtp_port": 1025,
        "ssl": False,
        "note": "ProtonMail Bridge muss installiert und aktiv sein",
    },
    "mailde": {
        "name": "Mail.de",
        "imap_host": "imap.mail.de",
        "imap_port": 993,
        "smtp_host": "smtp.mail.de",
        "smtp_port": 587,
        "note": "",
    },
    "posteo": {
        "name": "Posteo",
        "imap_host": "posteo.de",
        "imap_port": 993,
        "smtp_host": "posteo.de",
        "smtp_port": 587,
        "note": "",
    },
    "mailbox_org": {
        "name": "Mailbox.org",
        "imap_host": "imap.mailbox.org",
        "imap_port": 993,
        "smtp_host": "smtp.mailbox.org",
        "smtp_port": 587,
        "note": "",
    },
    "ionos": {
        "name": "IONOS (1&1)",
        "imap_host": "imap.ionos.de",
        "imap_port": 993,
        "smtp_host": "smtp.ionos.de",
        "smtp_port": 587,
        "note": "",
    },
    "strato": {
        "name": "Strato",
        "imap_host": "imap.strato.de",
        "imap_port": 993,
        "smtp_host": "smtp.strato.de",
        "smtp_port": 465,
        "note": "",
    },
    "freenet": {
        "name": "Freenet",
        "imap_host": "mx.freenet.de",
        "imap_port": 993,
        "smtp_host": "mx.freenet.de",
        "smtp_port": 587,
        "note": "",
    },
}


def get_provider_names() -> list[str]:
    """Alle bekannten Provider-Namen zurueckgeben."""
    return [v["name"] for v in KNOWN_PROVIDERS.values()] + ["Gmail (OAuth2 API)", "Benutzerdefiniert (IMAP/SMTP)"]


def get_provider_key_by_name(display_name: str) -> str | None:
    """Provider-Key anhand des Anzeigenamens finden."""
    for key, val in KNOWN_PROVIDERS.items():
        if val["name"] == display_name:
            return key
    return None


# ---------------------------------------------------------------------------
# Abstrakte Basis-Klasse
# ---------------------------------------------------------------------------

class EmailProvider(ABC):
    """Abstrakte Basis-Klasse fuer E-Mail-Provider."""

    @abstractmethod
    def get_inbox_emails(self, max_results: int = 20, only_unread: bool = True) -> list[dict]:
        """Posteingang lesen."""
        ...

    @abstractmethod
    def create_draft(self, to: str, subject: str, body: str) -> dict:
        """E-Mail-Entwurf erstellen."""
        ...

    @abstractmethod
    def create_reply_draft(self, thread_id: str, message_id: str,
                           to: str, subject: str, body: str) -> dict:
        """Antwort-Entwurf erstellen."""
        ...

    @abstractmethod
    def get_templates(self, folder_name: str = None, min_year: int = None) -> list[dict]:
        """Vorlagen aus einem Ordner/Label lesen."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Pruefen ob der Provider konfiguriert ist."""
        ...

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Verbindung testen. Gibt (Erfolg, Nachricht) zurueck."""
        ...


# ---------------------------------------------------------------------------
# Gmail OAuth2 Provider (bestehende Implementierung)
# ---------------------------------------------------------------------------

class GmailOAuthProvider(EmailProvider):
    """Gmail ueber OAuth2 API (bestehende Implementierung)."""

    def get_inbox_emails(self, max_results: int = 20, only_unread: bool = True) -> list[dict]:
        from scripts.gmail import get_inbox_emails
        return get_inbox_emails(max_results=max_results, only_unread=only_unread)

    def create_draft(self, to: str, subject: str, body: str) -> dict:
        from scripts.gmail import create_draft
        return create_draft(to, subject, body)

    def create_reply_draft(self, thread_id: str, message_id: str,
                           to: str, subject: str, body: str) -> dict:
        from scripts.gmail import create_reply_draft
        return create_reply_draft(thread_id, message_id, to, subject, body)

    def get_templates(self, folder_name: str = None, min_year: int = None) -> list[dict]:
        from scripts.gmail import get_templates
        return get_templates(label_name=folder_name, min_year=min_year)

    def is_configured(self) -> bool:
        from scripts.gmail import has_credentials
        return has_credentials()

    def test_connection(self) -> tuple[bool, str]:
        try:
            from scripts.gmail import authenticate
            authenticate()
            return True, "Gmail OAuth2 Verbindung erfolgreich"
        except Exception as e:
            return False, f"Gmail-Fehler: {e}"


# ---------------------------------------------------------------------------
# IMAP/SMTP Provider (generisch, fuer alle anderen)
# ---------------------------------------------------------------------------

class ImapSmtpProvider(EmailProvider):
    """Generischer IMAP/SMTP-Provider fuer beliebige E-Mail-Anbieter."""

    def __init__(self, imap_host: str, imap_port: int, smtp_host: str, smtp_port: int,
                 username: str, password: str, use_ssl: bool = True,
                 drafts_folder: str = "Drafts", template_folder: str = "Vorlagen"):
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.drafts_folder = drafts_folder
        self.template_folder = template_folder

    def _connect_imap(self) -> imaplib.IMAP4:
        """IMAP-Verbindung herstellen."""
        if self.use_ssl:
            conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        else:
            conn = imaplib.IMAP4(self.imap_host, self.imap_port)
        conn.login(self.username, self.password)
        return conn

    def _find_drafts_folder(self, conn: imaplib.IMAP4) -> str:
        """Entwuerfe-Ordner finden (verschiedene Provider nutzen verschiedene Namen)."""
        status, folders = conn.list()
        if status != "OK":
            return self.drafts_folder

        folder_names = []
        for f in folders:
            decoded = f.decode("utf-8") if isinstance(f, bytes) else f
            # Ordnernamen extrahieren (letzter Teil nach dem Trennzeichen)
            match = re.search(r'"([^"]*)"$|(\S+)$', decoded)
            if match:
                name = match.group(1) or match.group(2)
                folder_names.append(name)

        # Bekannte Drafts-Ordner-Namen
        draft_names = [
            "Drafts", "INBOX.Drafts", "Entwuerfe", "Entw&APw-rfe",
            "[Gmail]/Drafts", "[Gmail]/Entw&APw-rfe",
            "INBOX.Drafts", "Draft",
        ]

        for dn in draft_names:
            if dn in folder_names:
                return dn

        # Fallback: Ordner mit "draft" oder "entwu" im Namen
        for name in folder_names:
            lower = name.lower()
            if "draft" in lower or "entwu" in lower or "entw" in lower:
                return name

        return self.drafts_folder

    def _find_template_folder(self, conn: imaplib.IMAP4) -> str | None:
        """Vorlagen-Ordner finden."""
        status, folders = conn.list()
        if status != "OK":
            return None

        folder_names = []
        for f in folders:
            decoded = f.decode("utf-8") if isinstance(f, bytes) else f
            match = re.search(r'"([^"]*)"$|(\S+)$', decoded)
            if match:
                name = match.group(1) or match.group(2)
                folder_names.append(name)

        # Konfigurierter Name oder Varianten
        search_names = [
            self.template_folder,
            f"INBOX.{self.template_folder}",
            f"[Gmail]/{self.template_folder}",
        ]

        for sn in search_names:
            if sn in folder_names:
                return sn

        # Fuzzy-Suche
        for name in folder_names:
            if self.template_folder.lower() in name.lower():
                return name

        return None

    @staticmethod
    def _decode_mime_header(header: str) -> str:
        """MIME-kodierten Header dekodieren."""
        if not header:
            return ""
        decoded_parts = email_lib.header.decode_header(header)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return " ".join(result)

    @staticmethod
    def _get_body(msg: email_lib.message.Message) -> str:
        """E-Mail-Body extrahieren."""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
            # Fallback: text/html
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        html = payload.decode(charset, errors="replace")
                        text = re.sub(r"<[^>]+>", " ", html)
                        return re.sub(r"\s+", " ", text).strip()
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""

    def get_inbox_emails(self, max_results: int = 20, only_unread: bool = True) -> list[dict]:
        conn = self._connect_imap()
        try:
            conn.select("INBOX")
            criteria = "UNSEEN" if only_unread else "ALL"
            status, data = conn.search(None, criteria)
            if status != "OK":
                return []

            msg_ids = data[0].split()
            # Neueste zuerst, limitiert
            msg_ids = msg_ids[-max_results:][::-1]

            emails = []
            for mid in msg_ids:
                status, msg_data = conn.fetch(mid, "(RFC822)")
                if status != "OK":
                    continue
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)

                message_id = msg.get("Message-ID", "")
                from_addr = self._decode_mime_header(msg.get("From", ""))
                to_addr = self._decode_mime_header(msg.get("To", ""))
                subject = self._decode_mime_header(msg.get("Subject", ""))
                date = msg.get("Date", "")
                body = self._get_body(msg)

                # Thread-ID: verwende References oder Message-ID
                references = msg.get("References", "")
                thread_id = references.split()[0] if references else message_id

                emails.append({
                    "id": mid.decode() if isinstance(mid, bytes) else str(mid),
                    "thread_id": thread_id,
                    "message_id": message_id,
                    "from": from_addr,
                    "to": to_addr,
                    "subject": subject,
                    "date": date,
                    "body": body,
                    "snippet": body[:200] if body else "",
                })

            return emails
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def create_draft(self, to: str, subject: str, body: str) -> dict:
        conn = self._connect_imap()
        try:
            drafts = self._find_drafts_folder(conn)

            msg = MIMEText(body, _charset="utf-8")
            msg["To"] = to
            msg["From"] = self.username
            msg["Subject"] = subject
            msg["Date"] = email_lib.utils.formatdate(localtime=True)

            status, _ = conn.append(
                drafts, "\\Draft",
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes(),
            )

            if status != "OK":
                raise RuntimeError(f"Entwurf konnte nicht erstellt werden (IMAP: {status})")

            return {
                "id": f"draft_{int(time.time())}",
                "to": to,
                "subject": subject,
            }
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def create_reply_draft(self, thread_id: str, message_id: str,
                           to: str, subject: str, body: str) -> dict:
        conn = self._connect_imap()
        try:
            drafts = self._find_drafts_folder(conn)

            msg = MIMEText(body, _charset="utf-8")
            msg["To"] = to
            msg["From"] = self.username
            msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
            msg["Date"] = email_lib.utils.formatdate(localtime=True)
            if message_id:
                msg["In-Reply-To"] = message_id
                msg["References"] = message_id

            status, _ = conn.append(
                drafts, "\\Draft",
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes(),
            )

            if status != "OK":
                raise RuntimeError(f"Antwort-Entwurf konnte nicht erstellt werden (IMAP: {status})")

            return {
                "id": f"reply_{int(time.time())}",
                "to": to,
                "subject": subject,
                "thread_id": thread_id,
            }
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def get_templates(self, folder_name: str = None, min_year: int = None) -> list[dict]:
        cfg = load_config().get("email_processing", {})
        if folder_name is None:
            folder_name = cfg.get("template_label", self.template_folder)
        if min_year is None:
            min_year = cfg.get("min_template_year", 2025)

        conn = self._connect_imap()
        try:
            tmpl_folder = folder_name
            # Versuche den Ordner zu finden
            status, _ = conn.select(tmpl_folder)
            if status != "OK":
                # Versuche mit Praefix
                for prefix in ["INBOX.", "[Gmail]/", ""]:
                    alt = f"{prefix}{folder_name}"
                    status, _ = conn.select(alt)
                    if status == "OK":
                        tmpl_folder = alt
                        break
                else:
                    raise ValueError(
                        f"Vorlagen-Ordner '{folder_name}' nicht gefunden. "
                        "Erstelle den Ordner in deinem E-Mail-Programm und verschiebe Vorlagen dorthin."
                    )

            status, data = conn.search(None, "ALL")
            if status != "OK":
                return []

            msg_ids = data[0].split()
            templates = []

            for mid in msg_ids:
                status, msg_data = conn.fetch(mid, "(RFC822)")
                if status != "OK":
                    continue
                raw = msg_data[0][1]
                msg = email_lib.message_from_bytes(raw)

                subject = self._decode_mime_header(msg.get("Subject", ""))
                body = self._get_body(msg)

                # Jahr-Filter
                years = re.findall(r"\b(20\d{2})\b", subject)
                if years:
                    max_year_in_subject = max(int(y) for y in years)
                    if max_year_in_subject < min_year:
                        continue

                templates.append({
                    "id": mid.decode() if isinstance(mid, bytes) else str(mid),
                    "subject": subject,
                    "body": body,
                })

            return templates
        finally:
            try:
                conn.logout()
            except Exception:
                pass

    def is_configured(self) -> bool:
        return bool(self.username and self.password and self.imap_host)

    def test_connection(self) -> tuple[bool, str]:
        try:
            conn = self._connect_imap()
            conn.select("INBOX")
            conn.logout()
            return True, f"IMAP-Verbindung zu {self.imap_host} erfolgreich"
        except imaplib.IMAP4.error as e:
            return False, f"IMAP-Anmeldung fehlgeschlagen: {e}"
        except Exception as e:
            return False, f"Verbindungsfehler: {e}"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_provider() -> EmailProvider:
    """Provider anhand der Konfiguration erstellen.

    Liest den konfigurierten Provider aus settings.yaml und gibt die
    passende Provider-Instanz zurueck.
    """
    cfg = load_config()
    email_cfg = cfg.get("email", {})
    provider_type = email_cfg.get("provider", "gmail_oauth")

    if provider_type == "gmail_oauth":
        return GmailOAuthProvider()

    if provider_type == "imap":
        imap_cfg = email_cfg.get("imap", {})
        import os
        password = imap_cfg.get("password", "") or os.getenv("EMAIL_PASSWORD", "")
        return ImapSmtpProvider(
            imap_host=imap_cfg.get("host", ""),
            imap_port=imap_cfg.get("port", 993),
            smtp_host=imap_cfg.get("smtp_host", ""),
            smtp_port=imap_cfg.get("smtp_port", 587),
            username=imap_cfg.get("username", ""),
            password=password,
            use_ssl=imap_cfg.get("ssl", True),
            drafts_folder=imap_cfg.get("drafts_folder", "Drafts"),
            template_folder=email_cfg.get("template_folder",
                                          cfg.get("email_processing", {}).get("template_label", "Vorlagen")),
        )

    raise ValueError(f"Unbekannter E-Mail-Provider: {provider_type}")


def get_provider_display_name() -> str:
    """Anzeigename des aktuell konfigurierten Providers."""
    cfg = load_config()
    email_cfg = cfg.get("email", {})
    provider_type = email_cfg.get("provider", "gmail_oauth")

    if provider_type == "gmail_oauth":
        return "Gmail (OAuth2 API)"

    if provider_type == "imap":
        imap_cfg = email_cfg.get("imap", {})
        preset = email_cfg.get("preset", "")
        if preset and preset in KNOWN_PROVIDERS:
            return KNOWN_PROVIDERS[preset]["name"]
        return f"IMAP: {imap_cfg.get('host', '?')}"

    return provider_type


def is_any_provider_configured() -> bool:
    """Pruefen ob irgendein E-Mail-Provider konfiguriert ist."""
    cfg = load_config()
    email_cfg = cfg.get("email", {})
    provider_type = email_cfg.get("provider", "gmail_oauth")

    if provider_type == "gmail_oauth":
        try:
            from scripts.gmail import has_credentials
            return has_credentials()
        except Exception:
            return False

    if provider_type == "imap":
        imap_cfg = email_cfg.get("imap", {})
        import os
        password = imap_cfg.get("password", "") or os.getenv("EMAIL_PASSWORD", "")
        return bool(imap_cfg.get("host") and imap_cfg.get("username") and password)

    return False


def setup_imap_provider(preset_key: str = None, imap_host: str = None,
                        imap_port: int = 993, smtp_host: str = None,
                        smtp_port: int = 587, username: str = "",
                        password: str = "", use_ssl: bool = True) -> dict:
    """IMAP/SMTP-Provider in settings.yaml konfigurieren.

    Args:
        preset_key: Key aus KNOWN_PROVIDERS (z.B. 'gmx', 'outlook').
        imap_host: IMAP-Server (wird von Preset ueberschrieben falls gesetzt).
        imap_port: IMAP-Port.
        smtp_host: SMTP-Server.
        smtp_port: SMTP-Port.
        username: E-Mail-Adresse / Benutzername.
        password: Passwort (wird in settings.yaml gespeichert).
        use_ssl: SSL verwenden.

    Returns:
        Die aktualisierte E-Mail-Konfiguration.
    """
    cfg = load_config()

    if preset_key and preset_key in KNOWN_PROVIDERS:
        preset = KNOWN_PROVIDERS[preset_key]
        imap_host = preset["imap_host"]
        imap_port = preset["imap_port"]
        smtp_host = preset["smtp_host"]
        smtp_port = preset["smtp_port"]
        use_ssl = preset.get("ssl", True)

    email_cfg = {
        "provider": "imap",
        "preset": preset_key or "",
        "imap": {
            "host": imap_host or "",
            "port": imap_port,
            "smtp_host": smtp_host or "",
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
            "ssl": use_ssl,
            "drafts_folder": "Drafts",
        },
    }

    cfg["email"] = email_cfg
    save_config(cfg)
    return email_cfg


def setup_gmail_oauth() -> dict:
    """Gmail OAuth2 als Provider konfigurieren."""
    cfg = load_config()
    cfg["email"] = {
        "provider": "gmail_oauth",
    }
    save_config(cfg)
    return cfg["email"]
