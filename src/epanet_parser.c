#include "stdio.h"
#include "stdlib.h"
#include "epanet2.h"
#include "epanet2_2.h"
#include "epanet2_enums.h"
#include "structure.h"

enum type_sommet parser_type_sommet(int type_epanet) {
	switch (type_epanet) {
		case EN_RESERVOIR:
			return RESERVOIR;
		case EN_TANK:
			return TANK;
		case EN_JUNCTION:
			return JONCTION;
		default:
			return JONCTION;
    }
}

enum type_arcs parser_type_arc(int type_epanet) {
	switch (type_epanet) {
		case EN_PUMP:
			return POMPE;
		case EN_PIPE:
			return TUYAU;
		case EN_CVPIPE:
			return TUYAU;
		case EN_PRV:
			return VALVE;
		case EN_PSV:
			return VALVE;
		case EN_PBV:
			return VALVE;
		case EN_FCV:
			return VALVE;
		case EN_TCV:
			return VALVE;
		case EN_GPV:
			return VALVE;
		case EN_PCV:
			return VALVE;
		default:
			return TUYAU;
	}
}

EN_Project init_inp_file(char* input, char* log, char* binairy) {
	EN_Project ph;
	EN_createproject(&ph);
	int err = EN_open(ph, input, log, binairy);
	if (err > 0) exit(31);
	return ph;
}

// a revoir
void comput_flow(EN_Project* ph) {
	EN_solveH(*ph);
}

struct graph chargement_graph(EN_Project* ph) {
	int nb_sommets, nb_arcs;
	EN_getcount(*ph, EN_NODECOUNT, &nb_sommets);
	EN_getcount(*ph, EN_LINKCOUNT, &nb_arcs);
	struct graph G = assignation_graph(nb_sommets, nb_arcs*2);
	int *degrees = calloc(nb_sommets, sizeof(nbr));
	for (int j = 1 ; j <= nb_arcs ; j++) {
		int noeud1, noeud2;
		EN_getlinknodes(*ph, j, &noeud1,& noeud2);
		degrees[noeud1-1] += 1;
		degrees[noeud2-1] += 1;
	}

	for (int i = 1 ; i <= nb_sommets ; i++) {
		int type_node;
		double elevation, demande;
		EN_getnodetype(*ph, i, &type_node);
		type_node = parser_type_sommet(type_node);
		EN_getnodevalue(*ph, i, EN_ELEVATION, &elevation);
		EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demande);
		G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], elevation, demande);
		degrees[i-1] = 0;
	}

	for (int j = 1, i = 0 ; j <= nb_arcs ; j++, i += 2) {
		int noeud1, noeud2, type_epa;
		double diametre, longueur, flow;
		EN_getlinknodes(*ph, j, &noeud1, &noeud2);
		EN_getlinknodes(*ph, j, &noeud1, &noeud2);
		EN_getlinktype(*ph, j, &type_epa);
		type_epa = parser_type_arc(type_epa);
		EN_getlinkvalue(*ph, j, EN_DIAMETER, &diametre);
		EN_getlinkvalue(*ph, j, EN_LENGTH, &longueur);
		EN_getlinkvalue(*ph, j, EN_FLOW, &flow);
		G.arcs[i] = assignation_arc(type_epa, diametre, longueur, 0, flow, &G.sommets[noeud1-1], &G.sommets[noeud2-1]);
		G.arcs[i+1] = assignation_arc_oppose(&G.arcs[i]);
		G.sommets[noeud1-1].arcs[degrees[noeud1-1]] = assignation_arc_symmetrique(&G.arcs[i], &G.arcs[i+1], &G.sommets[noeud1-1]);
		G.sommets[noeud2-1].arcs[degrees[noeud2-1]] = assignation_arc_symmetrique(&G.arcs[i], &G.arcs[i+1], &G.sommets[noeud2-1]);
		degrees[noeud1-1] += 1;
		degrees[noeud2-1] += 1;
	}
	free(degrees);
	return G;
}


int main() {
    // 1. Noms des fichiers (Modifiez "mon_reseau.inp" selon votre vrai fichier)
    char* fichier_inp = "net3.inp";
    char* fichier_rpt = "rapport.rpt";
    char* fichier_bin = "";

    printf("=== 1. Initialisation d'EPANET ===\n");
    EN_Project mon_projet = init_inp_file(fichier_inp, fichier_rpt, fichier_bin);

    printf("=== 2. Calcul Hydraulique ===\n");
    // Indispensable : il faut lancer le calcul pour que les débits (Flow) soient calculés !
    int err_solve = EN_solveH(mon_projet);
    if (err_solve > 0) {
        printf("Alerte: Erreur lors du calcul hydraulique (Code %d)\n", err_solve);
    } else {
        printf("Calcul hydraulique reussi.\n");
    }

    printf("=== 3. Chargement du graphe ===\n");
    struct graph mon_reseau = chargement_graph(&mon_projet);

    printf("Graphe genere avec succes !\n");
    printf("-> %d sommets charges.\n", mon_reseau.nb_sommet);
    printf("-> %d arcs au total (soit %d paires opposees).\n", mon_reseau.nb_arcs, mon_reseau.nb_arcs / 2);

    // --- TEST D'AFFICHAGE ---
    if (mon_reseau.nb_sommet > 0) {
        printf("\n--- Test : Examen du Noeud 1 ---\n");
        printf("Type : %d (0=Source, 1=Jonction, etc.)\n", mon_reseau.sommets[0].type);
        printf("Elevation : %.2f m\n", mon_reseau.sommets[0].elevation);
        printf("Degre : %d arc(s) connecte(s)\n", mon_reseau.sommets[0].degree);

        if (mon_reseau.sommets[0].degree > 0) {
            printf("L'arc sortant de la premiere connexion a un debit de %.2f\n", 
                   mon_reseau.sommets[0].arcs[0].arc_sortant->flow);
        }
    }

    // === 4. Nettoyage de la mémoire ===
    printf("\n=== 4. Liberation de la memoire ===\n");
    
    // Nettoyage de votre structure Graphe
    for (int i = 0; i < mon_reseau.nb_sommet; i++) {
        free(mon_reseau.sommets[i].arcs);
    }
    free(mon_reseau.sommets);
    free(mon_reseau.arcs);

    // Fermeture et nettoyage d'EPANET
    EN_close(mon_projet);
    EN_deleteproject(mon_projet); 

    return 0;
}
