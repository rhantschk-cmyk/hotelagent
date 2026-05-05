"""HotelAgent — Gmail: Entwuerfe erstellen, Posteingang lesen, Vorlagen verwalten."""

import base64
import re
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from scripts.config_manager import load_config

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]

PROJECT_ROOT = Path(__file__).parent.parent


def _get_paths() -> tuple[Path, Path]:
    """Credentials- und Token-Pfade aus Config laden."""
    cfg = load_config().get("gmail", {})
    creds_path = PROJECT_ROOT / cfg.get("credentials_path", "config/credentials.json")
    token_path = PROJECT_ROOT / cfg.get("token_path", "config/token.json")
    return creds_path, token_path


def authenticate() -> Credentials:
    """Gmail OAuth2-Authentifizierung. Startet Browser-Flow falls noetig."""
    creds_path, token_path = _get_paths()

    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.is_file():
                raise FileNotFoundError(
                    f"credentials.json nicht gefunden: {creds_path}\n"
                    "Lade sie von der Google Cloud Console herunter."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return creds


def get_service():
    """Gmail API Service erstellen."""
    creds = authenticate()
    return build("gmail", "v1", credentials=creds)


# ---------------------------------------------------------------------------
# Entwuerfe erstellen (Phase 6)
# ---------------------------------------------------------------------------

def create_draft(to: str, subject: str, body: str) -> dict:
    """Gmail-Entwurf erstellen. Gibt Draft-Info zurueck."""
    service = get_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}},
    ).execute()

    return {
        "id": draft["id"],
        "to": to,
        "subject": subject,
    }


def create_reply_draft(thread_id: str, message_id: str, to: str, subject: str, body: str) -> dict:
    """Gmail-Entwurf als Antwort auf eine bestehende E-Mail erstellen."""
    service = get_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    message["In-Reply-To"] = message_id
    message["References"] = message_id

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={
            "message": {"raw": raw, "threadId": thread_id},
        },
    ).execute()

    return {
        "id": draft["id"],
        "to": to,
        "subject": subject,
        "thread_id": thread_id,
    }


def list_drafts(max_results: int = 10) -> list[dict]:
    """Gmail-Entwuerfe auflisten."""
    service = get_service()
    results = service.users().drafts().list(userId="me", maxResults=max_results).execute()
    drafts = results.get("drafts", [])

    draft_list = []
    for d in drafts:
        detail = service.users().drafts().get(userId="me", id=d["id"]).execute()
        headers = detail["message"]["payload"].get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(kein Betreff)")
        to = next((h["value"] for h in headers if h["name"] == "To"), "(kein Empfaenger)")
        draft_list.append({"id": d["id"], "subject": subject, "to": to})

    return draft_list


# ---------------------------------------------------------------------------
# Posteingang lesen (Phase 9)
# ---------------------------------------------------------------------------

def _decode_body(payload: dict) -> str:
    """E-Mail-Body aus Gmail-API-Payload dekodieren."""
    # Einfache Nachricht
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Multipart — text/plain suchen
    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

    # Fallback: text/html
    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")
        if mime == "text/html" and part.get("body", {}).get("data"):
            raw = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            # Grobe HTML-Bereinigung
            text = re.sub(r"<[^>]+>", " ", raw)
            text = re.sub(r"\s+", " ", text).strip()
            return text

    # Verschachtelte multipart
    for part in payload.get("parts", []):
        if part.get("parts"):
            result = _decode_body(part)
            if result:
                return result

    return ""


def _get_header(headers: list[dict], name: str) -> str:
    """Header-Wert aus Gmail-Header-Liste extrahieren."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def get_inbox_emails(max_results: int = 20, only_unread: bool = True) -> list[dict]:
    """Ungelesene E-Mails aus dem Posteingang abrufen."""
    service = get_service()

    query = "in:inbox"
    if only_unread:
        query += " is:unread"

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full",
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        body = _decode_body(msg.get("payload", {}))

        emails.append({
            "id": msg["id"],
            "thread_id": msg.get("threadId", ""),
            "message_id": _get_header(headers, "Message-ID"),
            "from": _get_header(headers, "From"),
            "to": _get_header(headers, "To"),
            "subject": _get_header(headers, "Subject"),
            "date": _get_header(headers, "Date"),
            "body": body,
            "snippet": msg.get("snippet", ""),
        })

    return emails


# ---------------------------------------------------------------------------
# Vorlagen lesen (Phase 9)
# ---------------------------------------------------------------------------

def _find_label_id(service, label_name: str) -> str | None:
    """Label-ID fuer einen Label-Namen finden."""
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"].lower() == label_name.lower():
            return label["id"]
    return None


def get_templates(label_name: str = None, min_year: int = None) -> list[dict]:
    """Gmail-Vorlagen (E-Mails mit bestimmtem Label) abrufen.

    Args:
        label_name: Gmail-Label unter dem Vorlagen gespeichert sind.
        min_year: Vorlagen mit Jahr < min_year im Betreff werden ignoriert.

    Returns:
        Liste von Vorlagen mit subject, body, id.
    """
    cfg = load_config().get("email_processing", {})
    if label_name is None:
        label_name = cfg.get("template_label", "Vorlagen")
    if min_year is None:
        min_year = cfg.get("min_template_year", 2025)

    service = get_service()

    label_id = _find_label_id(service, label_name)
    if not label_id:
        raise ValueError(
            f"Gmail-Label '{label_name}' nicht gefunden. "
            "Erstelle das Label in Gmail und verschiebe deine Vorlagen dorthin."
        )

    results = service.users().messages().list(
        userId="me", labelIds=[label_id], maxResults=100,
    ).execute()

    messages = results.get("messages", [])
    templates = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full",
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        subject = _get_header(headers, "Subject")
        body = _decode_body(msg.get("payload", {}))

        # Jahr-Filter: Vorlagen mit Jahr < min_year ignorieren
        years = re.findall(r"\b(20\d{2})\b", subject)
        if years:
            max_year_in_subject = max(int(y) for y in years)
            if max_year_in_subject < min_year:
                continue

        templates.append({
            "id": msg["id"],
            "subject": subject,
            "body": body,
        })

    return templates


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def is_authenticated() -> bool:
    """Pruefen ob bereits authentifiziert."""
    _, token_path = _get_paths()
    if not token_path.is_file():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        return creds.valid or (creds.expired and creds.refresh_token is not None)
    except Exception:
        return False


def has_credentials() -> bool:
    """Pruefen ob credentials.json vorhanden."""
    creds_path, _ = _get_paths()
    return creds_path.is_file()
