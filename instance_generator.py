"""
Instance Generator for the Open Vehicle Routing Problem with Split Deliveries (OVRPSD).

Generates random test instances following the criteria described in:
  Ruiz y Ruiz et al. (2022) - "Open vehicle routing problem with split deliveries"

Based on the generation procedure from Archetti et al. (2008) to encourage splitting.
"""

import numpy as np
import json
import os
import math


class OVRPSDInstance:
    """
    Represents a single OVRPSD problem instance.

    Attributes:
        name (str): Instance identifier (e.g., 'IES20-1')
        n (int): Number of customers (excluding depot)
        depot (tuple): (x, y) coordinates of the depot
        customers (list[tuple]): List of (x, y) coordinates for each customer
        demands (list[int]): Demand of each customer (index 0 = customer 1)
        Q (int): Vehicle capacity
        H (float): Hiring cost per vehicle
        L (float): Maximum allowed route distance
        K (int): Number of available vehicles (fleet size)
        cost_matrix (np.ndarray): Symmetric cost/distance matrix (n+1 x n+1)
    """

    def __init__(self, name, n, depot, customers, demands, Q, H, L, K, cost_matrix):
        self.name = name
        self.n = n
        self.depot = depot
        self.customers = customers
        self.demands = demands
        self.Q = Q
        self.H = H
        self.L = L
        self.K = K
        self.cost_matrix = cost_matrix

    def total_demand(self):
        """Return the total demand across all customers."""
        return sum(self.demands)

    def min_vehicles_needed(self):
        """Return the minimum number of vehicles needed based on capacity."""
        return math.ceil(self.total_demand() / self.Q)

    def __repr__(self):
        return (
            f"OVRPSDInstance(name='{self.name}', n={self.n}, "
            f"Q={self.Q}, H={self.H}, L={self.L}, K={self.K}, "
            f"total_demand={self.total_demand()}, "
            f"min_vehicles={self.min_vehicles_needed()})"
        )

    def to_dict(self):
        """Serialize instance to a dictionary for JSON storage."""
        return {
            "name": self.name,
            "n": self.n,
            "depot": list(self.depot),
            "customers": [list(c) for c in self.customers],
            "demands": self.demands,
            "Q": self.Q,
            "H": self.H,
            "L": self.L,
            "K": self.K,
            "cost_matrix": self.cost_matrix.tolist(),
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize instance from a dictionary."""
        return cls(
            name=data["name"],
            n=data["n"],
            depot=tuple(data["depot"]),
            customers=[tuple(c) for c in data["customers"]],
            demands=data["demands"],
            Q=data["Q"],
            H=data["H"],
            L=data["L"],
            K=data["K"],
            cost_matrix=np.array(data["cost_matrix"]),
        )

    def save(self, filepath):
        """Save instance to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath):
        """Load instance from a JSON file."""
        with open(filepath, "r") as f:
            return cls.from_dict(json.load(f))


def compute_euclidean_distance_matrix(depot, customers):
    """
    Compute the symmetric Euclidean distance matrix between all nodes.

    Args:
        depot (tuple): (x, y) coordinates of the depot (node 0)
        customers (list[tuple]): List of (x, y) customer coordinates

    Returns:
        np.ndarray: Distance matrix of shape (n+1, n+1)
    """
    all_nodes = [depot] + customers
    n_total = len(all_nodes)
    dist = np.zeros((n_total, n_total))
    for i in range(n_total):
        for j in range(i + 1, n_total):
            dx = all_nodes[i][0] - all_nodes[j][0]
            dy = all_nodes[i][1] - all_nodes[j][1]
            d = math.sqrt(dx * dx + dy * dy)
            dist[i][j] = round(d, 2)
            dist[j][i] = round(d, 2)
    return dist


def generate_instance(name, n, Q=100, H=0, L=None, seed=None):
    """
    Generate a random OVRPSD instance.

    Follows the generation criteria from Archetti et al. (2008) to encourage
    split deliveries: customer demands are drawn from a range that makes them
    large relative to vehicle capacity.

    Args:
        name (str): Instance name
        n (int): Number of customers
        Q (int): Vehicle capacity (default: 100)
        H (float): Hiring cost per vehicle (default: 0)
        L (float): Max route distance (default: auto-calculated)
        seed (int): Random seed for reproducibility

    Returns:
        OVRPSDInstance: The generated instance
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate depot at center of a 100x100 grid
    depot = (50.0, 50.0)

    # Generate customer locations uniformly in [0, 100] x [0, 100]
    customers = [(np.random.uniform(0, 100), np.random.uniform(0, 100)) for _ in range(n)]

    # Generate demands to encourage splitting:
    # Demands are drawn from [0.3*Q, 0.9*Q] (one of Archetti et al.'s demand
    # classes), so many customers need > 50% capacity and splitting pays off
    demands = [int(np.random.uniform(0.3 * Q, 0.9 * Q)) for _ in range(n)]

    # Compute distance matrix
    cost_matrix = compute_euclidean_distance_matrix(depot, customers)

    # Maximum route distance: if not specified, use a generous default
    if L is None:
        # Use 3 times the maximum distance from depot to any customer
        max_depot_dist = max(cost_matrix[0, j] for j in range(1, n + 1))
        L = round(3.0 * max_depot_dist, 2)

    # Fleet size: use enough vehicles to cover total demand with some slack
    total_demand = sum(demands)
    K = math.ceil(total_demand / Q) + 2  # Add slack

    return OVRPSDInstance(
        name=name,
        n=n,
        depot=depot,
        customers=customers,
        demands=demands,
        Q=Q,
        H=H,
        L=L,
        K=K,
        cost_matrix=cost_matrix,
    )


def generate_case_study_instance(name, n, seed=None):
    """
    Generate a case study instance mimicking the pharmaceutical company scenario.

    The pharmaceutical company:
    - Located in the center of the metropolitan area
    - Serves 13-25 small pharmacies
    - Demand: 8-24 pallets per customer
    - Vehicle capacity: ~50 pallets (estimated from paper)

    Args:
        name (str): Instance name (e.g., 'CE1')
        n (int): Number of customers (13-30)
        seed (int): Random seed

    Returns:
        OVRPSDInstance: The generated instance
    """
    if seed is not None:
        np.random.seed(seed)

    # Depot at center (simulating Guadalajara city center)
    depot = (50.0, 50.0)

    # Customers distributed around metropolitan area
    # Closer customers (pharmacies) have higher demand
    customers = []
    demands = []
    for _ in range(n):
        # Distance from center varies
        angle = np.random.uniform(0, 2 * math.pi)
        radius = np.random.uniform(10, 45)
        cx = 50 + radius * math.cos(angle)
        cy = 50 + radius * math.sin(angle)
        customers.append((round(cx, 2), round(cy, 2)))

        # Demand inversely correlated with distance (closer = higher demand)
        # Range: 8-24 pallets (as stated in paper)
        base_demand = int(8 + (45 - radius) / 45 * 16)
        demands.append(max(8, min(24, base_demand + np.random.randint(-3, 4))))

    # Compute distance matrix
    cost_matrix = compute_euclidean_distance_matrix(depot, customers)

    # Vehicle capacity for case study
    Q = 50  # Estimated from paper context

    # Maximum route distance
    max_depot_dist = max(cost_matrix[0, j] for j in range(1, n + 1))
    L = round(3.5 * max_depot_dist, 2)

    # Fleet size with slack
    total_demand = sum(demands)
    K = math.ceil(total_demand / Q) + 2

    return OVRPSDInstance(
        name=name,
        n=n,
        depot=depot,
        customers=customers,
        demands=demands,
        Q=Q,
        H=0,  # HC will be varied during experiments
        L=L,
        K=K,
        cost_matrix=cost_matrix,
    )


def generate_benchmark_instances(output_dir="instances"):
    """
    Generate the full set of benchmark instances as described in the paper.

    Creates:
    - IES20-1 through IES20-10  (20 customers each)
    - IES25-1 through IES25-10  (25 customers each)
    - IES30-1 through IES30-10  (30 customers each)
    - CE1 through CE5           (case study instances)

    All saved to the output directory as JSON files.
    """
    os.makedirs(output_dir, exist_ok=True)

    instances = []

    # Benchmark instances
    for n in [20, 25, 30]:
        for i in range(1, 11):
            inst = generate_instance(
                name=f"IES{n}-{i}",
                n=n,
                Q=100,
                H=0,
                seed=n * 100 + i,
            )
            inst.save(os.path.join(output_dir, f"IES{n}-{i}.json"))
            instances.append(inst)
            print(f"  Generated {inst.name}: {inst.n} customers, "
                  f"total_demand={inst.total_demand()}, "
                  f"min_vehicles={inst.min_vehicles_needed()}")

    # Case study instances
    case_study_sizes = [21, 13, 21, 14, 21]
    for i, n in enumerate(case_study_sizes, 1):
        inst = generate_case_study_instance(
            name=f"CE{i}",
            n=n,
            seed=500 + i,
        )
        inst.save(os.path.join(output_dir, f"CE{i}.json"))
        instances.append(inst)
        print(f"  Generated {inst.name}: {inst.n} customers, "
              f"total_demand={inst.total_demand()}, "
              f"min_vehicles={inst.min_vehicles_needed()}")

    return instances


if __name__ == "__main__":
    print("=" * 60)
    print("OVRPSD Instance Generator")
    print("=" * 60)
    print()

    # Generate a small demo instance
    print("--- Demo Instance ---")
    demo = generate_instance("DEMO-5", n=5, Q=100, H=50, seed=42)
    print(demo)
    print(f"  Demands: {demo.demands}")
    print(f"  Cost matrix shape: {demo.cost_matrix.shape}")
    print()

    # Generate all benchmark instances
    print("--- Generating Benchmark Instances ---")
    instances = generate_benchmark_instances(output_dir="instances")
    print(f"\nGenerated {len(instances)} instances total.")
