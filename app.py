import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="Explainable Cloud Cost Anomaly Detection",
    layout="wide"
)

st.title("☁️ Explainable Cloud Cost Anomaly Detection")
st.caption("Causal root cause analysis for cloud anomalies")

# Sidebar
st.sidebar.header("Input Configuration")

uploaded_file = st.sidebar.file_uploader(
    "Upload Event Log CSV",
    type=["csv"]
)

chain_depth = st.sidebar.slider(
    "Causal Chain Depth",
    min_value=1,
    max_value=5,
    value=3
)

run_clicked = st.sidebar.button("🚀 Run Analysis")

st.divider()

# Guard: no file uploaded
if uploaded_file is None:
    st.info("Please upload an event_log CSV file to begin.")
    st.stop()

# Load CSV safely
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

st.subheader("📋 Event Log Preview")
st.dataframe(df.head(20), width="stretch")

# 🚨 IMPORTANT: analysis ONLY runs after button click
if not run_clicked:
    st.warning("Click **Run Analysis** to perform causal reasoning.")
    st.stop()

# ---------------- ANALYSIS LOGIC ----------------

st.subheader("🧠 Root Cause Analysis")

events = df["event_type"].tolist()

best_chain = []
for event in reversed(events):
    best_chain.append(event)
    if len(best_chain) == chain_depth:
        break

best_chain = list(reversed(best_chain))

explanation = " → ".join(best_chain)

st.success("Causal chain identified")

st.markdown("**Explanation:**")
st.code(explanation)

st.subheader("📊 Confidence Metrics")

confidence_score = round(len(best_chain) / len(events), 2)

st.metric("Causal Coverage Score", confidence_score)

st.subheader("🧾 Explanation Summary")

summary = {
    "chain_depth": chain_depth,
    "identified_chain": best_chain,
    "confidence": confidence_score
}

st.json(summary)
