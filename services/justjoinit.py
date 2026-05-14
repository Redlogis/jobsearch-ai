import requests
import streamlit as st
from .base import JobOffer, parse_date_iso

# JustJoin.IT zmigrowało z /api/offers na v2 API
_V2_URL = "https://api.justjoin.it/v2/user-panel/offers"
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Version": "2",
}


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_all_offers() -> tuple[list[dict], str | None]:
    try:
        resp = requests.get(
            _V2_URL,
            params={"perPage": 100, "page": 1, "sortBy": "newest", "orderBy": "DESC"},
            headers=_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        # v2 zwraca {"data": [...]} lub bezpośrednio listę
        if isinstance(body, list):
            return body, None
        return body.get("data", body.get("offers", [])), None
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
        if kw in str(o.get("title", "")).lower()
        or kw in str(o.get("companyName", o.get("company_name", ""))).lower()
        or any(kw in str(s.get("name", "")).lower() for s in o.get("requiredSkills", o.get("skills", [])))
    ]

    offers = []
    for item in matched[:50]:
        salary = _format_salary(item)
        remote = item.get("remoteOnly", item.get("remote_only", False))
        city = item.get("city", "")
        slug = item.get("slug", item.get("id", ""))

        offers.append(JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("companyName", item.get("company_name", "Nieznana firma")),
            location="Zdalnie" if remote else city or "Nieznana lokalizacja",
            salary=salary,
            date_posted=parse_date_iso(item.get("publishedAt", item.get("published_at", ""))),
            apply_url=f"https://justjoin.it/offers/{slug}",
            source="JustJoin.IT",
        ))
    return offers, None


def _format_salary(item: dict) -> str | None:
    try:
        # v2 format: {"salary": {"from": ..., "to": ..., "currency": ...}}
        sal = item.get("salary") or {}
        if isinstance(sal, dict):
            lo = sal.get("from", sal.get("salaryFrom"))
            hi = sal.get("to", sal.get("salaryTo"))
            cur = sal.get("currency", "PLN") or "PLN"
        else:
            # stary format: pola bezpośrednio na obiekcie
            lo = item.get("salary_from")
            hi = item.get("salary_to")
            cur = item.get("salary_currency", "PLN") or "PLN"

        lo = int(lo) if lo else None
        hi = int(hi) if hi else None
        if lo and hi:
            return f"{lo:,} – {hi:,} {cur}".replace(",", " ")
        if lo:
            return f"od {lo:,} {cur}".replace(",", " ")
        if hi:
            return f"do {hi:,} {cur}".replace(",", " ")
    except (TypeError, ValueError, AttributeError):
        pass
    return None
