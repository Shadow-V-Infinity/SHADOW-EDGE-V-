from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import teamgamelog, commonteamroster, leaguedashteamstats
from nba_api.stats.static import teams


class NBAPreMatchService:
    def __init__(self):
        pass

    def get_match_preview(self, game_id: str):
        try:
            # 1) Récupération du scoreboard du jour
            board = scoreboard.ScoreBoard().get_dict()
            games = board.get("scoreboard", {}).get("games", [])

            game = next((g for g in games if g.get("gameId") == game_id), None)
            if not game:
                return {"error": "game_id introuvable pour aujourd’hui."}

            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})

            home_id = home.get("teamId")
            away_id = away.get("teamId")

            # 2) Blessures (via boxscore)
            try:
                bs = boxscore.BoxScore(game_id).get_dict()
                injuries = bs.get("game", {}).get("injuries", [])
            except Exception:
                injuries = []

            # 3) Lineups probables
            probable = {
                "home": home.get("probableStarters", []),
                "away": away.get("probableStarters", []),
            }

            # 4) Stats des équipes (ORTG / DRTG / Pace)
            stats = leaguedashteamstats.LeagueDashTeamStats().get_dict()
            rows = stats.get("resultSets", [])[0].get("rowSet", [])
            headers = stats.get("resultSets", [])[0].get("headers", [])

            def extract_team_stats(team_id):
                for r in rows:
                    if r[headers.index("TEAM_ID")] == team_id:
                        return {
                            "ORTG": r[headers.index("OFF_RATING")],
                            "DRTG": r[headers.index("DEF_RATING")],
                            "PACE": r[headers.index("PACE")],
                        }
                return {}

            home_stats = extract_team_stats(home_id)
            away_stats = extract_team_stats(away_id)

            return {
                "game_id": game_id,
                "home_team": home.get("teamName"),
                "away_team": away.get("teamName"),
                "game_time": game.get("gameStatusText"),
                "injuries": injuries,
                "probable_lineups": probable,
                "team_stats": {
                    "home": home_stats,
                    "away": away_stats,
                }
            }

        except Exception as e:
            print(f"[NBAPreMatchService] Erreur: {e}")
            return {"error": str(e)}
