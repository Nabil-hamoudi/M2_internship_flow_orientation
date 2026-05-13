from librairie._reseau_C import ffi, lib

def ensure_bytes(chaine):
    if isinstance(chaine, str):
        return chaine.encode()
    return chaine

def get_graph_pointer(p_reseau):
    if ffi.typeof(p_reseau).kind != 'pointer':
        return ffi.addressof(p_reseau)

    return p_reseau

def print_graph_details(p_reseau, vitesse_reservoir, vitesse_arcs):
    p_reseau = get_graph_pointer(p_reseau)
    return lib.print_graph_details(p_reseau, vitesse_reservoir, vitesse_arcs)

def export_flow_matrix(p_reseau, file, source_destination):
    p_reseau = get_graph_pointer(p_reseau)
    lib.export_flow_matrix(p_reseau, ensure_bytes(file), 0)

def fix_capacite_flow(p_reseau, vitesse_reservoir, vitesse_arcs):
    p_reseau = get_graph_pointer(p_reseau)
    lib.fix_capacite_flow(p_reseau, vitesse_reservoir, vitesse_arcs)

def fix_capacite_flow_oriente(p_reseau, vitesse_reservoir, vitesse_arcs):
    p_reseau = get_graph_pointer(p_reseau)
    lib.fix_capacite_flow_oriente(p_reseau, vitesse_reservoir, vitesse_arcs)

def ajout_source_destination(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.ajout_source_destination(p_reseau)

def ajout_capacite_demande(p_reseau, proportion_demande):
    p_reseau = get_graph_pointer(p_reseau)
    lib.ajout_capacite_demande(p_reseau, proportion_demande)

def ajout_capacite_source(p_reseau, proportion_source):
    p_reseau = get_graph_pointer(p_reseau)
    lib.ajout_capacite_source(p_reseau, proportion_source)

def nullifier_flow(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.nullifier_flow(p_reseau)

def compute_flow_ford_fukerson(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.compute_flow_ford_fukerson(p_reseau)

def compute_flow_edmonds_karp(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.compute_flow_edmonds_karp(p_reseau)

def create_epanet_project(input):
    projet = lib.init_inp_file(ensure_bytes(input), b"epanet_file.log", b"resultat.res")
    return ffi.new("EN_Project *", projet)

def randomise_demande(p_projet):
    lib.randomise_demande(p_projet)

def modif_multiplicateur(p_projet, mult):
    lib.modif_multiplicateur(p_projet, mult)

def compute_epanet(p_projet):
    lib.comput_flow(p_projet)

def import_epanet_graph(p_projet):
    return lib.chargement_graph(p_projet)

def extraire_arcs_orientes_dominants(graph_ptr):
    active_set = set()

    nb_tuyaux = graph_ptr.nb_arcs // 2
    
    for k in range(nb_tuyaux):
        idx_aller = 2 * k
        idx_retour = 2 * k + 1
        
        flow_aller = graph_ptr.arcs[idx_aller].flow
        flow_retour = graph_ptr.arcs[idx_retour].flow
        
        if flow_aller > 0 or flow_retour > 0:
            if flow_aller > flow_retour:
                active_set.add(idx_aller)
            elif flow_retour > flow_aller:
                active_set.add(idx_retour)
            
    return active_set

def extraire_tuyaux_physiques_actifs(graph_ptr):
    active_set = set()
    nb_tuyaux = graph_ptr.nb_arcs // 2
    
    for k in range(nb_tuyaux):
        flow_aller = graph_ptr.arcs[2 * k].flow
        flow_retour = graph_ptr.arcs[2 * k + 1].flow
        
        if flow_aller != flow_retour and (flow_aller > 0 or flow_retour > 0):
            active_set.add(k)
            
    return active_set


def jaccard_distance_non_symmetrique(graph1_ptr, graph2_ptr):
    active1 = extraire_arcs_orientes_dominants(graph1_ptr)
    active2 = extraire_arcs_orientes_dominants(graph2_ptr)
    
    union = len(active1 | active2)
    if union == 0:
        return 0.0
        
    intersection = len(active1 & active2)
    return 1.0 - (intersection / union)


def jaccard_distance_symmetrique(graph1_ptr, graph2_ptr):
    active1 = extraire_tuyaux_physiques_actifs(graph1_ptr)
    active2 = extraire_tuyaux_physiques_actifs(graph2_ptr)
    
    union = len(active1 | active2)
    if union == 0:
        return 0.0
        
    intersection = len(active1 & active2)
    return 1.0 - (intersection / union)

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
    count = 0
    n_arcs = get_n_arcs(p_reseau, ignore_source_dest)
    
    for i in range(n_arcs):
        if p_reseau.arcs[i].flow != 0.0:
            count += 1
    return count

def get_arcs_symmetrique(p_reseau, ignore_source_dest=False):
    p_reseau = get_graph_pointer(p_reseau)
    count = 0
    n_arcs = get_n_arcs(p_reseau, ignore_source_dest)
    nb_tuyaux = n_arcs // 2
    
    TYPE_SOURCE = 0
    TYPE_DESTINATION = 2
    
    for k in range(nb_tuyaux):
        arc_aller = p_reseau.arcs[2 * k]
        arc_retour = p_reseau.arcs[2 * k + 1]
        
        if (arc_aller.source.type != TYPE_SOURCE and arc_aller.source.type != TYPE_DESTINATION and
            arc_aller.destination.type != TYPE_SOURCE and arc_aller.destination.type != TYPE_DESTINATION):
            
            if arc_aller.flow > 0.0 and arc_retour.flow > 0.0:
                count += 1
                
    return count