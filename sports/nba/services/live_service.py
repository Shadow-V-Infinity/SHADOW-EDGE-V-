from nba_api.live.nba.endpoints import scoreboard, boxscore


class NBALiveService:
    def __init__(self):
        pass

    def get_live_games(self):
        try:
            board = scoreboard.ScoreBoard()
            data = board.get_dict()

            games = data.get("scoreboard", {}).get("games", [])
            live_games = []

            for g in games:
                status = g.get("gameStatusText", "")

                # Match en cours si Q1/Q2/Q3/Q4/OT
                if any(x in status for x in ["Q1", "Q2", "Q3", "Q4", "OT"]):
                    game_id = g.get("gameId")

                    # Récupération du boxscore live
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
                        "leaders": {
                            "home": game_bs.get("homeTeam", {}).get("leaders", {}),
                            "away": game_bs.get("awayTeam", {}).get("leaders", {}),
                        }
                    })

            return live_games

        except Exception as e:
            print(f"[NBALiveService] Erreur: {e}")
            return []
