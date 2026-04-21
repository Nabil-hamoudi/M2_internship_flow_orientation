#include "stdlib.h"
#include "math.h"
#include "float.h"
#include "structure.h"
#include "epanet_parser.h"
#include "time.h"

#define MALOC_RANDOM_SOURCE_FAIL 41
#define MALOC_RANDOM_DESTINATION_FAIL 42
#define EPSILON 0.0

void fix_capacite_flow(struct graph* reseau) {
for (int i=0; i < reseau->nb_arcs ; i++) {
	struct sommet* source = reseau->arcs[i].source;
	struct sommet* destination = reseau->arcs[i].destination;
	if (source->type != SOURCE && destination->type != DESTINATION) {
		if (source->type != DESTINATION && destination->type != SOURCE) {
			// capacité pour 2m/s en litre par minute
			reseau->arcs[i].capacite =  (M_PI * (pow(reseau->arcs[i].diametre, 2.0)/4) * 120.0) * 1000;
				if (source->type == RESERVOIR) {
					// capacité max pour 3 m/s en litre par minute pour reservoir
					reseau->arcs[i].capacite =  (M_PI * (pow(reseau->arcs[i].diametre, 2.0)/4) * 180.0) * 1000;
				}
			}
		}
	}
}

void ajout_source_destination(struct graph* reseau) {
	nbr degree_source = 0, degree_destination = 0;
	for (int i=0; i < reseau->nb_sommet ; i++) {
		if (reseau->sommets[i].demande > 0) {
			degree_destination++;
		} else if (reseau->sommets[i].demande < 0) {
			degree_source++;
		}
	}
	reseau->nb_sommet += 2;

	// revoir aussi car elevation etc
	reseau->sommets[reseau->nb_sommet-2] = assignation_sommet(SOURCE, degree_source, 0, 0, 0, 0);
	reseau->sommets[reseau->nb_sommet-1] = assignation_sommet(DESTINATION, degree_destination, 0, 0, 0, 0);
	reseau->sommet_source = &reseau->sommets[reseau->nb_sommet-2];
	reseau->sommet_destination = &reseau->sommets[reseau->nb_sommet-1];
	nbr lien_source = 0, lien_destination = 0;
	for (int i=0; i < reseau->nb_sommet ; i++) {
		if (reseau->sommets[i].demande < 0) {
			reseau->nb_arcs += 2;
			reseau->arcs[reseau->nb_arcs-2] = assignation_arc(TUYAU, 0, 0, 0, 0, reseau->sommet_source, &reseau->sommets[i]);
			reseau->arcs[reseau->nb_arcs-1] = assignation_arc_oppose(&reseau->arcs[reseau->nb_arcs-2]);
			reseau->sommet_source->arcs[lien_source] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], reseau->sommet_source);
			lien_source++;
			reseau->sommets[i].degree++;
			reseau->sommets[i].arcs[reseau->sommets[i].degree-1] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], &reseau->sommets[i]);
		} else if (reseau->sommets[i].demande > 0) {
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
		double capacite = reseau->demande_global / reseau->sommet_source->degree;
		reseau->sommet_source->arcs[i].arc_sortant->capacite = capacite * proportion_source;
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
	srand(time(NULL));
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

flotant compute_satisfaction_rate(struct graph* reseau) {
	if (reseau == NULL || reseau->sommet_destination == NULL) return 0.0;

	nbr deg = reseau->sommet_destination->degree;
	if (deg == 0) return 0.0;

	flotant total_satisfaction = 0.0;

	for (int i = 0; i < deg; i++) {
		struct arc *a = reseau->sommet_destination->arcs[i].arc_entrant;
		if (a == NULL) { continue; }
		flotant cap = a->capacite;
		flotant flow = a->flow;

		flotant s = 0.0;
		if (cap > 0.0) {
			s = flow / cap;
			if (s < 0.0) s = 0.0;
			else if (s > 1.0) s = 1.0;
		}
		total_satisfaction += s;
	}

	return total_satisfaction / (flotant) deg;
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
	reseau->satifaisabilite = compute_satisfaction_rate(reseau);
}


