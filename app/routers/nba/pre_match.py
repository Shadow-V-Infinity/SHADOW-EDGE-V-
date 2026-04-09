from fastapi import APIRouter, Query
from app.services.nba.pre_match_service import ShadowEdgePreMatchService

router = APIRouter()
service = ShadowEdgePreMatchService()

@router.get("/today")
def today_games():
    return service.get_today_games()

@router.get("/package")
def pre_match_package(
    game_id: str = Query(...),
    home: str = Query(...),
    away: str = Query(...),
):
    return service.get_pre_match_package(game_id, home, away)
