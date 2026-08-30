import os
import random
from src.wrapper_tools import ffi_wrapper

from src.backend.extract_data import (
    extract_data, extract_dashboard_metrics, compute_metrics, DEMANDES
)

def compute_algo(reseau, choix, m_src, m_dst):
    if choix == "Ford-Fulkerson":
        ffi_wrapper.ajout_source_destination(reseau)
        ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
        ffi_wrapper.ajout_capacite_source(reseau, m_src)
        ffi_wrapper.nullifier_flow(reseau)
        ffi_wrapper.compute_flow_ford_fukerson(reseau)
        ffi_wrapper.delete_source_destination(reseau)
    elif choix == "Edmonds-Karp":
        ffi_wrapper.ajout_source_destination(reseau)
        ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
        ffi_wrapper.ajout_capacite_source(reseau, m_src)
        ffi_wrapper.nullifier_flow(reseau)
        ffi_wrapper.compute_flow_edmonds_karp(reseau)
        ffi_wrapper.delete_source_destination(reseau)
    elif choix == "Ford-Fulkerson_elevation":
        ffi_wrapper.ajout_source_destination(reseau)
        ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
        ffi_wrapper.ajout_capacite_source(reseau, m_src)
        ffi_wrapper.nullifier_flow(reseau)
        ffi_wrapper.compute_flow_elevation_prioritaire_ff(reseau)
        ffi_wrapper.delete_source_destination(reseau)
    elif choix == "Edmonds-Karp_elevation":
        ffi_wrapper.ajout_source_destination(reseau)
        ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
        ffi_wrapper.ajout_capacite_source(reseau, m_src)
        ffi_wrapper.nullifier_flow(reseau)
        ffi_wrapper.compute_flow_edmonds_karp_elevation(reseau)
        ffi_wrapper.delete_source_destination(reseau)
    elif choix == "Ford-Fulkerson_annulation":
        ffi_wrapper.ajout_source_destination(reseau)
        ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
        ffi_wrapper.ajout_capacite_source(reseau, m_src)
        ffi_wrapper.nullifier_flow(reseau)
        ffi_wrapper.compute_flow_ford_fukerson(reseau)
        ffi_wrapper.annuler_circuits_flot(reseau)
        ffi_wrapper.delete_source_destination(reseau)
    elif choix == "Ford-Fulkerson_elevation_annulation":
        ffi_wrapper.ajout_source_destination(reseau)
        ffi_wrapper.ajout_capacite_demande(reseau, m_dst)
        ffi_wrapper.ajout_capacite_source(reseau, m_src)
        ffi_wrapper.nullifier_flow(reseau)
        ffi_wrapper.compute_flow_elevation_prioritaire_ff(reseau)
        ffi_wrapper.annuler_circuits_flot(reseau)
        ffi_wrapper.delete_source_destination(reseau)
    elif choix == "Test Orientation":
        ffi_wrapper.tester_orientation_flow(reseau)

def compute_orientation(projet, reseau, choix_ori, p_src, p_dem, portion=1.0):
    if choix_ori == "EPANET":
        ffi_wrapper.reget_epanet_flow(projet, reseau)
        ffi_wrapper.fix_capacite_flow_oriente(reseau)
    elif choix_ori == "EPANET Partiel":
        ffi_wrapper.reget_epanet_flow(projet, reseau)
        ffi_wrapper.fix_capacite_flow_oriente_portion(reseau, portion)
    elif choix_ori == "Pression Statique":
        ffi_wrapper.compute_pression_statique(reseau, 0)
        ffi_wrapper.orienter_arcs_par_pression(reseau)
    elif choix_ori == "Orientation Laplace":
        ffi_wrapper.orienter_st_harmonique(reseau)
    elif choix_ori == "Orientation s-t elevation":
        ffi_wrapper.orienter_elevation_dfs(reseau)
    elif choix_ori == "Orientation Elevation Descendante":
        ffi_wrapper.orienter_elevation_descendante(reseau)
    elif choix_ori == "Orientation s-t aleatoire":
        ffi_wrapper.orienter_aleatoire_dfs(reseau)
    elif choix_ori == "Orientation DAG aleatoire":
        ffi_wrapper.orienter_dag_aleatoire(reseau)
    elif choix_ori == "Orientation completement aleatoire":
        ffi_wrapper.orienter_completement_aleatoire(reseau)

def compute_network(projet, choix_algo, choix_ori, choix_capa, choix_dem, p_src, p_dem, v_res, v_arc, mult_epa=1.0, portion=1.0, ecart_type=0.3):
    ffi_wrapper.modif_multiplicateur(projet, max(mult_epa, 1e-6))
    reseau = None

    demandes_epanet = [d for d in DEMANDES if d == "EPANET"]
    
    if choix_dem == "Normale":
        ffi_wrapper.randomise_demande_normale(projet, ecart_type)
    elif choix_dem == "Exponentielle":
        ffi_wrapper.randomise_demande_exponentielle(projet, ecart_type)
    elif choix_dem == "Toutes à 1":
        ffi_wrapper.set_demande_un(projet)

    if choix_algo == "EPANET":
        ffi_wrapper.compute_epanet(projet)
        reseau = ffi_wrapper.import_epanet_graph(projet)
    else:                        
        besoin_epanet = (choix_dem in demandes_epanet) or (choix_capa in ["EPANET", "EPANET Partiel"]) or (choix_ori in ["EPANET", "EPANET Partiel"])
        if besoin_epanet:
            ffi_wrapper.compute_epanet(projet)
            
        reseau = ffi_wrapper.import_epanet_graph(projet)

        if choix_dem in demandes_epanet:
            ffi_wrapper.get_epanet_demande(projet, reseau)

        if choix_capa == "EPANET":
            ffi_wrapper.reget_epanet_flow(projet, reseau)
            ffi_wrapper.fix_capacite_flow_calcule(reseau)
        elif choix_capa == "EPANET Partiel":
            ffi_wrapper.reget_epanet_flow(projet, reseau)
            ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
            ffi_wrapper.fix_capacite_flow_calcule_portion(reseau, portion)
        elif choix_capa == "Vitesse Max":
            ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
        else:
            ffi_wrapper.fix_capacite_flow(reseau, v_res, v_arc)
            compute_algo(reseau, choix_capa, p_src, p_dem)
            ffi_wrapper.fix_capacite_flow_calcule(reseau)
            ffi_wrapper.nullifier_flow(reseau)

        compute_orientation(projet, reseau, choix_ori, p_src, p_dem, portion)
        compute_algo(reseau, choix_algo, p_src, p_dem)
        
        if choix_dem in demandes_epanet:
            ffi_wrapper.get_epanet_fulldemande(projet, reseau)

    ffi_wrapper.modif_multiplicateur(projet, 1.0 / max(mult_epa, 1e-6))
    return reseau

def run_single_simulation(filepath, choix_algo, choix_ori, choix_capa, choix_dem, 
                          p_src, p_dem, v_res, v_arc, mult_epa=1.0, portion=1.0, 
                          seed=None, ecart_type=0.3):
    projet = ffi_wrapper.create_epanet_project(filepath)

    if seed is not None:
        ffi_wrapper.set_random_seed(seed)
    
    if choix_dem == "Uniforme":
        ffi_wrapper.randomise_demande(projet)
    elif choix_dem == "Normale":
        ffi_wrapper.randomise_demande_normale(projet, ecart_type)
    elif choix_dem == "Exponentielle":
        ffi_wrapper.randomise_demande_exponentielle(projet, ecart_type)
    elif choix_dem == "Toutes à 1":
        ffi_wrapper.set_demande_un(projet)

    reseau = compute_network(projet, choix_algo, choix_ori, choix_capa, choix_dem, 
                             p_src, p_dem, v_res, v_arc, mult_epa, portion, ecart_type)
                             
    nodes, edges, bounds = extract_data(reseau)
    metrics = extract_dashboard_metrics(reseau)

    ffi_wrapper.free_graph(reseau)
    ffi_wrapper.free_project(projet)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "bounds": bounds,
        "metrics": metrics
    }

def run_analysis_worker(task_args):
    filepath, filename, flags, rand_type, seed_val, rand_ecart, params = task_args
    results = []
    projet = None
    
    try:
        projet = ffi_wrapper.create_epanet_project(filepath)

        ffi_wrapper.set_random_seed(seed_val)
        
        if rand_type == "Uniforme":
            ffi_wrapper.randomise_demande(projet)
        elif rand_type == "Normale":
            ffi_wrapper.randomise_demande_normale(projet, rand_ecart)
        elif rand_type == "Exponentielle":
            ffi_wrapper.randomise_demande_exponentielle(projet, rand_ecart)
        elif rand_type == "Toutes à 1":
            ffi_wrapper.set_demande_un(projet)

        ref_grid = params['ref_grid']
        
        for r_ecart in ref_grid["ecart_type"]:
            for r_epa in ref_grid["m_epa"]:
                ffi_wrapper.modif_multiplicateur(projet, max(r_epa, 1e-6))
                
                for r_dst in ref_grid["m_dst"]:
                    for r_src in ref_grid["m_src"]:
                        for r_v in ref_grid["vitesse"]:
                            for r_p in ref_grid["portion"]:

                                if params['ref_algo'] == "EPANET":
                                    graph_ref = compute_network(projet, params['ref_algo'], params['ref_ori'], params['ref_capa'], params['ref_dem'], 1.0, 1.0, r_v, r_v, 1.0, r_p, r_ecart)
                                else:
                                    graph_ref = compute_network(projet, params['ref_algo'], params['ref_ori'], params['ref_capa'], params['ref_dem'], r_src, r_dst, r_v, r_v, 1.0, r_p, r_ecart)

                                for tgt in params['targets']:
                                    t_grid = tgt['grid']
                                    for t_ecart in t_grid["ecart_type"]:
                                        for t_epa in t_grid["m_epa"]:
                                            ratio = max(t_epa, 1e-6) / max(r_epa, 1e-6)
                                            ffi_wrapper.modif_multiplicateur(projet, ratio)

                                            for t_dst in t_grid["m_dst"]:
                                                for t_src in t_grid["m_src"]:
                                                    for t_v in t_grid["vitesse"]:
                                                        for t_p in t_grid["portion"]:

                                                            if tgt['algo'] == "EPANET":
                                                                graph_tgt = compute_network(projet, tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'], 1.0, 1.0, t_v, t_v, 1.0, t_p, t_ecart)
                                                            else:
                                                                graph_tgt = compute_network(projet, tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'], t_src, t_dst, t_v, t_v, 1.0, t_p, t_ecart)

                                                            metrics = compute_metrics(
                                                                graph_ref, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt, 
                                                                r_src, r_epa, r_dst, r_v, r_p, r_ecart,
                                                                t_src, t_epa, t_dst, t_v, t_p, t_ecart
                                                            )
                                                            metrics["rand_ecart"] = rand_ecart
                                                            results.append(metrics)

                                                            ffi_wrapper.free_graph(graph_tgt)

                                            ffi_wrapper.modif_multiplicateur(projet, 1.0 / ratio)

                                ffi_wrapper.free_graph(graph_ref)

                ffi_wrapper.modif_multiplicateur(projet, 1.0 / max(r_epa, 1e-6))

    finally:
        if projet is not None:
            ffi_wrapper.free_project(projet)
            
    return results