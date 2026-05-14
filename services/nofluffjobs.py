import requests
from urllib.parse import quote
from .base import JobOffer, parse_date_iso

API_URL = "https://nofluffjobs.com/api/posting"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "pl-PL,pl;q=0.9",
}


def search_nofluffjobs(keyword: str) -> tuple[list[JobOffer], str | None]:
    # criteria musi być bez podwójnego kodowania
    params = {
        "criteria": f"keyword%3D{quote(keyword)}",
        "salaryCurrency": "PLN",
        "salaryPeriod": "month",
        "region": "pl",
    }
    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź NoFluffJobs"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z NoFluffJobs: {e}"
    except ValueError:
        return [], "Nieprawidłowa odpowiedź z NoFluffJobs"

    offers = []
    for item in data.get("postings", [])[:30]:
        try:
            salary = _format_salary(item.get("salary"))
            location = _format_location(item.get("location") or {})
            url_raw = item.get("url") or item.get("id") or ""
            url_slug = str(url_raw)
            apply_url = url_slug if url_slug.startswith("http") else f"https://nofluffjobs.com/pl/praca/{url_slug}"
            company_raw = item.get("company") or {}
            company = company_raw.get("name", "Nieznana firma") if isinstance(company_raw, dict) else str(company_raw)

            offers.append(JobOffer(
                title=item.get("name", "Brak tytułu"),
                company=company,
                location=location,
                salary=salary,
                date_posted=parse_date_iso(str(item.get("posted", ""))),
                apply_url=apply_url,
                source="NoFluffJobs",
            ))
        except Exception:
            continue

    return offers, None


def _format_salary(sal) -> str | None:
    if not sal or not isinstance(sal, dict):
        return None
    try:
        lo = sal.get("from") or sal.get("min")
        hi = sal.get("to") or sal.get("max")
        cur = str(sal.get("currency") or "PLN")
        lo = int(lo) if lo is not None else None
        hi = int(hi) if hi is not None else None
        if lo and hi:
            return f"{lo:,} – {hi:,} {cur}".replace(",", " ")
        if lo:
            return f"od {lo:,} {cur}".replace(",", " ")
        if hi:
            return f"do {hi:,} {cur}".replace(",", " ")
    except (TypeError, ValueError):
        pass
    return None


def _format_location(loc: dict) -> str:
    try:
        if loc.get("fullyRemote"):
            return "Zdalnie"
        places = loc.get("places") or []
        cities = [p.get("city", "") for p in places if isinstance(p, dict) and p.get("city")]
        return ", ".join(cities[:2]) if cities else "Nieznana lokalizacja"
    except (AttributeError, TypeError):
        return "Nieznana lokalizacja"
