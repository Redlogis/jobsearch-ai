import requests
import xml.etree.ElementTree as ET
from typing import Optional
from .base import JobOffer, parse_date_rss

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}


def search_pracuj(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    kw_slug = keyword.replace(" ", "+")
    loc_part = f";wp,{location.replace(' ', '+')}" if location else ""
    url = f"https://www.pracuj.pl/praca/{kw_slug};kw{loc_part}.rss"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź Pracuj.pl"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z Pracuj.pl: {e}"
    except ET.ParseError:
        return [], "Nieprawidłowa odpowiedź XML z Pracuj.pl"

    offers = []
    for item in root.findall(".//item")[:30]:
        title_raw = _text(item, "title")
        title, company, loc_parsed = _split_title(title_raw)
        if not loc_parsed and location:
            loc_parsed = location

        offers.append(JobOffer(
            title=title,
            company=company,
            location=loc_parsed or "Polska",
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
    """Pracuj.pl tytuły: 'Stanowisko – Firma – Miasto' lub 'Stanowisko - Firma - Miasto'."""
    for sep in (" – ", " - "):
        parts = [p.strip() for p in raw.split(sep) if p.strip()]
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return parts[0], parts[1], ""
    return raw, "", ""
