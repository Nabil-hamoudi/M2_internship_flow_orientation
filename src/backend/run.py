import os
import random
from src.wrapper_tools import ffi_wrapper

from src.backend.extract_data import (
    extract_data, extract_dashboard_metrics, compute_metrics, DEMANDES
)

def compute_algo(reseau, choix, m_src, m_dst, tank_as_reservoir=False):
    if tank_as_reservoir:
        ffi_wrapper.treat_tanks_as_reservoirs(reseau)
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

def compute_network(projet, choix_algo, choix_ori, choix_capa, choix_dem, p_src, p_dem, v_res, v_arc, mult_epa=1.0, portion=1.0, ecart_type=0.3, tank_as_reservoir=False):
    ffi_wrapper.modif_multiplicateur(projet, max(mult_epa, 1e-6))
    reseau = None

    demandes_epanet = [d for d in DEMANDES if d == "EPANET"]

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
            compute_algo(reseau, choix_capa, p_src, p_dem, tank_as_reservoir)
            ffi_wrapper.fix_capacite_flow_calcule(reseau)
            ffi_wrapper.nullifier_flow(reseau)

        compute_orientation(projet, reseau, choix_ori, p_src, p_dem, portion)
        compute_algo(reseau, choix_algo, p_src, p_dem, tank_as_reservoir)
        
        if choix_dem in demandes_epanet:
            ffi_wrapper.get_epanet_fulldemande(projet, reseau)

    ffi_wrapper.modif_multiplicateur(projet, 1.0)
    return reseau

def run_single_simulation(filepath, choix_algo, choix_ori, choix_capa, choix_dem, 
                          p_src, p_dem, v_res, v_arc, mult_epa=1.0, portion=1.0, 
                          seed=None, ecart_type=0.3, tank_as_reservoir=False):
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
                             p_src, p_dem, v_res, v_arc, mult_epa, portion, ecart_type, tank_as_reservoir)
                             
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

def build_cartesian_tasks(file_entries, params):
    """
    Construit le produit cartésien aplati de toutes les simulations atomiques.
    
    Args:
        file_entries: liste de tuples (filepath, filename, flags, rand_type, seed_val, rand_ecart)
        params: dictionnaire contenant ref_grid, ref_algo, ref_ori, ref_capa, ref_dem, ref_tank, targets
    
    Returns:
        Liste de tuples atomiques, chacun représentant une simulation individuelle.
        Les tuples sont triés par (filepath, rand_type, seed_val, ref_combo) pour
        optimiser la réutilisation du graph_ref dans les workers.
    """
    ref_grid = params['ref_grid']
    
    # Paramètres de référence légers (sans les grilles, pour éviter la duplication)
    ref_params = {
        'ref_algo': params['ref_algo'],
        'ref_ori': params['ref_ori'],
        'ref_capa': params['ref_capa'],
        'ref_dem': params['ref_dem'],
        'ref_tank': params.get('ref_tank', False),
    }
    
    all_tasks = []
    
    for filepath, filename, flags, rand_type, seed_val, rand_ecart in file_entries:
        for r_ecart in ref_grid["ecart_type"]:
            for r_epa in ref_grid["m_epa"]:
                for r_dst in ref_grid["m_dst"]:
                    for r_src in ref_grid["m_src"]:
                        for r_v in ref_grid["vitesse"]:
                            for r_p in ref_grid["portion"]:
                                ref_combo = (r_ecart, r_epa, r_dst, r_src, r_v, r_p)
                                
                                for tgt in params['targets']:
                                    t_grid = tgt['grid']
                                    for t_ecart in t_grid["ecart_type"]:
                                        for t_epa in t_grid["m_epa"]:
                                            for t_dst in t_grid["m_dst"]:
                                                for t_src in t_grid["m_src"]:
                                                    for t_v in t_grid["vitesse"]:
                                                        for t_p in t_grid["portion"]:
                                                            tgt_combo = (t_ecart, t_epa, t_dst, t_src, t_v, t_p)
                                                            
                                                            all_tasks.append((
                                                                filepath, filename, flags,
                                                                rand_type, seed_val, rand_ecart,
                                                                ref_combo, tgt, tgt_combo,
                                                                ref_params
                                                            ))
    
    # Tri par (filepath, rand_type, seed_val, ref_combo) pour que les tâches partageant
    # le même graph_ref soient adjacentes → optimise le cache dans les workers
    all_tasks.sort(key=lambda t: (t[0], t[3], t[4], t[6]))
    
    return all_tasks


def distribute_tasks(all_tasks, num_workers):
    """
    Distribue les tâches atomiques uniformément entre les workers en round-robin.
    Les tâches étant pré-triées par (filepath, ref_combo), le round-robin distribue
    des blocs contigus qui partagent le même graph_ref au même worker.
    
    Args:
        all_tasks: liste triée de tâches atomiques
        num_workers: nombre de workers
    
    Returns:
        Liste de num_workers paquets (listes de tâches).
        Les paquets vides ne sont pas inclus.
    """
    actual_workers = min(num_workers, len(all_tasks))
    if actual_workers == 0:
        return []
    
    chunk_size = len(all_tasks) // actual_workers
    remainder = len(all_tasks) % actual_workers
    
    chunks = []
    start = 0
    for i in range(actual_workers):
        # Les premiers 'remainder' workers reçoivent 1 tâche de plus
        end = start + chunk_size + (1 if i < remainder else 0)
        chunks.append(all_tasks[start:end])
        start = end
    
    return chunks


def _apply_randomization(projet, rand_type, rand_ecart):
    """Applique la randomisation des demandes sur un projet EPANET."""
    if rand_type == "Uniforme":
        ffi_wrapper.randomise_demande(projet)
    elif rand_type == "Normale":
        ffi_wrapper.randomise_demande_normale(projet, rand_ecart)
    elif rand_type == "Exponentielle":
        ffi_wrapper.randomise_demande_exponentielle(projet, rand_ecart)
    elif rand_type == "Toutes à 1":
        ffi_wrapper.set_demande_un(projet)


def run_analysis_worker(task_chunk):
    """
    Traite un paquet de tâches atomiques. Maintient un cache local pour :
    - Les projets EPANET (un par clé (filepath, rand_type, seed_val))
    - Le graph_ref (recalculé uniquement quand la clé ref change)
    
    Args:
        task_chunk: liste de tuples atomiques (pré-triés par filepath+ref_combo)
    
    Returns:
        Liste de dictionnaires de métriques.
    """
    results = []
    projet_cache = {}       # (filepath, rand_type, seed_val) -> projet
    current_ref_key = None   # (filepath, rand_type, seed_val, ref_combo)
    graph_ref = None
    
    try:
        for task in task_chunk:
            (filepath, filename, flags,
             rand_type, seed_val, rand_ecart,
             ref_combo, tgt, tgt_combo,
             ref_params) = task
            
            r_ecart, r_epa, r_dst, r_src, r_v, r_p = ref_combo
            t_ecart, t_epa, t_dst, t_src, t_v, t_p = tgt_combo
            
            # --- Cache du projet EPANET ---
            projet_key = (filepath, rand_type, seed_val)
            if projet_key not in projet_cache:
                projet = ffi_wrapper.create_epanet_project(filepath)
                ffi_wrapper.set_random_seed(seed_val)
                _apply_randomization(projet, rand_type, rand_ecart)
                projet_cache[projet_key] = projet
            projet = projet_cache[projet_key]
            
            # --- Cache du graph_ref ---
            new_ref_key = (filepath, rand_type, seed_val, ref_combo)
            if new_ref_key != current_ref_key:
                if graph_ref is not None:
                    ffi_wrapper.free_graph(graph_ref)
                
                ffi_wrapper.modif_multiplicateur(projet, max(r_epa, 1e-6))
                
                if ref_params['ref_algo'] == "EPANET":
                    graph_ref = compute_network(
                        projet, ref_params['ref_algo'], ref_params['ref_ori'],
                        ref_params['ref_capa'], ref_params['ref_dem'],
                        1.0, 1.0, r_v, r_v, r_epa, r_p, r_ecart,
                        ref_params['ref_tank']
                    )
                else:
                    graph_ref = compute_network(
                        projet, ref_params['ref_algo'], ref_params['ref_ori'],
                        ref_params['ref_capa'], ref_params['ref_dem'],
                        r_src, r_dst, r_v, r_v, r_epa, r_p, r_ecart,
                        ref_params['ref_tank']
                    )
                current_ref_key = new_ref_key
            
            # --- Calcul target ---
            actual_t_epa = r_epa * t_epa
            ffi_wrapper.modif_multiplicateur(projet, max(actual_t_epa, 1e-6))
            
            if tgt['algo'] == "EPANET":
                graph_tgt = compute_network(
                    projet, tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'],
                    1.0, 1.0, t_v, t_v, actual_t_epa, t_p, t_ecart,
                    tgt.get('tank_as_reservoir', False)
                )
            else:
                graph_tgt = compute_network(
                    projet, tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'],
                    t_src, t_dst, t_v, t_v, actual_t_epa, t_p, t_ecart,
                    tgt.get('tank_as_reservoir', False)
                )
            
            metrics = compute_metrics(
                graph_ref, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt,
                r_src, r_epa, r_dst, r_v, r_p, r_ecart,
                t_src, actual_t_epa, t_dst, t_v, t_p, t_ecart
            )
            metrics["rand_ecart"] = rand_ecart
            results.append(metrics)
            
            ffi_wrapper.free_graph(graph_tgt)
    
    finally:
        if graph_ref is not None:
            ffi_wrapper.free_graph(graph_ref)
        for projet in projet_cache.values():
            ffi_wrapper.free_project(projet)
    
    return results


def build_iterative_tasks(file_entries, params):
    """
    Construit les séquences de tâches itératives pour les cibles de type itératif.
    Chaque séquence contient un ref_combo et la liste ordonnée de tous les tgt_combos.
    Les séquences sont traitées séquentiellement par run_iterative_worker.
    
    Returns:
        Liste de tuples (filepath, filename, flags, rand_type, seed_val, rand_ecart,
                         ref_combo, tgt, tgt_combos, ref_params)
    """
    iterative_targets = params.get('iterative_targets', [])
    if not iterative_targets:
        return []
    
    ref_grid = params['ref_grid']
    ref_params = {
        'ref_algo': params['ref_algo'],
        'ref_ori': params['ref_ori'],
        'ref_capa': params['ref_capa'],
        'ref_dem': params['ref_dem'],
        'ref_tank': params.get('ref_tank', False),
    }
    
    all_sequences = []
    
    for filepath, filename, flags, rand_type, seed_val, rand_ecart in file_entries:
        for r_ecart in ref_grid["ecart_type"]:
            for r_epa in ref_grid["m_epa"]:
                for r_dst in ref_grid["m_dst"]:
                    for r_src in ref_grid["m_src"]:
                        for r_v in ref_grid["vitesse"]:
                            for r_p in ref_grid["portion"]:
                                ref_combo = (r_ecart, r_epa, r_dst, r_src, r_v, r_p)
                                
                                for tgt in iterative_targets:
                                    t_grid = tgt['grid']
                                    tgt_combos = []
                                    for t_ecart in t_grid["ecart_type"]:
                                        for t_epa in t_grid["m_epa"]:
                                            for t_dst in t_grid["m_dst"]:
                                                for t_src in t_grid["m_src"]:
                                                    for t_v in t_grid["vitesse"]:
                                                        for t_p in t_grid["portion"]:
                                                            tgt_combos.append((t_ecart, t_epa, t_dst, t_src, t_v, t_p))
                                    
                                    all_sequences.append((
                                        filepath, filename, flags,
                                        rand_type, seed_val, rand_ecart,
                                        ref_combo, tgt, tgt_combos,
                                        ref_params
                                    ))
    
    return all_sequences


def run_iterative_worker(task_sequence):
    """
    Traite une séquence itérative. Pour chaque pas de multiplicateur :
    - Compare avec la référence (résultat avec uid principal, suffixe 'vs Réf')
    - Compare avec le pas précédent (résultat avec uid_prev, suffixe 'vs Préc')
    
    Le calcul de min_cut est désactivé pour préserver l'état des graphes
    entre les comparaisons successives.
    """
    (filepath, filename, flags,
     rand_type, seed_val, rand_ecart,
     ref_combo, tgt, tgt_combos,
     ref_params) = task_sequence
    
    r_ecart, r_epa, r_dst, r_src, r_v, r_p = ref_combo
    
    results = []
    projet = None
    graph_ref = None
    graph_prev = None
    prev_combo = None
    
    uid_ref = tgt['uid']
    uid_prev = tgt['uid_prev']
    name_ref = tgt['name'] + " (vs Réf)"
    name_prev = tgt['name'] + " (vs Préc)"
    
    tgt_vs_ref = dict(tgt)
    tgt_vs_ref['uid'] = uid_ref
    tgt_vs_ref['name'] = name_ref
    
    tgt_vs_prev = dict(tgt)
    tgt_vs_prev['uid'] = uid_prev
    tgt_vs_prev['name'] = name_prev
    
    try:
        projet = ffi_wrapper.create_epanet_project(filepath)
        ffi_wrapper.set_random_seed(seed_val)
        _apply_randomization(projet, rand_type, rand_ecart)
        
        # Calcul du graphe de référence
        ffi_wrapper.modif_multiplicateur(projet, max(r_epa, 1e-6))
        if ref_params['ref_algo'] == "EPANET":
            graph_ref = compute_network(
                projet, ref_params['ref_algo'], ref_params['ref_ori'],
                ref_params['ref_capa'], ref_params['ref_dem'],
                1.0, 1.0, r_v, r_v, r_epa, r_p, r_ecart,
                ref_params['ref_tank']
            )
        else:
            graph_ref = compute_network(
                projet, ref_params['ref_algo'], ref_params['ref_ori'],
                ref_params['ref_capa'], ref_params['ref_dem'],
                r_src, r_dst, r_v, r_v, r_epa, r_p, r_ecart,
                ref_params['ref_tank']
            )
        
        for step_idx, tgt_combo in enumerate(tgt_combos):
            t_ecart, t_epa, t_dst, t_src, t_v, t_p = tgt_combo
            
            actual_t_epa = r_epa * t_epa
            ffi_wrapper.modif_multiplicateur(projet, max(actual_t_epa, 1e-6))
            
            if tgt['algo'] == "EPANET":
                graph_tgt = compute_network(
                    projet, tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'],
                    1.0, 1.0, t_v, t_v, actual_t_epa, t_p, t_ecart,
                    tgt.get('tank_as_reservoir', False)
                )
            else:
                graph_tgt = compute_network(
                    projet, tgt['algo'], tgt['ori'], tgt['capa'], tgt['dem'],
                    t_src, t_dst, t_v, t_v, actual_t_epa, t_p, t_ecart,
                    tgt.get('tank_as_reservoir', False)
                )
            
            # Métriques vs référence (min_cut désactivé pour préserver l'état du graphe)
            metrics_ref = compute_metrics(
                graph_ref, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt_vs_ref,
                r_src, r_epa, r_dst, r_v, r_p, r_ecart,
                t_src, actual_t_epa, t_dst, t_v, t_p, t_ecart,
                compute_min_cut_flag=False
            )
            metrics_ref['rand_ecart'] = rand_ecart
            metrics_ref['is_iterative'] = True
            metrics_ref['iter_compare_type'] = 'iter_vs_ref'
            metrics_ref['iter_step_index'] = step_idx
            results.append(metrics_ref)
            
            # Métriques vs pas précédent
            if graph_prev is not None and prev_combo is not None:
                prev_ecart, prev_epa, prev_dst, prev_src, prev_v, prev_p = prev_combo
                prev_actual_epa = r_epa * prev_epa
                
                metrics_prev = compute_metrics(
                    graph_prev, graph_tgt, filepath, filename, flags, rand_type, seed_val, tgt_vs_prev,
                    prev_src, prev_actual_epa, prev_dst, prev_v, prev_p, prev_ecart,
                    t_src, actual_t_epa, t_dst, t_v, t_p, t_ecart,
                    compute_min_cut_flag=False
                )
                metrics_prev['rand_ecart'] = rand_ecart
                metrics_prev['is_iterative'] = True
                metrics_prev['iter_compare_type'] = 'iter_vs_prev'
                metrics_prev['iter_step_index'] = step_idx
                results.append(metrics_prev)
                ffi_wrapper.free_graph(graph_prev)
            
            prev_combo = tgt_combo
            graph_prev = graph_tgt
    
    finally:
        if graph_prev is not None:
            ffi_wrapper.free_graph(graph_prev)
        if graph_ref is not None:
            ffi_wrapper.free_graph(graph_ref)
        if projet is not None:
            ffi_wrapper.free_project(projet)
    
    return results