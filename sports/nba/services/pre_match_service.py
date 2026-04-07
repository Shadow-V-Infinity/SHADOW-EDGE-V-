from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import teamgamelog, leaguedashteamstats
from market.market_service import MarketService

class NBAPreMatchService:
    def __init__(self):
        self.market_service = MarketService()

    def get_match_preview(self, game_id: str):
        # ... ton code actuel ...

        # Probabilité modèle simple (basée sur W_PCT)
        home_wp = home_stats.get("W_PCT", 0)
        away_wp = away_stats.get("W_PCT", 0)
        model_home_prob = home_wp / (home_wp + away_wp) if (home_wp + away_wp) > 0 else None

        preview["market_analysis"] = self.market_service.analyze_match(
            home.get("teamName"),
            away.get("teamName"),
            model_home_prob=model_home_prob,
        )

        return preview

    def get_today_games(self):
        """Retourne la liste des matchs du jour (game_id + noms des équipes)."""
        try:
            board = scoreboard.ScoreBoard().get_dict()
            games = board.get("scoreboard", {}).get("games", [])

            match_list = []
            for g in games:
                match_list.append({
                    "game_id": g.get("gameId"),
                    "home": g.get("homeTeam", {}).get("teamName"),
                    "away": g.get("awayTeam", {}).get("teamName"),
                })
            return match_list

        except Exception as e:
            print(f"[NBAPreMatchService] Erreur get_today_games: {e}")
            return []

    def get_last_games(self, team_id, n=5):
        """Retourne les N derniers matchs d’une équipe."""
        try:
            logs = teamgamelog.TeamGameLog(team_id=team_id).get_dict()
            rows = logs["resultSets"][0]["rowSet"]
            headers = logs["resultSets"][0]["headers"]

            games = []
            for r in rows[:n]:
                games.append({
                    "matchup": r[headers.index("MATCHUP")],
                    "points": r[headers.index("PTS")],
                    "points_allowed": r[headers.index("PTS_ALLOWED")],
                    "result": r[headers.index("WL")],
                })
            return games
        except Exception:
            return []

    def compute_trends(self, games):
        """Calcule les tendances sur les derniers matchs."""
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

    def get_match_preview(self, game_id: str):
        try:
            board = scoreboard.ScoreBoard().get_dict()
            games = board.get("scoreboard", {}).get("games", [])

            game = next((g for g in games if g.get("gameId") == game_id), None)
            if not game:
                return {"error": "game_id introuvable pour aujourd’hui."}

            home = game.get("homeTeam", {})
            away = game.get("awayTeam", {})

            home_id = home.get("teamId")
            away_id = away.get("teamId")

            # Blessures
            try:
                bs = boxscore.BoxScore(game_id).get_dict()
                injuries = bs.get("game", {}).get("injuries", [])
            except Exception:
                injuries = []

            # Lineups probables
            probable = {
                "home": home.get("probableStarters", []),
                "away": away.get("probableStarters", []),
            }

            # Stats (version basique compatible Termux)
            stats = leaguedashteamstats.LeagueDashTeamStats().get_dict()
            rows = stats["resultSets"][0]["rowSet"]
            headers = stats["resultSets"][0]["headers"]

            def extract_team_stats(team_id):
                for r in rows:
                    if r[headers.index("TEAM_ID")] == team_id:

                        def safe(col):
                            return r[headers.index(col)] if col in headers else None

                        # Fallback universel : stats toujours présentes
                        return {
                            "PTS": safe("PTS"),
                            "REB": safe("REB"),
                            "AST": safe("AST"),
                            "W_PCT": safe("W_PCT"),
                        }
                return {}

            home_stats = extract_team_stats(home_id)
            away_stats = extract_team_stats(away_id)

            # 5 derniers matchs + tendances
            home_last = self.get_last_games(home_id)
            away_last = self.get_last_games(away_id)
            home_trends = self.compute_trends(home_last)
            away_trends = self.compute_trends(away_last)

            # Mini prédiction basée sur W_PCT (toujours dispo)
            prediction = "Équilibré"
            if home_stats.get("W_PCT", 0) > away_stats.get("W_PCT", 0) + 0.05:
                prediction = f"{home.get('teamName')} léger avantage"
            elif away_stats.get("W_PCT", 0) > home_stats.get("W_PCT", 0) + 0.05:
                prediction = f"{away.get('teamName')} léger avantage"

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
                },
                "last_games": {
                    "home": home_last,
                    "away": away_last,
                },
                "trends": {
                    "home": home_trends,
                    "away": away_trends,
                },
                "prediction": prediction,
            }

        except Exception as e:
            print(f"[NBAPreMatchService] Erreur: {e}")
            return {"error": str(e)}
