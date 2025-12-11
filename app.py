import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from src.monte_carlo import MonteCarloSimulator
from src.data_ops import fetch_all_nba_data

st.set_page_config(page_title="NBA Monte Carlo Engine", layout="wide", page_icon="🏀")

st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    .reportview-container .main .block-container { max-width: 1000px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)


def clear_cache():
    st.cache_data.clear()
    if 'sim' in st.session_state:
        del st.session_state['sim']


st.title("🏀 NBA Monte Carlo Simülasyon Motoru")
st.markdown("**Veri Odaklı Karar Destek Sistemi** | *Stokastik Modelleme & Uzman Sistem Mimarisi*")

with st.expander("ℹ️ Bu Sistem Nasıl Çalışır? (Metodoloji)"):
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
        Bu proje, klasik bir "Yapay Zeka" (Machine Learning) modeli değil, basketbol dinamiklerini matematiksel kurallara döken bir **Uzman Sistem** ve **İstatistiksel Simülatör**dür.

        **1. Dinamik Veri (Dynamic Data):**
        B-Ref ve ESPN üzerinden güç, form, sakatlık ve yorgunluk (B2B) verileri anlık çekilir.

        **2. Akıllı Faktörler (Smart Factors):**
        * **Ağırlıklı Form:** Son maçlar, eskisine göre daha çok puan kazandırır.
        * **Volatilite:** Çok üçlük atan takımların sürpriz ihtimali (standart sapma) artırılır.
        * **Net Rating:** Takımın oyun dominasyonu güce eklenir.

        **3. Monte Carlo Simülasyonu:**
        İki takımın gücü, hesaplanan volatilite ile **10.000 kez** sanal maçta çarpıştırılır.
        """)
    with c2:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Normal_Distribution_PDF.svg/1200px-Normal_Distribution_PDF.svg.png",
            caption="Normal Dağılım Modeli")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Kontrol Paneli")
    st.info("Kaynaklar: **B-Ref** & **ESPN**")

    if st.button("🔄 Verileri Güncelle", type="secondary"):
        with st.spinner("Web siteleri taranıyor...(Biraz zaman alabilir)"):
            try:
                fetch_all_nba_data()
                clear_cache()
                st.success("Veri seti başarıyla yenilendi!")
            except Exception as e:
                st.error(f"Hata: {e}")

    st.divider()

    if os.path.exists("data/raw/nba_master_data_2026.csv"):
        df_check = pd.read_csv("data/raw/nba_master_data_2026.csv")
        st.success(f"{len(df_check)} Takım Hazır")
        with st.expander("Mevcut Takım Listesi"):
            teams_display = df_check['Team'].sort_values().reset_index(drop=True)
            teams_display.index += 1
            st.dataframe(teams_display, use_container_width=True)
    else:
        st.error("Veri dosyası bulunamadı! Lütfen güncelleyin.")

if 'sim' not in st.session_state:
    try:
        st.session_state['sim'] = MonteCarloSimulator()
    except:
        pass

if 'sim' in st.session_state:
    sim = st.session_state['sim']
    sim.df = sim.load_data()
    teams = sim.get_all_teams()
else:
    teams = []

if teams:
    st.divider()

    c1, c2, c3 = st.columns([1, 0.2, 1])

    with c1:
        st.subheader("🏠 Ev Sahibi")
        home_team = st.selectbox("Ev Seç", teams, index=0, key="home", label_visibility="collapsed")

    with c3:
        st.subheader("🚌 Deplasman")
        away_options = [t for t in teams if t != home_team]
        away_team = st.selectbox("Dep Seç", away_options, index=0, key="away", label_visibility="collapsed")

    with c2:
        st.markdown("<div style='text-align: center; font-size: 2em; padding-top: 15px; color: #888;'>VS</div>",
                    unsafe_allow_html=True)

    st.write("")
    with st.expander("Gelişmiş Ayarlar (Sakatlık & Yorgunluk)", expanded=True):
        h_data = sim.get_team_stats(home_team)
        a_data = sim.get_team_stats(away_team)

        h_stars = [s.strip() for s in str(h_data.get('Top_Stars', '')).split(',') if s.strip()]
        a_stars = [s.strip() for s in str(a_data.get('Top_Stars', '')).split(',') if s.strip()]

        col_h, col_sep, col_a = st.columns([1, 0.1, 1])

        with col_h:
            st.markdown(f"**{home_team}**")
            home_missing = st.multiselect("Eksik Oyuncular (-5 Puan)", h_stars, key="h_miss")

            h_b2b_auto = h_data.get('Is_B2B', False)
            h_b2b_override = st.checkbox(f"Yorgunluk (B2B)? {'(Otomatik: Evet)' if h_b2b_auto else ''}",
                                         value=h_b2b_auto, key="h_b2b")

        with col_a:
            st.markdown(f"**{away_team}**")
            away_missing = st.multiselect("Eksik Oyuncular (-5 Puan)", a_stars, key="a_miss")

            a_b2b_auto = a_data.get('Is_B2B', False)
            a_b2b_override = st.checkbox(f"Yorgunluk (B2B)? {'(Otomatik: Evet)' if a_b2b_auto else ''}",
                                         value=a_b2b_auto, key="a_b2b")

    st.write("")

    if st.button("10.000 MAÇI SİMÜLE ET", type="primary"):

        result = sim.simulate_match(
            home_team, away_team,
            override_home_b2b=h_b2b_override,
            override_away_b2b=a_b2b_override,
            home_missing_players=home_missing,
            away_missing_players=away_missing
        )

        if result:
            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                win_pct = result['home_win_pct']
                color_h = "#4CAF50" if win_pct > 50 else "#FF5252"
                st.markdown(
                    f"<div style='padding:15px; border-radius:10px; border: 2px solid {color_h}; text-align:center;'><h3 style='margin:0;'>{home_team}</h3><h1 style='color:{color_h}; margin:0;'>%{win_pct:.1f}</h1><p style='margin:0;'>Kazanma Olasılığı</p></div>",
                    unsafe_allow_html=True)

            with col_b:
                win_pct = result['away_win_pct']
                color_a = "#4CAF50" if win_pct > 50 else "#FF5252"
                st.markdown(
                    f"<div style='padding:15px; border-radius:10px; border: 2px solid {color_a}; text-align:center;'><h3 style='margin:0;'>{away_team}</h3><h1 style='color:{color_a}; margin:0;'>%{win_pct:.1f}</h1><p style='margin:0;'>Kazanma Olasılığı</p></div>",
                    unsafe_allow_html=True)

            st.markdown("---")
            st.markdown(
                f"<div style='text-align:center; padding:15px; background-color:#262730; border-radius:12px;'><h4 style='margin:0; color:#ddd;'>Beklenen Skor</h4><h1 style='margin:5px 0; color:white;'>{result['home_score']:.0f} - {result['away_score']:.0f}</h1><p style='margin:0; color:#888;'>Tahmini Toplam Sayı: <b>{result['total_score']:.1f}</b></p></div>",
                unsafe_allow_html=True)

            st.markdown("###Simülasyon Analizi")
            sims = 10000
            h_samples = np.random.normal(result['home_score'], 13.0, sims).round().astype(int)
            a_samples = np.random.normal(result['away_score'], 13.0, sims).round().astype(int)

            tab1, tab2 = st.tabs(["En Olası Skorlar", "Fark Analizi"])

            with tab1:
                scores = [f"{h}-{a}" for h, a in zip(h_samples, a_samples)]
                score_counts = pd.Series(scores).value_counts().head(10)
                fig1, ax1 = plt.subplots(figsize=(10, 5))
                plt.style.use('dark_background')
                colors = ['#FFD700' if i == 0 else '#4CAF50' for i in range(10)]
                bars = ax1.barh(score_counts.index, score_counts.values, color=colors)
                ax1.invert_yaxis()
                ax1.bar_label(bars, padding=3, color='white', fontsize=10)
                ax1.set_title(f"En Sık Görülen 10 Skor", fontsize=14)
                ax1.grid(axis='x', alpha=0.2)
                st.pyplot(fig1)

            with tab2:
                margins = h_samples - a_samples
                bins = [-float('inf'), -10.5, -5.5, -0.5, 0.5, 5.5, 10.5, float('inf')]
                labels = [f"{away_team} Farklı (11+)", f"{away_team} Orta (6-10)", f"{away_team} Yakın (1-5)",
                          "Uzatma İhtimali", f"{home_team} Yakın (1-5)", f"{home_team} Orta (6-10)",
                          f"{home_team} Farklı (11+)"]
                cats = pd.cut(margins, bins=bins, labels=labels)
                cat_counts = cats.value_counts().sort_index()
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                bar_colors = ['#FF5252'] * 3 + ['gray'] + ['#4CAF50'] * 3
                bars2 = ax2.bar(cat_counts.index, cat_counts.values, color=bar_colors)
                ax2.bar_label(bars2, fmt='%d', padding=3)
                ax2.set_xticklabels(cat_counts.index, rotation=45, ha='right')
                ax2.set_title("Maçın Fark Aralığı Tahmini", fontsize=14)
                ax2.grid(axis='y', alpha=0.2)
                st.pyplot(fig2)

            st.markdown("---")
            st.subheader("Neden Bu Sonuç?")
            d = result['details']

            h_miss_pen = d['h_missing_count'] * -5.0
            a_miss_pen = d['a_missing_count'] * -5.0

            analysis_data = {
                "Analiz Faktörü": ["Saha Avantajı", "Ağırlıklı Form", "Stil Eşleşmesi", "Net Rating Bonusu",
                                   "Yorgunluk Cezası", "Eksik Oyuncu Cezası"],
                f"{home_team} (Ev)": [
                    f"+{d['home_adv']:.1f}",
                    f"{d['home_form']:.1f}",
                    f"{d['home_style']:.1f}",
                    f"{d['h_net_bonus']:.1f}",
                    f"{d['h_fatigue']:.1f}",
                    f"{h_miss_pen:.1f}"
                ],
                f"{away_team} (Dep)": [
                    "-",
                    f"{d['away_form']:.1f}",
                    f"{d['away_style']:.1f}",
                    f"{d['a_net_bonus']:.1f}",
                    f"{d['a_fatigue']:.1f}",
                    f"{a_miss_pen:.1f}"
                ]
            }
            st.table(pd.DataFrame(analysis_data))

            st.info(
                "Not: **Ağırlıklı Form**, son maçların skorlarına ve serilere daha fazla önem veren özel bir algoritmadır.")