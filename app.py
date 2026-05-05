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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #F5F7FB;
}

/* Główna szerokość i odstępy */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}

/* Header */
.dashboard-header {
    background: #FFFFFF;
    padding: 1.6rem 2rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    border: 1px solid #E5E7EB;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.dashboard-header h1 {
    color: #111827;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.6px;
}

.dashboard-header p {
    color: #6B7280;
    margin: 0.45rem 0 0 0;
    font-size: 0.95rem;
}

/* KPI Cards */
.kpi-card {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #E5E7EB;
    margin-bottom: 1rem;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
    line-height: 1;
}

.kpi-label {
    font-size: 0.78rem;
    color: #6B7280;
    margin-top: 0.45rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600;
}

.kpi-sub {
    font-size: 0.78rem;
    color: #2563EB;
    margin-top: 0.25rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
}

[data-testid="stSidebar"] * {
    color: #F9FAFB !important;
}

[data-testid="stSidebar"] label {
    color: #E5E7EB !important;
    font-weight: 600;
}

[data-testid="stSidebar"] .stSlider,
[data-testid="stSidebar"] .stCheckbox,
[data-testid="stSidebar"] .stMultiSelect,
[data-testid="stSidebar"] .stTextInput {
    margin-bottom: 1rem;
}

/* Zakładki */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    background: #FFFFFF;
    border-radius: 999px;
    border: 1px solid #E5E7EB;
    padding: 0.5rem 1rem;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: #2563EB !important;
    color: white !important;
}

/* Info box */
.info-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0 1rem 0;
    font-size: 0.9rem;
    color: #1E3A8A;
}

/* Tabele */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #E5E7EB;
}

/* Przyciski */
.stDownloadButton button {
    background: #2563EB;
    color: white;
    border-radius: 999px;
    border: none;
    padding: 0.6rem 1.2rem;
    font-weight: 700;
}

.stDownloadButton button:hover {
    background: #1D4ED8;
    color: white;
}

/* Wykresy */
.js-plotly-plot {
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
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
                '#2563EB', '#16A34A', '#F97316', '#9333EA',
    '#0EA5E9', '#EF4444', '#14B8A6', '#64748B',
    '#EAB308', '#DB2777'
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
