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


def export_flow_matrix(p_reseau, file, ignore_source_dest=False):
    p_reseau = get_graph_pointer(p_reseau)
    lib.export_flow_matrix(p_reseau, ensure_bytes(file), ignore_source_dest)


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


def create_epanet_project(input_file):
    projet = lib.init_inp_file(ensure_bytes(
        input_file), b"epanet_file.log", b"resultat.res")
    return ffi.new("EN_Project *", projet)


def randomise_demande(p_projet):
    lib.randomise_demande(p_projet)


def modif_multiplicateur(p_projet, mult):
    lib.modif_multiplicateur(p_projet, mult)


def compute_epanet(p_projet):
    lib.comput_flow(p_projet)


def import_epanet_graph(p_projet):
    return lib.chargement_graph(p_projet)


def free_graph(p_reseau):
    if p_reseau is not None:
        p_reseau = get_graph_pointer(p_reseau)
        lib.free_graph(p_reseau)


def compute_satisfaction_rate(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.compute_satisfaction_rate(p_reseau)
