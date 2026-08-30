import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import matplotlib
import os
import json
import concurrent.futures
import threading
import queue

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from src.wrapper_tools import ffi_wrapper
from src.creation_dataset import prepare_dataset

from src.backend.run import run_analysis_worker
from src.backend.extract_data import (
    ALGORITHMES, ORIENTATIONS, CAPACITES, DEMANDES, 
    FILETYPES_INP, FILETYPES_JSON, NpEncoder
)

matplotlib.use("TkAgg")

class AnalysisWindow(tk.Frame):
    def __init__(self, parent, app_manager):
        super().__init__(parent, bg="white", bd=2, relief="groove")
        self.app_manager = app_manager
        self.projet = None
        self.loaded_files = []
        self.results = []
        self.file_vars = {}  

        self.prep_dir = os.path.join(os.getcwd(), "prepared_datasets")
        os.makedirs(self.prep_dir, exist_ok=True)

        self.keys_map = {
            "Cible (Nom)": "target_name",
            "Fichier": "filename",
            "Algorithme": "target_algo",
            "Orientation": "target_ori",
            "Capacité": "target_capa",
            "Demande": "target_dem",
            "Réf - Mult. Source": "ref_m_src",
            "Réf - Mult. Dest. (EPA)": "ref_m_epa",
            "Réf - Mult. Dest. (Algo)": "ref_m_dst",
            "Réf - Vitesse": "ref_vitesse",
            "Réf - Portion": "ref_portion",
            "Réf - Ecart Type": "ref_ecart_type",
            "Cible - Mult. Source": "tgt_m_src",
            "Cible - Mult. Dest. (EPA)": "tgt_m_epa",
            "Cible - Mult. Dest. (Algo)": "tgt_m_dst",
            "Cible - Vitesse": "tgt_vitesse",
            "Cible - Portion": "tgt_portion",
            "Cible - Ecart Type": "tgt_ecart_type",
            "Satisfaisabilité Réf (%)": "sat_ref",
            "Satisfaisabilité Cible (%)": "sat_tgt",
            "Erreur Absolue ponderee Flow (WAPE %)": "wape",
            "Erreur ponderee Flow (%)": "wp",
            "Erreur Absolue ponderee Pression (WAPE %)": "wape_p",
            "Erreur ponderee Pression (%)": "wp_p",
            "Distance de Jaccard (%)": "jaccard",
            "Portion Arcs Flow Nul Réf (%)": "arc_nul_ref",
            "Portion Arcs Flow Non Nul Réf (%)": "arc_non_nul_ref",
            "Portion Arcs Flow Nul Cible (%)": "arc_nul_cible",
            "Portion Arcs Flow Non Nul Cible (%)": "arc_non_nul_cible",
            "Liens mal non orientés (%)": "ratio_nul_tgt_ref",
            "Liens mal orientés (%)": "ratio_inter_ref",
            "Nombre de sommets": "nb_nodes",
            "Nombre d'arêtes": "nb_edges",
            "% Arcs dP >= 0 (Réf)": "ref_dp_pos_zero",
            "% Arcs dP < 0 (Réf)": "ref_dp_neg",
            "% Arcs dP >= 0 (Cible)": "tgt_dp_pos_zero",
            "% Arcs dP < 0 (Cible)": "tgt_dp_neg",
            "Valeur de la Coupe Min": "min_cut"
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
            ("portion", "Portion", "1.0", "1.0", "1"),
            ("ecart_type", "Ecart-Type", "0.3", "0.3", "1")
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

        io_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        io_f.pack(fill=tk.X, pady=(0, 5))
        self.btn_load_analysis = tk.Button(io_f, text="Ouvrir Analyse", command=self.load_analysis, bg="#f39c12", fg="white", font=("Segoe UI", 8, "bold"))
        self.btn_load_analysis.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self.btn_save_analysis = tk.Button(io_f, text="Sauvegarder", command=self.save_analysis, bg="#d35400", fg="white", font=("Segoe UI", 8, "bold"), state=tk.DISABLED)
        self.btn_save_analysis.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

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

        self.ref_f = tk.LabelFrame(self.sidebar, text="Modèle de Référence", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.ref_f.pack(fill=tk.X, pady=5)
        
        tk.Label(self.ref_f, text="Algo:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_algo = tk.StringVar(value="EPANET")
        ttk.Combobox(self.ref_f, textvariable=self.ref_algo, values=ALGORITHMES, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(self.ref_f, text="Demande:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_dem = tk.StringVar(value="Inchanger")
        ttk.Combobox(self.ref_f, textvariable=self.ref_dem, values=DEMANDES, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(self.ref_f, text="Capacite:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_capa = tk.StringVar(value="Vitesse Max")
        ttk.Combobox(self.ref_f, textvariable=self.ref_capa, values=CAPACITES, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(self.ref_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_ori = tk.StringVar(value="Aucune")
        ttk.Combobox(self.ref_f, textvariable=self.ref_ori, values=ORIENTATIONS, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(self.ref_f, text="Balayage Réf", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5,0))
        self.ref_ranges = self.create_grid_ui(self.ref_f)

        self.targets_container = tk.Frame(self.sidebar, bg="#ecf0f1")
        self.targets_container.pack(fill=tk.X, pady=5)
        
        self.target_counter = 0
        self.target_ui_rows = []
        self.target_configs = []

        self.btn_add_target = tk.Button(self.sidebar, text="➕ Ajouter un Modèle Cible", bg="#f39c12", font=("Segoe UI", 8, "bold"), command=self.add_target_ui)
        self.btn_add_target.pack(fill=tk.X, pady=(0, 5))
        
        self.add_target_ui()

        self.targets_list_frame = tk.LabelFrame(self.sidebar, text="Afficher/Masquer les Cibles", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.targets_list_frame.pack(fill=tk.X, pady=(0, 5))

        self.run_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        self.run_frame.pack(fill=tk.X, pady=10)

        proc_f = tk.Frame(self.run_frame, bg="#ecf0f1")
        proc_f.pack(fill=tk.X, pady=(0, 5))
        tk.Label(proc_f, text="Nb Processus:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT)
        self.num_proc_var = tk.StringVar(value="4")
        tk.Entry(proc_f, textvariable=self.num_proc_var, width=5).pack(side=tk.LEFT, padx=5)

        self.btn_run = tk.Button(self.run_frame, text="Lancer l'Analyse", bg="#2980b9", fg="white", font=("Segoe UI", 9, "bold"), command=self.run_analysis)
        self.btn_run.pack(fill=tk.X, pady=(0, 5))

        self.btn_reset = tk.Button(self.run_frame, text="Réinitialiser & Déverrouiller", bg="#e74c3c", fg="white", font=("Segoe UI", 9, "bold"), command=self.reset_analysis)

        tk.Label(self.sidebar, text="Tracé du Graphe", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        plot_opts = list(self.keys_map.keys())

        tk.Label(self.sidebar, text="Type :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.plot_type_var = tk.StringVar(value="Nuage de points")
        self.cb_type = ttk.Combobox(self.sidebar, textvariable=self.plot_type_var, values=["Nuage de points", "Histogramme/Barres", "Boîte à moustaches", "Carte de chaleur (2D)"], state="readonly")
        self.cb_type.pack(fill=tk.X, pady=(0, 5))
        self.cb_type.bind("<<ComboboxSelected>>", self.update_plot)
        
        tk.Label(self.sidebar, text="Axe X :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.x_var = tk.StringVar(value="Cible - Mult. Dest. (EPA)")
        self.cb_x = ttk.Combobox(self.sidebar, textvariable=self.x_var, values=plot_opts, state="readonly")
        self.cb_x.pack(fill=tk.X, pady=(0, 5)); self.cb_x.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Axe Y (Métriques) :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.y_var = tk.StringVar(value="Satisfaisabilité Cible (%)")
        self.cb_y = ttk.Combobox(self.sidebar, textvariable=self.y_var, values=plot_opts, state="readonly")
        self.cb_y.pack(fill=tk.X, pady=(0, 5))
        self.cb_y.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Comptage (Histo.) :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.agg_var = tk.StringVar(value="Nombre d'instances")
        self.cb_agg = ttk.Combobox(self.sidebar, textvariable=self.agg_var, values=["Nombre d'instances", "Nombre de fichiers"], state="readonly")
        self.cb_agg.pack(fill=tk.X, pady=(0, 5))
        self.cb_agg.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Paramètre / Couleur :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.c_var = tk.StringVar(value="Cibles")
        self.cb_c = ttk.Combobox(self.sidebar, textvariable=self.c_var, values=["Cibles", "Fichiers"] + plot_opts, state="readonly")
        self.cb_c.pack(fill=tk.X); self.cb_c.bind("<<ComboboxSelected>>", self.update_plot)

        bins_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        bins_f.pack(fill=tk.X, pady=5)
        tk.Label(bins_f, text="Nb divisions (ou [0,5]):", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.bins_var = tk.Entry(bins_f, width=10)
        self.bins_var.insert(0, "15")
        self.bins_var.pack(side=tk.RIGHT, padx=5)
        self.bins_var.bind("<Return>", self.update_plot)

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
        self.progress_bar = ttk.Progressbar(self.status_bar, orient="horizontal", length=250, mode="determinate")

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
        self._set_state(self.ref_f, freeze)

        for row in self.target_ui_rows:
            row['btn_delete'].config(state=state)
            for child in row['frame'].winfo_children():
                if child != row['header_f']:
                    self._set_state(child, freeze)

    def reset_analysis(self):
        self.results = []
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
        ttk.Combobox(tgt_f, textvariable=algo_var, values=ALGORITHMES, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(tgt_f, text="Demande:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        dem_var = tk.StringVar(value="Inchanger")
        ttk.Combobox(tgt_f, textvariable=dem_var, values=DEMANDES, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(tgt_f, text="Capacite:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        capa_var = tk.StringVar(value="Vitesse Max")
        ttk.Combobox(tgt_f, textvariable=capa_var, values=CAPACITES, state="readonly").pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(tgt_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        ori_var = tk.StringVar(value="Aucune")
        ttk.Combobox(tgt_f, textvariable=ori_var, values=ORIENTATIONS, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))
        
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
                prepare_dataset.convertir_unites(wn, 'LPM')
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
        paths = filedialog.askopenfilenames(filetypes=FILETYPES_INP)
        if paths:
            self._prepare_and_load(paths)

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
            "portion": np.linspace(safe_float(ranges["portion"][0], 1.0), safe_float(ranges["portion"][1], 1.0), safe_int(ranges["portion"][2])),
            "ecart_type": np.linspace(safe_float(ranges["ecart_type"][0], 0.3), safe_float(ranges["ecart_type"][1], 0.3), safe_int(ranges["ecart_type"][2]))
        }

    def _extract_analysis_params(self):
        self.target_configs = []
        clean_targets_for_mp = []
        
        for i, row in enumerate(self.target_ui_rows):
            name = f"C{i+1}: {row['algo'].get()[:4]} | O:{row['ori'].get()[:4]} | C:{row['capa'].get()[:4]}"
            
            self.target_configs.append({
                "uid": row['uid'], "name": name,
                "algo": row['algo'].get(), "ori": row['ori'].get(),
                "capa": row['capa'].get(), "dem": row['dem'].get(),
                "var": row['var'],
                "grid": self._extract_grid(row['ranges'])
            })
            
            if row['var'].get():
                clean_targets_for_mp.append({
                    "uid": row['uid'], "name": name,
                    "algo": row['algo'].get(), "ori": row['ori'].get(),
                    "capa": row['capa'].get(), "dem": row['dem'].get(),
                    "grid": self._extract_grid(row['ranges'])
                })

        # Utilise un seul scénario de base afin que le backend puisse continuer de fonctionner
        randomizations = [("Aucune", None, 0.0)]

        return {
            "ref_algo": self.ref_algo.get(),
            "ref_capa": self.ref_capa.get(),
            "ref_ori": self.ref_ori.get(),
            "ref_dem": self.ref_dem.get(),
            "ref_grid": self._extract_grid(self.ref_ranges),
            "randomizations": randomizations,
            "targets": clean_targets_for_mp
        }

    def run_analysis(self):
        params = self._extract_analysis_params()
        num_procs = int(self.num_proc_var.get())
        
        ref_grid = params['ref_grid']
        ref_iters = len(ref_grid["ecart_type"]) * len(ref_grid["m_epa"]) * len(ref_grid["m_dst"]) * len(ref_grid["m_src"]) * len(ref_grid["vitesse"]) * len(ref_grid["portion"])
        
        tgt_iters = 0
        for t in params['targets']:
            t_grid = t['grid']
            tgt_iters += len(t_grid["ecart_type"]) * len(t_grid["m_epa"]) * len(t_grid["m_dst"]) * len(t_grid["m_src"]) * len(t_grid["vitesse"]) * len(t_grid["portion"])
            
        sims_per_task = ref_iters * tgt_iters
        
        tasks = []
        file_flags = {fp: prepare_dataset.file_contains_elements(fp) for fp in self.loaded_files}
        for filepath in self.loaded_files:
            if not self.file_vars[filepath].get(): continue
            filename = os.path.basename(filepath)
            for rand_type, seed_val, rand_ecart in params['randomizations']:
                tasks.append((filepath, filename, file_flags[filepath], rand_type, seed_val, rand_ecart, params))

        total_simulations = len(tasks) * sims_per_task

        self.freeze_ui(True)
        self.progress_queue = queue.Queue()
        
        self.progress_bar.pack(side=tk.LEFT, padx=10)
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = total_simulations
        print(f"\n[--- Lancement de l'analyse : {total_simulations} simulations prévues ---]")

        threading.Thread(target=self._run_multiprocessing, args=(tasks, num_procs, sims_per_task, total_simulations), daemon=True).start()
        self.after(100, self._check_progress)

    def _run_multiprocessing(self, tasks, num_procs, sims_per_task, total_simulations):
        all_results = []
        completed_sims = 0
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_procs) as executor:
                futures = [executor.submit(run_analysis_worker, t) for t in tasks]
                for f in concurrent.futures.as_completed(futures):
                    all_results.extend(f.result())
                    completed_sims += sims_per_task
                    self.progress_queue.put(('step', completed_sims, total_simulations))
                    
            self.progress_queue.put(('done', all_results))
        except Exception as e:
            self.progress_queue.put(('error', str(e)))

    def _check_progress(self):
        import sys
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                
                if isinstance(msg, tuple) and msg[0] == 'step':
                    completed, total = msg[1], msg[2]
                    
                    self.progress_bar["value"] = completed
                    self.status_label.config(text=f"Calcul en cours : {completed}/{total} simulation(s)...")
                    
                    percent = (completed / total) * 100 if total > 0 else 0
                    bar_len = 40
                    filled_len = int(bar_len * completed // total) if total > 0 else 0
                    bar = '█' * filled_len + '-' * (bar_len - filled_len)
                    sys.stdout.write(f'\rProgression |{bar}| {percent:.1f}% ({completed}/{total})')
                    sys.stdout.flush()
                    
                elif isinstance(msg, tuple) and msg[0] == 'done':
                    self.results = msg[1]
                    self.rebuild_filters_from_results()
                    self.btn_save_analysis.config(state=tk.NORMAL)
                    self.progress_bar.pack_forget()
                    self.update_plot()
                    self.status_label.config(text=f"Analyse terminée avec succès ({len(self.results)} résultats).")
                    print("\n[--- Analyse terminée ! ---]\n")
                    return
                    
                elif isinstance(msg, tuple) and msg[0] == 'error':
                    from tkinter import messagebox
                    messagebox.showerror("Erreur", str(msg[1]))
                    self.progress_bar.pack_forget()
                    self.freeze_ui(False)
                    print(f"\n[X] Erreur d'analyse : {msg[1]}\n")
                    return
                    
        except queue.Empty:
            pass
            
        self.after(100, self._check_progress)

    def update_plot(self, event=None):
        if not hasattr(self, 'results') or not self.results:
            return

        plot_type = self.plot_type_var.get()
        
        if plot_type == "Histogramme/Barres":
            self.cb_y.config(state="disabled")
            self.cb_agg.config(state="readonly")
            self.cb_c.config(state="disabled")
            self.chk_mean_y.config(state="disabled")
            self.chk_median_y.config(state="disabled")
        elif plot_type == "Boîte à moustaches":
            self.cb_y.config(state="readonly")
            self.cb_agg.config(state="disabled")
            self.cb_c.config(state="disabled")
            self.chk_mean_y.config(state="normal")
            self.chk_median_y.config(state="normal")
        else:
            self.cb_y.config(state="readonly")
            self.cb_agg.config(state="disabled")
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
            if r['filepath'] in self.file_vars and not self.file_vars[r['filepath']].get(): continue
            flags = r['flags']
            tgt_config = next((c for c in self.target_configs if c['uid'] == r['target_uid']), None)
            if not tgt_config or not tgt_config['var'].get(): continue 
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
        y_sel = self.y_var.get()
        y_k = self.keys_map.get(y_sel, None)

        try:
            bins_str = self.bins_var.get().strip()
            if ';' in bins_str:
                custom_mode = "intervals"
                parsed_intervals = []
                for part in bins_str.split(';'):
                    part = part.strip()
                    if not part: continue
                    inc_min = part.startswith('[')
                    inc_max = part.endswith(']')
                    inner = part[1:-1].split(',')
                    min_v = float(inner[0].strip().replace('+inf', 'inf').replace('-inf', '-inf'))
                    max_v = float(inner[1].strip().replace('+inf', 'inf').replace('-inf', '-inf'))
                    parsed_intervals.append((min_v, max_v, inc_min, inc_max, part))
            elif ',' in bins_str:
                custom_mode = "edges"
                bins_val = [float(x.strip()) for x in bins_str.split(',') if x.strip()]
                if len(bins_val) < 2: 
                    bins_val = 15
                    custom_mode = "auto"
            else:
                custom_mode = "auto"
                bins_val = int(bins_str)
                if bins_val <= 0: bins_val = 15
        except Exception:
            custom_mode = "auto"
            bins_val = 15

        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.scatters = []

        all_x_data = [r[x_k] for r in filtered_results]
        all_y_data = [r[y_k] for r in filtered_results] if y_k else []

        subsets = []
        x_labels = []
        
        if plot_type in ("Histogramme/Barres", "Boîte à moustaches"):
            if len(filtered_results) > 0 and isinstance(filtered_results[0][x_k], str):
                unique_vals = sorted(list(set([r[x_k] for r in filtered_results])))
                for val in unique_vals:
                    x_labels.append(str(val))
                    subset = [r for r in filtered_results if r[x_k] == val]
                    subsets.append(subset)
            elif custom_mode == "intervals":
                for min_v, max_v, inc_min, inc_max, label in parsed_intervals:
                    x_labels.append(label)
                    subset = [r for r in filtered_results if ((r[x_k] >= min_v) if inc_min else (r[x_k] > min_v)) and ((r[x_k] <= max_v) if inc_max else (r[x_k] < max_v))]
                    subsets.append(subset)
            else:
                if custom_mode == "auto":
                    bin_edges = np.histogram_bin_edges([r[x_k] for r in filtered_results], bins=bins_val)
                else:
                    bin_edges = np.array(bins_val)
                    
                for i in range(len(bin_edges) - 1):
                    b_min = bin_edges[i]
                    b_max = bin_edges[i+1]
                    if i == len(bin_edges) - 2:
                        subset = [r for r in filtered_results if b_min <= r[x_k] <= b_max]
                        label = f"[{b_min:.2f}, {b_max:.2f}]"
                    else:
                        subset = [r for r in filtered_results if b_min <= r[x_k] < b_max]
                        label = f"[{b_min:.2f}, {b_max:.2f}["
                    x_labels.append(label)
                    subsets.append(subset)

        if plot_type == "Histogramme/Barres":
            agg_mode = self.agg_var.get()
            if agg_mode == "Nombre de fichiers":
                total_items = len(set(r['filename'] for r in filtered_results))
                agg_vals = [len(set(r['filename'] for r in s)) for s in subsets]
            else:
                total_items = len(filtered_results)
                agg_vals = [len(s) for s in subsets]
                
            x_pos = np.arange(len(x_labels))
            bars = self.ax.bar(x_pos, agg_vals, color='#3498db', edgecolor='black', alpha=0.8)
            self.ax.set_xticks(x_pos)
            self.ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=9)
            
            for bar, val in zip(bars, agg_vals):
                if val > 0 and total_items > 0:
                    pct = (val / total_items) * 100
                    self.ax.text(bar.get_x() + bar.get_width()/2, val, f'{val}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=8, fontweight='bold')
                elif val == 0:
                    self.ax.text(bar.get_x() + bar.get_width()/2, val, '0', ha='center', va='bottom', fontsize=8)
                    
            self.ax.set_ylabel(agg_mode, fontweight='bold')
            self.ax.set_ylim(0, max(agg_vals) * 1.15 if agg_vals and max(agg_vals) > 0 else 1)

        elif plot_type == "Boîte à moustaches":
            boxplot_data = [[r[y_k] for r in s] for s in subsets]
            x_pos = np.arange(1, len(x_labels) + 1)
            
            bp = self.ax.boxplot(boxplot_data, positions=x_pos, patch_artist=True, showmeans=True,
                                 boxprops=dict(facecolor='#9b59b6', alpha=0.7),
                                 capprops=dict(color='#2c3e50', linewidth=1.5),
                                 whiskerprops=dict(color='#2c3e50', linewidth=1.5),
                                 flierprops=dict(marker='o', markerfacecolor='#e74c3c', markersize=5, alpha=0.6, markeredgecolor='none'),
                                 medianprops=dict(color='black', linewidth=2),
                                 meanprops=dict(marker='^', markerfacecolor='white', markeredgecolor='black', markersize=7))
            
            new_x_labels = []
            new_x_labels = []
            for i in range(len(boxplot_data)):
                data_i = boxplot_data[i]
                if len(data_i) > 0:
                    y_min = np.min(data_i)
                    y_max = np.max(data_i)
                    y_q1 = np.percentile(data_i, 25)
                    y_median = np.median(data_i)
                    y_q3 = np.percentile(data_i, 75)
                    y_mean = np.mean(data_i)
                    
                    lbl = (f"{x_labels[i]}\n"
                           f"Min: {y_min:.2f} | Max: {y_max:.2f}\n"
                           f"Q1: {y_q1:.2f} | Q3: {y_q3:.2f}\n"
                           f"Med: {y_median:.2f} | Moy: {y_mean:.2f}")
                    new_x_labels.append(lbl)
                else:
                    new_x_labels.append(x_labels[i])
                
            self.ax.set_xticks(x_pos)
            self.ax.set_xticklabels(new_x_labels, rotation=0, ha='center', fontsize=9)
            self.ax.set_ylabel(y_sel, fontweight='bold')
            self.ax.grid(axis='y', linestyle='--', alpha=0.7)

            import matplotlib.patches as mpatches
            import matplotlib.lines as mlines
            legend_elements = [
                mpatches.Patch(facecolor='#9b59b6', alpha=0.7, label='Boîte (Q1 - Q3)'),
                mlines.Line2D([0], [0], color='black', lw=2, label='Médiane'),
                mlines.Line2D([0], [0], marker='^', color='w', markerfacecolor='white', markeredgecolor='black', markersize=7, label='Moyenne'),
                mlines.Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c', markersize=6, label='Valeurs aberrantes')
            ]
            self.ax.legend(handles=legend_elements, loc='best', fontsize=9)

        elif plot_type == "Carte de chaleur (2D)":
            if len(all_x_data) > 0 and (isinstance(all_x_data[0], str) or isinstance(all_y_data[0], str)):
                messagebox.showwarning("Incompatible", "La carte de chaleur ne supporte pas les axes catégoriels (textes).")
                return

            c_selection = self.c_var.get()
            c_k = self.keys_map.get(c_selection) if c_selection not in ["Cibles", "Fichiers", "Aucune"] else None

            H_count, xedges, yedges = np.histogram2d(all_x_data, all_y_data, bins=bins_val if isinstance(bins_val, int) else 15)

            if c_k:
                c_data = [r[c_k] for r in filtered_results]
                H_sum, _, _ = np.histogram2d(all_x_data, all_y_data, bins=bins_val if isinstance(bins_val, int) else 15, weights=c_data)
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
            self.ax.set_xticklabels([f"{v:.2f}" for v in x_centers], rotation=45, ha='right', fontsize=8)
            self.ax.set_yticklabels([f"{v:.2f}" for v in y_centers], fontsize=8)
            
            cbar = self.fig.colorbar(im, ax=self.ax)
            cbar.set_label(f"Moyenne : {c_selection}" if c_k else "Densité (Nombre de réseaux)", fontsize=9)

        else: # Nuage de points
            c_selection = self.c_var.get()
            if c_selection == "Cibles" or c_selection == "Aucune":
                unique_targets = list(dict.fromkeys([r['target_name'] for r in filtered_results]))
                colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#34495e']
                for i, t_name in enumerate(unique_targets):
                    t_res = [r for r in filtered_results if r['target_name'] == t_name]
                    sc = self.ax.scatter([r[x_k] for r in t_res], [r[y_k] for r in t_res], label=t_name, color=colors[i % len(colors)], edgecolors='black', alpha=0.8, s=60, picker=5)
                    sc.custom_data = t_res 
                    self.scatters.append(sc)
            elif c_selection == "Fichiers":
                unique_files = list(dict.fromkeys([r['filename'] for r in filtered_results]))
                colors = ['#e67e22', '#1abc9c', '#e74c3c', '#3498db', '#9b59b6', '#34495e', '#2ecc71', '#f1c40f']
                for i, f_name in enumerate(unique_files):
                    f_res = [r for r in filtered_results if r['filename'] == f_name]
                    sc = self.ax.scatter([r[x_k] for r in f_res], [r[y_k] for r in f_res], label=f_name, color=colors[i % len(colors)], edgecolors='black', alpha=0.8, s=60, picker=5)
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

        if y_k and plot_type not in ("Histogramme/Barres", "Boîte à moustaches"):
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            x_span = x_max - x_min
            
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

        if plot_type not in ("Histogramme/Barres", "Boîte à moustaches") and y_k:
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
        msg += f"Paramètres Réf:\nSrc: {res['ref_m_src']:.2f} | Dst(EPA): {res['ref_m_epa']:.2f} | Dst(A): {res['ref_m_dst']:.2f} | Vit: {res['ref_vitesse']:.2f} | Por: {res['ref_portion']:.2f} | Ecart: {res['ref_ecart_type']:.2f}\n\n"
        msg += f"Paramètres Cible:\nSrc: {res['tgt_m_src']:.2f} | Dst(EPA): {res['tgt_m_epa']:.2f} | Dst(A): {res['tgt_m_dst']:.2f} | Vit: {res['tgt_vitesse']:.2f} | Por: {res['tgt_portion']:.2f} | Ecart: {res['tgt_ecart_type']:.2f}"
        
        if not messagebox.askyesno("Visualisation Croisée", msg + "\n\nVoulez-vous visualiser ce scénario en détail ?"):
            return

        from src.interface.visualisation import InternalWindow

        def spawn_visualizer(title, filepath):
            win = InternalWindow(self.app_manager.workspace, self.app_manager, title=title)
            self.app_manager.windows.append(win)
            win.current_filepath = filepath
            
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
            
            win.inputs["Ecart-Type"].delete(0, tk.END)
            win.inputs["Ecart-Type"].insert(0, str(res["tgt_ecart_type"]))

            win.trigger_run()
            win.after(100, win.reset_view)
            return win

        win_tgt = spawn_visualizer(f"Cible: {res['target_name']}", res['filepath'])

    def save_analysis(self):
        if not self.results:
            messagebox.showwarning("Attention", "Aucune analyse à sauvegarder.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=FILETYPES_JSON)
        if filepath:
            # Création d'un objet englobant les résultats ET la configuration UI
            data_to_save = {
                "config": {
                    "sim_mode": self.sim_mode.get(),
                    "p_min": self.p_min_ent.get(),
                    "p_req": self.p_req_ent.get(),
                    "p_exp": self.p_exp_ent.get(),
                    "exclude_tanks": self.exclude_tanks.get(),
                    "exclude_pumps": self.exclude_pumps.get(),
                    "exclude_valves": self.exclude_valves.get(),
                    "min_res": self.min_res_ent.get(),
                    "max_res": self.max_res_ent.get(),
                    "ref_algo": self.ref_algo.get(),
                    "ref_dem": self.ref_dem.get(),
                    "ref_capa": self.ref_capa.get(),
                    "ref_ori": self.ref_ori.get()
                },
                "results": self.results
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, cls=NpEncoder, indent=4)
            messagebox.showinfo("Succès", "L'analyse a été sauvegardée avec succès.")

    def load_analysis(self, pre_filepath=None):
        filepath = pre_filepath or filedialog.askopenfilename(filetypes=FILETYPES_JSON)
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier si c'est l'ancien format (liste simple) ou le nouveau (dictionnaire)
            if isinstance(data, dict) and "results" in data:
                self.results = data["results"]
                config = data.get("config", {})
                
                # --- Restauration de l'interface gauche ---
                if "sim_mode" in config: self.sim_mode.set(config["sim_mode"])
                if "exclude_tanks" in config: self.exclude_tanks.set(config["exclude_tanks"])
                if "exclude_pumps" in config: self.exclude_pumps.set(config["exclude_pumps"])
                if "exclude_valves" in config: self.exclude_valves.set(config["exclude_valves"])
                if "ref_algo" in config: self.ref_algo.set(config["ref_algo"])
                if "ref_dem" in config: self.ref_dem.set(config["ref_dem"])
                if "ref_capa" in config: self.ref_capa.set(config["ref_capa"])
                if "ref_ori" in config: self.ref_ori.set(config["ref_ori"])

                # Pour les Entry (champs de texte), il faut supprimer puis insérer
                def restore_entry(entry_widget, key):
                    if key in config:
                        entry_widget.delete(0, tk.END)
                        entry_widget.insert(0, str(config[key]))

                restore_entry(self.p_min_ent, "p_min")
                restore_entry(self.p_req_ent, "p_req")
                restore_entry(self.p_exp_ent, "p_exp")
                restore_entry(self.min_res_ent, "min_res")
                restore_entry(self.max_res_ent, "max_res")
                
            else:
                self.results = data

            self.rebuild_filters_from_results()
            self.freeze_ui(True)
            self.update_plot()
            self.btn_save_analysis.config(state=tk.NORMAL)
            self.status_label.config(text=f"Analyse chargée depuis : {os.path.basename(filepath)}")

    def rebuild_filters_from_results(self):
        for widget in self.files_frame.winfo_children(): widget.destroy()
        for widget in self.targets_list_frame.winfo_children(): widget.destroy()
        self.file_vars.clear()
        
        # Sauvegarde des configurations existantes
        existing_configs = {c['uid']: c for c in self.target_configs}
        self.target_configs.clear()

        for f in list(set([r['filepath'] for r in self.results])):
            self.file_vars[f] = tk.BooleanVar(value=True)
            tk.Checkbutton(self.files_frame, text=os.path.basename(f), variable=self.file_vars[f], bg="white", font=("Segoe UI", 7), anchor="w", command=self.update_plot).pack(fill=tk.X)

        for uid in sorted(list(set([r['target_uid'] for r in self.results]))):
            # On isole un résultat (le premier trouvé) pour cette cible afin d'y lire ses métadonnées
            sample_r = next(r for r in self.results if r['target_uid'] == uid)
            name = sample_r['target_name']
            var = tk.BooleanVar(value=True)
            
            if uid in existing_configs:
                # Si la cible existe déjà dans l'interface en cours, on la garde
                config = existing_configs[uid]
                config['var'] = var
                self.target_configs.append(config)
            else:
                # Récupération depuis le JSON (ou valeurs par défaut si vieux JSON)
                saved_algo = sample_r.get('target_algo', 'EPANET')
                saved_ori = sample_r.get('target_ori', 'Aucune')
                saved_capa = sample_r.get('target_capa', 'Vitesse Max')
                saved_dem = sample_r.get('target_dem', 'Inchanger')
                
                self.target_configs.append({
                    'uid': uid, 'name': name, 'var': var, 
                    'algo': saved_algo, 'ori': saved_ori, 
                    'capa': saved_capa, 'dem': saved_dem
                })
                
            tk.Checkbutton(self.targets_list_frame, text=name, variable=var, bg="#ecf0f1", font=("Segoe UI", 8), anchor="w", command=self.update_plot).pack(fill=tk.X, padx=5)
