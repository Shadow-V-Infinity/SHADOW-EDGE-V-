import streamlit as st
from streamlit_echarts import st_echarts
from sports.nba.services.player_profile_service import PlayerProfileService
from sports.nba.services.player_profile_service import (
    build_shotchart_heatmap,
    build_playtype_radar,
)

service = PlayerProfileService()

def render():
    st.title("👤 Player Profile — Shadow Edge V∞")

    player_id = st.text_input("ID du joueur (NBA API)", "")

    if not player_id:
        st.info("Entre un player_id NBA API.")
        return

    data = service.get_player_profile(player_id)

    # ---------------------------------------------------------------
    # 1) Infos générales
    # ---------------------------------------------------------------
    st.header("📇 Informations Joueur")
    st.json(data["info"])

    # ---------------------------------------------------------------
    # 2) Blessure
    # ---------------------------------------------------------------
    st.header("🚑 Statut Blessure")
    st.json(data["injury"])

    # ---------------------------------------------------------------
    # 3) Derniers matchs
    # ---------------------------------------------------------------
    st.header("📊 Derniers Matchs")
    st.dataframe(data["last_games"])

    # ---------------------------------------------------------------
    # 4) Shot Chart PRO
    # ---------------------------------------------------------------
    st.header("🎯 Shot Chart — Heatmap PRO")

    heatmap = build_shotchart_heatmap(data["shotchart"])
    st_echarts(heatmap, height="500px")

    # ---------------------------------------------------------------
    # 5) Play Types — Radar Chart PRO
    # ---------------------------------------------------------------
    st.header("🎬 Play Types — Radar Chart PRO")

    radar = build_playtype_radar(data["playtypes"])
    st_echarts(radar, height="500px")

    # ---------------------------------------------------------------
    # 6) Tracking Data
    # ---------------------------------------------------------------
    st.header("📡 Tracking Data")
    st.json(data["tracking"])

    # ---------------------------------------------------------------
    # 7) Props
    # ---------------------------------------------------------------
    st.header("💸 Player Props")
    st.dataframe(data["props"])

    # ---------------------------------------------------------------
    # 8) Film Room
    # ---------------------------------------------------------------
    st.header("🎥 Film Room — Clips Vidéo")

    clips = service.get_player_clips(player_id)
    if clips:
        for c in clips:
            st.video(c["url"])
    else:
        st.info("Aucun clip disponible.")

    # ---------------------------------------------------------------
    # 9) Synthèse automatique
    # ---------------------------------------------------------------
    st.header("🧠 Synthèse Shadow Edge V∞")

    st.success(f"""
    - **Tendance scoring :** {data['last_games'][0]['PTS']} pts au dernier match  
    - **Play type dominant :** {max(data['playtypes'], key=data['playtypes'].get) if data['playtypes'] else 'N/A'}  
    - **Prop value :** {data['props'][0]['market'] if data['props'] else 'Aucune'}  
    """)
