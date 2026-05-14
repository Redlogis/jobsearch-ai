import requests
from dataclasses import dataclass
from typing import Optional
import streamlit as st

JUSTJOINIT_API_URL = "https://justjoin.it/api/offers"


@dataclass
class JobOffer:
    title: str
    company: str
    location: str
    salary: Optional[str]
    date_posted: Optional[str]
    apply_url: str
    source: str


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_all_offers() -> tuple[list[dict], str | None]:
    try:
        resp = requests.get(
            JUSTJOINIT_API_URL,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź JustJoin.IT API"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z JustJoin.IT API: {e}"
    except ValueError:
        return [], "Nieprawidłowa odpowiedź z JustJoin.IT API"


def search_justjoinit(keyword: str) -> tuple[list[JobOffer], str | None]:
    raw_offers, error = _fetch_all_offers()
    if error:
        return [], error

    kw_lower = keyword.lower()
    matched = [
        o for o in raw_offers
        if kw_lower in o.get("title", "").lower()
        or kw_lower in o.get("company_name", "").lower()
        or any(kw_lower in s.get("name", "").lower() for s in o.get("skills", []))
    ]

    offers = []
    for item in matched[:50]:
        salary = _format_salary(item)
        city = item.get("city", "")
        remote = item.get("remote_only", False)
        location = "Zdalnie" if remote else city or "Nieznana lokalizacja"

        offer = JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("company_name", "Nieznana firma"),
            location=location,
            salary=salary,
            date_posted=_parse_date(item.get("published_at", "")),
            apply_url=f"https://justjoin.it/offers/{item.get('id', '')}",
            source="JustJoin.IT",
        )
        offers.append(offer)

    return offers, None


def _format_salary(item: dict) -> Optional[str]:
    sal_from = item.get("salary_from")
    sal_to = item.get("salary_to")
    currency = item.get("salary_currency", "PLN")
    if sal_from and sal_to:
        return f"{sal_from:,} – {sal_to:,} {currency}".replace(",", " ")
    if sal_from:
        return f"od {sal_from:,} {currency}".replace(",", " ")
    if sal_to:
        return f"do {sal_to:,} {currency}".replace(",", " ")
    return None


def _parse_date(raw: str) -> Optional[str]:
    if not raw:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return raw[:10] if len(raw) >= 10 else raw
