import os
import requests
from .base import JobOffer, parse_date_iso


JOOBLE_API_URL = "https://pl.jooble.org/api/{key}"


def search_jooble(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    api_key = os.getenv("JOOBLE_API_KEY", "")
    if not api_key or api_key == "twoj_klucz_api_tutaj":
        return [], "Brak klucza API Jooble. Dodaj JOOBLE_API_KEY do pliku .env"

    url = JOOBLE_API_URL.format(key=api_key)
    try:
        resp = requests.post(url, json={"keywords": keyword, "location": location}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź Jooble API"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z Jooble API: {e}"
    except ValueError:
        return [], "Nieprawidłowa odpowiedź z Jooble API"

    offers = [
        JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("company", "Nieznana firma"),
            location=item.get("location", "Nieznana lokalizacja"),
            salary=item.get("salary", "").strip() or None,
            date_posted=parse_date_iso(item.get("updated", "")),
            apply_url=item.get("link", "#"),
            source="Jooble",
        )
        for item in data.get("jobs", [])
    ]
    return offers, None
