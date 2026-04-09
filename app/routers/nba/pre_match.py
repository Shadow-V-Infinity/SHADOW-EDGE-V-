from fastapi import APIRouter, Query
from app.services.nba.pre_match_service import ShadowEdgePreMatchService

router = APIRouter()
service = ShadowEdgePreMatchService()


@router.get("/games")
def games():
    """Liste des matchs du jour."""
    return service.get_today_games()


@router.get("/package")
def pre_match_package(
    game_id: str = Query(..., description="ID du match"),
    home:    str = Query(..., description="Nom équipe domicile"),
    away:    str = Query(..., description="Nom équipe extérieur"),
):
    """Package complet avant-match."""
    return service.get_pre_match_package(game_id, home, away)


@router.get("/debug")
def debug():
    return {"status": "pre_match_router_ok"}
