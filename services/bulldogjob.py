import requests
import xml.etree.ElementTree as ET
from .base import JobOffer, parse_date_rss

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# Bulldogjob zmienił URL feeda — próbujemy kolejno
_RSS_CANDIDATES = [
    "https://bulldogjob.pl/feed/jobs",
    "https://bulldogjob.pl/jobs.rss",
    "https://bulldogjob.pl/news/feeds/job_feed.rss",
    "https://bulldogjob.pl/companies/jobs.rss",
]


def search_bulldogjob(keyword: str) -> tuple[list[JobOffer], str | None]:
    root = None
    last_err = ""
    for url in _RSS_CANDIDATES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                break
        except requests.exceptions.RequestException as e:
            last_err = str(e)
        except ET.ParseError:
            last_err = "Nieprawidłowy XML"

    if root is None:
        return [], f"Nie można pobrać feedu Bulldogjob: {last_err}"

    kw = keyword.lower()
    offers = []
    for item in root.findall(".//item"):
        title = _text(item, "title")
        desc = _text(item, "description").lower()
        if kw not in title.lower() and kw not in desc:
            continue

        role, company = (title.split(" @ ", 1) + [""])[:2] if " @ " in title else (title, "")
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
