# include "stdio.h"
# include "stdlib.h"
# include "structure.h"
# include "math.h"

const char* get_nom_type_sommet(enum type_sommet type) {
	switch (type) {
	case SOURCE:		return "SOURCE";
	case JONCTION:		return "JONCTION";
	case DESTINATION:	return "DESTINATION";
	case RESERVOIR:		return "RESERVOIR";
	case TANK:		return "TANK";
	default:		return "INCONNU";
	}
}

const char* get_nom_type_arc(enum type_arcs type) {
	switch (type) {
		case TUYAU: return "TUYAU";
		case POMPE: return "POMPE";
		case VALVE: return "VALVE";
		default:    return "INCONNU";
	}
}

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs, nbr sommet_supplementaire, nbr arcs_supplementaire, flotant pression_requise, flotant exposant_pression, flotant demande_global, flotant demande_multiplier, flotant satifaisabilite, long temp) {
	struct graph G;
	G.nb_sommet = nb_sommet;
	G.nb_arcs = nb_arcs;
	G.pression_requise = pression_requise;
	G.exposant_pression = exposant_pression;
	G.demande_global = demande_global;
	G.demande_multiplier = demande_multiplier;
	G.satifaisabilite = satifaisabilite;
	G.temp = temp;
	G.sommets = malloc((G.nb_sommet+sommet_supplementaire) * sizeof(struct sommet));
	if (G.sommets == NULL && G.nb_sommet > 0) exit(ALLOCATION_FAIL_GRAPH);
	G.arcs = malloc((G.nb_arcs+arcs_supplementaire) * sizeof(struct arc));
	if (G.arcs == NULL && G.nb_arcs > 0) exit(ALLOCATION_FAIL_GRAPH);
	return G;
}

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree, nbr degree_ajouter, flotant elevation, flotant pression, flotant demande, flotant coord_x, flotant coord_y) {
	struct sommet S;
	struct coordonnee C;
	S.type = type_s;
	S.elevation = elevation;
	S.degree = degree;
	S.pression = pression;
	S.demande = demande;
	S.marque = 0;
	C.x = coord_x;
	C.y = coord_y;
	S.position = C;
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

int free_graph(struct graph *G) {
	if (G == NULL) return GRAPHE_NON_INIT;
	if (G->sommets != NULL) {
		for (nbr i = 0; i < G->nb_sommet; i++) {
			if (G->sommets[i].arcs != NULL) {
				free(G->sommets[i].arcs);
			}
		}
		free(G->sommets);
	}
	if (G->arcs != NULL) {
		free(G->arcs);
	}
	return 0;
}

void compute_satisfaction_rate(struct graph* reseau) {
	nbr deg = reseau->sommet_destination->degree;

	flotant total_satisfaction = 0.0;

	for (int i = 0; i < deg; i++) {
		struct arc *a = reseau->sommet_destination->arcs[i].arc_entrant;
		total_satisfaction += a->flow;
	}

	reseau->satifaisabilite = total_satisfaction / reseau->demande_global;
}

flotant compute_velocity(struct graph* reseau, nbr arc_index) {
	return (4.0 * (reseau->arcs[arc_index].flow / 1000.0)) / (M_PI * ((reseau->arcs[arc_index].diametre/1000.0) * (reseau->arcs[arc_index].diametre/1000.0)));
}

void export_flow_matrix(struct graph *G, const char *filename, int source_destination) {
	if (G == NULL || G->sommets == NULL || G->arcs == NULL) exit(GRAPHE_NON_INIT);

	FILE *file = fopen(filename, "w");
	if (file == NULL) exit(ERREUR_FICHIER_OUTPUT_MATRICE_FLOW);
	nbr n;
	nbr n_arcs;
	nbr n_arcs_non_nul = 0;
	flotant efficacite = G->satifaisabilite;
	nbr arcs_symmetrique = 0;
	if (source_destination) {
		n = G->nb_sommet - 2;
		n_arcs = G->nb_arcs - ((G->sommet_source->degree + G->sommet_destination->degree)*2);
	} else {
		n = G->nb_sommet;
		n_arcs = G->nb_arcs;
	};

	flotant **matrice = malloc(n * sizeof(flotant *));
	if (matrice == NULL) {
		fclose(file);
		exit(ERREUR_MATRICE_FLOW_ALLOC); 
	}

	for (nbr i = 0; i < n; i++) {
		matrice[i] = (flotant*) calloc(n, sizeof(flotant));
		if (matrice[i] == NULL) {
			fclose(file);
			exit(ERREUR_MATRICE_FLOW_ALLOC);
		}
		
		if (G->sommets[i].type != SOURCE && G->sommets[i].type != DESTINATION) {
			for (nbr j = 0; j < G->sommets[i].degree; j++) {
				if (G->sommets[i].arcs[j].arc_entrant->flow > 0.0 &&  G->sommets[i].arcs[j].arc_sortant->flow > 0.0 && G->sommets[i].arcs[j].arc_sortant->destination - G->sommets > i) {
					arcs_symmetrique++;
				}
			}
		}
	}

	for (nbr k = 0; k < n_arcs; k++) {
		struct arc *a = &G->arcs[k];
		nbr index_source = a->source - G->sommets;
		nbr index_destination = a->destination - G->sommets;
		if (a->destination->type != DESTINATION && a->source->type != SOURCE) {
			matrice[index_source][index_destination] = a->flow;
		}
		if (a->flow != 0.0) {
			n_arcs_non_nul += 1;
		}
	}

	fprintf(file, "%d\n", n);
	fprintf(file, "%d\n", n_arcs_non_nul);
	fprintf(file, "%.4f\n", efficacite);
	fprintf(file, "%d\n", arcs_symmetrique);
	fprintf(file, "%d\n", n_arcs);
	for (nbr i = 0; i < n; i++) {
		for (nbr j = 0; j < n; j++) {
			fprintf(file, "%.4f ", matrice[i][j]);
		}
		fprintf(file, "\n");
	}

	for (nbr i = 0; i < n; i++) {
	free(matrice[i]);
	}
	free(matrice);
	fclose(file);
}



