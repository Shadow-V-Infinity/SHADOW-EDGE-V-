import os
import requests
from math import isfinite

class MarketService:
    BASE_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"

    def __init__(self, api_key=None):
        # Charge la clé depuis l'environnement si non fournie
        self.api_key = api_key or os.getenv("ODDS_API_KEY")

        if not self.api_key:
            raise ValueError("ODDS_API_KEY is missing in environment variables")

    # ---------------------------
    # 1) Fetch odds (The Odds API)
    # ---------------------------
    def fetch_odds(self):
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal",
        }
        r = requests.get(self.BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    @staticmethod
    def implied_prob(odds):
        if not odds or odds <= 1:
            return None
        return 1 / odds

    def value_bet(self, model_prob, market_odds):
        if model_prob is None or market_odds is None:
            return None
        ip = self.implied_prob(market_odds)
        if ip is None:
            return None
        return model_prob - ip

    @staticmethod
    def kelly_fraction(p, odds):
        if p is None or odds is None:
            return None
        b = odds - 1
        q = 1 - p
        f = (b * p - q) / b if b != 0 else None
        return f if f and isfinite(f) and f > 0 else None

    def arbitrage(self, home_odds, away_odds):
        if not home_odds or not away_odds:
            return None
        inv = (1 / home_odds) + (1 / away_odds)
        return inv < 1

    def get_game_market(self, home_team, away_team):
        data = self.fetch_odds()

        for game in data:
            bookmakers = game.get("bookmakers", [])
            if not bookmakers:
                continue

            bm = bookmakers[0]
            markets = bm.get("markets", [])
            if not markets:
                continue

            outcomes = markets[0].get("outcomes", [])
            names = [o["name"] for o in outcomes]

            if home_team in names and away_team in names:
                home_odds = next(o["price"] for o in outcomes if o["name"] == home_team)
                away_odds = next(o["price"] for o in outcomes if o["name"] == away_team)

                return {
                    "bookmaker": bm.get("title"),
                    "home_odds": home_odds,
                    "away_odds": away_odds,
                }

        return None

    def analyze_match(self, home_team, away_team, model_home_prob):
        market = self.get_game_market(home_team, away_team)
        if not market:
            return {"market": None}

        home_odds = market["home_odds"]
        away_odds = market["away_odds"]

        home_ip = self.implied_prob(home_odds)
        away_ip = self.implied_prob(away_odds)

        value = self.value_bet(model_home_prob, home_odds)
        kelly = self.kelly_fraction(model_home_prob, home_odds)
        arb = self.arbitrage(home_odds, away_odds)

        return {
            "market": market,
            "implied_probability": {
                "home": home_ip,
                "away": away_ip,
            },
            "value": {
                "home_value": value,
            },
            "kelly": {
                "home_fraction": kelly,
            },
            "arbitrage": arb,
        }
