"""
Max-Flow implementation using Ford-Fulkerson algorithm with BFS (Edmonds-Karp).

Used in the cutting-plane method to separate rounded-capacity inequalities
for the OVRPSD problem.

Reference: Section 4 of Ruiz y Ruiz et al. (2022)
"""

from collections import defaultdict, deque
import numpy as np


class MaxFlowGraph:
    """
    Graph structure supporting max-flow computation using the Edmonds-Karp
    variant of Ford-Fulkerson (uses BFS for augmenting paths).

    Flow is stored skew-symmetrically (flow[v][u] == -flow[u][v]), so the
    residual capacity of any ordered pair is graph[u][v] - flow[u][v]; this
    covers reverse arcs and antiparallel arcs (x_ij and x_ji) uniformly.

    Attributes:
        n (int): Number of nodes
        graph (dict): Adjacency list with capacities
        flow (dict): Current (net) flow on each node pair
        adj (dict): Neighbors in either direction, for residual traversal
    """

    def __init__(self, n):
        """
        Initialize the max-flow graph.

        Args:
            n (int): Number of nodes in the graph
        """
        self.n = n
        self.graph = defaultdict(lambda: defaultdict(float))  # capacity
        self.flow = defaultdict(lambda: defaultdict(float))   # current flow
        self.adj = defaultdict(set)

    def add_edge(self, u, v, capacity):
        """
        Add a directed edge with given capacity.

        Args:
            u (int): Source node
            v (int): Destination node
            capacity (float): Edge capacity
        """
        self.graph[u][v] += capacity  # Support multiple edges by summing capacity
        self.adj[u].add(v)
        self.adj[v].add(u)

    def residual(self, u, v):
        """Residual capacity of the ordered pair (u, v)."""
        return self.graph[u][v] - self.flow[u][v]

    def bfs(self, source, sink):
        """
        Perform BFS to find an augmenting path from source to sink.

        Args:
            source (int): Source node
            sink (int): Sink node

        Returns:
            list or None: The augmenting path as list of nodes, or None if no path exists
        """
        visited = {source}
        queue = deque([(source, [source])])

        while queue:
            node, path = queue.popleft()

            for neighbor in self.adj[node]:
                if neighbor not in visited and self.residual(node, neighbor) > 1e-9:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    if neighbor == sink:
                        return new_path
                    queue.append((neighbor, new_path))

        return None

    def max_flow(self, source, sink):
        """
        Compute the maximum flow from source to sink using Edmonds-Karp.

        Args:
            source (int): Source node
            sink (int): Sink node

        Returns:
            float: The maximum flow value
        """
        # Reset flow
        self.flow = defaultdict(lambda: defaultdict(float))
        total_flow = 0.0

        while True:
            path = self.bfs(source, sink)
            if path is None:
                break

            # Find bottleneck capacity along the path
            bottleneck = min(
                self.residual(path[i], path[i + 1]) for i in range(len(path) - 1)
            )

            # Update flow along the path (skew-symmetric)
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                self.flow[u][v] += bottleneck
                self.flow[v][u] -= bottleneck

            total_flow += bottleneck

        return total_flow

    def min_cut(self, source):
        """
        Find the minimum cut (set of nodes reachable from source in residual graph).
        Must be called after max_flow().

        Args:
            source (int): Source node

        Returns:
            set: Nodes reachable from source in the residual graph
        """
        visited = {source}
        queue = deque([source])

        while queue:
            node = queue.popleft()

            for neighbor in self.adj[node]:
                if neighbor not in visited and self.residual(node, neighbor) > 1e-9:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return visited


def build_support_graph(n, K, x_values):
    """
    Build a support graph G* from fractional LP solution values.

    In the support graph:
    - Nodes are the same as the original problem
    - An arc (i,j) exists if sum over k of x*_ij^k > 0
    - The capacity of arc (i,j) = sum over k of x*_ij^k

    This is used in the cutting-plane method (Section 4 of the paper).

    Args:
        n (int): Number of customers
        K (int): Number of vehicles
        x_values (dict): Dictionary of x[i][j][k] fractional values

    Returns:
        MaxFlowGraph: The support graph with capacities
    """
    graph = MaxFlowGraph(n + 1)  # nodes 0..n

    for i in range(n + 1):
        for j in range(1, n + 1):
            if i == j:
                continue
            # Sum over all vehicles
            total = sum(
                x_values.get((i, j, k), 0.0)
                for k in range(K)
            )
            if total > 1e-9:
                graph.add_edge(i, j, total)

    return graph


def find_violated_capacity_cuts(n, K, Q, demands, x_values):
    """
    Find violated rounded-capacity inequalities using max-flow min-cut.

    For each customer j, compute max-flow from depot (0) to j.
    If the max-flow is less than ceil(d(D)/Q) for some subset D
    containing j, the inequality is violated and should be added as a cut.

    The rounded-capacity inequality (Eq. 33 in the paper):
        sum_{k in K} sum_{i not in D} sum_{j in D} x^k_ij >= ceil(d(D)/Q)

    Args:
        n (int): Number of customers
        K (int): Number of vehicles
        Q (int): Vehicle capacity
        demands (list[int]): Customer demands (index 0 = customer 1)
        x_values (dict): Fractional LP solution

    Returns:
        list[tuple]: List of violated cuts as (D, required_flow) tuples,
                     where D is the set of customer nodes in the cut
    """
    import math

    # Build the support graph from fractional solution
    support_graph = build_support_graph(n, K, x_values)

    violated_cuts = []
    seen = set()

    # For each customer, check if capacity inequality is satisfied
    for j in range(1, n + 1):
        # Compute max-flow from depot to customer j (max_flow resets the flow)
        support_graph.max_flow(0, j)

        # Find the min-cut to identify the subset D
        reachable = support_graph.min_cut(0)

        # D = customers NOT reachable from depot in residual graph
        D = set()
        for node in range(1, n + 1):
            if node not in reachable:
                D.add(node)

        if len(D) == 0 or frozenset(D) in seen:
            continue
        seen.add(frozenset(D))

        # Left-hand side of (33): total x* entering D (equals the max-flow value)
        cut_value = sum(
            support_graph.graph[i][jj]
            for i in range(n + 1) if i not in D
            for jj in D
        )

        # Compute total demand of D
        d_D = sum(demands[node - 1] for node in D)

        # Required minimum flow = ceil(d(D) / Q)
        required = math.ceil(d_D / Q)

        # Check if the capacity inequality is violated
        if cut_value < required - 1e-6:
            violated_cuts.append((D, required))

    return violated_cuts


if __name__ == "__main__":
    # Simple test of the max-flow algorithm
    print("=" * 50)
    print("Max-Flow Algorithm Test")
    print("=" * 50)

    # Create a simple test graph
    g = MaxFlowGraph(6)
    g.add_edge(0, 1, 16)
    g.add_edge(0, 2, 13)
    g.add_edge(1, 2, 10)
    g.add_edge(1, 3, 12)
    g.add_edge(2, 1, 4)
    g.add_edge(2, 4, 14)
    g.add_edge(3, 2, 9)
    g.add_edge(3, 5, 20)
    g.add_edge(4, 3, 7)
    g.add_edge(4, 5, 4)

    max_f = g.max_flow(0, 5)
    print(f"Max flow from 0 to 5: {max_f}")
    print(f"Expected: 23")

    reachable = g.min_cut(0)
    print(f"Min-cut reachable set: {reachable}")
