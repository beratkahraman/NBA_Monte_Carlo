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
        if not os.path.exists(self.data_path):
            return pd.DataFrame()

        df = pd.read_csv(self.data_path)

        if 'Team' in df.columns:
            df = df.dropna(subset=['Team'])
            df['Team'] = df['Team'].astype(str).str.strip()
            df = df.sort_values('Team')

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
            return w / (w + l) if (w + l) > 0 else 0.5
        except:
            return 0.5

    def get_streak_bonus(self, streak):
        try:
            s = str(streak).upper().strip()
            if 'W' in s: return min(int(s.replace('W', '')) * 0.5, 2.5)
            if 'L' in s: return max(int(s.replace('L', '')) * -0.5, -2.5)
            return 0
        except:
            return 0

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

    def simulate_match(self, home_team, away_team, simulations=10000):
        h = self.get_team_stats(home_team)
        a = self.get_team_stats(away_team)

        if h is None or a is None: return None


        home_rec = h.get('Home', '0-0')
        home_win_rate = self.parse_record(home_rec)
        home_adv = 2.0 + (home_win_rate * 3.0)

        h_streak = self.get_streak_bonus(h.get('Streak', ''))
        a_streak = self.get_streak_bonus(a.get('Streak', ''))

        h_form = (self.parse_record(h.get('Last_10', '5-5')) - 0.5) * 5
        a_form = (self.parse_record(a.get('Last_10', '5-5')) - 0.5) * 5

        h_style = self.calculate_style_matchup(h, a)
        a_style = self.calculate_style_matchup(a, h)

        h_rating = float(h.get('ORtg', 110)) + h_streak + h_form + h_style
        a_rating = float(a.get('ORtg', 110)) + a_streak + a_form + a_style

        a_rating *= 0.985

        pace = (float(h.get('Pace', 99)) + float(a.get('Pace', 99))) / 2

        h_drtg = float(h.get('DRtg', 110))
        a_drtg = float(a.get('DRtg', 110))

        h_score_exp = (pace / 100) * ((h_rating + a_drtg) / 2) + home_adv
        a_score_exp = (pace / 100) * ((a_rating + h_drtg) / 2)

        h_sim = np.random.normal(h_score_exp, 12.0, simulations)
        a_sim = np.random.normal(a_score_exp, 12.0, simulations)

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
                'home_streak': h_streak,
                'away_streak': a_streak,
                'home_style': h_style,
                'away_style': a_style,
                'home_last10': h.get('Last_10', '5-5'),
                'away_last10': a.get('Last_10', '5-5')
            }
        }