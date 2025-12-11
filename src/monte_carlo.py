import pandas as pd
import numpy as np
import os


class MonteCarloSimulator:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(base_dir, 'data', 'raw', 'nba_master_data_2026.csv')
        self.df = self.load_data()

        if not self.df.empty:
            self.league_avg_efg = self.df['Off_eFG'].mean()
            self.league_avg_tov = self.df['Off_TOV'].mean()
        else:
            self.league_avg_efg = 0.54
            self.league_avg_tov = 13.0

    def load_data(self):
        if not os.path.exists(self.data_path): return pd.DataFrame()
        df = pd.read_csv(self.data_path)
        if 'Team' in df.columns:
            df = df.dropna(subset=['Team'])
            df['Team'] = df['Team'].astype(str).str.strip()
            df = df.drop_duplicates(subset=['Team'], keep='first')
            df = df.sort_values('Team')

            if 'Is_B2B' in df.columns:
                df['Is_B2B'] = df['Is_B2B'].fillna(False).astype(bool)
            else:
                df['Is_B2B'] = False

            if 'Top_Stars' in df.columns:
                df['Top_Stars'] = df['Top_Stars'].fillna("")
            else:
                df['Top_Stars'] = ""

            if 'Off_3PAr' not in df.columns: df['Off_3PAr'] = 0.40
            if 'Net_Rtg' not in df.columns: df['Net_Rtg'] = 0.0

        return df

    def get_team_stats(self, team_name):
        if self.df.empty: return None
        match = self.df[self.df['Team'] == team_name]
        return match.iloc[0] if not match.empty else None

    def get_all_teams(self):
        if self.df.empty: return []
        return sorted(self.df['Team'].unique().tolist())

    def parse_record(self, record):
        try:
            w, l = map(int, str(record).split('-'))
            total = w + l
            return w / total if total > 0 else 0.5
        except:
            return 0.5

    def get_streak_value(self, streak):
        try:
            s = str(streak).upper().strip()
            if 'W' in s: return int(s.replace('W', ''))
            if 'L' in s: return -int(s.replace('L', ''))
            return 0
        except:
            return 0

    def calculate_weighted_form(self, last10_rec, streak_str):
        l10_win_pct = self.parse_record(last10_rec)
        l10_score = (l10_win_pct - 0.5) * 5.0

        streak_val = self.get_streak_value(streak_str)
        if streak_val > 0:
            streak_score = min(np.log1p(streak_val) * 0.8, 2.0)
        elif streak_val < 0:
            streak_score = max(-np.log1p(abs(streak_val)) * 0.8, -2.0)
        else:
            streak_score = 0

        weighted_form = (l10_score * 0.7) + (streak_score * 0.3)

        return weighted_form

    def calculate_volatility(self, stats):
        try:
            par = float(stats.get('Off_3PAr', 0.40))
            volatility = 9.0 + (par * 10.0)
            return volatility
        except:
            return 12.0

    def calculate_style_matchup(self, offense, defense):
        bonus = 0
        off_efg = float(offense.get('Off_eFG', 0.54))
        opp_3p = float(defense.get('Opp_3P_Pct', 0.36))

        if (off_efg > self.league_avg_efg) and (opp_3p > 0.36):
            bonus += 2.5
        elif (off_efg < self.league_avg_efg) and (opp_3p < 0.35):
            bonus -= 1.5

        off_tov = float(offense.get('Off_TOV', 13.0))
        if off_tov < 12.0:
            bonus += 1.0
        elif off_tov > 15.0:
            bonus -= 1.5

        off_orb = float(offense.get('Off_ORB', 24.0))
        if off_orb > 27.0: bonus += 1.5

        return bonus

    def simulate_match(self, home_team, away_team, simulations=10000,
                       override_home_b2b=None, override_away_b2b=None,
                       home_missing_players=None, away_missing_players=None):

        h = self.get_team_stats(home_team)
        a = self.get_team_stats(away_team)

        if h is None or a is None: return None

        home_adv = 2.0 + (self.parse_record(h.get('Home', '0-0')) * 3.0)

        h_form_weighted = self.calculate_weighted_form(h.get('Last_10', '5-5'), h.get('Streak', ''))
        a_form_weighted = self.calculate_weighted_form(a.get('Last_10', '5-5'), a.get('Streak', ''))

        h_style = self.calculate_style_matchup(h, a)
        a_style = self.calculate_style_matchup(a, h)

        h_is_b2b = override_home_b2b if override_home_b2b is not None else h.get('Is_B2B', False)
        a_is_b2b = override_away_b2b if override_away_b2b is not None else a.get('Is_B2B', False)

        h_fatigue_pen = -3.0 if h_is_b2b else 0.0
        a_fatigue_pen = -3.0 if a_is_b2b else 0.0

        h_missing_count = len(home_missing_players) if home_missing_players else 0
        a_missing_count = len(away_missing_players) if away_missing_players else 0

        h_injury_pen = h_missing_count * -5.0
        a_injury_pen = a_missing_count * -5.0

        h_net_bonus = float(h.get('Net_Rtg', 0.0)) * 0.3
        a_net_bonus = float(a.get('Net_Rtg', 0.0)) * 0.3

        h_rating = float(h.get('ORtg', 110)) + h_form_weighted + h_style + h_fatigue_pen + h_injury_pen + h_net_bonus
        a_rating = float(a.get('ORtg', 110)) + a_form_weighted + a_style + a_fatigue_pen + a_injury_pen + a_net_bonus

        a_rating *= 0.985

        pace = (float(h.get('Pace', 99)) + float(a.get('Pace', 99))) / 2
        h_drtg = float(h.get('DRtg', 110))
        a_drtg = float(a.get('DRtg', 110))

        h_score_exp = (pace / 100) * ((h_rating + a_drtg) / 2) + home_adv
        a_score_exp = (pace / 100) * ((a_rating + h_drtg) / 2)

        h_vol = self.calculate_volatility(h)
        a_vol = self.calculate_volatility(a)
        match_volatility = (h_vol + a_vol) / 2

        h_sim = np.random.normal(h_score_exp, match_volatility, simulations)
        a_sim = np.random.normal(a_score_exp, match_volatility, simulations)

        win_prob = (np.sum(h_sim > a_sim) / simulations) * 100

        return {
            'home_team': h['Team'],
            'away_team': a['Team'],
            'home_win_pct': win_prob,
            'away_win_pct': 100 - win_prob,
            'home_score': h_score_exp,
            'away_score': a_score_exp,
            'total_score': h_score_exp + a_score_exp,
            'details': {
                'home_adv': home_adv,
                'home_form': h_form_weighted,
                'away_form': a_form_weighted,
                'home_style': h_style,
                'away_style': a_style,
                'home_last10': h.get('Last_10', '5-5'),
                'away_last10': a.get('Last_10', '5-5'),
                'h_fatigue': h_fatigue_pen,
                'a_fatigue': a_fatigue_pen,
                'h_missing_count': h_missing_count,
                'a_missing_count': a_missing_count,
                'h_net_bonus': h_net_bonus,
                'a_net_bonus': a_net_bonus
            }
        }