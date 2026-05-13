#include "stdio.h"
#include "stdlib.h"
#include "math.h"
#include "float.h"
#include "structure.h"
#include "epanet_parser.h"

struct file {
	struct sommet* sommet;
	struct arc* arc;
	int inverse;
	flotant flow_ajoutable;
	struct file* precedent;
	struct file* suivant;
};


void print_graph_details(struct graph *G, flotant v_res, flotant v_arc) {
	if (G == NULL || G->sommets == NULL) {
		printf("Erreur : Graphe non initialisé.\n");
		return;
	}

	printf("\n=====================================================================================\n");
	printf("                  ÉTAT DU RÉSEAU (Temps: %ld s)                         \n", G->temp);
	printf("=====================================================================================\n");
	printf("Sommets : %d | Arcs : %d\n", G->nb_sommet, G->nb_arcs);
	printf("Demande Globale : %.2f | Satisfaisabilité : %.2f%%\n", 
		G->demande_global, G->satifaisabilite * 100);
	printf("Pression requise : %.2f | Exposant : %.2f\n", 
		G->pression_requise, G->exposant_pression);
	printf("Multiplicateur global de demande : %.4f\n", G->demande_multiplier);
	printf("Vitesse max Reservoir : %.4f m/min | arcs : %.4f m/min\n", v_res*60, v_arc*60);
	printf("-------------------------------------------------------------------------------------\n\n");

	printf("--- LISTE DES SOMMETS ---\n");
	printf("%-5s | %-12s | %-8s | %-12s | %-8s | %-5s\n", 
		"ID", "Type", "Elev.", "Demande", "Press.", "Degré");
	for (int i = 0; i < G->nb_sommet; i++) {
		struct sommet *s = &G->sommets[i];
		printf("%-5d | %-12s | %-8.2f | %-12.4f | %-8.2f | %-5d\n",
		i + 1, get_nom_type_sommet(s->type), s->elevation, s->demande, s->pression, s->degree);
	}

	// Affichage des Arcs avec la colonne de Vitesse d'entrée
	printf("\n--- LISTE DES ARCS ---\n");
	printf("%-5s | %-8s | %-15s | %-8s | %-8s | %-12s | %-12s | %-10s\n", 
		"ID", "Type", "Connexion", "Diam.", "Long.", "Capacité", "Flow", "Vit.In(m/min)");

	for (int i = 0; i < G->nb_arcs; i++) {
		struct arc *a = &G->arcs[i];
		int idx_src = (int)(a->source - G->sommets) + 1;
		int idx_dst = (int)(a->destination - G->sommets) + 1;

		// On récupère la vitesse directement depuis les arguments de la fonction
		// selon la même logique que dans fix_capacite_flow
		flotant v_input = 0.0;
		if (a->diametre > 0.0) {
			v_input = compute_velocity(G, i);
		}

	printf("%-5d | %-8s | %3d -> %-9d | %-8.1f | %-8.1f | %-12.4f | %-12.4f | %-10.2f\n",
		i + 1,
		get_nom_type_arc(a->type),
		idx_src, idx_dst,
		a->diametre,
		a->longueur,
		a->capacite,
		a->flow,
		v_input); // Affichage direct du paramètre
	}
	printf("=====================================================================================\n\n");
}

void fix_capacite_flow(struct graph* reseau, float vitesse_reservoir, float vitesse_arcs) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			if (source->type == RESERVOIR) {
				// capacité max pour 3 m/s en litre par minute pour reservoir
				reseau->arcs[i].capacite =  (M_PI * (((reseau->arcs[i].diametre/1000) * (reseau->arcs[i].diametre/1000))/4.0) * (60.0 * vitesse_reservoir)) * 1000.0;
			} else if (destination->type != RESERVOIR) {
				// capacité pour 2m/s en litre par minute
				reseau->arcs[i].capacite =  (M_PI * (((reseau->arcs[i].diametre/1000) * (reseau->arcs[i].diametre/1000))/4.0) * (60.0 * vitesse_arcs)) * 1000.0;
			}
		}
	}
}

void fix_capacite_flow_oriente(struct graph* reseau, float vitesse_reservoir, float vitesse_arcs) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			if (reseau->arcs[i].flow > 0.0) {
				if (source->type == RESERVOIR) {
					// capacité max pour 3 m/s en litre par minute pour reservoir
					reseau->arcs[i].capacite =  (M_PI * (pow((reseau->arcs[i].diametre/1000), 2.0)/4.0) * (60.0 * vitesse_reservoir)) * 1000.0;
				} else if (destination->type != RESERVOIR) {
					// capacité pour 2m/s en litre par minute
					reseau->arcs[i].capacite =  (M_PI * (pow((reseau->arcs[i].diametre/1000), 2.0)/4.0) * (60.0 * vitesse_arcs)) * 1000.0;
				}
			} else {
				reseau->arcs[i].capacite = 0.0;
			}
		}
	}
}


void ajout_source_destination(struct graph* reseau) {
	nbr degree_source = 0, degree_destination = 0;
	for (int i=0; i < reseau->nb_sommet ; i++) {
		if (reseau->sommets[i].demande > 0) {
			degree_destination++;
		} else if (reseau->sommets[i].type == RESERVOIR ||reseau->sommets[i].demande < 0.0) {
			degree_source++;
		}
	}
	reseau->nb_sommet += 2;

	reseau->sommets[reseau->nb_sommet-2] = assignation_sommet(SOURCE, degree_source, 0, 0, 0, 0, 0, 0);
	reseau->sommets[reseau->nb_sommet-1] = assignation_sommet(DESTINATION, degree_destination, 0, 0, 0, 0, 0, 0);
	reseau->sommet_source = &reseau->sommets[reseau->nb_sommet-2];
	reseau->sommet_destination = &reseau->sommets[reseau->nb_sommet-1];
	nbr lien_source = 0, lien_destination = 0;
	for (int i=0; i < reseau->nb_sommet ; i++) {
		if (reseau->sommets[i].type == RESERVOIR || reseau->sommets[i].demande < 0.0) {
			reseau->nb_arcs += 2;
			reseau->arcs[reseau->nb_arcs-2] = assignation_arc(TUYAU, 0.0, 0.0, 0.0, 0.0, reseau->sommet_source, &reseau->sommets[i]);
			reseau->arcs[reseau->nb_arcs-1] = assignation_arc_oppose(&reseau->arcs[reseau->nb_arcs-2]);
			reseau->sommet_source->arcs[lien_source] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], reseau->sommet_source);
			lien_source++;
			reseau->sommets[i].degree++;
			reseau->sommets[i].arcs[reseau->sommets[i].degree-1] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], &reseau->sommets[i]);
		} else if (reseau->sommets[i].demande > 0.0) {
			reseau->nb_arcs += 2;
			reseau->arcs[reseau->nb_arcs-2] = assignation_arc(TUYAU, 0, 0, 0, 0, &reseau->sommets[i], reseau->sommet_destination);
			reseau->arcs[reseau->nb_arcs-1] = assignation_arc_oppose(&reseau->arcs[reseau->nb_arcs-2]);
			reseau->sommet_destination->arcs[lien_destination] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], reseau->sommet_destination);
			lien_destination++;
			reseau->sommets[i].degree++;
			reseau->sommets[i].arcs[reseau->sommets[i].degree-1] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], &reseau->sommets[i]);}
	}
}

void ajout_capacite_source(struct graph* reseau, float proportion_source) {
	for (int i=0; i < reseau->sommet_source->degree; i++) {
		reseau->sommet_source->arcs[i].arc_sortant->capacite = reseau->demande_global * proportion_source;
		reseau->sommet_source->arcs[i].arc_entrant->capacite = 0.0;
	}

}

void ajout_capacite_demande(struct graph* reseau, float proportion_demande) {
	reseau->demande_global = 0.0;
	for (int i=0; i < reseau->sommet_destination->degree; i++) {
		reseau->demande_global += (reseau->sommet_destination->arcs[i].arc_entrant->source->demande) * proportion_demande;
		reseau->sommet_destination->arcs[i].arc_entrant->capacite = (reseau->sommet_destination->arcs[i].arc_entrant->source->demande) * proportion_demande;
		reseau->sommet_destination->arcs[i].arc_sortant->capacite = 0.0;
	}
}

void nullifier_flow(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs; i++) {
		reseau->arcs[i].flow = 0.0;
	};
}


flotant parcours_ff(struct sommet *sommet, flotant flow) {
	flotant flow_ajoutable, new_flot;
	flotant epsilon = 0.0;
	if (sommet->type == DESTINATION) {return flow;};
	for (int i=0; i < sommet->degree; i++) {
		flow_ajoutable = sommet->arcs[i].arc_sortant->capacite - sommet->arcs[i].arc_sortant->flow;
		if (flow_ajoutable > epsilon && !sommet->arcs[i].arc_sortant->destination->marque) {
			struct sommet* new_sommet;
			flow_ajoutable = fmin(flow, flow_ajoutable);
			sommet->arcs[i].arc_sortant->destination->marque = 1;
			new_sommet = sommet->arcs[i].arc_sortant->destination;
			new_flot = parcours_ff(new_sommet, flow_ajoutable);
			if (new_flot != -1.0) {
				sommet->arcs[i].arc_sortant->flow += new_flot;
				return new_flot;
			}
		}
		flow_ajoutable = sommet->arcs[i].arc_entrant->flow;
		if (flow_ajoutable > epsilon && !sommet->arcs[i].arc_entrant->source->marque) {
			struct sommet* new_sommet;
			flow_ajoutable = fmin(flow, flow_ajoutable);
			sommet->arcs[i].arc_entrant->source->marque = 1;
			new_sommet = sommet->arcs[i].arc_entrant->source;
			new_flot = parcours_ff(new_sommet, flow_ajoutable);
			if (new_flot != -1.0) {
				sommet->arcs[i].arc_entrant->flow -= new_flot;
				return new_flot;
			}
		}

	}
	return -1.0;
}

void marque_zero(struct graph* reseau) {
	for (int i=0; i<reseau->nb_sommet; i++) {
		reseau->sommets[i].marque = 0;
	}
}

void compute_flow_ford_fukerson(struct graph* reseau) {
	struct sommet* sommet = reseau->sommet_source;
	flotant result = 1.0;
	while (result != -1.0) {
		marque_zero(reseau);
		sommet->marque = 1;
		result = parcours_ff(sommet, DBL_MAX);
	};
	compute_satisfaction_rate(reseau);
}

flotant parcours_ek(struct file* file, struct file** end_file) {
	flotant flow_ajoutable;
	flotant epsilon = 0.0;
	struct sommet* sommet = file->sommet;
	flotant flow = file->flow_ajoutable;
	if (sommet->type == DESTINATION) {return flow;}

	for (int i=0; i < sommet->degree; i++) {
		flow_ajoutable = sommet->arcs[i].arc_sortant->capacite - sommet->arcs[i].arc_sortant->flow;
		if (flow_ajoutable > epsilon && !sommet->arcs[i].arc_sortant->destination->marque) {
			flow_ajoutable = fmin(flow, flow_ajoutable);
			sommet->arcs[i].arc_sortant->destination->marque = 1;
			struct file* sommet_suivant = malloc(sizeof(struct file));
			sommet_suivant->sommet = sommet->arcs[i].arc_sortant->destination;
			sommet_suivant->flow_ajoutable = flow_ajoutable;
			sommet_suivant->arc = sommet->arcs[i].arc_sortant;
			sommet_suivant->inverse = 1;
			sommet_suivant->precedent = file;
			sommet_suivant->suivant = NULL;
			(*end_file)->suivant = sommet_suivant;
			*end_file = sommet_suivant;
		}
		flow_ajoutable = sommet->arcs[i].arc_entrant->flow;
		if (flow_ajoutable > epsilon && !sommet->arcs[i].arc_entrant->source->marque) {
			flow_ajoutable = fmin(flow, flow_ajoutable);
			sommet->arcs[i].arc_entrant->source->marque = 1;
			struct file* sommet_suivant = malloc(sizeof(struct file));
			sommet_suivant->sommet = sommet->arcs[i].arc_entrant->source;
			sommet_suivant->flow_ajoutable = flow_ajoutable;
			sommet_suivant->arc = sommet->arcs[i].arc_entrant;
			sommet_suivant->inverse = -1;
			sommet_suivant->precedent = file;
			sommet_suivant->suivant = NULL;
			(*end_file)->suivant = sommet_suivant;
			(*end_file) = sommet_suivant;
		}
	}

	return -1.0;
}

void compute_flow_edmonds_karp(struct graph* reseau) {
	flotant new_flot;
	do {
		struct file* file = malloc(sizeof(struct file));
		struct file* end = file;
		struct file** end_file = &end;
		file->sommet = reseau->sommet_source;
		file->flow_ajoutable = DBL_MAX;
		file->precedent = NULL;
		file->suivant = NULL;
		reseau->sommet_source->marque = 1;
		new_flot = parcours_ek(file, end_file);
		struct file* current = file;
		struct file* final = file;
		struct file* tmp;
		while (current->suivant != NULL && new_flot == -1.0) {
			current = current->suivant;
			new_flot = parcours_ek(current, end_file);
			if (new_flot != -1.0) {
				final = current;
				break;
			}
		}
		if (new_flot != -1.0) {
			while (1) {
				if (final->precedent == NULL) { break; }
				final->arc->flow += new_flot * final->inverse;
				final = final->precedent;
			}
		}
		current = file;
		while (current != NULL) {
			tmp = current->suivant;
			free(current);
			current = tmp;
		}
		marque_zero(reseau);
	} while (new_flot != -1.0);
	compute_satisfaction_rate(reseau);
}
