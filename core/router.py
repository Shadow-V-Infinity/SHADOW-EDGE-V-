import streamlit as st
from sports.nba.pages import live as nba_live
from sports.nba.pages import avant_match as nba_avant_match

def render_page(page: str):
    if page == "🏀 NBA - Live":
        nba_live.render()
    elif page == "🏀 NBA - Avant-match":
        nba_avant_match.render()
    else:
        st.write("Page non trouvée.")
