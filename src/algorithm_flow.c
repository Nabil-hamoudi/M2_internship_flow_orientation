#include "stdio.h"
#include "stdlib.h"
#include "math.h"
#include "structure.h"
#include "epanet_parser.h"

#define MALOC_RANDOM_SOURCE_FAIL 41
#define MALOC_RANDOM_DESTINATION_FAIL 42

void fix_capacite_flow(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		reseau->arcs[i].flow = 0.0;
		reseau->arcs[i].capacite = 3.1415 * pow((reseau->arcs[i].diametre*1000) / 2.0, 2) * reseau->arcs[i].longueur;
	}
}

void ajout_source_destination(struct graph* reseau) {
	struct sommet source, destination;
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
	flotant* random_source = malloc(reseau->sommet_source->degree * sizeof(flotant));
	if (random_source == NULL) exit(MALOC_RANDOM_SOURCE_FAIL);
	flotant* random_demande = malloc(reseau->sommet_destination->degree * sizeof(flotant));
	if (random_source == NULL) exit(MALOC_RANDOM_DESTINATION_FAIL);
	for (int i=0; i < reseau->nb_sommet; i++) {
		
	}
}

