import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src.wrapper_tools import ffi_wrapper
from src.wrapper_tools import analyse_tools
import numpy as np

# --- IMPORT MATPLOTLIB ---
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

SOURCEDEST = ("Ford-Fulkerson", "Edmonds-Karp")
ALGO = ("EPANET", "Ford-Fulkerson", "Edmonds-Karp")
ORIEN = ("Aucune", "EPANET", "Ford-Fulkerson", "Edmonds-Karp")

class AnalysisWindow(tk.Frame):
    def __init__(self, parent, app_manager):
        super().__init__(parent, bg="white", bd=2, relief="groove")
        self.app_manager = app_manager
        self.projet = None
        self.results = []
        
        self.keys_map = {
            "Mult. Source": "m_src",
            "Mult. Dest. (EPA)": "m_dst_epa",
            "Mult. Dest. (Algo)": "m_dst",
            "Satisfaisabilité Réf (%)": "sat_ref",
            "Satisfaisabilité Cible (%)": "sat_tgt",
            "Erreur Absolue ponderee (WAPE %)": "wape",
            "Erreur ponderee (%)": "wp",
            "Distance de Jaccard (%)": "jaccard"
        }

        self.setup_ui()
        self.setup_bindings()
        self.place(x=100, y=100, width=1100, height=750)
        self.set_focus()

    def setup_ui(self):
        self.title_bar = tk.Frame(self, bg="#8e44ad", relief="flat", bd=0, height=25)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        self.title_label = tk.Label(self.title_bar, text="Analyse Paramétrique Croisée", bg="#8e44ad", fg="white", font=("Segoe UI", 9, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=5)
        self.close_btn = tk.Button(self.title_bar, text="X", bg="#e74c3c", fg="white", bd=0, width=3, command=self.close_window)
        self.close_btn.pack(side=tk.RIGHT)

        main_content = tk.Frame(self, bg="white")
        main_content.pack(fill=tk.BOTH, expand=True)

        # 1. PANNEAU LATÉRAL AVEC SCROLLBAR
        sidebar_container = tk.Frame(main_content, width=280, bg="#ecf0f1", relief="solid", bd=1)
        sidebar_container.pack(side=tk.LEFT, fill=tk.Y)
        sidebar_container.pack_propagate(False)

        canvas_side = tk.Canvas(sidebar_container, bg="#ecf0f1", highlightthickness=0)
        scrollbar = ttk.Scrollbar(sidebar_container, orient="vertical", command=canvas_side.yview)
        self.sidebar = tk.Frame(canvas_side, bg="#ecf0f1", padx=10, pady=10)

        self.sidebar.bind("<Configure>", lambda e: canvas_side.configure(scrollregion=canvas_side.bbox("all")))
        canvas_side.create_window((0, 0), window=self.sidebar, anchor="nw", width=260)
        canvas_side.configure(yscrollcommand=scrollbar.set)
        
        canvas_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(self.sidebar, text="Charger Réseau (.inp)", command=self.load_file, bg="white").pack(fill=tk.X, pady=(0, 10))

        seed_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        seed_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(seed_frame, text="Seed (Opt.):", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.seed_entry = tk.Entry(seed_frame, width=10)
        self.seed_entry.pack(side=tk.LEFT, padx=2)

        tk.Button(self.sidebar, text="Randomiser Demandes", bg="#f39c12", fg="black", 
                  font=("Segoe UI", 8, "bold"), command=self.randomise_demandes).pack(fill=tk.X, pady=(0, 10))

        tk.Label(self.sidebar, text="Balayage (Grid Search)", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        grid = tk.Frame(self.sidebar, bg="#ecf0f1")
        grid.pack(fill=tk.X, pady=2)
        tk.Label(grid, text="Min", bg="#ecf0f1", width=5).grid(row=0, column=1)
        tk.Label(grid, text="Max", bg="#ecf0f1", width=5).grid(row=0, column=2)
        tk.Label(grid, text="Nb", bg="#ecf0f1", width=4).grid(row=0, column=3)

        self.ranges = {}
        for i, (key, label) in enumerate([("m_src", "M.Src"), ("m_dst_epa", "M.Dst(E)"), ("m_dst", "M.Dst(A)")]):
            tk.Label(grid, text=label, bg="#ecf0f1", anchor="w", font=("Segoe UI", 8)).grid(row=i+1, column=0, sticky="w")
            ent_min, ent_max, ent_n = tk.Entry(grid, width=5), tk.Entry(grid, width=5), tk.Entry(grid, width=4)
            ent_min.insert(0, "1.0")
            ent_max.insert(0, "1.0")
            ent_n.insert(0, "1")
            ent_min.grid(row=i+1, column=1, padx=2, pady=1)
            ent_max.grid(row=i+1, column=2, padx=2)
            ent_n.grid(row=i+1, column=3, padx=2)
            self.ranges[key] = (ent_min, ent_max, ent_n)

        # --- MODÈLE RÉFÉRENCE ---
        ref_f = tk.LabelFrame(self.sidebar, text="Modèle de Référence", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        ref_f.pack(fill=tk.X, pady=5)
        tk.Label(ref_f, text="Algo:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_algo = tk.StringVar(value="EPANET")
        ttk.Combobox(ref_f, textvariable=self.ref_algo, values=ALGO, state="readonly").pack(fill=tk.X, padx=5, pady=2)
        tk.Label(ref_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_ori = tk.StringVar(value="Aucune")
        ttk.Combobox(ref_f, textvariable=self.ref_ori, values=ORIEN, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        # --- MODÈLE CIBLE ---
        tgt_f = tk.LabelFrame(self.sidebar, text="Modèle à Comparer (Cible)", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        tgt_f.pack(fill=tk.X, pady=5)
        tk.Label(tgt_f, text="Algo:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.tgt_algo = tk.StringVar(value="Edmonds-Karp")
        ttk.Combobox(tgt_f, textvariable=self.tgt_algo, values=ALGO, state="readonly").pack(fill=tk.X, padx=5, pady=2)
        tk.Label(tgt_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.tgt_ori = tk.StringVar(value="Aucune")
        ttk.Combobox(tgt_f, textvariable=self.tgt_ori, values=ORIEN, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        v_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        v_frame.pack(fill=tk.X, pady=5)
        tk.Label(v_frame, text="V. Rés:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.v_res = tk.Entry(v_frame, width=5); self.v_res.insert(0, "180.0"); self.v_res.pack(side=tk.LEFT, padx=2)
        tk.Label(v_frame, text="V. Arc:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.v_arc = tk.Entry(v_frame, width=5); self.v_arc.insert(0, "120.0"); self.v_arc.pack(side=tk.LEFT, padx=2)

        tk.Button(self.sidebar, text="Lancer l'Analyse", bg="#2980b9", fg="white", font=("Segoe UI", 9, "bold"), command=self.run_analysis).pack(fill=tk.X, pady=10)

        # --- TRACÉ MATPLOTLIB ---
        tk.Label(self.sidebar, text="Tracé du Graphe", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        plot_opts = list(self.keys_map.keys())
        
        tk.Label(self.sidebar, text="Axe X :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.x_var = tk.StringVar(value="Mult. Dest. (EPA)")
        cb_x = ttk.Combobox(self.sidebar, textvariable=self.x_var, values=plot_opts, state="readonly")
        cb_x.pack(fill=tk.X); cb_x.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Axe Y :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.y_var = tk.StringVar(value="Satisfaisabilité Cible (%)")
        cb_y = ttk.Combobox(self.sidebar, textvariable=self.y_var, values=plot_opts, state="readonly")
        cb_y.pack(fill=tk.X); cb_y.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Couleur :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.c_var = tk.StringVar(value="Aucune")
        cb_c = ttk.Combobox(self.sidebar, textvariable=self.c_var, values=["Aucune"] + plot_opts, state="readonly")
        cb_c.pack(fill=tk.X); cb_c.bind("<<ComboboxSelected>>", self.update_plot)

        # 2. ZONE DE DESSIN MATPLOTLIB
        self.plot_frame = tk.Frame(main_content, bg="white")
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar_frame = tk.Frame(self.plot_frame, bg="white")
        self.toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()

        self.canvas.mpl_connect('pick_event', self.on_pick)

        # Barre d'état
        self.status_bar = tk.Frame(self, bg="#bdc3c7", height=20)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(self.status_bar, text="Prêt", bg="#bdc3c7", font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.grip = tk.Label(self.status_bar, text="◢", bg="#bdc3c7", fg="#7f8c8d", cursor="bottom_right_corner")
        self.grip.pack(side=tk.RIGHT, anchor="se", padx=2)

    def setup_bindings(self):
        self.title_bar.bind("<ButtonPress-1>", self.start_drag_window)
        self.title_label.bind("<ButtonPress-1>", self.start_drag_window)
        self.title_bar.bind("<B1-Motion>", self.do_drag_window)
        self.title_label.bind("<B1-Motion>", self.do_drag_window)
        self.grip.bind("<ButtonPress-1>", self.start_resize_window)
        self.grip.bind("<B1-Motion>", self.do_resize_window)

    def set_focus(self, event=None):
        self.tkraise()
        self.app_manager.set_active_window(self)

    def set_active_style(self, is_active):
        color = "#9b59b6" if is_active else "#8e44ad"
        self.title_bar.config(bg=color)
        self.title_label.config(bg=color)

    def close_window(self):
        self.app_manager.remove_window(self)
        self.destroy()

    def start_drag_window(self, event):
        self.set_focus()
        self._drag_start_x, self._drag_start_y = event.x, event.y

    def do_drag_window(self, event):
        self.place(x=self.winfo_x() - self._drag_start_x + event.x, y=self.winfo_y() - self._drag_start_y + event.y)

    def start_resize_window(self, event):
        self.set_focus()
        self.start_w, self.start_h = self.winfo_width(), self.winfo_height()
        self.start_x, self.start_y = event.x_root, event.y_root

    def do_resize_window(self, event):
        self.place(width=max(600, self.start_w + event.x_root - self.start_x), height=max(400, self.start_h + event.y_root - self.start_y))

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("EPANET", "*.inp")])
        if path:
            self.current_file = path
            self.projet = ffi_wrapper.create_epanet_project(path)
            filename = path.split("/")[-1].split("\\")[-1]
            self.title_label.config(text=f"|  Analyse : {filename}")
            self.status_label.config(text=f"Fichier {filename} chargé.")

    def randomise_demandes(self):
        if not self.projet:
            messagebox.showinfo("Info", "Veuillez charger un réseau d'abord.")
            return

        seed_str = self.seed_entry.get().strip()

        if seed_str:
            try:
                seed_val = int(seed_str)
            except ValueError:
                messagebox.showwarning("Attention", "La seed doit être un nombre entier.")
                return
        else:
            seed_val = None

        ffi_wrapper.set_random_seed(seed_val)
        ffi_wrapper.randomise_demande(self.projet)

        self.status_label.config(text=f"Demandes randomisées (Seed: {seed_val}).")

    def compute_algo(self, reseau, choix, m_src, m_dst):
        match (choix):
            case "Ford-Fulkerson":
                ffi_wrapper.ajout_source_destination(reseau)
                ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
                ffi_wrapper.ajout_capacite_source(reseau, m_src)
                ffi_wrapper.nullifier_flow(reseau)
                ffi_wrapper.compute_flow_ford_fukerson(reseau)
                ffi_wrapper.delete_source_destination(reseau)
            case "Edmonds-Karp":
                ffi_wrapper.ajout_source_destination(reseau)
                ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
                ffi_wrapper.ajout_capacite_source(reseau, m_src)
                ffi_wrapper.nullifier_flow(reseau)
                ffi_wrapper.compute_flow_edmonds_karp(reseau)
                ffi_wrapper.delete_source_destination(reseau)

    def compute_graph(self, algo, ori, m_src, m_dst, v_res, v_arc):
        if algo == "EPANET":
            ffi_wrapper.compute_epanet(self.projet)
            reseau = ffi_wrapper.import_epanet_graph(self.projet)
        else:
            reseau = None
            if ori == "EPANET":
                ffi_wrapper.compute_epanet(self.projet)
                reseau = ffi_wrapper.import_epanet_graph(self.projet)
                ffi_wrapper.fix_capacite_flow_oriente(reseau, v_res, v_arc)
            elif ori == "Aucune":
                reseau = ffi_wrapper.import_epanet_graph(self.projet)
                ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
            else:
                reseau = ffi_wrapper.import_epanet_graph(self.projet)
                ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
                self.compute_algo(reseau, ori, m_src, m_dst)
                ffi_wrapper.fix_capacite_flow_oriente(reseau, v_res, v_arc)

            self.compute_algo(reseau, algo, m_src, m_dst)

        return reseau

    def run_analysis(self):
        if not self.projet:
            messagebox.showinfo("Info", "Veuillez charger un fichier .inp d'abord.")
            return

        try:
            v_res, v_arc = float(self.v_res.get()), float(self.v_arc.get())
            algo_ref, ori_ref = self.ref_algo.get(), self.ref_ori.get()
            algo_tgt, ori_tgt = self.tgt_algo.get(), self.tgt_ori.get()
            
            src_min, src_max, src_n = map(float, [self.ranges["m_src"][i].get() for i in range(3)])
            epa_min, epa_max, epa_n = map(float, [self.ranges["m_dst_epa"][i].get() for i in range(3)])
            dst_min, dst_max, dst_n = map(float, [self.ranges["m_dst"][i].get() for i in range(3)])

            arr_src = np.linspace(src_min, src_max, int(src_n))
            arr_epa = np.linspace(epa_min, epa_max, int(epa_n))
            arr_dst = np.linspace(dst_min, dst_max, int(dst_n))

            self.results = []
            total_iters = len(arr_src) * len(arr_epa) * len(arr_dst)
            current_iter = 0
            current_epa_mult = 1.0 
            graph_ref = None
            graph_tgt = None

            for m_epa in arr_epa:
                ffi_wrapper.modif_multiplicateur(self.projet, m_epa / current_epa_mult)
                current_epa_mult = m_epa
                if algo_ref == "EPANET":
                    graph_ref = self.compute_graph(algo_ref, ori_ref, 1.0, 1.0, 1.0, 1.0)
                if algo_tgt == "EPANET":
                    graph_tgt = self.compute_graph(algo_tgt, ori_ref, 1.0, 1.0, 1.0, 1.0)

                for m_dst in arr_dst:
                    for m_src in arr_src:
                        current_iter += 1
                        self.status_label.config(text=f"Simulation... {current_iter}/{total_iters}")
                        self.update_idletasks()

                        if algo_ref != "EPANET":
                            if graph_ref is not None:
                                ffi_wrapper.free_graph(graph_ref)
                            graph_ref = self.compute_graph(algo_ref, ori_ref, m_src, m_dst, v_res, v_arc)
                        if algo_tgt != "EPANET":
                            if graph_tgt is not None:
                                ffi_wrapper.free_graph(graph_tgt)
                            graph_tgt = self.compute_graph(algo_tgt, ori_tgt, m_src, m_dst, v_res, v_arc)

                        wape = analyse_tools.get_wape_flow(graph_ref, graph_tgt) * 100
                        wp = analyse_tools.get_wp_flow(graph_ref, graph_tgt) * 100
                        sat_ref = float(analyse_tools.get_efficacite(graph_ref)) * 100
                        sat_tgt = float(analyse_tools.get_efficacite(graph_tgt)) * 100
                        jaccard_d = analyse_tools.jaccard_distance(graph_ref, graph_tgt) * 100

                        self.results.append({
                            "m_src": m_src, "m_dst_epa": m_epa, "m_dst": m_dst,
                            "wape": wape, "wp": wp, "sat_ref": sat_ref, "sat_tgt": sat_tgt,
                            "jaccard": jaccard_d
                        })

            if current_epa_mult != 1.0:
                ffi_wrapper.modif_multiplicateur(self.projet, 1.0 / current_epa_mult)

            self.status_label.config(text=f"Analyse terminée ({total_iters} points).")
            self.update_plot()

        except Exception as e:
            messagebox.showerror("Erreur lors de l'analyse", str(e))

    def on_pick(self, event):
        if not hasattr(self, 'current_file') or not self.current_file:
            return

        ind = event.ind[0]
        res = self.results[ind]

        msg = f"Voulez-vous visualiser ce scénario en détail ?\n\nMult. Demande (EPANET) : {res['m_dst_epa']:.2f}\nMult. Source : {res['m_src']:.2f}\nMult. Dest (Algo) : {res['m_dst']:.2f}"
        if not messagebox.askyesno("Visualisation Croisée", msg):
            return

        from src.interface.visualisation import InternalWindow

        def spawn_visualizer(title, algo, ori):
            win = InternalWindow(self.app_manager.workspace, self.app_manager, title=title)
            self.app_manager.windows.append(win)
            win.load_file(self.current_file)

            win.algo_var.set(algo)
            win.ori_var.set(ori)

            win.inputs["Mult. Demande"].delete(0, tk.END)
            win.inputs["Mult. Demande"].insert(0, str(res["m_dst_epa"]))
            
            win.inputs["Vit. Rés (m/min)"].delete(0, tk.END)
            win.inputs["Vit. Rés (m/min)"].insert(0, self.v_res.get())
            
            win.inputs["Vit. Arcs (m/min)"].delete(0, tk.END)
            win.inputs["Vit. Arcs (m/min)"].insert(0, self.v_arc.get())
            
            win.inputs["Prop. Source"].delete(0, tk.END)
            win.inputs["Prop. Source"].insert(0, str(res["m_src"]))
            
            win.inputs["Prop. Demande"].delete(0, tk.END)
            win.inputs["Prop. Demande"].insert(0, str(res["m_dst"]))
            
            win.trigger_run()
            return win

        win_tgt = spawn_visualizer(f"Cible: {self.tgt_algo.get()}", self.tgt_algo.get(), self.tgt_ori.get())

    def update_plot(self, event=None):
        if not self.results:
            return

        x_k = self.keys_map[self.x_var.get()]
        y_k = self.keys_map[self.y_var.get()]

        x_data = [r[x_k] for r in self.results]
        y_data = [r[y_k] for r in self.results]

        self.fig.clf()
        self.ax = self.fig.add_subplot(111)

        c_selection = self.c_var.get()
        
        if c_selection == "Aucune":
            self.ax.scatter(x_data, y_data, color='#3498db', edgecolors='black', alpha=0.8, s=60, picker=5)
        else:
            c_k = self.keys_map[c_selection]
            c_data = [r[c_k] for r in self.results]

            sc = self.ax.scatter(x_data, y_data, c=c_data, cmap='viridis', edgecolors='black', alpha=0.8, s=60, picker=5)
            cbar = self.fig.colorbar(sc, ax=self.ax)
            cbar.set_label(c_selection, fontsize=9)

        self.ax.set_xlabel(self.x_var.get(), fontweight='bold')
        self.ax.set_ylabel(self.y_var.get(), fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        
        self.fig.tight_layout()
        self.canvas.draw()