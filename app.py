
import streamlit as st
import pandas as pd

st.title("Explainable Cloud Cost Anomaly Detection")

event_log = pd.read_csv("event_log.csv")
st.subheader("Event Log")
st.dataframe(event_log)

with open("explanation.txt") as f:
    explanation = f.read()

st.subheader("Root Cause Explanation")
st.write(explanation)
