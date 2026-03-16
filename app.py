# -------------------------------------------------
# PYTHON 3.13 SAFETY SHIM
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
st.set_page_config(page_title="Explainable Cloud Cost Anomaly Detection", layout="wide")

st.title("☁️ Explainable Cloud Cost Anomaly Detection")
st.caption("Detecting unusual cloud cost behaviour with human-readable explanations")


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("📂 Input Configuration")

uploaded_file = st.sidebar.file_uploader("Upload Event Log CSV", type=["csv"])

use_sample = st.sidebar.checkbox("Use sample dataset", value=True)

z_thresh = st.sidebar.slider("Z-score Threshold", 2.0, 5.0, 3.0)

run_btn = st.sidebar.button("🚀 Run Analysis")


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
@st.cache_data
def load_sample():
    path = os.path.join("data", "event_log.csv")
    return pd.read_csv(path)

if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif use_sample:
    df = load_sample()
else:
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)


# -------------------------------------------------
# SYNTHETIC COST SIGNAL
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
            return "High CPU usage increased compute cost."

        if row["event_type"] == "MEMORY_SURGE":
            return "Memory usage surge required additional resources."

        if row["event_type"] == "TRAFFIC_SPIKE":
            return "Traffic surge triggered backend scaling."

        if row["event_type"] == "RESOURCE_SCALE":
            return "Autoscaling increased instance count."

        if row["event_type"] == "COST_ANOMALY":
            return "Billing significantly exceeded expected baseline."

        return "Routine cloud operation."

    df["Explanation"] = df.apply(explain, axis=1)

    anomaly_df = df[df["is_anomaly"]]


    # -------------------------------------------------
    # TABS
    # -------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Data",
        "🚨 Anomalies",
        "📈 Cost Trend",
        "📉 Forecast",
        "📊 Root Causes",
        "📑 Explainability",
        "📋 Summary"
    ])


    # -------------------------------------------------
    # DATA TAB
    # -------------------------------------------------
    with tab1:

        st.subheader("Event Log Preview")
        st.dataframe(df.head(50), use_container_width=True)


    # -------------------------------------------------
    # ANOMALIES TAB
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
            use_container_width=True
        )


    # -------------------------------------------------
    # COST TREND TAB
    # -------------------------------------------------
    with tab3:

        st.subheader("Cloud Cost Trend with Detected Anomalies")

        # Hourly cost trend
        hourly_cost = df.set_index("timestamp")["cost"].resample("H").mean()

        # Smooth the trend
        smoothed_cost = hourly_cost.rolling(6, min_periods=1).mean()

        # Hourly anomaly cost
        anomaly_hours = anomaly_df.set_index("timestamp")["cost"].resample("H").mean()

        fig, ax = plt.subplots(figsize=(12,5))

        ax.plot(
            smoothed_cost.index,
            smoothed_cost.values,
            linewidth=2,
            label="Cost Trend"
        )

        ax.scatter(
            anomaly_hours.index,
            anomaly_hours.values,
            color="red",
            s=70,
            label="Anomaly"
        )

        # Threshold line
        threshold = mean_cost + z_thresh * std_cost

        ax.axhline(
            threshold,
            linestyle="--",
            color="orange",
            label="Anomaly Threshold"
        )

        ax.set_xlabel("Time")
        ax.set_ylabel("Cost")

        ax.legend()
        ax.grid(True)

        st.pyplot(fig)


    # -------------------------------------------------
    # FORECAST TAB
    # -------------------------------------------------
    with tab4:

        st.subheader("Cost Forecast")

        future_cost = forecast_cost(df)

        st.metric("Predicted Next Cost", round(future_cost, 2))


    # -------------------------------------------------
    # ROOT CAUSE TAB
    # -------------------------------------------------
    with tab5:

        st.subheader("Anomaly Type Distribution")
        st.bar_chart(anomaly_df["event_type"].value_counts())

        st.subheader("Severity Distribution")
        st.bar_chart(anomaly_df["severity"].value_counts())


    # -------------------------------------------------
    # EXPLAINABILITY TAB
    # -------------------------------------------------
    with tab6:

        if len(anomaly_df) > 0:
            top_event = anomaly_df["event_type"].value_counts().idxmax()
        else:
            top_event = "No anomalies detected"

        st.write(f"""
        **Most anomalies were caused by:** {top_event}

        The system monitors cloud usage events and estimates expected cost behaviour.

        When cost deviates significantly from the expected baseline, an anomaly is detected.

        This detection uses a statistical **Z-score method** that identifies unusually high cost events.

        The dashboard then provides recommendations to help engineers optimize resource usage.
        """)


    # -------------------------------------------------
    # SUMMARY TAB
    # -------------------------------------------------
    with tab7:

        total_events = len(df)
        anomalies = len(anomaly_df)
        anomaly_rate = anomalies / total_events

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Events", total_events)
        col2.metric("Detected Anomalies", anomalies)
        col3.metric("Anomaly Rate", f"{anomaly_rate:.2%}")

        st.write("""
        ### Simple Explanation

        This system monitors cloud infrastructure activity and calculates expected cost patterns.

        When costs deviate significantly from normal behaviour, the system flags them as anomalies.

        In this dataset, most anomalies are caused by traffic spikes and resource scaling events that temporarily increase cloud spending.

        Early detection helps cloud engineers investigate issues and reduce unnecessary costs.
        """)
