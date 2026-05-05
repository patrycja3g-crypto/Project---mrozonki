import streamlit as st
import pandas as pd
import numpy as np
import pickle
import holidays
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── KONFIGURACJA STRONY ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Prognoz Sprzedaży",
    page_icon="🍦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLE CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Cała aplikacja */
.stApp {
    background:
        radial-gradient(circle at top left, rgba(125, 211, 252, 0.35), transparent 30%),
        radial-gradient(circle at top right, rgba(196, 181, 253, 0.35), transparent 28%),
        linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 45%, #FDF2F8 100%);
}

/* Kontener główny */
.block-container {
    padding-top: 1.4rem;
    padding-bottom: 2.5rem;
    max-width: 1320px;
}

/* Header */
.dashboard-header {
    background:
        linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.72)),
        linear-gradient(135deg, #DBEAFE 0%, #FCE7F3 100%);
    padding: 2rem 2.4rem;
    border-radius: 28px;
    margin-bottom: 1.6rem;
    border: 1px solid rgba(255,255,255,0.75);
    box-shadow: 0 24px 60px rgba(99,102,241,0.13);
    backdrop-filter: blur(18px);
}

.dashboard-header h1 {
    color: #0F172A;
    font-size: 2.15rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.8px;
}

.dashboard-header p {
    color: #64748B;
    margin: 0.5rem 0 0 0;
    font-size: 0.98rem;
    font-weight: 500;
}

/* KPI Cards */
.kpi-card {
    position: relative;
    background: rgba(255,255,255,0.86);
    border-radius: 26px;
    padding: 1.35rem 1.45rem;
    box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
    border: 1px solid rgba(255,255,255,0.75);
    margin-bottom: 1rem;
    overflow: hidden;
    backdrop-filter: blur(16px);
}

.kpi-card:before {
    content: "";
    position: absolute;
    width: 95px;
    height: 95px;
    top: -35px;
    right: -30px;
    border-radius: 999px;
    background: linear-gradient(135deg, #60A5FA, #F0ABFC);
    opacity: 0.25;
}

.kpi-value {
    font-size: 2.15rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1;
    letter-spacing: -0.5px;
}

.kpi-label {
    font-size: 0.74rem;
    color: #64748B;
    margin-top: 0.55rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 800;
}

.kpi-sub {
    display: inline-block;
    font-size: 0.75rem;
    color: #2563EB;
    margin-top: 0.45rem;
    background: #DBEAFE;
    padding: 0.22rem 0.55rem;
    border-radius: 999px;
    font-weight: 700;
}

/* Sidebar — jasny, nie ciężki */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(255,255,255,0.96), rgba(239,246,255,0.92));
    border-right: 1px solid rgba(226,232,240,0.9);
}

[data-testid="stSidebar"] * {
    color: #0F172A !important;
}

[data-testid="stSidebar"] h3 {
    color: #2563EB !important;
    font-weight: 800;
}

[data-testid="stSidebar"] label {
    color: #334155 !important;
    font-weight: 700;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(148,163,184,0.25);
}

/* Inputy */
.stTextInput input,
.stSelectbox div,
.stMultiSelect div {
    border-radius: 16px !important;
}

/* Suwak */
.stSlider [data-baseweb="slider"] {
    padding-top: 0.6rem;
}

/* Zakładki */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.65rem;
    background: rgba(255,255,255,0.55);
    padding: 0.45rem;
    border-radius: 999px;
    border: 1px solid rgba(226,232,240,0.85);
}

.stTabs [data-baseweb="tab"] {
    height: 42px;
    background: transparent;
    border-radius: 999px;
    padding: 0.45rem 1.05rem;
    font-weight: 800;
    color: #475569;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #2563EB, #7C3AED) !important;
    color: white !important;
    box-shadow: 0 10px 25px rgba(37,99,235,0.25);
}

/* Info box */
.info-box {
    background: rgba(255,255,255,0.82);
    border: 1px solid rgba(191,219,254,0.95);
    border-radius: 22px;
    padding: 1rem 1.2rem;
    margin: 0.6rem 0 1rem 0;
    font-size: 0.9rem;
    color: #1E3A8A;
    box-shadow: 0 14px 35px rgba(59,130,246,0.09);
    backdrop-filter: blur(16px);
}

/* Tabele */
[data-testid="stDataFrame"] {
    border-radius: 22px;
    overflow: hidden;
    border: 1px solid rgba(226,232,240,0.95);
    box-shadow: 0 18px 42px rgba(15,23,42,0.07);
}

/* Przyciski */
.stDownloadButton button,
.stButton button {
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    color: white !important;
    border-radius: 999px;
    border: none;
    padding: 0.7rem 1.25rem;
    font-weight: 800;
    box-shadow: 0 14px 30px rgba(37,99,235,0.25);
    transition: all 0.2s ease;
}

.stDownloadButton button:hover,
.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 18px 38px rgba(37,99,235,0.32);
}

/* Wykresy */
.js-plotly-plot {
    border-radius: 26px;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
    border: 1px solid rgba(226,232,240,0.85);
}

/* Alerty Streamlit */
.stAlert {
    border-radius: 20px;
}

/* Ukrycie trochę technicznego wyglądu */
[data-testid="stDecoration"] {
    background: linear-gradient(90deg, #38BDF8, #818CF8, #F472B6);
}

/* Stopka */
.footer-modern {
    text-align: center;
    color: #64748B;
    font-size: 0.82rem;
    padding: 1.4rem 0;
}

/* Mobile */
@media (max-width: 768px) {
    .dashboard-header {
        padding: 1.4rem 1.3rem;
        border-radius: 22px;
    }

    .dashboard-header h1 {
        font-size: 1.55rem;
    }

    .kpi-value {
        font-size: 1.7rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ── FUNKCJE POMOCNICZE ────────────────────────────────────────────────────────

@st.cache_resource
def wczytaj_modele():
    """Wczytuje modele z pliku pkl."""
    try:
        with open('models_top10.pkl', 'rb') as f:
            dane = pickle.load(f)
        return dane
    except FileNotFoundError:
        return None

def pobierz_temperature_api(api_key, tygodnie=8):
    """Pobiera prognozę pogody z OpenWeatherMap (Warszawa)."""
    try:
        url = (f"https://api.openweathermap.org/data/2.5/forecast"
               f"?lat=52.23&lon=21.01&appid={api_key}"
               f"&units=metric&cnt=40")
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            daily = {}
            for item in data['list']:
                date = item['dt_txt'][:10]
                tmax = item['main']['temp_max']
                if date not in daily:
                    daily[date] = tmax
                else:
                    daily[date] = max(daily[date], tmax)
            return daily
    except Exception:
        pass
    return None

def srednie_historyczne_tmax():
    """Historyczne średnie tmax per tydzień ISO (fallback)."""
    # Przybliżone średnie dla Polski (kwiecień-sierpień)
    return {
        14: 15.2, 15: 16.8, 16: 18.5, 17: 19.2, 18: 20.1,
        19: 21.8, 20: 23.5, 21: 24.2, 22: 25.8, 23: 26.5,
        24: 27.8, 25: 28.5, 26: 29.2, 27: 29.8, 28: 30.1,
        29: 29.5, 30: 28.8, 31: 28.2, 32: 27.5, 33: 26.2,
        34: 24.8, 35: 22.5
    }

def oblicz_cechy_swiateczne(date, pl_hol):
    """Oblicza zmienne świąteczne dla danej daty."""
    is_hol = 1 if date.date() in pl_hol else 0

    days_to = 14
    for i in range(1, 15):
        if (date + timedelta(days=i)).date() in pl_hol:
            days_to = i
            break

    days_since = 14
    for i in range(1, 15):
        if (date - timedelta(days=i)).date() in pl_hol:
            days_since = i
            break

    easter_dates = {
        2025: datetime(2025, 4, 20),
        2026: datetime(2026, 4, 5),
        2027: datetime(2027, 3, 28),
    }
    easter_week = 0
    for ed in easter_dates.values():
        if abs((date - ed).days) <= 7:
            easter_week = 1
            break

    may_wknd = 1 if (
        (date.month == 5 and date.day <= 10) or
        (date.month == 4 and date.day >= 25)
    ) else 0

    return {
        'is_holiday': is_hol,
        'days_to_holiday': days_to,
        'days_since_holiday': days_since,
        'easter_week': easter_week,
        'may_long_weekend': may_wknd,
        'week_of_year': date.isocalendar()[1],
        'month': date.month
    }

def generuj_prognoze(modele_dane, tygodnie=8, api_key=None):
    """Generuje prognozę sprzedaży na N tygodni."""
    modele = modele_dane['modele']
    cechy = modele_dane['cechy']
    top10 = modele_dane['top10']

    # Data startu – najbliższy poniedziałek
    dzis = datetime.now()
    dni_do_pon = (7 - dzis.weekday()) % 7
    if dni_do_pon == 0:
        dni_do_pon = 7
    start = dzis + timedelta(days=dni_do_pon)
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Temperatury
    api_temps = {}
    if api_key:
        api_temps = pobierz_temperature_api(api_key) or {}
    srednie = srednie_historyczne_tmax()

    pl_hol = holidays.Poland(years=[
        start.year, start.year + 1])

    wiersze = []
    for w in range(tygodnie):
        data = start + timedelta(weeks=w)
        woy = data.isocalendar()[1]

        # Temperatura: API (tydzień 1) lub historyczna średnia
        if w == 0 and api_temps:
            tmax_vals = []
            for d in range(7):
                d_str = (data + timedelta(days=d)).strftime('%Y-%m-%d')
                if d_str in api_temps:
                    tmax_vals.append(api_temps[d_str])
            tmax = np.mean(tmax_vals) if tmax_vals else srednie.get(woy, 22)
        else:
            tmax = srednie.get(woy, 22)

        swieta = oblicz_cechy_swiateczne(data, pl_hol)
        wektor = {'tmax_mean': tmax, **swieta}

        row = {
            'Tydzień': w + 1,
            'Data od': data.strftime('%d.%m.%Y'),
            'tmax_°C': round(tmax, 1)
        }

        for asort in top10:
            if asort in modele:
                X = np.array([[wektor.get(c, 0) for c in cechy]])
                pred = max(0, modele[asort].predict(X)[0])
                row[asort] = int(round(pred))

        wiersze.append(row)

    return pd.DataFrame(wiersze), start

# ── GŁÓWNA APLIKACJA ──────────────────────────────────────────────────────────

def main():
    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1>🍦 Dashboard Prognoz Sprzedaży Lodów</h1>
        <p>System AI · Kanał tradycyjny · Model XGBoost · Dane pogodowe + kalendarz świąt</p>
    </div>
    """, unsafe_allow_html=True)

    # Wczytaj modele
    dane_modeli = wczytaj_modele()

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Ustawienia")
        st.markdown("---")

        # Liczba tygodni
        tygodnie = st.slider(
            "Horyzont prognozy (tygodnie)",
            min_value=1, max_value=8, value=4, step=1)

        st.markdown("---")
        st.markdown("### 🌡️ Dane pogodowe")

        uzywaj_api = st.checkbox(
            "Użyj API pogodowego (tydzień 1)", value=False)
        api_key = ""
        if uzywaj_api:
            api_key = st.text_input(
                "f9f6ca2b29ed2a433634e4eceb8c81c6",
                type="password",
                help="Uzyskaj bezpłatny klucz na openweathermap.org")

        st.markdown("---")
        st.markdown("### 📊 Filtrowanie")

        if dane_modeli:
            top10 = dane_modeli['top10']
            wybrane = st.multiselect(
                "Wybierz asortymenty",
                options=top10,
                default=top10[:5])
        else:
            wybrane = []

        st.markdown("---")
        st.markdown("""
        <div style='font-size:0.75rem; color:#8899CC; padding:0.5rem 0;'>
        Model trenowany na danych 2023–2025<br>
        Retrenowanie: raz na sezon
        </div>
        """, unsafe_allow_html=True)

    # ── SPRAWDZENIE PLIKU MODELU ──────────────────────────────────────────────
    if dane_modeli is None:
        st.error("""
        ❌ Nie znaleziono pliku **models_top10.pkl**

        Upewnij się że plik models_top10.pkl jest w tym samym folderze co app.py
        """)
        st.info("""
        **Jak dodać plik modelu:**
        1. Pobierz models_top10.pkl z Google Colab
        2. Umieść go w tym samym folderze co app.py
        3. Wgraj oba pliki na GitHub
        4. Zrestartuj aplikację
        """)
        return

    wyniki = dane_modeli.get('wyniki', {})
    top10 = dane_modeli['top10']

    # ── KPI ROW ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    doskonale = sum(1 for a in wyniki
                    if wyniki[a]['mape'] <= 0.15)
    dobre = sum(1 for a in wyniki
                if 0.15 < wyniki[a]['mape'] <= 0.20)
    best_mape = min(wyniki[a]['mape'] for a in wyniki) if wyniki else 0
    best_asort = min(wyniki, key=lambda a: wyniki[a]['mape']) if wyniki else "-"

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{len(top10)}</div>
            <div class="kpi-label">Asortymentów w modelu</div>
            <div class="kpi-sub">kanał tradycyjny</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#2D7D46">
            <div class="kpi-value" style="color:#2D7D46">{doskonale}</div>
            <div class="kpi-label">Modeli doskonałych</div>
            <div class="kpi-sub">MAPE ≤ 15%</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#1D4ED8">
            <div class="kpi-value" style="color:#1D4ED8">{dobre}</div>
            <div class="kpi-label">Modeli dobrych</div>
            <div class="kpi-sub">MAPE 15–20%</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:#2D7D46">
            <div class="kpi-value" style="color:#2D7D46">{best_mape:.1%}</div>
            <div class="kpi-label">Najlepszy MAPE</div>
            <div class="kpi-sub">{best_asort}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── GENERUJ PROGNOZĘ ──────────────────────────────────────────────────────
    with st.spinner("⏳ Generuję prognozę..."):
        df_prognoza, data_start = generuj_prognoze(
            dane_modeli, tygodnie,
            api_key if uzywaj_api else None)

    if wybrane:
        kolumny_asort = [a for a in wybrane if a in df_prognoza.columns]
    else:
        kolumny_asort = [a for a in top10 if a in df_prognoza.columns]

    # ── ZAKŁADKI ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📈 Wykresy prognoz",
        "📋 Tabela szczegółowa",
        "🎯 Jakość modeli"
    ])

    # ── TAB 1: WYKRESY ────────────────────────────────────────────────────────
    with tab1:
        st.markdown(f"""
        <div class="info-box">
        📅 <strong>Horyzont prognozy:</strong>
        {df_prognoza['Data od'].iloc[0]} –
        {df_prognoza['Data od'].iloc[-1]}
        &nbsp;|&nbsp;
        🌡️ <strong>Temperatura:</strong>
        {df_prognoza['tmax_°C'].min():.1f}°C –
        {df_prognoza['tmax_°C'].max():.1f}°C
        &nbsp;|&nbsp;
        {'🌐 API pogodowe (tydzień 1)' if uzywaj_api and api_key
         else '📊 Historyczne średnie sezonowe'}
        </div>
        """, unsafe_allow_html=True)

        if len(kolumny_asort) == 0:
            st.warning("Wybierz co najmniej jeden asortyment.")
        else:
            # Wykres liniowy prognoz
            fig = go.Figure()

            kolory = [
                '#2563EB', '#EC4899', '#10B981', '#F59E0B',
    '#8B5CF6', '#06B6D4', '#F97316', '#22C55E',
    '#6366F1', '#EF4444'
            ]

            for i, asort in enumerate(kolumny_asort):
                kolor = kolory[i % len(kolory)]
                mape = wyniki.get(asort, {}).get('mape', 0)
                fig.add_trace(go.Scatter(
                    x=df_prognoza['Data od'],
                    y=df_prognoza[asort],
                    name=f"{asort} (MAPE: {mape:.1%})",
                    mode='lines+markers',
                    line=dict(color=kolor, width=2.5),
                    marker=dict(size=7, color=kolor),
                    hovertemplate=(
                        f"<b>{asort}</b><br>"
                        "Tydzień od: %{x}<br>"
                        "Prognoza: %{y:,.0f} szt.<br>"
                        f"MAPE modelu: {mape:.1%}<extra></extra>"
                    )
                ))

            fig.update_layout(
                title=dict(
                    text="Prognoza sprzedaży tygodniowej (sztuki)",
                    font=dict(size=16, color='#030928')),
                xaxis=dict(
                    title="Tydzień",
                    showgrid=True,
                    gridcolor='#E5E7EB'),
                yaxis=dict(
                    title="Sprzedaż (szt.)",
                    showgrid=True,
                    gridcolor='#E5E7EB',
                    tickformat=','),
                plot_bgcolor='white',
                paper_bgcolor='white',
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=-0.3,
                    xanchor="center", x=0.5),
                height=450,
                margin=dict(l=60, r=30, t=60, b=120),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Wykres temperatury
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Bar(
                x=df_prognoza['Data od'],
                y=df_prognoza['tmax_°C'],
                name='tmax (°C)',
                marker_color=[
                    '#B91C1C' if t > 28
                    else '#D97706' if t > 22
                    else '#1D4ED8'
                    for t in df_prognoza['tmax_°C']
                ],
                hovertemplate=(
                    "Tydzień od: %{x}<br>"
                    "tmax: %{y:.1f}°C<extra></extra>")
            ))
            fig_temp.update_layout(
                title="Prognoza temperatury maksymalnej (°C)",
                xaxis_title="Tydzień",
                yaxis_title="Temperatura (°C)",
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=220,
                margin=dict(l=60, r=30, t=40, b=40),
                showlegend=False
            )
            st.plotly_chart(fig_temp, use_container_width=True)

    # ── TAB 2: TABELA ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 📋 Prognoza sprzedaży – szczegóły")

        cols_show = ['Tydzień', 'Data od', 'tmax_°C'] + kolumny_asort
        df_show = df_prognoza[cols_show].copy()

        # Wiersz sumy
        suma_row = {'Tydzień': 'SUMA', 'Data od': '—',
                    'tmax_°C': '—'}
        for a in kolumny_asort:
            suma_row[a] = df_show[a].sum()
        df_show = pd.concat(
            [df_show, pd.DataFrame([suma_row])],
            ignore_index=True)

        # Formatowanie liczb
        for a in kolumny_asort:
            df_show[a] = df_show[a].apply(
                lambda x: f"{int(x):,}" if isinstance(x, (int, float))
                and not np.isnan(float(x)) else x)

        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # Przycisk pobierania
        csv = df_prognoza[cols_show].to_csv(
            index=False, sep=';', decimal=',')
        st.download_button(
            label="⬇️ Pobierz CSV",
            data=csv.encode('utf-8-sig'),
            file_name=f"prognoza_{data_start.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # ── TAB 3: JAKOŚĆ MODELI ──────────────────────────────────────────────────
    with tab3:
        st.markdown("### 🎯 Jakość modeli XGBoost")

        if wyniki:
            df_wyniki = pd.DataFrame([
    {
        'Asortyment': a,
        'MAPE': wyniki[a]['mape'],
        'R²': wyniki[a]['r2'],
        'Ocena': (
            'Doskonały' if wyniki[a]['mape'] <= 0.15
            else 'Dobry' if wyniki[a]['mape'] <= 0.20
            else 'Akceptowalny' if wyniki[a]['mape'] <= 0.30
            else 'Wymaga danych'
        )
    }
    for a in wyniki
]).sort_values('MAPE').reset_index(drop=True)
            df_wyniki.index += 1

            # Wykres MAPE
            kolory_mape = [
                '#2D7D46' if m <= 0.15
                else '#1D4ED8' if m <= 0.20
                else '#D97706' if m <= 0.30
                else '#B91C1C'
                for m in df_wyniki['MAPE']
            ]

            fig_mape = go.Figure(go.Bar(
                x=df_wyniki['Asortyment'],
                y=df_wyniki['MAPE'] * 100,
                marker_color=kolory_mape,
                text=[f"{m:.1%}" for m in df_wyniki['MAPE']],
                textposition='outside',
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "MAPE: %{y:.2f}%<extra></extra>")
            ))
            fig_mape.add_hline(
                y=15, line_dash="dash",
                line_color="#2D7D46", line_width=1.5,
                annotation_text="15% – próg doskonały")
            fig_mape.add_hline(
                y=20, line_dash="dash",
                line_color="#1D4ED8", line_width=1.5,
                annotation_text="20% – próg dobry")
            fig_mape.update_layout(
                title="MAPE dla każdego asortymentu (%)",
                xaxis_title="Asortyment",
                yaxis_title="MAPE (%)",
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=380,
                margin=dict(l=60, r=30, t=60, b=60)
            )
            st.plotly_chart(fig_mape, use_container_width=True)

            # Tabela wyników
            df_wyniki['MAPE'] = df_wyniki['MAPE'].apply(
                lambda x: f"{x:.2%}")
            df_wyniki['R²'] = df_wyniki['R²'].apply(
                lambda x: f"{x:.3f}")

            st.dataframe(
                df_wyniki,
                use_container_width=True,
                hide_index=False,
                height=380
            )

            # Legenda
            st.markdown("""
            <div class="info-box">
            🟢 <strong>Doskonały</strong> – MAPE ≤ 15% &nbsp;|&nbsp;
            🔵 <strong>Dobry</strong> – MAPE 15–20% &nbsp;|&nbsp;
            🟡 <strong>Akceptowalny</strong> – MAPE 20–30% &nbsp;|&nbsp;
            🔴 <strong>Wymaga danych</strong> – MAPE > 30%<br><br>
            <strong>R²</strong> = współczynnik determinacji
            (1.0 = model idealny, 0.0 = model losowy)
            </div>
            """, unsafe_allow_html=True)

    # ── STOPKA ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; color:#6B7280; font-size:0.8rem; padding:1rem 0'>
    🍦 Dashboard Prognoz Sprzedaży Lodów &nbsp;|&nbsp;
    Model XGBoost · Dane pogodowe + kalendarz świąt polskich &nbsp;|&nbsp;
    Projekt AI · ALK 2026
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
