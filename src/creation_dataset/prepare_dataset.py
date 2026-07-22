import os
import wntr

def file_contains_elements(filepath):
    flags = {"tanks": False, "pumps": False, "valves": False, "reservoir_count": 0}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            current_section = None
            for line in f:
                line_strip = line.strip()
                if not line_strip:
                    continue
                if line_strip.startswith('[') and line_strip.endswith(']'):
                    current_section = line_strip.upper()
                    continue
                
                # Ajout de [RESERVOIRS] aux sections scannées
                if current_section in ['[TANKS]', '[PUMPS]', '[VALVES]', '[RESERVOIRS]'] and not line_strip.startswith(';'):
                    if current_section == '[TANKS]': 
                        flags["tanks"] = True
                    elif current_section == '[PUMPS]': 
                        flags["pumps"] = True
                    elif current_section == '[VALVES]': 
                        flags["valves"] = True
                    elif current_section == '[RESERVOIRS]':
                        flags["reservoir_count"] += 1
    except Exception:
        pass
    return flags

def open_file_epa_int(fichier_source):
    wn = None
    try:
        wn = wntr.network.WaterNetworkModel(fichier_source)

    except Exception as e:
        print(f"Erreur lors de l'init '{fichier_source}': {e}")

    return wn

def convertir_unites(wn, unite_cible='LPS'):
    try:
        wn.options.hydraulic.inpfile_units = unite_cible

    except Exception as e:
        print(f"Erreur lors de la conversion de : {e}")
        return False
    
    return True

def change_mode(wn, mode_cible='PDA', p_min=0.0, p_req=20.0, p_exp=0.5):
    try:
        wn.options.hydraulic.demand_model = mode_cible
        if (mode_cible == "PDA"):
            wn.options.hydraulic.minimum_pressure = p_min
            wn.options.hydraulic.required_pressure = p_req
            wn.options.hydraulic.pressure_exponent = p_exp
    except Exception as e:
        print(f"Erreur lors de la conversion de : {e}")
        return False
    
    return True

def write_file(wn, fichier_destination):
    try:
        wntr.network.write_inpfile(wn, fichier_destination)

    except Exception as e:
        print(f"Erreur lors de la conversion de '{fichier_destination}': {e}")
        return False

    return True

import os

def convertir_unites_dossier(dossier_source, dossier_destination, unite_cible='LPS', mode_simu='PDA', p_min=0.0, p_req=10.0, p_exp=0.5):
    # Création du dossier de destination s'il n'existe pas
    if not os.path.exists(dossier_destination):
        os.makedirs(dossier_destination)

    fichiers_inp = []
    
    for root, dirs, files in os.walk(dossier_source):
        for file in files:
            if file.endswith('.inp'):
                fichiers_inp.append(os.path.join(root, file))
    
    if not fichiers_inp:
        print(f"Avertissement : Aucun fichier .inp trouvé dans '{dossier_source}' ou ses sous-dossiers.")
        return 0, 0

    reussites = 0
    echecs = 0

    print(f"Début de la conversion de {len(fichiers_inp)} fichier(s) vers '{unite_cible}'...")

    for chemin_fichier in fichiers_inp:
        chemin_relatif = os.path.relpath(chemin_fichier, dossier_source)
        chemin_sauvegarde = os.path.join(dossier_destination, chemin_relatif)
        
        dossier_sauvegarde = os.path.dirname(chemin_sauvegarde)
        if not os.path.exists(dossier_sauvegarde):
            os.makedirs(dossier_sauvegarde)

        try:
            wn = open_file_epa_int(chemin_fichier)
            
            convertir_unites(wn, unite_cible)
            change_mode(wn, mode_simu, p_min, p_req, p_exp)
            
            succes = write_file(wn, chemin_sauvegarde)
            
            if succes:
                reussites += 1
            else:
                echecs += 1
        except Exception as e:
            print(f"Erreur lors du traitement de {chemin_fichier} : {e}")
            echecs += 1

    print(f"Réussites : {reussites}")
    print(f"Échecs : {echecs}")