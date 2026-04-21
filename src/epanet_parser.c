#include "stdlib.h"
#include "epanet2.h"
#include "epanet2_2.h"
#include "epanet2_enums.h"
#include "structure.h"
#include "float.h"

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

flotant compute_satisfaction_rate_epanet(EN_Project* ph) {
	if (ph == NULL || *ph == NULL) return 0.0;

	int nb_nodes = 0;
	EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);
	if (nb_nodes <= 0) return 0.0;

	flotant total = 0.0;
	int valid = 0;

	for (int i = 1; i <= nb_nodes; i++) {
		double base = 0.0, delivered = 0.0;
		EN_getnodevalue(*ph, i, EN_BASEDEMAND, &base);
		EN_getnodevalue(*ph, i, EN_DEMANDFLOW, &delivered);

		if (base <= 0.0) continue; /* ignore negative or zero base demand */

		double s = 0.0;
		s = delivered / base;
		if (s < 0.0) s = 0.0;
		else if (s > 1.0) s = 1.0;

		total += (flotant) s;
		valid++;
	}

	if (valid == 0) return 0.0;
	return total / (flotant) valid;
}

struct graph chargement_graph(EN_Project* ph) {
	int nb_sommets, nb_arcs, out_model;
	flotant pression_min, pression_requise, exposant_pression, demande_multiplier;
	EN_getdemandmodel(*ph, &out_model, &pression_min, &pression_requise, &exposant_pression);
	EN_getoption(*ph, EN_DEMANDMULT, &demande_multiplier);
	EN_getcount(*ph, EN_NODECOUNT, &nb_sommets);
	EN_getcount(*ph, EN_LINKCOUNT, &nb_arcs);

	nbr degree_supp = 0;
	double demande_temp, demande_global = 0;
	int temp_type;
	for (int i=1; i <= nb_sommets ; i++) {
		EN_getnodevalue(*ph, i, EN_FULLDEMAND, &demande_temp);
		EN_getnodetype(*ph, i, &temp_type);
		if (demande_temp != 0 || temp_type == EN_RESERVOIR) {
			degree_supp++;
		};
		if (demande_temp > 0) {
			demande_global += demande_temp;
		};
	}
	struct graph G = assignation_graph(nb_sommets, nb_arcs*2, 2, degree_supp*2, pression_requise, exposant_pression, demande_global, demande_multiplier, compute_satisfaction_rate_epanet(ph));
	int *degrees = calloc(nb_sommets, sizeof(nbr));
	for (int j = 1 ; j <= nb_arcs ; j++) {
		int noeud1, noeud2;
		EN_getlinknodes(*ph, j, &noeud1,& noeud2);
		degrees[noeud1-1] += 1;
		degrees[noeud2-1] += 1;
	}

	for (int i = 1 ; i <= nb_sommets ; i++) {
		int type_node;
		double elevation, demande, pression;
		EN_getnodetype(*ph, i, &type_node);
		type_node = parser_type_sommet(type_node);
		EN_getnodevalue(*ph, i, EN_PRESSURE, &pression);
		EN_getnodevalue(*ph, i, EN_ELEVATION, &elevation);
		if (type_node == RESERVOIR) {
			demande = -DBL_MAX;
		} else {
			EN_getnodevalue(*ph, i, EN_DEMAND, &demande);
		}
		if (demande == 0) {
			G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 0, elevation, pression, demande);
		} else {
			G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 1, elevation, pression, demande);
		}
		degrees[i-1] = 0;
	}

	for (int j = 1, i = 0 ; j <= nb_arcs ; j++, i += 2) {
		int noeud1, noeud2, type_epa;
		double diametre, longueur, flow;
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

