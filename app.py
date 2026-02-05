import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import timedelta

# ---------------- UI CONFIG ----------------
st.set_page_config(
    page_title="Explainable Cloud Cost Anomaly Detection",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("☁️ Explainable Cloud Cost Anomaly Detection")
st.caption("Causal root-cause analysis for cloud anomalies")

# ---------------- SIDEBAR ----------------
st.sidebar.header("📂 Input Configuration")

uploaded_file = st.sidebar.file_uploader(
    "Upload Event Log CSV",
    type=["csv"]
)

use_sample = st.sidebar.checkbox("Use sample dataset", value=True)

max_depth = st.sidebar.slider("Causal Chain Depth", 2, 8, 6)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_sample():
    return pd.read_csv("event_log.csv")

if uploaded_file:
    event_log = pd.read_csv(uploaded_file)
    st.sidebar.success("Custom dataset loaded")
elif use_sample:
    event_log = load_sample()
    st.sidebar.info("Using sample dataset")
else:
    st.warning("Upload a dataset or enable sample data")
    st.stop()

event_log["timestamp"] = pd.to_datetime(event_log["timestamp"])

# ---------------- DISPLAY EVENT LOG ----------------
st.subheader("📋 Event Log")
st.dataframe(event_log, use_container_width=True)

# ---------------- CAUSAL RULES ----------------
CAUSAL_RULES = {
    ("CONFIG_CHANGE", "RESOURCE_SCALE"),
    ("CPU_SPIKE", "RESOURCE_SCALE"),
    ("RESOURCE_SCALE", "TRAFFIC_SPIKE"),
    ("TRAFFIC_SPIKE", "COST_ANOMALY"),
}

# ---------------- BUILD GRAPH ----------------
G = nx.DiGraph()

for idx, row in event_log.iterrows():
    G.add_node(idx, **row.to_dict())

event_log_sorted = event_log.sort_values("timestamp")
indices = event_log_sorted.index.tolist()

for i in range(len(indices)):
    e1 = event_log.loc[indices[i]]
    for j in range(i + 1, len(indices)):
        e2 = event_log.loc[indices[j]]
        if (e2["timestamp"] - e1["timestamp"]) > timedelta(hours=24):
            break
        if (e1["event_type"], e2["event_type"]) in CAUSAL_RULES:
            G.add_edge(indices[i], indices[j])

# ---------------- FIND BEST CHAIN ----------------
def score_chain(chain):
    return len(chain)

def find_best_chain(G):
    best_chain = None
    best_score = -1

    for node, data in G.nodes(data=True):
        if data["event_type"] != "COST_ANOMALY":
            continue

        stack = [(node, [node])]
        while stack:
            current, path = stack.pop()
            if len(path) >= max_depth:
                continue

            if len(path) >= 2:
                score = score_chain(path)
                if score > best_score:
                    best_chain = path
                    best_score = score

            for p in G.predecessors(current):
                if p not in path:
                    stack.append((p, [p] + path))

    return best_chain

best_chain = find_best_chain(G)

# ---------------- EXPLANATION ----------------
def explain_chain(chain):
    if not chain:
        return "No causal chain found."
    parts = []
    for n in chain:
        e = G.nodes[n]
        parts.append(f"{e['event_type']} on {e['resource_id']} by {e['actor']}")
    return " → ".join(parts)

st.subheader("🧠 Root Cause Explanation")
st.success(explain_chain(best_chain))

# ---------------- GRAPH VISUALIZATION ----------------
st.subheader("📊 Causal Graph Visualization")

if best_chain:
    chain_graph = nx.DiGraph()
    for i in range(len(best_chain) - 1):
        chain_graph.add_edge(best_chain[i], best_chain[i + 1])

    pos = nx.spring_layout(chain_graph, seed=42)

    fig, ax = plt.subplots(figsize=(8, 4))
    nx.draw(
        chain_graph,
        pos,
        with_labels=True,
        node_size=2500,
        node_color="#87CEEB",
        font_size=9,
        ax=ax
    )
    st.pyplot(fig)
else:
    st.info("No graph to display")
