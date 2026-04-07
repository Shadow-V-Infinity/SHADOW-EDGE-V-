import streamlit as st
from sports.nba.services.pre_match_service import ShadowEdgePreMatchService

pre = ShadowEdgePreMatchService()

def render():
    st.title("💸 Betting Radar — Shadow Edge V∞")

    games = pre.get_today_games()
    game_names = [f"{g['away']} @ {g['home']}" for g in games]
    selected = st.selectbox("Sélectionne un match", game_names)

    if not selected:
        return

    idx = game_names.index(selected)
    game = games[idx]

    game_id = game["game_id"]
    home = game["home"]
    away = game["away"]

    data = pre.get_pre_match_package(game_id, home, away)

    # Marché
    st.header("💹 Analyse Marché")
    st.json(data["market_analysis"])

    # Props Value
    st.header("🎯 Props Value")
    st.dataframe(data["props"])

    # Predictions
    st.header("🔮 Modèle Shadow Edge")
    pred = data["predictions"]
    st.metric("Home Win %", f"{pred['home_win_prob']}%")
    st.metric("Away Win %", f"{pred['away_win_prob']}%")

    # Mismatchs
    st.header("⚠️ Mismatchs")
    st.dataframe(data["matchups"]["alerts"])

    # Tendances
    st.header("📊 Tendances")
    col1, col2 = st.columns(2)
    col1.json(data["trends"]["home"])
    col2.json(data["trends"]["away"])
