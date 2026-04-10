# app/services/nba/pre_match_service.py

import os
from datetime import datetime

import requests
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguedashteamstats

from app.services.nba.prediction_service import PredictionService
from app.services.nba.trends_service import TrendsService
from app.services.nba.betting_radar import BettingRadar
from app.services.nba.injury_service import InjuryService
from app.services.nba.matchup_service import MatchupService
from app.services.nba.ppb_analysis_service import PpbAnalysisService
from app.services.nba.props_service import PropsService

BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
ODDS_KEY = os.getenv("ODDS_API_KEY", "")

BALL_URL = "https://api.balldontlie.io/v1"
ODDS_URL = "https://api.the-odds-api.com/v4/sports/basketball_nba"

HEADERS_BDL = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}


class ShadowEdgePreMatchService:
    def __init__(self):
        self.predictions = PredictionService()
        self.trends = TrendsService()
        self.radar = BettingRadar()
        self.injuries = InjuryService()
        self.matchups = MatchupService()
        self.ppb = PpbAnalysisService()
        self.props = PropsService()
        self._team_stats_cache: dict[str, dict] = {}  # cache pour éviter les appels répétés

    # 1) Matchs du jour - avec stats enrichies
    def get_today_games(self, day: str = None):
        """
        Retourne les matchs du jour avec stats réelles + fallbacks propres.
        Compatible frontend Shadow Edge V∞.
        :param day: date au format 'YYYY-MM-DD'. Si None, utilise aujourd'hui (heure NBA = US Eastern).
        """
        try:
            # Scoreboard avec date optionnelle
            if day:
                sb = scoreboard.ScoreBoard(game_date=day)
            else:
                sb = scoreboard.ScoreBoard()

            games = sb.get_dict()["scoreboard"]["games"]
            if not games:
                return []

            # Charger les stats de la ligue une seule fois (plus efficace)
            league_stats = self._get_league_team_stats()

            result = []
            for g in games:
                home_tri = g["homeTeam"]["teamTricode"]  # ex: "BOS"
                away_tri = g["awayTeam"]["teamTricode"]

                home_full = g["homeTeam"]["teamName"]  # ex: "Celtics"
                away_full = g["awayTeam"]["teamName"]

                # Stats depuis nba_api league dashboard
                home_s = league_stats.get(home_tri, {})
                away_s = league_stats.get(away_tri, {})

                # Derniers matchs BallDontLie pour la forme
                home_bdl = self.get_team_stats(home_full)
                home_last = self.get_last_games(home_bdl.get("team_id"))
                home_trends = self.compute_trends(home_last)

                away_bdl = self.get_team_stats(away_full)
                away_last = self.get_last_games(away_bdl.get("team_id"))
                away_trends = self.compute_trends(away_last)

                # Fallbacks propres
                pace_home = home_s.get("pace", 0)
                off_home = home_s.get("off_rating", 0)
                def_home = home_s.get("def_rating", 0)
                form_home = home_trends.get("avg_total_points", 0)

                pace_away = away_s.get("pace", 0)
                off_away = away_s.get("off_rating", 0)
                def_away = away_s.get("def_rating", 0)
                form_away = away_trends.get("avg_total_points", 0)

                result.append(
                    {
                        "game_id": g["gameId"],
                        "homeTeam": home_full,
                        "awayTeam": away_full,
                        "status": g.get("gameStatusText", ""),
                        # Stats domicile
                        "home": {
                            "pace": pace_home,
                            "off_rating": off_home,
                            "def_rating": def_home,
                            "form": form_home,
                            "wins": home_s.get("wins", 0),
                            "losses": home_s.get("losses", 0),
                        },
                        # Stats extérieur
                        "away": {
                            "pace": pace_away,
                            "off_rating": off_away,
                            "def_rating": def_away,
                            "form": form_away,
                            "wins": away_s.get("wins", 0),
                            "losses": away_s.get("losses", 0),
                        },
                        # Champs racines pour compat frontend existant
                        "pace": pace_home,
                        "off_rating": off_home,
                        "def_rating": def_home,
                        "form": form_home,
                    }
                )

            return result

        except Exception as e:
            print(f"[PreMatchService] get_today_games error: {e}")
            return []

    # 1b) Stats ligue via nba_api (Pace, OffRtg, DefRtg, W, L)
    def _get_league_team_stats(self) -> dict:
        """
        Retourne un dict { tricode: { pace, off_rating, def_rating, wins, losses } }
        Utilise nba_api LeagueDashTeamStats (saison en cours).
        """
        if self._team_stats_cache:
            return self._team_stats_cache

        try:
            # Saison dynamique type "2024-25"
            year = datetime.now().year
            season = f"{year-1}-{str(year)[-2:]}"
            stats = leaguedashteamstats.LeagueDashTeamStats(
                measure_type_simple="Advanced",
                per_mode_simple="PerGame",
                season=season,
                timeout=30,
            )
            df = stats.get_data_frames()[0]

            for _, row in df.iterrows():
                tricode = row.get("TEAM_ABBREVIATION", "")
                if not tricode:
                    continue
                self._team_stats_cache[tricode] = {
                    "pace": round(float(row.get("PACE", 0) or 0), 1),
                    "off_rating": round(float(row.get("OFF_RATING", 0) or 0), 1),
                    "def_rating": round(float(row.get("DEF_RATING", 0) or 0), 1),
                    "wins": int(row.get("W", 0) or 0),
                    "losses": int(row.get("L", 0) or 0),
                }

        except Exception as e:
            print(f"[PreMatchService] _get_league_team_stats error: {e}")

        return self._team_stats_cache

    # 2) Stats BallDontLie
    def get_team_stats(self, team_name: str) -> dict:
        try:
            r = requests.get(
                f"{BALL_URL}/teams",
                headers=HEADERS_BDL,
                params={"search": team_name},
                timeout=5,
            )
            data = r.json()
            if not data.get("data"):
                return {}

            team_id = data["data"][0]["id"]
            stats = requests.get(
                f"{BALL_URL}/stats",
                headers=HEADERS_BDL,
                params={"team_ids[]": team_id, "per_page": 100},
                timeout=5,
            ).json()
            return {"team_id": team_id, "raw": stats}

        except Exception as e:
            print(f"[PreMatchService] get_team_stats({team_name}) error: {e}")
            return {}

    # 3) Derniers matchs
    def get_last_games(self, team_id) -> dict:
        if not team_id:
            return {}
        try:
            r = requests.get(
                f"{BALL_URL}/games",
                headers=HEADERS_BDL,
                params={"team_ids[]": team_id, "per_page": 5},
                timeout=5,
            )
            return r.json()
        except Exception as e:
            print(f"[PreMatchService] get_last_games error: {e}")
            return {}

    # 4) Tendances
    def compute_trends(self, last_games: dict) -> dict:
        try:
            games = last_games.get("data", [])
            if not games:
                return {}
            pts = [
                g["home_team_score"] + g["visitor_team_score"]
                for g in games
            ]
            return {
                "avg_total_points": round(sum(pts) / len(pts), 1),
                "games_count": len(pts),
            }
        except Exception as e:
            print(f"[PreMatchService] compute_trends error: {e}")
            return {}

    # 5) Odds
    def get_odds(self) -> dict:
        if not ODDS_KEY:
            return {}
        try:
            r = requests.get(
                f"{ODDS_URL}/odds",
                params={
                    "apiKey": ODDS_KEY,
                    "regions": "eu",
                    "markets": "h2h,spreads,totals",
                },
                timeout=5,
            )
            return r.json()
        except Exception as e:
            print(f"[PreMatchService] get_odds error: {e}")
            return {}

    # 6) Playtypes (placeholder stable)
    def compute_playtypes(self, stats: dict) -> dict:
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

    # 7) Style index
    def compute_style_index(self, playtypes: dict) -> dict:
        return {
            "pace": playtypes.get("transition", {}).get("frequency", 0),
            "iso_rate": playtypes.get("isolation", {}).get("frequency", 0),
            "pnr_rate": playtypes.get("pick_and_roll", {}).get("frequency", 0),
        }

    # 7b) Alerts / mismatch (wrapper MatchupService)
    def get_mismatch_alerts(self, game_id: str) -> dict:
        try:
            return self.matchups.get_mismatch_alerts(game_id)
        except Exception as e:
            print(f"[PreMatchService] get_mismatch_alerts({game_id}) error: {e}")
            return {}

    # 8) Package complet
    def get_pre_match_package(self, game_id: str, home: str, away: str) -> dict:
        home_stats = self.get_team_stats(home)
        away_stats = self.get_team_stats(away)

        home_last = self.get_last_games(home_stats.get("team_id"))
        away_last = self.get_last_games(away_stats.get("team_id"))

        home_trends = self.compute_trends(home_last)
        away_trends = self.compute_trends(away_last)

        play_home = self.compute_playtypes(home_stats)
        play_away = self.compute_playtypes(away_stats)

        style_home = self.compute_style_index(play_home)
        style_away = self.compute_style_index(play_away)

        # Stats avancées via nba_api pour le package complet
        league_stats = self._get_league_team_stats()
        odds = self.get_odds()
        injuries = self.injuries.get_all_injuries()

        prediction = self.predictions.get_game_prediction(game_id)
        simulation = self.predictions.simulate_game(game_id)
        trend_data = self.trends.get_trends(game_id)

        return {
            "game_id": game_id,
            "injuries": injuries,
            "matchups": {
                "full": {"home_raw": home_stats, "away_raw": away_stats},
                "alerts": self.get_mismatch_alerts(game_id),
            },
            "team_stats": {
                "home": home_stats,
                "away": away_stats,
                "league": league_stats,
            },
            "trends": {
                "home": home_trends,
                "away": away_trends,
                "shadow": trend_data,
            },
            "playtypes": {"home": play_home, "away": play_away},
            "style_index": {"home": style_home, "away": style_away},
            "prediction": prediction,
            "simulation": simulation,
            "props": self.props.get_player_props(game_id),
            "market_analysis": odds,
            "pbp": {},
        }
