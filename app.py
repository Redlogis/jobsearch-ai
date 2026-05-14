import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from services.jooble import search_jooble
from services.justjoinit import search_justjoinit

st.set_page_config(
    page_title="JobSearch AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
/* Ogólne */
[data-testid="stAppViewContainer"] { background-color: #0F172A; }
[data-testid="stHeader"] { background-color: transparent; }

/* Karta oferty */
.job-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
}
.job-card:hover { border-color: #2563EB; }

.job-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #F1F5F9;
    margin: 0 0 4px 0;
}
.job-company {
    font-size: 0.95rem;
    color: #94A3B8;
    margin: 0 0 12px 0;
}
.job-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 0.85rem;
    margin-bottom: 14px;
}
.meta-item {
    display: flex;
    align-items: center;
    gap: 5px;
    color: #CBD5E1;
}
.salary-badge {
    background: #14532D;
    color: #4ADE80;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}
.source-badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.source-jooble {
    background: #1E3A5F;
    color: #60A5FA;
}
.source-justjoinit {
    background: #3B1F5E;
    color: #C084FC;
}
.apply-btn {
    display: inline-block;
    background: #2563EB;
    color: #ffffff !important;
    padding: 7px 18px;
    border-radius: 8px;
    text-decoration: none !important;
    font-size: 0.88rem;
    font-weight: 600;
    transition: background 0.2s;
}
.apply-btn:hover { background: #1D4ED8; }

/* Statystyki */
.stats-bar {
    background: #1E293B;
    border-radius: 10px;
    padding: 12px 20px;
    margin-bottom: 20px;
    color: #94A3B8;
    font-size: 0.9rem;
}

/* Input styling */
[data-testid="stTextInput"] input {
    background-color: #1E293B !important;
    border-color: #334155 !important;
    color: #F1F5F9 !important;
}

/* Divider */
hr { border-color: #334155; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Nagłówek ──────────────────────────────────────────────────────────────────
st.markdown("## 💼 JobSearch AI")
st.markdown(
    "<p style='color:#94A3B8;margin-top:-8px;margin-bottom:24px;'>"
    "Wyszukaj oferty pracy z Jooble i JustJoin.IT w jednym miejscu</p>",
    unsafe_allow_html=True,
)

tab_search, tab_info = st.tabs(["🔍 Wyszukiwarka ofert pracy", "ℹ️ O aplikacji"])


# ── Zakładka: Wyszukiwarka ─────────────────────────────────────────────────────
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

    st.markdown("---")

    if search_clicked:
        if not keyword.strip():
            st.warning("Wpisz słowo kluczowe, aby rozpocząć wyszukiwanie.")
        else:
            with st.spinner("Szukam ofert pracy..."):
                jooble_offers, jooble_err = search_jooble(keyword.strip(), location.strip())
                jjit_offers, jjit_err = search_justjoinit(keyword.strip())

            if jooble_err:
                st.info(f"ℹ️ Jooble: {jooble_err}", icon="ℹ️")
            if jjit_err:
                st.error(f"JustJoin.IT: {jjit_err}")

            all_offers = jjit_offers + jooble_offers

            if not all_offers:
                st.markdown(
                    "<div style='text-align:center;padding:60px 0;color:#64748B;'>"
                    "<div style='font-size:3rem;'>🔎</div>"
                    "<div style='font-size:1.1rem;margin-top:12px;'>Nie znaleziono ofert dla frazy "
                    f"<strong style='color:#94A3B8;'>„{keyword}"</strong></div>"
                    "<div style='margin-top:8px;font-size:0.9rem;'>Spróbuj innego słowa kluczowego</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                jjit_count = len(jjit_offers)
                jooble_count = len(jooble_offers)
                st.markdown(
                    f"<div class='stats-bar'>Znaleziono <strong style='color:#F1F5F9;'>"
                    f"{len(all_offers)}</strong> ofert — "
                    f"<span style='color:#C084FC;'>{jjit_count} z JustJoin.IT</span> · "
                    f"<span style='color:#60A5FA;'>{jooble_count} z Jooble</span></div>",
                    unsafe_allow_html=True,
                )

                for offer in all_offers:
                    source_class = (
                        "source-justjoinit" if offer.source == "JustJoin.IT" else "source-jooble"
                    )
                    salary_html = (
                        f"<span class='salary-badge'>💰 {offer.salary}</span>"
                        if offer.salary
                        else ""
                    )
                    date_html = (
                        f"<span class='meta-item'>📅 {offer.date_posted}</span>"
                        if offer.date_posted
                        else ""
                    )

                    st.markdown(
                        f"""
<div class="job-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
    <div>
      <div class="job-title">{offer.title}</div>
      <div class="job-company">🏢 {offer.company}</div>
    </div>
    <span class="source-badge {source_class}">{offer.source}</span>
  </div>
  <div class="job-meta">
    <span class="meta-item">📍 {offer.location}</span>
    {date_html}
    {salary_html}
  </div>
  <a class="apply-btn" href="{offer.apply_url}" target="_blank" rel="noopener noreferrer">
    Aplikuj →
  </a>
</div>
""",
                        unsafe_allow_html=True,
                    )

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


# ── Zakładka: O aplikacji ──────────────────────────────────────────────────────
with tab_info:
    st.markdown("### O aplikacji")
    st.markdown(
        """
Aplikacja agreguje oferty pracy z dwóch źródeł:

| Źródło | Opis | Wymagania |
|---|---|---|
| **JustJoin.IT** | Publiczne API — brak klucza | Brak |
| **Jooble** | Globalny agregator ofert | Klucz API (bezpłatny) |

---

#### Konfiguracja klucza API Jooble

1. Zarejestruj się na [jooble.org/api/about](https://jooble.org/api/about)
2. Skopiuj plik `.env.example` jako `.env`
3. Wpisz swój klucz: `JOOBLE_API_KEY=twoj_klucz`

---

#### Technologie
- **Python** + **Streamlit**
- Jooble REST API
- JustJoin.IT Public API
"""
    )
