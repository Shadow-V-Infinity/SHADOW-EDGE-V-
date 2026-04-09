from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.nba import live as nba_live
from app.routers.nba import pre_match as nba_pre_match

app = FastAPI(
    title="Shadow Edge V∞",
    version="1.0.0",
    description="Moteur analytique multi-sport"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTERS
app.include_router(nba_live.router, prefix="/nba/live", tags=["NBA Live"])
app.include_router(nba_pre_match.router, prefix="/nba/pre_match", tags=["NBA Pre-Match"])

# FRONTEND STATIC (doit être APRÈS app = FastAPI)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Ton endpoint JSON doit être ailleurs que "/"
@app.get("/api")
def root():
    return {"status": "ok", "engine": "Shadow Edge V∞"}
