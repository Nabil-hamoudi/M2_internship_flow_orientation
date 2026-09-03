import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import numpy as np
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.wrapper_tools import ffi_wrapper
from src.backend.run import run_single_simulation
from src.backend.extract_data import (
    ALGORITHMES, ORIENTATIONS, CAPACITES, DEMANDES, 
    COULEURS_SOMMET, COULEURS_ARC
)

matplotlib.use("TkAgg")

class InternalWindow(tk.Frame):
    def __init__(self, parent, app_manager, title="Réseau"):
        super().__init__(parent, bg="white", bd=2, relief="groove")
        self.app_manager = app_manager
        self.current_filepath = None
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

        self.colors_arc = ["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000"]
        self.colors_node = ["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff0000"]
        self.classif_arc = "Equal Intervals"
        self.classif_node = "Equal Intervals"
        self.custom_bounds_arc = [0.0, 25.0, 50.0, 75.0, 100.0]
        self.custom_bounds_node = [0.0, 25.0, 50.0, 75.0, 100.0]

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

        self.sidebar_container = tk.Frame(main_content, width=240, bg="#ecf0f1", relief="solid", bd=1)
        self.sidebar_container.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_container.pack_propagate(False)

        self.canvas_side = tk.Canvas(self.sidebar_container, bg="#ecf0f1", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.sidebar_container, orient="vertical", command=self.canvas_side.yview)
        
        self.sidebar = tk.Frame(self.canvas_side, bg="#ecf0f1", padx=10, pady=10)
        self.sidebar.bind("<Configure>", lambda e: self.canvas_side.configure(scrollregion=self.canvas_side.bbox("all")))
        self.canvas_side.create_window((0, 0), window=self.sidebar, anchor="nw", width=220)
        self.canvas_side.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _on_mousewheel(event):
            if event.num == 4 or getattr(event, 'delta', 0) > 0:
                self.canvas_side.yview_scroll(-1, "units")
            elif event.num == 5 or getattr(event, 'delta', 0) < 0:
                self.canvas_side.yview_scroll(1, "units")

        def _bind_scroll(e):
            self.sidebar_container.bind_all("<MouseWheel>", _on_mousewheel)
            self.sidebar_container.bind_all("<Button-4>", _on_mousewheel)
            self.sidebar_container.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_scroll(e):
            self.sidebar_container.unbind_all("<MouseWheel>")
            self.sidebar_container.unbind_all("<Button-4>")
            self.sidebar_container.unbind_all("<Button-5>")

        self.sidebar_container.bind("<Enter>", _bind_scroll)
        self.sidebar_container.bind("<Leave>", _unbind_scroll)

        tk.Label(self.sidebar, text="Algo Principal:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.algo_var = tk.StringVar(value="EPANET")
        ttk.Combobox(self.sidebar, textvariable=self.algo_var, values=ALGORITHMES, state="readonly").pack(fill=tk.X, pady=(0, 5))

        tk.Label(self.sidebar, text="Capacite:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.capa_var = tk.StringVar(value="Vitesse Max")
        ttk.Combobox(self.sidebar, textvariable=self.capa_var, values=CAPACITES, state="readonly").pack(fill=tk.X, pady=(0, 10))

        tk.Label(self.sidebar, text="Orientation:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.ori_var = tk.StringVar(value="Aucune")
        ttk.Combobox(self.sidebar, textvariable=self.ori_var, values=ORIENTATIONS, state="readonly").pack(fill=tk.X, pady=(0, 10))

        tk.Label(self.sidebar, text="Demande:", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.dem_var = tk.StringVar(value="Inchanger")
        ttk.Combobox(self.sidebar, textvariable=self.dem_var, values=DEMANDES, state="readonly").pack(fill=tk.X, pady=(0, 10))

        self.inputs = {}
        fields = [("Mult. Demande", "1.0"), ("Vit. Rés (m/s)", "3.0"),
                  ("Vit. Arcs (m/s)", "2.0"), ("Prop. Source", "1.0"),
                  ("Prop. Demande", "1.0"), ("Portion", "0.1"), 
                  ("Ecart-Type", "0.3"), ("Seed (Optionnel)", "")]
        
        for label, default in fields:
            tk.Label(self.sidebar, text=label+":", bg="#ecf0f1", font=("Segoe UI", 8)).pack(anchor="w")
            ent = tk.Entry(self.sidebar, relief="flat", highlightthickness=1, justify="center")
            ent.insert(0, default)
            ent.pack(fill=tk.X, pady=(0, 5))
            self.inputs[label] = ent
            
        tk.Label(self.sidebar, text="Colorer les arcs par :", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.color_var = tk.StringVar(value="Aucune")
        cb_color = ttk.Combobox(self.sidebar, textvariable=self.color_var, values=COULEURS_ARC, state="readonly")
        cb_color.pack(fill=tk.X, pady=(0, 5))
        cb_color.bind("<<ComboboxSelected>>", lambda e: self.draw_graph())

        tk.Label(self.sidebar, text="Colorer les sommets par :", bg="#ecf0f1", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(5, 0))
        self.color_node_var = tk.StringVar(value="Aucune")
        cb_node_color = ttk.Combobox(self.sidebar, textvariable=self.color_node_var, values=COULEURS_SOMMET, state="readonly")
        cb_node_color.pack(fill=tk.X, pady=(0, 10))
        cb_node_color.bind("<<ComboboxSelected>>", lambda e: self.draw_graph())

        tk.Button(self.sidebar, text="▶ SIMULER", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=self.trigger_run).pack(fill=tk.X, pady=(10, 5))
        tk.Button(self.sidebar, text="Recentrer la vue", command=self.reset_view).pack(fill=tk.X)

        res_frame = tk.LabelFrame(self.sidebar, text="Résultats", bg="#ecf0f1", font=("Segoe UI", 8, "bold"))
        res_frame.pack(fill=tk.X, pady=10)
        self.res_labels = {}
        for key, text in [("eff", "Eff: N/A"), ("pre", "P.Req: N/A"), ("exp", "Exp: N/A"), ("dem", "Dem: N/A L/min")]:
            lbl = tk.Label(res_frame, text=text, bg="#ecf0f1", font=("Segoe UI", 8))
            lbl.pack(anchor="w")
            self.res_labels[key] = lbl

        self.legend_frame = tk.Frame(main_content, bg="white", width=120)
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.legend_frame.pack_propagate(False)

        self.canvas = tk.Canvas(main_content, bg="#F0F0F0", highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.status_bar = tk.Frame(self, bg="#bdc3c7", height=20)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(self.status_bar, text="Prêt", bg="#bdc3c7", font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.grip = tk.Label(self.status_bar, text="◢", bg="#bdc3c7", fg="#7f8c8d", cursor="bottom_right_corner")
        self.grip.pack(side=tk.RIGHT, anchor="se", padx=2)
        
        tk.Button(self.sidebar, text="Options des Couleurs", bg="#9b59b6", fg="white", font=("Segoe UI", 8, "bold"), command=self.open_color_settings).pack(fill=tk.X, pady=(5, 10))

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

    def load_file(self, filepath):
        self.current_filepath = filepath
        self.title_label.config(text=f"|  {os.path.basename(filepath)}")
        try:
            results = run_single_simulation(
                filepath=filepath, choix_algo="EPANET", choix_ori="Aucune", 
                choix_capa="Vitesse Max", choix_dem="Inchanger", 
                p_src=1.0, p_dem=1.0, v_res=2.0, v_arc=2.0, mult_epa=1.0, portion=1.0, ecart_type=0.3
            )
            self.nodes = results["nodes"]
            self.edges = results["edges"]
            self.min_x, self.max_x, self.min_y, self.max_y = results["bounds"]
            self.update_dashboard(results["metrics"])
            self.status_label.config(text="Fichier chargé.")
            self.reset_view()
        except Exception as e:
            messagebox.showerror("Erreur de chargement", str(e))

    def trigger_run(self):
        try:
            v_res = float(self.inputs["Vit. Rés (m/s)"].get())
            v_arc = float(self.inputs["Vit. Arcs (m/s)"].get())
            p_src = float(self.inputs["Prop. Source"].get())
            p_dem = float(self.inputs["Prop. Demande"].get())
            choix_algo = self.algo_var.get()
            choix_ori = self.ori_var.get()
            choix_capa = self.capa_var.get()
            choix_dem = self.dem_var.get()
            mult = float(self.inputs["Mult. Demande"].get())
            portion_val = float(self.inputs["Portion"].get())
            ecart_val = float(self.inputs["Ecart-Type"].get())

            seed_str = self.inputs["Seed (Optionnel)"].get().strip()
            seed_val = None
            if seed_str:
                seed_val = int(seed_str)
                if seed_val < 0 or seed_val > 4294967295:
                    messagebox.showwarning("Attention", "La seed doit être comprise entre 0 et 4294967295.")
                    return

            if not self.current_filepath:
                return

            self.status_label.config(text="Calcul en cours...")
            self.update_idletasks()

            results = run_single_simulation(
                filepath=self.current_filepath, choix_algo=choix_algo, 
                choix_ori=choix_ori, choix_capa=choix_capa, choix_dem=choix_dem, 
                p_src=p_src, p_dem=p_dem, v_res=v_res, v_arc=v_arc, 
                mult_epa=mult, portion=portion_val, seed=seed_val, ecart_type=ecart_val
            )

            self.nodes = results["nodes"]
            self.edges = results["edges"]
            self.min_x, self.max_x, self.min_y, self.max_y = results["bounds"]
            
            self.update_dashboard(results["metrics"])
            self.draw_graph()

            self.status_label.config(text=f"Simulation terminée ({choix_algo})")

        except ValueError:
            messagebox.showerror("Erreur", "Valeurs invalides.")
        except Exception as e:
            messagebox.showerror("Erreur CFFI", str(e))

    def update_dashboard(self, metrics):
        eff = metrics["efficacite"]
        p_req = metrics["pression_requise"]
        e_pres = metrics["exposant_pression"]
        d_glob = metrics["demande_globale"]
        
        self.res_labels["eff"].config(text=f"Eff: {eff:f}%", fg="#27ae60" if eff > 99 else "#c0392b")
        self.res_labels["pre"].config(text=f"P.Req: {p_req:f} m")
        self.res_labels["exp"].config(text=f"Exp: {e_pres:f}")
        self.res_labels["dem"].config(text=f"Dem: {d_glob:f} L/min")

    def toggle_sidebar(self):
        if self.sidebar_container.winfo_ismapped():
            self.sidebar_container.pack_forget()
            self.toggle_btn.config(text="▶ Options")
        else:
            self.sidebar_container.pack(side=tk.LEFT, fill=tk.Y, before=self.canvas)
            self.toggle_btn.config(text="◀ Options")

    def set_focus(self, event=None):
        self.tkraise()
        self.app_manager.set_active_window(self)

    def set_active_style(self, is_active):
        color = "#2980b9" if is_active else "#7f8c8d"
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
        self.place(width=max(400, self.start_w + event.x_root - self.start_x), height=max(300, self.start_h + event.y_root - self.start_y))

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
        wx, wy = (event.x - self.pan_x) / self.scale, - (event.y - self.pan_y) / self.scale
        self.scale *= factor
        self.pan_x, self.pan_y = event.x - (wx * self.scale), event.y + (wy * self.scale)
        self.draw_graph()

    def world_to_screen(self, wx, wy):
        return (wx * self.scale) + self.pan_x, -(wy * self.scale) + self.pan_y

    def open_color_settings(self):
        win = tk.Toplevel(self)
        win.title("Symbologie & Couleurs")
        win.geometry("500x480")
        win.configure(bg="white")
        
        self.classif_node_var = tk.StringVar(value=getattr(self, 'classif_node', "Equal Quantiles"))
        self.classif_arc_var = tk.StringVar(value=getattr(self, 'classif_arc', "Equal Quantiles"))
        
        frame_node = tk.LabelFrame(win, text=" Sommets (Couleurs & Classification) ", bg="white", font=("Segoe UI", 9, "bold"))
        frame_node.pack(fill="x", padx=15, pady=10)

        color_f_n = tk.Frame(frame_node, bg="white")
        color_f_n.pack(fill="x", pady=5)
        self.btn_nodes = []
        for i, color in enumerate(self.colors_node):
            btn = tk.Button(color_f_n, bg=color, width=4, height=1, relief="ridge", command=lambda idx=i: self.choose_color('node', idx))
            btn.pack(side="left", padx=5, expand=True)
            self.btn_nodes.append(btn)

        rad_f_n = tk.Frame(frame_node, bg="white")
        rad_f_n.pack(fill="x", pady=5)
        tk.Radiobutton(rad_f_n, text="Equal Intervals", variable=self.classif_node_var, value="Equal Intervals", bg="white").pack(side="left", padx=5)
        tk.Radiobutton(rad_f_n, text="Equal Quantiles", variable=self.classif_node_var, value="Equal Quantiles", bg="white").pack(side="left", padx=5)
        tk.Radiobutton(rad_f_n, text="Personnalisé", variable=self.classif_node_var, value="Personnalisé", bg="white").pack(side="left", padx=5)

        cust_f_n = tk.Frame(frame_node, bg="white")
        cust_f_n.pack(fill="x", pady=5)
        tk.Label(cust_f_n, text="Seuils (Min -> Max) :", bg="white", font=("Segoe UI", 8)).pack(side="left", padx=5)
        self.entries_node = []
        for val in getattr(self, 'custom_bounds_node', [0.0, 25.0, 50.0, 75.0, 100.0]):
            ent = tk.Entry(cust_f_n, width=6, justify="center")
            ent.insert(0, str(val))
            ent.pack(side="left", padx=2)
            self.entries_node.append(ent)

        frame_arc = tk.LabelFrame(win, text=" Arcs (Couleurs & Classification) ", bg="white", font=("Segoe UI", 9, "bold"))
        frame_arc.pack(fill="x", padx=15, pady=5)

        color_f_a = tk.Frame(frame_arc, bg="white")
        color_f_a.pack(fill="x", pady=5)
        self.btn_arcs = []
        for i, color in enumerate(self.colors_arc):
            btn = tk.Button(color_f_a, bg=color, width=4, height=1, relief="ridge", command=lambda idx=i: self.choose_color('arc', idx))
            btn.pack(side="left", padx=5, expand=True)
            self.btn_arcs.append(btn)
            
        rad_f_a = tk.Frame(frame_arc, bg="white")
        rad_f_a.pack(fill="x", pady=5)
        tk.Radiobutton(rad_f_a, text="Equal Intervals", variable=self.classif_arc_var, value="Equal Intervals", bg="white").pack(side="left", padx=5)
        tk.Radiobutton(rad_f_a, text="Equal Quantiles", variable=self.classif_arc_var, value="Equal Quantiles", bg="white").pack(side="left", padx=5)
        tk.Radiobutton(rad_f_a, text="Personnalisé", variable=self.classif_arc_var, value="Personnalisé", bg="white").pack(side="left", padx=5)

        cust_f_a = tk.Frame(frame_arc, bg="white")
        cust_f_a.pack(fill="x", pady=5)
        tk.Label(cust_f_a, text="Seuils (Min -> Max) :", bg="white", font=("Segoe UI", 8)).pack(side="left", padx=5)
        self.entries_arc = []
        for val in getattr(self, 'custom_bounds_arc', [0.0, 25.0, 50.0, 75.0, 100.0]):
            ent = tk.Entry(cust_f_a, width=6, justify="center")
            ent.insert(0, str(val))
            ent.pack(side="left", padx=2)
            self.entries_arc.append(ent)

        action_frame = tk.Frame(win, bg="white")
        action_frame.pack(fill="x", pady=15)
        
        def apply_and_close():
            self.classif_node = self.classif_node_var.get()
            self.classif_arc = self.classif_arc_var.get()
            try:
                self.custom_bounds_node = [float(e.get()) for e in self.entries_node]
                self.custom_bounds_arc = [float(e.get()) for e in self.entries_arc]
            except ValueError:
                messagebox.showerror("Erreur de saisie", "Les valeurs personnalisées doivent être des nombres.")
                return
            self.draw_graph()
            win.destroy()
            
        tk.Button(action_frame, text="Appliquer & Fermer", bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), command=apply_and_close).pack(side="right", padx=15)

    def choose_color(self, type_target, idx):
        current_color = self.colors_arc[idx] if type_target == 'arc' else self.colors_node[idx]
        color = colorchooser.askcolor(initialcolor=current_color, title=f"Choisir la couleur {idx+1}")

        if color[1]: 
            if type_target == 'arc':
                self.colors_arc[idx] = color[1]
                self.btn_arcs[idx].config(bg=color[1])
            else:
                self.colors_node[idx] = color[1]
                self.btn_nodes[idx].config(bg=color[1])

    def get_dynamic_color(self, val, boundaries, is_node=False):
        palette = self.colors_node if is_node else self.colors_arc
        
        if val <= boundaries[0]: return palette[0]
        if val >= boundaries[-1]: return palette[-1]
        
        def hex_to_rgb(h): return tuple(int(h.strip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        for i in range(len(boundaries) - 1):
            if boundaries[i] <= val <= boundaries[i+1]:
                segment_min = boundaries[i]
                segment_max = boundaries[i+1]
                
                if segment_max == segment_min:
                    return palette[i]
                    
                local_ratio = (val - segment_min) / (segment_max - segment_min)
                
                r1, g1, b1 = hex_to_rgb(palette[i])
                r2, g2, b2 = hex_to_rgb(palette[i+1])
                
                r = int(r1 + (r2 - r1) * local_ratio)
                g = int(g1 + (g2 - g1) * local_ratio)
                b = int(b1 + (b2 - b1) * local_ratio)
                
                return f'#{r:02x}{g:02x}{b:02x}'
        
        return palette[-1]

    def draw_graph(self):
        self.canvas.delete("all")
        
        if not self.nodes and not self.edges:
            self.update_color_bar([0]*5, "Aucune", [0]*5, "Aucune")
            return

        mode_couleur = self.color_var.get()
        edge_vals = []
        if mode_couleur == "Flow (Débit)": edge_vals = [e['flow'] for e in self.edges]
        elif mode_couleur == "Vitesse": edge_vals = [e['velocity'] for e in self.edges]
        elif mode_couleur == "Roughness (Rugosité)": edge_vals = [e['roughness'] for e in self.edges]
        elif mode_couleur == "Différence d'Élévation": edge_vals = [e['diff_elevation'] for e in self.edges] # Ajout

        boundaries_arc = [0.0, 0.25, 0.5, 0.75, 1.0]
        if edge_vals:
            max_val = max(edge_vals)
            min_val = min(edge_vals)
            classif = getattr(self, 'classif_arc', 'Equal Intervals')
            
            if classif == "Personnalisé":
                boundaries_arc = sorted(getattr(self, 'custom_bounds_arc', [0.0, 25.0, 50.0, 75.0, 100.0]))
            elif classif == "Equal Quantiles":
                non_zeros = [v for v in edge_vals]
                if len(non_zeros) >= 2:
                    boundaries_arc = list(np.quantile(non_zeros, [0, 0.25, 0.5, 0.75, 1.0]))
                else:
                    boundaries_arc = [min_val + (max_val - min_val) * (i/4.0) for i in range(5)]
            else:
                boundaries_arc = [min_val + (max_val - min_val) * (i/4.0) for i in range(5)]

        mode_couleur_node = self.color_node_var.get()
        node_vals = []
        if mode_couleur_node == "Élévation": node_vals = [n['elevation'] for n in self.nodes]
        elif mode_couleur_node == "Pression": node_vals = [n['pression'] for n in self.nodes]
        elif mode_couleur_node == "Demande": node_vals = [n['demande'] for n in self.nodes]
        elif mode_couleur_node == "Satisfaction": node_vals = [n['satisfaction'] for n in self.nodes]

        boundaries_node = [0.0, 0.25, 0.5, 0.75, 1.0]
        if node_vals:
            max_val_node = max(node_vals)
            classif_node = getattr(self, 'classif_node', 'Equal Intervals')
            
            if classif_node == "Personnalisé":
                boundaries_node = sorted(getattr(self, 'custom_bounds_node', [0.0, 25.0, 50.0, 75.0, 100.0]))
            elif classif_node == "Equal Quantiles":
                non_zeros = [v for v in node_vals]
                if len(non_zeros) >= 2:
                    boundaries_node = list(np.quantile(non_zeros, [0, 0.25, 0.5, 0.75, 1.0]))
                else:
                    boundaries_node = [max_val_node * (i/4.0) for i in range(5)]
            else:
                boundaries_node = [max_val_node * (i/4.0) for i in range(5)]

        self.update_color_bar(boundaries_arc, mode_couleur, boundaries_node, mode_couleur_node)

        for idx, e in enumerate(self.edges):
            sx1, sy1 = self.world_to_screen(e['x1'], e['y1'])
            sx2, sy2 = self.world_to_screen(e['x2'], e['y2'])
            mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2
            
            val_color = 0.0
            if mode_couleur == "Flow (Débit)": val_color = e['flow']
            elif mode_couleur == "Vitesse": val_color = e['velocity']
            elif mode_couleur == "Roughness (Rugosité)": val_color = e['roughness']
            elif mode_couleur == "Différence d'Élévation": val_color = e['diff_elevation']

            width_line = 3
            if mode_couleur == "Aucune":
                color = "#e67e22" if ffi_wrapper.get_nom_type_arc(e['type']) == "RESERVOIR" else "black"
            elif val_color == 0.0 and mode_couleur in ("Flow (Débit)", "Vitesse", "Roughness (Rugosité)"):
                color = "black"
            else:
                color = self.get_dynamic_color(val_color, boundaries_arc, is_node=False)

            if e['flow'] > 0.0:
                self.canvas.create_line(sx1, sy1, mx, my, fill=color, width=width_line, arrow=tk.LAST, arrowshape=(8, 10, 3), tags=(f"edge_{idx}", "edge"))
                self.canvas.create_line(mx, my, sx2, sy2, fill=color, width=width_line, tags=(f"edge_{idx}", "edge"))
            else:
                self.canvas.create_line(sx1, sy1, sx2, sy2, fill=color, width=width_line, tags=(f"edge_{idx}", "edge"))

        r = 5 if (mode_couleur != "Aucune" or mode_couleur_node != "Aucune") else 4
        for idx, n in enumerate(self.nodes):
            sx, sy = self.world_to_screen(n['x'], n['y'])
            
            val_color_node = 0.0
            if mode_couleur_node == "Élévation": val_color_node = n['elevation']
            elif mode_couleur_node == "Pression": val_color_node = n['pression']
            elif mode_couleur_node == "Demande": val_color_node = n['demande']
            elif mode_couleur_node == "Satisfaction": val_color_node = n['satisfaction']

            if mode_couleur_node == "Aucune":
                if ffi_wrapper.get_nom_type_sommet(n['type']) == "JONCTION": node_color = "#2c3e50"
                elif ffi_wrapper.get_nom_type_sommet(n['type']) == "RESERVOIR": node_color = "#3498db"
                elif ffi_wrapper.get_nom_type_sommet(n['type']) == "TANK": node_color = "#2ecc71"
                else: node_color = "black"
            elif val_color_node == 0.0 and mode_couleur_node in ("Élévation", "Pression", "Demande"):
                node_color = "black"
            else:
                node_color = self.get_dynamic_color(val_color_node, boundaries_node, is_node=True)
                if mode_couleur_node == "Satisfaction" and n['demande'] == 0.0:
                    node_color = "black"

            if ffi_wrapper.get_nom_type_sommet(n['type']) == "JONCTION":
                self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill=node_color, outline="white", tags=(f"node_{idx}", "node"))
            elif ffi_wrapper.get_nom_type_sommet(n['type']) == "RESERVOIR":
                self.canvas.create_polygon(sx-r*2, sy-r, sx-r, sy+r, sx+r, sy+r, sx+r*2, sy-r, fill=node_color, outline="black", tags=(f"node_{idx}", "node"))
            elif ffi_wrapper.get_nom_type_sommet(n['type']) == "TANK":
                self.canvas.create_rectangle(sx-r, sy-r*2, sx+r, sy+r*2, fill=node_color, outline="black", tags=(f"node_{idx}", "node"))

    def update_color_bar(self, boundaries_arc, mode_couleur_edge, boundaries_node, mode_couleur_node):
        for widget in self.legend_frame.winfo_children():
            widget.destroy()

        if mode_couleur_edge == "Aucune" and mode_couleur_node == "Aucune":
            self.legend_frame.config(width=0)
            return
        
        self.legend_frame.config(width=110)

        center_x = 75
        current_y = 15
        lbl_font = ("Segoe UI", 8)
        
        nb_legends = (mode_couleur_edge != "Aucune") + (mode_couleur_node != "Aucune")
        grad_height = 180 if nb_legends == 2 else 250
        grad_width = 15

        def draw_gradient_strip(canvas, palette):
            def hex_to_rgb(h): return tuple(int(h.strip('#')[i:i+2], 16) for i in (0, 2, 4))
            n_colors = len(palette)
            for y in range(grad_height):
                ratio = (grad_height - y) / grad_height 
                segment = ratio * (n_colors - 1)
                idx1 = int(segment)
                idx2 = min(idx1 + 1, n_colors - 1)
                local_ratio = segment - idx1
                r1, g1, b1 = hex_to_rgb(palette[idx1])
                r2, g2, b2 = hex_to_rgb(palette[idx2])
                r = int(r1 + (r2 - r1) * local_ratio)
                g = int(g1 + (g2 - g1) * local_ratio)
                b = int(b1 + (b2 - b1) * local_ratio)
                canvas.create_line(0, y, grad_width, y, fill=f'#{r:02x}{g:02x}{b:02x}')

        if mode_couleur_node != "Aucune":
            if mode_couleur_node in ("Élévation", "Pression"): unit = "(m)"
            elif mode_couleur_node == "Satisfaction": unit = "(%)"
            else: unit = "(L/min)"
            label_text = f"Sommets:\n{mode_couleur_node}\n{unit}"
            tk.Label(self.legend_frame, text=label_text, bg="white", fg="black", font=("Segoe UI", 8, "bold")).place(x=center_x, y=current_y, anchor="n")
            
            y_offset = current_y + 50
            grad_canvas = tk.Canvas(self.legend_frame, width=grad_width, height=grad_height, bg="white", highlightthickness=1, relief="solid")
            grad_canvas.place(x=center_x - (grad_width/2), y=y_offset)
            
            draw_gradient_strip(grad_canvas, self.colors_node)

            for i in range(5):
                val = boundaries_node[4 - i]
                y_pos = y_offset + (grad_height * (i / 4.0))
                tk.Label(self.legend_frame, text=f"{val:.2f}", bg="white", fg="black", font=lbl_font).place(x=center_x - 12, y=y_pos, anchor="e")
            
            current_y = y_offset + grad_height + 20

        if mode_couleur_edge != "Aucune":
            unit = "(L/min)" if mode_couleur_edge == "Flow (Débit)" else ("(m)" if mode_couleur_edge == "Différence d'Élévation" else ("" if mode_couleur_edge == "Roughness (Rugosité)" else "(m/s)"))
            label_text = f"Arcs:\n{mode_couleur_edge.split(' (')[0]}\n{unit}"
            tk.Label(self.legend_frame, text=label_text, bg="white", fg="black", font=("Segoe UI", 8, "bold")).place(x=center_x, y=current_y, anchor="n")
            
            y_offset = current_y + 50
            grad_canvas = tk.Canvas(self.legend_frame, width=grad_width, height=grad_height, bg="white", highlightthickness=1, relief="solid")
            grad_canvas.place(x=center_x - (grad_width/2), y=y_offset)
            
            draw_gradient_strip(grad_canvas, self.colors_arc)

            for i in range(5):
                val = boundaries_arc[4 - i]
                y_pos = y_offset + (grad_height * (i / 4.0))
                tk.Label(self.legend_frame, text=f"{val:.2f}", bg="white", fg="black", font=lbl_font).place(x=center_x - 12, y=y_pos, anchor="e")

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
        msg = f"--- Détails du Sommet ---\n\n"
        msg += f"ID : {n['id']}\n"
        msg += f"Type de nœud : {ffi_wrapper.get_nom_type_sommet(n['type'])}\n"
        msg += f"Élévation : {n['elevation']:f} m\n"
        msg += f"Pression calculée : {n['pression']:f} m\n"
        msg += f"Demande à la cible : {n['demande']:f} L/min\n"
        msg += f"Demande satisfaite à la cible : {n['satisfaction']:f} %\n"
        msg += f"Degré topologique : {n['degree']}"
        messagebox.showinfo(f"Sommet ID: {n['id']}", msg)

    def show_edge_details(self, idx):
        e = self.edges[idx]
        msg = f"--- Conduites Symétriques Jumelles ---\n\n"
        msg += f"Type structurel : {ffi_wrapper.get_nom_type_arc(e['type'])}\n"
        msg += f"Diamètre nominal : {e['diametre']:f} mm\n"
        msg += f"Longueur physique : {e['longueur']:f} m\n\n"
        msg += f" - ARC ALLER (Index C: {idx*2}) :\n"
        msg += f"  • Débit (Flow) : {e['flow_aller']:f} L/min\n"
        msg += f"  • Capacité Max : {e['cap_aller']:f} L/min\n\n"
        msg += f" - ARC RETOUR (Index C: {idx*2+1}) :\n"
        msg += f"  • Débit (Flow) : {e['flow_retour']:f} L/min\n"
        msg += f"  • Capacité Max : {e['cap_retour']:f} L/min\n\n"
        msg += f" - Métriques actives de rendu :\n"
        msg += f"  • Débit dominant : {e['flow']:f} L/min\n"
        msg += f"  • Rugosité (Roughness) : {e['roughness']}\n"
        msg += f"  • Vitesse calculée : {e['velocity']:f} m/s"
        messagebox.showinfo(f"Double Conduite #{idx}", msg)