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

void modif_multiplicateur(EN_Project* ph, float multiplicateur) {
	double mult;
	EN_getoption(*ph, EN_DEMANDMULT, &mult);
	EN_setoption(*ph, EN_DEMANDMULT, mult * multiplicateur);
}

long get_time(EN_Project* ph) {
	long duree_totale, heure_debut;
	ENgettimeparam(EN_DURATION, &duree_totale); 
	ENgettimeparam(EN_STARTTIME, &heure_debut); 

	return heure_debut + duree_totale;
}

void comput_flow(EN_Project* ph) {
	EN_solveH(*ph);
}

flotant compute_satisfaction_rate_epanet(EN_Project* ph) {
	nbr nb_nodes;
	EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);

	flotant total_demand = 0.0;
	flotant total_delivered = 0.0;

	flotant demand, delivered;
	for (nbr i = 1; i <= nb_nodes; i++) {
		EN_getnodevalue(*ph, i, EN_FULLDEMAND, &demand);
		EN_getnodevalue(*ph, i, EN_DEMANDFLOW, &delivered);

		if (demand > 0.0) {
			total_demand += demand;
			total_delivered += delivered;
		}
	}

	if (total_demand == 0.0) {
        return 1.0; 
    }

	return total_delivered / total_demand;
}

int get_time_pattern(EN_Project* ph, int id_node, int patern_id, float temp) {
	long patStep, patStart;
	int patLength;

	EN_gettimeparam(*ph, EN_PATTERNSTEP, &patStep);   // Ex: 3600 s
	EN_gettimeparam(*ph, EN_PATTERNSTART, &patStart);
	EN_getpatternlen(*ph, patern_id, &patLength);

	long index_periode = (temp + patStart) / patStep; 

	return (index_periode % patLength) + 1;
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
		EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demande_temp);
		EN_getnodetype(*ph, i, &temp_type);
		if (demande_temp != 0 || temp_type == EN_RESERVOIR) {
			degree_supp++;
		};
		if (demande_temp > 0) {
			demande_global += demande_temp;
		};
	}
	struct graph G = assignation_graph(nb_sommets, nb_arcs*2, 2, degree_supp*2, pression_requise, exposant_pression, demande_global, demande_multiplier, compute_satisfaction_rate_epanet(ph), get_time(ph));
	int *degrees = calloc(nb_sommets, sizeof(nbr));
	for (int j = 1 ; j <= nb_arcs ; j++) {
		int noeud1, noeud2;
		EN_getlinknodes(*ph, j, &noeud1,& noeud2);
		degrees[noeud1-1] += 1;
		degrees[noeud2-1] += 1;
	}

	for (int i = 1 ; i <= nb_sommets ; i++) {
		int type_node, pattern_id, pattern_stamp;
		double elevation, demande, pression, multiplier = 1.0;
		
		EN_getnodetype(*ph, i, &type_node);
		type_node = parser_type_sommet(type_node);
		EN_getnodevalue(*ph, i, EN_PRESSURE, &pression);
		EN_getnodevalue(*ph, i, EN_ELEVATION, &elevation);
		// a revoir categorie de demande
		EN_getdemandpattern(*ph, i, 1, &pattern_id);
		if (pattern_id > 0.0) {
			pattern_stamp = get_time_pattern(ph, i, pattern_id, G.temp);
			EN_getpatternvalue(*ph, pattern_id, pattern_stamp, &multiplier);
		}
		EN_getnodevalue(*ph, i, EN_DEMAND, &demande);
		if (demande == 0 && type_node != EN_RESERVOIR) {
			G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 0, elevation, pression, demande * G.demande_multiplier * multiplier);
		} else {
			G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 1, elevation, pression, demande * G.demande_multiplier * multiplier);
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

