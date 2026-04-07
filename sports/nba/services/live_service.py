from datetime import datetime
from nba_api.live.nba.endpoints import scoreboard


class NBALiveService:
    def __init__(self):
        pass

    def get_live_games(self):
        try:
            # Récupère le scoreboard du jour
            board = scoreboard.ScoreBoard()
            data = board.get_dict()

            games = data.get("scoreboard", {}).get("games", [])

            live_games = []
            for g in games:
                game_status = g.get("gameStatusText", "")
                # Exemples de valeurs : "Final", "Q3 05:32", "Halftime", "7:00 pm ET"
                # On considère "live" si il y a un Q ou un temps restant
                if any(x in game_status for x in ["Q1", "Q2", "Q3", "Q4", "OT"]):
                    live_games.append({
                        "game_id": g.get("gameId"),
                        "home_team": g.get("homeTeam", {}).get("teamName"),
                        "away_team": g.get("awayTeam", {}).get("teamName"),
                        "home_score": g.get("homeTeam", {}).get("score"),
                        "away_score": g.get("awayTeam", {}).get("score"),
                        "status": game_status,
                    })

            return live_games

        except Exception as e:
            # En cas de problème, on loggera plus tard
            print(f"Erreur NBALiveService.get_live_games: {e}")
            return []
