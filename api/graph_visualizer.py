from collections import defaultdict, deque
import heapq
import math

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    HAS_DRAW = True
except Exception:
    HAS_DRAW = False

class Graph:
    def __init__(self):
        self.adj = defaultdict(list)
        self.nodes_set = set()
        self.pos = {}

    def add_edge(self, u, v, w=1.0):
        self.nodes_set.add(u); self.nodes_set.add(v)
        self.adj[u].append((v, float(w)))

    def add_undirected_edge(self, u, v, w=1.0):
        self.add_edge(u, v, w); self.add_edge(v, u, w)

    def set_pos(self, node, xy):
        self.pos[node] = xy
        self.nodes_set.add(node)

    def nodes(self):
        return list(self.nodes_set)

    def edges(self):
        for u in self.adj:
            for v, w in self.adj[u]:
                yield (u, v, w)

def dijkstra(g: Graph, source):
    dist = {u: math.inf for u in g.nodes()}
    parent = {u: None for u in g.nodes()}
    dist[source] = 0.0
    pq = [(0.0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist[u]:
            continue
        for v, w in g.adj[u]:
            if w < 0:
                raise ValueError("Dijkstra requires non-negative weights.")
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))
    return dist, parent

def bellman_ford(g: Graph, source):
    nodes = g.nodes()
    dist = {u: math.inf for u in nodes}
    parent = {u: None for u in nodes}
    dist[source] = 0.0

    for _ in range(len(nodes) - 1):
        updated = False
        for u, v, w in g.edges():
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                parent[v] = u
                updated = True
        if not updated:
            break

    for u, v, w in g.edges():
        if dist[u] + w < dist[v]:
            return None, None
    return dist, parent

def floyd_warshall(g: Graph):
    nodes = g.nodes()
    idx = {u: i for i, u in enumerate(nodes)}
    n = len(nodes)
    dist = [[math.inf] * n for _ in range(n)]
    nxt = [[None] * n for _ in range(n)]

    for u in nodes:
        i = idx[u]
        dist[i][i] = 0.0

    for u, v, w in g.edges():
        i, j = idx[u], idx[v]
        if w < dist[i][j]:
            dist[i][j] = w
            nxt[i][j] = v

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    nxt[i][j] = nxt[i][k]

    return nodes, dist, nxt

def fw_path(nodes, dist, nxt, u, v):
    idx = {u_: i for i, u_ in enumerate(nodes)}
    i, j = idx[u], idx[v]
    if math.isinf(dist[i][j]):
        return None
    path = [u]
    while u != v:
        u = nxt[idx[u]][j]
        path.append(u)
    return path

def heuristic(g: Graph, a, b):
    if a in g.pos and b in g.pos:
        (x1, y1), (x2, y2) = g.pos[a], g.pos[b]
        return math.hypot(x1 - x2, y1 - y2)
    return 0.0

def a_star(g: Graph, start, goal):
    open_pq = [(0.0, start)]
    g_score = {u: math.inf for u in g.nodes()}
    f_score = {u: math.inf for u in g.nodes()}
    parent = {u: None for u in g.nodes()}
    g_score[start] = 0.0
    f_score[start] = heuristic(g, start, goal)

    while open_pq:
        _, current = heapq.heappop(open_pq)
        if current == goal:
            path = deque([goal])
            while parent[path[0]] is not None:
                path.appendleft(parent[path[0]])
            return list(path), g_score[goal]

        for v, w in g.adj[current]:
            tentative = g_score[current] + w
            if tentative < g_score[v]:
                parent[v] = current
                g_score[v] = tentative
                f_score[v] = tentative + heuristic(g, v, goal)
                heapq.heappush(open_pq, (f_score[v], v))

    return None, math.inf

def draw_graph(g: Graph, path_edges=None, title="Graph"):
    if not HAS_DRAW:
        print("(Visualization skipped – install networkx & matplotlib)")
        return
    G = nx.DiGraph()
    G.add_nodes_from(g.nodes())
    for u, v, w in g.edges():
        G.add_edge(u, v, weight=w)

    pos = g.pos if g.pos else nx.spring_layout(G, seed=42)
    edge_labels = {(u, v): f"{w:g}" for u, v, w in g.edges()}

    plt.figure()
    nx.draw(G, pos, with_labels=True, node_size=800)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    if path_edges:
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, width=4)
    plt.title(title)
    plt.show()

def edges_from_path(path):
    return list(zip(path[:-1], path[1:])) if path and len(path) > 1 else []

def user_defined_graph():
    g = Graph()
    n = int(input("Enter number of nodes: "))
    print("Enter node names (e.g., A B C):")
    nodes = input().split()
    for u in nodes:
        g.set_pos(u.upper(), (len(g.pos), len(g.pos)))
    m = int(input("Enter number of edges: "))
    print("Enter edges in format: u v w (from u to v with weight w):")
    for _ in range(m):
        u, v, w = input().split()
        g.add_edge(u.upper(), v.upper(), float(w))
    return g

def get_valid_node(prompt, g):
    while True:
        node = input(prompt).strip()
        if node == "0":
            return None
        node = node.upper()
        if node in g.nodes():
            return node
        print(f"Invalid node '{node}'. Available nodes: {g.nodes()}")

def menu():
    print("\n=== Graph Algorithm Visualizer (DAA) ===")
    print("1) Dijkstra (non-negative)")
    print("2) Bellman-Ford (negative edges ok)")
    print("3) Floyd-Warshall (all-pairs)")
    print("4) A* (heuristic)")
    print("5) Demo: Negative-edge graph")
    print("6) Enter your own graph")
    print("0) Exit")
    return input("Choose: ").strip()

def main():
    while True:
        choice = menu()
        if choice == "0":
            print("Exiting... Goodbye!")
            break

        if choice == "5":
            g = Graph()
            g.set_pos("S",(0,0)); g.set_pos("A",(1,2))
            g.set_pos("B",(2,1)); g.set_pos("C",(3,2))
            g.set_pos("D",(4,1)); g.set_pos("T",(5,0))
            g.add_edge("S","A",1); g.add_edge("S","B",4)
            g.add_edge("A","B",-2); g.add_edge("A","C",2)
            g.add_edge("B","D",2); g.add_edge("C","T",3)
            g.add_edge("D","T",1)
            src, dst = "S","T"
            print("\nBellman-Ford on graph with a negative edge:")
            dist, par = bellman_ford(g, src)
            if dist is None:
                print("Negative cycle detected!")
                draw_graph(g, title="Negative-Cycle Graph")
            else:
                path=[]; cur=dst
                while cur: path.append(cur); cur=par[cur]
                path.reverse()
                print("Path:", path)
                draw_graph(g, edges_from_path(path), "Bellman-Ford")
            continue

        if choice == "6":
            g = user_defined_graph()
            while True:
                src = get_valid_node("Enter source node (0 to exit): ", g)
                if src is None: break
                dst = get_valid_node("Enter destination node (0 to exit): ", g)
                if dst is None: break
                algo = menu()
                if algo == "0":
                    break
                run_algorithm(g, algo, src, dst)
            continue

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
        src, dst = "A","F"
        run_algorithm(g, choice, src, dst)

def run_algorithm(g, choice, src, dst):
    if choice == "1":
        dist, par = dijkstra(g, src)
        path=[]; cur=dst
        while cur: path.append(cur); cur=par[cur]
        path.reverse()
        print("Dijkstra Path:", path, "cost=", dist[dst])
        draw_graph(g, edges_from_path(path), "Dijkstra")

    elif choice == "2":
        dist, par = bellman_ford(g, src)
        if dist is None:
            print("Negative cycle detected!")
            draw_graph(g, title="Graph")
            return
        path=[]; cur=dst
        while cur: path.append(cur); cur=par[cur]
        path.reverse()
        print("Bellman-Ford Path:", path, "cost=", dist[dst])
        draw_graph(g, edges_from_path(path), "Bellman-Ford")

    elif choice == "3":
        nodes, dist, nxt = floyd_warshall(g)
        print("Distance Matrix:")
        for i,u in enumerate(nodes):
            row = {nodes[j]:dist[i][j] if dist[i][j]!=math.inf else "inf" for j in range(len(nodes))}
            print(f"{u}: {row}")
        path = fw_path(nodes, dist, nxt, src, dst)
        print("FW Path:", path)
        draw_graph(g, edges_from_path(path), "Floyd-Warshall")

    elif choice == "4":
        path, cost = a_star(g, src, dst)
        print("A* Path:", path, "cost=", cost)
        draw_graph(g, edges_from_path(path), "A*")

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
