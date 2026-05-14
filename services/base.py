from dataclasses import dataclass
from typing import Optional


@dataclass
class JobOffer:
    title: str
    company: str
    location: str
    salary: Optional[str]
    date_posted: Optional[str]
    apply_url: str
    source: str


SOURCE_STYLES: dict[str, dict] = {
    "JustJoin.IT": {"bg": "#3B1F5E", "text": "#C084FC"},
    "Jooble":      {"bg": "#1E3A5F", "text": "#60A5FA"},
    "NoFluffJobs": {"bg": "#7F1D1D", "text": "#F87171"},
    "Adzuna":      {"bg": "#1C3557", "text": "#38BDF8"},
}


def parse_date_rss(raw: str) -> Optional[str]:
    """Parse RFC 2822 date (used in RSS pubDate)."""
    if not raw:
        return None
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(raw).strftime("%d.%m.%Y")
    except Exception:
        return raw[:10] if len(raw) >= 10 else raw


def parse_date_iso(raw: str) -> Optional[str]:
    """Parse ISO 8601 date."""
    if not raw:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return raw[:10] if len(raw) >= 10 else raw
