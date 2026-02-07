# -------------------------------------------------
# PYTHON 3.13 SAFETY SHIM (DO NOT REMOVE)
# -------------------------------------------------
import sys
import types

if "imghdr" not in sys.modules:
    imghdr_stub = types.ModuleType("imghdr")
    def what(file, h=None):
        return None
    imghdr_stub.what = what
    sys.modules["imghdr"] = imghdr_stub


# -------------------------------------------------
# IMPORTS
# -------------------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Explainable Cloud Cost Anomaly Detection",
    layout="wide"
)

st.title("☁️ Explainable Cloud Cost Anomaly Detection")
st.caption("Statistical anomaly detection with human-readable explanations")


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("📂 Input Configuration")

uploaded_file = st.sidebar.file_uploader(
    "Upload Event Log CSV",
    type=["csv"]
)

use_sample = st.sidebar.checkbox("Use sample dataset", value=True)
z_thresh = st.sidebar.slider("Z-score Threshold", 2.0, 5.0, 3.0)
run_btn = st.sidebar.button("🚀 Run Analysis")


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_sample():
    return pd.read_csv("event_log.csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif use_sample:
    df = load_sample()
else:
    st.info("Upload a CSV or select sample dataset to begin.")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)


# -------------------------------------------------
# DISPLAY RAW DATA
# -------------------------------------------------
st.subheader("📋 Event Log Preview")
st.dataframe(df.head(50), width="stretch")


# -------------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------------
# Create synthetic cost column (simple + explainable)
np.random.seed(42)
df["cost"] = (
    2.5
    + np.random.normal(0, 0.15, len(df))
)

# Inject higher cost for anomaly-related events
df.loc[df["event_type"].isin(["CPU_SPIKE", "MEMORY_SURGE"]), "cost"] += 0.8
df.loc[df["event_type"] == "RESOURCE_SCALE", "cost"] += 1.2
df.loc[df["event_type"] == "COST_ANOMALY", "cost"] += 2.0


# -------------------------------------------------
# RUN ANALYSIS
# -------------------------------------------------
if run_btn:

    st.subheader("🔍 Detected Anomalies")

    # Z-score
    mean_cost = df["cost"].mean()
    std_cost = df["cost"].std()

    df["z_score"] = (df["cost"] - mean_cost) / std_cost
    df["is_anomaly"] = df["z_score"].abs() >= z_thresh

    # Explanation column
    def explain(row):
        if row["event_type"] == "CPU_SPIKE":
            return "High EC2 cost due to unusual CPU utilization spike"
        if row["event_type"] == "MEMORY_SURGE":
            return "High EC2 cost due to abnormal memory consumption"
        if row["event_type"] == "RESOURCE_SCALE":
            return "Cost increase caused by automatic resource scaling"
        if row["event_type"] == "COST_ANOMALY":
            return "Detected billing anomaly exceeding expected baseline"
        return "Normal operational behavior"

    df["Explanation"] = df.apply(explain, axis=1)

    anomaly_df = df[df["is_anomaly"]]

    st.dataframe(
        anomaly_df[
            ["timestamp", "event_type", "resource_id", "cost", "z_score", "Explanation"]
        ],
        width="stretch"
    )


    # -------------------------------------------------
    # COST TREND GRAPH (MATPLOTLIB – SAFE)
    # -------------------------------------------------
    st.subheader("📈 Cost Trend with Anomalies")

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(df["timestamp"], df["cost"], label="Cost", linewidth=1)
    ax.scatter(
        anomaly_df["timestamp"],
        anomaly_df["cost"],
        color="red",
        label="Anomaly",
        s=40
    )

    ax.set_xlabel("Time")
    ax.set_ylabel("Cost")
    ax.set_title("Cloud Cost Trend with Detected Anomalies")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)


    # -------------------------------------------------
    # SUMMARY METRICS
    # -------------------------------------------------
    st.subheader("📊 Summary")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Total Events", len(df))

    with c2:
        st.metric("Detected Anomalies", len(anomaly_df))

    with c3:
        st.metric("Anomaly Rate", f"{len(anomaly_df)/len(df):.2%}")
