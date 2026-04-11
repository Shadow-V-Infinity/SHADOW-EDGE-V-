from fastapi import APIRouter
from nba_api.live.nba.endpoints import scoreboard, boxscore

router = APIRouter()

@router.get("/games")
def get_live_games():
    try:
        board = scoreboard.ScoreBoard().get_dict()
        games = board.get("scoreboard", {}).get("games", [])
        live  = []
        for g in games:
            status = g.get("gameStatusText", "")
            if not any(x in status for x in ["Q1","Q2","Q3","Q4","OT"]):
                continue
            game_id = g.get("gameId")
            try:
                bs = boxscore.BoxScore(game_id).get_dict()
                game_bs = bs.get("game", {})
            except:
                game_bs = {}
            home = g.get("homeTeam", {})
            away = g.get("awayTeam", {})
            live.append({
                "game_id":    game_id,
                "status":     status,
                "home_team":  home.get("teamName"),
                "away_team":  away.get("teamName"),
                "home_score": home.get("score"),
                "away_score": away.get("score"),
                "clock":      g.get("gameClock"),
                "period":     g.get("period"),
                "leaders": {
                    "home": game_bs.get("homeTeam", {}).get("leaders", {}) or home.get("leaders", {}),
                    "away": game_bs.get("awayTeam", {}).get("leaders", {}) or away.get("leaders", {}),
                }
            })
        return live
    except Exception as e:
        return []

@router.get("/boxscore/{game_id}")
def get_boxscore(game_id: str):
    try:
        bs = boxscore.BoxScore(game_id).get_dict()
        return bs.get("game", {})
    except:
        return {}
