"""
Script to generate the comprehensive OVRPSD Codebase Architecture & Implementation Guide PDF.
"""
import os
import sys
from fpdf import FPDF

PDF_OUTPUT_PATH = r"x:\CODING\OVRPSD\OVRPSD_Codebase_Architecture_and_Implementation_Guide.pdf"
DOC_ASSETS_DIR = r"x:\CODING\OVRPSD\output\doc_assets"
OUTPUT_DIR = r"x:\CODING\OVRPSD\output"

class CodebaseGuidePDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(18, 18, 18)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, "OVRPSD Codebase Architecture & Technical Implementation Guide", align="L")
            self.cell(0, 8, f"Page {self.page_no()}", align="R")
            self.ln(10)
            self.set_draw_color(226, 232, 240)
            self.set_line_width(0.3)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-14)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 6, "Ruiz y Ruiz et al. (2022) Implementation  |  Open Vehicle Routing Problem with Split Deliveries", align="C")

    def chapter_title(self, title, level=1):
        if level == 1:
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(15, 23, 42)
            self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(30, 64, 175)
            self.set_line_width(0.7)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font("Helvetica", "B", 12.5)
            self.set_text_color(29, 78, 216)
            self.cell(0, 7.5, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        elif level == 3:
            self.set_font("Helvetica", "B", 10.5)
            self.set_text_color(51, 65, 85)
            self.cell(0, 6.5, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1.5)

    def body_p(self, text):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.0, text)
        self.ln(1.5)

    def bullet(self, text, bold_prefix=""):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 41, 59)
        x = self.get_x()
        self.cell(4, 5.0, "-")
        if bold_prefix:
            self.set_font("Helvetica", "B", 9.5)
            self.write(5.0, bold_prefix + " ")
            self.set_font("Helvetica", "", 9.5)
        self.multi_cell(0, 5.0, text)
        self.ln(1.0)

    def key_val(self, key, value):
        self.set_font("Helvetica", "B", 9.5)
        self.set_text_color(30, 41, 59)
        kw = self.get_string_width(key + ": ") + 1
        self.cell(kw, 5.0, key + ": ")
        self.set_font("Helvetica", "", 9.5)
        self.multi_cell(0, 5.0, value)
        self.ln(0.8)

    def callout_box(self, text, title=None, kind="info"):
        colors = {
            "info": (240, 249, 255, 3, 105, 161, 2, 132, 199),      # sky
            "tip": (240, 253, 244, 21, 128, 61, 22, 163, 74),       # emerald
            "warn": (255, 251, 235, 180, 83, 9, 217, 119, 6),       # amber
            "note": (248, 250, 252, 71, 85, 105, 148, 163, 184),    # slate
        }
        bg_r, bg_g, bg_b, txt_r, txt_g, txt_b, bdr_r, bdr_g, bdr_b = colors.get(kind, colors["info"])
        w = self.w - self.l_margin - self.r_margin

        # Height check
        self.set_font("Helvetica", "", 8.8)
        content_to_measure = (f"{title}\n" if title else "") + text
        h_est = self.multi_cell(w - 8, 4.5, content_to_measure, dry_run=True, output="HEIGHT") + 8
        if self.get_y() + h_est > self.h - self.b_margin:
            self.add_page()

        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(bg_r, bg_g, bg_b)
        self.set_draw_color(bdr_r, bdr_g, bdr_b)
        self.set_line_width(0.6)
        self.rect(x, y, w, h_est, style="DF")

        # Left accent stripe
        self.set_fill_color(txt_r, txt_g, txt_b)
        self.rect(x, y, 2.5, h_est, style="F")

        self.set_xy(x + 5, y + 4)
        if title:
            self.set_font("Helvetica", "B", 9.2)
            self.set_text_color(txt_r, txt_g, txt_b)
            self.cell(0, 4.5, title, new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 5)
        self.set_font("Helvetica", "", 8.8)
        self.set_text_color(30, 41, 59)
        self.multi_cell(w - 8, 4.3, text)
        self.set_y(y + h_est + 3)

    def code_box(self, code_snippet, title=None):
        w = self.w - self.l_margin - self.r_margin
        lines = code_snippet.strip().split("\n")
        line_height = 4.0
        h_box = len(lines) * line_height + (8 if title else 6)

        if self.get_y() + h_box > self.h - self.b_margin:
            self.add_page()

        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.4)
        self.rect(x, y, w, h_box, style="DF")

        curr_y = y + 3
        if title:
            self.set_xy(x + 4, curr_y)
            self.set_font("Helvetica", "B", 8.2)
            self.set_text_color(71, 85, 105)
            self.cell(0, 3.5, f"// {title}", new_x="LMARGIN", new_y="NEXT")
            curr_y += 4.5

        self.set_font("Courier", "", 8.0)
        self.set_text_color(15, 23, 42)
        for line in lines:
            self.set_xy(x + 4, curr_y)
            self.cell(0, line_height, line)
            curr_y += line_height

        self.set_y(y + h_box + 3)

    def add_image_card(self, path, w=160, caption=None):
        if not os.path.exists(path):
            self.body_p(f"[Image file not found: {os.path.basename(path)}]")
            return
        # Calculate aspect ratio
        from PIL import Image
        with Image.open(path) as img:
            iw, ih = img.size
            aspect = ih / iw
        img_h = w * aspect

        if self.get_y() + img_h + 12 > self.h - self.b_margin:
            self.add_page()

        x = (self.w - w) / 2
        y = self.get_y()

        # Image border & subtle shadow
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.4)
        self.rect(x - 0.5, y - 0.5, w + 1.0, img_h + 1.0)
        self.image(path, x=x, y=y, w=w, h=img_h)
        self.set_y(y + img_h + 2)

        if caption:
            self.set_font("Helvetica", "I", 8.0)
            self.set_text_color(100, 116, 139)
            self.cell(0, 4.5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(2.5)

    def draw_table(self, headers, rows, col_widths=None):
        available_w = self.w - self.l_margin - self.r_margin
        if col_widths is None:
            col_widths = [available_w / len(headers)] * len(headers)

        header_h = 7.0
        row_h = 5.8

        if self.get_y() + header_h + row_h > self.h - self.b_margin:
            self.add_page()

        # Header
        self.set_font("Helvetica", "B", 8.2)
        self.set_fill_color(30, 64, 175)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], header_h, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 7.8)
        self.set_text_color(15, 23, 42)
        fill = False
        for row in rows:
            if self.get_y() + row_h > self.h - self.b_margin:
                self.add_page()
                # Repeat header
                self.set_font("Helvetica", "B", 8.2)
                self.set_fill_color(30, 64, 175)
                self.set_text_color(255, 255, 255)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], header_h, h, border=1, fill=True, align="C")
                self.ln()
                self.set_font("Helvetica", "", 7.8)
                self.set_text_color(15, 23, 42)

            self.set_fill_color(248, 250, 252 if fill else 255)
            for i, cell_val in enumerate(row):
                align = "C" if i == 0 or len(str(cell_val)) < 8 else "L"
                self.cell(col_widths[i], row_h, str(cell_val), border=1, fill=True, align=align)
            self.ln()
            fill = not fill
        self.ln(3)


def build_codebase_guide():
    pdf = CodebaseGuidePDF()
    pdf.set_title("OVRPSD Codebase Architecture & Technical Implementation Guide")
    pdf.set_author("OVRPSD Technical Documentation Engine")

    # ================= PAGE 1: TITLE / COVER PAGE =================
    pdf.add_page()
    pdf.ln(25)

    # Decorative header tag
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(29, 78, 216)
    pdf.cell(0, 6, "COMPREHENSIVE CODEBASE COMPANION & TECHNICAL ARCHITECTURE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Main Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 11, "Open Vehicle Routing Problem", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 11, "with Split Deliveries (OVRPSD)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Subtitle
    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 7, "A File-by-File Technical Guide to the Implementation & Workflows", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # Decorative line
    pdf.set_draw_color(30, 64, 175)
    pdf.set_line_width(1.0)
    pdf.line(40, pdf.get_y(), pdf.w - 40, pdf.get_y())
    pdf.ln(10)

    # Research paper attribution card
    pdf.callout_box(
        "Based on the seminal research paper:\n"
        "\"Open vehicle routing problem with split deliveries: mathematical formulations and a cutting-plane method\"\n"
        "Authors: Ruíz y Ruíz, García-Calvillo, Nucamendi-Guillén (2022)\n"
        "Journal: Operational Research, Vol. 22, pp. 1017-1037 (Springer)",
        title="ACADEMIC FOUNDATION",
        kind="info"
    )
    pdf.ln(4)

    pdf.body_p(
        "This document is an exhaustive engineering and algorithmic manual designed to help researchers, students, "
        "and developers understand every single file in the OVRPSD implementation (excluding the PDF documents). "
        "It details what each file does, the data structures and algorithms it encapsulates, how each module connects "
        "and communicates with others, and how the end-to-end experimental and visualization pipeline operates."
    )
    pdf.ln(4)

    # Key modules summary pill list
    pdf.key_val("Modules Covered", "instance_generator.py, ovrpsd_model.py, max_flow.py, cutting_plane.py, visualization.py, run_experiments.py, run_all.bat/sh, requirements.txt, README.md, and output/ directory.")
    pdf.key_val("Primary Solver", "COIN-OR CBC via PuLP 2.8+ (Linear & Mixed Integer Programming)")
    pdf.key_val("Core Methods", "Exact MILP (Formulations 1 & 2), Ford-Fulkerson / Edmonds-Karp Max-Flow Min-Cut, Cutting-Plane Separation of Rounded Capacity Inequalities (RCIs)")

    # ================= PAGE 2: TABLE OF CONTENTS & QUICK FILE MATRIX =================
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    toc_items = [
        "1. Executive Summary & Problem Context",
        "2. Complete File Inventory & Quick Reference Matrix",
        "3. System Architecture & Inter-Module Interaction Flows",
        "4. Deep-Dive: instance_generator.py (Data Models & Benchmarks)",
        "5. Deep-Dive: ovrpsd_model.py (Formulation 1, Formulation 2 & No-Split)",
        "6. Deep-Dive: max_flow.py (Edmonds-Karp Max-Flow & RCI Cut Separation)",
        "7. Deep-Dive: cutting_plane.py (Two-Phase Cutting-Plane Optimization)",
        "8. Deep-Dive: visualization.py (Route Rendering & Metric Analytics)",
        "9. Deep-Dive: run_experiments.py & Automation Scripts (CLI & Batch)",
        "10. Output Directory Anatomy (Generated Plots, Tables & Logs)",
        "11. End-to-End Workflow Scenarios & Dataflow Walkthroughs",
        "12. Technical Synthesis & Architectural Patterns",
    ]
    for item in toc_items:
        pdf.bullet(item)
    pdf.ln(4)

    pdf.chapter_title("1. Executive Summary & Problem Context")
    pdf.body_p(
        "The Open Vehicle Routing Problem with Split Deliveries (OVRPSD) extends the classical Vehicle Routing Problem "
        "by combining two realistic logistics features:"
    )
    pdf.bullet("Open Routes: Vehicles originate at a central depot to make deliveries but do not return to the depot after visiting the final customer on their route. This models outsourced freight carriers, rented vehicle fleets, or third-party logistics where return trips are not compensated.", "1. Open Routing Structure -")
    pdf.bullet("Split Deliveries: A customer's pallet or parcel demand may exceed vehicle capacity or may be split across multiple visiting vehicles if doing so reduces overall fleet costs or travel distance.", "2. Demand Splitting -")
    pdf.bullet("Bi-Objective Cost Trade-off: The objective function minimizes Total Cost = (Vehicle Hiring Cost * Vehicles Used) + Total Distance Traveled. When hiring cost HC is zero, routes minimize pure Euclidean travel; when HC is high, vehicles are packed more tightly to reduce fleet count.", "3. Cost Model -")
    pdf.ln(2)

    pdf.chapter_title("2. Complete File Inventory & Quick Reference Matrix")
    pdf.body_p("The table below summarizes all non-PDF files in the codebase, their functional category, lines of code, and communication peers:")

    headers = ["File Name", "Role / Category", "Key Classes / Functions", "Direct Imports", "Imported By"]
    widths = [36, 32, 42, 32, 32]
    matrix_rows = [
        ["instance_generator.py", "Data & Benchmarks", "OVRPSDInstance, generate_instance, generate_case_study", "numpy, json, math", "ovrpsd_model, cutting_plane, run_exp"],
        ["ovrpsd_model.py", "MILP Formulations", "OVRPSDSolution, solve_formulation1, solve_formulation2", "pulp, instance_gen", "cutting_plane, run_exp"],
        ["max_flow.py", "RCI Cut Separation", "MaxFlowGraph, build_support_graph, find_violated_cuts", "collections, math", "cutting_plane"],
        ["cutting_plane.py", "Two-Phase Optimizer", "solve_with_cutting_planes, compare_methods", "pulp, ovrpsd, max_flow", "run_experiments"],
        ["visualization.py", "Visual Analytics", "plot_instance, plot_solution, plot_hc_impact", "matplotlib, numpy", "run_experiments"],
        ["run_experiments.py", "CLI Runner & Suites", "run_small_demo, run_case_study, main", "tabulate, all modules", "run_all.bat, run_all.sh"],
        ["run_all.bat / .sh", "Batch Automation", "Invokes 'run_experiments.py 6' > run_all.log", "OS Shell / Python", "Terminal / User"],
        ["requirements.txt", "Dependencies", "pulp, numpy, matplotlib, tabulate", "pip", "Setup / Developers"],
        ["README.md", "Documentation", "Project overview, setup, formulation notes", "Markdown", "Users / Readers"],
    ]
    pdf.draw_table(headers, matrix_rows, widths)

    # ================= PAGE 3: SYSTEM ARCHITECTURE =================
    pdf.add_page()
    pdf.chapter_title("3. System Architecture & Inter-Module Interaction Flows")
    pdf.body_p(
        "The OVRPSD codebase is structured in a clear four-tier modular architecture with clean separation of concerns. "
        "No circular dependencies exist. The diagram below illustrates how each file communicates across architectural boundaries:"
    )
    pdf.add_image_card(os.path.join(DOC_ASSETS_DIR, "architecture_diagram.png"), w=170,
                       caption="Figure 3.1: OVRPSD System Architecture & Component Interaction Flow")

    pdf.body_p(
        "The architecture operates through three primary interfaces:"
    )
    pdf.bullet("instance_generator.py provides immutable OVRPSDInstance objects containing the coordinate coordinates, demand vector, vehicle capacity Q, maximum route length L, and cost matrix.", "Data Transfer: ")
    pdf.bullet("ovrpsd_model.py exposes pure solving functions returning standardized OVRPSDSolution objects containing status, objective, route sequences, customer delivery shares, lower/upper bounds, and MIP gap.", "Solver Interface: ")
    pdf.bullet("cutting_plane.py acts as a higher-level orchestrator that coordinates ovrpsd_model (for LP relaxation and full MILP) with max_flow (which inspects fractional solutions to separate violated cuts).", "Separation Loop: ")

    # ================= PAGE 4: DEPENDENCY HIERARCHY =================
    pdf.add_page()
    pdf.chapter_title("Module Layering & Dependency Hierarchy", level=2)
    pdf.body_p(
        "Understanding which file imports which is critical for debugging, modifying, or extending the solver. "
        "Figure 3.2 displays the strict tiered hierarchy from entry scripts down to mathematical algorithms:"
    )
    pdf.add_image_card(os.path.join(DOC_ASSETS_DIR, "file_dependency_graph.png"), w=155,
                       caption="Figure 3.2: OVRPSD Layered Dependency Hierarchy")

    pdf.body_p("Notice the distinct architectural tiers:")
    pdf.bullet("run_experiments.py and batch scripts run_all.bat / run_all.sh. These files parse user inputs, handle command line arguments, and coordinate experimental batches.", "Application Layer: ")
    pdf.bullet("cutting_plane.py and visualization.py. cutting_plane controls the algorithmic separation loop, while visualization renders graphical output for completed runs.", "Algorithm & Presentation Layer: ")
    pdf.bullet("ovrpsd_model.py. Formulates mathematical optimization models using PuLP and interfaces with COIN-OR CBC.", "Mathematical Formulation Layer: ")
    pdf.bullet("instance_generator.py and max_flow.py. Independent, self-contained mathematical and data utility modules with zero coupling to other project files.", "Foundational Layer: ")

    # ================= PAGE 5: INSTANCE_GENERATOR.PY =================
    pdf.add_page()
    pdf.chapter_title("4. Deep-Dive: instance_generator.py")
    pdf.body_p(
        "instance_generator.py is the foundational data file. It defines the formal representation of an OVRPSD problem "
        "instance and provides generators for both synthetic benchmark sets and realistic case study problems."
    )

    pdf.chapter_title("The OVRPSDInstance Data Structure", level=2)
    pdf.body_p(
        "The class OVRPSDInstance encapsulates all geometric, operational, and fleet parameters of a vehicle routing instance:"
    )
    pdf.key_val("name (str)", "Unique alphanumeric identifier (e.g. 'IES10-1', 'G20a', 'CE1', 'DEMO-5')")
    pdf.key_val("n (int)", "Number of customer nodes (excluding the depot). Node 0 is always the depot; nodes 1..n are customers.")
    pdf.key_val("depot (tuple)", "(x, y) coordinates of the central depot, conventionally placed at (50.0, 50.0).")
    pdf.key_val("customers (list)", "List of n tuples [(x1, y1), ..., (xn, yn)] specifying customer locations.")
    pdf.key_val("demands (list)", "Integer demands for each customer: demands[i-1] represents demand d_i for customer node i.")
    pdf.key_val("Q (int)", "Vehicle payload capacity (e.g. 100 pallets for benchmark instances; 50 for case study).")
    pdf.key_val("H (float)", "Hiring cost per vehicle used (can be overridden during solver calls).")
    pdf.key_val("L (float)", "Maximum allowable travel distance for any individual vehicle route.")
    pdf.key_val("K (int)", "Upper bound on available fleet size (derived as ceil(total_demand / Q) + slack).")
    pdf.key_val("cost_matrix (ndarray)", "Symmetric (n+1) x (n+1) Euclidean distance matrix rounded to 2 decimal places.")

    pdf.chapter_title("Key Functions in instance_generator.py", level=2)

    pdf.bullet(
        "Computes Euclidean distance d = sqrt((x_i - x_j)^2 + (y_i - y_j)^2) between all node pairs including the depot (node 0) and customers 1..n. Returns an (n+1) x (n+1) symmetric numpy array.",
        "compute_euclidean_distance_matrix(depot, customers) -> np.ndarray:"
    )

    pdf.bullet(
        "Generates synthetic instances following the criteria of Archetti et al. (2008). Customers are placed uniformly in a 100x100 grid. Demands are drawn uniformly from [0.3*Q, 0.9*Q], which ensures customers require large fractions of vehicle capacity, thereby creating strong economic incentives for delivery splitting. L defaults to 3 times the maximum depot-to-customer distance.",
        "generate_instance(name, n, Q=100, H=0, L=None, seed=None) -> OVRPSDInstance:"
    )

    pdf.bullet(
        "Constructs instances specifically mimicking the metropolitan distribution network of a pharmaceutical distributor in Guadalajara, Mexico (Section 6 of the paper). Depot is placed at city center (50, 50); pharmacies are distributed radially at distances 10-45 km. Customer demands range from 8 to 24 pallets, with closer customers having higher volume. Vehicle capacity is set to Q = 50.",
        "generate_case_study_instance(name, n, seed=None) -> OVRPSDInstance:"
    )

    pdf.bullet(
        "Batch generator creating the complete 35-instance benchmark library: 10 instances each for n=20, n=25, and n=30 ('IES20-1' to 'IES30-10'), plus 5 case study instances ('CE1' to 'CE5'). Automatically serializes each instance as a JSON file.",
        "generate_benchmark_instances(output_dir='instances') -> list[OVRPSDInstance]:"
    )

    pdf.code_box(
        "# How to generate and inspect an instance:\n"
        "inst = generate_instance('IES10-1', n=10, Q=100, H=50, seed=101)\n"
        "print(f'Total demand: {inst.total_demand()}, Min vehicles: {inst.min_vehicles_needed()}')\n"
        "inst.save('IES10-1.json')\n"
        "reloaded = OVRPSDInstance.load('IES10-1.json')",
        title="Python Usage: instance_generator.py"
    )

    # ================= PAGE 6: OVRPSD_MODEL.PY =================
    pdf.add_page()
    pdf.chapter_title("5. Deep-Dive: ovrpsd_model.py")
    pdf.body_p(
        "ovrpsd_model.py is the core mathematical engine. It defines the solution data class OVRPSDSolution and translates "
        "the paper's linear integer programming models into executable PuLP optimization problems solved with CBC."
    )

    pdf.chapter_title("The OVRPSDSolution Data Structure", level=2)
    pdf.body_p("Every solver function returns an instance of OVRPSDSolution containing complete solution telemetry:")
    pdf.key_val("status", "'Optimal', 'Feasible' (stopped on time limit), 'Infeasible', or 'No Solution'")
    pdf.key_val("objective", "Total cost achieved: sum of travel costs + sum of vehicle hiring charges")
    pdf.key_val("routes", "List of routes, where each route is an ordered list of node indices starting at 0 (e.g. [0, 4, 2, 7])")
    pdf.key_val("deliveries", "Dictionary {(customer_id, vehicle_k): delivered_amount} detailing split deliveries")
    pdf.key_val("vehicles_used", "Number of distinct vehicles that leave the depot (len(routes))")
    pdf.key_val("splits", "Count of customer nodes served by more than one vehicle")
    pdf.key_val("gap", "Optimality gap percentage calculated strictly as in the paper: (UB - LB) / LB * 100%")
    pdf.key_val("cpu_time", "Total elapsed solver time in seconds")
    pdf.key_val("initial_lb / lower_bound", "Initial LP relaxation bound and best proven lower bound from branch-and-bound")

    pdf.chapter_title("Mathematical Formulations Implemented", level=2)

    pdf.bullet(
        "Implements the classical arc-flow formulation (Section 2.1). Uses 3-index binary decision variables x_ij^k (vehicle k travels arc (i,j)), continuous cumulative load flow variables u_ij^k on each arc, and explicit vehicle activation binary variables z^k. MTZ subtour elimination is handled via cumulative arc flow balances (Eq. 10-12). Although it has a tighter LP relaxation bound, it requires O(|K| * n^2) continuous flow variables, making the root relaxation significantly larger.",
        "Formulation 1 (solve_formulation1) - Arc Flow:"
    )

    pdf.bullet(
        "Implements the simplified, improved model (Section 2.2). Employs node-indexed load variables u_i^k (cumulative load of vehicle k after visiting node i) instead of arc-indexed variables, dramatically reducing variable count. A critical simplification is that vehicle hiring cost H is absorbed directly into depot departure arcs: c'_0j = c_0j + H for all customers j, which eliminates the explicit z^k variables. Subtour elimination uses the simplified MTZ constraint (Eq. 28): u_i^k - u_j^k + Q * x_ij^k <= Q - q_j^k.",
        "Formulation 2 (solve_formulation2) - Node Flow:"
    )

    pdf.bullet(
        "Modified Formulation 2 where split deliveries are prohibited (Section 6.2). Constraints (24-26) are eliminated, and each customer must be visited exactly once. The delivery quantity q_j^k is replaced with the fixed demand d_j in MTZ subtour elimination. Used as a baseline in the case study to prove the cost savings of split deliveries.",
        "No-Split Variant (solve_formulation2_no_split):"
    )

    pdf.callout_box(
        "Formulation 2 is equipped with three critical boolean flags enabling cutting-plane integration:\n"
        "- relax_integers=True: Relaxes binary variables x_ij^k and s_j to continuous [0, 1] for LP solving.\n"
        "- exclude_mtz=True: Omits MTZ subtour constraint (28) during cut generation so max-flow finds capacity cuts.\n"
        "- extra_constraints=cuts: Dynamically injects generated rounded capacity inequality cuts into the model.",
        title="CUTTING-PLANE INTERFACE FLAGS",
        kind="tip"
    )

    pdf.chapter_title("Low-Level CBC Solver Interaction", level=2)
    pdf.body_p(
        "PuLP's default Python wrapper does not expose CBC's internal branch-and-bound lower bounds. "
        "ovrpsd_model.py implements _solve_with_cbc(), which executes CBC single-threaded (preventing Windows multi-threading deadlocks) "
        "and parses the raw log file with regular expressions to extract 'Continuous objective value is' (Initial LB) and 'Lower bound:' (Final LB)."
    )

    # ================= PAGE 7: MAX_FLOW.PY =================
    pdf.add_page()
    pdf.chapter_title("6. Deep-Dive: max_flow.py")
    pdf.body_p(
        "max_flow.py provides the separation algorithm for Rounded Capacity Inequalities (RCIs). "
        "It implements a self-contained, high-performance Ford-Fulkerson network flow algorithm with Edmonds-Karp BFS "
        "and translates fractional LP solutions into minimum cut separations."
    )

    pdf.chapter_title("Mathematical Foundation: Rounded Capacity Inequalities (Eq. 33)", level=2)
    pdf.body_p(
        "For any subset of customers D subset V^+, let d(D) = sum_{j in D} d_j be their total demand. "
        "Since each vehicle can carry at most capacity Q, at least ceil(d(D) / Q) distinct vehicle entries are strictly required. "
        "The Rounded Capacity Inequality (RCI) states:"
    )
    pdf.code_box(
        "sum_{k in K} sum_{i not in D} sum_{j in D} x_ij^k  >=  ceil( d(D) / Q )    [Equation 33]",
        title="Rounded Capacity Inequality (RCI)"
    )
    pdf.body_p(
        "Because there are 2^n possible customer subsets D, adding all RCIs upfront would cause an exponential explosion of constraints. "
        "Instead, we solve the LP relaxation and identify only those subsets D where the fractional solution violates Eq. 33."
    )

    pdf.chapter_title("Classes and Functions in max_flow.py", level=2)

    pdf.bullet(
        "Directed residual network graph. Edges are stored in an adjacency dictionary. Residual capacity is maintained skew-symmetrically: residual(u, v) = graph[u][v] - flow[u][v]. The bfs(source, sink) method finds the shortest augmenting path using a queue (Edmonds-Karp), ensuring O(V * E^2) worst-case polynomial time. max_flow() computes the maximum bottleneck flow, and min_cut(source) traverses the residual network to identify the set of all nodes reachable from the source.",
        "MaxFlowGraph(n):"
    )

    pdf.bullet(
        "Constructs the fractional support network G* = (V, A*) from the fractional LP relaxation solution x*. Nodes 0..n represent depot and customers. For every ordered pair (i, j), the arc capacity equals the sum of fractional flows across all vehicles: capacity(i, j) = sum_{k in K} x*_ij^k. Only arcs with positive flow (> 10^-9) are added.",
        "build_support_graph(n, K, x_values) -> MaxFlowGraph:"
    )

    pdf.bullet(
        "Executes the exact separation routine. For each customer node j in 1..n, it sets the depot (node 0) as source and j as sink, computes max_flow(0, j), and retrieves the min-cut reachable set. The unreachable customer set D = V^+ \\ Reachable is evaluated: if sum_{i not in D, j in D} capacity(i, j) < ceil(d(D)/Q) - 10^-6, the cut is violated! Returns a list of (D, required_flow) tuples.",
        "find_violated_capacity_cuts(n, K, Q, demands, x_values) -> list[tuple]:"
    )

    pdf.callout_box(
        "Max-Flow Min-Cut Duality in Cut Separation:\n"
        "By the Max-Flow Min-Cut theorem, the maximum flow from depot (0) to customer j equals the capacity of the minimum cut "
        "separating 0 from j. If this maximum flow is strictly less than ceil(d(D) / Q), we have mathematically proven that the "
        "current fractional routing cannot deliver the required goods to subset D, providing an exact violated cutting plane.",
        title="ALGORITHMIC ELEGANCE",
        kind="info"
    )

    # ================= PAGE 8: CUTTING_PLANE.PY =================
    pdf.add_page()
    pdf.chapter_title("7. Deep-Dive: cutting_plane.py")
    pdf.body_p(
        "cutting_plane.py connects ovrpsd_model.py and max_flow.py into the two-phase cutting-plane algorithm "
        "described in Section 4 of the paper. It dramatically accelerates convergence on challenging instances."
    )
    pdf.add_image_card(os.path.join(DOC_ASSETS_DIR, "cutting_plane_lifecycle.png"), w=170,
                       caption="Figure 7.1: Cutting-Plane Method Two-Phase Execution Lifecycle")

    pdf.chapter_title("Detailed Two-Phase Algorithm Walkthrough", level=2)

    pdf.bullet(
        "The solver initializes an empty cut repository all_cuts = []. In each iteration (up to 50 iterations or until time runs out): "
        "(1) It calls solve_formulation2() with relax_integers=True and exclude_mtz=True, passing all accumulated cuts via extra_constraints. "
        "(2) It extracts positive fractional variables x*. "
        "(3) It passes x* to max_flow.find_violated_capacity_cuts(). "
        "(4) Any newly discovered cuts (D, required) not already in all_cuts are appended. "
        "(5) If no new violated cuts are found, Phase 1 terminates early.",
        "Phase 1 - Cut Separation Loop:"
    )

    pdf.bullet(
        "Once Phase 1 finishes (either no more cuts or time reached): "
        "(1) Integrality is restored (relax_integers=False), making x_ij^k and s_j binary. "
        "(2) Simplified MTZ subtour elimination constraints (Eq. 28) are activated (exclude_mtz=False). "
        "(3) All accumulated capacity cuts from Phase 1 are injected as static linear constraints. "
        "(4) The complete model is solved using CBC branch-and-bound with the remaining time budget.",
        "Phase 2 - Final Full MILP:"
    )

    pdf.chapter_title("The compare_methods() Utility", level=2)
    pdf.body_p(
        "cutting_plane.py also includes compare_methods(instance, H_values=[0, 50, 100], time_limit=300), which directly evaluates "
        "plain Formulation 2 versus Cutting-Plane Formulation 2 on the exact same instance across multiple hiring cost levels. "
        "This function was used to empirically demonstrate why cutting planes are indispensable: on 20-customer instances, plain F2 "
        "stalls with large GAPs or 'No Solution', while the cutting-plane method closes the optimality gap in a fraction of the time."
    )

    # ================= PAGE 9: VISUALIZATION.PY =================
    pdf.add_page()
    pdf.chapter_title("8. Deep-Dive: visualization.py")
    pdf.body_p(
        "visualization.py is the graphical presentation module. Built on matplotlib, it produces high-DPI "
        "charts and route network maps styled consistently with the figures in Ruiz y Ruiz et al. (2022)."
    )

    pdf.chapter_title("Visualization Functions & Capabilities", level=2)

    pdf.bullet(
        "Renders the customer network prior to solving. The central depot (node 0) is depicted as a distinct square; customer nodes are plotted as circles with marker sizes scaled proportionally to demand d_i.",
        "plot_instance(instance, title, save_path, show):"
    )

    pdf.bullet(
        "The flagship visualizer. Renders open vehicle routes, each in a unique color from ROUTE_COLORS. Small arrowheads indicate travel direction along each arc. Customer nodes served by multiple vehicles are highlighted with glowing gold diamond markers labeled '(SPLIT)'. Open routes terminate at customer nodes without returning to the depot.",
        "plot_solution(instance, solution, title, save_path, show):"
    )

    pdf.bullet(
        "Plots 3-panel horizontal subplots showing how varying hiring cost H from 0 to 100 impacts: (1) Total Objective Cost, (2) Vehicles Used (Fleet Size), and (3) Total Customer Delivery Splits.",
        "plot_hc_impact(hc_values, objectives, vehicles, splits, instance_name, save_path):"
    )

    pdf.bullet(
        "Generates grouped bar charts comparing different algorithms (e.g. F2 vs Cutting Planes) or delivery policies (Split Deliveries vs No-Split) across Objective Value, Fleet Size, and CPU Time.",
        "plot_comparison_bar_chart(results_dict, title, save_path):"
    )

    pdf.ln(2)
    pdf.chapter_title("Sample Visual Outputs Generated by the Codebase", level=2)
    pdf.body_p("Below are actual visual artifacts produced by visualization.py during the experimental runs:")

    # Embed two sample plots side-by-side or stacked
    pdf.add_image_card(os.path.join(OUTPUT_DIR, "demo_solution_hc50.png"), w=135,
                       caption="Figure 8.1: DEMO-5 Solution with HC=50 showing open routes and Split Delivery at Customer 5")
    pdf.add_image_card(os.path.join(OUTPUT_DIR, "hc_impact.png"), w=135,
                       caption="Figure 8.2: Hiring Cost Sensitivity Analysis (Total Cost, Fleet Size, Splits)")

    # ================= PAGE 10: RUN_EXPERIMENTS.PY =================
    pdf.add_page()
    pdf.chapter_title("9. Deep-Dive: run_experiments.py & Automation Scripts")
    pdf.body_p(
        "run_experiments.py is the master command-line application. It provides an interactive menu and automated harness "
        "to reproduce every table and computational experiment presented in Ruiz y Ruiz et al. (2022)."
    )

    pdf.chapter_title("Menu Options & Experimental Suites", level=2)

    pdf.bullet(
        "Solves a 5-customer instance (DEMO-5) under HC in {0, 50, 100} using both Formulation 2 and Cutting Planes. Takes ~30 seconds. Confirms system health, verifies split delivery logic, and saves solution plots.",
        "Option 1 - Quick Demo (run_small_demo):"
    )

    pdf.bullet(
        "Solves 6 synthetic instances (2x20, 2x25, 2x30 customers) under HC in {0, 50, 100} using both Formulation 1 and Formulation 2. Formats results into Table 1 (F1) and Table 2 (F2), reporting Initial LB, Upper Bound, Lower Bound, GAP, and CPU time.",
        "Option 2 - Preliminary Comparison (run_preliminary_experiments):"
    )

    pdf.bullet(
        "Tests the cutting-plane method across 9 benchmark instances (IES10, IES15, IES20) with HC in {0, 50, 100} (27 total solves). Generates formatted output matching Tables 7-9 of the paper, detailing cuts added and splits found.",
        "Option 3 - Cutting-Plane Experiments (run_cutting_plane_experiments):"
    )

    pdf.bullet(
        "Executes the Guadalajara pharmaceutical case study across 5 instances (CE1 to CE5, 13 to 21 customers). Generates Table 5 (impact of HC=0 vs HC=100) and Table 6 (direct comparison of Split vs No-Split delivery policies, proving percentage savings).",
        "Option 4 - Case Study Evaluation (run_case_study):"
    )

    pdf.bullet(
        "Evaluates hiring cost sensitivity on a 10-customer instance with HC in {0, 25, 50, 75, 100}. Tracks how fleet size contracts and how split deliveries compensate for reduced vehicle count.",
        "Option 5 - Hiring Cost Sensitivity Analysis (run_hc_impact_analysis):"
    )

    pdf.bullet(
        "Executes Options 1 through 5 sequentially in an unattended automated batch run. Generates all text tables, summary logs, and route diagrams in the output/ directory.",
        "Option 6 - Run ALL Experiments:"
    )

    pdf.chapter_title("Batch Execution Scripts: run_all.bat & run_all.sh", level=2)
    pdf.body_p(
        "To allow long-running computational benchmarks to run unattended in the background, two wrapper scripts are provided:"
    )
    pdf.key_val("run_all.bat", "Windows batch script. Navigates to folder, verifies requirements via pip, creates output directory, and runs 'python -u run_experiments.py 6 > output\\run_all.log 2>&1'.")
    pdf.key_val("run_all.sh", "POSIX shell script for Linux/macOS. Executes option 6 with output tee'd to output/run_all.log.")
    pdf.key_val("requirements.txt", "Minimal pinned dependencies: PuLP>=2.7, numpy>=1.21, matplotlib>=3.5, tabulate>=0.9.")

    # ================= PAGE 11: OUTPUT DIRECTORY ANATOMY =================
    pdf.add_page()
    pdf.chapter_title("10. Output Directory Anatomy")
    pdf.body_p(
        "All computational runs, formatted text tables, log traces, and rendered diagrams are centralized in the output/ directory. "
        "The table below details every generated file, the script that produces it, and how to interpret its contents:"
    )

    out_headers = ["Output File", "Generating Function / Option", "Content Description & Key Metrics"]
    out_widths = [45, 45, 84]
    out_rows = [
        ["run_all.log", "run_all.bat / run_all.sh", "Complete console stdout/stderr log of Option 6 (33KB, 475 lines of execution trace)."],
        ["demo_results.txt", "run_small_demo() (Option 1)", "Comparative table for DEMO-5 comparing F2 vs CP across HC=0, 50, 100."],
        ["table1_formulation1.txt", "run_preliminary() (Option 2)", "Formulation 1 results on G20, G25, G30 (18 rows: Init LB, UB, LB, GAP, CPU)."],
        ["table2_formulation2.txt", "run_preliminary() (Option 2)", "Formulation 2 results on G20, G25, G30 (demonstrates CBC stalls without cuts)."],
        ["cutting_plane_results.txt", "run_cutting_plane() (Option 3)", "Tables 7-9 layout: IES10, IES15, IES20 benchmarks (27 rows: vehicles, cuts, splits)."],
        ["table5_case_study_hc.txt", "run_case_study() (Option 4)", "Pharmaceutical case study CE1-CE5 under HC=0 vs HC=100 (vehicles, cost, splits)."],
        ["table6_split_vs_nosplit.txt", "run_case_study() (Option 4)", "Cost savings comparison: Split vs No-Split delivery policy at HC=100."],
        ["demo_instance.png", "run_small_demo()", "Scatter plot of DEMO-5 depot and 5 customers with demand annotations."],
        ["demo_solution_hc*.png", "run_small_demo()", "Route maps for DEMO-5 under HC=0 (4 veh), HC=50 (3 veh, 1 split), HC=100."],
        ["cp_IES*_hc50.png", "run_cutting_plane()", "Route plots for benchmark instances solved via cutting-plane method."],
        ["cs_CE*_hc*.png", "run_case_study()", "Route maps for case study instances CE1 through CE5 with split indicators."],
        ["case_study_comparison.png", "run_case_study()", "Grouped bar chart comparing Split vs No-Split delivery costs and fleet sizes."],
        ["hc_impact.png", "run_hc_impact_analysis()", "Three-panel sensitivity curves showing Cost, Vehicles, and Splits vs HC."],
    ]
    pdf.draw_table(out_headers, out_rows, out_widths)

    # Embed Case study comparison plot
    pdf.ln(2)
    pdf.add_image_card(os.path.join(OUTPUT_DIR, "case_study_comparison.png"), w=155,
                       caption="Figure 10.1: Case Study Split vs No-Split Cost & Fleet Size Comparison (output/case_study_comparison.png)")

    # ================= PAGE 12: WORKFLOW SCENARIOS =================
    pdf.add_page()
    pdf.chapter_title("11. End-to-End Workflow Scenarios")
    pdf.body_p(
        "To illustrate how control and data flow through the codebase in practice, let us examine two representative execution traces:"
    )

    pdf.chapter_title("Scenario A: Quick Demo Execution Trace (Option 1)", level=2)
    pdf.body_p("When a user runs 'python run_experiments.py 1', the following sequence of calls occurs across files:")
    pdf.bullet("run_experiments.py calls instance_generator.generate_instance('DEMO-5', n=5, Q=100, H=0, seed=42). This computes the 6x6 Euclidean distance matrix.", "Step 1 (Generate): ")
    pdf.bullet("run_experiments.py calls visualization.plot_instance(inst, save_path='output/demo_instance.png') to render the initial depot and customer scatter map.", "Step 2 (Plot): ")
    pdf.bullet("For each HC in [0, 50, 100], run_experiments calls ovrpsd_model.solve_formulation2(inst, H=hc, time_limit=120). PuLP builds the problem, writes a temporary CBC log, executes CBC, parses the bounds, and returns sol_f2.", "Step 3 (Solve F2): ")
    pdf.bullet("run_experiments calls cutting_plane.solve_with_cutting_planes(inst, H=hc). cutting_plane iteratively solves the LP relaxation via ovrpsd_model, calls max_flow to separate capacity cuts, injects cuts, and solves the final MILP.", "Step 4 (Solve CP): ")
    pdf.bullet("The best solution between sol_f2 and sol_cp is plotted using visualization.plot_solution() and saved as output/demo_solution_hc{hc}.png.", "Step 5 (Render): ")
    pdf.bullet("Metrics are formatted into an ASCII table via tabulate and saved to output/demo_results.txt.", "Step 6 (Export): ")

    pdf.chapter_title("Scenario B: Case Study Comparison Trace (Option 4)", level=2)
    pdf.body_p("When running the pharmaceutical case study comparison (Table 6):")
    pdf.bullet("instance_generator.generate_case_study_instance('CE1' to 'CE5') generates 5 metropolitan instances with demands 8-24 pallets and Q=50.", "Step 1: ")
    pdf.bullet("cutting_plane.solve_with_cutting_planes(inst, H=100) solves the problem WITH split deliveries allowed. Routes and split delivery allocations are extracted.", "Step 2: ")
    pdf.bullet("ovrpsd_model.solve_formulation2_no_split(inst, H=100) solves the exact same instance WITHOUT split deliveries (each customer visited exactly once).", "Step 3: ")
    pdf.bullet("Cost savings percentage = (NoSplit_Cost - Split_Cost) / NoSplit_Cost * 100% is computed. Results show 9% to 27% cost savings from allowing split deliveries.", "Step 4: ")
    pdf.bullet("visualization.plot_comparison_bar_chart() generates output/case_study_comparison.png.", "Step 5: ")

    # ================= PAGE 13: TECHNICAL SYNTHESIS =================
    pdf.add_page()
    pdf.chapter_title("12. Technical Synthesis & Architectural Patterns")
    pdf.body_p(
        "The OVRPSD codebase serves as an exemplary implementation of modern Operations Research software engineering. "
        "Several key design patterns and algorithmic principles are demonstrated:"
    )

    pdf.bullet("The OVRPSDInstance and OVRPSDSolution classes act as strict boundaries between modules. Solvers, visualizers, and experiment harnesses never access raw files or global variables; they exchange clean, typed DTOs.", "1. Data Transfer Object (DTO) Pattern: ")
    pdf.bullet("Formulation 1, Formulation 2, and Formulation 2 No-Split all share identical method signatures (instance, H, time_limit, verbose) and return identical OVRPSDSolution contracts. This allows run_experiments to benchmark different models interchangeably.", "2. Strategy Pattern for Mathematical Models: ")
    pdf.bullet("Cut separation (max_flow.py) is completely decoupled from MILP solving (ovrpsd_model.py). max_flow has zero dependencies on PuLP or CBC; it operates purely on graphs and numeric capacities. This allows the max-flow algorithm to be optimized or replaced independently.", "3. Separation of Separation from Solving: ")
    pdf.bullet("Because PuLP does not natively expose internal branch-and-bound lower bounds for CBC, ovrpsd_model transparently intercepts CBC execution logs via temporary files, parsing the bounds with regular expressions while keeping the public API clean.", "4. Non-Invasive Solver Telemetry: ")

    pdf.ln(3)
    pdf.callout_box(
        "SUMMARY TAKEAWAY FOR STUDYING THE CODEBASE:\n"
        "- To modify instance properties or add real-world GPS coordinates: edit instance_generator.py.\n"
        "- To adjust mathematical constraints, subtour rules, or objective terms: edit ovrpsd_model.py.\n"
        "- To implement new valid inequalities (e.g. framed capacity cuts or clique cuts): add separation in max_flow.py.\n"
        "- To alter cutting-plane termination criteria or cut limits: tune cutting_plane.py.\n"
        "- To customize route plots, color palettes, or layout styling: edit visualization.py.\n"
        "- To run custom experiments or adjust time limits: edit run_experiments.py.",
        title="DEVELOPER'S EXTENSION GUIDE",
        kind="tip"
    )

    pdf.ln(6)
    pdf.set_draw_color(30, 64, 175)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, "End of Technical Architecture Guide. Generated for the OVRPSD Implementation Repository.", align="C")

    # Output file
    pdf.output(PDF_OUTPUT_PATH)
    print(f"Guide successfully compiled to: {PDF_OUTPUT_PATH}")

if __name__ == "__main__":
    build_codebase_guide()

