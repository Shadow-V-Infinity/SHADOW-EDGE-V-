from fastapi import APIRouter
from app.services.nba.live_service import NBALiveService

router = APIRouter()
service = NBALiveService()


@router.get("/games")
def get_live_games():
    """Matchs en cours (Q1/Q2/Q3/Q4/OT)."""
    return service.get_live_games()


@router.get("/boxscore/{game_id}")
def get_boxscore(game_id: str):
    """Boxscore live complet."""
    return service.get_boxscore(game_id)


@router.get("/momentum/{game_id}")
def get_momentum(game_id: str):
    """Courbe de momentum Shadow Edge."""
    return service.get_momentum(game_id)


@router.get("/mismatches/{game_id}")
def get_mismatches(game_id: str):
    """Alertes mismatch Shadow Edge."""
    return service.get_mismatch_alerts(game_id)
