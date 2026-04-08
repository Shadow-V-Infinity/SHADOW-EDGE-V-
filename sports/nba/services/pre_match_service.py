# sports/nba/pages/pre_match_service.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from sports.nba.services.pre_match_service import ShadowEdgePreMatchService

pre = ShadowEdgePreMatchService()


def render_playtypes_radar(playtypes_home, playtypes_away, home_name, away_name):
    labels = ["Pick & Roll", "Isolation", "Handoff", "Spot-Up", "Post-Up", "Transition"]
    keys = ["pick_and_roll", "isolation", "handoff", "spot_up", "post_up", "transition"]

    def extract_freq(pt_dict):
        return [
            (pt_dict.get(k, {}) or {}).get("frequency") or 0
            for k in keys
        ]

    home_vals = extract_freq(playtypes_home)
    away_vals = extract_freq(playtypes_away)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=home_vals + home_vals[:1],
        theta=labels + labels[:1],
        fill='toself',
        name=home_name
    ))

    fig.add_trace(go.Scatterpolar(
        r=away_vals + away_vals[:1],
        theta=labels + labels[:1],
        fill='toself',
        name=away_name
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Profil Playtypes — Home vs Away"
    )

    return fig


def render_playtypes_heatmap(play_home, play_away, home_name, away_name):
    keys = ["pick_and_roll", "isolation", "handoff", "spot_up", "post_up", "transition"]
    labels = ["PnR", "ISO", "HO", "Spot", "Post", "Trans"]

    def to_row(team_name, pt_dict):
        return {
            "team": team_name,
            **{
                label: (pt_dict.get(k, {}) or {}).get("frequency") or 0
                for k, label in zip(keys, labels)
            }
        }

    df = pd.DataFrame([
        to_row(home_name, play_home),
        to_row(away_name, play_away),
    ])

    df_melt = df.melt(id_vars="team", var_name="playtype", value_name="frequency")

    fig = px.density_heatmap(
        df_melt,
        x="playtype",
        y="team",
        z="frequency",
        color_continuous_scale="Blues",
        title="Heatmap Playtypes — Intensité par équipe"
    )
    return fig


def render():
    st.title("🏀 Avant‑Match — Shadow Edge V∞")

    games = pre.get_today_games()
    if not games:
        st.warning("Aucun match trouvé pour aujourd’hui.")
        return

    game_labels = [f"{g['away']} @ {g['home']}" for g in games]
    selected = st.selectbox("Sélectionne un match", game_labels)

    idx = game_labels.index(selected)
    game = games[idx]

    game_id = game["game_id"]
    home = game["home"]
    away = game["away"]

    data = pre.get_pre_match_package(game_id, home, away)

    if "error" in data:
        st.error(data["error"])
        return

    st.subheader(f"{away} @ {home}")

    # ---------------- Injuries ----------------
    st.markdown("### Blessures")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{home} — Shadow Edge**")
        st.json(data["injuries"]["shadow_edge"]["home"])
        st.markdown("**NBA API**")
        st.json(data["injuries"]["nba_api"])
    with col2:
        st.markdown(f"**{away} — Shadow Edge**")
        st.json(data["injuries"]["shadow_edge"]["away"])

    # ---------------- Matchups ----------------
    st.markdown("### Matchups & Alerts")
    st.json(data["matchups"]["full"])
    if data["matchups"]["alerts"]:
        st.warning("Alerts mismatch :")
        st.json(data["matchups"]["alerts"])

    # ---------------- Team stats & trends ----------------
    st.markdown("### Stats d'équipe & Tendances")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{home} — Stats**")
        st.json(data["team_stats"]["home"])
        st.markdown("**Derniers matchs**")
        st.json(data["last_games"]["home"])
        st.markdown("**Tendances**")
        st.json(data["trends"]["home"])
    with col2:
        st.markdown(f"**{away} — Stats**")
        st.json(data["team_stats"]["away"])
        st.markdown("**Derniers matchs**")
        st.json(data["last_games"]["away"])
        st.markdown("**Tendances**")
        st.json(data["trends"]["away"])

    # ---------------- Playtypes + Style Index ----------------
    play_home = data["playtypes"]["home"]
    play_away = data["playtypes"]["away"]
    style_home = data.get("style_index", {}).get("home", {})
    style_away = data.get("style_index", {}).get("away", {})

    st.markdown("### Playtypes — Style de jeu comparé")
    fig_radar = render_playtypes_radar(play_home, play_away, home, away)
    st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("### Heatmap Playtypes")
    fig_heat = render_playtypes_heatmap(play_home, play_away, home, away)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("### Indice de style de jeu")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{home}**")
        st.json(style_home)
    with col2:
        st.markdown(f"**{away}**")
        st.json(style_away)

    # ---------------- PBP / Props / Predictions / Market ----------------
    st.markdown("### PBP — Runs & Momentum")
    st.json(data["pbp"])

    st.markdown("### Props")
    st.json(data["props"])

    st.markdown("### Prédictions Shadow Edge V∞")
    st.json(data["predictions"])

    st.markdown("### Analyse Marché")
    st.json(data["market_analysis"])
