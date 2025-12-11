# 🏀 NBA Monte Carlo Simulation Engine (v2.0)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-ff4b4b?style=for-the-badge&logo=streamlit)
![Selenium](https://img.shields.io/badge/Selenium-Automated-green?style=for-the-badge&logo=selenium)
![Build Status](https://img.shields.io/badge/Build-Passing-success?style=for-the-badge)

**A professional-grade, stochastic decision support system for NBA match prediction and analysis.**

Unlike simple average-based predictors, this engine utilizes **Monte Carlo simulations**, **Dynamic Volatility Modeling**, and **Weighted Recency Algorithms** to provide a probabilistic view of match outcomes.

---

## 🚀 Key Features (v2.0)

### 🧠 Advanced Math Engine
* **Dynamic Volatility:** Standard deviation is no longer static. The engine calculates volatility based on a team's **3-Point Attempt Rate (3PAr)**. Teams that rely heavily on 3-pointers are modeled with higher variance (higher upset potential).
* **Weighted Recency Form:** Instead of a flat "Last 10 Games" record, the system uses a **Logarithmic Decay** formula. Recent games and active streaks carry significantly more weight than older results.
* **Net Rating Integration:** Power rankings now account for **Net Rating** (dominance factor), not just raw Offensive/Defensive ratings.

### ⚡ Automated Intelligence
* **Smart Fatigue Detection:** The scraper checks yesterday's box scores. If a team played yesterday, the **"Back-to-Back"** flag is automatically raised, and a fatigue penalty is applied.
* **Star Player Tracking:** The system automatically identifies the top scorers for every team from Basketball-Reference.
* **CI/CD Pipeline:** Data is updated automatically every day at **08:00 UTC** via **GitHub Actions**, ensuring the dashboard always has the latest stats without manual intervention.

### 📊 Interactive Dashboard
* **Visual Analytics:** Probability density charts and "Most Likely 10 Scores" bar charts.
* **Scenario Analysis:** Users can manually toggle fatigue status or select missing key players to see how "What-If" scenarios impact the win probability.

---

## 🧪 Methodology: How It Works

The engine calculates a **Power Score** for each team using a weighted formula:

$$\text{Power} = \text{ORtg} + \text{Form}_{\text{weighted}} + \text{Style}_{\text{bonus}} + \text{NetRtg}_{\text{bonus}} - \text{Penalties}$$

1.  **Data Mining:** Scripts fetch advanced stats (Pace, Four Factors, 3PAr) via Selenium in Headless mode.
2.  **Matchup Analysis:**
    * *Style Bonus:* E.g., A high-rebounding team vs. a poor-rebounding team gets a bonus.
    * *Penalties:* **-5.0** per missing star, **-3.0** for fatigue (B2B).
3.  **Monte Carlo Simulation:**
    * The engine runs **10,000** virtual matches.
    * Scores are generated using a **Normal Distribution** where $\mu = \text{Expected Score}$ and $\sigma = \text{Dynamic Volatility}$.

---

## 🛠️ Installation & Local Usage

### Prerequisites
* Python 3.9+
* Google Chrome (Installed locally)

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/nba-monte-carlo.git](https://github.com//beratkahraman/NBA_monte_carlo.git)
cd nba-monte-carlo
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```

## ☁️ Cloud Deployment & Automation

### Streamlit Community Cloud
This project is optimized for **Streamlit Community Cloud**.

* **`packages.txt`:** Installs `chromium` and `chromium-driver` on the Linux server.
* **`data_ops.py`:** Contains logic to switch between local Chrome driver and Cloud Chromium driver automatically.

### GitHub Actions (Auto-Update)
A workflow (`.github/workflows/daily_update.yml`) is configured to:

1.  Boot up a server daily.
2.  Install Chrome & Python.
3.  Run the scraper script.
4.  Commit the new `nba_master_data_2026.csv` back to the repository.

---

## 📂 Project Structure

```text
nba_monte_carlo/
├── .github/
│   └── workflows/
│       └── daily_update.yml  # CI/CD Automation script
├── data/
│   └── raw/                  # Stores the master data CSV
├── src/
│   ├── data_ops.py           # Universal Scraper (Local/Cloud/Actions)
│   └── monte_carlo.py        # Math engine & Simulation logic
├── app.py                    # Streamlit Dashboard UI
├── requirements.txt          # Python libraries
├── packages.txt              # System binaries for Cloud
└── README.md                 # Documentation
```

## 📝 Disclaimer

This tool is designed for educational and analytical purposes. While it uses advanced statistical modeling, sports outcomes are inherently unpredictable. This tool does not guarantee winning bets. Please use responsibly.

## Developed by Berat Kahraman
