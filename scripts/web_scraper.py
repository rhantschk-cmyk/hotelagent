"""HotelAgent — Web-Scraper: Website crawlen und Wissen extrahieren."""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from rich.console import Console

from scripts.documents import save_to_knowledge
from scripts.llm import llm_call

console = Console()


def crawl_site(base_url: str, max_pages: int = 30) -> dict[str, str]:
    """Website crawlen und Text aller Seiten extrahieren."""
    visited = set()
    pages = {}
    to_visit = [base_url]
    domain = urlparse(base_url).netloc

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "HotelAgent/1.0"})
            if resp.status_code != 200 or "text/html" not in resp.headers.get("content-type", ""):
                visited.add(url)
                continue
        except Exception:
            visited.add(url)
            continue

        visited.add(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Unnoetige Elemente entfernen
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Mehrfache Leerzeilen reduzieren
        text = re.sub(r"\n{3,}", "\n\n", text)

        if text.strip():
            # Seitentitel ermitteln
            title = soup.title.string.strip() if soup.title and soup.title.string else url
            pages[url] = f"# {title}\n\n{text}"
            console.print(f"  [green]OK[/green] {url} ({len(text)} Zeichen)")

        # Links auf derselben Domain finden
        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            href = href.split("#")[0].split("?")[0]  # Fragment/Query entfernen
            if urlparse(href).netloc == domain and href not in visited:
                to_visit.append(href)

    return pages


def analyze_website(pages: dict[str, str]) -> str:
    """Alle gecrawlten Seiten durch LLM analysieren."""
    # Alle Seiten zusammenfuegen
    combined = "\n\n---\n\n".join(pages.values())

    # Kuerzen falls zu lang
    max_chars = 30000
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n[... gekuerzt ...]"

    analysis = llm_call(
        messages=[
            {"role": "system", "content": (
                "Du analysierst die Website eines Hotels. Erstelle eine umfassende, strukturierte Zusammenfassung mit:\n"
                "1. **Allgemeine Infos**: Name, Standort, Beschreibung, Kontaktdaten\n"
                "2. **Zimmer & Preise**: Zimmertypen, Ausstattung, Preisbereiche\n"
                "3. **Gastronomie**: Restaurants, Bars, Speiseangebote\n"
                "4. **Wellness & Freizeit**: Spa, Pool, Aktivitaeten\n"
                "5. **Veranstaltungen**: Tagungsraeume, Events, Feiern\n"
                "6. **Besonderheiten**: Alleinstellungsmerkmale, Auszeichnungen\n"
                "7. **Buchung & Anreise**: Buchungsinfos, Anfahrt, Parken\n\n"
                "Schreibe alles auf Deutsch. Sei gruendlich und behalte alle konkreten Details (Preise, Zimmernamen, Oeffnungszeiten etc.)."
            )},
            {"role": "user", "content": combined},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    # Preise automatisch extrahieren und in PRICES.md speichern
    try:
        from scripts.price_manager import extract_prices_from_text, save_to_prices
        console.print("[dim]Extrahiere Preise...[/dim]")
        prices = extract_prices_from_text(combined, source_name=f"Website: {list(pages.keys())[0] if pages else 'unbekannt'}")
        if prices.strip():
            source = list(pages.keys())[0].split("/")[2] if pages else "website"
            save_to_prices(f"Website: {source}", prices)
            console.print("[green]Preise in PRICES.md gespeichert.[/green]")
    except Exception as e:
        console.print(f"[yellow]Preis-Extraktion fehlgeschlagen: {e}[/yellow]")

    return analysis
