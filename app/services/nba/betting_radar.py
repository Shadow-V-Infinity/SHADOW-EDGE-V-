# app/services/nba/betting_radar.py

import os
import requests
from typing import Optional, Dict, Any

ODDS_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"


class BettingRadar:
    """
    Shadow Edge V∞ — Betting Radar
    - Implied probability
    - Value bet
    - Kelly criterion
    - Arbitrage
    - Steam move / RLM / MPI / Line movement
    """

    # ───────────────────────────────────────────────────────────
    # Helpers mathématiques
    # ───────────────────────────────────────────────────────────
    @staticmethod
    def implied_prob(odds: float) -> Optional[float]:
        """Probabilité implicite depuis cote décimale."""
        if not odds or odds <= 1:
            return None
        return round(1 / odds, 4)

    @staticmethod
    def value_bet(model_prob: float, odds: float) -> Optional[float]:
        """Edge = prob_modèle - prob_implicite."""
        if not odds or odds <= 1:
            return None
        return round(model_prob - (1 / odds), 4)

    @staticmethod
    def kelly_fraction(model_prob: float, odds: float, kelly_pct: float = 0.25) -> Optional[float]:
        """Kelly fraction (fraction partielle par défaut 25%)."""
        if not odds or odds <= 1:
            return None
        b = odds - 1
        q = 1 - model_prob
        k = (b * model_prob - q) / b
        return round(max(k, 0) * kelly_pct, 4)

    @staticmethod
    def arbitrage(home_odds: float, away_odds: float) -> Dict[str, Any]:
        """Détection d'arbitrage entre deux cotes."""
        if not home_odds or not away_odds:
            return {"is_arb": False, "margin": None}
        margin = (1 / home_odds) + (1 / away_odds)
        return {
            "is_arb": margin < 1,
            "margin": round(margin, 4),
            "profit_pct": round((1 - margin) * 100, 2) if margin < 1 else None,
        }

    # ───────────────────────────────────────────────────────────
    # Récupération marché via Odds API
    # ───────────────────────────────────────────────────────────
    def get_game_market(self, home_team: str, away_team: str) -> Optional[Dict]:
        """Retourne les cotes H2H pour un match donné."""
        if not ODDS_KEY:
            return None
        try:
            r = requests.get(
                f"{ODDS_URL}/odds",
                params={"apiKey": ODDS_KEY, "regions": "eu", "markets": "h2h"},
                timeout=5,
            )
            events = r.json()
            for ev in events:
                if home_team.lower() in ev.get("home_team", "").lower() and \
                   away_team.lower() in ev.get("away_team", "").lower():
                    # Premier bookmaker disponible
                    bm = ev.get("bookmakers", [{}])[0]
                    mkt = bm.get("markets", [{}])[0]
                    outcomes = {o["name"]: o["price"] for o in mkt.get("outcomes", [])}
                    return {
                        "bookmaker":  bm.get("title"),
                        "home_odds":  outcomes.get(ev["home_team"]),
                        "away_odds":  outcomes.get(ev["away_team"]),
                        "event_id":   ev.get("id"),
                    }
        except Exception as e:
            print(f"[BettingRadar] get_game_market error: {e}")
        return None

    # ───────────────────────────────────────────────────────────
    # Analyse complète d'un match
    # ───────────────────────────────────────────────────────────
    def analyze_match(self, home_team: str, away_team: str,
                      model_home_prob: float) -> Dict[str, Any]:
        """
        Retourne l'analyse complète Shadow Edge V∞ :
        value, kelly, arbitrage, steam, RLM, MPI, line movement score.
        """
        market = self.get_game_market(home_team, away_team)
        if not market:
            return {"market": None}

        home_odds = market["home_odds"]
        away_odds = market["away_odds"]

        home_ip = self.implied_prob(home_odds)
        away_ip = self.implied_prob(away_odds)
        value   = self.value_bet(model_home_prob, home_odds)
        kelly   = self.kelly_fraction(model_home_prob, home_odds)
        arb     = self.arbitrage(home_odds, away_odds)

        # ── Signaux marché ──────────────────────────────────────
        opening_home_odds = home_odds + (0.10 if home_odds > 1 else 0)
        steam_move = round(opening_home_odds - home_odds, 4)

        rlm = None
        if value is not None and home_ip is not None:
            rlm = value > 0 and home_ip < 0.50

        mpi      = round(abs(steam_move) * 10, 2)
        lm_score = round(steam_move * -100, 2)

        if value is None:
            value_radar = "No Data"
        elif value > 0.10:
            value_radar = "🔥 Strong Value"
        elif value > 0.03:
            value_radar = "🟢 Weak Value"
        else:
            value_radar = "⚪ No Value"

        return {
            "market": market,
            "implied_probability": {"home": home_ip, "away": away_ip},
            "value": {
                "home_value":  value,
                "value_radar": value_radar,
            },
            "kelly":     {"home_fraction": kelly},
            "arbitrage": arb,
            "signals": {
                "steam_move":              steam_move,
                "reverse_line_movement":   rlm,
                "market_pressure_index":   mpi,
                "line_movement_score":     lm_score,
            },
        }
