import os
import requests
from dataclasses import dataclass
from typing import Optional

JOOBLE_API_URL = "https://pl.jooble.org/api/{key}"


@dataclass
class JobOffer:
    title: str
    company: str
    location: str
    salary: Optional[str]
    date_posted: Optional[str]
    apply_url: str
    source: str


def search_jooble(keyword: str, location: str = "") -> tuple[list[JobOffer], str | None]:
    api_key = os.getenv("JOOBLE_API_KEY", "")
    if not api_key or api_key == "twoj_klucz_api_tutaj":
        return [], "Brak klucza API Jooble. Dodaj JOOBLE_API_KEY do pliku .env"

    url = JOOBLE_API_URL.format(key=api_key)
    payload = {"keywords": keyword, "location": location}

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return [], "Przekroczono czas oczekiwania na odpowiedź Jooble API"
    except requests.exceptions.RequestException as e:
        return [], f"Błąd połączenia z Jooble API: {e}"
    except ValueError:
        return [], "Nieprawidłowa odpowiedź z Jooble API"

    offers = []
    for item in data.get("jobs", []):
        salary = item.get("salary", "").strip() or None

        offer = JobOffer(
            title=item.get("title", "Brak tytułu"),
            company=item.get("company", "Nieznana firma"),
            location=item.get("location", "Nieznana lokalizacja"),
            salary=salary,
            date_posted=_parse_date(item.get("updated", "")),
            apply_url=item.get("link", "#"),
            source="Jooble",
        )
        offers.append(offer)

    return offers, None


def _parse_date(raw: str) -> Optional[str]:
    if not raw:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return raw[:10] if len(raw) >= 10 else raw
