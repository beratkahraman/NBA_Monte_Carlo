from src.monte_carlo import MonteCarloSimulator
import sys


def main():
    print("=" * 50)
    print("   NBA MONTE CARLO SIMULATOR - 2026   ")
    print("=" * 50)

    try:
        sim = MonteCarloSimulator()
    except Exception as e:
        print(f"Hata: {e}")
        return

    teams = sorted(sim.df['Team'].unique())

    while True:
        print("\n--- NE YAPMAK İSTERSİNİZ? ---")
        print("1. Maç Simüle Et")
        print("2. Takım Listesini Gör")
        print("3. Çıkış")

        choice = input("Seçiminiz (1-3): ")

        if choice == '3':
            print("Görüşmek üzere!")
            break

        elif choice == '2':
            print("\n--- MEVCUT TAKIMLAR ---")
            for i, team in enumerate(teams, 1):
                print(f"{i}. {team}")
            print("-" * 30)

        elif choice == '1':
            print("\nLütfen takım isimlerini tam listedeki gibi yazın (Büyük/küçük harf duyarlı olabilir).")

            home_team = input("Ev Sahibi Takım: ").strip()
            away_team = input("Deplasman Takım: ").strip()

            print(f"\n{home_team} vs {away_team} maçı 10.000 kez oynatılıyor...")

            try:
                sim.simulate_match(home_team, away_team)
            except Exception as e:
                print(f"\nBİR HATA OLUŞTU: Takım isimlerini yanlış yazmış olabilirsiniz.")
                print("Lütfen '2' seçeneği ile listeyi kontrol edin.")

        else:
            print("Geçersiz seçim.")


if __name__ == "__main__":
    main()