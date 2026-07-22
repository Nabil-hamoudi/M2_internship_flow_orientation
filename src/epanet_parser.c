
#include "stdlib.h"
#include "epanet2_2.h"
#include "epanet2_enums.h"
#include "epanet_parser.h"
#include <math.h>

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
			return VALVE_PRV;
		case EN_PSV:
			return VALVE_PSV;
		case EN_PBV:
			return VALVE_PBV;
		case EN_FCV:
			return VALVE_FCV;
		case EN_TCV:
			return VALVE_TCV;
		case EN_GPV:
			return VALVE_GPV;
		case EN_PCV:
			return VALVE_PCV;
		default:
			return TUYAU;
	}
}

enum demand_model parser_type_model(int type_epanet) {
	switch (type_epanet) {
		case EN_DDA:
			return DDA;
		case EN_PDA:
			return PDA;
		default:
			return PDA;
	}
}

EN_Project create_project() {
	EN_Project ph;
	EN_createproject(&ph);
	return ph;
}

EN_Project init_inp_file(char* input, char* log, char* binairy) {
	EN_Project ph = create_project();
	int err = EN_open(ph, input, log, binairy);
	if (err > 0) exit(OPEN_EPANET_INP_ERROR);
	return ph;
}

long get_time(EN_Project* ph) {
	long duree_totale;
	EN_gettimeparam(*ph, EN_DURATION, &duree_totale); 
	return duree_totale;
}

int get_time_pattern(EN_Project* ph, int id_node, int patern_id, long t_ecoule) {
	long patStep, patStart;
	int patLength;

	EN_gettimeparam(*ph, EN_PATTERNSTEP, &patStep);
	EN_gettimeparam(*ph, EN_PATTERNSTART, &patStart); // Contient déjà l'offset de STARTTIME
	EN_getpatternlen(*ph, patern_id, &patLength);

    if (patLength == 0 || patStep == 0) return 1; // Sécurité

	long index_periode = (t_ecoule + patStart) / patStep; 

	return (int)((index_periode % patLength) + 1);
}

/*
* Revoir pour ajouter multiplicateur pattern
*/
void randomise_demande(EN_Project* ph) {
	nbr nb_nodes;
	double demand, demande_global = 0, demande_global_rand = 0;
	EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);
	for (nbr i = 1; i <= nb_nodes; i++) {
		EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);

		if (demand > 0.0) {
			demande_global += demand;
			EN_setnodevalue(*ph, i, EN_BASEDEMAND, demand * (((flotant) rand() / RAND_MAX) * 2));
			EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);
			demande_global_rand += demand;
		}
	}

	if (demande_global_rand > 0.0) {
		double ratio_normalisation = demande_global / demande_global_rand;
		for (nbr i = 1; i <= nb_nodes; i++) {
			EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);
			if (demand > 0.0) {
				demand = demand * ratio_normalisation;
				EN_setnodevalue(*ph, i, EN_BASEDEMAND, demand);
			}
		}
	}
}

void set_demande_un(EN_Project* ph) {
    nbr nb_nodes;
    EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);
    
    for (nbr i = 1; i <= nb_nodes; i++) {
        int num_demands = 0;
        EN_getnumdemands(*ph, i, &num_demands);

        for (int cat = 1; cat <= num_demands; cat++) {
            double base_demand = 0.0;
            EN_getbasedemand(*ph, i, cat, &base_demand);

            if (base_demand > 0.0) {
                EN_setbasedemand(*ph, i, cat, 1.0);
            }

            EN_setdemandpattern(*ph, i, cat, 0); 
        }
    }
}

void randomise_demande_normale(EN_Project* ph, double ecart_type) {
    nbr nb_nodes;
    double demand, demande_global = 0, demande_global_rand = 0;
    EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);
    
    for (nbr i = 1; i <= nb_nodes; i++) {
        EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);

        if (demand > 0.0) {
            demande_global += demand;
            
            double u1 = ((double) rand() / RAND_MAX);
            double u2 = ((double) rand() / RAND_MAX);
            if (u1 == 0.0) u1 = 1e-9;
            
            double z0 = sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
            
            double facteur = 1.0 + ecart_type * z0;
            if (facteur < 0.0) facteur = 0.0;
            
            EN_setnodevalue(*ph, i, EN_BASEDEMAND, demand * facteur);
            EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);
            demande_global_rand += demand;
        }
    }

    if (demande_global_rand > 0.0) {
        double ratio_normalisation = demande_global / demande_global_rand;
        for (nbr i = 1; i <= nb_nodes; i++) {
            EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);
            if (demand > 0.0) {
                demand = demand * ratio_normalisation;
                EN_setnodevalue(*ph, i, EN_BASEDEMAND, demand);
            }
        }
    }
}

void randomise_demande_exponentielle(EN_Project* ph, double ecart_type) {
    nbr nb_nodes;
    double demand, demande_global = 0, demande_global_rand = 0;
    EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);
    
    for (nbr i = 1; i <= nb_nodes; i++) {
        EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);

        if (demand > 0.0) {
            demande_global += demand;
            
            double u = ((double) rand() / RAND_MAX);
            if (u == 0.0) u = 1e-9;
            
            double x = -log(u);
            
            double facteur = 1.0 + ecart_type * (x - 1.0);
            if (facteur < 0.0) facteur = 0.0;
            
            EN_setnodevalue(*ph, i, EN_BASEDEMAND, demand * facteur);
            EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);
            demande_global_rand += demand;
        }
    }

    if (demande_global_rand > 0.0) {
        double ratio_normalisation = demande_global / demande_global_rand;
        for (nbr i = 1; i <= nb_nodes; i++) {
            EN_getnodevalue(*ph, i, EN_BASEDEMAND, &demand);
            if (demand > 0.0) {
                demand = demand * ratio_normalisation;
                EN_setnodevalue(*ph, i, EN_BASEDEMAND, demand);
            }
        }
    }
}

void set_time_step(EN_Project* ph, long pas_temp) {
    EN_settimeparam(*ph, EN_HYDSTEP, pas_temp);
}

void modif_multiplicateur(EN_Project* ph, double multiplicateur) {
	double mult;
	EN_getoption(*ph, EN_DEMANDMULT, &mult);
	EN_setoption(*ph, EN_DEMANDMULT, mult * multiplicateur);
}

void comput_flow(EN_Project* ph) {
	EN_solveH(*ph);
}

void fermeture_free_project(EN_Project* ph) {
	EN_close(*ph);
	EN_deleteproject(*ph);
}

void nullifier_demande(struct graph* reseau) {
	nbr nb_nodes = reseau->nb_sommet;
	for (nbr i = 0; i < nb_nodes; i++) {
		reseau->sommets[i].demande = 0.0;
	}
}

void get_epanet_fulldemande(EN_Project* ph, struct graph* reseau) {
	nbr nb_nodes;
	EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);

	double full_demande = 0.0, full_delivered = 0.0;
	double demande, delivered;

	double demande_multiplier = 1.0;
	EN_getoption(*ph, EN_DEMANDMULT, &demande_multiplier);
	long t_fin = get_time(ph);

	for (nbr i = 1; i <= nb_nodes; i++) {
		int num_demands = 0;
		EN_getnumdemands(*ph, i, &num_demands);
		
		demande = 0.0;
		for (int cat = 1; cat <= num_demands; cat++) {
			double base_demand = 0.0;
			int pattern_id = 0;
			double pattern_multiplier = 1.0;

			EN_getbasedemand(*ph, i, cat, &base_demand);
			EN_getdemandpattern(*ph, i, cat, &pattern_id);

			if (pattern_id > 0) {
				int pattern_stamp = get_time_pattern(ph, i, pattern_id, t_fin);
				EN_getpatternvalue(*ph, pattern_id, pattern_stamp, &pattern_multiplier);
			}

			demande += base_demand * demande_multiplier * pattern_multiplier;
		}

		if (demande > 0.0) {
			delivered = reseau->sommets[i-1].demande * reseau->sommets[i-1].satisfaction;
			
			full_delivered += delivered;
			full_demande += demande;

			reseau->sommets[i-1].satisfaction = delivered / demande;
			reseau->sommets[i-1].demande = demande;
		} else {
			reseau->sommets[i-1].satisfaction = 1.0;
			reseau->sommets[i-1].demande = 0.0;
		}
	}

	if (full_demande > 0.0) {	
		reseau->demande_global = full_demande;
		reseau->satifaisabilite = full_delivered / full_demande;
	} else {
		reseau->demande_global = 0.0;
		reseau->satifaisabilite = 1.0;
	}
}

void get_epanet_demande(EN_Project* ph, struct graph* reseau) {
	nullifier_demande(reseau);
	nbr nb_nodes;
	EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);

	double delivered;
	for (nbr i = 1; i <= nb_nodes; i++) {
		EN_getnodevalue(*ph, i, EN_DEMANDFLOW, &delivered);

		if (delivered > 0.0) {
			reseau->sommets[i-1].demande = delivered;
		}
	}
}

void compute_satisfaction_rate_epanet(EN_Project* ph, struct graph* reseau) {
	nbr nb_nodes;
	EN_getcount(*ph, EN_NODECOUNT, &nb_nodes);

	flotant total_demand = 0.0;
	flotant total_delivered = 0.0;
	double demand, delivered;

	double demande_multiplier = 1.0;
	EN_getoption(*ph, EN_DEMANDMULT, &demande_multiplier);
	long t_fin = get_time(ph);

	for (nbr i = 1; i <= nb_nodes; i++) {
		int num_demands = 0;
		EN_getnumdemands(*ph, i, &num_demands);
		demand = 0.0; 

		for (int cat = 1; cat <= num_demands; cat++) {
			double base_demand = 0.0;
			int pattern_id = 0;
			double pattern_multiplier = 1.0;

			EN_getbasedemand(*ph, i, cat, &base_demand);
			EN_getdemandpattern(*ph, i, cat, &pattern_id);

			if (pattern_id > 0) {
				int pattern_stamp = get_time_pattern(ph, i, pattern_id, t_fin);
				EN_getpatternvalue(*ph, pattern_id, pattern_stamp, &pattern_multiplier);
			}

			demand += base_demand * demande_multiplier * pattern_multiplier;
		}

		EN_getnodevalue(*ph, i, EN_DEMANDFLOW, &delivered);

		if (demand > 0.0) {
			reseau->sommets[i-1].satisfaction = delivered / demand;
			total_demand += demand;
			total_delivered += delivered;
		} else {
			reseau->sommets[i-1].satisfaction = 1.0;
		}
	}

	if (total_demand == 0.0) {
		reseau->satifaisabilite = 1.0;
	} else {
		reseau->satifaisabilite = total_delivered / total_demand;
	}
}

void set_random_seed(unsigned int seed) {
	srand(seed);
}

void nullifier_flow_epa(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs; i++) {
		reseau->arcs[i].flow = 0.0;
	};
}

void reget_epanet_flow(EN_Project* ph, struct graph* reseau) {
	nullifier_flow_epa(reseau);
	double flow;
	int noeud1, noeud2;
	for (nbr i=0, j=1; j <= reseau->nb_arcs / 2; j++, i+=2) {
		EN_getlinknodes(*ph, j, &noeud1, &noeud2);
		noeud1 -= 1;
		noeud2 -= 1;
		EN_getlinkvalue(*ph, j, EN_FLOW, &flow);
		if (flow < 0.0) {
			int noeud1temp = noeud2;
			noeud1 = noeud2;
			noeud2 = noeud1temp;
			flow = flow * -1;
		}
		if (reseau->arcs[i].source - reseau->sommets == noeud1) {
			reseau->arcs[i].flow = flow;
			reseau->arcs[i+1].flow = 0.0;
		} else {
			reseau->arcs[i+1].flow = flow;
			reseau->arcs[i].flow = 0.0;
		}
	}
}

void get_tank_max_flow_limits_from_levels(EN_Project* ph, int id_node, flotant* max_out_L_min, flotant* max_in_L_min) {
    int type_node;
    EN_getnodetype(*ph, id_node, &type_node);

    if (type_node != EN_TANK) {
        *max_out_L_min = 0.0;
        *max_in_L_min = 0.0;
        return;
    }

    double niveau_courant, niveau_min, niveau_max, diametre;
    
    EN_getnodevalue(*ph, id_node, EN_TANKLEVEL, &niveau_courant);
    EN_getnodevalue(*ph, id_node, EN_MINLEVEL, &niveau_min);
    EN_getnodevalue(*ph, id_node, EN_MAXLEVEL, &niveau_max);
    EN_getnodevalue(*ph, id_node, EN_TANKDIAM, &diametre);

    double surface = M_PI * ((diametre / 2.0) * (diametre / 2.0));

    double vol_courant = surface * niveau_courant;
    double vol_min = surface * niveau_min;
    double vol_max = surface * niveau_max;

    long pas_temp;
    EN_gettimeparam(*ph, EN_HYDSTEP, &pas_temp);

    if (pas_temp <= 0) {
        *max_out_L_min = 0.0;
        *max_in_L_min = 0.0;
        return;
    }

    *max_out_L_min = ((vol_courant - vol_min) * 1000.0) / ((double)pas_temp / 60.0);
    *max_in_L_min = ((vol_max - vol_courant) * 1000.0) / ((double)pas_temp / 60.0);
}

struct graph chargement_graph(EN_Project* ph) {
	int nb_sommets, nb_arcs, out_model;
	flotant pression_min, pression_requise, exposant_pression, demande_multiplier;
	EN_getdemandmodel(*ph, &out_model, &pression_min, &pression_requise, &exposant_pression);
	EN_getoption(*ph, EN_DEMANDMULT, &demande_multiplier);
	EN_getcount(*ph, EN_NODECOUNT, &nb_sommets);
	EN_getcount(*ph, EN_LINKCOUNT, &nb_arcs);
	long pas_temp_hydraulique = 3600;
	EN_gettimeparam(*ph, EN_HYDSTEP, &pas_temp_hydraulique);

	nbr degree_supp = 0;
	int temp_type;
	for (int i=1; i <= nb_sommets ; i++) {
		EN_getnodetype(*ph, i, &temp_type);
		
		int num_demands = 0;
		EN_getnumdemands(*ph, i, &num_demands);
		double total_base_demand = 0.0;
		
		for (int cat = 1; cat <= num_demands; cat++) {
			double base_demand = 0.0;
			EN_getbasedemand(*ph, i, cat, &base_demand);
			total_base_demand += base_demand;
		}

		if (total_base_demand != 0.0 || temp_type == EN_RESERVOIR) {
			degree_supp++;
		} else if (temp_type == EN_TANK) {
			degree_supp += 2;
		};
	}

	struct graph G = assignation_graph(out_model, nb_sommets, nb_arcs*2, 2, degree_supp*2, pression_min, pression_requise, exposant_pression, 0.0, demande_multiplier, 1.0, get_time(ph), pas_temp_hydraulique);
	int *degrees = calloc(nb_sommets, sizeof(nbr));
	for (int j = 1 ; j <= nb_arcs ; j++) {
		int noeud1, noeud2;
		EN_getlinknodes(*ph, j, &noeud1,& noeud2);
		degrees[noeud1-1] += 1;
		degrees[noeud2-1] += 1;
	}
	int type_node, pattern_stamp;
	double elevation, elevation_supp = 0.0, demande = 0.0, emmission = 0.0, pression, x, y, charge;
	for (int i = 1; i <= nb_sommets ; i++) {
		elevation_supp = 0.0, demande = 0.0, emmission = 0.0;
		
		EN_getnodetype(*ph, i, &type_node);
		type_node = parser_type_sommet(type_node);
		EN_getnodevalue(*ph, i, EN_PRESSURE, &pression);
		EN_getnodevalue(*ph, i, EN_ELEVATION, &elevation);
		charge = elevation;
		EN_getcoord(*ph, i, &x, &y);

		int num_demands = 0;
		EN_getnumdemands(*ph, i, &num_demands);

		for (int cat = 1; cat <= num_demands; cat++) {
			double base_demand = 0.0;
			int cat_pattern_id = 0;
			double pattern_multiplier = 1.0;

			EN_getbasedemand(*ph, i, cat, &base_demand);
			EN_getdemandpattern(*ph, i, cat, &cat_pattern_id);

			if (cat_pattern_id > 0) {
				pattern_stamp = get_time_pattern(ph, i, cat_pattern_id, G.temp);
				EN_getpatternvalue(*ph, cat_pattern_id, pattern_stamp, &pattern_multiplier);
			}

			demande += base_demand * G.demande_multiplier * pattern_multiplier;
		}

		if (demande == 0.0 && type_node != RESERVOIR && type_node != TANK) {
			G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 0, elevation, pression, charge, 0.0, 0.0, 0.0, x, y);
		} else if (type_node != TANK) {
			if (demande < 0.0 || type_node == RESERVOIR) {
				G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 1, elevation, pression, charge, 0.0, demande, emmission, x, y);
			} else {
				G.demande_global += demande;
				G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 1, elevation, pression, charge, 0.0, demande, emmission, x, y);
			}
		} else {
			get_tank_max_flow_limits_from_levels(ph, i, &emmission, &demande);
			EN_getnodevalue(*ph, i, EN_TANKLEVEL, &elevation_supp);
			G.sommets[i-1] = assignation_sommet(type_node, degrees[i-1], 2, elevation+elevation_supp, pression, charge, 0.0, demande, emmission, x, y);
		}
		degrees[i-1] = 0;
	}

	for (int j = 1, i = 0 ; j <= nb_arcs ; j++, i += 2) {
		int noeud1, noeud2, type_epa, ouvert;
		double diametre, longueur, flow, roughness, status;
		EN_getlinknodes(*ph, j, &noeud1, &noeud2);
		EN_getlinktype(*ph, j, &type_epa);
		type_epa = parser_type_arc(type_epa);
		EN_getlinkvalue(*ph, j, EN_DIAMETER, &diametre);
		EN_getlinkvalue(*ph, j, EN_LENGTH, &longueur);
		EN_getlinkvalue(*ph, j, EN_ROUGHNESS, &roughness);
		EN_getlinkvalue(*ph, j, EN_FLOW, &flow);
		EN_getlinkvalue(*ph, j, EN_INITSTATUS, &status);
		if (status == EN_OPEN) {
			ouvert = 1;
		} else {
			ouvert = 0;
		}
		G.arcs[i] = assignation_arc(type_epa, diametre, longueur, roughness, 0.0, flow, &G.sommets[noeud1-1], &G.sommets[noeud2-1], ouvert);
		G.arcs[i+1] = assignation_arc_oppose(&G.arcs[i]);
		G.sommets[noeud1-1].arcs[degrees[noeud1-1]] = assignation_arc_symmetrique(&G.arcs[i], &G.arcs[i+1], &G.sommets[noeud1-1]);
		G.sommets[noeud2-1].arcs[degrees[noeud2-1]] = assignation_arc_symmetrique(&G.arcs[i], &G.arcs[i+1], &G.sommets[noeud2-1]);
		degrees[noeud1-1] += 1;
		degrees[noeud2-1] += 1;
	}

	compute_satisfaction_rate_epanet(ph, &G);

	free(degrees);
	return G;
}


