#include "stdlib.h"
#include "math.h"
#include "float.h"
#include "structure.h"
#include "epanet_parser.h"

#define MALOC_RANDOM_SOURCE_FAIL 41
#define MALOC_RANDOM_DESTINATION_FAIL 42
#define EPSILON 0.0

void fix_capacite_flow(struct graph* reseau, float vitesse_reservoir, float vitesse_arcs) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			if (source->type == RESERVOIR) {
				// capacité max pour 3 m/s en litre par minute pour reservoir
				reseau->arcs[i].capacite =  (M_PI * (pow((reseau->arcs[i].diametre/1000), 2.0)/4.0) * (60.0 * vitesse_reservoir)) * 1000.0;
			} else if (destination->type != RESERVOIR) {
				// capacité pour 2m/s en litre par minute
				reseau->arcs[i].capacite =  (M_PI * (pow((reseau->arcs[i].diametre/1000), 2.0)/4.0) * (60.0 * vitesse_arcs)) * 1000.0;
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

	reseau->sommets[reseau->nb_sommet-2] = assignation_sommet(SOURCE, degree_source, 0, 0, 0, 0);
	reseau->sommets[reseau->nb_sommet-1] = assignation_sommet(DESTINATION, degree_destination, 0, 0, 0, 0);
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
	for (int i=0; i < reseau->sommet_destination->degree; i++) {
		reseau->sommet_destination->arcs[i].arc_entrant->capacite = (reseau->sommet_destination->arcs[i].arc_entrant->source->demande) * proportion_demande;
		reseau->sommet_destination->arcs[i].arc_sortant->capacite = 0.0;
	}
}

void ajout_capacite_random(struct graph* reseau, float proportion_demande, float proportion_source) {
	proportion_demande = (((flotant) rand() / RAND_MAX) * 2) * proportion_demande;
	ajout_capacite_demande(reseau, proportion_demande);
	proportion_source = (((flotant) rand() / RAND_MAX) * 2) * proportion_source;
	ajout_capacite_source(reseau, proportion_source);
}



void nullifier_flow(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs; i++) {
		reseau->arcs[i].flow = 0.0;
	};
}


flotant parcours_ff(struct sommet *sommet, flotant flow) {
	flotant flow_ajoutable, new_flot;
	if (sommet->type == DESTINATION) {return flow;};
	for (int i=0; i < sommet->degree; i++) {
		flow_ajoutable = sommet->arcs[i].arc_sortant->capacite - sommet->arcs[i].arc_sortant->flow;
		if (flow_ajoutable > EPSILON && !sommet->arcs[i].arc_sortant->destination->marque) {
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
		if (flow_ajoutable > EPSILON && !sommet->arcs[i].arc_entrant->source->marque) {
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


