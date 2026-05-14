import requests
import xml.etree.ElementTree as ET
from .base import JobOffer, parse_date_rss

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}
RSS_URL = "https://bulldogjob.pl/companies/jobs/feed"


def search_bulldogjob(keyword: str) -> tuple[list[JobOffer], str | None]:
    try:
        resp = requests.get(RSS_URL, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź Bulldogjob"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z Bulldogjob: {e}"
    except ET.ParseError:
        return [], "Nieprawidłowa odpowiedź XML z Bulldogjob"

    kw = keyword.lower()
    offers = []
    for item in root.findall(".//item"):
        title = _text(item, "title")
        desc = _text(item, "description").lower()
        if kw not in title.lower() and kw not in desc:
            continue

        # Bulldogjob RSS: title format "Rola @ Firma"
        if " @ " in title:
            role, company = title.split(" @ ", 1)
        else:
            role, company = title, ""

        category = _text(item, "category")

        offers.append(JobOffer(
            title=role.strip(),
            company=company.strip() or "Nieznana firma",
            location=category or "Polska",
            salary=None,
            date_posted=parse_date_rss(_text(item, "pubDate")),
            apply_url=_text(item, "link") or "#",
            source="Bulldogjob",
        ))
        if len(offers) >= 30:
            break

    return offers, None


def _text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""
