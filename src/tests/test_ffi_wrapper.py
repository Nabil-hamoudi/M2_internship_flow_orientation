import pytest
from wrapper_tools import ffi_wrapper
from librairie._reseau_C import ffi

def test_ensure_bytes():
    assert ffi_wrapper.ensure_bytes("test") == b"test"
    assert ffi_wrapper.ensure_bytes(b"test") == b"test"

def test_get_graph_pointer(reseau_mock):
    # Testez que la fonction gère bien à la fois un pointeur direct et une valeur déréférencée
    pytest.skip("À implémenter")

def test_print_graph_details(reseau_mock, capsys):
    # capsys permet de capturer ce qui est affiché dans la console par le C (si stdout n'est pas bypassé)
    pytest.skip("À implémenter")

def test_export_flow_matrix(reseau_mock, tmp_path):
    fichier_sortie = tmp_path / "matrice.csv"
    # ffi_wrapper.export_flow_matrix(reseau_mock, str(fichier_sortie))
    # assert fichier_sortie.exists()
    pytest.skip("À implémenter")

def test_fix_capacite_flow(reseau_mock):
    pytest.skip("À implémenter")

def test_fix_capacite_flow_oriente(reseau_mock):
    pytest.skip("À implémenter")

def test_ajout_source_destination(reseau_mock):
    pytest.skip("À implémenter")

def test_ajout_capacite_demande(reseau_mock):
    pytest.skip("À implémenter")

def test_ajout_capacite_source(reseau_mock):
    pytest.skip("À implémenter")

def test_nullifier_flow(reseau_mock):
    pytest.skip("À implémenter")

def test_compute_flow_ford_fukerson(reseau_mock):
    pytest.skip("À implémenter")

def test_compute_flow_edmonds_karp(reseau_mock):
    pytest.skip("À implémenter")

def test_create_epanet_project(tmp_path):
    dummy_inp = tmp_path / "test.inp"
    dummy_inp.write_text("[TITLE]\nTest")
    # p_projet = ffi_wrapper.create_epanet_project(str(dummy_inp))
    # assert p_projet is not None
    pytest.skip("À implémenter")

def test_randomise_demande(epanet_project_mock):
    pytest.skip("À implémenter")

def test_modif_multiplicateur(epanet_project_mock):
    pytest.skip("À implémenter")

def test_compute_epanet(epanet_project_mock):
    pytest.skip("À implémenter")

def test_import_epanet_graph(epanet_project_mock):
    pytest.skip("À implémenter")

def test_free_graph(reseau_mock):
    pytest.skip("À implémenter")

def test_compute_satisfaction_rate(reseau_mock):
    pytest.skip("À implémenter")