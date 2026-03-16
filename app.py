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
st.caption("Detect unusual cloud cost behaviour with simple explanations")


# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Input Configuration")

uploaded_file = st.sidebar.file_uploader("Upload Event Log CSV", type=["csv"])
use_sample = st.sidebar.checkbox("Use sample dataset", value=True)
z_thresh = st.sidebar.slider("Z-score Threshold", 2.0, 5.0, 3.0)
run_btn = st.sidebar.button("Run Analysis")


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
    def explain(event):

        explanations = {
            "CPU_SPIKE": "High CPU usage increased compute cost.",
            "MEMORY_SURGE": "Memory demand increased instance usage.",
            "TRAFFIC_SPIKE": "Traffic spike triggered backend scaling.",
            "RESOURCE_SCALE": "Autoscaling increased infrastructure cost.",
            "COST_ANOMALY": "Billing deviated significantly from baseline."
        }

        return explanations.get(event, "Routine cloud operation.")

    df["Explanation"] = df["event_type"].apply(explain)


    # CREATE anomaly_df AFTER Explanation column exists
    anomaly_df = df[df["is_anomaly"]]


    # -------------------------------------------------
    # TABS
    # -------------------------------------------------
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Data",
        "Anomalies",
        "Cost Trend",
        "Forecast",
        "Root Causes",
        "Explainability",
        "Summary"
    ])


    # -------------------------------------------------
    # DATA TAB
    # -------------------------------------------------
    with tab1:

        st.subheader("Event Log Preview")

        st.dataframe(df.head(50), width="stretch")


    # -------------------------------------------------
    # ANOMALIES TAB
    # -------------------------------------------------
    with tab2:

        st.subheader("Detected Anomalies")

        if len(anomaly_df) == 0:

            st.success("No anomalies detected")

        else:

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


    # -------------------------------------------------
    # COST TREND TAB
    # -------------------------------------------------
    with tab3:

        st.subheader("Daily Cloud Cost Trend")

        daily_cost = df.set_index("timestamp")["cost"].resample("D").mean()

        fig, ax = plt.subplots(figsize=(12,5))

        ax.plot(
            daily_cost.index,
            daily_cost.values,
            linewidth=2,
            label="Average Cost"
        )

        if len(anomaly_df) > 0:

            ax.scatter(
                anomaly_df["timestamp"],
                anomaly_df["cost"],
                color="red",
                s=40,
                label="Anomaly"
            )

        threshold = mean_cost + z_thresh * std_cost

        ax.axhline(
            threshold,
            linestyle="--",
            color="orange",
            label="Anomaly Threshold"
        )

        ax.set_xlabel("Date")
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

        st.subheader("Top Anomaly Sources")

        if len(anomaly_df) > 0:

            st.bar_chart(anomaly_df["event_type"].value_counts())

        else:

            st.info("No anomaly causes detected")


    # -------------------------------------------------
    # EXPLAINABILITY TAB
    # -------------------------------------------------
    with tab6:

        st.subheader("Model Explanation")

        if len(anomaly_df) > 0:

            top_event = anomaly_df["event_type"].value_counts().idxmax()

            avg_cost = anomaly_df["cost"].mean()

            st.write(f"Most anomalies were caused by **{top_event}** events.")
            st.write(f"Average anomalous cost: **{avg_cost:.2f}**")

            st.write("Detection uses statistical Z-score deviation from normal cost behaviour.")

        else:

            st.write("No abnormal behaviour detected.")


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

        st.markdown("### Key Insights")

        if anomalies > 0:

            most_common = anomaly_df["event_type"].value_counts().idxmax()

            st.write(f"- Most anomalies caused by **{most_common}**")
            st.write("- Cost spikes linked to scaling or workload surges")
            st.write("- Monitoring these events helps reduce unexpected cloud spend")

        else:

            st.write("- System behaviour is within normal cost range")
