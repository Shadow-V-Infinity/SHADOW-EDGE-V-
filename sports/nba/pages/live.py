import streamlit as st
from sports.nba.services.live_service import NBALiveService

service = NBALiveService()

def live_page():
    st.title("📡 LIVE — Shadow Edge V∞")

    games = service.get_live_games()

    if not games:
        st.info("Aucun match en direct pour le moment.")
        return

    # Sélection du match
    game_names = [f"{g['away_team']} @ {g['home_team']}" for g in games]
    selected = st.selectbox("Match en cours", game_names)

    idx = game_names.index(selected)
    game = games[idx]
    game_id = game["game_id"]

    # ---------------------------------------------------------------
    # SCORE
    # ---------------------------------------------------------------
    st.header("🏀 Score")
    col1, col2 = st.columns(2)
    col1.metric(game["home_team"], game["home_score"])
    col2.metric(game["away_team"], game["away_score"])

    st.caption(f"Période : {game['period']} — Horloge : {game['clock']} — Statut : {game['status']}")

    # ---------------------------------------------------------------
    # LEADERS
    # ---------------------------------------------------------------
    st.header("🔥 Leaders")
    col1, col2 = st.columns(2)
    col1.subheader("🏠 Home")
    col1.json(game["leaders"]["home"])
    col2.subheader("🛫 Away")
    col2.json(game["leaders"]["away"])

    # ---------------------------------------------------------------
    # BOXSCORE LIVE
    # ---------------------------------------------------------------
    st.header("📊 Boxscore Live")
    bs = service.get_boxscore(game_id)
    st.json(bs)

    # ---------------------------------------------------------------
    # MOMENTUM
    # ---------------------------------------------------------------
    st.header("📈 Momentum Live")
    momentum = service.get_momentum(game_id)
    if momentum:
        st.line_chart(momentum)
    else:
        st.info("Momentum non disponible.")

    # ---------------------------------------------------------------
    # MISMATCH ALERTS
    # ---------------------------------------------------------------
    st.header("⚠️ Mismatchs détectés")
    alerts = service.get_mismatch_alerts(game_id)
    if alerts:
        st.dataframe(alerts)
    else:
        st.info("Aucun mismatch détecté.")
