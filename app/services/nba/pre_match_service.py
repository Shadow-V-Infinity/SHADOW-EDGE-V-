import os
import requests
from nba_api.live.nba.endpoints import scoreboard

BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY")
ODDS_KEY = os.getenv("ODDS_API_KEY")

BALL_URL = "https://api.balldontlie.io/v1"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"

HEADERS_BDL = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}
HEADERS_ODDS = {}


class ShadowEdgePreMatchService:

    # ---------------------------------------------------------
    # 1) MATCHS DU JOUR — COMPATIBLE FRONTEND
    # ---------------------------------------------------------
    def get_today_games(self):
        try:
            sb = scoreboard.ScoreBoard()
            games = sb.get_dict()["scoreboard"]["games"]

            formatted = []
            for g in games:
                formatted.append({
                    "game_id": g["gameId"],
                    "homeTeam": g["homeTeam"]["teamName"],
                    "awayTeam": g["awayTeam"]["teamName"],

                    # placeholders pour éviter undefined
                    "pace": None,
                    "off_rating": None,
                    "def_rating": None,
                    "form": None,
                })
            return formatted

        except Exception:
            return []

    # ---------------------------------------------------------
    # 2) STATS BALDONTLIE
    # ---------------------------------------------------------
    def get_team_stats(self, team_name):
        try:
            r = requests.get(
                f"{BALL_URL}/teams",
                headers=HEADERS_BDL,
                params={"search": team_name}
            )
            data = r.json()
            if not data["data"]:
                return {}

            team_id = data["data"][0]["id"]

            stats = requests.get(
                f"{BALL_URL}/stats",
                headers=HEADERS_BDL,
                params={"team_ids[]": team_id, "per_page": 100}
            ).json()

            return {
                "team_id": team_id,
                "raw": stats
            }

        except Exception:
            return {}

    # ---------------------------------------------------------
    # 3) DERNIERS MATCHS
    # ---------------------------------------------------------
    def get_last_games(self, team_id):
        try:
            r = requests.get(
                f"{BALL_URL}/games",
                headers=HEADERS_BDL,
                params={"team_ids[]": team_id, "per_page": 5}
            )
            return r.json()
        except:
            return {}

    # ---------------------------------------------------------
    # 4) TENDANCES — FIXÉ
    # ---------------------------------------------------------
    def compute_trends(self, last_games):
        try:
            games = last_games.get("data", [])
            if not games:
                return {}

            pts = []
            for g in games:
                pts.append(g["home_team_score"] + g["visitor_team_score"])

            return {
                "avg_points": sum(pts) / len(pts),
                "games_count": len(pts)
            }
        except:
            return {}

    # ---------------------------------------------------------
    # 5) ODDS
    # ---------------------------------------------------------
    def get_odds(self):
        try:
            r = requests.get(
                f"{ODDS_URL}/odds",
                params={
                    "apiKey": ODDS_KEY,
                    "regions": "eu",
                    "markets": "h2h,spreads,totals"
                }
            )
            return r.json()
        except:
            return {}

    # ---------------------------------------------------------
    # 6) INJURIES
    # ---------------------------------------------------------
    def get_injuries(self):
        return {
            "shadow_edge": {"home": [], "away": []},
            "nba_api": []
        }

    # ---------------------------------------------------------
    # 7) MATCHUPS
    # ---------------------------------------------------------
    def compute_matchups(self, home_stats, away_stats):
        return {
            "full": {
                "home_raw": home_stats,
                "away_raw": away_stats
            },
            "alerts": []
        }

    # ---------------------------------------------------------
    # 8) PLAYTYPES
    # ---------------------------------------------------------
    def compute_playtypes(self, stats):
        try:
            raw = stats.get("raw", {}).get("data", [])
            if not raw:
                return {}

            return {
                "pick_and_roll": {"frequency": 0.20},
                "isolation": {"frequency": 0.15},
                "handoff": {"frequency": 0.10},
                "spot_up": {"frequency": 0.25},
                "post_up": {"frequency": 0.10},
                "transition": {"frequency": 0.20},
            }
        except:
            return {}

    # ---------------------------------------------------------
    # 9) STYLE INDEX
    # ---------------------------------------------------------
    def compute_style_index(self, playtypes):
        try:
            return {
                "pace": playtypes.get("transition", {}).get("frequency", 0),
                "iso_rate": playtypes.get("isolation", {}).get("frequency", 0),
                "pnr_rate": playtypes.get("pick_and_roll", {}).get("frequency", 0),
            }
        except:
            return {}

    # ---------------------------------------------------------
    # 10) PACKAGE COMPLET — FIXÉ
    # ---------------------------------------------------------
    def get_pre_match_package(self, game_id, home, away):

        home_stats = self.get_team_stats(home)
        away_stats = self.get_team_stats(away)

        home_last = self.get_last_games(home_stats.get("team_id"))
        away_last = self.get_last_games(away_stats.get("team_id"))

        home_trends = self.compute_trends(home_last)
        away_trends = self.compute_trends(away_last)

        matchups = self.compute_matchups(home_stats, away_stats)

        play_home = self.compute_playtypes(home_stats)
        play_away = self.compute_playtypes(away_stats)

        style_home = self.compute_style_index(play_home)
        style_away = self.compute_style_index(play_away)

        odds = self.get_odds()
        injuries = self.get_injuries()

        return {
            "injuries": injuries,
            "matchups": matchups,
            "team_stats": {
                "home": home_stats,
                "away": away_stats
            },
            "last_games": {
                "home": home_last,
                "away": away_last
            },
            "trends": {
                "home": home_trends,
                "away": away_trends
            },
            "playtypes": {
                "home": play_home,
                "away": play_away
            },
            "style_index": {
                "home": style_home,
                "away": style_away
            },
            "props": {},
            "predictions": {},
            "market_analysis": odds,
            "pbp": {}
        }
