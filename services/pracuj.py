import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from .base import JobOffer, parse_date_rss

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9",
    "Referer": "https://www.pracuj.pl/",
}

_RSS_CANDIDATES = [
    "https://www.pracuj.pl/praca/{kw};kw{loc}.rss",
    "https://www.pracuj.pl/praca.rss?q={kw_raw}",
]


def search_pracuj(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    kw = quote(keyword.replace(" ", "+"))
    loc_part = f";wp,{quote(location.replace(' ', '+'))}" if location else ""

    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://www.pracuj.pl/", timeout=8)
    except Exception:
        pass

    root = None
    last_err = ""
    for tpl in _RSS_CANDIDATES:
        url = tpl.format(kw=kw, loc=loc_part, kw_raw=quote(keyword))
        try:
            resp = session.get(url, timeout=12)
            if resp.status_code == 200 and b"<rss" in resp.content[:500]:
                root = ET.fromstring(resp.content)
                break
            last_err = f"HTTP {resp.status_code}"
        except requests.exceptions.RequestException as e:
            last_err = str(e)
        except ET.ParseError:
            last_err = "Nieprawidłowy XML"

    if root is None:
        return [], f"Nie można pobrać feedu Pracuj.pl: {last_err}"

    offers = []
    for item in root.findall(".//item")[:30]:
        title_raw = _text(item, "title")
        title, company, loc = _split_title(title_raw)
        if not loc and location:
            loc = location

        offers.append(JobOffer(
            title=title or "Brak tytułu",
            company=company or "Nieznana firma",
            location=loc or "Polska",
            salary=None,
            date_posted=parse_date_rss(_text(item, "pubDate")),
            apply_url=_text(item, "link") or "#",
            source="Pracuj.pl",
        ))
    return offers, None


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _split_title(raw: str) -> tuple[str, str, str]:
    for sep in (" – ", " - "):
        parts = [p.strip() for p in raw.split(sep) if p.strip()]
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return parts[0], parts[1], ""
    return raw, "", ""
