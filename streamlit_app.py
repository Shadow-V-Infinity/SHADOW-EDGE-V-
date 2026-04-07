import streamlit as st
from core.router import render_page

st.set_page_config(
    page_title="Shadow Edge V∞",
    layout="wide",
)

st.sidebar.title("Shadow Edge V∞")
page = st.sidebar.selectbox(
    "Navigation",
    [
        "🏀 NBA - Live",
        "🏀 NBA - Avant-match",
    ],
)

render_page(page)
