import streamlit as st
from sports.nba.services.player_profile_service import PlayerProfileService

service = PlayerProfileService()

def render():
    st.title("👤 Player Profile — Shadow Edge V∞")

    # ---------------------------------------------------------------
    # 1) Sélection joueur
    # ---------------------------------------------------------------
    player_id = st.text_input("ID du joueur (NBA API)", "")

    if not player_id:
        st.info("Entre un player_id NBA API.")
        return

    data = service.get_player_profile(player_id)

    # ---------------------------------------------------------------
    # 2) Infos générales
    # ---------------------------------------------------------------
    st.header("📇 Informations Joueur")
    st.json(data["info"])

    # ---------------------------------------------------------------
    # 3) Blessure
    # ---------------------------------------------------------------
    st.header("🚑 Statut Blessure")
    st.json(data["injury"])

    # ---------------------------------------------------------------
    # 4) Derniers matchs
    # ---------------------------------------------------------------
    st.header("📊 Derniers Matchs")
    st.dataframe(data["last_games"])

    # ---------------------------------------------------------------
    # 5) Shot Chart
    # ---------------------------------------------------------------
    st.header("🎯 Shot Chart")
    st.json(data["shotchart"])  # tu peux remplacer par une vraie heatmap plus tard

    # ---------------------------------------------------------------
    # 6) Play Types
    # ---------------------------------------------------------------
    st.header("🎬 Play Types (Synergy‑like)")
    st.json(data["playtypes"])

    # ---------------------------------------------------------------
    # 7) Tracking Data
    # ---------------------------------------------------------------
    st.header("📡 Tracking Data")
    st.json(data["tracking"])

    # ---------------------------------------------------------------
    # 8) Props
    # ---------------------------------------------------------------
    st.header("💸 Player Props")
    st.dataframe(data["props"])

    # ---------------------------------------------------------------
    # 9) Synthèse automatique
    # ---------------------------------------------------------------
    st.header("🧠 Synthèse Shadow Edge V∞")

    st.success(f"""
    - **Tendance scoring :** {data['last_games'][0]['PTS']} pts au dernier match  
    - **Play type dominant :** {max(data['playtypes'], key=data['playtypes'].get) if data['playtypes'] else 'N/A'}  
    - **Zone forte :** à calculer avec shotchart  
    - **Prop value :** {data['props'][0]['market'] if data['props'] else 'Aucune'}  
    """)
