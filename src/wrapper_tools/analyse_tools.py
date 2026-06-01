from librairie._reseau_C import ffi, lib
from src.wrapper_tools.ffi_wrapper import get_graph_pointer
import numpy as np

def get_sommet_type(p_reseau, index):
    return get_graph_pointer(p_reseau).sommets[index].type

def get_sommet_degree(p_reseau, index):
    return get_graph_pointer(p_reseau).sommets[index].degree

def get_sommet_satisfaction(p_reseau, index):
    return get_graph_pointer(p_reseau).sommets[index].satisfaction

def get_sommet_elevation(p_reseau, index):
    return get_graph_pointer(p_reseau).sommets[index].elevation

def get_sommet_demande(p_reseau, index):
    return get_graph_pointer(p_reseau).sommets[index].demande

def get_sommet_pression(p_reseau, index):
    return get_graph_pointer(p_reseau).sommets[index].pression

def get_sommet_position(p_reseau, index):
    s = get_graph_pointer(p_reseau).sommets[index]
    return s.position.x, s.position.y

def get_arc_type(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].type

def get_arc_diametre(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].diametre

def get_arc_longueur(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].longueur

def get_arc_roughness(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].roughness

def get_arc_capacite(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].capacite

def get_arc_flow(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].flow

def get_arc_non_oriente_flow(p_reseau, index_aller, index_retour):
    return lib.get_flow_non_oriente(get_graph_pointer(p_reseau), index_aller, index_retour)

def get_arc_non_oriente_velocity(p_reseau, index_aller, index_retour):
    return lib.get_velocity_non_oriente(get_graph_pointer(p_reseau), index_aller, index_retour)

def get_arc_source_type(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].source.type

def get_arc_dest_type(p_reseau, index):
    return get_graph_pointer(p_reseau).arcs[index].destination.type

def get_arc_source_position(p_reseau, index):
    s = get_graph_pointer(p_reseau).arcs[index].source
    return s.position.x, s.position.y

def get_arc_dest_position(p_reseau, index):
    s = get_graph_pointer(p_reseau).arcs[index].destination
    return s.position.x, s.position.y

def get_nom_type_sommet(type_sommet):
    return lib.get_nom_type_sommet(type_sommet)


def get_nom_type_arc(type_arc):
    return lib.get_nom_type_arc(type_arc)


def extraire_arcs_orientes_dominants(p_reseau):
    nb_tuyaux = p_reseau.nb_arcs // 2

    active_set = np.zeros(nb_tuyaux*2, dtype=np.int32)
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

def extraire_arcs_nulles(p_reseau):
    nb_tuyaux = p_reseau.nb_arcs // 2

    active_set = np.zeros(nb_tuyaux*2, dtype=np.int32)
    set_size = 0

    idx_aller = 0
    idx_retour = 1
    for k in range(nb_tuyaux):
        flow_aller = p_reseau.arcs[idx_aller].flow
        flow_retour = p_reseau.arcs[idx_retour].flow

        if flow_aller == 0.0 and flow_retour == 0.0:
            active_set[set_size] = idx_aller
            set_size += 1
            active_set[set_size] = idx_retour
            set_size += 1

        idx_aller += 2
        idx_retour += 2

    active_set.resize(set_size)

    return active_set

def extraire_arcs_egaux(p_reseau):
    nb_tuyaux = p_reseau.nb_arcs // 2

    active_set = np.zeros(nb_tuyaux*2, dtype=np.int32)
    set_size = 0

    idx_aller = 0
    idx_retour = 1
    for k in range(nb_tuyaux):
        flow_aller = p_reseau.arcs[idx_aller].flow
        flow_retour = p_reseau.arcs[idx_retour].flow

        if flow_aller == flow_retour:
            active_set[set_size] = idx_aller
            set_size += 1
            active_set[set_size] = idx_retour
            set_size += 1

        idx_aller += 2
        idx_retour += 2

    active_set.resize(set_size)

    return active_set

def jaccard_distance(graph_ref, graph_sim):
    active1 = extraire_arcs_orientes_dominants(graph_ref)
    active2 = extraire_arcs_orientes_dominants(graph_sim)

    union = np.union1d(active1, active2)
    if union.shape[0] == 0:
        return 1.0

    intersection = np.intersect1d(active1, active2)
    return 1.0 - (intersection.shape[0] / union.shape[0])


def get_efficacite(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.satifaisabilite


def get_n_sommet(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.nb_sommet


def get_n_arcs(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return p_reseau.nb_arcs

def get_n_arcs_no(p_reseau):
    return get_n_arcs(p_reseau) / 2

def get_n_arcs_non_nul(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    arcs = extraire_arcs_orientes_dominants(p_reseau)
    return arcs.shape[0]

def get_n_arcs_nulles(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    return extraire_arcs_nulles(p_reseau).shape[0]


def get_arcs_symmetrique(p_reseau):
    nb_tuyaux = p_reseau.nb_arcs // 2

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


def get_wape_flow(graph_ref, graph_sim):
    gref = get_graph_pointer(graph_ref)
    gsim = get_graph_pointer(graph_sim)

    if get_n_arcs(gref) != get_n_arcs(gsim):
        return -1.0

    somme_erreurs = 0.0
    somme_flux_ref = 0.0

    n = get_n_arcs(gsim) // 2

    for i in range(n):
        a1_flow = np.absolute(graph_ref.arcs[2*i].flow - graph_ref.arcs[2*i + 1].flow)
        a2_flow = np.absolute(graph_sim.arcs[2*i].flow - graph_sim.arcs[2*i + 1].flow)
        
        somme_erreurs += np.absolute(a1_flow - a2_flow)
        
        somme_flux_ref += a1_flow

    if somme_flux_ref == 0.0:
        return 0.0 

    return somme_erreurs / somme_flux_ref

def get_wp_flow(graph_ref, graph_sim):
    gref = get_graph_pointer(graph_ref)
    gsim = get_graph_pointer(graph_sim)

    if get_n_arcs(gref) != get_n_arcs(gsim):
        return -1.0

    somme_erreurs = 0.0
    somme_flux_ref = 0.0

    n = get_n_arcs(gsim) // 2

    for i in range(n):
        a1_flow = np.absolute(graph_ref.arcs[2*i].flow - graph_ref.arcs[2*i + 1].flow )
        a2_flow = np.absolute(graph_sim.arcs[2*i].flow  - graph_sim.arcs[2*i + 1].flow )
        
        somme_erreurs += a1_flow - a2_flow
        
        somme_flux_ref += a1_flow

    if somme_flux_ref == 0.0:
        return 0.0 

    return somme_erreurs / somme_flux_ref
