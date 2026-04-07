import streamlit as st
from sports.nba.services.pre_match_service import NBAPreMatchService

def render():
    st.title("🧬 Avant-match NBA")
    service = NBAPreMatchService()

    game_id = st.text_input("ID du match (ou sélection à venir)")

    if not game_id:
        st.info("Entre un game_id pour voir l’avant-match.")
        return

    preview = service.get_match_preview(game_id)

    if not preview:
        st.warning("Aucune donnée trouvée pour ce match.")
        return

    st.subheader(preview["title"])
    st.write(preview["summary"])
