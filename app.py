import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from services.base import SOURCE_STYLES
from services.analiza import find_stanowisko, list_stanowiska
from services.jooble import search_jooble
from services.justjoinit import search_justjoinit
from services.nofluffjobs import search_nofluffjobs
from services.adzuna import search_adzuna

st.set_page_config(
    page_title="PracaRadar",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0F172A; }
[data-testid="stHeader"] { background-color: transparent; }

.job-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 14px;
    transition: border-color 0.2s;
}
.job-card:hover { border-color: #2563EB; }
.job-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #F1F5F9;
    margin: 0 0 3px 0;
}
.job-company {
    font-size: 0.9rem;
    color: #94A3B8;
    margin: 0 0 10px 0;
}
.job-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.82rem;
    margin-bottom: 12px;
    color: #CBD5E1;
}
.salary-badge {
    background: #14532D;
    color: #4ADE80;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.82rem;
}
.source-badge {
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
}
.apply-btn {
    display: inline-block;
    background: #2563EB;
    color: #ffffff !important;
    padding: 6px 16px;
    border-radius: 8px;
    text-decoration: none !important;
    font-size: 0.85rem;
    font-weight: 600;
}
.apply-btn:hover { background: #1D4ED8; }
.stats-bar {
    background: #1E293B;
    border-radius: 10px;
    padding: 10px 18px;
    margin-bottom: 18px;
    color: #94A3B8;
    font-size: 0.88rem;
}
[data-testid="stTextInput"] input {
    background-color: #1E293B !important;
    border-color: #334155 !important;
    color: #F1F5F9 !important;
}
hr { border-color: #334155; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📡 PracaRadar")
st.markdown(
    "<p style='color:#94A3B8;margin-top:-8px;margin-bottom:20px;'>"
    "Twój radar na rynku pracy &nbsp;·&nbsp; 4 źródła jednocześnie</p>",
    unsafe_allow_html=True,
)

tab_search, tab_analysis, tab_info = st.tabs(["🔍 Wyszukiwarka ofert pracy", "🤖 Analiza stanowiska", "ℹ️ O aplikacji"])

with tab_search:
    col_kw, col_loc, col_btn = st.columns([3, 2, 1])
    with col_kw:
        keyword = st.text_input(
            "Słowo kluczowe",
            placeholder="np. logistyk, programista Python, analityk...",
            label_visibility="collapsed",
        )
    with col_loc:
        location = st.text_input(
            "Lokalizacja",
            placeholder="Lokalizacja (np. Warszawa)",
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button("🔍 Szukaj", type="primary", use_container_width=True)

    with st.expander("⚙️ Ustawienia", expanded=False):
        src_cols = st.columns(4)
        all_sources = list(SOURCE_STYLES.keys())
        selected: list[str] = []
        for i, src in enumerate(all_sources):
            with src_cols[i % 4]:
                if st.checkbox(src, value=True, key=f"src_{src}"):
                    selected.append(src)

        st.markdown("---")
        jooble_key = st.text_input(
            "Klucz API Jooble",
            placeholder="Wklej klucz z jooble.org/api/about",
            type="password",
            help="Bezpłatny klucz API dostępny na jooble.org/api/about",
        )

    st.markdown("---")

    if search_clicked:
        if not keyword.strip():
            st.warning("Wpisz słowo kluczowe, aby rozpocząć wyszukiwanie.")
        elif not selected:
            st.warning("Wybierz co najmniej jedno źródło.")
        else:
            kw = keyword.strip()
            loc = location.strip()

            search_fns = {
                "JustJoin.IT": lambda: search_justjoinit(kw),
                "Jooble":      lambda: search_jooble(kw, loc, jooble_key),
                "NoFluffJobs": lambda: search_nofluffjobs(kw),
                "Adzuna":      lambda: search_adzuna(kw, loc),
            }

            results: dict[str, tuple] = {}
            progress = st.progress(0, text="Szukam ofert pracy...")

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(search_fns[src]): src
                    for src in selected if src in search_fns
                }
                done = 0
                for future in as_completed(futures):
                    src = futures[future]
                    try:
                        results[src] = future.result()
                    except Exception:
                        results[src] = ([], None)
                    done += 1
                    progress.progress(done / len(futures), text=f"Pobrano: {src}")

            progress.empty()

            for src in selected:
                _, err = results.get(src, ([], None))
                if err and src in ("JustJoin.IT", "Jooble", "NoFluffJobs", "Adzuna"):
                    st.info(f"**{src}:** {err}", icon="ℹ️")

            all_offers = [
                offer
                for src in selected
                for offer in results.get(src, ([], None))[0]
            ]

            if not all_offers:
                st.markdown(
                    "<div style='text-align:center;padding:60px 0;color:#64748B;'>"
                    "<div style='font-size:3rem;'>🔎</div>"
                    "<div style='font-size:1.1rem;margin-top:12px;'>Nie znaleziono ofert dla frazy "
                    f"<strong style='color:#94A3B8;'>&#8222;{kw}&#8221;</strong></div>"
                    "<div style='margin-top:8px;font-size:0.9rem;'>Spróbuj innego słowa kluczowego</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                counts = {src: len(results.get(src, ([], None))[0]) for src in selected}
                def _src_span(s: str) -> str:
                    col = SOURCE_STYLES[s]["text"]
                    return f"<span style='color:{col}'>{counts[s]} {s}</span>"
                count_html = " &nbsp;·&nbsp; ".join(
                    _src_span(s) for s in selected if counts.get(s, 0) > 0
                )
                st.markdown(
                    f"<div class='stats-bar'>Znaleziono <strong style='color:#F1F5F9;'>"
                    f"{len(all_offers)}</strong> ofert &nbsp;—&nbsp; {count_html}</div>",
                    unsafe_allow_html=True,
                )

                for offer in all_offers:
                    style = SOURCE_STYLES.get(offer.source, {"bg": "#1E293B", "text": "#94A3B8"})
                    salary_html = (
                        f"<span class='salary-badge'>💰 {offer.salary}</span>"
                        if offer.salary else ""
                    )
                    date_html = f"<span>📅 {offer.date_posted}</span>" if offer.date_posted else ""
                    st.markdown(f"""
<div class="job-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
    <div>
      <div class="job-title">{offer.title}</div>
      <div class="job-company">🏢 {offer.company}</div>
    </div>
    <span class="source-badge" style="background:{style['bg']};color:{style['text']}">
      {offer.source}
    </span>
  </div>
  <div class="job-meta">
    <span>📍 {offer.location}</span>
    {date_html}
    {salary_html}
  </div>
  <a class="apply-btn" href="{offer.apply_url}" target="_blank" rel="noopener noreferrer">Aplikuj →</a>
</div>""", unsafe_allow_html=True)

    else:
        st.markdown(
            "<div style='text-align:center;padding:60px 0;color:#64748B;'>"
            "<div style='font-size:4rem;'>💼</div>"
            "<div style='font-size:1.15rem;margin-top:16px;color:#94A3B8;'>"
            "Wpisz słowo kluczowe i kliknij <strong>Szukaj</strong></div>"
            "<div style='margin-top:8px;font-size:0.9rem;'>"
            "Np. <em>logistyk</em>, <em>programista Python</em>, <em>analityk danych</em></div>"
            "</div>",
            unsafe_allow_html=True,
        )

_WAGA_COLOR = {
    "Kluczowa": "#4ADE80",
    "Wysoka":   "#60A5FA",
    "Średnia":  "#FBBF24",
    "Ważna":    "#FBBF24",
    "Przydatna":"#94A3B8",
}

with tab_analysis:
    st.markdown("### 📊 Analiza stanowiska pracy")
    st.markdown(
        "<p style='color:#94A3B8;margin-top:-8px;margin-bottom:20px;'>"
        "Wpisz nazwę stanowiska i sprawdź zarobki, wymagane umiejętności i wskazówki rekrutacyjne</p>",
        unsafe_allow_html=True,
    )

    available = list_stanowiska()
    col_pos, col_abtn = st.columns([4, 1])
    with col_pos:
        position_name = st.text_input(
            "Stanowisko",
            placeholder="np. programista Python, logistyk, analityk danych, HR...",
            label_visibility="collapsed",
            key="position_input",
        )
    with col_abtn:
        analyze_clicked = st.button("🔎 Analizuj", type="primary", use_container_width=True)

    st.markdown(
        "<p style='color:#475569;font-size:0.8rem;margin-top:4px;'>Dostępne stanowiska: "
        + ", ".join(f"<em>{n}</em>" for n in available) + "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    if analyze_clicked:
        if not position_name.strip():
            st.warning("Wpisz nazwę stanowiska, aby rozpocząć analizę.")
        else:
            dane = find_stanowisko(position_name.strip())
            if dane is None:
                st.error(
                    f"Nie znaleziono danych dla stanowiska **{position_name.strip()}**. "
                    "Spróbuj innej nazwy lub skorzystaj z listy dostępnych stanowisk powyżej."
                )
            else:
                st.markdown(
                    f"<h3 style='color:#F1F5F9;margin-bottom:20px;'>📋 {dane['nazwa']}</h3>",
                    unsafe_allow_html=True,
                )

                # --- Zarobki ---
                st.markdown("#### 💰 Widełki płacowe w Polsce (brutto/miesiąc)")
                z = dane["zarobki"]
                col_j, col_m, col_s = st.columns(3)
                for col, poziom, label in [
                    (col_j, "junior", "Junior"),
                    (col_m, "mid",    "Mid / Regular"),
                    (col_s, "senior", "Senior"),
                ]:
                    with col:
                        st.markdown(
                            f"<div style='background:#1E293B;border:1px solid #334155;"
                            f"border-radius:10px;padding:16px;text-align:center;'>"
                            f"<div style='color:#94A3B8;font-size:0.8rem;margin-bottom:6px;'>{label}</div>"
                            f"<div style='color:#4ADE80;font-weight:700;font-size:0.95rem;'>UoP: {z[poziom]['uop']}</div>"
                            f"<div style='color:#60A5FA;font-size:0.88rem;margin-top:4px;'>B2B: {z[poziom]['b2b']}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                miasta = dane.get("miasta", {})
                if miasta:
                    modif = " &nbsp;·&nbsp; ".join(
                        f"<span style='color:#94A3B8'>{m}:</span> <span style='color:#F1F5F9'>{v}</span>"
                        for m, v in miasta.items()
                    )
                    st.markdown(
                        f"<p style='color:#64748B;font-size:0.82rem;margin-top:8px;'>Korekta lokalizacji: {modif}</p>",
                        unsafe_allow_html=True,
                    )

                st.markdown("---")

                # --- Umiejętności ---
                st.markdown("#### 🛠️ Top 10 wymaganych umiejętności")
                for i, u in enumerate(dane["umiejetnosci"], 1):
                    kolor = _WAGA_COLOR.get(u["waga"], "#94A3B8")
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:12px;"
                        f"padding:8px 0;border-bottom:1px solid #1E293B;'>"
                        f"<span style='color:#475569;font-size:0.8rem;width:20px;text-align:right;'>{i}.</span>"
                        f"<span style='color:#F1F5F9;flex:1;'>{u['nazwa']}</span>"
                        f"<span style='background:{kolor}22;color:{kolor};padding:2px 8px;"
                        f"border-radius:12px;font-size:0.72rem;font-weight:600;'>{u['waga']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("---")

                # --- Pytania rekrutacyjne ---
                st.markdown("#### ❓ Pytania rekrutacyjne z odpowiedziami")
                for i, pq in enumerate(dane["pytania"], 1):
                    with st.expander(f"Pytanie {i}: {pq['pytanie']}"):
                        st.markdown(
                            f"<div style='color:#CBD5E1;line-height:1.6;'>{pq['odpowiedz']}</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")

                # --- Wyróżnienie ---
                st.markdown("#### ⭐ Jak wyróżnić się spośród kandydatów")
                for tip in dane["wyroznienie"]:
                    st.markdown(
                        f"<div style='display:flex;gap:10px;align-items:flex-start;"
                        f"padding:8px 0;border-bottom:1px solid #1E293B;'>"
                        f"<span style='color:#FBBF24;font-size:1rem;'>✓</span>"
                        f"<span style='color:#CBD5E1;'>{tip}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

with tab_info:
    st.markdown("### O aplikacji")
    st.markdown("""
Aplikacja agreguje oferty pracy z 4 źródeł jednocześnie:

| Źródło | Typ | Wymagania |
|---|---|---|
| **JustJoin.IT** | Publiczne API | Brak |
| **NoFluffJobs** | REST API | Brak |
| **Adzuna** | REST API | Wbudowany klucz |
| **Jooble** | REST API | Opcjonalny klucz API |

---

#### Klucz API Jooble (opcjonalny)
Wpisz własny klucz w sekcji **Ustawienia** pod wyszukiwarką.
Bezpłatny klucz: [jooble.org/api/about](https://jooble.org/api/about)

---

#### Technologie
- **Python** + **Streamlit**
- Równoległe pobieranie (ThreadPoolExecutor)
- REST API
- Statyczna baza wiedzy o stanowiskach (JSON)
""")
