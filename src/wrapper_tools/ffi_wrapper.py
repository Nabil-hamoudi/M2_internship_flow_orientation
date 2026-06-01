from librairie._reseau_C import ffi, lib
import time

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

def delete_source_destination(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.delete_source_destination(p_reseau)

def export_flow_matrix(p_reseau, file):
    p_reseau = get_graph_pointer(p_reseau)
    lib.export_flow_matrix(p_reseau, ensure_bytes(file))


def fix_capacite_flow(p_reseau, vitesse_reservoir, vitesse_arcs):
    p_reseau = get_graph_pointer(p_reseau)
    lib.fix_capacite_flow(p_reseau, vitesse_reservoir, vitesse_arcs)

def fix_capacite_flow_calcule(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.fix_capacite_flow_calcule(p_reseau)

def fix_capacite_flow_oriente(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.fix_capacite_flow_oriente(p_reseau)

def get_epanet_demande(p_projet, p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.get_epanet_demande(p_projet, p_reseau)

def get_epanet_fulldemande(p_projet, p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.get_epanet_fulldemande(p_projet, p_reseau)

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

def set_random_seed(seed=None):
    if seed is None:
        seed = int(time.time())
    lib.set_random_seed(seed)

def compute_epanet(p_projet):
    lib.comput_flow(p_projet)

def reget_epanet_flow(p_projet, p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.reget_epanet_flow(p_projet, p_reseau)

def import_epanet_graph(p_projet):
    return lib.chargement_graph(p_projet)

def get_nom_type_arc(type_enum):
    return ffi.string(lib.get_nom_type_arc(type_enum)).decode('utf-8') 

def get_nom_type_sommet(type_enum):
    return ffi.string(lib.get_nom_type_sommet(type_enum)).decode('utf-8')

def free_graph(p_reseau):
    if p_reseau is not None:
        p_reseau = get_graph_pointer(p_reseau)
        lib.free_graph(p_reseau)

def free_project(p_projet):
    lib.fermeture_free_project(p_projet)

def compute_satisfaction_rate(p_reseau):
    p_reseau = get_graph_pointer(p_reseau)
    lib.compute_satisfaction_rate(p_reseau)
