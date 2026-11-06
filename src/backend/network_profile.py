"""
Profil Statistique Intra-Réseau — Module Backend

Extraction et calcul des métriques par catégorie d'éléments 
à partir d'un graphe de réseau unique déjà simulé.
"""

import numpy as np
from src.wrapper_tools import ffi_wrapper

# ─── Constantes ─────────────────────────────────────────────

# Catégories de sommets
NODE_CATEGORIES = [
    "Réservoirs",
    "Tanks (Cuves)",
    "Jonctions (avec demande)",
    "Jonctions (sans demande)",
]

# Catégories d'arcs
EDGE_CATEGORIES = [
    "Tuyaux",
    "Pompes",
    "Vannes",
]

# Métriques disponibles pour les sommets
NODE_METRICS = [
    ("Élévation", "elevation", "m"),
    ("Pression", "pression", "m"),
    ("Demande", "demande", "L/min"),
    ("Satisfaction", "satisfaction", "%"),
    ("Degré", "degree", ""),
    ("Charge", "charge", "m"),
]

# Métriques disponibles pour les arcs
EDGE_METRICS = [
    ("Débit (Flow)", "flow", "L/min"),
    ("Vitesse", "velocity", "m/s"),
    ("Diamètre", "diametre", "mm"),
    ("Longueur", "longueur", "m"),
    ("Rugosité", "roughness", ""),
    ("Capacité", "capacite", "L/min"),
    ("Diff. d'Élévation", "diff_elevation", "m"),
    ("Diff. de Pression", "diff_pression", "m"),
    ("Ratio Débit/Capacité", "flow_cap_ratio", "%"),
]


# ─── Fonctions utilitaires ──────────────────────────────────

def compute_descriptive_stats(values):
    """Calcule les statistiques descriptives pour un tableau de valeurs.
    
    Retourne un dict avec min, max, mean, median, Q1, Q3, std, cv, count.
    Retourne None si le tableau est vide.
    """
    if not values or len(values) == 0:
        return None

    arr = np.array(values, dtype=float)
    mean_val = np.mean(arr)
    std_val = np.std(arr)

    return {
        "count": len(arr),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(mean_val),
        "median": float(np.median(arr)),
        "Q1": float(np.percentile(arr, 25)),
        "Q3": float(np.percentile(arr, 75)),
        "std": float(std_val),
        "cv": float(std_val / mean_val) if mean_val != 0 else 0.0,
    }


def _classify_node(node):
    """Retourne le nom de catégorie d'un nœud."""
    type_name = ffi_wrapper.get_nom_type_sommet(node['type'])
    if type_name == "RESERVOIR":
        return "Réservoirs"
    elif type_name == "TANK":
        return "Tanks (Cuves)"
    elif type_name == "JONCTION":
        if node['demande'] > 0:
            return "Jonctions (avec demande)"
        else:
            return "Jonctions (sans demande)"
    return None


def _classify_edge(edge):
    """Retourne le nom de catégorie d'un arc."""
    type_name = ffi_wrapper.get_nom_type_arc(edge['type'])
    if type_name == "TUYAU":
        return "Tuyaux"
    elif type_name == "POMPE":
        return "Pompes"
    elif type_name.startswith("VALVE") or type_name.startswith("PRV") or type_name.startswith("PSV") or type_name.startswith("PBV") or type_name.startswith("FCV") or type_name.startswith("TCV") or type_name.startswith("GPV") or type_name.startswith("PCV"):
        return "Vannes"
    # Fallback pour tout type VALVE_*
    if "VALVE" in type_name or "RESERVOIR" in type_name:
        return "Vannes" if "VALVE" in type_name else "Tuyaux"
    return "Tuyaux"


# ─── Extraction principale ──────────────────────────────────

def extract_node_profiles(nodes):
    """Extrait les métriques par catégorie de nœuds.
    
    Args:
        nodes: Liste de dicts de nœuds (provenant de extract_data).
        
    Returns:
        Dict {catégorie: {metric_key: [valeurs]}}
    """
    profiles = {cat: {m[1]: [] for m in NODE_METRICS} for cat in NODE_CATEGORIES}

    for node in nodes:
        cat = _classify_node(node)
        if cat is None:
            continue
        for _, key, _ in NODE_METRICS:
            if key == "charge":
                # La charge = élévation + pression
                val = node.get('elevation', 0.0) + node.get('pression', 0.0)
            else:
                val = node.get(key, 0.0)
            profiles[cat][key].append(val)

    return profiles


def extract_edge_profiles(edges):
    """Extrait les métriques par catégorie d'arcs.
    
    Args:
        edges: Liste de dicts d'arcs (provenant de extract_data).
        
    Returns:
        Dict {catégorie: {metric_key: [valeurs]}}
    """
    profiles = {cat: {m[1]: [] for m in EDGE_METRICS} for cat in EDGE_CATEGORIES}

    for edge in edges:
        cat = _classify_edge(edge)
        if cat not in profiles:
            continue
        for _, key, _ in EDGE_METRICS:
            if key == "flow_cap_ratio":
                # Ratio débit / capacité en pourcentage
                cap = max(edge.get('cap_aller', 0.0), edge.get('cap_retour', 0.0))
                flow = edge.get('flow', 0.0)
                val = (flow / cap * 100.0) if cap > 0 else 0.0
            elif key == "capacite":
                val = max(edge.get('cap_aller', 0.0), edge.get('cap_retour', 0.0))
            else:
                val = edge.get(key, 0.0)
            profiles[cat][key].append(val)

    return profiles


def compute_category_stats(profiles, metrics_list):
    """Calcule les stats descriptives pour chaque catégorie et métrique.
    
    Args:
        profiles: Dict {catégorie: {metric_key: [valeurs]}}
        metrics_list: Liste de tuples (label, key, unit) décrivant les métriques.
        
    Returns:
        Dict {catégorie: {metric_key: stats_dict ou None}}
    """
    stats = {}
    for cat, cat_data in profiles.items():
        stats[cat] = {}
        for _, key, _ in metrics_list:
            stats[cat][key] = compute_descriptive_stats(cat_data.get(key, []))
    return stats


def get_network_summary(nodes, edges, metrics=None):
    """Calcule le résumé global, les stats par catégorie, et retourne le tout.
    
    Args:
        nodes: Liste des dicts de nœuds.
        edges: Liste des dicts d'arcs.
        metrics: (Optionnel) dict retourné par extract_dashboard_metrics contenant efficacite, demande_globale, etc.
        
    Returns:
        Dict contenant 'global', 'node_stats', 'edge_stats'.
    """
    efficacite = metrics.get('efficacite') if metrics else None
    demande_globale = metrics.get('demande_globale') if metrics else None
    ratio_arcs_low_flow = metrics.get('ratio_arcs_low_flow') if metrics else None

    global_summary = compute_global_summary(nodes, edges, efficacite, demande_globale, ratio_arcs_low_flow)
    
    node_profiles = extract_node_profiles(nodes)
    node_stats = compute_category_stats(node_profiles, NODE_METRICS)
    
    edge_profiles = extract_edge_profiles(edges)
    edge_stats = compute_category_stats(edge_profiles, EDGE_METRICS)

    return {
        "global": global_summary,
        "node_stats": node_stats,
        "edge_stats": edge_stats
    }


def compute_global_summary(nodes, edges, efficacite=None, demande_globale=None, ratio_arcs_low_flow=None):
    """Calcule les métriques globales résumant l'ensemble du réseau.
    
    Args:
        nodes: Liste de dicts de nœuds.
        edges: Liste de dicts d'arcs.
        efficacite: Satisfaisabilité en % (optionnel, pré-calculé).
        demande_globale: Demande globale en L/min (optionnel, pré-calculé).
        ratio_arcs_low_flow: Pourcentage d'arcs avec flow < 1 L/min.
        
    Returns:
        Dict de métriques résumées.
    """
    # Comptages par type de nœud
    node_counts = {cat: 0 for cat in NODE_CATEGORIES}
    for n in nodes:
        cat = _classify_node(n)
        if cat:
            node_counts[cat] += 1

    # Comptages par type d'arc
    edge_counts = {cat: 0 for cat in EDGE_CATEGORIES}
    for e in edges:
        cat = _classify_edge(e)
        if cat in edge_counts:
            edge_counts[cat] += 1

    # Métriques globales
    all_pressures = [n.get('pression', 0.0) for n in nodes]
    all_flows = [e.get('flow', 0.0) for e in edges]
    all_lengths = [e.get('longueur', 0.0) for e in edges]
    all_demands = [n.get('demande', 0.0) for n in nodes if n.get('demande', 0.0) > 0]

    arcs_actifs = sum(1 for f in all_flows if f > 0)
    arcs_nuls = sum(1 for f in all_flows if f == 0)

    summary = {
        "nb_nodes": len(nodes),
        "nb_edges": len(edges),
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "efficacite": efficacite,
        "demande_globale": demande_globale,
        "debit_total": sum(all_flows),
        "longueur_totale": sum(all_lengths),
        "arcs_actifs": arcs_actifs,
        "arcs_nuls": arcs_nuls,
        "ratio_arcs_actifs": (arcs_actifs / len(edges) * 100) if edges else 0.0,
        "ratio_arcs_low_flow": ratio_arcs_low_flow
    }

    # Stats globales de pression
    if all_pressures:
        summary["pression_min"] = min(all_pressures)
        summary["pression_max"] = max(all_pressures)
        summary["pression_moy"] = float(np.mean(all_pressures))
    else:
        summary["pression_min"] = summary["pression_max"] = summary["pression_moy"] = 0.0

    # Stats globales de demande (uniquement nœuds avec demande)
    if all_demands:
        summary["demande_min"] = min(all_demands)
        summary["demande_max"] = max(all_demands)
        summary["demande_moy"] = float(np.mean(all_demands))
    else:
        summary["demande_min"] = summary["demande_max"] = summary["demande_moy"] = 0.0

    return summary

def get_flat_profiles(nodes, edges):
    """Extrait une liste plate des nœuds et des arcs avec toutes leurs métriques.
    
    Returns:
        flat_nodes: Liste de dicts pour les nœuds (incluant la clé 'categorie').
        flat_edges: Liste de dicts pour les arcs (incluant la clé 'categorie').
    """
    flat_nodes = []
    for node in nodes:
        cat = _classify_node(node)
        if cat is None: continue
        item = {"categorie": cat}
        for _, key, _ in NODE_METRICS:
            if key == "charge":
                item[key] = node.get('elevation', 0.0) + node.get('pression', 0.0)
            else:
                item[key] = node.get(key, 0.0)
        flat_nodes.append(item)
        
    flat_edges = []
    for edge in edges:
        cat = _classify_edge(edge)
        if cat is None: continue
        item = {"categorie": cat}
        for _, key, _ in EDGE_METRICS:
            if key == "flow_cap_ratio":
                cap = max(edge.get('cap_aller', 0.0), edge.get('cap_retour', 0.0))
                flow = edge.get('flow', 0.0)
                item[key] = (flow / cap * 100.0) if cap > 0 else 0.0
            elif key == "capacite":
                item[key] = max(edge.get('cap_aller', 0.0), edge.get('cap_retour', 0.0))
            else:
                item[key] = edge.get(key, 0.0)
        flat_edges.append(item)
        
    return flat_nodes, flat_edges
