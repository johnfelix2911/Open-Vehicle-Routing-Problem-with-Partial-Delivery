"""
Cutting-Plane Method for the OVRPSD.

Implements the cutting-plane algorithm described in Section 4 of:
  Ruiz y Ruiz et al. (2022) - "Open vehicle routing problem with split deliveries"

The algorithm:
1. Start with Formulation 2 (without MTZ constraint 28, with relaxed integrality)
2. Solve the LP relaxation
3. Build a support graph from the fractional solution
4. Use max-flow/min-cut to find violated rounded-capacity inequalities
5. Add violated inequalities as cuts
6. Repeat until no more cuts are found
7. Add MTZ constraints + restore integrality, solve final MILP
"""

import pulp
import math
import time
import numpy as np

from instance_generator import OVRPSDInstance
from ovrpsd_model import OVRPSDSolution, solve_formulation2
from max_flow import find_violated_capacity_cuts


def solve_with_cutting_planes(instance, H=None, time_limit=600,
                               max_cuts_iterations=50, verbose=False):
    """
    Solve the OVRPSD using the cutting-plane method based on Formulation 2.

    Algorithm (from Section 4 of the paper):
    1. Start with Formulation 2 without constraint (28), relax integrality
    2. Solve LP relaxation → get fractional solution x*
    3. Build support graph G* from x*
    4. For each customer j, compute max-flow from depot to j
    5. If max-flow < ceil(d(D)/Q), add rounded-capacity inequality as cut
    6. Repeat until no violated cuts found
    7. Add constraint (28) and integrality constraints
    8. Solve the full MILP with time limit

    Args:
        instance (OVRPSDInstance): The problem instance
        H (float): Hiring cost override
        time_limit (int): Total time limit in seconds
        max_cuts_iterations (int): Maximum cutting plane iterations
        verbose (bool): Print detailed progress

    Returns:
        OVRPSDSolution: The final solution
    """
    start_time = time.time()

    n = instance.n
    Q = instance.Q
    HC = H if H is not None else instance.H
    K_size = instance.K
    d = instance.demands

    if verbose:
        print(f"\n{'='*60}")
        print(f"Cutting-Plane Method for {instance.name} (HC={HC})")
        print(f"{'='*60}")

    # Collect all cuts found across iterations
    all_cuts = []

    # ---- Phase 1: Iterative Cutting Plane ----
    for iteration in range(max_cuts_iterations):
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            if verbose:
                print(f"  Time limit reached during cutting plane phase.")
            break

        if verbose:
            print(f"\n  --- Cutting Plane Iteration {iteration + 1} ---")

        # Solve LP relaxation (no MTZ, relaxed integers, with accumulated cuts)
        remaining_time = max(10, time_limit - elapsed)

        sol_lp, x_ref = solve_formulation2(
            instance,
            H=HC,
            time_limit=min(remaining_time, 300),
            verbose=False,
            relax_integers=True,
            exclude_mtz=True,
            extra_constraints=all_cuts,
        )

        if sol_lp.status not in ["Optimal", "Feasible"]:
            if verbose:
                print(f"  LP relaxation infeasible or error: {sol_lp.status}")
            break

        initial_lb = sol_lp.objective
        if verbose:
            print(f"  LP relaxation value (LB): {initial_lb:.2f}")

        # Extract fractional x values
        x_values = {}
        for key, var in x_ref.items():
            val = pulp.value(var)
            if val is not None and val > 1e-9:
                x_values[key] = val

        # Find violated capacity cuts using max-flow
        violated_cuts = find_violated_capacity_cuts(
            n, K_size, Q, d, x_values
        )

        if not violated_cuts:
            if verbose:
                print(f"  No violated cuts found. Cutting plane phase complete.")
            break

        # Add new cuts
        new_cuts_added = 0
        for D, required in violated_cuts:
            # Check if this cut is already in our collection
            cut_exists = False
            for existing_D, existing_req in all_cuts:
                if existing_D == D and existing_req == required:
                    cut_exists = True
                    break

            if not cut_exists:
                all_cuts.append((D, required))
                new_cuts_added += 1
                if verbose:
                    print(f"    Added cut: D={D}, required_flow={required}")

        if new_cuts_added == 0:
            if verbose:
                print(f"  No new cuts to add. Cutting plane phase complete.")
            break

        if verbose:
            print(f"  Added {new_cuts_added} new cuts (total: {len(all_cuts)})")

    # ---- Phase 2: Solve Full MILP ----
    elapsed = time.time() - start_time
    remaining_time = max(30, time_limit - elapsed)

    if verbose:
        print(f"\n  --- Phase 2: Solving Full MILP ---")
        print(f"  Time remaining: {remaining_time:.1f}s")
        print(f"  Total cuts added: {len(all_cuts)}")

    # Solve the complete model with all cuts, MTZ constraints, and integer variables
    final_sol, _ = solve_formulation2(
        instance,
        H=HC,
        time_limit=remaining_time,
        verbose=verbose,
        relax_integers=False,
        exclude_mtz=False,
        extra_constraints=all_cuts,
    )

    total_time = time.time() - start_time
    final_sol.cpu_time = total_time
    final_sol.cuts_added = len(all_cuts)

    if verbose:
        print(f"\n  --- Final Results ---")
        print(f"  Status: {final_sol.status}")
        print(f"  Objective: {final_sol.objective:.2f}")
        print(f"  Lower bound: {final_sol.lower_bound:.2f} (GAP {final_sol.gap:.2f}%)")
        print(f"  Vehicles: {final_sol.vehicles_used}")
        print(f"  Splits: {final_sol.splits}")
        print(f"  Total CPU: {total_time:.2f}s")
        print(f"  Cuts used: {len(all_cuts)}")

    return final_sol


def compare_methods(instance, H_values=None, time_limit=300, verbose=False):
    """
    Compare Formulation 2 with and without cutting planes across different HC values.

    This reproduces the comparison from Tables 2 and 3 of the paper.

    Args:
        instance (OVRPSDInstance): The problem instance
        H_values (list[float]): HC values to test (default: [0, 50, 100])
        time_limit (int): Time limit per experiment
        verbose (bool): Print progress

    Returns:
        dict: Results organized by method and HC value
    """
    if H_values is None:
        H_values = [0, 50, 100]

    results = {}

    for hc in H_values:
        if verbose:
            print(f"\n{'#'*60}")
            print(f"HC = {hc}")
            print(f"{'#'*60}")

        # Without cutting planes
        if verbose:
            print(f"\n  [Formulation 2 without cutting planes]")
        sol_f2, _ = solve_formulation2(
            instance, H=hc, time_limit=time_limit, verbose=False
        )

        # With cutting planes
        if verbose:
            print(f"\n  [Formulation 2 with cutting planes]")
        sol_cp = solve_with_cutting_planes(
            instance, H=hc, time_limit=time_limit, verbose=verbose
        )

        results[hc] = {
            "formulation2": sol_f2,
            "cutting_plane": sol_cp,
        }

        if verbose:
            print(f"\n  Comparison for HC={hc}:")
            print(f"    F2:  Obj={sol_f2.objective:.2f}, "
                  f"Vehicles={sol_f2.vehicles_used}, "
                  f"Splits={sol_f2.splits}, "
                  f"Time={sol_f2.cpu_time:.2f}s")
            print(f"    CP:  Obj={sol_cp.objective:.2f}, "
                  f"Vehicles={sol_cp.vehicles_used}, "
                  f"Splits={sol_cp.splits}, "
                  f"Time={sol_cp.cpu_time:.2f}s")

    return results


if __name__ == "__main__":
    from instance_generator import generate_instance

    print("=" * 60)
    print("Cutting-Plane Method Test")
    print("=" * 60)

    # Create a small test instance
    inst = generate_instance("CP-TEST-8", n=8, Q=100, H=0, seed=42)
    print(f"\nInstance: {inst}")
    print(f"Demands: {inst.demands}")

    # Solve with cutting planes
    sol = solve_with_cutting_planes(
        inst, H=50, time_limit=120, verbose=True
    )

    print(f"\nFinal Solution: {sol}")
    if sol.routes:
        for i, route in enumerate(sol.routes):
            print(f"  Route {i + 1}: {' -> '.join(str(n) for n in route)}")
