import requests
import streamlit as st
from .base import JobOffer, parse_date_iso


JUSTJOINIT_API_URL = "https://justjoin.it/api/offers"


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_all_offers() -> tuple[list[dict], str | None]:
    try:
        resp = requests.get(JUSTJOINIT_API_URL, headers={"Accept": "application/json"}, timeout=15)
        resp.raise_for_status()
        return resp.json(), None
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
        if kw in o.get("title", "").lower()
        or kw in o.get("company_name", "").lower()
        or any(kw in s.get("name", "").lower() for s in o.get("skills", []))
    ]

    offers = []
    for item in matched[:50]:
        sal_from = item.get("salary_from")
        sal_to = item.get("salary_to")
        cur = item.get("salary_currency", "PLN")
        if sal_from and sal_to:
            salary = f"{sal_from:,} – {sal_to:,} {cur}".replace(",", " ")
        elif sal_from:
            salary = f"od {sal_from:,} {cur}".replace(",", " ")
        elif sal_to:
            salary = f"do {sal_to:,} {cur}".replace(",", " ")
        else:
            salary = None

        remote = item.get("remote_only", False)
        city = item.get("city", "")

        offers.append(JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("company_name", "Nieznana firma"),
            location="Zdalnie" if remote else city or "Nieznana lokalizacja",
            salary=salary,
            date_posted=parse_date_iso(item.get("published_at", "")),
            apply_url=f"https://justjoin.it/offers/{item.get('id', '')}",
            source="JustJoin.IT",
        ))
    return offers, None
