import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
from flask import Flask, request, jsonify
from flask_cors import CORS
import io, base64, math
import serverless_wsgi

from graph_visualizer import (
    Graph, dijkstra, bellman_ford, floyd_warshall, fw_path, a_star
)

# Flask app
app = Flask(__name__)
CORS(app)

# --- Helper functions ---
def render_graph_base64(g: Graph, path=None):
    G = nx.DiGraph()
    G.add_nodes_from(g.nodes())
    for u, v, w in g.edges():
        G.add_edge(u, v, weight=w)

    pos = g.pos if g.pos else nx.spring_layout(G, seed=42)
    edge_labels = {(u, v): f"{w:g}" for u, v, w in g.edges()}

    plt.figure(figsize=(5, 4))
    nx.draw(G, pos, with_labels=True, node_size=800,
            node_color="#2b82ff", font_color="white")
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    if path:
        path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                               width=3, edge_color="black")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def build_graph_from_payload(payload):
    g = Graph()
    for n in payload.get("nodes", []):
        name = str(n.get("name", "")).strip().upper()
        if not name:
            continue
        x, y = n.get("x"), n.get("y")
        if x is not None and y is not None:
            g.set_pos(name, (float(x), float(y)))
        else:
            g.set_pos(name, (len(g.pos), len(g.pos)))
    for e in payload.get("edges", []):
        u = str(e.get("u", "")).strip().upper()
        v = str(e.get("v", "")).strip().upper()
        if not (u and v):
            continue
        w = float(e.get("w", 1))
        g.add_edge(u, v, w)
    return g

# --- API Endpoint ---
@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True) or {}
    mode = data.get("mode", "custom")
    algo = data.get("algo", "1")
    src = (data.get("src") or "").strip().upper()
    dst = (data.get("dst") or "").strip().upper()

    # Default sample graph (A–F, no negatives)
    if mode == "default":
        g = Graph()
        g.set_pos('A',(0,0)); g.set_pos('B',(2,1))
        g.set_pos('C',(4,0)); g.set_pos('D',(1,3))
        g.set_pos('E',(3,3)); g.set_pos('F',(5,2))
        g.add_undirected_edge('A','B',2)
        g.add_undirected_edge('A','D',4)
        g.add_undirected_edge('B','C',2)
        g.add_undirected_edge('B','E',5)
        g.add_undirected_edge('C','F',3)
        g.add_undirected_edge('D','E',1)
        g.add_undirected_edge('E','F',2)
        if not src: src = "A"
        if not dst: dst = "F"

    # Negative-edge demo graph
    elif mode == "negative_demo":
        g = Graph()
        g.set_pos("S",(0,0)); g.set_pos("A",(1,2))
        g.set_pos("B",(2,1)); g.set_pos("C",(3,2))
        g.set_pos("D",(4,1)); g.set_pos("T",(5,0))
        g.add_edge("S","A",1); g.add_edge("S","B",4)
        g.add_edge("A","B",-2); g.add_edge("A","C",2)
        g.add_edge("B","D",2); g.add_edge("C","T",3)
        g.add_edge("D","T",1)
        if not src: src = "S"
        if not dst: dst = "T"

    else:
        g = build_graph_from_payload(data)

    if algo in {"1","2","4"}:
        if src not in g.nodes() or dst not in g.nodes():
            return jsonify({"error": f"Invalid src/dst. Available: {sorted(g.nodes())}"}), 400

    try:
        if algo == "1":
            dist, par = dijkstra(g, src)
            path, cur = [], dst
            while cur:
                path.append(cur); cur = par[cur]
            path.reverse()
            img = render_graph_base64(g, path)
            return jsonify({"algo": "Dijkstra", "path": path, "cost": dist.get(dst, float("inf")), "image": img})

        elif algo == "2":
            dist, par = bellman_ford(g, src)
            if dist is None:
                return jsonify({"algo": "Bellman-Ford", "negative_cycle": True})
            path, cur = [], dst
            while cur:
                path.append(cur); cur = par[cur]
            path.reverse()
            img = render_graph_base64(g, path)
            return jsonify({"algo": "Bellman-Ford", "path": path, "cost": dist.get(dst, float("inf")), "image": img})

        elif algo == "3":
            nodes, dist, nxt = floyd_warshall(g)
            matrix = []
            for i, u in enumerate(nodes):
                row = {v: ("inf" if math.isinf(dist[i][j]) else dist[i][j]) for j, v in enumerate(nodes)}
                matrix.append({"row": u, "dist": row})
            path = None
            if src in g.nodes() and dst in g.nodes():
                path = fw_path(nodes, dist, nxt, src, dst)
            img = render_graph_base64(g, path)
            return jsonify({"algo": "Floyd-Warshall", "nodes": nodes, "matrix": matrix, "path": path, "image": img})

        elif algo == "4":
            path, cost = a_star(g, src, dst)
            img = render_graph_base64(g, path)
            return jsonify({"algo": "A*", "path": path, "cost": cost, "image": img})

        else:
            return jsonify({"error": "Invalid algo"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- For Vercel ---
def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)


# --- For local debug ---
if __name__ == "__main__":
    app.run(debug=True)
