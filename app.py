import streamlit as st
import pandas as pd
from datetime import timedelta# This shim prevents Streamlit from crashing.

import sys
import types

if "imghdr" not in sys.modules:
    imghdr_stub = types.ModuleType("imghdr")

    def what(file, h=None):
        return None

    imghdr_stub.what = what
    sys.modules["imghdr"] = imghdr_stub


# -----------------------------
# IMPORTS
# -----------------------------
import streamlit as st
import pandas as pd
from datetime import timedelta


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Explainable Cloud Cost Anomaly Detection",
    layout="wide"
)

st.title("☁️ Explainable Cloud Cost Anomaly Detection")
st.caption("Causal root-cause analysis for cloud anomalies (graph-free, cloud-safe)")


# -----------------------------
# SIDEBAR INPUT
# -----------------------------
st.sidebar.header("📂 Input Configuration")

uploaded_file = st.sidebar.file_uploader(
    "Upload Event Log CSV",
    type=["csv"]
)

use_sample = st.sidebar.checkbox("Use sample dataset", value=True)

max_depth = st.sidebar.slider(
    "Causal Chain Depth",
    min_value=2,
    max_value=6,
    value=3
)

run_btn = st.sidebar.button("🚀 Run Analysis")


# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_sample():
    return pd.read_csv("event_log.csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif use_sample:
    df = load_sample()
else:
    df = None

if df is None:
    st.info("Upload a CSV or select sample dataset to begin.")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)


# -----------------------------
# DISPLAY EVENT LOG
# -----------------------------
st.subheader("📋 Event Log")
st.dataframe(df.head(50), width="stretch")


# -----------------------------
# BASIC STATS
# -----------------------------
st.subheader("📊 Event Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Events", len(df))

with col2:
    st.metric("Unique Resources", df["resource_id"].nunique())

with col3:
    st.metric(
        "Anomalies Detected",
        int((df["event_type"] == "COST_ANOMALY").sum())
    )


# -----------------------------
# CAUSAL RULES
# -----------------------------
CAUSAL_RULES = {
    ("CPU_SPIKE", "RESOURCE_SCALE"),
    ("MEMORY_SURGE", "RESOURCE_SCALE"),
    ("RESOURCE_SCALE", "COST_ANOMALY"),
    ("CPU_SPIKE", "COST_ANOMALY"),
    ("MEMORY_SURGE", "COST_ANOMALY"),
}


# -----------------------------
# FIND BEST CAUSAL CHAIN
# -----------------------------
def find_best_chain(df, max_depth):
    anomalies = df[df["event_type"] == "COST_ANOMALY"]

    if anomalies.empty:
        return None

    anomaly = anomalies.iloc[-1]
    chain = [anomaly]
    current_time = anomaly["timestamp"]

    for _ in range(max_depth - 1):
        candidates = df[
            (df["timestamp"] < current_time) &
            (df["timestamp"] >= current_time - timedelta(hours=24))
        ]

        found = False
        for _, row in candidates.iloc[::-1].iterrows():
            if (row["event_type"], chain[0]["event_type"]) in CAUSAL_RULES:
                chain.insert(0, row)
                current_time = row["timestamp"]
                found = True
                break

        if not found:
            break

    return chain if len(chain) > 1 else None


# -----------------------------
# RUN ANALYSIS
# -----------------------------
if run_btn:
    st.subheader("🧠 Root Cause Analysis")

    chain = find_best_chain(df, max_depth)

    if chain is None:
        st.error("No causal chain found.")
        st.stop()

    st.success("Causal chain identified")

    # -------------------------
    # EXPLANATION TEXT
    # -------------------------
    explanation_steps = [
        f"{step['event_type']} on {step['resource_id']} by {step['actor']}"
        for step in chain
    ]

    explanation = " → ".join(explanation_steps)

    st.markdown("### 🧾 Explanation")
    st.code(explanation)

    # -------------------------
    # CAUSAL TIMELINE
    # -------------------------
    st.markdown("### ⏱️ Causal Timeline")

    for i, step in enumerate(chain, start=1):
        with st.expander(f"Step {i}: {step['event_type']}"):
            st.write(f"**Timestamp:** {step['timestamp']}")
            st.write(f"**Resource:** {step['resource_id']}")
            st.write(f"**Actor:** {step['actor']}")
            st.write(f"**Metadata:** {step['metadata']}")

    # -------------------------
    # CONFIDENCE SCORE
    # -------------------------
    confidence = round(len(chain) / max_depth, 2)

    st.markdown("### 📌 Explanation Confidence")
    st.progress(confidence)
    st.write(f"Confidence Score: **{confidence}**")

    # -------------------------
    # DOWNLOAD REPORT
    # -------------------------
    report_text = (
        "Explainable Cloud Cost Anomaly Report\n\n"
        f"Causal Chain:\n{explanation}\n\n"
        f"Confidence Score: {confidence}\n"
    )

    st.download_button(
        "⬇️ Download Explanation Report",
        report_text,
        file_name="explanation.txt"
    )
