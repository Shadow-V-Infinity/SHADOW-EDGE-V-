from fastapi import APIRouter
from nba_api.live.nba.endpoints import scoreboard
import os, requests

router = APIRouter()

BALLDONTLIE_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
BALL_URL = "https://api.balldontlie.io/v1"
HEADERS_BDL = {"Authorization": f"Bearer {BALLDONTLIE_KEY}"} if BALLDONTLIE_KEY else {}

@router.get("/games")
def get_today_games():
    try:
        sb = scoreboard.ScoreBoard()
        games = sb.get_dict()["scoreboard"]["games"]
        return [
            {
                "game_id":  g["gameId"],
                "homeTeam": g["homeTeam"]["teamName"],
                "awayTeam": g["awayTeam"]["teamName"],
                "status":   g.get("gameStatusText", ""),
            }
            for g in games
        ]
    except:
        return []

@router.get("/debug")
def debug():
    return {"status": "nba_pre_match_ok"}
