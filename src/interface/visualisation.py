from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from src.wrapper_tools import ffi_wrapper
from src.wrapper_tools import analyse_tools
import numpy as np
import matplotlib
matplotlib.use("TkAgg")

ALGORITHMES = ("EPANET", "Ford-Fulkerson", "Edmonds-Karp")
ORIENTATIONS = ("Aucune", "EPANET","Ford-Fulkerson", "Edmonds-Karp")


class InternalWindow(tk.Frame):
    def __init__(self, parent, app_manager, title="Réseau"):
        super().__init__(parent, bg="white", bd=2, relief="groove")
        self.app_manager = app_manager
        self.projet = None
        self.nodes, self.edges = [], []
        self.scale = 1.0
        self.pan_x = self.pan_y = 0.0
        self.last_mouse_x = self.last_mouse_y = 0
        self.min_x = self.min_y = 0.0
        self.max_x = self.max_y = 1.0

        self.setup_ui(title)
        self.setup_bindings()

        self.bind("<ButtonPress-1>", self.set_focus, add="+")
        self.title_bar.bind("<ButtonPress-1>", self.set_focus, add="+")
        self.canvas.bind("<ButtonPress-1>", self.set_focus, add="+")

        self.place(x=30 + len(app_manager.windows)*30, y=30 + len(app_manager.windows)*30, width=1050, height=650)
        self.set_focus()

    def setup_ui(self, title):
        self.title_bar = tk.Frame(self, bg="#7f8c8d", relief="flat", bd=0, height=25)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)

        self.toggle_btn = tk.Button(self.title_bar, text="◀ Options", bg="#7f8c8d", fg="white", bd=0, font=("Segoe UI", 8, "bold"), command=self.toggle_sidebar)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        self.title_label = tk.Label(self.title_bar, text=f"|  {title}", bg="#7f8c8d", fg="white", font=("Segoe UI", 9, "bold"))
        self.title_label.pack(side=tk.LEFT, padx=5)

        self.close_btn = tk.Button(self.title_bar, text="X", bg="#e74c3c", fg="white", bd=0, width=3, command=self.close_window)
        self.close_btn.pack(side=tk.RIGHT)

        main_content = tk.Frame(self, bg="white")
        main_content.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(main_content, width=220, bg="#ecf0f1", padx=10, pady=10, relief="solid", bd=1)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="Algo Principal:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.algo_var = tk.StringVar(value="EPANET")
        ttk.Combobox(self.sidebar, textvariable=self.algo_var, values=ALGORITHMES, state="readonly").pack(fill=tk.X, pady=(0, 5))

        tk.Label(self.sidebar, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.ori_var = tk.StringVar(value="Aucune")
        ttk.Combobox(self.sidebar, textvariable=self.ori_var, values=ORIENTATIONS, state="readonly").pack(fill=tk.X, pady=(0, 10))

        self.inputs = {}
        fields = [("Mult. Demande", "1.0"), ("Vit. Rés (m/min)", "180.0"),
                  ("Vit. Arcs (m/min)", "120.0"), ("Prop. Source", "1.0"), ("Prop. Demande", "1.0"), ("Seed (Optionnel)", "")]
        for label, default in fields:
            tk.Label(self.sidebar, text=label+":", bg="#ecf0f1",
                     font=("Segoe UI", 8)).pack(anchor="w")
            ent = tk.Entry(self.sidebar, relief="flat",
                           highlightthickness=1, justify="center")
            ent.insert(0, default)
            ent.pack(fill=tk.X, pady=(0, 5))
            self.inputs[label] = ent
            
        tk.Label(self.sidebar, text="Colorer les arcs par :", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.color_var = tk.StringVar(value="Aucune")
        cb_color = ttk.Combobox(self.sidebar, textvariable=self.color_var, values=("Aucune", "Flow (Débit)", "Vitesse"), state="readonly")
        cb_color.pack(fill=tk.X, pady=(0, 10))
        cb_color.bind("<<ComboboxSelected>>", lambda e: self.draw_graph())

        tk.Button(self.sidebar, text="▶ SIMULER", bg="#27ae60", fg="white", font=(
            "Segoe UI", 9, "bold"), command=self.trigger_run).pack(fill=tk.X, pady=(10, 5))
        tk.Button(self.sidebar, text="Recentrer la vue",
                  command=self.reset_view).pack(fill=tk.X)

        tk.Button(self.sidebar, text="Randomiser Demandes", bg="#f39c12", fg="black", 
                  font=("Segoe UI", 8, "bold"), command=self.randomise_demandes).pack(fill=tk.X, pady=(5, 0))

        res_frame = tk.LabelFrame(
            self.sidebar, text="Résultats", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        res_frame.pack(fill=tk.X, pady=10)
        self.res_labels = {}
        for key, text in [("eff", "Eff: N/A"), ("pre", "P.Req: N/A"), ("exp", "Exp: N/A"), ("dem", "Dem: N/A L/min")]:
            lbl = tk.Label(res_frame, text=text,
                           bg="#ecf0f1", font=("Segoe UI", 8))
            lbl.pack(anchor="w")
            self.res_labels[key] = lbl

        self.legend_frame = tk.Frame(main_content, bg="white", width=120)
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.legend_frame.pack_propagate(False)

        self.canvas = tk.Canvas(main_content, bg="#F0F0F0", highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.status_bar = tk.Frame(self, bg="#bdc3c7", height=20)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(
            self.status_bar, text="Prêt", bg="#bdc3c7", font=("Segoe UI", 8))
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
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)
        self.canvas.bind("<Button-5>", self.on_zoom)
        self.canvas.bind("<Double-1>", self.on_canvas_click)

    def toggle_sidebar(self):
        if self.sidebar.winfo_ismapped():
            self.sidebar.pack_forget()
            self.toggle_btn.config(text="▶ Options")
        else:
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self.canvas)
            self.toggle_btn.config(text="◀ Options")

    def set_focus(self, event=None):
        self.tkraise()
        self.app_manager.set_active_window(self)

    def set_active_style(self, is_active):
        color = "#2980b9" if is_active else "#7f8c8d"
        self.title_bar.config(bg=color)
        self.title_label.config(bg=color)

    def close_window(self):
        if self.projet:
            ffi_wrapper.free_graph(
                ffi_wrapper.import_epanet_graph(self.projet))
        self.app_manager.remove_window(self)
        self.destroy()

    def start_drag_window(self, event):
        self.set_focus()
        self._drag_start_x, self._drag_start_y = event.x, event.y

    def do_drag_window(self, event):
        self.place(x=self.winfo_x() - self._drag_start_x + event.x,
                   y=self.winfo_y() - self._drag_start_y + event.y)

    def start_resize_window(self, event):
        self.set_focus()
        self.start_w, self.start_h = self.winfo_width(), self.winfo_height()
        self.start_x, self.start_y = event.x_root, event.y_root

    def do_resize_window(self, event):
        self.place(width=max(400, self.start_w + event.x_root - self.start_x),
                   height=max(300, self.start_h + event.y_root - self.start_y))

    def start_pan(self, event):
        self.set_focus()
        self.last_mouse_x, self.last_mouse_y = event.x, event.y

    def do_pan(self, event):
        self.pan_x += event.x - self.last_mouse_x
        self.pan_y += event.y - self.last_mouse_y
        self.last_mouse_x, self.last_mouse_y = event.x, event.y
        self.draw_graph()

    def on_zoom(self, event):
        factor = 1.2 if (event.num == 4 or event.delta > 0) else 0.8
        wx, wy = (event.x - self.pan_x) / self.scale, - \
        (event.y - self.pan_y) / self.scale
        self.scale *= factor
        self.pan_x, self.pan_y = event.x - \
            (wx * self.scale), event.y + (wy * self.scale)
        self.draw_graph()

    def world_to_screen(self, wx, wy):
        return (wx * self.scale) + self.pan_x, -(wy * self.scale) + self.pan_y

    def update_dashboard(self, reseau):
        eff, p_req, e_pres, d_glob = analyse_tools.get_efficacite(reseau)*100, analyse_tools.get_pression_requise(
            reseau), analyse_tools.get_exposant_pression(reseau), analyse_tools.get_demande_global(reseau)
        self.res_labels["eff"].config(
            text=f"Eff: {eff:.2f}%", fg="#27ae60" if eff > 99 else "#c0392b")
        self.res_labels["pre"].config(text=f"P.Req: {p_req:.1f} m")
        self.res_labels["exp"].config(text=f"Exp: {e_pres:.2f}")
        self.res_labels["dem"].config(text=f"Dem: {d_glob:.1f} L/min")

    def load_file(self, filepath):
        self.title_label.config(
            text=f"|  {filepath.split('/')[-1].split('\\')[-1]}")
        self.projet = ffi_wrapper.create_epanet_project(filepath)
        reseau = ffi_wrapper.import_epanet_graph(self.projet)
        ffi_wrapper.nullifier_flow(reseau)
        self.extract_data(reseau)
        ffi_wrapper.free_graph(reseau)
        self.status_label.config(text="Fichier chargé.")
        self.reset_view()

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

    def randomise_demandes(self):
        if not self.projet:
            messagebox.showinfo("Info", "Veuillez charger un réseau d'abord.")
            return
        
        seed_str = self.inputs["Seed (Optionnel)"].get().strip()
        
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

    def trigger_run(self):
        try:
            mult = float(self.inputs["Mult. Demande"].get())
            v_res, v_arc = float(
                self.inputs["Vit. Rés (m/min)"].get()), float(self.inputs["Vit. Arcs (m/min)"].get())
            p_src, p_dem = float(self.inputs["Prop. Source"].get()), float(self.inputs["Prop. Demande"].get())
            choix_algo, choix_ori = self.algo_var.get(), self.ori_var.get()

            self.status_label.config(text="Calcul en cours...")
            self.update_idletasks()

            ffi_wrapper.modif_multiplicateur(self.projet, mult)

            if choix_algo == "EPANET":
                ffi_wrapper.compute_epanet(self.projet)
                ffi_wrapper.import_epanet_graph(self.projet)

            reseau = None
            if choix_ori == "EPANET":
                ffi_wrapper.compute_epanet(self.projet)
                reseau = ffi_wrapper.import_epanet_graph(self.projet)
                ffi_wrapper.fix_capacite_flow_oriente(reseau, v_res, v_arc)
            elif choix_ori == "Aucune":
                reseau = ffi_wrapper.import_epanet_graph(self.projet)
                ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
            else:
                reseau = ffi_wrapper.import_epanet_graph(self.projet)
                ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
                self.compute_algo(reseau, choix_ori, p_src, p_dem)
                ffi_wrapper.fix_capacite_flow_oriente(reseau, v_res, v_arc)

            self.compute_algo(reseau, choix_algo, p_src, p_dem)

            self.update_dashboard(reseau)
            self.extract_data(reseau)
            ffi_wrapper.free_graph(reseau)
            self.draw_graph()

            self.status_label.config(
                text=f"Simulation terminée ({choix_algo})")

        except ValueError:
            messagebox.showerror("Erreur", "Valeurs invalides.")
        except Exception as e:
            messagebox.showerror("Erreur CFFI", str(e))

    def extract_data(self, reseau):
        self.nodes.clear()
        self.edges.clear()
        self.min_x = self.min_y = float('inf')
        self.max_x = self.max_y = float('-inf')

        nb_sommets = analyse_tools.get_n_sommet(reseau)
        for i in range(nb_sommets):
            s_type = analyse_tools.get_sommet_type(reseau, i)
            x, y = analyse_tools.get_sommet_position(reseau, i)
            self.nodes.append({
                'x': x, 'y': y, 'type': s_type, 'id': i + 1,
                'elevation': analyse_tools.get_sommet_elevation(reseau, i),
                'demande': analyse_tools.get_sommet_demande(reseau, i),
                'pression': analyse_tools.get_sommet_pression(reseau, i),
                'degree': analyse_tools.get_sommet_degree(reseau, i)
            })
            self.min_x, self.max_x = min(self.min_x, x), max(self.max_x, x)
            self.min_y, self.max_y = min(self.min_y, y), max(self.max_y, y)

        arcs_actifs = analyse_tools.extraire_arcs_orientes_dominants(reseau)
        nb_arcs = analyse_tools.get_n_arcs(reseau)
        for k in range(nb_arcs // 2):
            idx_aller, idx_retour = 2 * k, 2 * k + 1
            
            src_type = analyse_tools.get_arc_source_type(reseau, idx_aller)
            dst_type = analyse_tools.get_arc_dest_type(reseau, idx_aller)
            if src_type in (0, 2) or dst_type in (0, 2):
                continue

            x1, y1 = analyse_tools.get_arc_source_position(reseau, idx_aller)
            x2, y2 = analyse_tools.get_arc_dest_position(reseau, idx_aller)
            flow = 0.0
            velocity = 0.0
            
            if idx_aller in arcs_actifs:
                flow = analyse_tools.get_arc_flow(reseau, idx_aller)
                velocity = analyse_tools.compute_velocity(reseau, idx_aller)
            elif idx_retour in arcs_actifs:
                x1, y1, x2, y2 = x2, y2, x1, y1
                flow = analyse_tools.get_arc_flow(reseau, idx_retour)
                velocity = analyse_tools.compute_velocity(reseau, idx_retour)

            self.edges.append({
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 
                'flow': flow, 'velocity': velocity, 
                'type': analyse_tools.get_arc_type(reseau, idx_aller),
                'diametre': analyse_tools.get_arc_diametre(reseau, idx_aller),
                'longueur': analyse_tools.get_arc_longueur(reseau, idx_aller),
                'roughness': analyse_tools.get_arc_roughness(reseau, idx_aller),
                'flow_aller': analyse_tools.get_arc_flow(reseau, idx_aller), 
                'cap_aller': analyse_tools.get_arc_capacite(reseau, idx_aller),
                'flow_retour': analyse_tools.get_arc_flow(reseau, idx_retour), 
                'cap_retour': analyse_tools.get_arc_capacite(reseau, idx_retour)
            })

    def get_dynamic_color(self, val, max_val, mode_couleur):
        """Calcule un dégradé mathématique Bleu (Froid/Faible) -> Rouge (Chaud/Fort)."""
        if mode_couleur == "Aucune":
            return "#34495e"

        ratio = min(1.0, max(0.0, val / max_val))
        r = int(255 * ratio)
        b = int(255 * (1 - ratio))
        return f'#{r:02x}00{b:02x}'

    def draw_graph(self):
        self.canvas.delete("all")
        
        if not self.edges:
            self.update_color_bar(0.0, "Aucune")
            return

        mode_couleur = self.color_var.get()
        max_val = 0.01
        
        if mode_couleur == "Flow (Débit)":
            max_val = max([e['flow'] for e in self.edges] + [0.01])
        elif mode_couleur == "Vitesse":
            max_val = max([e['velocity'] for e in self.edges] + [0.01])

        self.update_color_bar(max_val, mode_couleur)

        for idx, e in enumerate(self.edges):
            sx1, sy1 = self.world_to_screen(e['x1'], e['y1'])
            sx2, sy2 = self.world_to_screen(e['x2'], e['y2'])
            mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2
            
            val_color = e['flow'] if mode_couleur == "Flow (Débit)" else e['velocity']
            
            if mode_couleur == "Aucune":
                color = "#e67e22" if e['type'] == 1 else "black"
                width_line = 3
            elif val_color <= 0.001:
                color = "black"
                width_line = 3
            else:
                color = self.get_dynamic_color(val_color, max_val, mode_couleur)
                width_line = 3

            if e['flow'] > 0.001:
                self.canvas.create_line(sx1, sy1, mx, my, fill=color, width=width_line, arrow=tk.LAST, arrowshape=(8, 10, 3), tags=(f"edge_{idx}", "edge"))
                self.canvas.create_line(mx, my, sx2, sy2, fill=color, width=width_line, tags=(f"edge_{idx}", "edge"))
            else:
                # Pour les conduites complètement inactives, pas de flèche
                self.canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=width_line, tags=(f"edge_{idx}", "edge"))

        # Tracé des Sommets (tags f"node_{idx}")
        r = 5 if mode_couleur != "Aucune" else 4
        for idx, n in enumerate(self.nodes):
            sx, sy = self.world_to_screen(n['x'], n['y'])
            if n['type'] == 1: # Jonction
                self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill="#2c3e50", outline="white", tags=(f"node_{idx}", "node"))
            elif n['type'] == 3: # Réservoir
                self.canvas.create_polygon(sx-r*2, sy-r, sx-r, sy+r, sx+r, sy+r, sx+r*2, sy-r, fill="#3498db", outline="black", tags=(f"node_{idx}", "node"))
            elif n['type'] == 4: # Tank
                self.canvas.create_rectangle(sx-r, sy-r*2, sx+r, sy+r*2, fill="#2ecc71", outline="black", tags=(f"node_{idx}", "node"))


    def update_color_bar(self, max_val, mode_couleur):
        """Dessine la barre de légende verticale (Bleu->Rouge) de manière figée."""
        # Nettoyage complet du panneau de légende
        for widget in self.legend_frame.winfo_children():
            widget.destroy()

        if mode_couleur == "Aucune":
            self.legend_frame.config(width=0)
            return
        
        self.legend_frame.config(width=100) # Légende légèrement rétrécie
        
        # --- Titre et Unité (Fixés en haut) ---
        unit = "(L/min)" if mode_couleur == "Flow (Débit)" else "(m/s)"
        label_text = f"{mode_couleur.split(' (')[0]}\n{unit}"
        tk.Label(self.legend_frame, text=label_text, bg="white", fg="black", font=("Segoe UI", 9, "bold")).place(x=50, y=20, anchor="n")

        # --- Paramètres géométriques réduits et fixes ---
        grad_height = 300 # Hauteur réduite
        grad_width = 20   # Largeur réduite
        
        # --- CANVAS DU GRADIENT ---
        # Placé de manière absolue (ne bougera JAMAIS)
        grad_canvas = tk.Canvas(self.legend_frame, width=grad_width, height=grad_height, bg="white", highlightthickness=1, relief="solid")
        grad_canvas.place(x=70, y=70) # Position fixe depuis le haut-gauche
        
        # Dessin du gradient vertical 
        for y in range(grad_height):
            ratio = (grad_height - y) / grad_height 
            color = self.get_dynamic_color(ratio * max_val, max_val, mode_couleur)
            grad_canvas.create_line(0, y, grad_width, y, fill=color)

        # --- ÉTIQUETTES DE VALEURS ---
        lbl_font = ("Segoe UI", 8)
        
        # Haut (Max)
        tk.Label(self.legend_frame, text=f"{max_val:.2f}", bg="white", fg="black", font=lbl_font).place(x=65, y=70, anchor="e")
        # 3/4
        tk.Label(self.legend_frame, text=f"{max_val*0.75:.2f}", bg="white", fg="black", font=lbl_font).place(x=65, y=70 + (grad_height * 0.25), anchor="e")
        # Milieu (1/2)
        tk.Label(self.legend_frame, text=f"{max_val*0.5:.2f}", bg="white", fg="black", font=lbl_font).place(x=65, y=70 + (grad_height * 0.5), anchor="e")
        # 1/4
        tk.Label(self.legend_frame, text=f"{max_val*0.25:.2f}", bg="white", fg="black", font=lbl_font).place(x=65, y=70 + (grad_height * 0.75), anchor="e")
        # Bas (Zéro)
        tk.Label(self.legend_frame, text=f"0.00", bg="white", fg="black", font=lbl_font).place(x=65, y=70 + grad_height, anchor="e")

    def reset_view(self):
        if not self.nodes:
            return
        self.update_idletasks()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        ww, wh = self.max_x - self.min_x, self.max_y - self.min_y
        if ww <= 0 or wh <= 0:
            self.scale = 1.0
        else:
            self.scale = min((cw*0.8)/ww, (ch*0.8)/wh)
        self.pan_x, self.pan_y = (cw/2) - ((self.min_x + self.max_x)/2 * self.scale), (ch/2) + ((self.min_y + self.max_y)/2 * self.scale)
        self.draw_graph()

    def on_canvas_click(self, event):
        # Détecte l'élément survolé au moment du double-clic
        item = self.canvas.find_withtag("current")
        if not item: return
        
        tags = self.canvas.gettags(item[0])
        for tag in tags:
            if tag.startswith("node_"):
                idx = int(tag.split("_")[1])
                self.show_node_details(idx)
                return
            elif tag.startswith("edge_"):
                idx = int(tag.split("_")[1])
                self.show_edge_details(idx)
                return

    def show_node_details(self, idx):
        n = self.nodes[idx]
        types_sommet = {0: "SOURCE", 1: "JONCTION", 2: "DESTINATION", 3: "RESERVOIR", 4: "TANK"}
        
        msg = f"--- Détails du Sommet ---\n\n"
        msg += f"ID ID_EPANET : {n['id']}\n"
        msg += f"Type de nœud : {types_sommet.get(n['type'], 'INCONNU')}\n"
        msg += f"Élévation : {n['elevation']:.2f} m\n"
        msg += f"Pression calculée : {n['pression']:.2f} m\n"
        msg += f"Demande à la cible : {n['demande']:.2f} L/min\n"
        msg += f"Degré topologique : {n['degree']}"
        
        messagebox.showinfo(f"Sommet ID: {n['id']}", msg)

    def show_edge_details(self, idx):
        e = self.edges[idx]
        types_arc = {0: "TUYAU", 1: "POMPE", 2: "VALVE"}

        msg = f"--- Conduites Symétriques Jumelles ---\n\n"
        msg += f"Type structurel : {types_arc.get(e['type'], 'INCONNU')}\n"
        msg += f"Diamètre nominal : {e['diametre']:.1f} mm\n"
        msg += f"Longueur physique : {e['longueur']:.1f} m\n\n"
        msg += f" - ARC ALLER (Index C: {idx*2}) :\n"
        msg += f"  • Débit (Flow) : {e['flow_aller']:.4f} L/min\n"
        msg += f"  • Capacité Max : {e['cap_aller']:.2f} L/min\n\n"
        msg += f" - ARC RETOUR (Index C: {idx*2+1}) :\n"
        msg += f"  • Débit (Flow) : {e['flow_retour']:.4f} L/min\n"
        msg += f"  • Capacité Max : {e['cap_retour']:.2f} L/min\n\n"
        msg += f" - Métriques actives de rendu :\n"
        msg += f"  • Débit dominant : {e['flow']:.4f} L/min\n"
        msg += f"  • Vitesse calculée : {e['velocity']:.4f} m/min"
        
        messagebox.showinfo(f"Double Conduite #{idx}", msg)
