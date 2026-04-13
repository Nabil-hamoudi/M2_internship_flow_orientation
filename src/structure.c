# include <stdio.h>
# include <stdlib.h>

#define ALLOCATION_FAIL_GRAPH 20
#define ALLOCATION_FAIL_SOMMETS 21
#define ALLOCATION_FAIL_ARCS 22

typedef float flotant;
typedef int nbr;

enum type_sommet {
	SOURCE,
	DESTINATION,
	RESERVOIR
};

enum type_arcs {
	TUYAU,
	POMPE,
	VALVE
};

struct sommet {
	enum type_sommet type;
	nbr degree_sortant;
	flotant elevation;
	struct arc *arcs;
};

struct arc {
	enum type_arcs type;
	flotant diametre;
	flotant longueur;
	struct sommet *destination;
};

struct graph {
	nbr nb_sommet;
	nbr nb_arcs;
	struct sommet *sommets;
};

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs) {
	struct graph G;
	G.nb_sommet = nb_sommet;
	G.nb_arcs = nb_arcs;
	G.sommets = malloc(G.nb_sommet * sizeof(struct sommet));
	if (G.sommets == NULL && G.nb_sommet > 0) exit(ALLOCATION_FAIL_GRAPH);
	return G;
}

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree_sortant, flotant elevation) {
	struct sommet S;
	S.type = type_s;
	S.elevation = elevation;
	S.degree_sortant = degree_sortant;
	S.arcs = malloc(S.degree_sortant * sizeof(struct arc));
	if (S.arcs == NULL && S.degree_sortant > 0) exit(ALLOCATION_FAIL_SOMMETS);
	return S;
}

struct arc assignation_arc(enum type_arcs type_a, flotant diametre, flotant longueur, struct sommet *destination) {
	struct arc A;
	A.type = type_a;
	A.diametre = diametre;
	A.longueur = longueur;
	A.diametre = diametre;
	A.destination = destination;
	return A;
}

int main() {
	struct graph mon_reseau = assignation_graph(2, 1);

	mon_reseau.sommets[0] = assignation_sommet(SOURCE, 1, 150.5);
	mon_reseau.sommets[1] = assignation_sommet(DESTINATION, 0, 100.0);

	mon_reseau.sommets[0].arcs[0] = assignation_arc(TUYAU, 300.0, 1500.0, &mon_reseau.sommets[1]);

	printf("=== VERIFICATION DU RESEAU ===\n");
	printf("Graphe global : %d sommets, %d arcs au total.\n\n", mon_reseau.nb_sommet, mon_reseau.nb_arcs);

	for (int i = 0; i < mon_reseau.nb_sommet; i++) {
		printf("-> Sommet [%d] :\n", i);
		printf("   Type : %d (0=SOURCE, 1=DESTINATION, 2=RESERVOIR)\n", mon_reseau.sommets[i].type);
		printf("   Elevation : %.2f m\n", mon_reseau.sommets[i].elevation);

		for (int j = 0; j < mon_reseau.sommets[i].degree_sortant; j++) {
			struct arc arc_actuel = mon_reseau.sommets[i].arcs[j];
			printf("   ||--- Arc %d sortant ---\n", j);
			printf("   || Type : %d (0=TUYAU, 1=POMPE, 2=VALVE)\n", arc_actuel.type);
			printf("   || Diametre : %.2f mm, Longueur : %.2f m\n", arc_actuel.diametre, arc_actuel.longueur);

			printf("   || -----> Connecte a un sommet d'elevation : %.2f m\n", 
			arc_actuel.destination->elevation);
		}
		printf("\n");
	}

    free(mon_reseau.sommets[0].arcs);
    free(mon_reseau.sommets);return 0;
}
