from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json
import os
from datetime import date

app = FastAPI(
    title="Shadow Edge V∞",
    version="2.0.0",
    description="Moteur analytique multi-sport"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Stockage en mémoire ─────────────────────────────────
store = {
    "football":   {"date": None, "matches": [], "top10": []},
    "basketball": {"date": None, "matches": [], "top10": []},
    "tennis":     {"date": None, "matches": [], "top10": []},
    "hockey":     {"date": None, "matches": [], "top10": []},
    "rugby":      {"date": None, "matches": [], "top10": []},
}

# ── INGEST — Termux envoie les données ──────────────────
@app.post("/ingest/{sport}")
def ingest(sport: str, data: dict):
    if sport not in store:
        return {"error": f"Sport inconnu: {sport}"}
    matches = data.get("matches", [])
    top10   = sorted(
        [m for m in matches if m.get("verdict", "") != "⚪ Pas de value"],
        key=lambda x: x.get("shadow_score", 0),
        reverse=True
    )[:10]
    store[sport] = {
        "date":    data.get("date", str(date.today())),
        "matches": matches,
        "top10":   top10,
    }
    return {"status": "ok", "sport": sport, "matches": len(matches)}

# ── GET DATA ────────────────────────────────────────────
@app.get("/data/{sport}")
def get_data(sport: str):
    if sport not in store:
        return {"error": f"Sport inconnu: {sport}"}
    return store[sport]

@app.get("/data/{sport}/top10")
def get_top10(sport: str):
    if sport not in store:
        return {"error": f"Sport inconnu: {sport}"}
    return store[sport]["top10"]

@app.get("/data/all/summary")
def get_summary():
    return {
        sport: {
            "date":    store[sport]["date"],
            "count":   len(store[sport]["matches"]),
            "top_pick": store[sport]["top10"][0] if store[sport]["top10"] else None,
        }
        for sport in store
    }

# ── NBA LIVE (existant) ──────────────────────────────────
from app.routers import nba_live, nba_pre_match

app.include_router(nba_live.router,      prefix="/nba/live",      tags=["NBA Live"])
app.include_router(nba_pre_match.router, prefix="/nba/pre_match", tags=["NBA Pre-Match"])

# ── FRONTEND ────────────────────────────────────────────
app.mount("/live",       StaticFiles(directory="frontend/live",       html=True), name="live")
app.mount("/pre_match",  StaticFiles(directory="frontend/pre_match",  html=True), name="pre_match")
app.mount("/basketball", StaticFiles(directory="frontend/basketball", html=True), name="basketball")
app.mount("/tennis",     StaticFiles(directory="frontend/tennis",     html=True), name="tennis")
app.mount("/hockey",     StaticFiles(directory="frontend/hockey",     html=True), name="hockey")
app.mount("/rugby",      StaticFiles(directory="frontend/rugby",      html=True), name="rugby")
app.mount("/",           StaticFiles(directory="frontend",            html=True), name="frontend")

@app.get("/api")
def root():
    return {"status": "ok", "engine": "Shadow Edge V∞ 2.0"}
