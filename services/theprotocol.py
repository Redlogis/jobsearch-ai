import requests
import xml.etree.ElementTree as ET
import re
from urllib.parse import quote
from .base import JobOffer, parse_date_iso, parse_date_rss

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
    "Referer": "https://theprotocol.it/",
}

_RSS_CANDIDATES = [
    "https://theprotocol.it/filtry/oferty;searchText,{kw}/rss",
    "https://theprotocol.it/praca;searchText,{kw}/rss",
    "https://theprotocol.it/oferty-pracy;searchText,{kw}/rss",
]


def search_theprotocol(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    kw_enc = quote(keyword)
    root = None
    last_err = ""

    session = requests.Session()
    session.headers.update(HEADERS)
    # Pobierz ciasteczka ze strony głównej
    try:
        session.get("https://theprotocol.it/", timeout=8)
    except Exception:
        pass

    for tpl in _RSS_CANDIDATES:
        url = tpl.format(kw=kw_enc)
        try:
            resp = session.get(url, timeout=12)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                break
            last_err = f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            last_err = str(e)
        except ET.ParseError:
            last_err = "Nieprawidłowy XML"

    if root is None:
        return [], f"Nie można pobrać feedu TheProtocol.it: {last_err}"

    offers = []
    for item in root.findall(".//item")[:30]:
        title = _text(item, "title")
        link = _text(item, "link")
        desc = _text(item, "description")
        company, loc = _parse_desc(desc)
        if not loc and location:
            loc = location
        pub = _text(item, "pubDate")
        date = parse_date_rss(pub) if pub else None

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
    clean = re.sub(r"<[^>]+>", " ", desc).strip()
    parts = [p.strip() for p in re.split(r"[|,·]", clean) if p.strip()]
    return (parts[0] if parts else ""), (parts[1] if len(parts) > 1 else "")
