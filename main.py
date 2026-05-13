

def safe_get_metrics(graph1_ptr, graph2_ptr):
    """
    Calcule MAE et MSE en toute sécurité en itérant uniquement sur 
    les vrais tuyaux physiques, évitant ainsi les pointeurs nuls et 
    les erreurs de typage numpy.
    """
    flows1 = []
    flows2 = []
    g1 = ffi_wrapper.get_graph_pointer(graph1_ptr)
    g2 = ffi_wrapper.get_graph_pointer(graph2_ptr)
    
    n = min(g1.nb_arcs, g2.nb_arcs)
    for i in range(n):
        a1 = g1.arcs[i]
        a2 = g2.arcs[i]
        
        # FIX 1 : Vérifier explicitement que les pointeurs (cdata) ne sont pas nuls 
        # avant d'essayer d'accéder à l'attribut .type
        if a1.source and a1.destination and a2.source and a2.destination:
            # On ignore les arcs connectés aux nœuds virtuels (0=SOURCE, 2=DESTINATION)
            if a1.source.type not in (0, 2) and a1.destination.type not in (0, 2):
                flows1.append(a1.flow)
                flows2.append(a2.flow)
            
    if not flows1:
        return 0.0, 0.0
        
    arr1 = np.array(flows1, dtype=np.float64)
    arr2 = np.array(flows2, dtype=np.float64)
    
    # FIX 2 : Forcer la conversion en float natif Python pour garantir
    # la compatibilité avec l'affichage et Matplotlib
    mae = float(np.mean(np.abs(arr1 - arr2)))
    mse = float(np.mean((arr1 - arr2) ** 2))
    
    return mae, mse

# =====================================================================
# FONCTION DE SÉCURITÉ POUR LES MÉTRIQUES (Empêche le Crash)
# =====================================================================
def safe_get_metrics(graph1_ptr, graph2_ptr):
    """
    Calcule MAE et MSE en toute sécurité en itérant uniquement sur 
    les vrais tuyaux physiques, évitant ainsi les pointeurs nuls.
    """
    flows1 = []
    flows2 = []
    g1 = ffi_wrapper.get_graph_pointer(graph1_ptr)
    g2 = ffi_wrapper.get_graph_pointer(graph2_ptr)
    
    n = min(g1.nb_arcs, g2.nb_arcs)
    for i in range(n):
        a1 = g1.arcs[i]
        a2 = g2.arcs[i]
        # On ignore les arcs connectés aux nœuds virtuels (0=SOURCE, 2=DESTINATION)
        if a1.source.type not in (0, 2) and a1.destination.type not in (0, 2):
            flows1.append(a1.flow)
            flows2.append(a2.flow)
            
    if not flows1:
        return 0.0, 0.0
        
    arr1 = np.array(flows1, dtype=np.float64)
    arr2 = np.array(flows2, dtype=np.float64)
    
    mae = np.mean(np.abs(arr1 - arr2))
    mse = np.mean((arr1 - arr2) ** 2)
    return mae, mse

# =====================================================================
# FENÊTRE DE VISUALISATION (Graphe Standard)
# =====================================================================


# =====================================================================
# FENÊTRE D'ANALYSE (Module de comparaison et MATPLOTLIB)
# =====================================================================



# =====================================================================
# MANAGER PRINCIPAL
# =====================================================================


if __name__ == "__main__":
    app = AppManager()
    app.mainloop()