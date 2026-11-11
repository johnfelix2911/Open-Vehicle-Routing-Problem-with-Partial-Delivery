# OVRPSD: Open Vehicle Routing Problem with Split Deliveries

## Overview

This project implements the mathematical formulations, cutting-plane method, and computational experiments from:

> **"Open vehicle routing problem with split deliveries: mathematical formulations and a cutting-plane method"**  
> Ruíz y Ruíz, García-Calvillo, Nucamendi-Guillén (2022)  
> *Operational Research*, Vol. 22, pp. 1017–1037  
> DOI: [10.1007/s12351-020-00590-w](https://doi.org/10.1007/s12351-020-00590-w)

The original research paper is included in this repository as [`vehicle_routing_paper.pdf`](vehicle_routing_paper.pdf).

---

## Problem Description

The **Open Vehicle Routing Problem with Split Deliveries (OVRPSD)** combines two significant extensions of the classical Vehicle Routing Problem (VRP):

1. **Open Routes:** Vehicles depart from a central depot to serve customers but are **not required to return to the depot** after servicing the final customer on their route. This realistically reflects scenarios involving subcontracted third-party logistics (3PL) or rented vehicle fleets where return trips are uncompensated.
2. **Split Deliveries:** A customer's demand can be fulfilled by **multiple visiting vehicles**. Splitting deliveries enables more efficient vehicle packing and can substantially reduce fleet size and total distance, especially when customer demands represent large fractions of vehicle capacity.

### Objective
The objective is to minimize total operational cost:
$$\text{Total Cost} = \sum_{k \in K} (\text{Vehicle Hiring Cost } H \times z^k) + \sum_{k \in K} \sum_{i} \sum_{j} (c_{ij} \times x_{ij}^k)$$

- When hiring cost $H = 0$, the model minimizes pure travel distance.
- When $H > 0$, the model actively trades off longer route lengths to use fewer vehicles.

---

## Project Structure

```
OVRPSD/
├── vehicle_routing_paper.pdf    # Original research paper (Ruíz y Ruíz et al., 2022)
│
├── instance_generator.py        # Problem instance generation, Euclidean metrics & JSON I/O
├── ovrpsd_model.py              # MILP models (Formulation 1, Formulation 2, No-Split baseline)
├── max_flow.py                  # Ford-Fulkerson / Edmonds-Karp max-flow for RCI cut separation
├── cutting_plane.py             # Two-phase cutting-plane algorithm & comparative evaluations
├── visualization.py             # Route network rendering, split delivery indicators & analytics
├── run_experiments.py           # Master CLI runner replicating the paper's experiments
│
├── run_all.bat                  # Automated batch execution script for Windows
├── run_all.sh                   # Automated batch execution script for Linux/macOS
├── requirements.txt             # Python package dependencies
├── README.md                    # Project documentation
│
└── output/                      # Generated experimental results, tables, logs & route plots
    ├── run_all.log              # Complete execution trace of the full benchmark suite
    │
    ├── demo_results.txt         # Small demo results table (F2 vs CP across HC=0, 50, 100)
    ├── table1_formulation1.txt  # Replication of Table 1: Formulation 1 preliminary results
    ├── table2_formulation2.txt  # Replication of Table 2: Formulation 2 preliminary results
    ├── cutting_plane_results.txt# Replication of Tables 7-9: Cutting-plane benchmark results
    ├── table5_case_study_hc.txt # Replication of Table 5: Effect of HC on case study
    ├── table6_split_vs_nosplit.txt # Replication of Table 6: Split vs. No-Split cost savings
    │
    ├── demo_instance.png        # Depot and customer layout for DEMO-5
    ├── demo_solution_hc*.png    # DEMO-5 solved routes for HC=0, HC=50, HC=100
    ├── cp_IES*_hc50.png         # Benchmark route plots (IES10-1, IES15-1, IES20-1 at HC=50)
    ├── cs_CE*_hc*.png           # Case study route plots (CE1 to CE5 at HC=0 and HC=100)
    ├── case_study_comparison.png# Grouped bar chart: Split vs. No-Split costs & fleet sizes
    └── hc_impact.png            # Sensitivity curves: Cost, Vehicles, and Splits vs. HC
```

---

## Setup & Installation

### Requirements
- Python 3.9+
- [PuLP](https://coin-or.github.io/pulp/) (bundled with the COIN-OR CBC solver)
- `numpy`, `matplotlib`, `tabulate`

Install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

---

## Running the Experiments

### 1. Interactive Menu
Launch the CLI runner without arguments to choose an experiment interactively:

```bash
python run_experiments.py
```

### 2. Direct CLI Options
You can execute specific experimental suites directly by passing the menu number:

| Command | Option | Description | Expected Runtime |
| :--- | :---: | :--- | :---: |
| `python run_experiments.py 1` | **Quick Demo** | Solves a 5-customer instance (DEMO-5) under $H \in \{0, 50, 100\}$. Compares Formulation 2 against Cutting Planes and plots routes. | ~1–2 min |
| `python run_experiments.py 2` | **Preliminary Experiments** | Replicates Tables 1 & 2 from Section 3. Compares Formulation 1 vs. Formulation 2 across 6 synthetic instances ($n \in \{20, 25, 30\}$) and $H \in \{0, 50, 100\}$. | ~10–15 min |
| `python run_experiments.py 3` | **Cutting-Plane Experiments** | Replicates Tables 7–9 layout from Section 5. Runs the cutting-plane algorithm across 9 benchmark instances ($n \in \{10, 15, 20\}$) under $H \in \{0, 50, 100\}$ (27 total runs). | ~15–20 min |
| `python run_experiments.py 4` | **Case Study: Pharmaceutical Company** | Replicates Section 6. Evaluates 5 case study instances ($n \in \{13, 14, 21\}$) with $Q=50$. Generates Table 5 (HC impact) and Table 6 (Split vs. No-Split cost savings). | ~10–15 min |
| `python run_experiments.py 5` | **Hiring Cost (HC) Impact Analysis** | Tests sensitivity across $H \in \{0, 25, 50, 75, 100\}$ on a 10-customer instance to observe fleet contraction and delivery splitting. | ~3–5 min |
| `python run_experiments.py 6` | **Run ALL Experiments** | Runs options 1 through 5 sequentially, saving all tables and figures. | ~40–60 min |

### 3. Automated Batch Execution
To run the full suite in the background and capture all logs automatically:

- **Windows:**
  ```cmd
  run_all.bat
  ```
- **Linux / macOS:**
  ```bash
  chmod +x run_all.sh
  ./run_all.sh
  ```

### 4. Running Individual Modules
Each source file contains a self-test block that can be run independently:

```bash
python instance_generator.py     # Generates sample instances and JSON benchmark files
python ovrpsd_model.py           # Solves test instances using Formulation 2 and No-Split
python max_flow.py               # Tests Ford-Fulkerson / Edmonds-Karp min-cut logic
python cutting_plane.py          # Solves a test instance with the cutting-plane method
python visualization.py          # Generates test instance and solution plots
```

---

## File Descriptions

### Core Implementation Files

- **[`instance_generator.py`](instance_generator.py)**
  - Defines the `OVRPSDInstance` class encapsulating customer locations, demands, vehicle capacity $Q$, hiring cost $H$, route distance limit $L$, fleet size $K$, and distance matrices.
  - Generates synthetic benchmark instances following Archetti et al. (2008) with customer demands drawn from $[0.3Q, 0.9Q]$ to promote split deliveries.
  - Generates realistic case study instances mimicking a pharmaceutical distribution network in Guadalajara, Mexico (central depot, radial pharmacies, demands 8–24 pallets, $Q = 50$).
  - Supports JSON serialization via `.save()` and `.load()`.

- **[`ovrpsd_model.py`](ovrpsd_model.py)**
  - Implements the MILP formulations in PuLP:
    - **Formulation 1 (`solve_formulation1`):** Arc-flow model (Section 2.1) with 3-index flow variables $u_{ij}^k$, explicit vehicle activation variables $z^k$, and MTZ subtour elimination.
    - **Formulation 2 (`solve_formulation2`):** Node-flow model (Section 2.2) with cumulative node load variables $u_i^k$. Vehicle hiring cost $H$ is absorbed into depot departure arcs ($c_{0j}' = c_{0j} + H$), eliminating $z^k$. Features flags `relax_integers`, `exclude_mtz`, and `extra_constraints` for cutting-plane integration.
    - **No-Split Formulation (`solve_formulation2_no_split`):** Constrains each customer to be visited exactly once (Section 6.2 baseline).
  - Encapsulates solution data in `OVRPSDSolution` (routes, delivery quantities, splits count, bounds, optimality gap, and CPU time).
  - Handles single-threaded CBC solver execution and log parsing via `_solve_with_cbc()`.

- **[`max_flow.py`](max_flow.py)**
  - Implements polynomial-time separation of **Rounded Capacity Inequalities (RCIs)** (Eq. 33 in the paper).
  - `MaxFlowGraph`: Implements Ford-Fulkerson with Edmonds-Karp BFS ($O(V \cdot E^2)$) using skew-symmetric residual capacities.
  - `build_support_graph()`: Constructs the fractional support network $G^* = (V, A^*)$ where arc capacities equal aggregated fractional flows $\sum_k x_{ij}^{*k}$.
  - `find_violated_capacity_cuts()`: Uses min-cut evaluation for each customer sink $j$ to identify customer subsets $D$ where cut capacity is strictly less than $\lceil d(D) / Q \rceil$.

- **[`cutting_plane.py`](cutting_plane.py)**
  - Implements the two-phase cutting-plane algorithm from Section 4:
    - **Phase 1:** Iteratively solves the LP relaxation of Formulation 2 without MTZ constraints, extracts fractional solutions, separates violated RCIs via `max_flow.py`, and adds them as cuts.
    - **Phase 2:** Restores integrality, enables MTZ subtour constraints (Eq. 28), injects all accumulated cuts, and solves the full MILP using CBC branch-and-bound.
  - `compare_methods()`: Conducts side-by-side benchmarking of plain Formulation 2 versus the cutting-plane method.

- **[`visualization.py`](visualization.py)**
  - Generates high-resolution figures matching the paper's visual style:
    - `plot_instance()`: Depot (square) and customer locations (circles scaled by demand).
    - `plot_solution()`: Color-coded vehicle routes with directional arrows, open route terminations, and split customers highlighted as yellow diamonds.
    - `plot_hc_impact()`: 3-panel sensitivity plots showing Total Cost, Fleet Size, and Splits vs. Hiring Cost.
    - `plot_comparison_bar_chart()`: Grouped bar charts comparing methods or policies (Split vs. No-Split).

- **[`run_experiments.py`](run_experiments.py)**
  - Main driver program providing the interactive menu and automated test runners.
  - Formats results using `tabulate` and exports tables to the `output/` folder.

- **[`run_all.bat`](run_all.bat) / [`run_all.sh`](run_all.sh)**
  - Automation scripts executing Option 6 headlessly and redirecting output to `output/run_all.log`.

---

## Results & Output Files

All experiment outputs are saved in the [`output/`](output/) directory:

### Text Tables & Numerical Results
- **[`demo_results.txt`](output/demo_results.txt):** Comparison of Formulation 2 vs. Cutting Planes on DEMO-5 ($n=5$) across $H \in \{0, 50, 100\}$. Demonstrates that the cutting-plane method closes the optimality gap in ~1 second compared to 120 seconds for plain F2.
- **[`table1_formulation1.txt`](output/table1_formulation1.txt):** Replication of Table 1 from the paper. Formulation 1 tested on G20, G25, and G30 instances under $H \in \{0, 50, 100\}$. Reports Initial LB, UB, LB, GAP%, and CPU time.
- **[`table2_formulation2.txt`](output/table2_formulation2.txt):** Replication of Table 2 from the paper. Formulation 2 tested on the same instances. Demonstrates that without cutting planes, plain F2 has weaker LP bounds and stalls when using CBC.
- **[`cutting_plane_results.txt`](output/cutting_plane_results.txt):** Replication of the layout of Tables 7–9 from the paper. Benchmark instances IES10, IES15, and IES20 solved via cutting planes across $H \in \{0, 50, 100\}$ (reporting fleet size $k$, cuts added, split deliveries, bounds, and GAP%).
- **[`table5_case_study_hc.txt`](output/table5_case_study_hc.txt):** Replication of Table 5 from the paper. Evaluates case study instances CE1–CE5 ($n \in \{13, 14, 21\}$) under $H=0$ vs. $H=100$. Shows fleet contraction as hiring cost increases.
- **[`table6_split_vs_nosplit.txt`](output/table6_split_vs_nosplit.txt):** Replication of Table 6 from the paper. Compares Split vs. No-Split delivery policies at $H=100$, demonstrating **9% to 27% cost savings** achievable by allowing split deliveries.
- **[`run_all.log`](output/run_all.log):** Complete raw console log from running all benchmark suites.

### Visualizations & Plots
- **Demo Visuals:**
  - [`demo_instance.png`](output/demo_instance.png): Depot and customer coordinates for the 5-customer instance.
  - [`demo_solution_hc0.png`](output/demo_solution_hc0.png): Optimal routes for $H=0$ (4 vehicles, 0 splits; pure distance minimization).
  - [`demo_solution_hc50.png`](output/demo_solution_hc50.png): Optimal routes for $H=50$ (3 vehicles, 1 split at customer 5).
  - [`demo_solution_hc100.png`](output/demo_solution_hc100.png): Optimal routes for $H=100$ (3 vehicles, 1 split at customer 5).
- **Benchmark Route Visuals:**
  - [`cp_IES10-1_hc50.png`](output/cp_IES10-1_hc50.png), [`cp_IES15-1_hc50.png`](output/cp_IES15-1_hc50.png), [`cp_IES20-1_hc50.png`](output/cp_IES20-1_hc50.png): Cutting-plane solutions showing open routes and customer delivery splits.
- **Case Study Visuals:**
  - [`cs_CE1_hc0.png`](output/cs_CE1_hc0.png) to [`cs_CE5_hc100.png`](output/cs_CE5_hc100.png): Route network maps for pharmaceutical distribution instances.
  - [`case_study_comparison.png`](output/case_study_comparison.png): Grouped bar chart comparing total costs and vehicle counts between Split and No-Split deliveries.
  - [`hc_impact.png`](output/hc_impact.png): Hiring cost sensitivity curve illustrating cost growth, vehicle reduction, and delivery splits.

---

## Notes on the Implementation vs. the Paper

1. **Open-Source Solver (PuLP with CBC):**
   - The paper solved models using commercial **IBM ILOG CPLEX 12.6**. This implementation uses **COIN-OR CBC** via PuLP.
   - CBC is weaker than CPLEX at finding integer feasible points for large root-gap models. Consequently, plain Formulation 2 often stalls on instances with $n \ge 20$, whereas the cutting-plane method tightens the root node and allows CBC to find high-quality solutions quickly.
   - Absolute CPU times are not directly comparable to the paper's CPLEX timings, but relative performance trends (Cutting Planes $\gg$ Formulation 2) remain fully consistent.

2. **Single-Threaded Execution Workaround:**
   - On Windows, the PuLP-bundled CBC binary can deadlock during root-node cut generation when the `threads` option is enabled. `_solve_with_cbc()` enforces single-threaded execution to guarantee stable completion.

3. **Log-Based Bound Parsing:**
   - PuLP does not natively expose internal continuous lower bounds from CBC. Each solve pipes output to a temporary log file, extracting `Continuous objective value is` as the Initial LP relaxation bound and `Lower bound:` as the final lower bound.
   - A run terminated by the time limit with an incumbent solution is categorized as `Feasible` rather than `Optimal`.

4. **Optimality Gap Definition:**
   - The optimality gap is calculated strictly following the paper's formula:
     $$\text{GAP} = \frac{\text{UB} - \text{LB}}{\text{LB}} \times 100\%$$

5. **Formulation 1 Terminal Node Correction:**
   - In Equation (14) of the paper, the terminal-node variable $s_j^k$ is indexed by vehicle $k$. If formulated with a single unindexed variable $s_j$ in the per-vehicle flow balance (Eq. 6), every vehicle would be forced to terminate at the same customer, rendering the problem infeasible for $|K| > 1$. The implementation uses $s_{j,k}$ with $\sum_k s_{j,k} \le 1$ to preserve the "no two routes end at the same node" policy.

6. **Formulation 1 Demand Flow Balance (Eq. 10):**
   - Equation (10) sums incoming flow $u_{ji}^k$ over customer nodes only ($j \in V^+$), ensuring the depot departure arc $u_{0i}^k$ (which is an explicit separate term) is not counted twice.
