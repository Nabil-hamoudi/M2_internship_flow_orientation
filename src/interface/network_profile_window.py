"""
Profil Statistique Intra-Réseau — Fenêtre d'Interface

Fenêtre tkinter affichant les distributions de métriques
par catégorie d'éléments pour un réseau unique.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

from src.backend.network_profile import (
    NODE_CATEGORIES, EDGE_CATEGORIES,
    NODE_METRICS, EDGE_METRICS,
    extract_node_profiles, extract_edge_profiles,
    get_flat_profiles,
    compute_category_stats, compute_global_summary,
    compute_descriptive_stats,
)

matplotlib.use("TkAgg")

# ─── Palettes de couleurs par catégorie ──────────────────────

CATEGORY_COLORS = {
    # Sommets
    "Réservoirs": "#3498db",
    "Tanks (Cuves)": "#2ecc71",
    "Jonctions (avec demande)": "#e74c3c",
    "Jonctions (sans demande)": "#95a5a6",
    # Arcs
    "Tuyaux": "#e67e22",
    "Pompes": "#9b59b6",
    "Vannes": "#1abc9c",
}


class NetworkProfileWindow(tk.Frame):
    """Fenêtre d'analyse du profil statistique d'un réseau unique."""

    TITLE_COLOR = "#16a085"
    TITLE_COLOR_ACTIVE = "#1abc9c"

    def __init__(self, parent, app_manager, nodes, edges, metrics, title="Profil Statistique"):
        super().__init__(parent, bg="white", bd=2, relief="groove")
        self.app_manager = app_manager

        # Données du réseau
        self.nodes = nodes
        self.edges = edges
        self.metrics = metrics

        # Extraction des profils
        self.node_profiles = extract_node_profiles(nodes)
        self.edge_profiles = extract_edge_profiles(edges)
        
        self.flat_nodes, self.flat_edges = get_flat_profiles(nodes, edges)

        self.node_stats = compute_category_stats(self.node_profiles, NODE_METRICS)
        self.edge_stats = compute_category_stats(self.edge_profiles, EDGE_METRICS)

        self.global_summary = compute_global_summary(
            nodes, edges,
            efficacite=metrics.get("efficacite"),
            demande_globale=metrics.get("demande_globale"),
        )

        # Variables UI
        self.category_vars = {}

        self.setup_ui(title)
        self.setup_bindings()
        self.place(x=80, y=80, width=1150, height=750)
        self.set_focus()

        # Tracé initial
        self.update_plot()

    # ─── Construction de l'UI ────────────────────────────────

    def setup_ui(self, title):
        # Barre de titre
        self.title_bar = tk.Frame(self, bg=self.TITLE_COLOR, relief="flat", bd=0, height=25)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)

        self.title_label = tk.Label(
            self.title_bar, text=f"📊  {title}", bg=self.TITLE_COLOR,
            fg="white", font=("Segoe UI", 9, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=5)

        self.close_btn = tk.Button(
            self.title_bar, text="X", bg="#e74c3c", fg="white",
            bd=0, width=3, command=self.close_window
        )
        self.close_btn.pack(side=tk.RIGHT)

        # Contenu principal
        main_content = tk.Frame(self, bg="white")
        main_content.pack(fill=tk.BOTH, expand=True)

        # ── Sidebar scrollable ──
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

        self._setup_sidebar_scroll()

        # ── Section : Type de graphe ──
        tk.Label(self.sidebar, text="Type de Graphe", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.plot_type_var = tk.StringVar(value="Boîte à moustaches")
        self.cb_plot_type = ttk.Combobox(
            self.sidebar, textvariable=self.plot_type_var,
            values=["Boîte à moustaches", "Histogramme", "Radar Chart", "Tableau récapitulatif", "Nuage de points", "Carte de chaleur"],
            state="readonly"
        )
        self.cb_plot_type.pack(fill=tk.X, pady=(0, 8))
        self.cb_plot_type.bind("<<ComboboxSelected>>", self.update_plot)

        # ── Section : Domaine ──
        tk.Label(self.sidebar, text="Domaine", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.domain_var = tk.StringVar(value="Sommets (Nœuds)")
        self.cb_domain = ttk.Combobox(
            self.sidebar, textvariable=self.domain_var,
            values=["Sommets (Nœuds)", "Arcs (Liens)"],
            state="readonly"
        )
        self.cb_domain.pack(fill=tk.X, pady=(0, 8))
        self.cb_domain.bind("<<ComboboxSelected>>", self._on_domain_change)

        # ── Section : Métrique ──
        tk.Label(self.sidebar, text="Axe X (Regroupement / M1)", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.metric_var = tk.StringVar(value="Catégorie")
        self.cb_metric = ttk.Combobox(
            self.sidebar, textvariable=self.metric_var,
            values=["Catégorie"] + [m[0] for m in NODE_METRICS],
            state="readonly"
        )
        self.cb_metric.pack(fill=tk.X, pady=(0, 8))
        self.cb_metric.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Axe Y (Valeur / M2)", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.metric2_var = tk.StringVar(value=NODE_METRICS[0][0])
        self.cb_metric2 = ttk.Combobox(
            self.sidebar, textvariable=self.metric2_var,
            values=[m[0] for m in NODE_METRICS],
            state="readonly"
        )
        self.cb_metric2.pack(fill=tk.X, pady=(0, 8))
        self.cb_metric2.bind("<<ComboboxSelected>>", self.update_plot)

        tk.Label(self.sidebar, text="Couleur (Nuage/Heatmap / M3)", bg="#ecf0f1", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        self.metric3_var = tk.StringVar(value="Catégorie")
        self.cb_metric3 = ttk.Combobox(
            self.sidebar, textvariable=self.metric3_var,
            values=["Catégorie"] + [m[0] for m in NODE_METRICS],
            state="readonly"
        )
        self.cb_metric3.pack(fill=tk.X, pady=(0, 8))
        self.cb_metric3.bind("<<ComboboxSelected>>", self.update_plot)

        # ── Section : Intervalles (histogramme/X) ──
        bins_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        bins_f.pack(fill=tk.X, pady=(0, 8))
        tk.Label(bins_f, text="Intervalles (Axe X) :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.bins_var = tk.Entry(bins_f, width=6, justify="center")
        self.bins_var.insert(0, "15")
        self.bins_var.pack(side=tk.LEFT, padx=5)
        self.bins_var.bind("<Return>", self.update_plot)
        
        # ── Section : Intervalles (Y pour Heatmap) ──
        bins_y_f = tk.Frame(self.sidebar, bg="#ecf0f1")
        bins_y_f.pack(fill=tk.X, pady=(0, 8))
        tk.Label(bins_y_f, text="Intervalles (Axe Y) :", bg="#ecf0f1", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self.bins_y_var = tk.Entry(bins_y_f, width=6, justify="center")
        self.bins_y_var.insert(0, "15")
        self.bins_y_var.pack(side=tk.LEFT, padx=5)
        self.bins_y_var.bind("<Return>", self.update_plot)

        # ── Section : Catégories ──
        self.cat_frame = tk.LabelFrame(
            self.sidebar, text="Catégories", bg="#ecf0f1",
            font=("Segoe UI", 8, "bold")
        )
        self.cat_frame.pack(fill=tk.X, pady=(0, 8))
        self._build_category_checkboxes()

        # ── Section : Résumé Global ──
        self.summary_frame = tk.LabelFrame(
            self.sidebar, text="Résumé Global du Réseau", bg="#ecf0f1",
            font=("Segoe UI", 8, "bold")
        )
        self.summary_frame.pack(fill=tk.X, pady=(0, 8))
        self._build_global_summary()

        # ── Zone de graphe ──
        self.plot_frame = tk.Frame(main_content, bg="white")
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar_frame = tk.Frame(self.plot_frame, bg="white")
        self.toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas_plot, self.toolbar_frame)
        self.toolbar.update()

        # ── Barre de statut ──
        self.status_bar = tk.Frame(self, bg="#bdc3c7", height=20)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = tk.Label(self.status_bar, text="Prêt", bg="#bdc3c7", font=("Segoe UI", 8))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.grip = tk.Label(self.status_bar, text="◢", bg="#bdc3c7", fg="#7f8c8d", cursor="bottom_right_corner")
        self.grip.pack(side=tk.RIGHT, anchor="se", padx=2)

    def _setup_sidebar_scroll(self):
        """Configure le scroll de la sidebar avec la molette."""
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

    def _build_category_checkboxes(self):
        """Construit les checkboxes de catégories pour le domaine actuel."""
        for w in self.cat_frame.winfo_children():
            w.destroy()
        self.category_vars.clear()

        categories = NODE_CATEGORIES if self.domain_var.get() == "Sommets (Nœuds)" else EDGE_CATEGORIES

        for cat in categories:
            var = tk.BooleanVar(value=True)
            self.category_vars[cat] = var

            f = tk.Frame(self.cat_frame, bg="#ecf0f1")
            f.pack(fill=tk.X, padx=5, pady=1)

            color_lbl = tk.Label(f, text="■", fg=CATEGORY_COLORS.get(cat, "#333"), bg="#ecf0f1", font=("Segoe UI", 10))
            color_lbl.pack(side=tk.LEFT)

            cb = tk.Checkbutton(
                f, text=cat, variable=var, bg="#ecf0f1",
                font=("Segoe UI", 8), anchor="w", command=lambda: self.update_plot()
            )
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_global_summary(self):
        """Affiche le résumé global du réseau dans la sidebar."""
        s = self.global_summary

        lines = [
            f"Sommets total : {s['nb_nodes']}",
        ]
        for cat in NODE_CATEGORIES:
            count = s['node_counts'].get(cat, 0)
            if count > 0:
                lines.append(f"  • {cat} : {count}")

        lines.append(f"Arcs total : {s['nb_edges']}")
        for cat in EDGE_CATEGORIES:
            count = s['edge_counts'].get(cat, 0)
            if count > 0:
                lines.append(f"  • {cat} : {count}")

        lines.append("")
        if s['efficacite'] is not None:
            lines.append(f"Efficacité : {s['efficacite']:.2f} %")
        if s['demande_globale'] is not None:
            lines.append(f"Dem. Globale : {s['demande_globale']:.2f} L/min")
        lines.append(f"Débit total : {s['debit_total']:.2f} L/min")
        lines.append(f"Long. totale : {s['longueur_totale']:.1f} m")
        lines.append(f"Arcs actifs : {s['arcs_actifs']} ({s['ratio_arcs_actifs']:.1f}%)")
        
        if s.get('ratio_arcs_low_flow') is not None:
            lines.append(f"% Arcs < 1 L/min : {s['ratio_arcs_low_flow']:.1f} %")
            
        lines.append(f"Pression : [{s['pression_min']:.1f}, {s['pression_max']:.1f}] m")
        lines.append(f"  moy : {s['pression_moy']:.2f} m")

        for line in lines:
            tk.Label(
                self.summary_frame, text=line, bg="#ecf0f1",
                font=("Segoe UI", 7), anchor="w"
            ).pack(fill=tk.X, padx=5)

    # ─── Callbacks ───────────────────────────────────────────

    def _on_domain_change(self, event=None):
        """Appelé quand l'utilisateur change le domaine (Sommets/Arcs)."""
        is_nodes = self.domain_var.get() == "Sommets (Nœuds)"
        metrics_list = NODE_METRICS if is_nodes else EDGE_METRICS
        metric_labels = [m[0] for m in metrics_list]
        
        self.cb_metric['values'] = ["Catégorie"] + metric_labels
        self.cb_metric2['values'] = metric_labels
        self.cb_metric3['values'] = ["Catégorie"] + metric_labels
        
        self.metric_var.set("Catégorie")
        self.metric2_var.set(metric_labels[0])
        self.metric3_var.set("Catégorie")
        
        self._build_category_checkboxes()
        self.update_plot()

    def _get_active_data(self):
        """Retourne les items plats filtrés, catégories et métriques pour le domaine actuel."""
        is_nodes = self.domain_var.get() == "Sommets (Nœuds)"

        if is_nodes:
            all_items = self.flat_nodes
            stats = self.node_stats
            categories = NODE_CATEGORIES
            metrics_list = NODE_METRICS
        else:
            all_items = self.flat_edges
            stats = self.edge_stats
            categories = EDGE_CATEGORIES
            metrics_list = EDGE_METRICS

        # Filtrer par catégories cochées
        active_cats = [cat for cat in categories if self.category_vars.get(cat, tk.BooleanVar(value=False)).get()]
        filtered_items = [item for item in all_items if item.get('categorie') in active_cats]

        # Trouver la métrique X
        selected_label = self.metric_var.get()
        metric_info = ("Catégorie", "categorie", "")
        if selected_label != "Catégorie":
            for label, key, unit in metrics_list:
                if label == selected_label:
                    metric_info = (label, key, unit)
                    break

        # Trouver la métrique Y
        selected_label2 = self.metric2_var.get()
        metric2_info = metrics_list[0]
        for label, key, unit in metrics_list:
            if label == selected_label2:
                metric2_info = (label, key, unit)
                break

        # Trouver la métrique Z (Couleur)
        selected_label3 = self.metric3_var.get()
        metric3_info = ("Catégorie", "categorie", "")
        if selected_label3 != "Catégorie":
            for label, key, unit in metrics_list:
                if label == selected_label3:
                    metric3_info = (label, key, unit)
                    break

        return filtered_items, stats, active_cats, metrics_list, metric_info, metric2_info, metric3_info

    # ─── Fonctions de Binning ────────────────────────────────────

    def _parse_bins(self, bin_str):
        try:
            b_str = bin_str.strip()
            if ';' in b_str:
                intervals = []
                for part in b_str.split(';'):
                    part = part.strip()
                    if not part: continue
                    inc_min = part.startswith('[')
                    inc_max = part.endswith(']')
                    inner = part[1:-1].split(',')
                    min_v = float(inner[0].strip().replace('+inf', 'inf').replace('-inf', '-inf'))
                    max_v = float(inner[1].strip().replace('+inf', 'inf').replace('-inf', '-inf'))
                    intervals.append((min_v, max_v, inc_min, inc_max, part))
                return "intervals", intervals
            elif ',' in b_str:
                b_val = [float(x.strip()) for x in b_str.split(',') if x.strip()]
                if len(b_val) < 2: return "auto", 15
                return "edges", b_val
            else:
                return "auto", max(1, int(b_str))
        except Exception:
            return "auto", 15

    def _apply_intervals(self, data, mode, bins):
        if mode == "intervals":
            cats = [lbl for _, _, _, _, lbl in bins]
            new_data = []
            for val in data:
                if isinstance(val, str):
                    new_data.append(val)
                    continue
                found = False
                for min_v, max_v, inc_min, inc_max, label in bins:
                    if ((val >= min_v) if inc_min else (val > min_v)) and ((val <= max_v) if inc_max else (val < max_v)):
                        new_data.append(label)
                        found = True
                        break
                if not found:
                    new_data.append("Hors limites")
            if "Hors limites" in new_data:
                cats.append("Hors limites")
            return True, new_data, cats
        return False, data, None

    # ─── Mise à jour du graphe ───────────────────────────────

    def update_plot(self, event=None):
        """Redessine le graphe selon les paramètres actuels."""
        plot_type = self.plot_type_var.get()

        if plot_type == "Boîte à moustaches":
            self._draw_boxplot()
        elif plot_type == "Histogramme":
            self._draw_histogram()
        elif plot_type == "Radar Chart":
            self._draw_radar()
        elif plot_type == "Tableau récapitulatif":
            self._draw_table()
        elif plot_type == "Nuage de points":
            self._draw_scatter()
        elif plot_type == "Carte de chaleur":
            self._draw_heatmap()

        self.canvas_plot.draw()

    def _draw_boxplot(self):
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        filtered_items, stats, active_cats, metrics_list, (label_x, x_k, unit_x), (label_y, y_k, unit_y), _ = self._get_active_data()

        if not filtered_items or not y_k:
            ax.text(0.5, 0.5, 'Aucune donnée correspondante.', ha='center', va='center', color='red')
            self.fig.tight_layout()
            return

        x_mode, x_bins = self._parse_bins(self.bins_var.get())
        custom_mode = x_mode
        parsed_intervals = x_bins if x_mode == "intervals" else []
        bins_val = x_bins if x_mode != "intervals" else 15

        all_x_data = [r.get(x_k, 0.0) if x_k != "categorie" else r["categorie"] for r in filtered_items]
        
        subsets = []
        x_labels = []

        if len(filtered_items) > 0 and isinstance(all_x_data[0], str):
            unique_vals = sorted(list(set(all_x_data)))
            for val in unique_vals:
                x_labels.append(str(val))
                subsets.append([r for r in filtered_items if r.get(x_k, r.get("categorie")) == val])
        elif custom_mode == "intervals":
            for min_v, max_v, inc_min, inc_max, label in parsed_intervals:
                x_labels.append(label)
                subset = [r for r in filtered_items if ((r.get(x_k,0.0) >= min_v) if inc_min else (r.get(x_k,0.0) > min_v)) and ((r.get(x_k,0.0) <= max_v) if inc_max else (r.get(x_k,0.0) < max_v))]
                subsets.append(subset)
        else:
            if custom_mode == "auto":
                bin_edges = np.histogram_bin_edges(all_x_data, bins=bins_val)
            else:
                bin_edges = np.array(bins_val)
                
            for i in range(len(bin_edges) - 1):
                b_min = bin_edges[i]
                b_max = bin_edges[i+1]
                if i == len(bin_edges) - 2:
                    subset = [r for r in filtered_items if b_min <= r.get(x_k,0.0) <= b_max]
                    label = f"[{b_min:.2f}, {b_max:.2f}]"
                else:
                    subset = [r for r in filtered_items if b_min <= r.get(x_k,0.0) < b_max]
                    label = f"[{b_min:.2f}, {b_max:.2f}["
                x_labels.append(label)
                subsets.append(subset)

        boxplot_data = [[r.get(y_k, 0.0) for r in s] for s in subsets]
        x_pos = np.arange(1, len(x_labels) + 1)

        bp = ax.boxplot(boxplot_data, positions=x_pos, patch_artist=True, showmeans=True,
                        boxprops=dict(facecolor='#9b59b6', alpha=0.7),
                        capprops=dict(color='#2c3e50', linewidth=1.5),
                        whiskerprops=dict(color='#2c3e50', linewidth=1.5),
                        flierprops=dict(marker='o', markerfacecolor='#e74c3c', markersize=5, alpha=0.6, markeredgecolor='none'),
                        medianprops=dict(color='black', linewidth=2),
                        meanprops=dict(marker='^', markerfacecolor='white', markeredgecolor='black', markersize=7))

        if x_k == "categorie":
            # Colorer les boites selon la catégorie
            for i, cat in enumerate(x_labels):
                if cat in CATEGORY_COLORS:
                    bp['boxes'][i].set_facecolor(CATEGORY_COLORS[cat])
                    bp['boxes'][i].set_alpha(0.7)

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
                       f"n={len(data_i)}\n"
                       f"Q1: {y_q1:.2f} | Q3: {y_q3:.2f}\n"
                       f"Med: {y_median:.2f} | Moy: {y_mean:.2f}")
                new_x_labels.append(lbl)
            else:
                new_x_labels.append(x_labels[i])
            
        ax.set_xticks(x_pos)
        ax.set_xticklabels(new_x_labels, rotation=0, ha='center', fontsize=9)
        unit_str_y = f" ({unit_y})" if unit_y else ""
        ax.set_ylabel(f"{label_y}{unit_str_y}", fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        ax.set_title(f"Box Plot : {label_y} selon {label_x}", fontweight='bold', fontsize=11)

        import matplotlib.patches as mpatches
        import matplotlib.lines as mlines
        legend_elements = [
            mpatches.Patch(facecolor='#9b59b6', alpha=0.7, label='Boîte (Q1 - Q3)'),
            mlines.Line2D([0], [0], color='black', lw=2, label='Médiane'),
            mlines.Line2D([0], [0], marker='^', color='w', markerfacecolor='white', markeredgecolor='black', markersize=7, label='Moyenne'),
            mlines.Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c', markersize=6, label='Valeurs aberrantes')
        ]
        ax.legend(handles=legend_elements, loc='best', fontsize=8)

        self.fig.tight_layout()
        self.status_label.config(text=f"Boîte à moustaches prête — {len(boxplot_data)} groupes")

    def _draw_histogram(self):
        """Histogramme en barres comptant le nombre d'éléments selon X."""
        self.fig.clf()
        ax = self.fig.add_subplot(111)

        filtered_items, stats, active_cats, metrics_list, (label_x, x_k, unit_x), _, _ = self._get_active_data()

        if not filtered_items:
            ax.text(0.5, 0.5, 'Aucune donnée correspondante.', ha='center', va='center', color='red')
            self.fig.tight_layout()
            return

        x_mode, x_bins = self._parse_bins(self.bins_var.get())
        custom_mode = x_mode
        parsed_intervals = x_bins if x_mode == "intervals" else []
        bins_val = x_bins if x_mode != "intervals" else 15

        all_x_data = [r.get(x_k, 0.0) if x_k != "categorie" else r["categorie"] for r in filtered_items]
        
        subsets = []
        x_labels = []

        if len(filtered_items) > 0 and isinstance(all_x_data[0], str):
            unique_vals = sorted(list(set(all_x_data)))
            for val in unique_vals:
                x_labels.append(str(val))
                subsets.append([r for r in filtered_items if r.get(x_k, r.get("categorie")) == val])
        elif custom_mode == "intervals":
            for min_v, max_v, inc_min, inc_max, label in parsed_intervals:
                x_labels.append(label)
                subset = [r for r in filtered_items if ((r.get(x_k,0.0) >= min_v) if inc_min else (r.get(x_k,0.0) > min_v)) and ((r.get(x_k,0.0) <= max_v) if inc_max else (r.get(x_k,0.0) < max_v))]
                subsets.append(subset)
        else:
            if custom_mode == "auto":
                bin_edges = np.histogram_bin_edges(all_x_data, bins=bins_val)
            else:
                bin_edges = np.array(bins_val)
                
            for i in range(len(bin_edges) - 1):
                b_min = bin_edges[i]
                b_max = bin_edges[i+1]
                if i == len(bin_edges) - 2:
                    subset = [r for r in filtered_items if b_min <= r.get(x_k,0.0) <= b_max]
                    label = f"[{b_min:.2f}, {b_max:.2f}]"
                else:
                    subset = [r for r in filtered_items if b_min <= r.get(x_k,0.0) < b_max]
                    label = f"[{b_min:.2f}, {b_max:.2f}["
                x_labels.append(label)
                subsets.append(subset)

        total_items = len(filtered_items)
        agg_vals = [len(s) for s in subsets]
            
        x_pos = np.arange(len(x_labels))
        bars = ax.bar(x_pos, agg_vals, color='#3498db', edgecolor='black', alpha=0.8)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=9)
        
        for bar, val in zip(bars, agg_vals):
            if val > 0 and total_items > 0:
                pct = (val / total_items) * 100
                ax.text(bar.get_x() + bar.get_width()/2, val, f'{val}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=8, fontweight='bold')
            elif val == 0:
                ax.text(bar.get_x() + bar.get_width()/2, val, '0', ha='center', va='bottom', fontsize=8)
                
        ax.set_ylabel("Nombre d'éléments", fontweight='bold')
        if agg_vals and max(agg_vals) > 0:
            ax.set_ylim(0, max(agg_vals) * 1.15)
            
        ax.set_title(f"Histogramme : Nombre d'éléments selon {label_x}", fontweight='bold', fontsize=11)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        self.fig.tight_layout()
        self.status_label.config(text=f"Histogramme — {len(x_labels)} barres")

    def _draw_radar(self):
        """Radar chart comparant plusieurs métriques normalisées entre catégories."""
        self.fig.clf()

        filtered_items, stats, active_cats, metrics_list, _, _, _ = self._get_active_data()

        # Pour le radar, on utilise toutes les métriques
        metric_labels = [m[0] for m in metrics_list]
        metric_keys = [m[1] for m in metrics_list]
        N = len(metric_labels)

        if N < 3:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "Minimum 3 métriques requises pour un radar.",
                    ha='center', va='center', fontsize=12, color='red',
                    transform=ax.transAxes)
            self.fig.tight_layout()
            return

        # D'abord, trouver le max global par métrique pour normaliser
        global_max = {}
        for key in metric_keys:
            all_vals = [r.get(key, 0.0) for r in filtered_items]
            global_max[key] = max(abs(v) for v in all_vals) if all_vals else 1.0
            if global_max[key] == 0:
                global_max[key] = 1.0

        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]  # Boucle fermée

        ax = self.fig.add_subplot(111, polar=True)

        cat_data = []
        for cat in active_cats:
            means = []
            cat_items = [r for r in filtered_items if r.get("categorie") == cat]
            if not cat_items:
                continue
                
            for key in metric_keys:
                vals = [r.get(key, 0.0) for r in cat_items]
                if vals:
                    means.append(abs(np.mean(vals)) / global_max[key])
                else:
                    means.append(0.0)
            cat_data.append((cat, means))

        if not cat_data:
            ax.text(0.5, 0.5, "Aucune donnée.", ha='center', va='center',
                    fontsize=12, color='red', transform=ax.transAxes)
            self.fig.tight_layout()
            return

        for cat, means in cat_data:
            values = means + means[:1]
            ax.plot(angles, values, 'o-', linewidth=1.5,
                    color=CATEGORY_COLORS.get(cat, "#333"), label=cat, markersize=4)
            ax.fill(angles, values, alpha=0.1, color=CATEGORY_COLORS.get(cat, "#333"))

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metric_labels, fontsize=7)
        ax.set_title("Radar — Métriques normalisées", fontweight='bold', fontsize=11, pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=7)

        self.fig.tight_layout()
        self.status_label.config(text=f"Radar Chart — {len(cat_data)} catégorie(s)")

    def _draw_table(self):
        """Tableau récapitulatif des stats descriptives par catégorie et métrique."""
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.axis('off')

        filtered_items, stats, active_cats, metrics_list, _, (sel_label, sel_key, sel_unit), _ = self._get_active_data()

        # En-têtes
        col_labels = ["Catégorie", "N", "Min", "Max", "Moy", "Méd", "Q1", "Q3", "σ", "CV"]
        cell_data = []
        cell_colors = []

        for cat in active_cats:
            s = stats[cat].get(sel_key)
            color = CATEGORY_COLORS.get(cat, "#333")
            if s:
                row = [
                    cat,
                    f"{s['count']}",
                    f"{s['min']:.2f}",
                    f"{s['max']:.2f}",
                    f"{s['mean']:.2f}",
                    f"{s['median']:.2f}",
                    f"{s['Q1']:.2f}",
                    f"{s['Q3']:.2f}",
                    f"{s['std']:.2f}",
                    f"{s['cv']:.3f}",
                ]
            else:
                row = [cat] + ["—"] * 9

            cell_data.append(row)
            cell_colors.append([color + "30"] * len(col_labels))  # couleur transparente

        if not cell_data:
            ax.text(0.5, 0.5, "Aucune donnée pour cette sélection.",
                    ha='center', va='center', fontsize=12, color='red',
                    transform=ax.transAxes)
            self.fig.tight_layout()
            return

        table = ax.table(
            cellText=cell_data,
            colLabels=col_labels,
            cellColours=cell_colors,
            colColours=["#16a085" + "40"] * len(col_labels),
            loc='center',
            cellLoc='center',
        )

        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.0, 1.5)

        # Style des en-têtes
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(fontweight='bold', color='white')
                cell.set_facecolor('#16a085')
                cell.set_edgecolor('white')
            else:
                cell.set_edgecolor('#ddd')

        unit_str = f" ({sel_unit})" if sel_unit else ""
        ax.set_title(f"Statistiques descriptives : {sel_label}{unit_str}",
                     fontweight='bold', fontsize=11, pad=20)

        self.fig.tight_layout()
        self.status_label.config(text=f"Tableau — {sel_label} — {len(cell_data)} catégorie(s)")

    def _draw_scatter(self):
        """Nuage de points comparant deux métriques."""
        self.fig.clf()
        ax = self.fig.add_subplot(111)

        filtered_items, stats, active_cats, metrics_list, (label_x, x_k, unit_x), (label_y, y_k, unit_y), (label_z, z_k, unit_z) = self._get_active_data()

        if not filtered_items:
            ax.text(0.5, 0.5, "Aucune donnée correspondante.", ha='center', va='center', color='red')
            self.fig.tight_layout()
            return

        all_x = [r.get(x_k, 0.0) if x_k != "categorie" else r["categorie"] for r in filtered_items]
        all_y = [r.get(y_k, 0.0) if y_k != "categorie" else r["categorie"] for r in filtered_items]

        # S'il faut colorer par une 3ème métrique continue
        if z_k != "categorie":
            all_z = [r.get(z_k, 0.0) for r in filtered_items]
            sc = ax.scatter(all_x, all_y, c=all_z, cmap='viridis', alpha=0.8, edgecolors='none', s=40)
            cbar = self.fig.colorbar(sc, ax=ax)
            unit_str_z = f" ({unit_z})" if unit_z else ""
            cbar.set_label(f"{label_z}{unit_str_z}", fontsize=8)
        else:
            # Colorer par catégorie
            unique_cats = list(set([r["categorie"] for r in filtered_items]))
            for cat in unique_cats:
                cat_x = [all_x[i] for i, r in enumerate(filtered_items) if r["categorie"] == cat]
                cat_y = [all_y[i] for i, r in enumerate(filtered_items) if r["categorie"] == cat]
                ax.scatter(
                    cat_x, cat_y, 
                    c=CATEGORY_COLORS.get(cat, "#333"), 
                    alpha=0.6, edgecolors='none', s=40, 
                    label=f"{cat} (n={len(cat_x)})"
                )
            ax.legend(fontsize=7, loc='best')

        unit_str_x = f" ({unit_x})" if unit_x else ""
        unit_str_y = f" ({unit_y})" if unit_y else ""
        ax.set_xlabel(f"{label_x}{unit_str_x}", fontweight='bold', fontsize=9)
        ax.set_ylabel(f"{label_y}{unit_str_y}", fontweight='bold', fontsize=9)
        ax.set_title(f"Nuage de points : {label_x} vs {label_y}", fontweight='bold', fontsize=11)
        ax.grid(linestyle='--', alpha=0.5)

        self.fig.tight_layout()
        self.status_label.config(text=f"Nuage de points — {len(filtered_items)} éléments affichés")

    def _draw_heatmap(self):
        """Carte de chaleur 2D comparant deux métriques."""
        self.fig.clf()
        ax = self.fig.add_subplot(111)

        filtered_items, stats, active_cats, metrics_list, (label_x, x_k, unit_x), (label_y, y_k, unit_y), (label_z, z_k, unit_z) = self._get_active_data()

        if not filtered_items:
            ax.text(0.5, 0.5, "Aucune donnée correspondante.", ha='center', va='center', color='red')
            self.fig.tight_layout()
            return

        x_mode, x_bins = self._parse_bins(self.bins_var.get())
        y_mode, y_bins = self._parse_bins(self.bins_y_var.get())

        all_x_data = [r.get(x_k, 0.0) if x_k != "categorie" else r["categorie"] for r in filtered_items]
        all_y_data = [r.get(y_k, 0.0) if y_k != "categorie" else r["categorie"] for r in filtered_items]

        x_transformed, final_x_data, x_cat_ordered = self._apply_intervals(all_x_data, x_mode, x_bins)
        y_transformed, final_y_data, y_cat_ordered = self._apply_intervals(all_y_data, y_mode, y_bins)

        x_is_cat = len(final_x_data) > 0 and isinstance(final_x_data[0], str)
        y_is_cat = len(final_y_data) > 0 and isinstance(final_y_data[0], str)

        if x_is_cat:
            x_categories = x_cat_ordered if x_transformed else sorted(list(set(final_x_data)))
            x_cat_map = {v: i for i, v in enumerate(x_categories)}
        else:
            x_categories = None

        if y_is_cat:
            y_categories = y_cat_ordered if y_transformed else sorted(list(set(final_y_data)))
            y_cat_map = {v: i for i, v in enumerate(y_categories)}
        else:
            y_categories = None

        # Remplissage de la matrice H_count / H_sum
        if x_is_cat and y_is_cat:
            nb_x, nb_y = len(x_categories), len(y_categories)
            H_count = np.zeros((nb_x, nb_y))
            H_sum = np.zeros((nb_x, nb_y))
            for idx, r in enumerate(filtered_items):
                xi, yi = x_cat_map[final_x_data[idx]], y_cat_map[final_y_data[idx]]
                H_count[xi, yi] += 1
                if z_k != "categorie": H_sum[xi, yi] += r.get(z_k, 0.0)
            
            if z_k != "categorie":
                Z = np.true_divide(H_sum, H_count)
            else:
                total_count = np.sum(H_count)
                Z = (H_count / total_count * 100.0) if total_count > 0 else H_count.copy()
            Z[H_count == 0] = np.nan

            im = ax.imshow(Z.T, origin='lower', aspect='auto', cmap='viridis')
            ax.set_xticks(np.arange(nb_x))
            ax.set_yticks(np.arange(nb_y))
            ax.set_xticklabels(x_categories, rotation=45, ha='right', fontsize=8)
            ax.set_yticklabels(y_categories, fontsize=8)
            
        elif x_is_cat:
            nb_x = len(x_categories)
            yb = y_bins if y_mode == "edges" or isinstance(y_bins, int) else 15
            y_edges = np.histogram_bin_edges(final_y_data, bins=yb)
            nb_y = len(y_edges) - 1
            H_count = np.zeros((nb_x, nb_y))
            H_sum = np.zeros((nb_x, nb_y))
            y_indices = np.clip(np.digitize(final_y_data, y_edges) - 1, 0, nb_y - 1)
            for idx, r in enumerate(filtered_items):
                xi, yi = x_cat_map[final_x_data[idx]], y_indices[idx]
                H_count[xi, yi] += 1
                if z_k != "categorie": H_sum[xi, yi] += r.get(z_k, 0.0)
                
            if z_k != "categorie":
                Z = np.true_divide(H_sum, H_count)
            else:
                total_count = np.sum(H_count)
                Z = (H_count / total_count * 100.0) if total_count > 0 else H_count.copy()
            Z[H_count == 0] = np.nan

            im = ax.imshow(Z.T, origin='lower', aspect='auto', cmap='viridis', extent=[-0.5, nb_x - 0.5, y_edges[0], y_edges[-1]])
            ax.set_xticks(np.arange(nb_x))
            ax.set_xticklabels(x_categories, rotation=45, ha='right', fontsize=8)
            
        elif y_is_cat:
            nb_y = len(y_categories)
            xb = x_bins if x_mode == "edges" or isinstance(x_bins, int) else 15
            x_edges = np.histogram_bin_edges(final_x_data, bins=xb)
            nb_x = len(x_edges) - 1
            H_count = np.zeros((nb_x, nb_y))
            H_sum = np.zeros((nb_x, nb_y))
            x_indices = np.clip(np.digitize(final_x_data, x_edges) - 1, 0, nb_x - 1)
            for idx, r in enumerate(filtered_items):
                xi, yi = x_indices[idx], y_cat_map[final_y_data[idx]]
                H_count[xi, yi] += 1
                if z_k != "categorie": H_sum[xi, yi] += r.get(z_k, 0.0)
                
            if z_k != "categorie":
                Z = np.true_divide(H_sum, H_count)
            else:
                total_count = np.sum(H_count)
                Z = (H_count / total_count * 100.0) if total_count > 0 else H_count.copy()
            Z[H_count == 0] = np.nan

            im = ax.imshow(Z.T, origin='lower', aspect='auto', cmap='viridis', extent=[x_edges[0], x_edges[-1], -0.5, nb_y - 0.5])
            ax.set_yticks(np.arange(nb_y))
            ax.set_yticklabels(y_categories, fontsize=8)
            
        else:
            xb = x_bins if x_mode == "edges" or isinstance(x_bins, int) else 15
            yb = y_bins if y_mode == "edges" or isinstance(y_bins, int) else 15
            x_edges = np.histogram_bin_edges(final_x_data, bins=xb)
            y_edges = np.histogram_bin_edges(final_y_data, bins=yb)
            
            if z_k != "categorie":
                all_z_data = [r.get(z_k, 0.0) for r in filtered_items]
                import scipy.stats
                statistic, _, _, _ = scipy.stats.binned_statistic_2d(final_x_data, final_y_data, all_z_data, statistic='mean', bins=[x_edges, y_edges])
                Z = np.ma.masked_invalid(statistic)
            else:
                H_count, _, _ = np.histogram2d(final_x_data, final_y_data, bins=[x_edges, y_edges])
                total_count = np.sum(H_count)
                Z_pct = (H_count / total_count * 100.0) if total_count > 0 else H_count.copy()
                Z = np.ma.masked_where(H_count == 0, Z_pct)

            im = ax.imshow(Z.T, origin='lower', aspect='auto', cmap='viridis', extent=[x_edges[0], x_edges[-1], y_edges[0], y_edges[-1]])

        cbar = self.fig.colorbar(im, ax=ax)
        if z_k != "categorie":
            unit_str_z = f" ({unit_z})" if unit_z else ""
            cbar.set_label(f"Moyenne de {label_z}{unit_str_z}", fontsize=8)
        else:
            cbar.set_label("Pourcentage (%)", fontsize=8)

        unit_str_x = f" ({unit_x})" if unit_x else ""
        unit_str_y = f" ({unit_y})" if unit_y else ""
        ax.set_xlabel(f"{label_x}{unit_str_x}", fontweight='bold', fontsize=9)
        ax.set_ylabel(f"{label_y}{unit_str_y}", fontweight='bold', fontsize=9)
        ax.set_title(f"Carte de chaleur : {label_x} vs {label_y}", fontweight='bold', fontsize=11)
        ax.grid(False)

        self.fig.tight_layout()
        self.status_label.config(text=f"Carte de chaleur — {label_x} vs {label_y}")

    # ─── Gestion de la fenêtre ───────────────────────────────

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
        color = self.TITLE_COLOR_ACTIVE if is_active else self.TITLE_COLOR
        self.title_bar.config(bg=color)
        self.title_label.config(bg=color)

    def close_window(self):
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
        self.place(
            width=max(600, self.start_w + event.x_root - self.start_x),
            height=max(400, self.start_h + event.y_root - self.start_y)
        )

    def refresh_data(self, nodes, edges, metrics):
        """Met à jour les données et redessine (appelé après une re-simulation)."""
        self.nodes = nodes
        self.edges = edges
        self.metrics = metrics

        self.node_profiles = extract_node_profiles(nodes)
        self.edge_profiles = extract_edge_profiles(edges)
        self.node_stats = compute_category_stats(self.node_profiles, NODE_METRICS)
        self.edge_stats = compute_category_stats(self.edge_profiles, EDGE_METRICS)
        self.global_summary = compute_global_summary(
            nodes, edges,
            efficacite=metrics.get("efficacite"),
            demande_globale=metrics.get("demande_globale"),
        )

        # Reconstruire le résumé
        for w in self.summary_frame.winfo_children():
            w.destroy()
        self._build_global_summary()

        self.update_plot()
