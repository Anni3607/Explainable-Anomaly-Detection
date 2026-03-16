from pyvis.network import Network
import networkx as nx

def visualize_graph(G):

    net = Network(height="500px", width="100%")

    for node in G.nodes():
        net.add_node(node, label=str(node))

    for edge in G.edges():
        net.add_edge(edge[0], edge[1])

    net.save_graph("graph.html")
