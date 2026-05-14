import requests
from urllib.parse import quote
from .base import JobOffer, parse_date_iso

API_URL = "https://nofluffjobs.com/api/posting"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobSearchBot/1.0)"}


def search_nofluffjobs(keyword: str) -> tuple[list[JobOffer], str | None]:
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
        salary = _format_salary(item.get("salary"))
        location = _format_location(item.get("location", {}))
        url_slug = item.get("url", item.get("id", ""))
        if not url_slug.startswith("http"):
            url_slug = f"https://nofluffjobs.com/pl/praca/{url_slug}"

        offers.append(JobOffer(
            title=item.get("name", "Brak tytułu"),
            company=item.get("company", {}).get("name", "Nieznana firma"),
            location=location,
            salary=salary,
            date_posted=parse_date_iso(item.get("posted", "")),
            apply_url=url_slug,
            source="NoFluffJobs",
        ))
    return offers, None


def _format_salary(sal: dict | None) -> str | None:
    if not sal:
        return None
    lo = sal.get("from")
    hi = sal.get("to")
    cur = sal.get("currency", "PLN")
    if lo and hi:
        return f"{lo:,} – {hi:,} {cur}".replace(",", " ")
    if lo:
        return f"od {lo:,} {cur}".replace(",", " ")
    if hi:
        return f"do {hi:,} {cur}".replace(",", " ")
    return None


def _format_location(loc: dict) -> str:
    if loc.get("fullyRemote"):
        return "Zdalnie"
    places = loc.get("places", [])
    cities = [p.get("city", "") for p in places if p.get("city")]
    return ", ".join(cities[:2]) if cities else "Nieznana lokalizacja"
