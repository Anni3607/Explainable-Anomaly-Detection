import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import timedelta

st.set_page_config(
    page_title="Explainable Cloud Cost Anomaly Detection",
    layout="wide"
)

st.title("☁️ Explainable Cloud Cost Anomaly Detection")
st.caption("Causal root-cause analysis for cloud anomalies")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("📂 Input Configuration")

uploaded_file = st.sidebar.file_uploader(
    "Upload Event Log CSV",
    type=["csv"]
)

max_depth = st.sidebar.slider(
    "Causal Chain Depth",
    min_value=2,
    max_value=6,
    value=3
)

run_btn = st.sidebar.button("🚀 Run Analysis")

# =========================
# LOAD DATA
# =========================
if uploaded_file:
    event_log = pd.read_csv(uploaded_file)
else:
    st.info("Upload a CSV file to begin analysis.")
    st.stop()

required_cols = {
    "timestamp", "event_type", "resource_id",
    "project_id", "actor", "metadata"
}

if not required_cols.issubset(event_log.columns):
    st.error("CSV format invalid. Required columns missing.")
    st.stop()

event_log["timestamp"] = pd.to_datetime(event_log["timestamp"])

st.subheader("📄 Event Log")
st.dataframe(event_log.head(20), use_container_width=True)

# =========================
# CAUSAL RULES
# =========================
CAUSAL_RULES = {
    ("CPU_SPIKE", "RESOURCE_SCALE"),
    ("MEMORY_SURGE", "RESOURCE_SCALE"),
    ("RESOURCE_SCALE", "COST_ANOMALY"),
    ("TRAFFIC_SPIKE", "COST_ANOMALY"),
    ("CPU_SPIKE", "COST_ANOMALY"),
}

# =========================
# ANALYSIS
# =========================
if run_btn:

    st.markdown("---")
    st.subheader("🧠 Root Cause Analysis")

    # Build graph
    G = nx.DiGraph()

    for idx, row in event_log.iterrows():
        G.add_node(idx, **row.to_dict())

    sorted_idx = event_log.sort_values("timestamp").index.tolist()

    for i in range(len(sorted_idx)):
        for j in range(i + 1, len(sorted_idx)):
            e1 = event_log.loc[sorted_idx[i]]
            e2 = event_log.loc[sorted_idx[j]]

            if (e2["timestamp"] - e1["timestamp"]) > timedelta(hours=24):
                break

            if (e1["event_type"], e2["event_type"]) in CAUSAL_RULES:
                G.add_edge(sorted_idx[i], sorted_idx[j])

    # =========================
    # FIND BEST CHAIN
    # =========================
    def score_chain(chain):
        return len(chain)

    def find_best_chain(G, max_depth):
        best_chain = None
        best_score = -1

        for node, data in G.nodes(data=True):
            if data.get("event_type") != "COST_ANOMALY":
                continue

            stack = [(node, [node])]

            while stack:
                current, path = stack.pop()

                if len(path) > max_depth:
                    continue

                if len(path) >= 2:
                    score = score_chain(path)
                    if score > best_score:
                        best_score = score
                        best_chain = path

                for p in G.predecessors(current):
                    if p not in path:
                        stack.append((p, [p] + path))

        return best_chain

    best_chain = find_best_chain(G, max_depth)

    # =========================
    # EXPLANATION
    # =========================
    def explain_chain(chain):
        parts = []
        for node in chain:
            e = G.nodes[node]
            parts.append(
                f"{e['event_type']} on {e['resource_id']} by {e['actor']}"
            )
        return " → ".join(parts)

    if best_chain:
        explanation = explain_chain(best_chain)
        st.success("✅ Causal chain identified")
        st.markdown(f"**Explanation:**  \n{explanation}")
    else:
        st.warning("No causal chain found.")
        st.stop()

    # =========================
    # GRAPH VISUALIZATION
    # =========================
    st.markdown("---")
    st.subheader("📈 Causal Graph (Best Chain)")

    chain_graph = nx.DiGraph()
    for i in range(len(best_chain) - 1):
        chain_graph.add_edge(best_chain[i], best_chain[i + 1])

    plt.figure(figsize=(8, 4))
    pos = nx.spring_layout(chain_graph, seed=42)
    nx.draw(
        chain_graph,
        pos,
        with_labels=True,
        node_color="#4CAF50",
        node_size=2000,
        font_size=9
    )
    st.pyplot(plt)

    # =========================
    # METRIC
    # =========================
    coverage = len(best_chain) / len(G.nodes)
    st.metric("Causal Coverage Score", f"{coverage:.2f}")
