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
import os

from modules.severity_scoring import severity
from modules.recommendation_engine import recommend
from modules.forecasting import forecast_cost


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

z_thresh = st.sidebar.slider(
    "Z-score Threshold",
    min_value=2.0,
    max_value=5.0,
    value=3.0
)

run_btn = st.sidebar.button("🚀 Run Analysis")


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_sample():
    path = os.path.join("data", "event_log.csv")

    if not os.path.exists(path):
        st.error("Sample dataset not found: data/event_log.csv")
        st.stop()

    return pd.read_csv(path)


if uploaded_file:
    df = pd.read_csv(uploaded_file)

elif use_sample:
    df = load_sample()

else:
    st.info("Upload a CSV or select sample dataset to begin.")
    st.stop()


# -------------------------------------------------
# DATA PREPARATION
# -------------------------------------------------
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)


# -------------------------------------------------
# FEATURE ENGINEERING
# -------------------------------------------------
np.random.seed(42)

df["cost"] = 2.5 + np.random.normal(0, 0.15, len(df))

df.loc[df["event_type"].isin(["CPU_SPIKE", "MEMORY_SURGE"]), "cost"] += 0.8
df.loc[df["event_type"] == "RESOURCE_SCALE", "cost"] += 1.2
df.loc[df["event_type"] == "COST_ANOMALY", "cost"] += 2.0


# -------------------------------------------------
# RUN ANALYSIS
# -------------------------------------------------
if run_btn:

    # Z-SCORE
    mean_cost = df["cost"].mean()
    std_cost = df["cost"].std()

    df["z_score"] = (df["cost"] - mean_cost) / std_cost
    df["is_anomaly"] = df["z_score"].abs() >= z_thresh

    df["severity"] = df["z_score"].apply(severity)

    df["Recommendation"] = df["event_type"].apply(recommend)


    # -------------------------------------------------
    # EXPLANATION ENGINE
    # -------------------------------------------------
    def explain(row):

        if row["event_type"] == "CPU_SPIKE":
            return "CPU utilization exceeded safe threshold, increasing compute cost."

        if row["event_type"] == "MEMORY_SURGE":
            return "Abnormal memory consumption detected on the instance."

        if row["event_type"] == "RESOURCE_SCALE":
            return "Autoscaling triggered additional compute resources."

        if row["event_type"] == "TRAFFIC_SPIKE":
            return "Unexpected traffic surge caused backend scaling."

        if row["event_type"] == "COST_ANOMALY":
            return "Billing deviated significantly from expected baseline."

        return "Routine system activity."


    df["Explanation"] = df.apply(explain, axis=1)

    anomaly_df = df[df["is_anomaly"]]


    # -------------------------------------------------
    # DASHBOARD TABS
    # -------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Data", "🚨 Anomalies", "📈 Trend", "🔮 Forecast", "📊 Summary"]
    )


    # -------------------------------------------------
    # TAB 1 : DATA PREVIEW
    # -------------------------------------------------
    with tab1:

        st.subheader("Event Log Preview")
        st.dataframe(df.head(50), width="stretch")


    # -------------------------------------------------
    # TAB 2 : ANOMALY TABLE
    # -------------------------------------------------
    with tab2:

        st.subheader("Detected Anomalies")

        st.dataframe(
            anomaly_df[
                [
                    "timestamp",
                    "event_type",
                    "resource_id",
                    "cost",
                    "z_score",
                    "severity",
                    "Explanation",
                    "Recommendation"
                ]
            ],
            width="stretch"
        )

        st.subheader("Anomaly Type Distribution")

        type_counts = anomaly_df["event_type"].value_counts()

        st.bar_chart(type_counts)


    # -------------------------------------------------
    # TAB 3 : COST TREND
    # -------------------------------------------------
    with tab3:

        st.subheader("Cloud Cost Trend with Anomalies")

        trend = df.set_index("timestamp")["cost"].resample("H").mean()

        fig, ax = plt.subplots(figsize=(12,5))

        ax.plot(trend.index, trend.values, label="Cost Trend")

        ax.scatter(
            anomaly_df["timestamp"],
            anomaly_df["cost"],
            color="red",
            label="Anomaly",
            s=40
        )

        ax.set_xlabel("Time")
        ax.set_ylabel("Cost")

        ax.legend()
        ax.grid(True)

        st.pyplot(fig)


    # -------------------------------------------------
    # TAB 4 : FORECAST
    # -------------------------------------------------
    with tab4:

        st.subheader("Cost Forecast")

        future_cost = forecast_cost(df)

        st.metric(
            "Predicted Next Cost",
            round(future_cost, 2)
        )


    # -------------------------------------------------
    # TAB 5 : SUMMARY
    # -------------------------------------------------
    with tab5:

        st.subheader("Summary Metrics")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Total Events", len(df))

        with c2:
            st.metric("Detected Anomalies", len(anomaly_df))

        with c3:
            st.metric(
                "Anomaly Rate",
                f"{len(anomaly_df)/len(df):.2%}"
            )
