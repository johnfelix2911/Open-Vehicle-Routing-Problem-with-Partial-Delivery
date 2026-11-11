"""
MILP Formulations for the Open Vehicle Routing Problem with Split Deliveries (OVRPSD).

Implements both mathematical formulations from:
  Ruiz y Ruiz et al. (2022) - "Open vehicle routing problem with split deliveries"

Formulation 1: Classical approach with arc-indexed u^k_ij variables (Section 2.1)
Formulation 2: Simplified approach with node-indexed u^k_i variables (Section 2.2)

Uses PuLP library with CBC solver (open-source alternative to CPLEX).
"""

import os
import re
import tempfile
import pulp
import math
import time
import numpy as np
from instance_generator import OVRPSDInstance


class OVRPSDSolution:
    """
    Represents a solution to the OVRPSD problem.

    Attributes:
        instance (OVRPSDInstance): The problem instance
        status (str): Solver status ('Optimal', 'Feasible', 'Infeasible', etc.)
        objective (float): Objective function value (total cost)
        routes (list[list[int]]): List of routes, each route is a list of node indices
        deliveries (dict): {(customer, vehicle): amount} deliveries
        vehicles_used (int): Number of vehicles used
        splits (int): Number of customers with split deliveries
        gap (float): Optimality gap percentage, (UB - LB) / LB * 100 as in the paper
        cpu_time (float): Elapsed CPU time in seconds
        initial_lb (float): LP relaxation value at the root node ("Initial LB")
        lower_bound (float): Best lower bound found
        upper_bound (float): Best upper bound (feasible solution) found
        cuts_added (int): Rounded-capacity cuts added by the cutting-plane phase
    """

    def __init__(self):
        self.instance = None
        self.status = "Not Solved"
        self.objective = float("inf")
        self.routes = []
        self.deliveries = {}
        self.vehicles_used = 0
        self.splits = 0
        self.gap = float("inf")
        self.cpu_time = 0.0
        self.initial_lb = None
        self.lower_bound = 0.0
        self.upper_bound = float("inf")
        self.cuts_added = 0

    def __repr__(self):
        return (
            f"OVRPSDSolution(status='{self.status}', "
            f"objective={self.objective:.2f}, "
            f"vehicles={self.vehicles_used}, "
            f"splits={self.splits}, "
            f"gap={self.gap:.2f}%, "
            f"cpu_time={self.cpu_time:.2f}s)"
        )


def solve_formulation1(instance, H=None, time_limit=600, verbose=False):
    """
    Solve the OVRPSD using Formulation 1 (Section 2.1 of the paper).

    This formulation uses:
    - Arc-indexed flow variables u^k_ij (more variables, tighter LP relaxation)
    - Explicit vehicle activation variables z^k
    - MTZ-style sub-tour elimination with arc flow

    Args:
        instance (OVRPSDInstance): The problem instance
        H (float): Hiring cost override (if None, uses instance.H)
        time_limit (int): Maximum solver time in seconds
        verbose (bool): Print solver output

    Returns:
        OVRPSDSolution: The solution object
    """
    start_time = time.time()
    sol = OVRPSDSolution()
    sol.instance = instance

    n = instance.n
    Q = instance.Q
    HC = H if H is not None else instance.H
    L = instance.L
    K_size = instance.K
    c = instance.cost_matrix
    d = instance.demands

    # Sets
    V = list(range(n + 1))       # All nodes (0 = depot, 1..n = customers)
    V_plus = list(range(1, n + 1))  # Customer nodes only
    K = list(range(K_size))      # Vehicle indices

    # ---- Create the MILP model ----
    model = pulp.LpProblem(f"OVRPSD_F1_{instance.name}", pulp.LpMinimize)

    # ---- Decision Variables ----
    # x[i][j][k]: binary, vehicle k uses arc (i,j)
    x = {}
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    x[i, j, k] = pulp.LpVariable(f"x_{i}_{j}_{k}", cat="Binary")

    # z[k]: binary, vehicle k is activated
    z = {}
    for k in K:
        z[k] = pulp.LpVariable(f"z_{k}", cat="Binary")

    # s[j][k]: binary, node j is the terminal node of vehicle k's route.
    # Eq. (14) indexes s by k; a single s_j shared by the per-vehicle balance
    # (6) would force every vehicle to end at j, making the model infeasible.
    s = {}
    for j in V_plus:
        for k in K:
            s[j, k] = pulp.LpVariable(f"s_{j}_{k}", cat="Binary")

    # u[i][j][k]: continuous, cumulative demand on arc (i,j) by vehicle k
    u = {}
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    u[i, j, k] = pulp.LpVariable(f"u_{i}_{j}_{k}", lowBound=0)

    # q[i][k]: continuous, demand delivered to node i by vehicle k
    q = {}
    for i in V_plus:
        for k in K:
            q[i, k] = pulp.LpVariable(f"q_{i}_{k}", lowBound=0)

    # ---- Objective Function (Eq. 1) ----
    # Minimize total travel cost + vehicle hiring cost
    model += (
        pulp.lpSum(c[i][j] * x[i, j, k] for i in V for j in V_plus if i != j for k in K)
        + pulp.lpSum(HC * z[k] for k in K),
        "Objective"
    )

    # ---- Constraints ----

    # Eq. (2): Fleet size limit
    model += (
        pulp.lpSum(x[0, j, k] for j in V_plus for k in K) <= K_size,
        "Fleet_size_limit"
    )

    # Eq. (3): Number of starting routes = number of ending routes
    model += (
        pulp.lpSum(x[0, j, k] for j in V_plus for k in K)
        == pulp.lpSum(s[j, k] for j in V_plus for k in K),
        "Start_end_balance"
    )

    # Non-split terminal vertices (Sect. 2.1): at most one route ends at each node
    for j in V_plus:
        model += (
            pulp.lpSum(s[j, k] for k in K) <= 1,
            f"Single_terminal_{j}"
        )

    # Eq. (4): Vehicle activation
    for k in K:
        model += (
            pulp.lpSum(x[0, j, k] for j in V_plus) <= z[k],
            f"Vehicle_activation_{k}"
        )

    # Eq. (5): Every customer visited at least once
    for j in V_plus:
        model += (
            pulp.lpSum(x[i, j, k] for i in V if i != j for k in K) >= 1,
            f"Visit_{j}"
        )

    # Eq. (6): Flow balance at each customer node
    for j in V_plus:
        for k in K:
            model += (
                pulp.lpSum(x[i, j, k] for i in V if i != j)
                == pulp.lpSum(x[j, i, k] for i in V_plus if i != j) + s[j, k],
                f"Flow_balance_{j}_{k}"
            )

    # Eq. (7): Demand fulfillment
    for i in V_plus:
        model += (
            pulp.lpSum(q[i, k] for k in K) == d[i - 1],
            f"Demand_fulfillment_{i}"
        )

    # Eq. (8): Delivery capacity per vehicle
    for i in V_plus:
        for k in K:
            model += (
                q[i, k] <= d[i - 1] * pulp.lpSum(x[j, i, k] for j in V if j != i),
                f"Delivery_capacity_{i}_{k}"
            )

    # Eq. (9): Route distance limit
    for k in K:
        model += (
            pulp.lpSum(
                c[i][j] * x[i, j, k] for i in V for j in V_plus if i != j
            ) <= L * z[k],
            f"Route_distance_{k}"
        )

    # Eq. (10): MTZ cumulative demand flow
    for i in V_plus:
        for k in K:
            model += (
                u[0, i, k]
                + pulp.lpSum(u[j, i, k] for j in V_plus if j != i)
                - pulp.lpSum(u[i, j, k] for j in V_plus if j != i)
                == q[i, k],
                f"MTZ_flow_{i}_{k}"
            )

    # Eq. (11): Lower bound on u
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    model += (
                        u[i, j, k] >= q[j, k] - Q * (1 - x[i, j, k]),
                        f"U_lower_{i}_{j}_{k}"
                    )

    # Eq. (12): Upper bound on u
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    model += (
                        u[i, j, k] <= Q * x[i, j, k],
                        f"U_upper_{i}_{j}_{k}"
                    )

    # ---- Solve ----
    cbc_info = _solve_with_cbc(model, time_limit, verbose)

    elapsed = time.time() - start_time

    # ---- Extract Solution ----
    sol.cpu_time = elapsed

    if _set_status_and_bounds(sol, model, cbc_info):
        # Extract routes
        sol.routes = _extract_routes(x, n, K_size, V, V_plus)

        # Extract deliveries and count splits
        sol.deliveries = {}
        vehicles_per_customer = {}
        for i in V_plus:
            vehicles_per_customer[i] = 0
            for k in K:
                qval = pulp.value(q[i, k])
                if qval is not None and qval > 0.5:
                    sol.deliveries[(i, k)] = qval
                    vehicles_per_customer[i] += 1

        sol.splits = sum(1 for v in vehicles_per_customer.values() if v > 1)
        sol.vehicles_used = len(sol.routes)

    return sol


def solve_formulation2(instance, H=None, time_limit=600, verbose=False,
                       relax_integers=False, exclude_mtz=False,
                       extra_constraints=None):
    """
    Solve the OVRPSD using Formulation 2 (Section 2.2 of the paper).

    This is the improved formulation with:
    - Node-indexed flow variables u^k_i (fewer variables)
    - Hiring cost absorbed into depot departure arcs (z^k eliminated)
    - Simplified MTZ constraint (Eq. 28)

    Args:
        instance (OVRPSDInstance): The problem instance
        H (float): Hiring cost override (if None, uses instance.H)
        time_limit (int): Maximum solver time in seconds
        verbose (bool): Print solver output
        relax_integers (bool): If True, relax binary variables to continuous [0,1]
                               (used in cutting-plane method)
        exclude_mtz (bool): If True, exclude MTZ constraint (28)
                            (used in cutting-plane method)
        extra_constraints (list): Additional constraints to add (cutting planes)

    Returns:
        OVRPSDSolution: The solution object
        dict: x variable references (for extracting fractional values)
    """
    start_time = time.time()
    sol = OVRPSDSolution()
    sol.instance = instance

    n = instance.n
    Q = instance.Q
    HC = H if H is not None else instance.H
    L = instance.L
    K_size = instance.K
    c = instance.cost_matrix.copy()
    d = instance.demands

    # Absorb hiring cost into depot departure arcs (key simplification of Form. 2)
    c_modified = c.copy()
    for j in range(1, n + 1):
        c_modified[0][j] = c[0][j] + HC

    # Sets
    V = list(range(n + 1))
    V_plus = list(range(1, n + 1))
    K = list(range(K_size))

    # ---- Create the MILP model ----
    cat = "Continuous" if relax_integers else "Binary"
    model = pulp.LpProblem(f"OVRPSD_F2_{instance.name}", pulp.LpMinimize)

    # ---- Decision Variables ----
    # x[i][j][k]: vehicle k uses arc (i,j)
    x = {}
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    if relax_integers:
                        x[i, j, k] = pulp.LpVariable(
                            f"x_{i}_{j}_{k}", lowBound=0, upBound=1, cat="Continuous"
                        )
                    else:
                        x[i, j, k] = pulp.LpVariable(f"x_{i}_{j}_{k}", cat="Binary")

    # s[j]: node j is terminal node
    s = {}
    for j in V_plus:
        if relax_integers:
            s[j] = pulp.LpVariable(f"s_{j}", lowBound=0, upBound=1, cat="Continuous")
        else:
            s[j] = pulp.LpVariable(f"s_{j}", cat="Binary")

    # u[i][k]: cumulative load of vehicle k after visiting node i
    u_var = {}
    for i in V:
        for k in K:
            u_var[i, k] = pulp.LpVariable(f"u_{i}_{k}", lowBound=0)

    # q[i][k]: demand delivered to node i by vehicle k
    q = {}
    for i in V_plus:
        for k in K:
            q[i, k] = pulp.LpVariable(f"q_{i}_{k}", lowBound=0)

    # ---- Objective Function (Eq. 18) ----
    # HC is absorbed into c_modified[0][j], so no separate z^k term
    model += (
        pulp.lpSum(
            c_modified[i][j] * x[i, j, k]
            for i in V for j in V_plus if i != j for k in K
        ),
        "Objective"
    )

    # ---- Constraints ----

    # Eq. (19): Number of starting routes = number of ending routes
    model += (
        pulp.lpSum(x[0, j, k] for j in V_plus for k in K)
        == pulp.lpSum(s[j] for j in V_plus),
        "Start_end_balance"
    )

    # Eq. (20): Each vehicle departs from depot at most once
    for k in K:
        model += (
            pulp.lpSum(x[0, j, k] for j in V_plus) <= 1,
            f"Vehicle_depart_{k}"
        )

    # Eq. (21): Every customer visited at least once
    for j in V_plus:
        model += (
            pulp.lpSum(x[i, j, k] for i in V if i != j for k in K) >= 1,
            f"Visit_{j}"
        )

    # Eq. (22): Flow balance (aggregated over vehicles)
    for j in V_plus:
        model += (
            pulp.lpSum(x[i, j, k] for i in V if i != j for k in K)
            == pulp.lpSum(x[j, i, k] for i in V_plus if i != j for k in K) + s[j],
            f"Flow_balance_agg_{j}"
        )

    # Eq. (23): Per-vehicle flow balance at customer nodes
    for j in V_plus:
        for k in K:
            model += (
                pulp.lpSum(x[i, j, k] for i in V if i != j)
                >= pulp.lpSum(x[j, i, k] for i in V_plus if i != j),
                f"Flow_balance_veh_{j}_{k}"
            )

    # Eq. (24): Demand fulfillment
    for i in V_plus:
        model += (
            pulp.lpSum(q[i, k] for k in K) == d[i - 1],
            f"Demand_{i}"
        )

    # Eq. (25): Delivery upper bound
    for i in V_plus:
        for k in K:
            model += (
                d[i - 1] * pulp.lpSum(x[j, i, k] for j in V if j != i) - q[i, k] >= 0,
                f"Delivery_upper_{i}_{k}"
            )

    # Eq. (26): Delivery requires visit
    for i in V_plus:
        for k in K:
            model += (
                pulp.lpSum(x[j, i, k] for j in V if j != i) - q[i, k] <= 0,
                f"Delivery_visit_{i}_{k}"
            )

    # Eq. (27): Route distance limit
    for k in K:
        model += (
            pulp.lpSum(
                c[i][j] * x[i, j, k] for i in V for j in V_plus if i != j
            ) <= L,
            f"Route_distance_{k}"
        )

    # Eq. (28): Simplified MTZ sub-tour elimination (only if not excluded)
    if not exclude_mtz:
        for i in V:
            for j in V_plus:
                if i != j:
                    for k in K:
                        model += (
                            u_var[i, k] - u_var[j, k] + Q * x[i, j, k]
                            <= Q - q[j, k],
                            f"MTZ_{i}_{j}_{k}"
                        )

    # Add extra constraints (cutting planes): rounded-capacity inequalities (33)
    if extra_constraints:
        for idx, (D, required) in enumerate(extra_constraints):
            V_minus_D = [i for i in V if i not in D]
            model += (
                pulp.lpSum(
                    x[i, j, k]
                    for i in V_minus_D for j in D for k in K if (i, j, k) in x
                ) >= required,
                f"Capacity_cut_{idx}"
            )

    # ---- Solve ----
    cbc_info = _solve_with_cbc(model, time_limit, verbose)

    elapsed = time.time() - start_time

    # ---- Extract Solution ----
    sol.cpu_time = elapsed

    if _set_status_and_bounds(sol, model, cbc_info):
        if relax_integers:
            # A pure LP has no branch-and-bound phase: its optimum is the root LB
            sol.initial_lb = sol.objective
        else:
            # Extract routes
            sol.routes = _extract_routes(x, n, K_size, V, V_plus)

            # Extract deliveries and count splits
            sol.deliveries = {}
            vehicles_per_customer = {}
            for i in V_plus:
                vehicles_per_customer[i] = 0
                for k in K:
                    qval = pulp.value(q[i, k])
                    if qval is not None and qval > 0.5:
                        sol.deliveries[(i, k)] = qval
                        vehicles_per_customer[i] += 1

            sol.splits = sum(1 for v in vehicles_per_customer.values() if v > 1)
            sol.vehicles_used = len(sol.routes)

    # Return x variable references for cutting-plane method
    x_ref = x
    return sol, x_ref


def solve_formulation2_no_split(instance, H=None, time_limit=600, verbose=False):
    """
    Solve the OVRPSD WITHOUT allowing split deliveries.

    This is the modified version of Formulation 2 used in the case study (Section 6.2)
    for comparison. Constraints (24), (25), (26) are removed, and q^k_j is replaced
    with d_j in constraint (28).

    Args:
        instance (OVRPSDInstance): The problem instance
        H (float): Hiring cost override
        time_limit (int): Maximum solver time
        verbose (bool): Print solver output

    Returns:
        OVRPSDSolution: The solution object
    """
    start_time = time.time()
    sol = OVRPSDSolution()
    sol.instance = instance

    n = instance.n
    Q = instance.Q
    HC = H if H is not None else instance.H
    L = instance.L
    K_size = instance.K
    c = instance.cost_matrix.copy()
    d = instance.demands

    # Absorb hiring cost
    c_modified = c.copy()
    for j in range(1, n + 1):
        c_modified[0][j] = c[0][j] + HC

    V = list(range(n + 1))
    V_plus = list(range(1, n + 1))
    K = list(range(K_size))

    model = pulp.LpProblem(f"OVRPSD_NoSplit_{instance.name}", pulp.LpMinimize)

    # Variables (no q variables needed since no splitting)
    x = {}
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    x[i, j, k] = pulp.LpVariable(f"x_{i}_{j}_{k}", cat="Binary")

    s = {}
    for j in V_plus:
        s[j] = pulp.LpVariable(f"s_{j}", cat="Binary")

    u_var = {}
    for i in V:
        for k in K:
            u_var[i, k] = pulp.LpVariable(f"u_{i}_{k}", lowBound=0)

    # Objective (Eq. 18)
    model += pulp.lpSum(
        c_modified[i][j] * x[i, j, k]
        for i in V for j in V_plus if i != j for k in K
    )

    # Eq. (19): Start = End
    model += (
        pulp.lpSum(x[0, j, k] for j in V_plus for k in K)
        == pulp.lpSum(s[j] for j in V_plus)
    )

    # Eq. (20): Each vehicle departs at most once
    for k in K:
        model += pulp.lpSum(x[0, j, k] for j in V_plus) <= 1

    # Each customer visited exactly once (no splitting)
    for j in V_plus:
        model += pulp.lpSum(x[i, j, k] for i in V if i != j for k in K) == 1

    # Flow balance
    for j in V_plus:
        model += (
            pulp.lpSum(x[i, j, k] for i in V if i != j for k in K)
            == pulp.lpSum(x[j, i, k] for i in V_plus if i != j for k in K) + s[j]
        )

    for j in V_plus:
        for k in K:
            model += (
                pulp.lpSum(x[i, j, k] for i in V if i != j)
                >= pulp.lpSum(x[j, i, k] for i in V_plus if i != j)
            )

    # Route distance limit
    for k in K:
        model += pulp.lpSum(
            c[i][j] * x[i, j, k] for i in V for j in V_plus if i != j
        ) <= L

    # MTZ with d_j instead of q_j (no splitting)
    for i in V:
        for j in V_plus:
            if i != j:
                for k in K:
                    model += (
                        u_var[i, k] - u_var[j, k] + Q * x[i, j, k]
                        <= Q - d[j - 1]
                    )

    # Solve
    cbc_info = _solve_with_cbc(model, time_limit, verbose)
    elapsed = time.time() - start_time

    sol.cpu_time = elapsed

    if _set_status_and_bounds(sol, model, cbc_info):
        sol.routes = _extract_routes(x, n, K_size, V, V_plus)
        sol.vehicles_used = len(sol.routes)
        sol.splits = 0

    return sol


def _extract_routes(x, n, K_size, V, V_plus):
    """
    Extract the vehicle routes from the solution x variables.

    Returns:
        list[list[int]]: Each route is a list of node indices starting from depot
    """
    routes = []

    for k in range(K_size):
        # Check if vehicle k departs from depot
        start_node = None
        for j in V_plus:
            val = pulp.value(x.get((0, j, k)))
            if val is not None and val > 0.5:
                start_node = j
                break

        if start_node is None:
            continue

        # Follow the route
        route = [0, start_node]
        current = start_node
        visited = {0, start_node}
        max_steps = n + 2  # Safety limit

        for _ in range(max_steps):
            next_node = None
            for j in V_plus:
                if j != current and j not in visited:
                    val = pulp.value(x.get((current, j, k)))
                    if val is not None and val > 0.5:
                        next_node = j
                        break

            if next_node is None:
                break

            route.append(next_node)
            visited.add(next_node)
            current = next_node

        routes.append(route)

    return routes


def _solve_with_cbc(model, time_limit, verbose):
    """
    Solve the model with CBC and parse its log for the bounds PuLP does not expose.

    CBC runs single-threaded: the PuLP-bundled Windows build deadlocks during
    root-node cut generation when the `threads` option is set.

    Args:
        model (pulp.LpProblem): The model to solve
        time_limit (float): Solver time limit in seconds
        verbose (bool): Print the CBC log after solving

    Returns:
        dict: {'initial_lb': float|None, 'lower_bound': float|None, 'stopped': bool}
    """
    fd, log_path = tempfile.mkstemp(prefix="cbc_", suffix=".log")
    os.close(fd)
    try:
        model.solve(pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=False, logPath=log_path))
        with open(log_path) as f:
            log = f.read()
    finally:
        os.remove(log_path)

    if verbose:
        print(log)

    info = {
        "initial_lb": None,
        "lower_bound": None,
        "stopped": "Result - Stopped on" in log,
    }
    match = re.search(r"Continuous objective value is\s+(\S+)", log)
    if match:
        info["initial_lb"] = float(match.group(1))
    match = re.search(r"Lower bound:\s+(\S+)", log)
    if match:
        info["lower_bound"] = float(match.group(1))
    return info


def _set_status_and_bounds(sol, model, cbc_info):
    """
    Fill status, objective, bounds and GAP of `sol` from the solved model.

    GAP follows the paper's tables: (UB - LB) / LB * 100.

    Returns:
        bool: True if the solver produced a feasible solution
    """
    sol.initial_lb = cbc_info["initial_lb"]

    if model.sol_status not in (pulp.LpSolutionOptimal, pulp.LpSolutionIntegerFeasible):
        sol.status = "Infeasible" if model.status == pulp.LpStatusInfeasible else "No Solution"
        return False

    sol.objective = pulp.value(model.objective)
    sol.upper_bound = sol.objective

    if model.sol_status == pulp.LpSolutionOptimal and not cbc_info["stopped"]:
        sol.status = "Optimal"
        sol.lower_bound = sol.objective
        sol.gap = 0.0
    else:
        # Stopped on the time limit with an incumbent
        sol.status = "Feasible"
        lb = cbc_info["lower_bound"]
        sol.lower_bound = lb if lb is not None else 0.0
        sol.gap = (sol.objective - lb) / lb * 100 if lb else float("inf")
    return True


if __name__ == "__main__":
    from instance_generator import generate_instance

    print("=" * 60)
    print("OVRPSD Model Test")
    print("=" * 60)

    # Create a small test instance
    inst = generate_instance("TEST-5", n=5, Q=100, H=0, seed=42)
    print(f"\nInstance: {inst}")
    print(f"Demands: {inst.demands}")
    print(f"Max route distance: {inst.L}")

    # Test Formulation 2 (the better one)
    print("\n--- Solving with Formulation 2 ---")
    sol2, _ = solve_formulation2(inst, H=0, time_limit=120, verbose=False)
    print(f"Solution: {sol2}")
    for i, route in enumerate(sol2.routes):
        print(f"  Route {i + 1}: {' -> '.join(str(n) for n in route)}")

    # Test with hiring cost
    print("\n--- Solving with Formulation 2 (HC=50) ---")
    sol2_hc, _ = solve_formulation2(inst, H=50, time_limit=120, verbose=False)
    print(f"Solution: {sol2_hc}")
    for i, route in enumerate(sol2_hc.routes):
        print(f"  Route {i + 1}: {' -> '.join(str(n) for n in route)}")

    # Test no-split version
    print("\n--- Solving without Split Deliveries ---")
    sol_ns = solve_formulation2_no_split(inst, H=50, time_limit=120, verbose=False)
    print(f"Solution: {sol_ns}")
    for i, route in enumerate(sol_ns.routes):
        print(f"  Route {i + 1}: {' -> '.join(str(n) for n in route)}")
