import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from .base import JobOffer, parse_date_iso, parse_date_rss

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}


def search_theprotocol(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    kw_enc = quote(keyword)
    url = f"https://theprotocol.it/filtry/oferty;searchText,{kw_enc}/rss"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź TheProtocol.it"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z TheProtocol.it: {e}"
    except ET.ParseError:
        return [], "Nieprawidłowa odpowiedź XML z TheProtocol.it"

    # obsługa namespace w RSS
    ns = {"dc": "http://purl.org/dc/elements/1.1/"}
    offers = []
    for item in root.findall(".//item")[:30]:
        title = _text(item, "title")
        link = _text(item, "link")

        # Próba wyciągnięcia firmy i lokalizacji z description
        desc = _text(item, "description")
        company, loc = _parse_desc(desc)
        if not loc and location:
            loc = location

        pub = _text(item, "pubDate")
        date = parse_date_rss(pub) if pub else parse_date_iso(_text(item, "date"))

        offers.append(JobOffer(
            title=title or "Brak tytułu",
            company=company or "Nieznana firma",
            location=loc or "Polska",
            salary=None,
            date_posted=date,
            apply_url=link or "#",
            source="TheProtocol.it",
        ))
    return offers, None


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _parse_desc(desc: str) -> tuple[str, str]:
    """Wyciąga firmę i lokalizację z HTML w description."""
    import re
    desc = re.sub(r"<[^>]+>", " ", desc)
    parts = [p.strip() for p in desc.split("|") if p.strip()]
    company = parts[0] if len(parts) > 0 else ""
    loc = parts[1] if len(parts) > 1 else ""
    return company, loc
