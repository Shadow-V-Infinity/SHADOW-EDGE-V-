import streamlit as st
from sports.nba.services.pre_match_service import ShadowEdgePreMatchService

pre = ShadowEdgePreMatchService()

def render():
    st.title("🏀 Avant‑Match — Shadow Edge V∞")

    # ---------------------------------------------------------------
    # 1) Sélection du match
    # ---------------------------------------------------------------
    games = pre.get_today_games()

    if not games:
        st.info("Aucun match aujourd’hui.")
        return

    game_names = [f"{g['away']} @ {g['home']}" for g in games]
    selected = st.selectbox("Sélectionne un match", game_names)

    if not selected:
        return

    idx = game_names.index(selected)
    game = games[idx]

    game_id = game["game_id"]
    home = game["home"]
    away = game["away"]

    # ---------------------------------------------------------------
    # 2) Chargement du pack complet
    # ---------------------------------------------------------------
    data = pre.get_pre_match_package(game_id, home, away)

    # ---------------------------------------------------------------
    # 3) Injuries
    # ---------------------------------------------------------------
    st.header("🚑 Injuries")

    col1, col2 = st.columns(2)
    col1.subheader(home)
    col1.dataframe(data["injuries"]["shadow_edge"]["home"])

    col2.subheader(away)
    col2.dataframe(data["injuries"]["shadow_edge"]["away"])

    # ---------------------------------------------------------------
    # 4) Matchups
    # ---------------------------------------------------------------
    st.header("🛡️ Matchups Individuels")
    st.dataframe(data["matchups"]["full"])

    st.subheader("⚠️ Mismatchs détectés")
    st.dataframe(data["matchups"]["alerts"])

    # ---------------------------------------------------------------
    # 5) Play Types
    # ---------------------------------------------------------------
    st.header("🎯 Play Types (Synergy‑like)")

    col1, col2 = st.columns(2)
    col1.subheader(home)
    col1.json(data["playtypes"]["home"])

    col2.subheader(away)
    col2.json(data["playtypes"]["away"])

    # ---------------------------------------------------------------
    # 6) Tracking Data
    # ---------------------------------------------------------------
    st.header("📡 Tracking Data (Second Spectrum‑like)")

    col1, col2 = st.columns(2)
    col1.subheader(home)
    col1.json(data["tracking"]["home"])

    col2.subheader(away)
    col2.json(data["tracking"]["away"])

    # ---------------------------------------------------------------
    # 7) Momentum & Runs
    # ---------------------------------------------------------------
    st.header("📈 Momentum & Runs")

    st.subheader("🔥 Runs détectés")
    st.dataframe(data["pbp"]["runs"])

    st.subheader("📈 Momentum Curve")
    st.line_chart(data["pbp"]["momentum"])

    # ---------------------------------------------------------------
    # 8) Player Props
    # ---------------------------------------------------------------
    st.header("💸 Player Props")
    st.dataframe(data["props"])

    # ---------------------------------------------------------------
    # 9) Prédictions
    # ---------------------------------------------------------------
    st.header("🔮 Prédictions Shadow Edge V∞")

    pred = data["predictions"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Home Win %", f"{pred['home_win_prob']}%")
    col2.metric("Away Win %", f"{pred['away_win_prob']}%")
    col3.metric("Marge Projetée", pred["expected_margin"])

    st.subheader("📊 Score Projeté")
    st.write(pred["expected_score"])

    # ---------------------------------------------------------------
    # 10) Analyse Marché
    # ---------------------------------------------------------------
    st.header("💹 Analyse Marché")
    st.json(data["market_analysis"])

    # ---------------------------------------------------------------
    # 11) Synthèse automatique
    # ---------------------------------------------------------------
    st.header("🧠 Synthèse Shadow Edge V∞")

    st.success(f"""
    - **Matchup clé :** {data['matchups']['alerts'][0]['matchup'] if data['matchups']['alerts'] else 'Aucun'}
    - **Équipe dominante (modèle) :** {home if pred['home_win_prob'] > pred['away_win_prob'] else away}
    - **Prop value détectée :** {data['props'][0]['player']} — {data['props'][0]['market'] if data['props'] else 'Aucune'}
    - **Run critique :** {data['pbp']['runs'][0]['description'] if data['pbp']['runs'] else 'Aucun'}
    """)
