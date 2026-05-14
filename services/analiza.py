import json
import re
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "data" / "stanowiska.json"

_ALIASES: dict[str, str] = {
    "programista": "programista python",
    "developer": "programista python",
    "deweloper": "programista python",
    "backend": "programista python",
    "python": "programista python",
    "java": "programista python",
    "frontend": "programista javascript",
    "js": "programista javascript",
    "javascript": "programista javascript",
    "react": "programista javascript",
    "analityk": "analityk danych",
    "data analyst": "analityk danych",
    "data": "analityk danych",
    "bi": "analityk danych",
    "logistyk": "logistyk",
    "logistyka": "logistyk",
    "supply chain": "logistyk",
    "scm": "logistyk",
    "magazyn": "magazynier",
    "operator": "magazynier",
    "hr": "specjalista hr",
    "rekruter": "specjalista hr",
    "recruiter": "specjalista hr",
    "zasoby ludzkie": "specjalista hr",
    "sprzedawca": "sprzedawca",
    "handlowiec": "sprzedawca",
    "przedstawiciel": "sprzedawca",
    "sales": "sprzedawca",
    "pm": "project manager",
    "kierownik projektu": "project manager",
    "scrum master": "project manager",
    "agile": "project manager",
    "ksiegowy": "ksiegowy",
    "ksiegowa": "ksiegowy",
    "księgowy": "ksiegowy",
    "finanse": "ksiegowy",
    "accountant": "ksiegowy",
    "grafik": "grafik",
    "graphic designer": "grafik",
    "designer": "grafik",
    "ux": "grafik",
    "ui": "grafik",
    "marketing": "specjalista marketingu",
    "marketer": "specjalista marketingu",
    "seo": "specjalista marketingu",
    "sem": "specjalista marketingu",
    "ppc": "specjalista marketingu",
    "kierowca": "kierowca",
    "driver": "kierowca",
    "tir": "kierowca",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[/\\()\[\]]", " ", text)
    return re.sub(r"\s+", " ", text)


def find_stanowisko(query: str) -> dict | None:
    with open(_DB_PATH, encoding="utf-8") as f:
        db = json.load(f)["stanowiska"]

    q = _normalize(query)

    if q in db:
        return db[q]

    for alias, key in _ALIASES.items():
        if alias in q and key in db:
            return db[key]

    for key, data in db.items():
        if key in q or q in key:
            return data

    for key, data in db.items():
        parts = key.split()
        if any(p in q for p in parts if len(p) > 3):
            return data

    return None


def list_stanowiska() -> list[str]:
    with open(_DB_PATH, encoding="utf-8") as f:
        db = json.load(f)["stanowiska"]
    return [v["nazwa"] for v in db.values()]
