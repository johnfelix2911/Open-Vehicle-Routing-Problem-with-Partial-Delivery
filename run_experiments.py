"""
Experiment Runner for the OVRPSD.

Reproduces the computational experiments from:
  Ruiz y Ruiz et al. (2022) - "Open vehicle routing problem with split deliveries"

Runs:
1. Preliminary comparison: Formulation 1 vs Formulation 2 (Section 3)
2. Cutting-plane experiments with Formulation 2 (Section 5)
3. Case study analysis (Section 6)

All results are printed in formatted tables and plots are saved.
"""

import os
import sys
import time
import math

from tabulate import tabulate

from instance_generator import (
    generate_instance,
    generate_case_study_instance,
    generate_benchmark_instances,
)
from ovrpsd_model import (
    solve_formulation1,
    solve_formulation2,
    solve_formulation2_no_split,
)
from cutting_plane import solve_with_cutting_planes
from visualization import (
    plot_instance,
    plot_solution,
    plot_comparison_bar_chart,
    plot_hc_impact,
)


def _fmt(value):
    """Format a numeric result, using 'N/A' for missing or infinite values."""
    if value is None or value == float("inf"):
        return "N/A"
    return f"{value:.2f}"


def _report_table(title, rows, filename):
    """Print a results table and save it to output/<filename>."""
    table = tabulate(rows, headers="keys", tablefmt="grid")
    print(f"\n\n  --- {title} ---")
    print(table)
    path = os.path.join("output", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{title}\n\n{table}\n")
    print(f"  [Saved table: {path}]")


def run_small_demo():
    """
    Run a small demonstration on a 5-node instance.
    Good for verifying everything works before running full experiments.
    """
    print("\n" + "=" * 70)
    print("  DEMO: Small Instance (5 customers)")
    print("=" * 70)

    inst = generate_instance("DEMO-5", n=5, Q=100, H=0, seed=42)
    print(f"\n  Instance: {inst}")
    print(f"  Demands: {inst.demands}")
    print(f"  Vehicle Capacity Q: {inst.Q}")
    print(f"  Max Route Distance L: {inst.L}")

    os.makedirs("output", exist_ok=True)

    # Plot instance
    plot_instance(inst, save_path="output/demo_instance.png", show=False)
    print("\n  [Saved instance plot: output/demo_instance.png]")

    results = []
    hc_values = [0, 50, 100]

    for hc in hc_values:
        print(f"\n  --- HC = {hc} ---")

        # Formulation 2
        print(f"  Solving with Formulation 2...")
        sol_f2, _ = solve_formulation2(inst, H=hc, time_limit=120, verbose=False)
        print(f"    F2: {sol_f2}")

        # Cutting Planes
        print(f"  Solving with Cutting Planes...")
        sol_cp = solve_with_cutting_planes(inst, H=hc, time_limit=120, verbose=False)
        print(f"    CP: {sol_cp}")

        results.append({
            "HC": hc,
            "F2_InitLB": _fmt(sol_f2.initial_lb),
            "F2_Obj": _fmt(sol_f2.objective),
            "F2_GAP%": _fmt(sol_f2.gap),
            "F2_Vehicles": sol_f2.vehicles_used,
            "F2_Splits": sol_f2.splits,
            "F2_Time": f"{sol_f2.cpu_time:.2f}",
            "CP_InitLB": _fmt(sol_cp.initial_lb),
            "CP_Obj": _fmt(sol_cp.objective),
            "CP_GAP%": _fmt(sol_cp.gap),
            "CP_Cuts": sol_cp.cuts_added,
            "CP_Vehicles": sol_cp.vehicles_used,
            "CP_Splits": sol_cp.splits,
            "CP_Time": f"{sol_cp.cpu_time:.2f}",
        })

        # Plot best solution
        best_sol = sol_cp if sol_cp.objective <= sol_f2.objective else sol_f2
        if best_sol.routes:
            plot_solution(
                inst, best_sol,
                title=f"DEMO-5 Solution (HC={hc})",
                save_path=f"output/demo_solution_hc{hc}.png",
                show=False
            )
            print(f"    [Saved solution plot: output/demo_solution_hc{hc}.png]")

    # Print summary table
    _report_table("Demo Results Summary", results, "demo_results.txt")


def run_preliminary_experiments(time_limit=300):
    """
    Reproduce the preliminary experiments from Section 3.

    Compares Formulation 1 vs Formulation 2 on a set of instances.
    """
    print("\n" + "=" * 70)
    print("  PRELIMINARY EXPERIMENTS: Formulation 1 vs Formulation 2")
    print("  (Reproducing Table 1 & 2 from the paper)")
    print("=" * 70)

    # Generate 6 test instances (similar to paper: 2x20, 2x25, 2x30)
    instances = []
    for n, suffix in [(20, "a"), (20, "b"), (25, "a"), (25, "b"), (30, "a"), (30, "b")]:
        seed = n * 10 + (ord(suffix) - ord("a"))
        inst = generate_instance(f"G{n}{suffix}", n=n, Q=100, H=0, seed=seed)
        instances.append(inst)

    hc_values = [0, 50, 100]

    results_f1 = []
    results_f2 = []

    for inst in instances:
        for hc in hc_values:
            print(f"\n  Solving {inst.name} with HC={hc}...")

            # Formulation 1
            print(f"    Formulation 1...", end=" ", flush=True)
            sol_f1 = solve_formulation1(inst, H=hc, time_limit=time_limit, verbose=False)
            print(f"Obj={sol_f1.objective:.2f}, Time={sol_f1.cpu_time:.2f}s")

            results_f1.append({
                "Instance": inst.name,
                "HC": hc,
                "n": inst.n,
                "Initial LB": _fmt(sol_f1.initial_lb),
                "UB": _fmt(sol_f1.objective),
                "LB": _fmt(sol_f1.lower_bound),
                "GAP": f"{_fmt(sol_f1.gap)}%",
                "CPU": f"{sol_f1.cpu_time:.2f}",
                "Status": sol_f1.status,
            })

            # Formulation 2
            print(f"    Formulation 2...", end=" ", flush=True)
            sol_f2, _ = solve_formulation2(inst, H=hc, time_limit=time_limit, verbose=False)
            print(f"Obj={sol_f2.objective:.2f}, Time={sol_f2.cpu_time:.2f}s")

            results_f2.append({
                "Instance": inst.name,
                "HC": hc,
                "n": inst.n,
                "Initial LB": _fmt(sol_f2.initial_lb),
                "UB": _fmt(sol_f2.objective),
                "LB": _fmt(sol_f2.lower_bound),
                "GAP": f"{_fmt(sol_f2.gap)}%",
                "CPU": f"{sol_f2.cpu_time:.2f}",
                "Status": sol_f2.status,
            })

    _report_table("Table 1: Formulation 1 Results", results_f1, "table1_formulation1.txt")
    _report_table("Table 2: Formulation 2 Results", results_f2, "table2_formulation2.txt")


def run_cutting_plane_experiments(time_limit=300):
    """
    Run experiments with the cutting-plane method (Section 5).

    Tests on generated benchmark instances with different HC values.
    """
    print("\n" + "=" * 70)
    print("  CUTTING-PLANE EXPERIMENTS")
    print("  (Reproducing Table 4 from the paper)")
    print("=" * 70)

    os.makedirs("output", exist_ok=True)

    # Generate a smaller set of instances for tractability
    instances = []
    for n in [10, 15, 20]:
        for i in range(1, 4):
            inst = generate_instance(
                f"IES{n}-{i}", n=n, Q=100, H=0,
                seed=n * 100 + i
            )
            instances.append(inst)

    hc_values = [0, 50, 100]
    all_results = []

    for inst in instances:
        for hc in hc_values:
            print(f"\n  Solving {inst.name} with HC={hc} (Cutting Planes)...")
            sol = solve_with_cutting_planes(
                inst, H=hc, time_limit=time_limit, verbose=False
            )

            row = {
                "Instance": inst.name,
                "HC": hc,
                "n": inst.n,
                "k": sol.vehicles_used,
                "Initial LB": _fmt(sol.initial_lb),
                "Best Integer": _fmt(sol.objective),
                "LB": _fmt(sol.lower_bound),
                "GAP": f"{_fmt(sol.gap)}%",
                "CPU (s)": f"{sol.cpu_time:.2f}",
                "Splits": sol.splits,
                "Cuts": sol.cuts_added,
            }
            all_results.append(row)
            print(f"    Result: {row}")

            # Plot solution for first instance of each size
            if inst.name.endswith("-1") and hc == 50 and sol.routes:
                plot_solution(
                    inst, sol,
                    title=f"{inst.name} (HC={hc}, Cutting Planes)",
                    save_path=f"output/cp_{inst.name}_hc{hc}.png",
                    show=False
                )

    _report_table("Cutting-Plane Results (Tables 7-9 layout)", all_results,
                  "cutting_plane_results.txt")


def run_case_study(time_limit=300):
    """
    Run the case study experiments (Section 6).

    Simulates the pharmaceutical company scenario with and without
    split deliveries, and compares costs.
    """
    print("\n" + "=" * 70)
    print("  CASE STUDY: Pharmaceutical Company")
    print("  (Reproducing Tables 5 and 6 from the paper)")
    print("=" * 70)

    os.makedirs("output", exist_ok=True)

    # Generate case study instances
    case_study_sizes = [21, 13, 21, 14, 21]
    instances = []
    for i, n in enumerate(case_study_sizes, 1):
        inst = generate_case_study_instance(f"CE{i}", n=n, seed=500 + i)
        instances.append(inst)

    # --- Table 5: Effect of HC ---
    print("\n  --- Table 5: Effect of HC on Solutions ---")
    table5_results = []

    for inst in instances:
        for hc in [0, 100]:
            print(f"\n  Solving {inst.name} with HC={hc}...")
            sol = solve_with_cutting_planes(
                inst, H=hc, time_limit=time_limit, verbose=False
            )

            table5_results.append({
                "Instance": inst.name,
                "n": inst.n,
                "HC": hc,
                "GAP": f"{sol.gap:.2f}%",
                "CPU (s)": f"{sol.cpu_time:.2f}",
                "Vehicles": sol.vehicles_used,
                "Splits": sol.splits,
                "Cost": _fmt(sol.objective),
            })

            if sol.routes:
                plot_solution(
                    inst, sol,
                    title=f"Case Study {inst.name} (HC={hc})",
                    save_path=f"output/cs_{inst.name}_hc{hc}.png",
                    show=False
                )

    _report_table("Table 5: Effect of HC on Solutions", table5_results,
                  "table5_case_study_hc.txt")

    # --- Table 6: Comparison with No-Split ---
    print("\n\n  --- Table 6: Comparison Split vs No-Split (HC=100) ---")
    table6_results = []

    for inst in instances:
        hc = 100
        print(f"\n  Solving {inst.name} (Split vs No-Split)...")

        # With split deliveries
        sol_split = solve_with_cutting_planes(
            inst, H=hc, time_limit=time_limit, verbose=False
        )

        # Without split deliveries
        sol_nosplit = solve_formulation2_no_split(
            inst, H=hc, time_limit=time_limit, verbose=False
        )

        # Cost savings
        if (sol_nosplit.objective < float("inf") and
            sol_split.objective < float("inf") and
            sol_nosplit.objective > 0):
            savings = ((sol_nosplit.objective - sol_split.objective) /
                       sol_nosplit.objective * 100)
        else:
            savings = 0.0

        table6_results.append({
            "Instance": inst.name,
            "n": inst.n,
            "No-Split Vehicles": sol_nosplit.vehicles_used,
            "No-Split Cost": _fmt(sol_nosplit.objective),
            "No-Split GAP": f"{_fmt(sol_nosplit.gap)}%",
            "Split Vehicles": sol_split.vehicles_used,
            "Split Cost": _fmt(sol_split.objective),
            "Split GAP": f"{_fmt(sol_split.gap)}%",
            "Splits": sol_split.splits,
            "Savings %": f"{savings:.2f}%",
        })

    _report_table("Table 6: Split vs No-Split (HC=100)", table6_results,
                  "table6_split_vs_nosplit.txt")

    # Comparison chart
    if table6_results:
        chart_data = {}
        for r in table6_results:
            name = r["Instance"]
            try:
                ns_cost = float(r["No-Split Cost"])
                s_cost = float(r["Split Cost"])
            except (ValueError, TypeError):
                continue
            chart_data[f"{name}\n(No Split)"] = {
                "objective": ns_cost,
                "vehicles": r["No-Split Vehicles"],
                "time": 0,
            }
            chart_data[f"{name}\n(Split)"] = {
                "objective": s_cost,
                "vehicles": r["Split Vehicles"],
                "time": 0,
            }

        if chart_data:
            plot_comparison_bar_chart(
                chart_data,
                title="Case Study: Split vs No-Split Delivery Costs (HC=100)",
                save_path="output/case_study_comparison.png",
                show=False,
            )
            print("\n  [Saved comparison chart: output/case_study_comparison.png]")


def run_hc_impact_analysis(time_limit=180):
    """
    Analyze the impact of hiring cost on solution characteristics.

    Tests a single instance with varying HC values and plots the trends.
    """
    print("\n" + "=" * 70)
    print("  HC IMPACT ANALYSIS")
    print("=" * 70)

    os.makedirs("output", exist_ok=True)

    inst = generate_instance("HC-ANALYSIS", n=10, Q=100, H=0, seed=42)
    print(f"\n  Instance: {inst}")

    hc_values = [0, 25, 50, 75, 100]
    objectives = []
    vehicles = []
    splits = []

    for hc in hc_values:
        print(f"  Solving with HC={hc}...", end=" ", flush=True)
        sol = solve_with_cutting_planes(
            inst, H=hc, time_limit=time_limit, verbose=False
        )
        print(f"Obj={sol.objective:.2f}, Vehicles={sol.vehicles_used}, Splits={sol.splits}")

        objectives.append(sol.objective if sol.objective < float("inf") else 0)
        vehicles.append(sol.vehicles_used)
        splits.append(sol.splits)

    # Plot HC impact
    plot_hc_impact(
        hc_values, objectives, vehicles, splits,
        instance_name=inst.name,
        save_path="output/hc_impact.png",
        show=False,
    )
    print("\n  [Saved HC impact plot: output/hc_impact.png]")


def main():
    """Main experiment runner with menu."""
    print()
    print("+" + "=" * 68 + "+")
    print("|" + " " * 8 + "OVRPSD: Open Vehicle Routing Problem with" + " " * 17 + "|")
    print("|" + " " * 8 + "Split Deliveries - Experiment Runner" + " " * 23 + "|")
    print("|" + " " * 8 + "Based on Ruiz y Ruiz et al. (2022)" + " " * 25 + "|")
    print("+" + "=" * 68 + "+")

    print("""
  Select experiment to run:

    1. Quick Demo (5 customers, ~5 min)
    2. Preliminary Experiments: F1 vs F2 (Section 3, ~10 min)
    3. Cutting-Plane Experiments (Section 5, ~15 min)
    4. Case Study: Pharmaceutical Company (Section 6, ~10 min)
    5. HC Impact Analysis (~5 min)
    6. Run ALL experiments (~40 min)
    """)

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("  Enter choice (1-6): ").strip()

    os.makedirs("output", exist_ok=True)

    start = time.time()

    if choice == "1":
        run_small_demo()
    elif choice == "2":
        run_preliminary_experiments(time_limit=300)
    elif choice == "3":
        run_cutting_plane_experiments(time_limit=300)
    elif choice == "4":
        run_case_study(time_limit=300)
    elif choice == "5":
        run_hc_impact_analysis(time_limit=180)
    elif choice == "6":
        run_small_demo()
        run_preliminary_experiments(time_limit=300)
        run_cutting_plane_experiments(time_limit=300)
        run_case_study(time_limit=300)
        run_hc_impact_analysis(time_limit=180)
    else:
        print(f"  Invalid choice: {choice}")
        return

    elapsed = time.time() - start
    print(f"\n{'='*70}")
    print(f"  Total elapsed time: {elapsed:.2f}s ({elapsed/60:.1f} min)")
    print(f"  Output files saved to: output/")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
