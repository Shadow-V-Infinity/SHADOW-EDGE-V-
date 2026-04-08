import streamlit as st

st.title("🔥 Betting Radar — Shadow Edge V∞")

st.markdown("### 📊 Analyse du Match")
st.info("Module en cours d'activation. Les analyses seront affichées ici.")

st.markdown("### 🎯 Value Bets")
st.warning("Aucune value détectée pour le moment.")

st.markdown("### 🧠 Predictions")
col1, col2 = st.columns(2)
with col1:
    st.metric("Probabilité Victoire Home", "—")
with col2:
    st.metric("Probabilité Victoire Away", "—")

st.markdown("### ⚡ Matchup Alerts")
st.success("Aucune alerte détectée.")

st.markdown("### 📈 Tendances")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Home")
    st.write("—")
with col2:
    st.subheader("Away")
    st.write("—")

st.markdown("---")
st.caption("Shadow Edge V∞ — Betting Radar en construction 🚧")
