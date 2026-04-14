# include "stdio.h"
# include "stdlib.h"
# include "structure.h"

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs) {
	struct graph G;
	G.nb_sommet = nb_sommet;
	G.nb_arcs = nb_arcs;
	G.sommets = malloc(G.nb_sommet * sizeof(struct sommet));
	if (G.sommets == NULL && G.nb_sommet > 0) exit(ALLOCATION_FAIL_GRAPH);
	G.arcs = malloc(G.nb_arcs * sizeof(struct arc));
	if (G.arcs == NULL && G.nb_arcs > 0) exit(ALLOCATION_FAIL_GRAPH);
	return G;
}

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree, flotant elevation) {
	struct sommet S;
	S.type = type_s;
	S.elevation = elevation;
	S.degree = degree;
	S.arcs = malloc((S.degree) * sizeof(struct arc_symmetrique));
	if (S.arcs == NULL && S.degree > 0) exit(ALLOCATION_FAIL_SOMMETS);
	return S;
}

struct arc assignation_arc(enum type_arcs type_a, flotant diametre, flotant longueur, flotant flow, struct sommet *source, struct sommet *destination) {
	struct arc A;
	A.type = type_a;
	A.diametre = diametre;
	A.longueur = longueur;
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
	flotant flow = 0;
	struct sommet *source = B->destination;
	struct sommet *destination = B->source;
	return assignation_arc(type_a, diametre, longueur, flow, source, destination);
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

int main() {
	struct graph mon_reseau = assignation_graph(2, 2);

	mon_reseau.sommets[0] = assignation_sommet(SOURCE, 1, 150.5);
	mon_reseau.sommets[1] = assignation_sommet(DESTINATION, 1, 100.0);

	mon_reseau.arcs[0] = assignation_arc(TUYAU, 300.0, 1500.0, 12.0, &mon_reseau.sommets[0], &mon_reseau.sommets[1]);
	mon_reseau.arcs[1] = assignation_arc_oppose(&mon_reseau.arcs[0]);

	mon_reseau.sommets[0].arcs[0] = assignation_arc_symmetrique(&mon_reseau.arcs[1], &mon_reseau.arcs[0], &mon_reseau.sommets[0]);
	mon_reseau.sommets[1].arcs[0] = assignation_arc_symmetrique(&mon_reseau.arcs[1], &mon_reseau.arcs[0], &mon_reseau.sommets[0]);	

	printf("=== VERIFICATION DU RESEAU ===\n");
	printf("Graphe global : %d sommets, %d arcs au total.\n\n", mon_reseau.nb_sommet, mon_reseau.nb_arcs);

	for (int i = 0; i < mon_reseau.nb_sommet; i++) {
		printf("-> Sommet [%d] :\n", i);
		printf("   Type : %d (0=SOURCE, 1=DESTINATION, 2=RESERVOIR)\n", mon_reseau.sommets[i].type);
		printf("   Elevation : %.2f m\n", mon_reseau.sommets[i].elevation);

		for (int j = 0; j < mon_reseau.sommets[i].degree; j++) {
			struct arc* arc_sortant = mon_reseau.sommets[i].arcs[j].arc_sortant;
			struct arc* arc_entrant = mon_reseau.sommets[i].arcs[j].arc_entrant;
			printf("   ||--- Arc %d sortant ---\n", j);
			printf("   || Source : %p \n", arc_sortant->source);
			printf("   || destination : %p \n", arc_sortant->destination);
			printf("   || Type : %d (0=TUYAU, 1=POMPE, 2=VALVE)\n", arc_sortant->type);
			printf("   || Diametre : %.2f mm, Longueur : %.2f m\n", arc_sortant->diametre, arc_sortant->longueur);

			printf("   || -----> Connecte a un sommet d'elevation : %.2f m\n", 
			arc_sortant->destination->elevation);
			printf("\n");
			printf("   ||--- Arc %d entrant ---\n", j);
			printf("   || Type : %d (0=TUYAU, 1=POMPE, 2=VALVE)\n", arc_entrant->type);
			printf("   || Source : %p \n", arc_entrant->source);
			printf("   || destination : %p \n", arc_entrant->destination);
			printf("   || Diametre : %.2f mm, Longueur : %.2f m\n", arc_entrant->diametre, arc_entrant->longueur);

			printf("   || -----> Connecte a un sommet d'elevation : %.2f m\n", 
			arc_sortant->destination->elevation);
}
		printf("\n");
		printf("\n");
	}

	for (int i = 0 ; i < mon_reseau.nb_sommet ; i++) {
		free(mon_reseau.sommets[i].arcs);
	}
	free(mon_reseau.sommets);
	free(mon_reseau.arcs);
	return 0;
}
