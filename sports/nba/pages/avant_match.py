import streamlit as st
from sports.nba.services.pre_match_service import NBAPreMatchService


def render():
    st.title("🧬 Avant-match NBA")

    service = NBAPreMatchService()

    # 🔥 Récupération automatique des matchs du jour
    today_games = service.get_today_games()

    if not today_games:
        st.info("Aucun match NBA prévu aujourd’hui.")
        return

    # Format lisible : "Lakers vs Warriors"
    game_labels = [
        f"{g['home']} vs {g['away']} ({g['game_id']})"
        for g in today_games
    ]

    # Sélecteur
    selected = st.selectbox("Sélectionne un match :", game_labels)

    # Extraction du game_id
    game_id = selected.split("(")[-1].replace(")", "")

    # Récupération des données
    data = service.get_match_preview(game_id)

    if "error" in data:
        st.error(data["error"])
        return

    # --- AFFICHAGE ---
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
