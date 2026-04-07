import streamlit as st
from sports.nba.services.shotchart_service import ShotChartService
from sports.nba.services.tracking_service import TrackingService
from sports.nba.services.pbp_analysis_service import PbpAnalysisService
from sports.nba.services.injury_service import InjuryService
from sports.nba.services.matchup_service import MatchupService
from sports.nba.services.playtype_service import PlayTypeService
from sports.nba.services.props_service import PropsService
from sports.nba.services.prediction_service import PredictionService

# -------------------------------------------------------------------
# INITIALISATION DES SERVICES
# -------------------------------------------------------------------

shotchart = ShotChartService()
tracking = TrackingService()
pbp = PbpAnalysisService()
injuries = InjuryService()
matchups = MatchupService()
playtypes = PlayTypeService()
props = PropsService()
predictions = PredictionService()

# -------------------------------------------------------------------
# PAGE AVANT-MATCH
# -------------------------------------------------------------------

def render(game_id: str, team_home: str, team_away: str):

    st.title("🏀 Avant‑Match — Shadow Edge V∞")

    st.subheader(f"{team_home} vs {team_away}")

    # ---------------------------------------------------------------
    # 1) INJURIES
    # ---------------------------------------------------------------
    st.header("🚑 Injuries & Lineups")

    home_inj = injuries.get_team_injuries(team_home)
    away_inj = injuries.get_team_injuries(team_away)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {team_home}")
        st.dataframe(home_inj)

    with col2:
        st.markdown(f"### {team_away}")
        st.dataframe(away_inj)

    # ---------------------------------------------------------------
    # 2) MATCHUPS
    # ---------------------------------------------------------------
    st.header("🛡️ Matchups Individuels")

    matchup_data = matchups.get_matchups(game_id)
    st.dataframe(matchup_data)

    mismatch_alerts = matchups.get_mismatch_alerts(game_id)
    st.markdown("### ⚠️ Mismatchs détectés")
    st.dataframe(mismatch_alerts)

    # ---------------------------------------------------------------
    # 3) PLAY TYPES
    # ---------------------------------------------------------------
    st.header("🎯 Play Types (Synergy‑like)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {team_home}")
        st.json(playtypes.get_team_playtypes(team_home))

    with col2:
        st.markdown(f"### {team_away}")
        st.json(playtypes.get_team_playtypes(team_away))

    # ---------------------------------------------------------------
    # 4) TRACKING DATA
    # ---------------------------------------------------------------
    st.header("📡 Tracking Data (Second Spectrum‑like)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {team_home}")
        st.json(tracking.get_team_tracking(team_home, "2024-25"))

    with col2:
        st.markdown(f"### {team_away}")
        st.json(tracking.get_team_tracking(team_away, "2024-25"))

    # ---------------------------------------------------------------
    # 5) MOMENTUM / RUNS (PBP)
    # ---------------------------------------------------------------
    st.header("📈 Momentum & Runs")

    runs = pbp.get_runs(game_id)
    st.markdown("### 🔥 Runs détectés")
    st.dataframe(runs)

    momentum = pbp.get_momentum_curve(game_id)
    st.line_chart(momentum)

    # ---------------------------------------------------------------
    # 6) PLAYER PROPS
    # ---------------------------------------------------------------
    st.header("💸 Player Props")

    props_data = props.get_player_props(game_id)
    st.dataframe(props_data)

    # ---------------------------------------------------------------
    # 7) PRÉDICTIONS
    # ---------------------------------------------------------------
    st.header("🔮 Prédictions du match")

    pred = predictions.get_game_prediction(game_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Win Probability (Home)", f"{pred['home_win_prob']}%")

    with col2:
        st.metric("Win Probability (Away)", f"{pred['away_win_prob']}%")

    with col3:
        st.metric("Marge Projetée", pred["expected_margin"])

    st.markdown("### 📊 Score Projeté")
    st.write(pred["expected_score"])

    # ---------------------------------------------------------------
    # 8) SYNTHÈSE AUTOMATIQUE
    # ---------------------------------------------------------------
    st.header("🧠 Synthèse Shadow Edge V∞")

    st.success(f"""
    - **Matchup clé** : {mismatch_alerts[0]['matchup']}  
    - **Play Type dominant** : {team_home if pred['home_win_prob'] > pred['away_win_prob'] else team_away}  
    - **Prop value détectée** : {props_data[0]['player']} — {props_data[0]['market']}  
    - **Run critique** : {runs[0]['description']}  
    """)
