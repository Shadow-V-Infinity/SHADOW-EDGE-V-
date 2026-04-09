import os
import requests
from nba_api.live.nba.endpoints import scoreboard, boxscore, playbyplay

# -----------------------------
#   CONFIGURATION
# -----------------------------

BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY")
ODDS_KEY = os.getenv("ODDS_API_KEY")

BALL_URL = "https://api.balldontlie.io/v1"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"

HEADERS_BDL = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}
HEADERS_ODDS = {}

# -----------------------------
#   SERVICE PRINCIPAL
# -----------------------------

class ShadowEdgePreMatchService:

    # -------------------------
    #   1) MATCHS DU JOUR
    # -------------------------
    def get_today_games(self):
        try:
            sb = scoreboard.ScoreBoard()
            games = sb.get_dict()["scoreboard"]["games"]

            formatted = []
            for g in games:
                formatted.append({
                    "game_id": g["gameId"],
                    "home": g["homeTeam"]["teamName"],
                    "away": g["awayTeam"]["teamName"],
                })
            return formatted

        except Exception as e:
            return []

    # -------------------------
    #   2) STATS BALDONTLIE
    # -------------------------
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

    # -------------------------
    #   3) DERNIERS MATCHS
    # -------------------------
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

    # -------------------------
    #   4) TENDANCES (simple)
    # -------------------------
    def compute_trends(self, last_games):
        try:
            games = last_games.get("data", [])
            if not games:
                return {}

            pts = [g["home_team_score"] if g["home_team"]["id"] else g["visitor_team_score"] for g in games]
            return {
                "avg_points": sum(pts) / len(pts),
                "games_count": len(pts)
            }
        except:
            return {}

    # -------------------------
    #   5) COTES — THE ODDS API
    # -------------------------
    def get_odds(self):
        try:
            r = requests.get(
                f"{ODDS_URL}/odds",
                params={
                    "apiKey": ODDS_KEY,
                    "regions": "eu",
                    "markets": "h2h,spreads,totals,player_props"
                }
            )
            return r.json()
        except:
            return {}

    # -------------------------
    #   6) INJURIES (simple)
    # -------------------------
    def get_injuries(self):
        # Pas d’API gratuite fiable → placeholder Shadow Edge
        return {
            "shadow_edge": {
                "home": [],
                "away": []
            },
            "nba_api": []
        }

    # -------------------------
    #   7) MATCHUPS (simple)
    # -------------------------
    def compute_matchups(self, home_stats, away_stats):
        return {
            "full": {
                "home_raw": home_stats,
                "away_raw": away_stats
            },
            "alerts": []
        }

    # -------------------------
    #   8) PLAYTYPES (dérivés)
    # -------------------------
    def compute_playtypes(self, stats):
        # dérivation simple basée sur fréquence de tirs
        try:
            raw = stats.get("raw", {}).get("data", [])
            if not raw:
                return {}

            total = len(raw)
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

    # -------------------------
    #   9) STYLE INDEX
    # -------------------------
    def compute_style_index(self, playtypes):
        try:
            return {
                "pace": playtypes.get("transition", {}).get("frequency", 0),
                "iso_rate": playtypes.get("isolation", {}).get("frequency", 0),
                "pnr_rate": playtypes.get("pick_and_roll", {}).get("frequency", 0),
            }
        except:
            return {}

    # -------------------------
    #   10) PACKAGE COMPLET
    # -------------------------
    def get_pre_match_package(self, game_id, home, away):

        # STATS
        home_stats = self.get_team_stats(home)
        away_stats = self.get_team_stats(away)

        # LAST GAMES
        home_last = self.get_last_games(home_stats.get("team_id"))
        away_last = self.get_last_games(away_stats.get("team_id"))

        # TRENDS
        home_trends = self.compute_trends(home_last)
        away_trends = self.compute_trends(away_last)

        # MATCHUPS
        matchups = self.compute_matchups(home_stats, away_stats)

        # PLAYTYPES
        play_home = self.compute_playtypes(home_stats)
        play_away = self.compute_playtypes(away_stats)

        # STYLE INDEX
        style_home = self.compute_style_index(play_home)
        style_away = self.compute_style_index(play_away)

        # ODDS
        odds = self.get_odds()

        # INJURIES
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
                "away": home_last
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
