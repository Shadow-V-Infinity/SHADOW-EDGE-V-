import streamlit as st
from sports.nba.services.pre_match_service import NBAPreMatchService


def render():
    st.title("🧬 Avant-match NBA")

    game_id = st.text_input("ID du match (ou sélection à venir)")

    if not game_id:
        st.info("Entre un game_id pour voir l’avant-match.")
        return

    service = NBAPreMatchService()
    data = service.get_match_preview(game_id)

    if "error" in data:
        st.error(data["error"])
        return

    st.subheader(f"{data['home_team']} vs {data['away_team']}")
    st.caption(f"Horaire : {data['game_time']}")

    st.markdown("---")
    st.write("### 🔥 Lineups probables")
    st.write("**Domicile :**", data["probable_lineups"]["home"])
    st.write("**Extérieur :**", data["probable_lineups"]["away"])

    st.markdown("---")
    st.write("### 🩹 Blessures")
    st.json(data["injuries"])

    st.markdown("---")
    st.write("### 📊 Stats avancées")
    st.write("**Domicile :**", data["team_stats"]["home"])
    st.write("**Extérieur :**", data["team_stats"]["away"])

    st.markdown("---")
    st.write("### 📈 5 derniers matchs")
    st.write("**Domicile :**")
    st.json(data["last_games"]["home"])
    st.write("**Extérieur :**")
    st.json(data["last_games"]["away"])

    st.markdown("---")
    st.write("### 🔥 Tendances")
    st.write("**Domicile :**", data["trends"]["home"])
    st.write("**Extérieur :**", data["trends"]["away"])

    st.markdown("---")
    st.write("### 🔮 Mini‑prédiction")
    st.success(data["prediction"])
