# app/services/nba/pre_match_service.py

import os
import requests
from nba_api.live.nba.endpoints import scoreboard

from app.services.nba.prediction_service import PredictionService
from app.services.nba.trends_service     import TrendsService
from app.services.nba.betting_radar      import BettingRadar
from app.services.nba.injury_service     import InjuryService
from app.services.nba.matchup_service    import MatchupService
from app.services.nba.pbp_analysis_service import PbpAnalysisService
from app.services.nba.props_service      import PropsService

BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
ODDS_KEY        = os.getenv("ODDS_API_KEY", "")

BALL_URL  = "https://api.balldontlie.io/v1"
ODDS_URL  = "https://api.the-odds-api.com/v4/sports/basketball_nba"

HEADERS_BDL = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}


class ShadowEdgePreMatchService:

    def __init__(self):
        self.predictions = PredictionService()
        self.trends      = TrendsService()
        self.radar       = BettingRadar()
        self.injuries    = InjuryService()
        self.matchups    = MatchupService()
        self.pbp         = PbpAnalysisService()
        self.props       = PropsService()

    # ───────────────────────────────────────────────────────────
    # 1) Matchs du jour
    # ───────────────────────────────────────────────────────────
    def get_today_games(self):
        try:
            sb    = scoreboard.ScoreBoard()
            games = sb.get_dict()["scoreboard"]["games"]

            return [
                {
                    "game_id":    g["gameId"],
                    "homeTeam":   g["homeTeam"]["teamName"],
                    "awayTeam":   g["awayTeam"]["teamName"],
                    "status":     g.get("gameStatusText", ""),
                    "pace":       None,
                    "off_rating": None,
                    "def_rating": None,
                    "form":       None,
                }
                for g in games
            ]
        except Exception as e:
            print(f"[PreMatchService] get_today_games error: {e}")
            return []

    # ───────────────────────────────────────────────────────────
    # 2) Stats BallDontLie
    # ───────────────────────────────────────────────────────────
    def get_team_stats(self, team_name: str) -> dict:
        try:
            r    = requests.get(f"{BALL_URL}/teams", headers=HEADERS_BDL,
                                params={"search": team_name}, timeout=5)
            data = r.json()
            if not data.get("data"):
                return {}

            team_id = data["data"][0]["id"]
            stats   = requests.get(f"{BALL_URL}/stats", headers=HEADERS_BDL,
                                   params={"team_ids[]": team_id, "per_page": 100},
                                   timeout=5).json()
            return {"team_id": team_id, "raw": stats}

        except Exception as e:
            print(f"[PreMatchService] get_team_stats({team_name}) error: {e}")
            return {}

    # ───────────────────────────────────────────────────────────
    # 3) Derniers matchs
    # ───────────────────────────────────────────────────────────
    def get_last_games(self, team_id) -> dict:
        if not team_id:
            return {}
        try:
            r = requests.get(f"{BALL_URL}/games", headers=HEADERS_BDL,
                             params={"team_ids[]": team_id, "per_page": 5},
                             timeout=5)
            return r.json()
        except Exception as e:
            print(f"[PreMatchService] get_last_games error: {e}")
            return {}

    # ───────────────────────────────────────────────────────────
    # 4) Tendances
    # ───────────────────────────────────────────────────────────
    def compute_trends(self, last_games: dict) -> dict:
        try:
            games = last_games.get("data", [])
            if not games:
                return {}
            pts = [g["home_team_score"] + g["visitor_team_score"] for g in games]
            return {
                "avg_total_points": round(sum(pts) / len(pts), 1),
                "games_count":      len(pts),
            }
        except Exception:
            return {}

    # ───────────────────────────────────────────────────────────
    # 5) Odds
    # ───────────────────────────────────────────────────────────
    def get_odds(self) -> dict:
        if not ODDS_KEY:
            return {}
        try:
            r = requests.get(
                f"{ODDS_URL}/odds",
                params={"apiKey": ODDS_KEY, "regions": "eu", "markets": "h2h,spreads,totals"},
                timeout=5,
            )
            return r.json()
        except Exception as e:
            print(f"[PreMatchService] get_odds error: {e}")
            return {}

    # ───────────────────────────────────────────────────────────
    # 6) Playtypes (placeholder stable)
    # ───────────────────────────────────────────────────────────
    def compute_playtypes(self, stats: dict) -> dict:
        raw = stats.get("raw", {}).get("data", [])
        if not raw:
            return {}
        return {
            "pick_and_roll": {"frequency": 0.20},
            "isolation":     {"frequency": 0.15},
            "handoff":       {"frequency": 0.10},
            "spot_up":       {"frequency": 0.25},
            "post_up":       {"frequency": 0.10},
            "transition":    {"frequency": 0.20},
        }

    # ───────────────────────────────────────────────────────────
    # 7) Style index
    # ───────────────────────────────────────────────────────────
    def compute_style_index(self, playtypes: dict) -> dict:
        return {
            "pace":     playtypes.get("transition",    {}).get("frequency", 0),
            "iso_rate": playtypes.get("isolation",     {}).get("frequency", 0),
            "pnr_rate": playtypes.get("pick_and_roll", {}).get("frequency", 0),
        }

    # ───────────────────────────────────────────────────────────
    # 8) Package complet
    # ───────────────────────────────────────────────────────────
    def get_pre_match_package(self, game_id: str, home: str, away: str) -> dict:
        home_stats = self.get_team_stats(home)
        away_stats = self.get_team_stats(away)

        home_last  = self.get_last_games(home_stats.get("team_id"))
        away_last  = self.get_last_games(away_stats.get("team_id"))

        home_trends  = self.compute_trends(home_last)
        away_trends  = self.compute_trends(away_last)

        play_home    = self.compute_playtypes(home_stats)
        play_away    = self.compute_playtypes(away_stats)

        style_home   = self.compute_style_index(play_home)
        style_away   = self.compute_style_index(play_away)

        odds     = self.get_odds()
        injuries = self.injuries.get_all_injuries()

        prediction  = self.predictions.get_game_prediction(game_id)
        simulation  = self.predictions.simulate_game(game_id)
        trend_data  = self.trends.get_trends(game_id)

        return {
            "game_id": game_id,
            "injuries": injuries,
            "matchups": {
                "full":   {"home_raw": home_stats, "away_raw": away_stats},
                "alerts": self.matchups.get_mismatch_alerts(game_id),
            },
            "team_stats":  {"home": home_stats,  "away": away_stats},
            "last_games":  {"home": home_last,   "away": away_last},
            "trends":      {"home": home_trends, "away": away_trends, "shadow": trend_data},
            "playtypes":   {"home": play_home,   "away": play_away},
            "style_index": {"home": style_home,  "away": style_away},
            "prediction":  prediction,
            "simulation":  simulation,
            "props":       self.props.get_player_props(game_id),
            "market_analysis": odds,
            "pbp": {},
        }
