import requests
import streamlit as st
from .base import JobOffer, parse_date_iso

_URL = "https://justjoin.it/api/offers"
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_all_offers() -> tuple[list[dict], str | None]:
    try:
        resp = requests.get(_URL, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            return [], "Nieoczekiwany format odpowiedzi JustJoin.IT"
        return data, None
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź JustJoin.IT"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z JustJoin.IT: {e}"
    except ValueError:
        return [], "Nieprawidłowa odpowiedź z JustJoin.IT"


def search_justjoinit(keyword: str) -> tuple[list[JobOffer], str | None]:
    raw_offers, error = _fetch_all_offers()
    if error:
        return [], error

    kw = keyword.lower()
    matched = [
        o for o in raw_offers
        if isinstance(o, dict) and (
            kw in str(o.get("title", "")).lower()
            or kw in str(o.get("companyName", "")).lower()
            or kw in str(o.get("marker_icon", "")).lower()
        )
    ]

    offers = []
    for item in matched[:50]:
        salary_from = item.get("salary_from")
        salary_to = item.get("salary_to")
        currency = item.get("currency", "PLN") or "PLN"
        try:
            lo = int(salary_from) if salary_from else None
            hi = int(salary_to) if salary_to else None
        except (TypeError, ValueError):
            lo = hi = None

        if lo and hi:
            salary = f"{lo:,} – {hi:,} {currency}".replace(",", " ")
        elif lo:
            salary = f"od {lo:,} {currency}".replace(",", " ")
        else:
            salary = None

        offer_id = item.get("id", "")
        offers.append(JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("companyName", "Nieznana firma"),
            location=item.get("city") or "Zdalnie",
            salary=salary,
            date_posted=parse_date_iso(item.get("publishedAt", "")),
            apply_url=f"https://justjoin.it/offers/{offer_id}",
            source="JustJoin.IT",
        ))

    return offers, None
