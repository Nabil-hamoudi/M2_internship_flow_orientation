import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src.wrapper_tools import ffi_wrapper
from src.wrapper_tools import analyse_tools
from src.creation_dataset import prepare_dataset
import numpy as np
import random
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os


SOURCEDEST = ("Ford-Fulkerson", "Edmonds-Karp")
ALGO = ("EPANET", "Ford-Fulkerson", "Edmonds-Karp")
ORIEN = ("Aucune", "EPANET", "EPANET Partiel", "Ford-Fulkerson", "Edmonds-Karp")
CAPACITE = ("Vitesse Max", "EPANET", "EPANET Partiel", "Ford-Fulkerson", "Edmonds-Karp")
DEMANDE = ("Uniforme", "EPANET")


class AnalysisWindow(tk.Frame):
    def __init__(self, parent, app_manager):
        super().__init__(parent, bg="white", bd=2, relief="groove")
        self.app_manager = app_manager
        self.projet = None
        self.loaded_files = []
        self.results = []
        self.file_vars = {}  
        self.rand_vars = {}

        self.prep_dir = os.path.join(os.getcwd(), "prepared_datasets")
        os.makedirs(self.prep_dir, exist_ok=True)

        self.keys_map = {
            "Réf - Mult. Source": "ref_m_src",
            "Réf - Mult. Dest. (EPA)": "ref_m_epa",
            "Réf - Mult. Dest. (Algo)": "ref_m_dst",
            "Réf - Vitesse": "ref_vitesse",
            "Réf - Portion": "ref_portion",
            "Cible - Mult. Source": "tgt_m_src",
            "Cible - Mult. Dest. (EPA)": "tgt_m_epa",
            "Cible - Mult. Dest. (Algo)": "tgt_m_dst",
            "Cible - Vitesse": "tgt_vitesse",
            "Cible - Portion": "tgt_portion",
            "Satisfaisabilité Réf (%)": "sat_ref",
            "Satisfaisabilité Cible (%)": "sat_tgt",
            "Erreur Absolue ponderee (WAPE %)": "wape",
            "Erreur ponderee (%)": "wp",
            "Distance de Jaccard (%)": "jaccard",
            "Portion Arcs Flow Nul Réf (%)": "arc_nul_ref",
            "Portion Arcs Flow Non Nul Réf (%)": "arc_non_nul_ref",
            "Portion Arcs Flow Nul Cible (%)": "arc_nul_cible",
            "Portion Arcs Flow Non Nul Cible (%)": "arc_non_nul_cible",
            "Liens mal non orientés (%)": "ratio_nul_tgt_ref",
            "Liens mal orientés (%)": "ratio_inter_ref"
        }

        self.setup_ui()
        self.setup_bindings()
        self.place(x=100, y=100, width=1100, height=750)
        self.set_focus()

    def create_grid_ui(self, parent):
        grid = tk.Frame(parent, bg="#ecf0f1")
        grid.pack(fill=tk.X, pady=2)
        tk.Label(grid, text="Min", bg="#ecf0f1", width=5).grid(row=0, column=1)
        tk.Label(grid, text="Max", bg="#ecf0f1", width=5).grid(row=0, column=2)
        tk.Label(grid, text="Nb", bg="#ecf0f1", width=4).grid(row=0, column=3)

        ranges = {}
        params = [
            ("m_src", "M.Src", "1.0", "1.0", "1"),
            ("m_dst_epa", "M.Dst(E)", "1.0", "1.0", "1"),
            ("m_dst", "M.Dst(A)", "1.0", "1.0", "1"),
            ("vitesse", "Vitesse", "2.0", "2.0", "1"),
            ("portion", "Portion", "1.0", "1.0", "1")
        ]
        for i, (key, label, d_min, d_max, d_n) in enumerate(params):
            tk.Label(grid, text=label, bg="#ecf0f1", anchor="w", font=("Segoe UI", 8)).grid(row=i+1, column=0, sticky="w")
            ent_min, ent_max, ent_n = tk.Entry(grid, width=5), tk.Entry(grid, width=5), tk.Entry(grid, width=4)
            ent_min.insert(0, d_min)
            ent_max.insert(0, d_max)
            ent_n.insert(0, d_n)
            ent_min.grid(row=i+1, column=1, padx=2, pady=1)
            ent_max.grid(row=i+1, column=2, padx=2)
            ent_n.grid(row=i+1, column=3, padx=2)
            ranges[key] = (ent_min, ent_max, ent_n)
        return ranges

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

        self.sidebar_container = tk.Frame(main_content, width=280, bg="#ecf0f1", relief="solid", bd=1)
        self.sidebar_container.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_container.pack_propagate(False)

        self.canvas_side = tk.Canvas(self.sidebar_container, bg="#ecf0f1", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.sidebar_container, orient="vertical", command=self.canvas_side.yview)
        
        self.sidebar = tk.Frame(self.canvas_side, bg="#ecf0f1", padx=10, pady=10)
        self.sidebar.bind("<Configure>", lambda e: self.canvas_side.configure(scrollregion=self.canvas_side.bbox("all")))
        self.canvas_side.create_window((0, 0), window=self.sidebar, anchor="nw", width=260)
        self.canvas_side.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _on_mousewheel_analyse(event):
            if event.num == 4 or getattr(event, 'delta', 0) > 0:
                self.canvas_side.yview_scroll(-1, "units")
            elif event.num == 5 or getattr(event, 'delta', 0) < 0:
                self.canvas_side.yview_scroll(1, "units")

        def _bind_scroll_analyse(e):
            self.sidebar_container.bind_all("<MouseWheel>", _on_mousewheel_analyse)
            self.sidebar_container.bind_all("<Button-4>", _on_mousewheel_analyse)
            self.sidebar_container.bind_all("<Button-5>", _on_mousewheel_analyse)

        def _unbind_scroll_analyse(e):
            self.sidebar_container.unbind_all("<MouseWheel>")
            self.sidebar_container.unbind_all("<Button-4>")
            self.sidebar_container.unbind_all("<Button-5>")

        self.sidebar_container.bind("<Enter>", _bind_scroll_analyse)
        self.sidebar_container.bind("<Leave>", _unbind_scroll_analyse)

        btn_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        self.btn_load_files = tk.Button(btn_frame, text="Ajouter & Préparer Fichier(s)", command=self.load_files, bg="#2ecc71", fg="black", font=("Segoe UI", 8, "bold"))
        self.btn_load_files.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        
        self.btn_load_dir = tk.Button(btn_frame, text="Ajouter & Préparer Dossier", command=self.load_directory, bg="#2ecc71", fg="black", font=("Segoe UI", 8, "bold"))
        self.btn_load_dir.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        self.files_frame = tk.Frame(self.sidebar, bg="white", relief="sunken", bd=1)
        self.files_frame.pack(fill=tk.X, pady=(0, 5))

        self.hyd_f = tk.LabelFrame(self.sidebar, text="Préparation Hydraulique (EPANET)", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.hyd_f.pack(fill=tk.X, pady=(0, 10))

        self.sim_mode = tk.StringVar(value="PDA")
        tk.Radiobutton(self.hyd_f, text="Mode PDA", variable=self.sim_mode, value="PDA", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w", padx=5)
        tk.Radiobutton(self.hyd_f, text="Mode DDA", variable=self.sim_mode, value="DDA", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w", padx=5)

        param_f = tk.Frame(self.hyd_f, bg="#ecf0f1")
        param_f.pack(fill=tk.X, pady=2, padx=5)

        tk.Label(param_f, text="P. Min:", bg="#ecf0f1", font=("Segoe UI", 7)).grid(row=0, column=0)
        self.p_min_ent = tk.Entry(param_f, width=5)
        self.p_min_ent.insert(0, "0.0")
        self.p_min_ent.grid(row=0, column=1)
        
        tk.Label(param_f, text="P. Req:", bg="#ecf0f1", font=("Segoe UI", 7)).grid(row=0, column=2, padx=(5,0))
        self.p_req_ent = tk.Entry(param_f, width=5)
        self.p_req_ent.insert(0, "10.0")
        self.p_req_ent.grid(row=0, column=3)
        
        tk.Label(param_f, text="P. Exp:", bg="#ecf0f1", font=("Segoe UI", 7)).grid(row=1, column=0, pady=2)
        self.p_exp_ent = tk.Entry(param_f, width=5)
        self.p_exp_ent.insert(0, "0.5")
        self.p_exp_ent.grid(row=1, column=1, pady=2)

        exclude_f = tk.LabelFrame(self.sidebar, text="Filtres d'exclusion et conditions", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        exclude_f.pack(fill=tk.X, pady=(0, 10))
        self.exclude_tanks = tk.BooleanVar(value=False)
        self.exclude_pumps = tk.BooleanVar(value=False)
        self.exclude_valves = tk.BooleanVar(value=False)
        
        tk.Checkbutton(exclude_f, text="Exclure si Bassins (Tanks)", variable=self.exclude_tanks, bg="#ecf0f1", font=("Segoe UI", 8), anchor="w", command=self.update_plot).pack(fill=tk.X, padx=5)
        tk.Checkbutton(exclude_f, text="Exclure si Pompes (Pumps)", variable=self.exclude_pumps, bg="#ecf0f1", font=("Segoe UI", 8), anchor="w", command=self.update_plot).pack(fill=tk.X, padx=5)
        tk.Checkbutton(exclude_f, text="Exclure si Vannes (Valves)", variable=self.exclude_valves, bg="#ecf0f1", font=("Segoe UI", 8), anchor="w", command=self.update_plot).pack(fill=tk.X, padx=5)

        res_count_f = tk.Frame(exclude_f, bg="#ecf0f1")
        res_count_f.pack(fill=tk.X, padx=5, pady=(5, 5))
        tk.Label(res_count_f, text="Nb. Réservoirs (Min-Max):", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.min_res_ent = tk.Entry(res_count_f, width=4)
        self.min_res_ent.insert(0, "1")
        self.min_res_ent.pack(side=tk.LEFT, padx=2)
        self.max_res_ent = tk.Entry(res_count_f, width=4)
        self.max_res_ent.insert(0, "1")
        self.max_res_ent.pack(side=tk.LEFT, padx=2)
        
        self.min_res_ent.bind("<KeyRelease>", self.update_plot)
        self.max_res_ent.bind("<KeyRelease>", self.update_plot)

        self.rand_f = tk.LabelFrame(self.sidebar, text="Scénarios de Randomisation", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.rand_f.pack(fill=tk.X, pady=(5, 5))

        self.run_base_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.rand_f, text="Fichier Base (Aucune)", variable=self.run_base_var, bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w", padx=5)

        self.run_all_one_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.rand_f, text="Dems = 1 (Toutes à 1)", variable=self.run_all_one_var, bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w", padx=5)

        def make_rand_entry(parent, label, default="0"):
            f = tk.Frame(parent, bg="#ecf0f1")
            f.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(f, text=label, bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
            ent = tk.Entry(f, width=5)
            ent.insert(0, default)
            ent.pack(side=tk.RIGHT)
            return ent

        self.nb_rand_uni = make_rand_entry(self.rand_f, "Nb. Uniforme :")
        self.nb_rand_norm = make_rand_entry(self.rand_f, "Nb. Normale :")
        self.nb_rand_exp = make_rand_entry(self.rand_f, "Nb. Exponentielle :")

        # --- MODÈLE RÉFÉRENCE ---
        self.ref_f = tk.LabelFrame(self.sidebar, text="Modèle de Référence", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.ref_f.pack(fill=tk.X, pady=5)
        
        tk.Label(self.ref_f, text="Algo:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_algo = tk.StringVar(value="EPANET")
        ttk.Combobox(self.ref_f, textvariable=self.ref_algo, values=ALGO, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(self.ref_f, text="Demande:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_dem = tk.StringVar(value="Uniforme")
        ttk.Combobox(self.ref_f, textvariable=self.ref_dem, values=DEMANDE, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(self.ref_f, text="Capacite:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_capa = tk.StringVar(value="Vitesse Max")
        ttk.Combobox(self.ref_f, textvariable=self.ref_capa, values=CAPACITE, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(self.ref_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_ori = tk.StringVar(value="Aucune")
        ttk.Combobox(self.ref_f, textvariable=self.ref_ori, values=ORIEN, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(self.ref_f, text="Balayage Réf", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5,0))
        self.ref_ranges = self.create_grid_ui(self.ref_f)

        # --- MODÈLES CIBLES ---
        self.targets_container = tk.Frame(self.sidebar, bg="#ecf0f1")
        self.targets_container.pack(fill=tk.X, pady=5)
        
        self.target_counter = 0
        self.target_ui_rows = []
        self.target_configs = []

        self.btn_add_target = tk.Button(self.sidebar, text="➕ Ajouter un Modèle Cible", bg="#f39c12", font=("Segoe UI", 8, "bold"), command=self.add_target_ui)
        self.btn_add_target.pack(fill=tk.X, pady=(0, 5))
        
        self.add_target_ui()

        # --- FILTRES DE RÉSULTATS (POST-RUN) ---
        self.targets_list_frame = tk.LabelFrame(self.sidebar, text="Afficher/Masquer les Cibles", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.targets_list_frame.pack(fill=tk.X, pady=(0, 5))

        self.rand_filter_frame = tk.LabelFrame(self.sidebar, text="Afficher/Masquer Randomisations", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.rand_filter_frame.pack(fill=tk.X, pady=(0, 5))

        self.run_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        self.run_frame.pack(fill=tk.X, pady=10)

        self.btn_run = tk.Button(self.run_frame, text="Lancer l'Analyse", bg="#2980b9", fg="white", font=("Segoe UI", 9, "bold"), command=self.run_analysis)
        self.btn_run.pack(fill=tk.X, pady=(0, 5))

        self.btn_reset = tk.Button(self.run_frame, text="Réinitialiser & Déverrouiller", bg="#e74c3c", fg="white", font=("Segoe UI", 9, "bold"), command=self.reset_analysis)

        # --- TRACÉ MATPLOTLIB ---
        tk.Label(self.sidebar, text="Tracé du Graphe", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        plot_opts = list(self.keys_map.keys())

        tk.Label(self.sidebar, text="Type :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.plot_type_var = tk.StringVar(value="Nuage de points")
        self.cb_type = ttk.Combobox(self.sidebar, textvariable=self.plot_type_var, values=["Nuage de points", "Histogramme (1D)", "Carte de chaleur (2D)"], state="readonly")
        self.cb_type.pack(fill=tk.X, pady=(0, 5))
        self.cb_type.bind("<<ComboboxSelected>>", self.update_plot)
        
        tk.Label(self.sidebar, text="Axe X :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.x_var = tk.StringVar(value="Cible - Mult. Dest. (EPA)")
        self.cb_x = ttk.Combobox(self.sidebar, textvariable=self.x_var, values=plot_opts, state="readonly")
        self.cb_x.pack(fill=tk.X); self.cb_x.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Axe Y :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.y_var = tk.StringVar(value="Satisfaisabilité Cible (%)")
        self.cb_y = ttk.Combobox(self.sidebar, textvariable=self.y_var, values=plot_opts, state="readonly")
        self.cb_y.pack(fill=tk.X); self.cb_y.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Paramètre / Couleur :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.c_var = tk.StringVar(value="Cibles")
        self.cb_c = ttk.Combobox(self.sidebar, textvariable=self.c_var, values=["Cibles", "Fichiers"] + plot_opts, state="readonly")
        self.cb_c.pack(fill=tk.X); self.cb_c.bind("<<ComboboxSelected>>", self.update_plot)

        bins_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        bins_f.pack(fill=tk.X, pady=5)
        tk.Label(bins_f, text="Nb divisions (Barres/Grille):", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.bins_var = tk.Entry(bins_f, width=5)
        self.bins_var.insert(0, "15")
        self.bins_var.pack(side=tk.RIGHT, padx=5)
        self.bins_var.bind("<Return>", self.update_plot)

        # --- LIGNES STATISTIQUES ---
        tk.Label(self.sidebar, text="Statistiques", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 0))
        
        stat_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        stat_f.pack(fill=tk.X, pady=2)
        
        self.show_mean_y_var = tk.BooleanVar(value=False)
        self.show_median_y_var = tk.BooleanVar(value=False)
        self.show_mean_x_var = tk.BooleanVar(value=False)
        self.show_median_x_var = tk.BooleanVar(value=False)
        
        self.chk_mean_y = tk.Checkbutton(stat_f, text="Moy. Y", variable=self.show_mean_y_var, bg="#ecf0f1", font=("Segoe UI", 8), command=self.update_plot)
        self.chk_mean_y.grid(row=0, column=0, sticky="w")
        self.chk_median_y = tk.Checkbutton(stat_f, text="Méd. Y", variable=self.show_median_y_var, bg="#ecf0f1", font=("Segoe UI", 8), command=self.update_plot)
        self.chk_median_y.grid(row=0, column=1, sticky="w")
        self.chk_mean_x = tk.Checkbutton(stat_f, text="Moy. X", variable=self.show_mean_x_var, bg="#ecf0f1", font=("Segoe UI", 8), command=self.update_plot)
        self.chk_mean_x.grid(row=1, column=0, sticky="w")
        self.chk_median_x = tk.Checkbutton(stat_f, text="Méd. X", variable=self.show_median_x_var, bg="#ecf0f1", font=("Segoe UI", 8), command=self.update_plot)
        self.chk_median_x.grid(row=1, column=1, sticky="w")

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
        self.scatters = []

        self.status_bar = tk.Frame(self, bg="#bdc3c7", height=20)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(self.status_bar, text="Prêt", bg="#bdc3c7", font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.grip = tk.Label(self.status_bar, text="◢", bg="#bdc3c7", fg="#7f8c8d", cursor="bottom_right_corner")
        self.grip.pack(side=tk.RIGHT, anchor="se", padx=2)

    def _set_state(self, widget, freeze):
        state = tk.DISABLED if freeze else tk.NORMAL
        
        if isinstance(widget, ttk.Combobox):
            widget.configure(state=tk.DISABLED if freeze else "readonly")
        elif isinstance(widget, (tk.Entry, tk.Button, tk.Radiobutton, tk.Checkbutton)):
            widget.configure(state=state)
            
        for child in widget.winfo_children():
            self._set_state(child, freeze)

    def freeze_ui(self, freeze=True):
        state = tk.DISABLED if freeze else tk.NORMAL
        
        self.btn_load_files.config(state=state)
        self.btn_load_dir.config(state=state)
        self.btn_run.config(state=state)
        self.btn_add_target.config(state=state)
        
        if freeze:
            self.btn_reset.pack(fill=tk.X, pady=(0, 5))
        else:
            self.btn_reset.pack_forget()

        self._set_state(self.hyd_f, freeze)
        self._set_state(self.rand_f, freeze)
        self._set_state(self.ref_f, freeze)

        for row in self.target_ui_rows:
            row['btn_delete'].config(state=state)
            for child in row['frame'].winfo_children():
                if child != row['header_f']:
                    self._set_state(child, freeze)

    def reset_analysis(self):
        self.results = []
        for widget in self.rand_filter_frame.winfo_children():
            widget.destroy()
        self.rand_vars.clear()
        
        self.freeze_ui(False)
        self.update_plot()
        self.status_label.config(text="Analyse réinitialisée. Prêt pour de nouvelles modifications.")

    def add_target_ui(self):
        self.target_counter += 1
        current_uid = self.target_counter

        tgt_f = tk.LabelFrame(self.targets_container, text=f"Modèle Cible {len(self.target_ui_rows)+1}", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        tgt_f.pack(fill=tk.X, pady=5)

        header_f = tk.Frame(tgt_f, bg="#ecf0f1")
        header_f.pack(fill=tk.X, padx=5, pady=(2, 5))

        var = tk.BooleanVar(value=True)
        tk.Checkbutton(header_f, text="Afficher", variable=var, bg="#ecf0f1", font=("Segoe UI", 8, "bold"), fg="#27ae60", command=self.update_plot).pack(side=tk.LEFT)

        def remove_self():
            tgt_f.destroy()
            self.target_ui_rows = [r for r in self.target_ui_rows if r['uid'] != current_uid]
            if hasattr(self, 'target_configs'):
                self.target_configs = [c for c in self.target_configs if c['uid'] != current_uid]
            self.update_plot()

            for i, r in enumerate(self.target_ui_rows):
                r['frame'].config(text=f"Modèle Cible {i+1}")

        btn_del = tk.Button(header_f, text="❌", fg="red", bg="#ecf0f1", bd=0, font=("Segoe UI", 8), command=remove_self)
        btn_del.pack(side=tk.RIGHT)

        tk.Label(tgt_f, text="Algo:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        algo_var = tk.StringVar(value="Edmonds-Karp")
        ttk.Combobox(tgt_f, textvariable=algo_var, values=ALGO, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(tgt_f, text="Demande:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        dem_var = tk.StringVar(value="Uniforme")
        ttk.Combobox(tgt_f, textvariable=dem_var, values=DEMANDE, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(tgt_f, text="Capacite:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        capa_var = tk.StringVar(value="Vitesse Max")
        ttk.Combobox(tgt_f, textvariable=capa_var, values=CAPACITE, state="readonly").pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(tgt_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        ori_var = tk.StringVar(value="Aucune")
        ttk.Combobox(tgt_f, textvariable=ori_var, values=ORIEN, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))
        
        tk.Label(tgt_f, text="Balayage Cible", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5,0))
        ranges = self.create_grid_ui(tgt_f)

        self.target_ui_rows.append({
            'frame': tgt_f, 'header_f': header_f, 'btn_delete': btn_del, 'algo': algo_var, 'dem': dem_var, 'capa': capa_var, 'ori': ori_var, 'var': var, 'uid': current_uid, 'ranges': ranges
        })

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
        if self.projet:
            ffi_wrapper.free_project(self.projet)
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

    def _prepare_and_load(self, raw_paths):
        mode = self.sim_mode.get()
        try:
            p_min = float(self.p_min_ent.get())
            p_req = float(self.p_req_ent.get())
            p_exp = float(self.p_exp_ent.get())
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides pour les pressions.")
            return

        self.status_label.config(text="Préparation des fichiers en cours...")
        self.update_idletasks()

        count = 0
        for p in raw_paths:
            wn = prepare_dataset.open_file_epa_int(p)
            if wn:
                prepare_dataset.convertir_unites(wn, 'LPS')
                prepare_dataset.change_mode(wn, mode, p_min, p_req, p_exp)

                base_name = os.path.basename(p)
                unique_name = f"prep_{len(self.loaded_files)}_{base_name}"
                dest_path = os.path.join(self.prep_dir, unique_name)

                if prepare_dataset.write_file(wn, dest_path):
                    if dest_path not in self.loaded_files:
                        self.loaded_files.append(dest_path)
                        
                        var = tk.BooleanVar(value=True)
                        self.file_vars[dest_path] = var
                        cb = tk.Checkbutton(self.files_frame, text=unique_name, variable=var, bg="white", font=("Segoe UI", 7), anchor="w", command=self.update_plot)
                        cb.pack(fill=tk.X)
                        
                        count += 1

        self.title_label.config(text=f"|  Analyse : {len(self.loaded_files)} fichier(s)")
        self.status_label.config(text=f"{count} fichier(s) préparé(s) dans le dossier séparé.")
        if count > 0:
            messagebox.showinfo("Succès", f"{count} fichier(s) converti(s) en {mode} et ajouté(s) à la liste d'analyse.\n(Stockés dans : {self.prep_dir})")

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            paths_to_prepare = []
            try:
                for root, dirs, files in os.walk(directory):
                    if os.path.abspath(self.prep_dir) == os.path.abspath(root):
                        continue

                    for file in files:
                        if file.lower().endswith('.inp'):
                            paths_to_prepare.append(os.path.normpath(os.path.join(root, file)))

                if paths_to_prepare:
                    self._prepare_and_load(paths_to_prepare)
                else:
                    messagebox.showinfo("Info", "Aucun fichier .inp trouvé dans le dossier sélectionné.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de lire l'arborescence : {str(e)}")

    def load_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("EPANET", "*.inp *.INP")])
        if paths:
            self._prepare_and_load(paths)

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

    def compute_orientation(self, reseau, choix_ori, p_src, p_dem, portion=1.0):
        match (choix_ori):
            case "EPANET":
                ffi_wrapper.reget_epanet_flow(self.projet, reseau)
                ffi_wrapper.fix_capacite_flow_oriente(reseau)
            case "EPANET Partiel":
                ffi_wrapper.reget_epanet_flow(self.projet, reseau)
                ffi_wrapper.fix_capacite_flow_oriente_portion(reseau, portion)
            case "Aucune":
                pass
            case _:
                self.compute_algo(reseau, choix_ori, p_src, p_dem)
                ffi_wrapper.fix_capacite_flow_oriente(reseau)

    def compute_network(self, choix_algo, choix_ori, choix_capa, choix_dem, p_src, p_dem, vitesse, portion=1.0):
        reseau = None

        if choix_algo == "EPANET":
            ffi_wrapper.compute_epanet(self.projet)
            reseau = ffi_wrapper.import_epanet_graph(self.projet)
        else:            
            besoin_epanet = (choix_dem == "EPANET") or (choix_capa in ["EPANET", "EPANET Partiel"]) or (choix_ori  in ["EPANET", "EPANET Partiel"])
            if besoin_epanet:
                ffi_wrapper.compute_epanet(self.projet)

            reseau = ffi_wrapper.import_epanet_graph(self.projet)

            if choix_dem == "EPANET":
                ffi_wrapper.get_epanet_demande(self.projet, reseau)

            match (choix_capa):
                case "EPANET":
                    ffi_wrapper.reget_epanet_flow(self.projet, reseau)
                    ffi_wrapper.fix_capacite_flow_calcule(reseau)
                case "EPANET Partiel":
                    ffi_wrapper.reget_epanet_flow(self.projet, reseau)
                    ffi_wrapper.fix_capacite_flow(reseau, vitesse, vitesse)
                    ffi_wrapper.fix_capacite_flow_calcule_portion(reseau, portion)
                case "Vitesse Max":
                    ffi_wrapper.fix_capacite_flow(reseau, vitesse, vitesse)
                case _:
                    ffi_wrapper.fix_capacite_flow(reseau, vitesse, vitesse)
                    self.compute_algo(reseau, choix_capa, p_src, p_dem)
                    ffi_wrapper.fix_capacite_flow_calcule(reseau)
                    ffi_wrapper.nullifier_flow(reseau)

            self.compute_orientation(reseau, choix_ori, p_src, p_dem, portion)
            self.compute_algo(reseau, choix_algo, p_src, p_dem)
            if choix_dem == "EPANET":
                ffi_wrapper.get_epanet_fulldemande(self.projet, reseau)

        return reseau

    def _extract_grid(self, ranges):
        def safe_float(v, default=1.0):
            try: return float(v.get())
            except: return default
        def safe_int(v, default=1):
            try: return max(1, int(v.get()))
            except: return default

        return {
            "m_src": np.linspace(safe_float(ranges["m_src"][0]), safe_float(ranges["m_src"][1]), safe_int(ranges["m_src"][2])),
            "m_epa": np.linspace(safe_float(ranges["m_dst_epa"][0]), safe_float(ranges["m_dst_epa"][1]), safe_int(ranges["m_dst_epa"][2])),
            "m_dst": np.linspace(safe_float(ranges["m_dst"][0]), safe_float(ranges["m_dst"][1]), safe_int(ranges["m_dst"][2])),
            "vitesse": np.linspace(safe_float(ranges["vitesse"][0], 2.0), safe_float(ranges["vitesse"][1], 2.0), safe_int(ranges["vitesse"][2])),
            "portion": np.linspace(safe_float(ranges["portion"][0], 1.0), safe_float(ranges["portion"][1], 1.0), safe_int(ranges["portion"][2]))
        }

    def _extract_analysis_params(self):
        self.target_configs = []
        for i, row in enumerate(self.target_ui_rows):
            name = f"C{i+1}: {row['algo'].get()[:4]} | O:{row['ori'].get()[:4]} | C:{row['capa'].get()[:4]}"
            self.target_configs.append({
                "uid": row['uid'], "name": name,
                "algo": row['algo'].get(), "ori": row['ori'].get(),
                "capa": row['capa'].get(), "dem": row['dem'].get(),
                "var": row['var'],
                "grid": self._extract_grid(row['ranges'])
            })

        randomizations = []
        if self.run_base_var.get():
            randomizations.append(("Aucune", None))
        if self.run_all_one_var.get():
            randomizations.append(("Toutes à 1", None))
            
        def parse_nb(ent):
            try: return max(0, int(ent.get()))
            except ValueError: return 0

        nb_uni = parse_nb(self.nb_rand_uni)
        nb_norm = parse_nb(self.nb_rand_norm)
        nb_exp = parse_nb(self.nb_rand_exp)

        MAX_SEED = 4294967295
        for _ in range(nb_uni): randomizations.append(("Uniforme", random.randint(1, MAX_SEED)))
        for _ in range(nb_norm): randomizations.append(("Normale", random.randint(1, MAX_SEED)))
        for _ in range(nb_exp): randomizations.append(("Exponentielle", random.randint(1, MAX_SEED)))

        return {
            "ref_algo": self.ref_algo.get(),
            "ref_capa": self.ref_capa.get(),
            "ref_ori": self.ref_ori.get(),
            "ref_dem": self.ref_dem.get(),
            "ref_grid": self._extract_grid(self.ref_ranges),
            "randomizations": randomizations,
            "targets": self.target_configs
        }

    def _compute_metrics(self, graph_ref, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt, 
                         r_src, r_epa, r_dst, r_v, r_p, 
                         t_src, t_epa, t_dst, t_v, t_p):
        wape = analyse_tools.get_wape_flow(graph_ref, graph_tgt) * 100
        wp = analyse_tools.get_wp_flow(graph_ref, graph_tgt) * 100
        sat_ref = float(analyse_tools.get_efficacite(graph_ref)) * 100
        sat_tgt = float(analyse_tools.get_efficacite(graph_tgt)) * 100
        jaccard_d = analyse_tools.jaccard_distance(graph_ref, graph_tgt) * 100
        
        arcs_non_nul_ref = (analyse_tools.get_n_arcs_non_nul(graph_ref) / max(1, analyse_tools.get_n_arcs_no(graph_ref))) * 100
        arcs_nul_ref = analyse_tools.extraire_arcs_nulles(graph_ref)
        arcs_non_nul_tgt = (analyse_tools.get_n_arcs_non_nul(graph_tgt) / max(1, analyse_tools.get_n_arcs_no(graph_tgt))) * 100
        arcs_nul_tgt = analyse_tools.extraire_arcs_nulles(graph_tgt)
        
        nb_dom_ref = analyse_tools.get_n_arcs_non_nul(graph_ref)
        nb_inter_dom = analyse_tools.get_intersection_arcs_dominants(graph_ref, graph_tgt).shape[0]
        nb_inter_nul = np.intersect1d(arcs_nul_ref, arcs_nul_tgt).shape[0]

        return {
            "filepath": filepath, "filename": filename, "rand_type": rand_type, "seed": seed_val,
            "target_uid": tgt['uid'], "target_name": tgt['name'], "flags": flags,
            "ref_m_src": r_src, "ref_m_epa": r_epa, "ref_m_dst": r_dst, "ref_vitesse": r_v, "ref_portion": r_p,
            "tgt_m_src": t_src, "tgt_m_epa": t_epa, "tgt_m_dst": t_dst, "tgt_vitesse": t_v, "tgt_portion": t_p,
            "wape": wape, "wp": wp, "sat_ref": sat_ref, "sat_tgt": sat_tgt,
            "jaccard": jaccard_d,  
            "arc_nul_ref": arcs_nul_ref.shape[0] / max(1, analyse_tools.get_n_arcs_no(graph_ref)) * 100,
            "arc_non_nul_ref" : arcs_non_nul_ref, 
            "arc_nul_cible": arcs_nul_tgt.shape[0] / max(1, analyse_tools.get_n_arcs_no(graph_tgt)) * 100,
            "arc_non_nul_cible": arcs_non_nul_tgt,
            "ratio_nul_tgt_ref": ((nb_inter_nul / nb_dom_ref) * 100) if nb_dom_ref > 0 else 1.0,
            "ratio_inter_ref": ((nb_inter_dom / nb_dom_ref) * 100) if nb_dom_ref > 0 else 1.0
        }

    def run_analysis(self):
        if not self.loaded_files:
            messagebox.showinfo("Info", "Veuillez charger au moins un fichier .inp d'abord.")
            return
        if not self.target_ui_rows:
            messagebox.showinfo("Info", "Veuillez ajouter au moins un modèle cible.")
            return

        params = self._extract_analysis_params()
        self.results = []
        
        ref_grid = params['ref_grid']
        ref_iters = len(ref_grid["m_epa"]) * len(ref_grid["m_dst"]) * len(ref_grid["m_src"]) * len(ref_grid["vitesse"]) * len(ref_grid["portion"])
        tgt_iters = sum([len(t['grid']["m_epa"]) * len(t['grid']["m_dst"]) * len(t['grid']["m_src"]) * len(t['grid']["vitesse"]) * len(t['grid']["portion"]) for t in params['targets']])
        
        total_iters = len(self.loaded_files) * len(params['randomizations']) * ref_iters * tgt_iters
        current_iter = 0

        file_flags = {filepath: prepare_dataset.file_contains_elements(filepath) for filepath in self.loaded_files}

        try:
            for filepath in self.loaded_files:
                filename = os.path.basename(filepath)
                flags = file_flags[filepath]
                print(filename)
                for rand_type, seed_val in params['randomizations']:
                    self.projet = ffi_wrapper.create_epanet_project(filepath)

                    if seed_val is not None:
                        ffi_wrapper.set_random_seed(seed_val)
                    
                    if rand_type == "Uniforme":
                        ffi_wrapper.randomise_demande(self.projet)
                    elif rand_type == "Normale":
                        ffi_wrapper.randomise_demande_normale(self.projet)
                    elif rand_type == "Exponentielle":
                        ffi_wrapper.randomise_demande_exponentielle(self.projet)
                    elif rand_type == "Toutes à 1":
                        ffi_wrapper.set_demande_un(self.projet)

                    for r_epa in ref_grid["m_epa"]:
                        ffi_wrapper.modif_multiplicateur(self.projet, max(r_epa, 1e-6))
                        for r_dst in ref_grid["m_dst"]:
                            for r_src in ref_grid["m_src"]:
                                for r_v in ref_grid["vitesse"]:
                                    for r_p in ref_grid["portion"]:

                                        if params['ref_algo'] == "EPANET":
                                            graph_ref = self.compute_network(params['ref_algo'], params['ref_ori'], params['ref_capa'], params['ref_dem'], 1.0, 1.0, r_v, r_p)
                                        else:
                                            graph_ref = self.compute_network(params['ref_algo'], params['ref_ori'], params['ref_capa'], params['ref_dem'], r_src, r_dst, r_v, r_p)

                                        for tgt in params['targets']:
                                            t_grid = tgt['grid']
                                            for t_epa in t_grid["m_epa"]:
                                                ratio = max(t_epa, 1e-6) / max(r_epa, 1e-6)
                                                ffi_wrapper.modif_multiplicateur(self.projet, ratio)

                                                for t_dst in t_grid["m_dst"]:
                                                    for t_src in t_grid["m_src"]:
                                                        for t_v in t_grid["vitesse"]:
                                                            for t_p in t_grid["portion"]:
                                                                current_iter += 1
                                                                self.status_label.config(text=f"Calcul : {current_iter}/{total_iters} ...")
                                                                self.update_idletasks()

                                                                if tgt['algo'] == "EPANET":
                                                                    graph_tgt = self.compute_network(tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'], 1.0, 1.0, t_v, t_p)
                                                                else:
                                                                    graph_tgt = self.compute_network(tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'], t_src, t_dst, t_v, t_p)

                                                                metrics = self._compute_metrics(graph_ref, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt, 
                                                                                                r_src, r_epa, r_dst, r_v, r_p, 
                                                                                                t_src, t_epa, t_dst, t_v, t_p)
                                                                self.results.append(metrics)

                                                                ffi_wrapper.free_graph(graph_tgt)

                                                ffi_wrapper.modif_multiplicateur(self.projet, 1.0 / ratio)

                                        ffi_wrapper.free_graph(graph_ref)

                        ffi_wrapper.modif_multiplicateur(self.projet, 1.0 / max(r_epa, 1e-6))

                    ffi_wrapper.free_project(self.projet)
                    self.projet = None

            unique_rands = list(set([r.get('rand_type', 'Aucune') for r in self.results]))
            for widget in self.rand_filter_frame.winfo_children():
                widget.destroy()
            self.rand_vars.clear()
            
            for r_type in sorted(unique_rands):
                var = tk.BooleanVar(value=True)
                self.rand_vars[r_type] = var
                cb = tk.Checkbutton(self.rand_filter_frame, text=r_type, variable=var, bg="#ecf0f1", font=("Segoe UI", 8), anchor="w", command=self.update_plot)
                cb.pack(fill=tk.X, padx=5)

            self.status_label.config(text=f"Analyse terminée ({total_iters} simulations).")
            self.freeze_ui(True)
            self.update_plot()

        except Exception as e:
            if getattr(self, 'projet', None) is not None:
                ffi_wrapper.free_project(self.projet)
                self.projet = None
            messagebox.showerror("Erreur lors de l'analyse", str(e))

    def update_plot(self, event=None):
        if not hasattr(self, 'results') or not self.results:
            return

        plot_type = self.plot_type_var.get()
        
        if plot_type == "Histogramme (1D)":
            self.cb_y.config(state="disabled")
            self.cb_c.config(state="disabled")
            self.chk_mean_y.config(state="disabled")
            self.chk_median_y.config(state="disabled")
        else:
            self.cb_y.config(state="readonly")
            self.cb_c.config(state="readonly")
            self.chk_mean_y.config(state="normal")
            self.chk_median_y.config(state="normal")

        filtered_results = []
        try:
            min_res = int(self.min_res_ent.get()) if self.min_res_ent.get().strip() else 0
            max_res = int(self.max_res_ent.get()) if self.max_res_ent.get().strip() else 999999
        except ValueError:
            min_res, max_res = 0, 999999

        for r in self.results:
            # Vérifier si le fichier est coché dans la liste des Checkbuttons
            if r['filepath'] in self.file_vars and not self.file_vars[r['filepath']].get():
                continue

            r_type = r.get('rand_type', 'Aucune')
            if r_type in self.rand_vars and not self.rand_vars[r_type].get():
                continue

            flags = r['flags']
            
            tgt_config = next((c for c in self.target_configs if c['uid'] == r['target_uid']), None)
            if not tgt_config: continue
            if not tgt_config['var'].get(): continue 
            
            if self.exclude_tanks.get() and flags.get("tanks", False): continue
            if self.exclude_pumps.get() and flags.get("pumps", False): continue
            if self.exclude_valves.get() and flags.get("valves", False): continue
            if not (min_res <= flags.get("reservoir_count", 0) <= max_res): continue
            
            filtered_results.append(r)

        if not filtered_results:
            self.fig.clf()
            self.ax = self.fig.add_subplot(111)
            self.ax.text(0.5, 0.5, 'Aucune donnée correspondante\naux filtres actuels.', ha='center', va='center', color='red')
            self.canvas.draw()
            return

        x_k = self.keys_map[self.x_var.get()]
        y_k = self.keys_map.get(self.y_var.get(), None)
        plot_type = self.plot_type_var.get()

        try:
            nb_bins = int(self.bins_var.get())
            if nb_bins <= 0: nb_bins = 15
        except ValueError:
            nb_bins = 15

        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.scatters = []

        all_x_data = [r[x_k] for r in filtered_results]
        all_y_data = [r[y_k] for r in filtered_results] if y_k else []

        if plot_type == "Histogramme (1D)":
            self.ax.hist(all_x_data, bins=nb_bins, color='#3498db', edgecolor='black', alpha=0.8)
            self.ax.set_ylabel("Nombre de réseaux (Fréquence)", fontweight='bold')

        elif plot_type == "Carte de chaleur (2D)":
            c_selection = self.c_var.get()
            
            if c_selection in ["Cibles", "Fichiers", "Aucune"]:
                c_k = None
            else:
                c_k = self.keys_map.get(c_selection)

            H_count, xedges, yedges = np.histogram2d(all_x_data, all_y_data, bins=nb_bins)

            if c_k:
                c_data = [r[c_k] for r in filtered_results]
                H_sum, _, _ = np.histogram2d(all_x_data, all_y_data, bins=nb_bins, weights=c_data)

                with np.errstate(divide='ignore', invalid='ignore'):
                    Z = np.true_divide(H_sum, H_count)
            else:
                Z = H_count

            Z[H_count == 0] = np.nan

            im = self.ax.imshow(Z.T, cmap='plasma', aspect='auto', origin='lower')

            x_centers = (xedges[:-1] + xedges[1:]) / 2
            y_centers = (yedges[:-1] + yedges[1:]) / 2
            
            self.ax.set_xticks(np.arange(len(x_centers)))
            self.ax.set_yticks(np.arange(len(y_centers)))
            
            def format_label(val): return f"{val:.2f}"
            self.ax.set_xticklabels([format_label(v) for v in x_centers], rotation=45, ha='right', fontsize=8)
            self.ax.set_yticklabels([format_label(v) for v in y_centers], fontsize=8)
            
            cbar = self.fig.colorbar(im, ax=self.ax)
            cbar.set_label(f"Moyenne : {c_selection}" if c_k else "Densité (Nombre de réseaux)", fontsize=9)

        else:
            c_selection = self.c_var.get()
            
            if c_selection == "Cibles" or c_selection == "Aucune":
                unique_targets = list(dict.fromkeys([r['target_name'] for r in filtered_results]))
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#34495e']
                
                for i, t_name in enumerate(unique_targets):
                    t_res = [r for r in filtered_results if r['target_name'] == t_name]
                    x_d = [r[x_k] for r in t_res]
                    y_d = [r[y_k] for r in t_res]
                    sc = self.ax.scatter(x_d, y_d, label=t_name, color=colors[i % len(colors)], edgecolors='black', alpha=0.8, s=60, picker=5)
                    sc.custom_data = t_res 
                    self.scatters.append(sc)
                

            elif c_selection == "Fichiers":
                unique_files = list(dict.fromkeys([r['filename'] for r in filtered_results]))
                colors = ['#e67e22', '#1abc9c', '#e74c3c', '#3498db', '#9b59b6', '#34495e', '#2ecc71', '#f1c40f']
                
                for i, f_name in enumerate(unique_files):
                    f_res = [r for r in filtered_results if r['filename'] == f_name]
                    x_d = [r[x_k] for r in f_res]
                    y_d = [r[y_k] for r in f_res]
                    sc = self.ax.scatter(x_d, y_d, label=f_name, color=colors[i % len(colors)], edgecolors='black', alpha=0.8, s=60, picker=5)
                    sc.custom_data = f_res 
                    self.scatters.append(sc)
                

            else:
                c_k = self.keys_map[c_selection]
                c_data = [r[c_k] for r in filtered_results]
                sc = self.ax.scatter(all_x_data, all_y_data, c=c_data, cmap='viridis', edgecolors='black', alpha=0.8, s=60, picker=5)
                sc.custom_data = filtered_results
                self.scatters.append(sc)
                cbar = self.fig.colorbar(sc, ax=self.ax)
                cbar.set_label(c_selection, fontsize=9)

        if y_k and plot_type != "Histogramme (1D)":
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            x_span = x_max - x_min
            y_span = y_max - y_min

            if self.show_mean_y_var.get():
                mean_y = np.mean(all_y_data)
                self.ax.axhline(mean_y, color='red', linestyle='--', alpha=0.8, label='Moy. Y')
                self.ax.text(x_min + x_span*0.05, mean_y, f' Moy. Y: {mean_y:.2f}', color='red', fontsize=8, fontweight='bold', va='bottom')

            if self.show_median_y_var.get():
                median_y = np.median(all_y_data)
                self.ax.axhline(median_y, color='blue', linestyle='-.', alpha=0.8, label='Méd. Y')
                self.ax.text(x_min + x_span*0.05, median_y, f' Méd. Y: {median_y:.2f}', color='blue', fontsize=8, fontweight='bold', va='top')

        if self.show_mean_x_var.get():
            mean_x = np.mean(all_x_data)
            self.ax.axvline(mean_x, color='green', linestyle='--', alpha=0.8, label='Moy. X')
            y_pos = self.ax.get_ylim()[0] + (self.ax.get_ylim()[1] - self.ax.get_ylim()[0])*0.8
            self.ax.text(mean_x, y_pos, f' Moy. X: {mean_x:.2f}', color='green', fontsize=8, fontweight='bold', ha='right', rotation=90)

        if self.show_median_x_var.get():
            median_x = np.median(all_x_data)
            self.ax.axvline(median_x, color='purple', linestyle='-.', alpha=0.8, label='Méd. X')
            y_pos = self.ax.get_ylim()[0] + (self.ax.get_ylim()[1] - self.ax.get_ylim()[0])*0.8
            self.ax.text(median_x, y_pos, f' Méd. X: {median_x:.2f}', color='purple', fontsize=8, fontweight='bold', ha='right', rotation=90)


        if plot_type != "Histogramme (1D)":
            if y_k:
                self.ax.set_ylabel(self.y_var.get(), fontweight='bold')
                
        self.ax.set_xlabel(self.x_var.get(), fontweight='bold')
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.fig.tight_layout()
        self.canvas.draw()

    def on_pick(self, event):
        artist = event.artist
        ind = event.ind[0]

        res = artist.custom_data[ind]

        msg = f"Fichier : {res['filename']}\nCible : {res['target_name']}\n\n"
        msg += f"Paramètres Réf:\nSrc: {res['ref_m_src']:.2f} | Dst(EPA): {res['ref_m_epa']:.2f} | Dst(A): {res['ref_m_dst']:.2f} | Vit: {res['ref_vitesse']:.2f} | Por: {res['ref_portion']:.2f}\n\n"
        msg += f"Paramètres Cible:\nSrc: {res['tgt_m_src']:.2f} | Dst(EPA): {res['tgt_m_epa']:.2f} | Dst(A): {res['tgt_m_dst']:.2f} | Vit: {res['tgt_vitesse']:.2f} | Por: {res['tgt_portion']:.2f}"
        
        msg += f"\n\nRandomisation : {res.get('rand_type', 'Aucune')}"
        if res.get('seed') is not None: msg += f" | Seed : {res['seed']}"
        
        if not messagebox.askyesno("Visualisation Croisée", msg + "\n\nVoulez-vous visualiser ce scénario en détail ?"):
            return

        from src.interface.visualisation import InternalWindow

        def spawn_visualizer(title, filepath):
            win = InternalWindow(self.app_manager.workspace, self.app_manager, title=title)
            self.app_manager.windows.append(win)
            win.load_file(filepath)
            tgt = next((c for c in self.target_configs if c['uid'] == res['target_uid']), None)
            if not tgt: return
            
            win.algo_var.set(tgt['algo'])
            win.ori_var.set(tgt['ori'])
            win.capa_var.set(tgt['capa'])
            win.dem_var.set(tgt['dem'])

            win.inputs["Mult. Demande"].delete(0, tk.END)
            win.inputs["Mult. Demande"].insert(0, str(res["tgt_m_epa"]))
            win.inputs["Vit. Rés (m/s)"].delete(0, tk.END)
            win.inputs["Vit. Rés (m/s)"].insert(0, str(res["tgt_vitesse"]))
            win.inputs["Vit. Arcs (m/s)"].delete(0, tk.END)
            win.inputs["Vit. Arcs (m/s)"].insert(0, str(res["tgt_vitesse"]))
            win.inputs["Prop. Source"].delete(0, tk.END)
            win.inputs["Prop. Source"].insert(0, str(res["tgt_m_src"]))
            win.inputs["Prop. Demande"].delete(0, tk.END)
            win.inputs["Prop. Demande"].insert(0, str(res["tgt_m_dst"]))
            win.inputs["Portion"].delete(0, tk.END)
            win.inputs["Portion"].insert(0, str(res["tgt_portion"]))

            win.rand_type_var.set(res.get('rand_type', 'Aucune'))
            if res.get('seed') is not None:
                win.inputs["Seed (Optionnel)"].delete(0, tk.END)
                win.inputs["Seed (Optionnel)"].insert(0, str(res['seed']))
            else:
                win.randomise_var.set(False)
            
            win.trigger_run()
            return win

        win_tgt = spawn_visualizer(f"Cible: {res['target_name']}", res['filepath'])