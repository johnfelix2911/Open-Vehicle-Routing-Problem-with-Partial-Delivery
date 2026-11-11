"""
Visualization module for OVRPSD solutions.

Generates route plots and comparison charts for the OVRPSD problem,
matching the visual style of figures in:
  Ruiz y Ruiz et al. (2022) - "Open vehicle routing problem with split deliveries"
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os


# Color palette for routes (up to 10 distinct colors)
ROUTE_COLORS = [
    "#e74c3c",  # Red
    "#3498db",  # Blue
    "#2ecc71",  # Green
    "#f39c12",  # Orange
    "#9b59b6",  # Purple
    "#1abc9c",  # Teal
    "#e67e22",  # Dark Orange
    "#34495e",  # Dark Gray-Blue
    "#e91e63",  # Pink
    "#00bcd4",  # Cyan
]


def plot_instance(instance, title=None, save_path=None, show=True):
    """
    Plot the problem instance (depot and customer locations with demands).

    Args:
        instance: OVRPSDInstance object
        title (str): Plot title
        save_path (str): Path to save the figure
        show (bool): Whether to display the plot
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Plot depot
    ax.scatter(
        [instance.depot[0]], [instance.depot[1]],
        c="#ff6b6b", s=200, marker="s", zorder=5,
        edgecolors="white", linewidths=2, label="Depot"
    )
    ax.annotate(
        "DEPOT", (instance.depot[0], instance.depot[1]),
        textcoords="offset points", xytext=(10, 10),
        fontsize=9, fontweight="bold", color="#ff6b6b"
    )

    # Plot customers
    for i, (cx, cy) in enumerate(instance.customers):
        demand = instance.demands[i]
        # Size proportional to demand
        size = 40 + demand * 2
        ax.scatter(
            [cx], [cy], c="#4ecdc4", s=size, marker="o", zorder=4,
            edgecolors="white", linewidths=1, alpha=0.85
        )
        ax.annotate(
            f"{i + 1}\n(d={demand})", (cx, cy),
            textcoords="offset points", xytext=(8, 5),
            fontsize=7, color="#e0e0e0"
        )

    # Styling
    ax.set_xlabel("X Coordinate", fontsize=12, color="white")
    ax.set_ylabel("Y Coordinate", fontsize=12, color="white")
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#555")
    ax.spines["left"].set_color("#555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=10, facecolor="#1a1a2e", edgecolor="#555",
              labelcolor="white")

    title = title or f"OVRPSD Instance: {instance.name} (n={instance.n}, Q={instance.Q})"
    ax.set_title(title, fontsize=14, fontweight="bold", color="white", pad=15)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    if show:
        plt.show()
    else:
        plt.close()


def plot_solution(instance, solution, title=None, save_path=None, show=True):
    """
    Plot the OVRPSD solution with routes and split delivery indicators.

    Each route is drawn in a different color. Split deliveries are highlighted
    with special markers.

    Args:
        instance: OVRPSDInstance object
        solution: OVRPSDSolution object
        title (str): Plot title
        save_path (str): Path to save the figure
        show (bool): Whether to display the plot
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 9))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # All node coordinates
    all_coords = [instance.depot] + instance.customers

    # Plot routes
    for r_idx, route in enumerate(solution.routes):
        color = ROUTE_COLORS[r_idx % len(ROUTE_COLORS)]

        for i in range(len(route) - 1):
            src = route[i]
            dst = route[i + 1]
            x_coords = [all_coords[src][0], all_coords[dst][0]]
            y_coords = [all_coords[src][1], all_coords[dst][1]]

            ax.plot(
                x_coords, y_coords, color=color, linewidth=2,
                alpha=0.7, zorder=2
            )
            # Arrow at midpoint
            mid_x = (x_coords[0] + x_coords[1]) / 2
            mid_y = (y_coords[0] + y_coords[1]) / 2
            dx = x_coords[1] - x_coords[0]
            dy = y_coords[1] - y_coords[0]
            ax.annotate(
                "", xy=(mid_x + dx * 0.05, mid_y + dy * 0.05),
                xytext=(mid_x - dx * 0.05, mid_y - dy * 0.05),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
                zorder=3
            )

    # Plot depot
    ax.scatter(
        [instance.depot[0]], [instance.depot[1]],
        c="#ff6b6b", s=250, marker="s", zorder=5,
        edgecolors="white", linewidths=2
    )
    ax.annotate(
        "DEPOT", (instance.depot[0], instance.depot[1]),
        textcoords="offset points", xytext=(12, 12),
        fontsize=10, fontweight="bold", color="#ff6b6b"
    )

    # Identify split customers
    vehicles_per_customer = {}
    for (cust, veh), amount in solution.deliveries.items():
        if cust not in vehicles_per_customer:
            vehicles_per_customer[cust] = []
        vehicles_per_customer[cust].append((veh, amount))

    # Plot customers
    for i, (cx, cy) in enumerate(instance.customers):
        cust_id = i + 1
        demand = instance.demands[i]

        is_split = len(vehicles_per_customer.get(cust_id, [])) > 1

        if is_split:
            ax.scatter(
                [cx], [cy], c="#f1c40f", s=120, marker="D", zorder=5,
                edgecolors="white", linewidths=2
            )
            ax.annotate(
                f"{cust_id} (SPLIT)", (cx, cy),
                textcoords="offset points", xytext=(10, 8),
                fontsize=7, fontweight="bold", color="#f1c40f"
            )
        else:
            ax.scatter(
                [cx], [cy], c="#4ecdc4", s=80, marker="o", zorder=5,
                edgecolors="white", linewidths=1
            )
            ax.annotate(
                f"{cust_id}", (cx, cy),
                textcoords="offset points", xytext=(8, 5),
                fontsize=7, color="#e0e0e0"
            )

    # Legend
    legend_elements = [
        mpatches.Patch(color="#ff6b6b", label="Depot"),
        mpatches.Patch(color="#4ecdc4", label="Customer"),
        mpatches.Patch(color="#f1c40f", label="Split Delivery"),
    ]
    for r_idx, route in enumerate(solution.routes):
        legend_elements.append(
            mpatches.Patch(
                color=ROUTE_COLORS[r_idx % len(ROUTE_COLORS)],
                label=f"Route {r_idx + 1}"
            )
        )

    ax.legend(
        handles=legend_elements, fontsize=9,
        facecolor="#1a1a2e", edgecolor="#555", labelcolor="white",
        loc="upper right"
    )

    # Info box
    info_text = (
        f"Vehicles: {solution.vehicles_used}  |  "
        f"Splits: {solution.splits}  |  "
        f"Cost: {solution.objective:.2f}  |  "
        f"Time: {solution.cpu_time:.2f}s"
    )
    ax.text(
        0.5, -0.05, info_text, transform=ax.transAxes,
        fontsize=10, color="#bdc3c7", ha="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#1a1a2e", edgecolor="#555")
    )

    # Styling
    ax.set_xlabel("X Coordinate", fontsize=12, color="white")
    ax.set_ylabel("Y Coordinate", fontsize=12, color="white")
    ax.tick_params(colors="white")
    ax.spines["bottom"].set_color("#555")
    ax.spines["left"].set_color("#555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    title = title or f"OVRPSD Solution: {instance.name}"
    ax.set_title(title, fontsize=14, fontweight="bold", color="white", pad=15)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    if show:
        plt.show()
    else:
        plt.close()


def plot_comparison_bar_chart(results_dict, title=None, save_path=None, show=True):
    """
    Create a grouped bar chart comparing different methods/HC values.

    Args:
        results_dict (dict): {label: {'objective': float, 'vehicles': int, 'splits': int, ...}}
        title (str): Chart title
        save_path (str): Path to save
        show (bool): Whether to display
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.patch.set_facecolor("#1a1a2e")

    labels = list(results_dict.keys())
    objectives = [r["objective"] for r in results_dict.values()]
    vehicles = [r["vehicles"] for r in results_dict.values()]
    times = [r["time"] for r in results_dict.values()]

    bar_colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
                  "#1abc9c", "#e67e22", "#34495e"]

    for ax_idx, (ax, values, ylabel) in enumerate(zip(
        axes,
        [objectives, vehicles, times],
        ["Total Cost", "Vehicles Used", "CPU Time (s)"]
    )):
        ax.set_facecolor("#16213e")
        bars = ax.bar(
            range(len(labels)), values,
            color=bar_colors[:len(labels)],
            edgecolor="white", linewidth=0.5, alpha=0.85
        )
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8, color="white")
        ax.set_ylabel(ylabel, fontsize=10, color="white")
        ax.tick_params(colors="white")
        ax.spines["bottom"].set_color("#555")
        ax.spines["left"].set_color("#555")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Value labels on bars
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:.1f}", ha="center", va="bottom",
                fontsize=8, color="white", fontweight="bold"
            )

    title = title or "OVRPSD Method Comparison"
    fig.suptitle(title, fontsize=14, fontweight="bold", color="white", y=1.02)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    if show:
        plt.show()
    else:
        plt.close()


def plot_hc_impact(hc_values, objectives, vehicles, splits,
                   instance_name="", save_path=None, show=True):
    """
    Plot the impact of hiring cost on objective, fleet size, and splits.

    Args:
        hc_values (list): HC values tested
        objectives (list): Corresponding objective values
        vehicles (list): Number of vehicles used
        splits (list): Number of split deliveries
        instance_name (str): Instance identifier
        save_path (str): Path to save
        show (bool): Whether to display
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.patch.set_facecolor("#1a1a2e")

    plot_data = [
        (objectives, "Total Cost", "#3498db", "o"),
        (vehicles, "Vehicles Used", "#e74c3c", "s"),
        (splits, "Split Deliveries", "#2ecc71", "D"),
    ]

    for ax, (values, ylabel, color, marker) in zip(axes, plot_data):
        ax.set_facecolor("#16213e")
        ax.plot(
            hc_values, values, color=color, marker=marker,
            linewidth=2, markersize=8, markeredgecolor="white",
            markeredgewidth=1.5
        )
        ax.fill_between(hc_values, values, alpha=0.1, color=color)
        ax.set_xlabel("Hiring Cost (HC)", fontsize=10, color="white")
        ax.set_ylabel(ylabel, fontsize=10, color="white")
        ax.tick_params(colors="white")
        ax.spines["bottom"].set_color("#555")
        ax.spines["left"].set_color("#555")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.15, color="white")

    fig.suptitle(
        f"Impact of Hiring Cost — {instance_name}",
        fontsize=14, fontweight="bold", color="white", y=1.02
    )

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    if show:
        plt.show()
    else:
        plt.close()


if __name__ == "__main__":
    from instance_generator import generate_instance
    from ovrpsd_model import solve_formulation2

    print("Visualization Test")
    print("=" * 40)

    # Generate a test instance
    inst = generate_instance("VIZ-TEST", n=8, Q=100, H=0, seed=42)

    # Plot the instance
    os.makedirs("output", exist_ok=True)
    plot_instance(inst, save_path="output/instance_plot.png", show=False)
    print("Saved instance plot to output/instance_plot.png")

    # Solve and plot solution
    sol, _ = solve_formulation2(inst, H=50, time_limit=120, verbose=False)
    if sol.status in ["Optimal", "Feasible"]:
        plot_solution(inst, sol, save_path="output/solution_plot.png", show=False)
        print("Saved solution plot to output/solution_plot.png")
    else:
        print(f"Could not solve: {sol.status}")
