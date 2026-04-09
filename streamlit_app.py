import streamlit as st

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

render_page(page)
