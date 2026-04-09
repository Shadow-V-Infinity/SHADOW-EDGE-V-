# app/services/nba/live_service.py

from nba_api.live.nba.endpoints import scoreboard, boxscore
from app.services.nba.pre_match_service import PreMatchService


class NBALiveService:
    """
    Service LIVE ULTIME
    Fusion des deux versions :
    - Détection propre des matchs live
    - Leaders via boxscore live
    - Scoreboard live
    - Momentum Shadow Edge
    - Mismatchs Shadow Edge
    """

    def __init__(self):
        self.shadow = ShadowEdgePreMatchService()

    # ---------------------------------------------------------------
    # 1) Récupération des matchs en direct
    # ---------------------------------------------------------------
    def get_live_games(self):
        try:
            board = scoreboard.ScoreBoard().get_dict()
            games = board.get("scoreboard", {}).get("games", [])

            live_games = []
            for g in games:
                status = g.get("gameStatusText", "")

                # Match en cours si Q1/Q2/Q3/Q4/OT
                if any(x in status for x in ["Q1", "Q2", "Q3", "Q4", "OT"]):
                    game_id = g.get("gameId")

                    # Boxscore live (pour leaders)
                    try:
                        bs = boxscore.BoxScore(game_id).get_dict()
                        game_bs = bs.get("game", {})
                    except Exception:
                        game_bs = {}

                    home = g.get("homeTeam", {})
                    away = g.get("awayTeam", {})

                    live_games.append({
                        "game_id": game_id,
                        "status": status,
                        "home_team": home.get("teamName"),
                        "away_team": away.get("teamName"),
                        "home_score": home.get("score"),
                        "away_score": away.get("score"),
                        "clock": g.get("gameClock"),
                        "period": g.get("period"),

                        # Leaders fusionnés (scoreboard + boxscore)
                        "leaders": {
                            "home": game_bs.get("homeTeam", {}).get("leaders", {}) or home.get("leaders", {}),
                            "away": game_bs.get("awayTeam", {}).get("leaders", {}) or away.get("leaders", {}),
                        }
                    })

            return live_games

        except Exception as e:
            print(f"[NBALiveService] Erreur get_live_games: {e}")
            return []

    # ---------------------------------------------------------------
    # 2) Boxscore live complet
    # ---------------------------------------------------------------
    def get_boxscore(self, game_id):
        try:
            bs = boxscore.BoxScore(game_id).get_dict()
            return bs.get("game", {})
        except Exception:
            return {}

    # ---------------------------------------------------------------
    # 3) Momentum Shadow Edge
    # ---------------------------------------------------------------
    def get_momentum(self, game_id):
        try:
            return self.shadow.pbp.get_momentum_curve(game_id)
        except:
            return None

    # ---------------------------------------------------------------
    # 4) Mismatchs Shadow Edge
    # ---------------------------------------------------------------
    def get_mismatch_alerts(self, game_id):
        try:
            return self.shadow.matchups.get_mismatch_alerts(game_id)
        except:
            return []

