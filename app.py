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
</style>
""", unsafe_allow_html=True)


def clear_cache():
    st.cache_data.clear()
    if 'sim' in st.session_state:
        del st.session_state['sim']


st.title("🏀 NBA Monte Carlo Simülasyon Motoru")
st.markdown("""
**Veri Odaklı Karar Destek Sistemi** | *Stokastik Modelleme & Uzman Sistem Mimarisi*
""")

with st.expander("ℹ️ Bu Sistem Nasıl Çalışır? (Metodoloji)"):
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
        Bu proje, klasik bir "Yapay Zeka" (Machine Learning) modeli değil, basketbol dinamiklerini matematiksel kurallara döken bir **Uzman Sistem** ve **İstatistiksel Simülatör**dür.

        **1. Veri Madenciliği (Data Mining):**
        Basketball-Reference ve ESPN üzerinden takımların *Pace*, *Offensive Rating* ve *Four Factors* verileri anlık olarak çekilir.

        **2. Stil Analizi (Pattern Recognition):**
        Takımların oyun kimyası eşleştirilir. Örneğin; iyi şut atan bir takım (Yüksek eFG%), kötü dış savunmaya (Yüksek Opp 3P%) karşı oynuyorsa sisteme **"Stil Bonusu"** eklenir.

        **3. Monte Carlo Simülasyonu:**
        İki takımın hesaplanan güç puanları, 12 puanlık standart sapma (varyans) ile **10.000 kez** sanal maçta çarpıştırılır.
        """)
    with c2:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Normal_Distribution_PDF.svg/1200px-Normal_Distribution_PDF.svg.png",
            caption="Normal Dağılım Modeli")

with st.sidebar:
    st.header("Kontrol Paneli")
    st.info("Kaynaklar: **B-Ref** & **ESPN**")

    if st.button("🔄 Verileri Güncelle", type="secondary"):
        with st.spinner("Veriler çekiliyor..."):
            try:
                fetch_all_nba_data()
                clear_cache()
                st.success("Veriler güncellendi!")
            except Exception as e:
                st.error(f"Hata: {e}")

    st.divider()

    if os.path.exists("data/raw/nba_master_data_2026.csv"):
        df_check = pd.read_csv("data/raw/nba_master_data_2026.csv")
        st.success(f"{len(df_check)} Takım Hazır")
    else:
        st.error("Veri yok!")

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
        home_team = st.selectbox("Ev Sahibi", teams, index=0)
    with c3:
        away_options = [t for t in teams if t != home_team]
        away_team = st.selectbox("Deplasman", away_options, index=0)
    with c2:
        st.markdown("<h2 style='text-align:center; padding-top:10px;'>VS</h2>", unsafe_allow_html=True)

    st.write("")

    if st.button("10.000 MAÇI SİMÜLE ET", type="primary"):
        result = sim.simulate_match(home_team, away_team)

        if result:
            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                color = "green" if result['home_win_pct'] > 50 else "red"
                st.markdown(
                    f"<div style='text-align:center; border:2px solid {color}; padding:10px; border-radius:10px;'><h3>{home_team}</h3><h1 style='color:{color}'>%{result['home_win_pct']:.1f}</h1></div>",
                    unsafe_allow_html=True)
            with col_b:
                color = "green" if result['away_win_pct'] > 50 else "red"
                st.markdown(
                    f"<div style='text-align:center; border:2px solid {color}; padding:10px; border-radius:10px;'><h3>{away_team}</h3><h1 style='color:{color}'>%{result['away_win_pct']:.1f}</h1></div>",
                    unsafe_allow_html=True)

            st.markdown("---")
            st.markdown(
                f"<h2 style='text-align:center;'>Beklenen Skor: {result['home_score']:.0f} - {result['away_score']:.0f}</h2>",
                unsafe_allow_html=True)
            st.markdown(
                f"<p style='text-align:center; color:gray;'>Tahmini Toplam Sayı: <b>{result['total_score']:.1f}</b></p>",
                unsafe_allow_html=True)

            st.markdown("### Simülasyon Sonuçları")

            sims = 10000
            h_samples = np.random.normal(result['home_score'], 12.0, sims).round().astype(int)
            a_samples = np.random.normal(result['away_score'], 12.0, sims).round().astype(int)

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

                labels = [
                    f"{away_team} Farklı (11+)",
                    f"{away_team} Orta (6-10)",
                    f"{away_team} Yakın (1-5)",
                    "Uzatma İhtimali",
                    f"{home_team} Yakın (1-5)",
                    f"{home_team} Orta (6-10)",
                    f"{home_team} Farklı (11+)"
                ]

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
            d = result['details']
            st.write("#### Neden Bu Sonuç?")

            comp_df = pd.DataFrame({
                "Faktör": ["Saha Avantajı", "Form (L10)", "Seri", "Stil Eşleşmesi"],
                f"{home_team}": [f"+{d['home_adv']:.1f}", d['home_last10'], f"{d['home_streak']:.1f}",
                                 f"{d['home_style']:.1f}"],
                f"{away_team}": ["-", d['away_last10'], f"{d['away_streak']:.1f}", f"{d['away_style']:.1f}"]
            })
            st.table(comp_df)