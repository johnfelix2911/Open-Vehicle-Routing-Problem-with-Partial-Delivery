"""
Refine connector labels in architecture_diagram.png to eliminate label overlap.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

doc_assets = r"x:\CODING\OVRPSD\output\doc_assets"

def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(16, 10), dpi=220)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")
    fig.patch.set_facecolor("#ffffff")

    # Header
    ax.text(8.0, 9.5, "OVRPSD System Architecture & Component Interaction Flow",
            ha="center", va="center", fontsize=18, fontweight="bold", color="#0f172a")
    ax.text(8.0, 9.1, "Data models, mathematical formulations, separation algorithms, experiment runners, and reporting",
            ha="center", va="center", fontsize=10.5, style="italic", color="#475569")

    def draw_card(x, y, w, h, bg_color, header_color, title, subtitle, items):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                                      facecolor=bg_color, edgecolor=header_color, linewidth=1.6)
        ax.add_patch(rect)
        header_rect = patches.FancyBboxPatch((x, y + h - 0.75), w, 0.75, boxstyle="round,pad=0.12",
                                            facecolor=header_color, edgecolor=header_color, linewidth=1.0)
        ax.add_patch(header_rect)
        ax.text(x + w/2, y + h - 0.38, title, ha="center", va="center",
                fontsize=11.5, fontweight="bold", color="#ffffff")
        ax.text(x + w/2, y + h - 1.0, subtitle, ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=header_color)
        for idx, item in enumerate(items):
            ax.text(x + 0.25, y + h - 1.4 - idx*0.35, f"- {item}",
                    ha="left", va="center", fontsize=8.2, color="#1e293b")

    # Card 1: run_experiments.py
    draw_card(0.8, 5.2, 4.2, 3.4, "#eff6ff", "#1d4ed8",
              "run_experiments.py", "CLI Experiment Runner & Menu",
              ["Interactive CLI menu (options 1 to 6)",
               "Orchestrates benchmarks & case study",
               "Manages solver parameters & limits",
               "Collects metrics & exports formatted tables",
               "Coordinates route visualization"])

    # Card 2: run_all.bat / run_all.sh
    draw_card(0.8, 1.2, 4.2, 3.2, "#f1f5f9", "#475569",
              "run_all.bat / run_all.sh", "Automated Batch Runners",
              ["Headless pipeline execution: option 6",
               "Captures combined log to output/run_all.log",
               "Validates environment & requirements.txt",
               "Runs 40+ minute full benchmark suite",
               "Ensures repeatable computational benchmarking"])

    # Card 3: instance_generator.py
    draw_card(5.9, 5.2, 4.3, 3.4, "#f0fdf4", "#047857",
              "instance_generator.py", "Instance Data Structures & I/O",
              ["OVRPSDInstance: Core problem data model",
               "generate_instance(): Synthetic instances",
               "generate_case_study_instance(): Pharma CE1-5",
               "compute_euclidean_distance_matrix()",
               "JSON serialization (.save() & .load())"])

    # Card 4: ovrpsd_model.py
    draw_card(5.9, 1.2, 4.3, 3.2, "#eff6ff", "#0284c7",
              "ovrpsd_model.py", "Exact MILP Formulations (PuLP)",
              ["solve_formulation1(): Arc-flow u_ij^k (Sec 2.1)",
               "solve_formulation2(): Node-flow u_i^k (Sec 2.2)",
               "solve_formulation2_no_split(): Baseline model",
               "_solve_with_cbc(): Single-thread CBC solve",
               "OVRPSDSolution: Routes, bounds, status"])

    # Card 5: cutting_plane.py
    draw_card(11.0, 5.2, 4.2, 3.4, "#fffbeb", "#d97706",
              "cutting_plane.py", "Cutting-Plane Method Controller",
              ["solve_with_cutting_planes(): 2-phase framework",
               "Phase 1: Iterative LP relaxation (no MTZ)",
               "Extracts fractional x* for separation",
               "Phase 2: Full MILP with MTZ + added cuts",
               "compare_methods(): F2 vs CP benchmark"])

    # Card 6: max_flow.py
    draw_card(11.0, 1.2, 4.2, 3.2, "#faf5ff", "#7c3aed",
              "max_flow.py", "RCI Cut Separation Engine",
              ["MaxFlowGraph: Ford-Fulkerson w/ Edmonds-Karp",
               "build_support_graph(): Capacities = sum_k x_ij",
               "find_violated_capacity_cuts(): Min-cut check",
               "Separates Eq. (33) rounded capacity cuts",
               "Identifies customer subset D where flow < ceil(d(D)/Q)"])

    def draw_path(pts, label="", color="#334155", lpos=(0, 0)):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=color, lw=1.6, linestyle="-", zorder=2)
        ax.annotate("", xy=pts[-1], xytext=pts[-2],
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.6, shrinkA=0, shrinkB=3), zorder=2)
        if label:
            lx, ly = lpos
            ax.text(lx, ly, label, ha="center", va="center",
                    fontsize=8.0, fontweight="bold", color=color,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffffff", edgecolor=color, lw=0.8, alpha=0.98), zorder=3)

    # 1. run_all -> run_experiments
    draw_path([(2.9, 4.4), (2.9, 5.2)], "Executes script", "#475569", (2.9, 4.8))

    # 2. run_experiments -> instance_generator
    draw_path([(5.0, 7.5), (5.9, 7.5)], "Generates instances", "#047857", (5.45, 7.75))

    # 3. instance_generator -> ovrpsd_model
    draw_path([(8.0, 5.2), (8.0, 4.4)], "OVRPSDInstance", "#047857", (8.0, 4.8))

    # 4. run_experiments -> ovrpsd_model
    draw_path([(5.0, 5.8), (5.5, 5.8), (5.5, 3.2), (5.9, 3.2)], "Direct solve", "#0284c7", (5.5, 4.5))

    # 5. run_experiments -> cutting_plane (top curve)
    draw_path([(2.9, 8.6), (2.9, 8.85), (13.1, 8.85), (13.1, 8.6)], "Invokes Cutting-Plane", "#d97706", (8.0, 8.85))

    # 6. cutting_plane -> instance_generator
    draw_path([(11.0, 7.5), (10.2, 7.5)], "Instance data", "#047857", (10.6, 7.75))

    # 7. cutting_plane -> ovrpsd_model
    draw_path([(11.0, 6.0), (10.5, 6.0), (10.5, 3.2), (10.2, 3.2)], "LP relax & MILP", "#0284c7", (10.5, 4.6))

    # 8. cutting_plane -> max_flow (staggered right)
    draw_path([(13.8, 5.2), (13.8, 4.4)], "Passes x* to separate", "#7c3aed", (13.8, 4.8))

    # 9. max_flow -> cutting_plane (staggered left)
    draw_path([(11.6, 4.4), (11.6, 5.2)], "Returns cuts (D, req)", "#7c3aed", (11.6, 4.8))

    # Bottom Banner: visualization.py & output/
    viz_rect = patches.FancyBboxPatch((0.8, 0.08), 14.4, 0.85, boxstyle="round,pad=0.1",
                                     facecolor="#ecfdf5", edgecolor="#059669", linewidth=1.5)
    ax.add_patch(viz_rect)
    ax.text(8.0, 0.60, "visualization.py & output/ Directory",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color="#065f46")
    ax.text(8.0, 0.28, "plot_instance() | plot_solution() (color-coded open routes, split markers) | plot_hc_impact() | plot_comparison_bar_chart() -> Saves PNGs & TXT tables",
            ha="center", va="center", fontsize=8.2, color="#047857")

    plt.tight_layout()
    path = os.path.join(doc_assets, "architecture_diagram.png")
    plt.savefig(path, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print("Perfect architecture_diagram.png regenerated.")

if __name__ == "__main__":
    generate_architecture_diagram()
