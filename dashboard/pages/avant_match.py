from sports.nba.services.pre_match_service import PreMatchService
import streamlit as st

pre = PreMatchService()

def render(game_id, team_home, team_away):

    data = pre.get_pre_match_package(game_id, team_home, team_away)

    st.title("🏀 Avant‑Match — Shadow Edge V∞")
    st.subheader(f"{team_home} vs {team_away}")

    # Injuries
    st.header("🚑 Injuries")
    col1, col2 = st.columns(2)
    col1.dataframe(data["injuries"]["home"])
    col2.dataframe(data["injuries"]["away"])

    # Matchups
    st.header("🛡️ Matchups")
    st.dataframe(data["matchups"]["full"])
    st.markdown("### ⚠️ Mismatchs")
    st.dataframe(data["matchups"]["alerts"])

    # Play Types
    st.header("🎯 Play Types")
    col1, col2 = st.columns(2)
    col1.json(data["playtypes"]["home"])
    col2.json(data["playtypes"]["away"])

    # Tracking
    st.header("📡 Tracking Data")
    col1, col2 = st.columns(2)
    col1.json(data["tracking"]["home"])
    col2.json(data["tracking"]["away"])

    # PBP
    st.header("📈 Momentum & Runs")
    st.dataframe(data["pbp"]["runs"])
    st.line_chart(data["pbp"]["momentum"])

    # Props
    st.header("💸 Player Props")
    st.dataframe(data["props"])

    # Predictions
    st.header("🔮 Prédictions")
    pred = data["predictions"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Home Win %", f"{pred['home_win_prob']}%")
    col2.metric("Away Win %", f"{pred['away_win_prob']}%")
    col3.metric("Marge", pred["expected_margin"])
