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
        
        # Création du dossier séparé pour stocker les fichiers préparés
        self.prep_dir = os.path.join(os.getcwd(), "prepared_datasets")
        os.makedirs(self.prep_dir, exist_ok=True)
        
        self.keys_map = {
            "Mult. Source": "m_src",
            "Mult. Dest. (EPA)": "m_dst_epa",
            "Mult. Dest. (Algo)": "m_dst",
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

        # Conteneur principal
        self.sidebar_container = tk.Frame(main_content, width=280, bg="#ecf0f1", relief="solid", bd=1)
        self.sidebar_container.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_container.pack_propagate(False)

        # Canvas et Scrollbar
        self.canvas_side = tk.Canvas(self.sidebar_container, bg="#ecf0f1", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.sidebar_container, orient="vertical", command=self.canvas_side.yview)
        
        self.sidebar = tk.Frame(self.canvas_side, bg="#ecf0f1", padx=10, pady=10)
        self.sidebar.bind("<Configure>", lambda e: self.canvas_side.configure(scrollregion=self.canvas_side.bbox("all")))
        self.canvas_side.create_window((0, 0), window=self.sidebar, anchor="nw", width=260)
        self.canvas_side.configure(yscrollcommand=self.scrollbar.set)
        
        # L'ORDRE EST CRUCIAL : On pack la scrollbar AVANT le canvas pour qu'elle ne soit pas écrasée
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Événements de la molette
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
        tk.Button(btn_frame, text="Ajouter & Préparer Fichier(s)", command=self.load_files, bg="#2ecc71", fg="black", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(btn_frame, text="Ajouter & Préparer Dossier", command=self.load_directory, bg="#2ecc71", fg="black", font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))

        self.files_listbox = tk.Listbox(self.sidebar, height=3, bg="white", font=("Segoe UI", 7))
        self.files_listbox.pack(fill=tk.X, pady=(0, 5))

        hyd_f = tk.LabelFrame(self.sidebar, text="Préparation Hydraulique (EPANET)", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        hyd_f.pack(fill=tk.X, pady=(0, 10))

        self.sim_mode = tk.StringVar(value="PDA")
        tk.Radiobutton(hyd_f, text="Mode PDA", variable=self.sim_mode, value="PDA", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w", padx=5)
        tk.Radiobutton(hyd_f, text="Mode DDA", variable=self.sim_mode, value="DDA", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w", padx=5)

        param_f = tk.Frame(hyd_f, bg="#ecf0f1")
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

        # --- FILTRES D'EXCLUSION DE COMPOSANTS ---
        exclude_f = tk.LabelFrame(self.sidebar, text="Filtres d'exclusion et conditions", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        exclude_f.pack(fill=tk.X, pady=(0, 10))
        self.exclude_tanks = tk.BooleanVar(value=False)
        self.exclude_pumps = tk.BooleanVar(value=False)
        self.exclude_valves = tk.BooleanVar(value=False)
        
        # NOUVEAU : Ajout de command=self.update_plot
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
        
        # NOUVEAU : Mise à jour en temps réel lors de la frappe
        self.min_res_ent.bind("<KeyRelease>", self.update_plot)
        self.max_res_ent.bind("<KeyRelease>", self.update_plot)

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

        rand_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        rand_f.pack(fill=tk.X, pady=(5, 5))
        tk.Label(rand_f, text="Nb Randomisations (0=Désactivé):", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.nb_rand_entry = tk.Entry(rand_f, width=5)
        self.nb_rand_entry.insert(0, "0")
        self.nb_rand_entry.pack(side=tk.RIGHT, padx=5)

        # --- MODÈLE RÉFÉRENCE ---
        ref_f = tk.LabelFrame(self.sidebar, text="Modèle de Référence", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        ref_f.pack(fill=tk.X, pady=5)
        
        tk.Label(ref_f, text="Algo:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_algo = tk.StringVar(value="EPANET")
        ttk.Combobox(ref_f, textvariable=self.ref_algo, values=ALGO, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ref_f, text="Demande:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_dem = tk.StringVar(value="Uniforme")
        ttk.Combobox(ref_f, textvariable=self.ref_dem, values=DEMANDE, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        tk.Label(ref_f, text="Capacite:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_capa = tk.StringVar(value="Vitesse Max")
        ttk.Combobox(ref_f, textvariable=self.ref_capa, values=CAPACITE, state="readonly").pack(fill=tk.X, padx=5, pady=2)

        tk.Label(ref_f, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.ref_ori = tk.StringVar(value="Aucune")
        ttk.Combobox(ref_f, textvariable=self.ref_ori, values=ORIEN, state="readonly").pack(fill=tk.X, padx=5, pady=(2, 5))

        # --- MODÈLES CIBLES (Dynamique & Spacieux) ---
        self.targets_container = tk.Frame(self.sidebar, bg="#ecf0f1")
        self.targets_container.pack(fill=tk.X, pady=5)
        
        self.target_counter = 0     # Compteur pour garantir un ID unique
        self.target_ui_rows = []    # Liste des boîtes créées
        self.target_configs = []    # Configurations figées au moment du "Run"

        tk.Button(self.sidebar, text="➕ Ajouter un Modèle Cible", bg="#f39c12", font=("Segoe UI", 8, "bold"), command=self.add_target_ui).pack(fill=tk.X, pady=(0, 5))
        
        # On ajoute une cible par défaut au démarrage
        self.add_target_ui()

        # --- FILTRES DE RÉSULTATS (POST-RUN) ---
        self.targets_list_frame = tk.LabelFrame(self.sidebar, text="Afficher/Masquer les Cibles", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        self.targets_list_frame.pack(fill=tk.X, pady=(0, 5))
        self.target_configs = []

        v_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        v_frame.pack(fill=tk.X, pady=5)
        tk.Label(v_frame, text="V. Rés:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.v_res = tk.Entry(v_frame, width=5); self.v_res.insert(0, "3.0"); self.v_res.pack(side=tk.LEFT, padx=2)
        tk.Label(v_frame, text="V. Arc:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.v_arc = tk.Entry(v_frame, width=5); self.v_arc.insert(0, "2.0"); self.v_arc.pack(side=tk.LEFT, padx=2)
        
        p_frame = tk.Frame(self.sidebar, bg="#ecf0f1")
        p_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(p_frame, text="Portion:", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.portion_ent = tk.Entry(p_frame, width=5)
        self.portion_ent.insert(0, "0.1")
        self.portion_ent.pack(side=tk.LEFT, padx=2)

        tk.Button(self.sidebar, text="Lancer l'Analyse", bg="#2980b9", fg="white", font=("Segoe UI", 9, "bold"), command=self.run_analysis).pack(fill=tk.X, pady=10)

        # --- TRACÉ MATPLOTLIB ---
        tk.Label(self.sidebar, text="Tracé du Graphe", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        plot_opts = list(self.keys_map.keys())

        tk.Label(self.sidebar, text="Type :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.plot_type_var = tk.StringVar(value="Nuage de points")
        self.cb_type = ttk.Combobox(self.sidebar, textvariable=self.plot_type_var, values=["Nuage de points", "Histogramme (1D)", "Carte de chaleur (2D)"], state="readonly")
        self.cb_type.pack(fill=tk.X, pady=(0, 5))
        self.cb_type.bind("<<ComboboxSelected>>", self.update_plot) # Nouvelle fonction
        
        tk.Label(self.sidebar, text="Axe X :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
        self.x_var = tk.StringVar(value="Mult. Dest. (EPA)")
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

    def add_target_ui(self):
        self.target_counter += 1
        current_uid = self.target_counter

        tgt_f = tk.LabelFrame(self.targets_container, text=f"Modèle Cible {len(self.target_ui_rows)+1}", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        tgt_f.pack(fill=tk.X, pady=5)

        header_f = tk.Frame(tgt_f, bg="#ecf0f1")
        header_f.pack(fill=tk.X, padx=5, pady=(2, 5))

        var = tk.BooleanVar(value=True)
        tk.Checkbutton(header_f, text="Afficher sur le graphe", variable=var, bg="#ecf0f1", font=("Segoe UI", 8, "bold"), fg="#27ae60", command=self.update_plot).pack(side=tk.LEFT)

        def remove_self():
            tgt_f.destroy()
            self.target_ui_rows = [r for r in self.target_ui_rows if r['uid'] != current_uid]
            if hasattr(self, 'target_configs'):
                self.target_configs = [c for c in self.target_configs if c['uid'] != current_uid]
            self.update_plot()

            for i, r in enumerate(self.target_ui_rows):
                r['frame'].config(text=f"Modèle Cible {i+1}")

        tk.Button(header_f, text="❌", fg="red", bg="#ecf0f1", bd=0, font=("Segoe UI", 8), command=remove_self).pack(side=tk.RIGHT)

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

        # Sauvegarde de la boîte
        self.target_ui_rows.append({
            'frame': tgt_f, 'algo': algo_var, 'dem': dem_var, 'capa': capa_var, 'ori': ori_var, 'var': var, 'uid': current_uid
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
                        self.files_listbox.insert(tk.END, unique_name)
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


    def compute_network(self, choix_algo, choix_ori, choix_capa, choix_dem, p_src, p_dem, v_res, v_arc, portion=1.0):
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
                    ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
                    ffi_wrapper.fix_capacite_flow_calcule_portion(reseau, portion)
                case "Vitesse Max":
                    ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
                case _:
                    ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
                    self.compute_algo(reseau, choix_capa, p_src, p_dem)
                    ffi_wrapper.fix_capacite_flow_calcule(reseau)
                    ffi_wrapper.nullifier_flow(reseau)

            self.compute_orientation(reseau, choix_ori, p_src, p_dem)
            self.compute_algo(reseau, choix_algo, p_src, p_dem)
            if choix_dem == "EPANET":
                ffi_wrapper.get_epanet_fulldemande(self.projet, reseau)

        return reseau

    def run_analysis(self):
        if not self.loaded_files:
            messagebox.showinfo("Info", "Veuillez charger au moins un fichier .inp d'abord.")
            return

        if not self.target_ui_rows:
            messagebox.showinfo("Info", "Veuillez ajouter au moins un modèle cible.")
            return

        self.target_configs = []
        for i, row in enumerate(self.target_ui_rows):
            algo_val = row['algo'].get()
            ori_val = row['ori'].get()
            capa_val = row['capa'].get()
            dem_val = row['dem'].get()
            
            name = f"C{i+1}: {algo_val[:4]} | O:{ori_val[:4]} | C:{capa_val[:4]}"
            
            self.target_configs.append({
                "uid": row['uid'],
                "name": name,
                "algo": algo_val,
                "ori": ori_val,
                "capa": capa_val,
                "dem": dem_val,
                "var": row['var']
            })

        file_flags = {}
        for filepath in self.loaded_files:
            file_flags[filepath] = prepare_dataset.file_contains_elements(filepath)

        try:
            v_res, v_arc = float(self.v_res.get()), float(self.v_arc.get())
            portion_val = float(self.portion_ent.get())
            algo_ref, capa_ref, ori_ref, dem_ref = self.ref_algo.get(), self.ref_capa.get(), self.ref_ori.get(), self.ref_dem.get()

            src_min, src_max, src_n = map(float, [self.ranges["m_src"][i].get() for i in range(3)])
            epa_min, epa_max, epa_n = map(float, [self.ranges["m_dst_epa"][i].get() for i in range(3)])
            dst_min, dst_max, dst_n = map(float, [self.ranges["m_dst"][i].get() for i in range(3)])

            try: nb_rand = int(self.nb_rand_entry.get())
            except ValueError: nb_rand = 0

            seeds_to_run = [None] if nb_rand <= 0 else [random.randint(1, 9999999) for _ in range(nb_rand)]

            arr_src = np.linspace(src_min, src_max, int(src_n))
            arr_epa = np.linspace(epa_min, epa_max, int(epa_n))
            arr_dst = np.linspace(dst_min, dst_max, int(dst_n))

            self.results = []

            total_iters = len(self.loaded_files) * len(arr_src) * len(arr_epa) * len(arr_dst) * len(seeds_to_run) * len(self.target_configs)
            current_iter = 0
            graph_ref = None

            for filepath in self.loaded_files:
                filename = os.path.basename(filepath)
                flags = file_flags[filepath]

                if nb_rand <= 0:
                    self.projet = ffi_wrapper.create_epanet_project(filepath)

                for m_epa in arr_epa:
                    if nb_rand <= 0:
                        ffi_wrapper.modif_multiplicateur(self.projet, m_epa)
                    
                    for m_dst in arr_dst:
                        for m_src in arr_src:
                            for seed_val in seeds_to_run:

                                if seed_val is not None:
                                    self.projet = ffi_wrapper.create_epanet_project(filepath)
                                    ffi_wrapper.modif_multiplicateur(self.projet, m_epa)
                                    ffi_wrapper.set_random_seed(seed_val)
                                    ffi_wrapper.randomise_demande(self.projet)

                                # Calcul du graphe de Référence (Une seule fois pour N Cibles)
                                if algo_ref == "EPANET":
                                    graph_ref = self.compute_network(algo_ref, ori_ref, capa_ref, dem_ref, 1.0, 1.0, 1.0, 1.0, portion_val)
                                else:
                                    graph_ref = self.compute_network(algo_ref, ori_ref, capa_ref, dem_ref, m_src, m_dst, v_res, v_arc, portion_val)

                                # --- NOUVEAU BLOC : Boucle sur toutes les Cibles ---
                                for t_idx, tgt in enumerate(self.target_configs):
                                    current_iter += 1
                                    self.status_label.config(text=f"Calcul : {current_iter}/{total_iters} ...")
                                    self.update_idletasks()

                                    if tgt['algo'] == "EPANET":
                                        graph_tgt = self.compute_network(tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'], 1.0, 1.0, 1.0, 1.0, portion_val)
                                    else:
                                        graph_tgt = self.compute_network(tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'], m_src, m_dst, v_res, v_arc, portion_val)

                                    wape = analyse_tools.get_wape_flow(graph_ref, graph_tgt) * 100
                                    wp = analyse_tools.get_wp_flow(graph_ref, graph_tgt) * 100
                                    sat_ref = float(analyse_tools.get_efficacite(graph_ref)) * 100
                                    sat_tgt = float(analyse_tools.get_efficacite(graph_tgt)) * 100
                                    jaccard_d = analyse_tools.jaccard_distance(graph_ref, graph_tgt) * 100
                                    arcs_non_nul_ref = (analyse_tools.get_n_arcs_non_nul(graph_ref) / analyse_tools.get_n_arcs_no(graph_ref)) * 100
                                    arcs_nul_ref = analyse_tools.extraire_arcs_nulles(graph_ref)
                                    arcs_non_nul_tgt = (analyse_tools.get_n_arcs_non_nul(graph_tgt) / analyse_tools.get_n_arcs_no(graph_tgt)) * 100
                                    arcs_nul_tgt = analyse_tools.extraire_arcs_nulles(graph_tgt)
                                    nb_dom_ref = analyse_tools.get_n_arcs_non_nul(graph_ref)
                                    nb_dom_cible = analyse_tools.get_n_arcs_non_nul(graph_tgt)
                                    nb_inter_dom = analyse_tools.get_intersection_arcs_dominants(graph_ref, graph_tgt).shape[0]
                                    nb_inter_nul = np.intersect1d(arcs_nul_ref, arcs_nul_tgt).shape[0]


                                    self.results.append({
                                        "filepath": filepath, "filename": filename, "seed": seed_val,
                                        "target_uid": tgt['uid'], "target_name": tgt['name'], "flags": flags, # MODIFIÉ ICI
                                        "m_src": m_src, "m_dst_epa": m_epa, "m_dst": m_dst,
                                        "wape": wape, "wp": wp, "sat_ref": sat_ref, "sat_tgt": sat_tgt,
                                        "jaccard": jaccard_d,  "arc_nul_ref": arcs_nul_ref.shape[0] / analyse_tools.get_n_arcs_no(graph_ref) * 100,
                                        "arc_non_nul_ref" : arcs_non_nul_ref, "arc_nul_cible": arcs_nul_tgt.shape[0] / analyse_tools.get_n_arcs_no(graph_tgt) * 100,
                                        "arc_non_nul_cible": arcs_non_nul_tgt,
                                        "ratio_nul_tgt_ref": ((nb_inter_nul / nb_dom_ref) * 100) if nb_dom_ref > 0 else 1.0,
                                        "ratio_inter_ref": ((nb_inter_dom / nb_dom_ref) * 100) if nb_dom_ref > 0 else 1.0
                                    })
                                    
                                    ffi_wrapper.free_graph(graph_tgt)

                                ffi_wrapper.free_graph(graph_ref)

                                if seed_val is not None:
                                    ffi_wrapper.free_project(self.projet)
                                    self.projet = None

                    if nb_rand <= 0:
                        ffi_wrapper.modif_multiplicateur(self.projet, 1.0 / m_epa)

                if nb_rand <= 0 and self.projet is not None:
                    ffi_wrapper.free_project(self.projet)
                    self.projet = None

            self.status_label.config(text=f"Analyse terminée ({total_iters} simulations).")
            self.update_plot()

        except Exception as e:
            messagebox.showerror("Erreur lors de l'analyse", str(e))

    def update_plot(self, event=None):
        if not hasattr(self, 'results') or not self.results:
            return

        # --- GESTION DE L'INTERFACE (Griser les options inutiles) ---
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
        # ------------------------------------------------------------

        # 1. APPLICATION DU FILTRAGE DYNAMIQUE
        filtered_results = []
        try:
            min_res = int(self.min_res_ent.get()) if self.min_res_ent.get().strip() else 0
            max_res = int(self.max_res_ent.get()) if self.max_res_ent.get().strip() else 999999
        except ValueError:
            min_res, max_res = 0, 999999

        for r in self.results:
            flags = r['flags']
            
            # Filtre sur la visibilité de la cible (par UID uniquement)
            tgt_config = next((c for c in self.target_configs if c['uid'] == r['target_uid']), None)
            if not tgt_config: continue             # La boîte cible a été supprimée avec la croix
            if not tgt_config['var'].get(): continue  # La boîte est décochée
            
            # Filtres sur les composants du réseau
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

        # --- TRACÉS ---
        if plot_type == "Histogramme (1D)":
            self.ax.hist(all_x_data, bins=nb_bins, color='#3498db', edgecolor='black', alpha=0.8)
            self.ax.set_ylabel("Nombre de réseaux (Fréquence)", fontweight='bold')

        elif plot_type == "Carte de chaleur (2D)":
            c_selection = self.c_var.get()
            
            # 1. Sécuriser la sélection : si c'est une catégorie ou "Aucune", on désactive c_k
            if c_selection in ["Cibles", "Fichiers", "Aucune"]:
                c_k = None
            else:
                c_k = self.keys_map.get(c_selection)

            # 2. Utiliser numpy.histogram2d pour grouper les valeurs en 'nb_bins' divisions
            # H_count contient la densité (le nombre de cas par case)
            H_count, xedges, yedges = np.histogram2d(all_x_data, all_y_data, bins=nb_bins)

            if c_k:
                # Si on a sélectionné une métrique pour la couleur, on calcule la somme par case
                c_data = [r[c_k] for r in filtered_results]
                H_sum, _, _ = np.histogram2d(all_x_data, all_y_data, bins=nb_bins, weights=c_data)
                
                # On divise la somme par le nombre pour obtenir la moyenne
                with np.errstate(divide='ignore', invalid='ignore'):
                    Z = np.true_divide(H_sum, H_count)
            else:
                Z = H_count

            # On met NaN là où il n'y a pas de données pour laisser la case vide (blanche/transparente)
            Z[H_count == 0] = np.nan
            
            # 3. Affichage : On transpose Z (.T) pour que X soit en abscisse et Y en ordonnée
            im = self.ax.imshow(Z.T, cmap='plasma', aspect='auto', origin='lower')
            
            # 4. Étiquettes des axes (on affiche le centre de chaque division)
            x_centers = (xedges[:-1] + xedges[1:]) / 2
            y_centers = (yedges[:-1] + yedges[1:]) / 2
            
            self.ax.set_xticks(np.arange(len(x_centers)))
            self.ax.set_yticks(np.arange(len(y_centers)))
            
            def format_label(val): return f"{val:.2f}"
            self.ax.set_xticklabels([format_label(v) for v in x_centers], rotation=45, ha='right', fontsize=8)
            self.ax.set_yticklabels([format_label(v) for v in y_centers], fontsize=8)
            
            cbar = self.fig.colorbar(im, ax=self.ax)
            cbar.set_label(f"Moyenne : {c_selection}" if c_k else "Densité (Nombre de réseaux)", fontsize=9)

        else: # Nuage de points
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
                # NOUVEAU : Coloration par Fichier 
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

        # --- LIGNES STATISTIQUES ---
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

        # On récupère les données exactes du point cliqué depuis l'attribut qu'on a créé
        res = artist.custom_data[ind]

        msg = f"Fichier : {res['filename']}\nCible : {res['target_name']}\n\nVoulez-vous visualiser ce scénario en détail ?\n\nMult. Demande (EPANET) : {res['m_dst_epa']:.2f}\nMult. Source : {res['m_src']:.2f}\nMult. Dest (Algo) : {res['m_dst']:.2f}"
        if res['seed'] is not None: msg += f"\nSeed : {res['seed']}"
        
        if not messagebox.askyesno("Visualisation Croisée", msg):
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
            win.inputs["Mult. Demande"].insert(0, str(res["m_dst_epa"]))
            win.inputs["Vit. Rés (m/s)"].delete(0, tk.END)
            win.inputs["Vit. Rés (m/s)"].insert(0, self.v_res.get())
            win.inputs["Vit. Arcs (m/s)"].delete(0, tk.END)
            win.inputs["Vit. Arcs (m/s)"].insert(0, self.v_arc.get())
            win.inputs["Prop. Source"].delete(0, tk.END)
            win.inputs["Prop. Source"].insert(0, str(res["m_src"]))
            win.inputs["Prop. Demande"].delete(0, tk.END)
            win.inputs["Prop. Demande"].insert(0, str(res["m_dst"]))
            win.inputs["Portion"].delete(0, tk.END)
            win.inputs["Portion"].insert(0, self.portion_ent.get())

            if res['seed'] is not None:
                win.randomise_var.set(True)
                win.inputs["Seed (Optionnel)"].delete(0, tk.END)
                win.inputs["Seed (Optionnel)"].insert(0, str(res['seed']))
            else:
                win.randomise_var.set(False)
            
            win.trigger_run()
            return win

        win_tgt = spawn_visualizer(f"Cible: {res['target_name']}", res['filepath'])
