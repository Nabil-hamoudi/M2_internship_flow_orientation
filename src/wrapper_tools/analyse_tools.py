from librairie._reseau_C import ffi, lib
from src.wrapper_tools.ffi_wrapper import get_graph_pointer
import numpy as np


def get_nom_type_sommet(type_sommet):
    return lib.get_nom_type_sommet(type_sommet)


def get_nom_type_arc(type_arc):
    return lib.get_nom_type_arc(type_arc)


def extraire_arcs_orientes_dominants(p_reseau, ignore_source_dest=False):
    nb_tuyaux = p_reseau.nb_arcs // 2

    if ignore_source_dest is False:
        nb_tuyaux -= p_reseau.sommet_source.degree + p_reseau.sommet_destination.degree

    active_set = np.zeros(nb_tuyaux*2, dtype=np.int64)
    set_size = 0

    idx_aller = 0
    idx_retour = 1
    for k in range(nb_tuyaux):

        flow_aller = p_reseau.arcs[idx_aller].flow
        flow_retour = p_reseau.arcs[idx_retour].flow

        if flow_aller != flow_retour and (flow_aller > 0 or flow_retour > 0):
            if flow_aller > flow_retour:
                active_set[set_size] = idx_aller
                set_size += 1
            else:
                active_set[set_size] = idx_retour
                set_size += 1

        idx_aller += 2
        idx_retour += 2

    active_set.resize(set_size)

    return active_set


def jaccard_distance(graph1_ptr, graph2_ptr):
    active1 = extraire_arcs_orientes_dominants(graph1_ptr)
    active2 = extraire_arcs_orientes_dominants(graph2_ptr)

    union = np.union1d(active1, active2)
    if union.shape[0] == 0:
        return 1.0

    intersection = np.intersect1d(active1, active2)
    return 1.0 - (intersection.shape[0] / union.shape[0])


def get_efficacite(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.satifaisabilite


def get_n_sommet(p_reseau, ignore_source_dest=False):
    p_reseau = get_graph_pointer(p_reseau)
    if ignore_source_dest:
        return p_reseau.nb_sommet - 2
    return p_reseau.nb_sommet


def get_n_arcs(p_reseau, ignore_source_dest=False):
    p_reseau = get_graph_pointer(p_reseau)
    if ignore_source_dest:
        return p_reseau.nb_arcs - ((p_reseau.sommet_source.degree + p_reseau.sommet_destination.degree) * 2)
    return p_reseau.nb_arcs


def get_n_arcs_non_nul(p_reseau, ignore_source_dest=False):
    p_reseau = get_graph_pointer(p_reseau)
    arcs = extraire_arcs_orientes_dominants(p_reseau, ignore_source_dest)
    return arcs.shape[0]


def get_arcs_symmetrique(p_reseau, ignore_source_dest=False):
    nb_tuyaux = p_reseau.nb_arcs // 2

    if ignore_source_dest is False:
        nb_tuyaux -= p_reseau.sommet_source.degree + p_reseau.sommet_destination.degree

    active_set = np.zeros(nb_tuyaux*2)
    set_size = 0

    idx_aller = 0
    idx_retour = 1
    for k in range(nb_tuyaux):

        flow_aller = p_reseau.arcs[idx_aller].flow
        flow_retour = p_reseau.arcs[idx_retour].flow

        if flow_aller != flow_retour and (flow_aller > 0 and flow_retour > 0):
            active_set[set_size] = idx_aller
            set_size += 1
            active_set[set_size] = idx_retour
            set_size += 1

        idx_aller += 2
        idx_retour += 2

    active_set.resize((set_size, 1))

    return active_set


def compute_velocity(p_reseau, arc_index):
    p_reseau = get_graph_pointer(p_reseau)
    return lib.compute_velocity(p_reseau, arc_index)


def get_pression_requise(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.pression_requise


def get_exposant_pression(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.exposant_pression


def get_demande_global(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.demande_global


def get_demande_multiplier(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.demande_multiplier


def get_wape_flow(graph_ref, graph_sim, ignore_source_dest=False):
    gref = get_graph_pointer(graph_ref)
    gsim = get_graph_pointer(graph_sim)

    if get_n_arcs(gref, ignore_source_dest) != get_n_arcs(gsim, ignore_source_dest):
        return -1.0

    somme_erreurs = 0.0
    somme_flux_ref = 0.0

    n = get_n_arcs(gsim, ignore_source_dest)

    for i in range(n):
        a1, a2 = graph_ref.arcs[i], graph_sim.arcs[i]
        
        somme_erreurs += np.absolute(a1.flow - a2.flow)
        
        somme_flux_ref += np.absolute(a1.flow)

    if somme_flux_ref == 0.0:
        return 0.0 

    return somme_erreurs / somme_flux_ref