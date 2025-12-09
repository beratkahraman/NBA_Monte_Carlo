import os
import time
import pandas as pd
import re
import io
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

SEASON = 2026

SLUG_MAP = {
    "atl": "Atlanta Hawks",
    "bos": "Boston Celtics",
    "bkn": "Brooklyn Nets",
    "cha": "Charlotte Hornets",
    "chi": "Chicago Bulls",
    "cle": "Cleveland Cavaliers",
    "dal": "Dallas Mavericks",
    "den": "Denver Nuggets",
    "det": "Detroit Pistons",
    "gs": "Golden State Warriors",
    "hou": "Houston Rockets",
    "ind": "Indiana Pacers",
    "lac": "Los Angeles Clippers",
    "lal": "Los Angeles Lakers",
    "mem": "Memphis Grizzlies",
    "mia": "Miami Heat",
    "mil": "Milwaukee Bucks",
    "min": "Minnesota Timberwolves",
    "no": "New Orleans Pelicans", "nop": "New Orleans Pelicans",
    "ny": "New York Knicks", "nyk": "New York Knicks",
    "okc": "Oklahoma City Thunder",
    "orl": "Orlando Magic",
    "phi": "Philadelphia 76ers",
    "phx": "Phoenix Suns",
    "por": "Portland Trail Blazers",
    "sac": "Sacramento Kings",
    "sa": "San Antonio Spurs", "sas": "San Antonio Spurs",
    "tor": "Toronto Raptors",
    "utah": "Utah Jazz", "uta": "Utah Jazz",
    "wsh": "Washington Wizards", "was": "Washington Wizards"
}


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def clean_bref_name(name):
    name = str(name).replace('*', '')
    name = re.sub(r'\s*\(\d+\)', '', name)
    return name.strip()


def extract_teams_from_links_espn(html_source):
    soup = BeautifulSoup(html_source, 'html.parser')
    teams_found = []

    seen = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if "/nba/team/_/name/" in href:
            try:
                parts = href.split("/name/")[1].split("/")
                slug = parts[0].lower()

                if slug in SLUG_MAP:
                    team_name = SLUG_MAP[slug]
                    if team_name not in seen:
                        teams_found.append(team_name)
                        seen.add(team_name)
            except:
                continue

    return teams_found


def extract_table_literal(html_content, table_id):
    clean_text = html_content.replace('', '')
    pattern = r'<table[^>]*id="' + table_id + r'"[^>]*>.*?</table>'
    match = re.search(pattern, clean_text, re.DOTALL)
    if match: return match.group(0)
    return None


def fetch_all_nba_data():
    driver = get_driver()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)

    try:
        url_adv = f"https://www.basketball-reference.com/leagues/NBA_{SEASON}.html"
        print(f"1/2: Güç Verileri (B-Ref) Çekiliyor...")
        driver.get(url_adv)
        time.sleep(3)
        html_source = driver.page_source

        tbl_adv = extract_table_literal(html_source, 'advanced-team')
        df_adv_raw = pd.read_html(io.StringIO(tbl_adv))[0]
        if isinstance(df_adv_raw.columns, pd.MultiIndex): df_adv_raw.columns = df_adv_raw.columns.droplevel(0)
        df_adv_raw = df_adv_raw.loc[:, ~df_adv_raw.columns.duplicated()]

        clean_adv = []
        for idx, row in df_adv_raw.iterrows():
            raw_t = str(row.get('Team', ''))
            if "League Average" in raw_t or "Team" in raw_t: continue

            t_clean = clean_bref_name(raw_t)

            if t_clean in SLUG_MAP.values():
                stats = {'Team': t_clean}

                def get_f(col, d=0.0):
                    try:
                        return float(row.get(col, d))
                    except:
                        return d

                stats['Pace'] = get_f('Pace', 99)
                stats['ORtg'] = get_f('ORtg', 114)
                stats['DRtg'] = get_f('DRtg', 114)
                stats['Off_eFG'] = get_f('eFG%', 0.54)
                stats['Off_TOV'] = get_f('TOV%', 13.0)
                stats['Off_ORB'] = get_f('ORB%', 24.0)

                ft = row.get('FT/FGA') if 'FT/FGA' in row else row.get('FTr', 0.20)
                stats['Off_FT_Rate'] = float(ft) if ft else 0.20

                clean_adv.append(stats)

        df_adv = pd.DataFrame(clean_adv).drop_duplicates(subset=['Team'])

        # Opponent
        tbl_opp = extract_table_literal(html_source, 'opponent-stats-per_game') or extract_table_literal(html_source,
                                                                                                         'per_game-opponent')
        if tbl_opp:
            df_o = pd.read_html(io.StringIO(tbl_opp))[0]
            if isinstance(df_o.columns, pd.MultiIndex): df_o.columns = df_o.columns.droplevel(0)
            df_o = df_o.loc[:, ~df_o.columns.duplicated()]

            opp_list = []
            for _, r in df_o.iterrows():
                tname = clean_bref_name(r.get('Team', ''))
                if tname in SLUG_MAP.values():
                    try:
                        p3 = float(r.get('3P%', 0.36))
                    except:
                        p3 = 0.36
                    try:
                        trb = float(r.get('TRB', 44))
                    except:
                        trb = 44
                    opp_list.append({'Team': tname, 'Opp_3P_Pct': p3, 'Opp_TRB': trb})

            df_opp = pd.DataFrame(opp_list).drop_duplicates(subset=['Team'])
            df_adv = pd.merge(df_adv, df_opp, on='Team', how='left')

        df_adv.fillna({'Opp_3P_Pct': 0.36, 'Opp_TRB': 44.0}, inplace=True)
        print(f"   -> B-Ref Tamam: {len(df_adv)} takım.")

        print(f"2/2: Form Verileri (ESPN) Çekiliyor...")
        driver.get("https://www.espn.com/nba/standings")
        time.sleep(3)
        espn_source = driver.page_source

        real_team_names = extract_teams_from_links_espn(espn_source)

        dfs_espn = pd.read_html(io.StringIO(espn_source))

        stats_frames = []
        if len(dfs_espn) >= 4:
            e_stats = dfs_espn[1]
            if isinstance(e_stats.columns, pd.MultiIndex): e_stats.columns = e_stats.columns.droplevel(0)
            stats_frames.append(e_stats)

            w_stats = dfs_espn[3]
            if isinstance(w_stats.columns, pd.MultiIndex): w_stats.columns = w_stats.columns.droplevel(0)
            stats_frames.append(w_stats)

            df_stats_raw = pd.concat(stats_frames, ignore_index=True)
        else:
            return print("HATA: ESPN tablo yapısı değişmiş.")

        clean_espn = []

        df_stats_raw.columns = [str(c).upper() for c in df_stats_raw.columns]

        if len(real_team_names) == len(df_stats_raw):
            print(f"   -> Link Eşleşmesi Başarılı: {len(real_team_names)} takım bulundu.")

            for i in range(len(real_team_names)):
                team_name = real_team_names[i]
                row = df_stats_raw.iloc[i]

                home = row.get('HOME', '0-0')
                road = row.get('AWAY', '0-0')
                if road == '0-0': road = row.get('ROAD', '0-0')

                clean_espn.append({
                    'Team': team_name,
                    'Home': home,
                    'Road': road,
                    'Last_10': row.get('L10', '5-5'),
                    'Streak': row.get('STRK', '')
                })
        else:
            print(
                f"UYARI: Link sayısı ({len(real_team_names)}) ile Tablo satır sayısı ({len(df_stats_raw)}) uyuşmuyor!")
            min_len = min(len(real_team_names), len(df_stats_raw))
            for i in range(min_len):
                clean_espn.append({
                    'Team': real_team_names[i],
                    'Home': df_stats_raw.iloc[i].get('HOME', '0-0'),
                    'Road': df_stats_raw.iloc[i].get('AWAY', '0-0'),
                    'Last_10': df_stats_raw.iloc[i].get('L10', '5-5'),
                    'Streak': df_stats_raw.iloc[i].get('STRK', '')
                })

        df_espn = pd.DataFrame(clean_espn).drop_duplicates(subset=['Team'])
        print(f"   -> ESPN Form Verileri Hazır: {len(df_espn)} takım.")

        print("Veriler Birleştiriliyor...")
        final_df = pd.merge(df_adv, df_espn, on='Team', how='inner')
        final_df = final_df.sort_values('Team')

        output_file = os.path.join(output_dir, f'nba_master_data_{SEASON}.csv')
        final_df.to_csv(output_file, index=False)

        print("-" * 50)
        print(f"BAŞARILI: {len(final_df)} takımın verisi hazır.")
        print("-" * 50)

        if len(final_df) < 30:
            missing = set(SLUG_MAP.values()) - set(final_df['Team'])
            print(f"EKSİK TAKIMLAR: {missing}")

        return final_df

    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()


if __name__ == "__main__":
    fetch_all_nba_data()