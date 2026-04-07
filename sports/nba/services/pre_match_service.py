# sports/nba/services/pre_match_service.py

from sports.nba.services.shotchart_service import ShotChartService
from sports.nba.services.tracking_service import TrackingService
from sports.nba.services.pbp_analysis_service import PbpAnalysisService
from sports.nba.services.injury_service import InjuryService
from sports.nba.services.matchup_service import MatchupService
from sports.nba.services.playtype_service import PlayTypeService
from sports.nba.services.props_service import PropsService
from sports.nba.services.prediction_service import PredictionService

from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import teamgamelog, leaguedashteamstats
from sport.market_service import MarketService


class ShadowEdgePreMatchService:
    """
    Service AVANT-MATCH ULTIME
    Fusion de :
    - PreMatchService (Shadow Edge V∞)
    - NBAPreMatchService (nba_api + marché)
    """

    def __init__(self):
        # Modules Shadow Edge V∞
        self.shotchart = ShotChartService()
        self.tracking = TrackingService()
        self.pbp = PbpAnalysisService()
        self.injuries = InjuryService()
        self.matchups = MatchupService()
        self.playtypes = PlayTypeService()
        self.props = PropsService()
        self.predictions = PredictionService()

        # Modules NBA API + marché
        self.market_service = MarketService()

    # ---------------------------------------------------------------
    # 1) LISTE DES MATCHS DU JOUR
    # ---------------------------------------------------------------
    def get_today_games(self):
        try:
            board = scoreboard.ScoreBoard().get_dict()
            games = board.get("scoreboard", {}).get("games", [])

            return [
                {
                    "game_id": g.get("gameId"),
                    "home": g.get("homeTeam", {}).get("teamName"),
                    "away": g.get("awayTeam", {}).get("teamName"),
                }
                for g in games
            ]

        except Exception as e:
            print(f"[ShadowEdgePreMatchService] Erreur get_today_games: {e}")
            return []

    # ---------------------------------------------------------------
    # 2) DERNIERS MATCHS + TENDANCES
    # ---------------------------------------------------------------
    def get_last_games(self, team_id, n=5):
        try:
            logs = teamgamelog.TeamGameLog(team_id=team_id).get_dict()
            rows = logs["resultSets"][0]["rowSet"]
            headers = logs["resultSets"][0]["headers"]

            return [
                {
                    "matchup": r[headers.index("MATCHUP")],
                    "points": r[headers.index("PTS")],
                    "points_allowed": r[headers.index("PTS_ALLOWED")],
                    "result": r[headers.index("WL")],
                }
                for r in rows[:n]
            ]
        except Exception:
            return []

    def compute_trends(self, games):
        if not games:
            return {}

        pts = [g["points"] for g in games]
        pts_allowed = [g["points_allowed"] for g in games]
        wins = sum(1 for g in games if g["result"] == "W")

        return {
            "avg_points": sum(pts) / len(pts),
            "avg_points_allowed": sum(pts_allowed) / len(pts_allowed),
            "wins_last_games": wins,
        }

    # ---------------------------------------------------------------
    # 3) PACK COMPLET AVANT-MATCH
    # ---------------------------------------------------------------
    def get_pre_match_package(self, game_id: str, team_home: str, team_away: str):
        """
        Retourne TOUT ce qu'il faut pour la page Avant‑match.
        Combine Shadow Edge V∞ + NBA API + Marché.
        """

        # ---------------- NBA API ----------------
        board = scoreboard.ScoreBoard().get_dict()
        games = board.get("scoreboard", {}).get("games", [])
        game = next((g for g in games if g.get("gameId") == game_id), None)

        if not game:
            return {"error": "game_id introuvable pour aujourd’hui."}

        home = game.get("homeTeam", {})
        away = game.get("awayTeam", {})

        home_id = home.get("teamId")
        away_id = away.get("teamId")

        # Blessures NBA API
        try:
            bs = boxscore.BoxScore(game_id).get_dict()
            nba_injuries = bs.get("game", {}).get("injuries", [])
        except Exception:
            nba_injuries = []

        # Stats officielles NBA
        stats = leaguedashteamstats.LeagueDashTeamStats().get_dict()
        rows = stats["resultSets"][0]["rowSet"]
        headers = stats["resultSets"][0]["headers"]

        def extract_team_stats(team_id):
            for r in rows:
                if r[headers.index("TEAM_ID")] == team_id:
                    def safe(col):
                        return r[headers.index(col)] if col in headers else None
                    return {
                        "PTS": safe("PTS"),
                        "REB": safe("REB"),
                        "AST": safe("AST"),
                        "W_PCT": safe("W_PCT"),
                    }
            return {}

        home_stats = extract_team_stats(home_id)
        away_stats = extract_team_stats(away_id)

        # Tendances
        home_last = self.get_last_games(home_id)
        away_last = self.get_last_games(away_id)
        home_trends = self.compute_trends(home_last)
        away_trends = self.compute_trends(away_last)

        # Mini modèle simple
        home_wp = home_stats.get("W_PCT", 0) or 0
        away_wp = away_stats.get("W_PCT", 0) or 0

        if home_wp > away_wp + 0.05:
            simple_prediction = f"{home.get('teamName')} léger avantage"
        elif away_wp > home_wp + 0.05:
            simple_prediction = f"{away.get('teamName')} léger avantage"
        else:
            simple_prediction = "Équilibré"

        # Probabilité modèle simple
        model_home_prob = home_wp / (home_wp + away_wp) if (home_wp + away_wp) > 0 else None

        # Analyse marché
        market_analysis = self.market_service.analyze_match(
            home.get("teamName"),
            away.get("teamName"),
            model_home_prob=model_home_prob,
        )

        # ---------------- SHADOW EDGE V∞ ----------------
        return {
            "game_id": game_id,
            "teams": {
                "home": home.get("teamName"),
                "away": away.get("teamName"),
            },

            # Injuries Shadow Edge + NBA API
            "injuries": {
                "shadow_edge": {
                    "home": self.injuries.get_team_injuries(team_home),
                    "away": self.injuries.get_team_injuries(team_away),
                },
                "nba_api": nba_injuries,
            },

            # Matchups
            "matchups": {
                "full": self.matchups.get_matchups(game_id),
                "alerts": self.matchups.get_mismatch_alerts(game_id),
            },

            # Play Types
            "playtypes": {
                "home": self.playtypes.get_team_playtypes(team_home),
                "away": self.playtypes.get_team_playtypes(team_away),
            },

            # Tracking
            "tracking": {
                "home": self.tracking.get_team_tracking(team_home, "2024-25"),
                "away": self.tracking.get_team_tracking(team_away, "2024-25"),
            },

            # PBP
            "pbp": {
                "runs": self.pbp.get_runs(game_id),
                "momentum": self.pbp.get_momentum_curve(game_id),
            },

            # Props
            "props": self.props.get_player_props(game_id),

            # Predictions Shadow Edge
            "predictions": self.predictions.get_game_prediction(game_id),

            # NBA API stats
            "team_stats": {
                "home": home_stats,
                "away": away_stats,
            },

            # Tendances
            "last_games": {
                "home": home_last,
                "away": away_last,
            },
            "trends": {
                "home": home_trends,
                "away": away_trends,
            },

            # Mini modèle simple
            "simple_prediction": simple_prediction,

            # Analyse marché
            "market_analysis": market_analysis,
        }
