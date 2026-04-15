#include "stdlib.h"
#include "math.h"
#include "float.h"
#include "structure.h"
#include "epanet_parser.h"
#include "time.h"

#define MALOC_RANDOM_SOURCE_FAIL 41
#define MALOC_RANDOM_DESTINATION_FAIL 42
#define EPSILON 0.0

struct stack {
	struct stack *prev;
	struct sommet *sommet;
};

void fix_capacite_flow(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		if (reseau->arcs[i].diametre || reseau->arcs[i].longueur) {
			reseau->arcs[i].flow = 0.0;
			reseau->arcs[i].capacite = 3.1415 * pow((reseau->arcs[i].diametre*1000.0) / 2.0, 2) * reseau->arcs[i].longueur;
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
	reseau->sommets[reseau->nb_sommet-2] = assignation_sommet(SOURCE, degree_source, 0, 0, 0);
	reseau->sommets[reseau->nb_sommet-1] = assignation_sommet(DESTINATION, degree_destination, 0, 0, 0);
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

void ajout_capacite_random(struct graph* reseau, float proportion_demande, float proportion_source) {
	flotant random_value;
	srand(time(NULL));

	for (nbr i=0; i < reseau->sommet_source->degree; i++) {
		random_value = (((flotant) rand() / RAND_MAX) * 2) * proportion_source;
		reseau->sommet_source->arcs[i].arc_sortant->capacite = reseau->sommet_source->arcs->arc_sortant->destination->demande * random_value;
	}

	for (int i=0; i < reseau->sommet_destination->degree; i++) {
		random_value = (((flotant) rand() / RAND_MAX) * 2) * proportion_demande;
		reseau->sommet_destination->arcs[i].arc_entrant->capacite = (reseau->sommet_destination->arcs->arc_entrant->source->demande*-1) * random_value;
	}
}

void nullifier_flow(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs; i++) {
		reseau->arcs[i].flow = 0.0;
	};
}


flotant parcours_ff(struct stack *pile, flotant flow) {
	flotant flow_ajoutable, new_flot;
	if (pile->sommet->type == DESTINATION) {return DBL_MAX;};
	for (int i=0; i < pile->sommet->degree; i++) {
		flow_ajoutable = pile->sommet->arcs[i].arc_sortant->capacite - pile->sommet->arcs[i].arc_sortant->flow;
		if (flow_ajoutable > EPSILON && !pile->sommet->arcs[i].arc_sortant->destination->marque) {
			struct stack new_pile;
			flow_ajoutable = fmin(flow, flow_ajoutable);
			pile->sommet->arcs[i].arc_sortant->destination->marque = 1;
			new_pile.sommet = pile->sommet->arcs[i].arc_sortant->destination;
			new_pile.prev = pile;
			new_flot = parcours_ff(&new_pile, flow_ajoutable);
			if (new_flot != -1.0) {
				new_flot = fmin(new_flot, flow_ajoutable);
				pile->sommet->arcs[i].arc_sortant->flow += new_flot;
				return new_flot;
			}
		}
		flow_ajoutable = pile->sommet->arcs[i].arc_entrant->flow;
		if (flow_ajoutable > EPSILON && !pile->sommet->arcs[i].arc_entrant->source->marque) {
			struct stack new_pile;
			flow_ajoutable = fmin(flow, flow_ajoutable);
			pile->sommet->arcs[i].arc_entrant->source->marque = 1;
			new_pile.sommet = pile->sommet->arcs[i].arc_entrant->source;
			new_pile.prev = pile;
			new_flot = parcours_ff(&new_pile, flow_ajoutable);
			if (new_flot != -1.0) {
				new_flot = fmin(new_flot, flow_ajoutable);
				pile->sommet->arcs[i].arc_entrant->flow -= new_flot;
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
	struct stack pile;
	pile.prev = NULL;
	pile.sommet = reseau->sommet_source;
	flotant result = 1.0;
	while (result != -1.0) {
		marque_zero(reseau);
		pile.sommet->marque = 1;
		result = parcours_ff(&pile, DBL_MAX);
	};
}

