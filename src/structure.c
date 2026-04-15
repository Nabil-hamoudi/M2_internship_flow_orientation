# include "stdio.h"
# include "stdlib.h"
# include "structure.h"

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs, nbr sommet_supplementaire, nbr arcs_supplementaire) {
	struct graph G;
	G.nb_sommet = nb_sommet;
	G.nb_arcs = nb_arcs;
	G.sommets = malloc((G.nb_sommet+sommet_supplementaire) * sizeof(struct sommet));
	if (G.sommets == NULL && G.nb_sommet > 0) exit(ALLOCATION_FAIL_GRAPH);
	G.arcs = malloc((G.nb_arcs+arcs_supplementaire) * sizeof(struct arc));
	if (G.arcs == NULL && G.nb_arcs > 0) exit(ALLOCATION_FAIL_GRAPH);
	return G;
}

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree, nbr degree_ajouter, flotant elevation, flotant demande) {
	struct sommet S;
	S.type = type_s;
	S.elevation = elevation;
	S.degree = degree;
	S.demande = demande;
	S.arcs = malloc((S.degree + degree_ajouter) * sizeof(struct arc_symmetrique));
	if (S.arcs == NULL && S.degree > 0) exit(ALLOCATION_FAIL_SOMMETS);
	return S;
}

struct arc assignation_arc(enum type_arcs type_a, flotant diametre, flotant longueur, flotant capacite, flotant flow, struct sommet *source, struct sommet *destination) {
	struct arc A;
	A.type = type_a;
	A.diametre = diametre;
	A.longueur = longueur;
	A.capacite = capacite;
	if (flow < 0.0) {
		struct sommet* sourcetemp = source;
		source = destination;
		destination = sourcetemp;
		flow = flow * -1;
	}
	A.flow = flow;
	A.source = source;
	A.destination = destination;
	return A;
}

struct arc assignation_arc_oppose(struct arc* B) {
	enum type_arcs type_a = B->type;
	flotant diametre = B->diametre;
	flotant longueur = B->longueur;
	flotant capacite = B->capacite;
	flotant flow = 0;
	struct sommet *source = B->destination;
	struct sommet *destination = B->source;
	return assignation_arc(type_a, diametre, longueur, capacite, flow, source, destination);
}

struct arc_symmetrique assignation_arc_symmetrique(struct arc* A, struct arc* B, struct sommet* source) {
	struct arc_symmetrique AB;
	if (A->source == source) {
		AB.arc_sortant = A;
		AB.arc_entrant = B;
	} else {
		AB.arc_sortant = B;
		AB.arc_entrant = A;
	};
	return AB;
}


