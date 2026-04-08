import streamlit as st
from sports.nba.services.pre_match_service import PreMatchService

st.title("🔥 Betting Radar — Shadow Edge V∞")

pre = PreMatchService()

st.markdown("### 🏀 Sélection du match")
game_id = st.text_input("Game ID", "")

if game_id:
    data = pre.get_pre_match_package(game_id, None, None)

    st.markdown("## 📊 Analyse du Marché")
    st.json(data["market_analysis"])

    st.markdown("## 🎯 Value Bets")
    if data["props"]:
        st.json(data["props"])
    else:
        st.info("Aucune value détectée pour le moment.")

    st.markdown("## 🧠 Prédictions")
    col1, col2 = st.columns(2)
    col1.metric("Home Win %", data["predictions"]["home_win_prob"])
    col2.metric("Away Win %", data["predictions"]["away_win_prob"])

    st.markdown("## ⚡ Matchup Alerts")
    if data["matchups"]["alerts"]:
        st.json(data["matchups"]["alerts"])
    else:
        st.success("Aucune alerte détectée.")

    st.markdown("## 📈 Tendances")
    col1, col2 = st.columns(2)
    col1.write(data["trends"]["home"])
    col2.write(data["trends"]["away"])

st.markdown("---")
st.caption("Shadow Edge V∞ — Betting Radar en construction 🚧")
