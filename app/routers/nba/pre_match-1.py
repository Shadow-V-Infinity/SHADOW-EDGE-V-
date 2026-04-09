# app/routers/nba/pre_match.py

from fastapi import APIRouter, Query
from app.services.nba.pre_match_service import ShadowEdgePreMatchService

router = APIRouter()
service = ShadowEdgePreMatchService()


@router.get("/games")
def games(
    day: str = Query(
        default=None,
        description="Date des matchs au format YYYY-MM-DD. Si absent, matchs du jour NBA (heure US)."
    )
):
    """
    Liste des matchs du jour avec stats enrichies (Pace, OffRtg, DefRtg, Forme).
    Exemple: /nba/pre_match/games?day=2026-04-10
    """
    return service.get_today_games(day=day)


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
