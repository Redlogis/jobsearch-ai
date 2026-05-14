import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import streamlit as st
import anthropic

load_dotenv()

from services.base import SOURCE_STYLES
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

with tab_analysis:
    st.markdown("### 🤖 Analiza stanowiska pracy")
    st.markdown(
        "<p style='color:#94A3B8;margin-top:-8px;margin-bottom:20px;'>"
        "Wpisz nazwę stanowiska i otrzymaj szczegółową analizę rynku pracy w Polsce</p>",
        unsafe_allow_html=True,
    )

    col_pos, col_abtn = st.columns([4, 1])
    with col_pos:
        position_name = st.text_input(
            "Stanowisko",
            placeholder="np. programista Python, analityk danych, project manager...",
            label_visibility="collapsed",
            key="position_input",
        )
    with col_abtn:
        analyze_clicked = st.button("🤖 Analizuj", type="primary", use_container_width=True)

    with st.expander("🔑 Klucz API Anthropic", expanded=False):
        anthropic_key = st.text_input(
            "Klucz API Anthropic",
            placeholder="sk-ant-...",
            type="password",
            help="Bezpłatny klucz API: console.anthropic.com",
            key="anthropic_key_input",
        )

    st.markdown("---")

    if analyze_clicked:
        if not position_name.strip():
            st.warning("Wpisz nazwę stanowiska, aby rozpocząć analizę.")
        else:
            api_key = anthropic_key.strip() or os.getenv("ANTHROPIC_API_KEY", "")
            if not api_key:
                st.error("Brak klucza API Anthropic. Wpisz klucz w sekcji powyżej lub ustaw zmienną ANTHROPIC_API_KEY.")
            else:
                pos = position_name.strip()
                prompt = f"""Przygotuj szczegółową analizę stanowiska "{pos}" na polskim rynku pracy.

Odpowiedź podziel na 4 sekcje z nagłówkami:

## 💰 Średnie zarobki w Polsce
Podaj realistyczne widełki wynagrodzeń brutto miesięcznie dla różnych poziomów doświadczenia (junior, mid, senior) oraz dla różnych miast (Warszawa, Kraków, Wrocław, inne). Uwzględnij B2B i UoP.

## 🛠️ Top 10 wymaganych umiejętności
Wymień 10 najważniejszych umiejętności technicznych i miękkich wymaganych na tym stanowisku. Każdą umiejętność krótko opisz i oceń jej ważność.

## ❓ 5 pytań rekrutacyjnych z odpowiedziami
Podaj 5 typowych pytań zadawanych podczas rozmów kwalifikacyjnych na to stanowisko. Dla każdego pytania daj wzorcową odpowiedź.

## ⭐ Jak wyróżnić się spośród kandydatów
Podaj konkretne, praktyczne wskazówki jak wyróżnić swoją kandydaturę spośród innych aplikantów na to stanowisko."""

                client = anthropic.Anthropic(api_key=api_key)
                output_placeholder = st.empty()
                full_text = ""

                try:
                    with st.spinner(f"Analizuję stanowisko: {pos}..."):
                        with client.messages.stream(
                            model="claude-opus-4-7",
                            max_tokens=2048,
                            thinking={"type": "adaptive"},
                            messages=[{"role": "user", "content": prompt}],
                        ) as stream:
                            for text in stream.text_stream:
                                full_text += text
                                output_placeholder.markdown(
                                    f"<div style='background:#1E293B;border:1px solid #334155;"
                                    f"border-radius:12px;padding:24px;color:#F1F5F9;'>{full_text}</div>",
                                    unsafe_allow_html=True,
                                )
                except anthropic.AuthenticationError:
                    st.error("Nieprawidłowy klucz API Anthropic. Sprawdź klucz i spróbuj ponownie.")
                except anthropic.RateLimitError:
                    st.error("Przekroczono limit zapytań API. Poczekaj chwilę i spróbuj ponownie.")
                except Exception as e:
                    st.error(f"Błąd podczas analizy: {e}")

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
""")
