import streamlit as st
from sports.nba.services.live_service import NBALiveService

def render():
    st.title("🏀 NBA Live")
    service = NBALiveService()

    games = service.get_live_games()

    if not games:
        st.info("Aucun match en direct pour le moment.")
        return

    for game in games:
        st.subheader(f"{game['home_team']} vs {game['away_team']}")
        st.write(f"Score : {game['home_score']} - {game['away_score']}")
