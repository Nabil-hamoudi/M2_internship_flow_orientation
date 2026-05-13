import pytest
from librairie._reseau_C import ffi, lib
from wrapper_tools.ffi_wrapper import create_epanet_project

@pytest.fixture
def reseau_mock():
    """
    Fixture pour créer un pointeur de graphe C (struct graph *) basique.
    À adapter selon la façon dont vous initialisez un graphe valide en C.
    """
    # Exemple d'allocation basique (à remplacer par votre vraie logique d'init)
    # ptr = lib.assignation_graph(...)
    # yield ptr
    # lib.free_graph(ptr)
    pytest.skip("Fixture reseau_mock à configurer")

@pytest.fixture
def epanet_project_mock(tmp_path):
    """
    Fixture pour créer un projet EPANET temporaire.
    Utilise tmp_path (fourni par pytest) pour éviter de polluer le dossier.
    """
    dummy_inp = tmp_path / "test.inp"
    dummy_inp.write_text("[TITLE]\nTest Project")
    
    # Init du projet via votre wrapper
    p_projet = create_epanet_project(str(dummy_inp))
    yield p_projet
    
    # Nettoyage si nécessaire
    # lib.fermeture_free_project(p_projet)