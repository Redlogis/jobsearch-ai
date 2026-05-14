import os
import requests
from .base import JobOffer, parse_date_iso


ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/pl/search/1"


def search_adzuna(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    app_id = os.getenv("ADZUNA_APP_ID", "166f4596")
    app_key = os.getenv("ADZUNA_APP_KEY", "c66c15bfae9938c23e38f2a6cdec67e9")

    params: dict = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 20,
        "what": keyword,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location

    try:
        resp = requests.get(ADZUNA_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź Adzuna API"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z Adzuna API: {e}"
    except ValueError:
        return [], "Nieprawidłowa odpowiedź z Adzuna API"

    offers = []
    for item in data.get("results", []):
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")
        if salary_min and salary_max:
            salary = f"{int(salary_min):,} – {int(salary_max):,} PLN".replace(",", " ")
        elif salary_min:
            salary = f"od {int(salary_min):,} PLN".replace(",", " ")
        else:
            salary = None

        offers.append(JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("company", {}).get("display_name", "Nieznana firma"),
            location=item.get("location", {}).get("display_name", "Nieznana lokalizacja"),
            salary=salary,
            date_posted=parse_date_iso(item.get("created", "")),
            apply_url=item.get("redirect_url", "#"),
            source="Adzuna",
        ))

    return offers, None
