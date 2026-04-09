from fastapi import APIRouter
from app.services.nba.live_service import NBALiveService

router = APIRouter()
service = NBALiveService()

@router.get("/games")
def get_live_games():
    return service.get_live_games()

@router.get("/boxscore/{game_id}")
def get_boxscore(game_id: str):
    return service.get_boxscore(game_id)
