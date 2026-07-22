import numpy as np
import json
from src.wrapper_tools import analyse_tools

# --- CONSTANTES PARTAGÉES ---
ALGORITHMES = ("EPANET", "Ford-Fulkerson", "Edmonds-Karp")
ORIENTATIONS = ("Aucune", "EPANET", "EPANET Partiel", "Ford-Fulkerson", "Edmonds-Karp")
CAPACITES = ("Vitesse Max", "EPANET", "EPANET Partiel", "Ford-Fulkerson", "Edmonds-Karp")
DEMANDES = ("Inchanger", "Uniforme", "EPANET", "Normale", "Exponentielle", "Toutes à 1")
COULEURS_SOMMET = ("Aucune", "Élévation", "Pression", "Demande", "Satisfaction")
COULEURS_ARC = ("Aucune", "Flow (Débit)", "Vitesse", "Roughness (Rugosité)")

FILETYPES_INP = [("EPANET", "*.inp *.INP")]
FILETYPES_JSON = [("JSON Files", "*.json")]

class NpEncoder(json.JSONEncoder):
    """Encodeur JSON pour gérer les types NumPy extraits."""
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NpEncoder, self).default(obj)

def extract_data(reseau):
    """Extrait les données géométriques et physiques du réseau (Utilisé par la Visualisation)."""
    nodes = []
    edges = []
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

    nb_sommets = analyse_tools.get_n_sommet(reseau)
    for i in range(nb_sommets):
        s_type = analyse_tools.get_sommet_type(reseau, i)
        x, y = analyse_tools.get_sommet_position(reseau, i)
        nodes.append({
            'x': x, 'y': y, 'type': s_type, 'id': i + 1,
            'elevation': analyse_tools.get_sommet_elevation(reseau, i),
            'demande': analyse_tools.get_sommet_demande(reseau, i),
            'pression': analyse_tools.get_sommet_pression(reseau, i),
            'degree': analyse_tools.get_sommet_degree(reseau, i),
            'satisfaction': analyse_tools.get_sommet_satisfaction(reseau, i) * 100
        })

        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)

    arcs_actifs = analyse_tools.extraire_arcs_orientes_dominants(reseau)
    nb_arcs = analyse_tools.get_n_arcs(reseau)
    for k in range(nb_arcs // 2):
        idx_aller, idx_retour = 2 * k, 2 * k + 1
        
        src_type = analyse_tools.get_arc_source_type(reseau, idx_aller)
        dst_type = analyse_tools.get_arc_dest_type(reseau, idx_aller)

        x1, y1 = analyse_tools.get_arc_source_position(reseau, idx_aller)
        x2, y2 = analyse_tools.get_arc_dest_position(reseau, idx_aller)

        if idx_retour in arcs_actifs:
            x1, y1, x2, y2 = x2, y2, x1, y1

        edges.append({
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 
            'flow': analyse_tools.get_arc_non_oriente_flow(reseau, idx_aller, idx_retour),
            'velocity': analyse_tools.get_arc_non_oriente_velocity(reseau, idx_aller, idx_retour),
            'type': analyse_tools.get_arc_type(reseau, idx_aller),
            'diametre': analyse_tools.get_arc_diametre(reseau, idx_aller),
            'longueur': analyse_tools.get_arc_longueur(reseau, idx_aller),
            'roughness': analyse_tools.get_arc_roughness(reseau, idx_aller),
            'flow_aller': analyse_tools.get_arc_flow(reseau, idx_aller), 
            'cap_aller': analyse_tools.get_arc_capacite(reseau, idx_aller),
            'flow_retour': analyse_tools.get_arc_flow(reseau, idx_retour), 
            'cap_retour': analyse_tools.get_arc_capacite(reseau, idx_retour)
        })
        
    return nodes, edges, (min_x, max_x, min_y, max_y)

def extract_dashboard_metrics(reseau):
    """Extrait les métriques globales d'un réseau unique (Utilisé par la Visualisation)."""
    return {
        "efficacite": analyse_tools.get_efficacite(reseau) * 100,
        "pression_requise": analyse_tools.get_pression_requise(reseau),
        "exposant_pression": analyse_tools.get_exposant_pression(reseau),
        "demande_globale": analyse_tools.get_demande_global(reseau)
    }

def compute_metrics(graph_ref, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt, 
                    r_src, r_epa, r_dst, r_v, r_p, r_ecart,
                    t_src, t_epa, t_dst, t_v, t_p, t_ecart):
    """Calcule les métriques comparatives entre le graphe de référence et le graphe cible."""
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
        "target_uid": tgt['uid'], "target_name": tgt['name'], 
        "target_algo": tgt['algo'], "target_ori": tgt['ori'], 
        "target_capa": tgt['capa'], "target_dem": tgt['dem'],
        "flags": flags,
        "ref_m_src": r_src, "ref_m_epa": r_epa, "ref_m_dst": r_dst, "ref_vitesse": r_v, "ref_portion": r_p, "ref_ecart_type": r_ecart,
        "tgt_m_src": t_src, "tgt_m_epa": t_epa, "tgt_m_dst": t_dst, "tgt_vitesse": t_v, "tgt_portion": t_p, "tgt_ecart_type": t_ecart,
        "wape": wape, "wp": wp, "sat_ref": sat_ref, "sat_tgt": sat_tgt,
        "jaccard": jaccard_d,  
        "arc_nul_ref": arcs_nul_ref.shape[0] / max(1, analyse_tools.get_n_arcs_no(graph_ref)) * 100,
        "arc_non_nul_ref" : arcs_non_nul_ref, 
        "arc_nul_cible": arcs_nul_tgt.shape[0] / max(1, analyse_tools.get_n_arcs_no(graph_tgt)) * 100,
        "arc_non_nul_cible": arcs_non_nul_tgt,
        "ratio_nul_tgt_ref": ((nb_inter_nul / nb_dom_ref) * 100) if nb_dom_ref > 0 else 1.0,
        "ratio_inter_ref": ((nb_inter_dom / nb_dom_ref) * 100) if nb_dom_ref > 0 else 1.0
    }