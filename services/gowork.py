import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
from .base import JobOffer, parse_date_rss

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}


def search_gowork(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    kw_slug = quote(keyword.replace(" ", "-").lower())
    loc_slug = f"/{quote(location.replace(' ', '-').lower())}" if location else ""
    url = f"https://www.gowork.pl/praca{loc_slug}/{kw_slug}.rss"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź GoWork"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z GoWork: {e}"
    except ET.ParseError:
        return [], "Nieprawidłowa odpowiedź XML z GoWork"

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
            source="GoWork",
        ))
    return offers, None


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _split_title(raw: str) -> tuple[str, str, str]:
    for sep in (" – ", " - ", " | "):
        parts = [p.strip() for p in raw.split(sep) if p.strip()]
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return parts[0], parts[1], ""
    return raw, "", ""
