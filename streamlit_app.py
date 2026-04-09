import streamlit as st
from sports.nba.pages.live import live_page
from sports.nba.pages.avant_match import avant_match_page

st.set_page_config(
    page_title="Shadow Edge V∞",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Shadow Edge V∞ — Dashboard")
st.write("Bienvenue dans ton interface Streamlit déployée sur Railway.")
st.sidebar.title("Shadow Edge V∞")

page = st.sidebar.selectbox(
    "Navigation",
    [
        "🏀 NBA - Live",
        "🏀 NBA - Avant-match",
    ],
)

if page == "🏀 NBA - Live":
    live_page()
elif page == "🏀 NBA - Avant-match":
    avant_match_page()
