#include "stdio.h"
#include "stdlib.h"
#include "math.h"
#include "float.h"
#include "structure.h"

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
	printf("Vitesse max Reservoir : %.4f m/s | arcs : %.4f m/s\n", v_res, v_arc);
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
		"ID", "Type", "Connexion", "Diam.", "Long.", "Capacité", "Flow", "Vit.In(m/s)");

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
		v_input);
	}
	printf("=====================================================================================\n\n");
}

void fermeture_arc_ferme(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		if (!(reseau->arcs[i].ouvert)) {
			reseau->arcs[i].capacite = 0.0;
		}
	}

}

void fix_capacite_flow(struct graph* reseau, float vitesse_reservoir, float vitesse_arcs) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			if (reseau->arcs[i].type != TUYAU) {
				reseau->arcs[i].capacite = DBL_MAX;
			} else if (source->type == RESERVOIR) {
				reseau->arcs[i].capacite =  (M_PI * (((reseau->arcs[i].diametre/1000) * (reseau->arcs[i].diametre/1000))/4.0) * (60.0 * vitesse_reservoir)) * 1000.0;
			} else {
				reseau->arcs[i].capacite =  (M_PI * (((reseau->arcs[i].diametre/1000) * (reseau->arcs[i].diametre/1000))/4.0) * (60.0 * vitesse_arcs)) * 1000.0;
			}
		}
	}
	fermeture_arc_ferme(reseau);
}

void fix_capacite_flow_un(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			if (reseau->arcs[i].type != TUYAU) {
				reseau->arcs[i].capacite = DBL_MAX;
			} else if (source->type == RESERVOIR) {
				reseau->arcs[i].capacite =  1.0;
			} else {
				reseau->arcs[i].capacite = 1.0;
			}
		}
	}
	fermeture_arc_ferme(reseau);
}

flotant get_flow_non_oriente(struct graph* reseau, nbr index_aller, nbr index_retour) {
	return fabs(reseau->arcs[index_aller].flow - reseau->arcs[index_retour].flow);
}

flotant get_velocity_non_oriente(struct graph* reseau, nbr index_aller, nbr index_retour) {
	return fabs(compute_velocity(reseau, index_aller) - compute_velocity(reseau, index_retour));
}

void fix_capacite_flow_calcule(struct graph* reseau) {
	for (nbr i=0; i < reseau->nb_arcs ; i += 2) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			flotant flow_abs = get_flow_non_oriente(reseau, i, i+1);
			if (flow_abs > 0.0) {
				reseau->arcs[i].capacite = flow_abs;
				reseau->arcs[i+1].capacite = flow_abs;
			} else {
				reseau->arcs[i].capacite = 0.0;
				reseau->arcs[i+1].capacite = 0.0;
			}
		}
	}
	fermeture_arc_ferme(reseau);
}

void fix_capacite_flow_calcule_portion(struct graph* reseau, flotant portion) {
	nbr nb_paires = reseau->nb_arcs / 2;
	nbr target = (nbr)(nb_paires * portion);
	nbr selected = 0;

	for (nbr i = 0; i < nb_paires && selected < target; i++) {
		flotant prob = (flotant)(target - selected) / (nb_paires - i);
		flotant r = (flotant)rand() / RAND_MAX;

		if (r < prob) {
			nbr idx_aller = i * 2;
			nbr idx_retour = i * 2 + 1;

			flotant flow_abs = get_flow_non_oriente(reseau, idx_aller, idx_retour);

			reseau->arcs[idx_aller].capacite = flow_abs;
			reseau->arcs[idx_retour].capacite = flow_abs;

			selected++;
		}
	}
}

void fix_capacite_flow_oriente(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs ; i++) {
		struct sommet* source = reseau->arcs[i].source;
		struct sommet* destination = reseau->arcs[i].destination;
		if (source->type != SOURCE && destination->type != DESTINATION && source->type != DESTINATION && destination->type != SOURCE) {
			if (!(reseau->arcs[i].flow > 0.0)) {
				reseau->arcs[i].capacite = 0.0;
			}
		}
	}
}

void fix_capacite_flow_oriente_portion(struct graph* reseau, flotant portion) {
	nbr nb_paires = reseau->nb_arcs / 2;
	nbr target = (nbr)(nb_paires * portion);
	nbr selected = 0;

	for (nbr i = 0; i < nb_paires && selected < target; i++) {
		flotant prob = (flotant)(target - selected) / (nb_paires - i);
		flotant r = (flotant)rand() / RAND_MAX;

		if (r < prob) {
			nbr idx_aller = i * 2;
			nbr idx_retour = i * 2 + 1;
			
			if (!(reseau->arcs[idx_aller].flow > 0.0)) {
				reseau->arcs[idx_aller].capacite = 0.0;
			}
			if (!(reseau->arcs[idx_retour].flow > 0.0)) {
				reseau->arcs[idx_retour].capacite = 0.0;
			}
			
			selected++;
		}
	}
}

void delete_source_destination(struct graph* reseau) {
	struct sommet *source = reseau->sommet_source;
	struct sommet *destination = reseau->sommet_destination;
	for (int i = 0; i < source->degree; i++) {
		struct sommet *source_destination = source->arcs[i].arc_sortant->destination;
		source_destination->degree -= 1;
	}

	for (int i = 0; i < destination->degree; i++) {
		struct sommet *source_destination = destination->arcs[i].arc_entrant->source;
		source_destination->degree -= 1;
	}

	reseau->nb_sommet -= 2;
	reseau->nb_arcs -= ((reseau->sommet_source->degree + reseau->sommet_destination->degree)*2);

	free(source->arcs);
	free(destination->arcs);

	reseau->sommet_source = NULL;
	reseau->sommet_destination = NULL;

}

void ajout_source_destination(struct graph* reseau) {
	nbr degree_source = 0, degree_destination = 0;
	for (int i=0; i < reseau->nb_sommet ; i++) {
		if (reseau->sommets[i].demande > 0.0 || reseau->sommets[i].type == TANK) {
			degree_destination++;
		}
		if (reseau->sommets[i].type == RESERVOIR || reseau->sommets[i].type == TANK || reseau->sommets[i].demande < 0.0) {
			degree_source++;
		}
	}

	reseau->nb_sommet += 2;

	reseau->sommets[reseau->nb_sommet-2] = assignation_sommet(SOURCE, degree_source, 0, 10000, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
	reseau->sommets[reseau->nb_sommet-1] = assignation_sommet(DESTINATION, degree_destination, 0, -10000, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
	reseau->sommet_source = &reseau->sommets[reseau->nb_sommet-2];
	reseau->sommet_destination = &reseau->sommets[reseau->nb_sommet-1];
	nbr lien_source = 0, lien_destination = 0;
	for (int i=0; i < reseau->nb_sommet-2 ; i++) {
		if (reseau->sommets[i].type == RESERVOIR || reseau->sommets[i].type == TANK || reseau->sommets[i].demande < 0.0) {
			reseau->nb_arcs += 2;
			reseau->arcs[reseau->nb_arcs-2] = assignation_arc(TUYAU, 0.0, 0.0, 0.0, 0.0, 0.0, reseau->sommet_source, &reseau->sommets[i], 1);
			reseau->arcs[reseau->nb_arcs-1] = assignation_arc_oppose(&reseau->arcs[reseau->nb_arcs-2]);
			reseau->sommet_source->arcs[lien_source] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], reseau->sommet_source);
			lien_source++;
			reseau->sommets[i].degree++;
			reseau->sommets[i].arcs[reseau->sommets[i].degree-1] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], &reseau->sommets[i]);
		} 
		if (reseau->sommets[i].demande > 0.0 || reseau->sommets[i].type == TANK) {
			reseau->nb_arcs += 2;
			reseau->arcs[reseau->nb_arcs-2] = assignation_arc(TUYAU, 0.0, 0.0, 0.0, 0.0, 0.0, &reseau->sommets[i], reseau->sommet_destination, 1);
			reseau->arcs[reseau->nb_arcs-1] = assignation_arc_oppose(&reseau->arcs[reseau->nb_arcs-2]);
			reseau->sommet_destination->arcs[lien_destination] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], reseau->sommet_destination);
			lien_destination++;
			reseau->sommets[i].degree++;
			reseau->sommets[i].arcs[reseau->sommets[i].degree-1] = assignation_arc_symmetrique(&reseau->arcs[reseau->nb_arcs-2], &reseau->arcs[reseau->nb_arcs-1], &reseau->sommets[i]);}
	}
}

void ajout_capacite_source(struct graph* reseau, float proportion_source) {
	for (int i=0; i < reseau->sommet_source->degree; i++) {
		if (reseau->sommet_source->arcs[i].arc_sortant->destination->type == TANK) {
			reseau->sommet_source->arcs[i].arc_sortant->capacite = reseau->sommet_source->arcs[i].arc_sortant->destination->emmission;
			reseau->sommet_source->arcs[i].arc_entrant->capacite = 0.0;
		} else {
			reseau->sommet_source->arcs[i].arc_sortant->capacite = DBL_MAX;
			reseau->sommet_source->arcs[i].arc_entrant->capacite = 0.0;
		}
	}

}

void ajout_capacite_demande(struct graph* reseau, float proportion_demande) {
	reseau->demande_global = 0.0;
	for (int i=0; i < reseau->sommet_destination->degree; i++) {
		if (reseau->sommet_destination->arcs[i].arc_sortant->destination->type == TANK) {
		reseau->sommet_destination->arcs[i].arc_entrant->capacite = reseau->sommet_destination->arcs[i].arc_entrant->source->demande;
		reseau->sommet_destination->arcs[i].arc_sortant->capacite = 0.0;
			} else {
			reseau->demande_global += (reseau->sommet_destination->arcs[i].arc_entrant->source->demande) * proportion_demande;
			reseau->sommet_destination->arcs[i].arc_entrant->capacite = (reseau->sommet_destination->arcs[i].arc_entrant->source->demande) * proportion_demande;
			reseau->sommet_destination->arcs[i].arc_sortant->capacite = 0.0;
			}
	}
}

void nullifier_flow(struct graph* reseau) {
	for (int i=0; i < reseau->nb_arcs; i++) {
		reseau->arcs[i].flow = 0.0;
	};
}

typedef void (*fonction_ordre_t)(struct sommet* depart, int* indices, int taille);

void generer_ordre_aleatoire(struct sommet* depart, int* indices, int taille) {
	for (int i = 0; i < taille; i++) {
		indices[i] = i;
	}
	for (int i = taille - 1; i > 0; i--) {
		int j = rand() % (i + 1);
		int temp = indices[i];
		indices[i] = indices[j];
		indices[j] = temp;
	}
}

void merge (int *a, int n, int m) {
    int i, j, k;
    int *x = malloc(n * sizeof (int));
    for (i = 0, j = m, k = 0; k < n; k++) {
        x[k] = j == n      ? a[i++]
             : i == m      ? a[j++]
             : a[j] < a[i] ? a[j++]
             :               a[i++];
    }
    for (i = 0; i < n; i++) {
        a[i] = x[i];
    }
    free(x);
}

void merge_sort (int *a, int n) {
    if (n < 2)
        return;
    int m = n / 2;
    merge_sort(a, m);
    merge_sort(a + m, n - m);
    merge(a, n, m);
}

void generer_ordre_elevation(struct sommet* depart, int* indices, int taille) {
    if (taille == 0) return;

    int *packed_array = malloc(taille * sizeof(int));

    for (int i = 0; i < taille; i++) {
        struct sommet* voisin = depart->arcs[i].arc_sortant->destination;
        int key = (int) (voisin->elevation * 10000.0);

        packed_array[i] = (key * taille) + i;
    }

    merge_sort(packed_array, taille);

    for (int i = 0; i < taille; i++) {
        int idx = ((packed_array[i] % taille) + taille) % taille;
        indices[i] = idx;
    }

    free(packed_array);
}

flotant parcours_ff_iteratif(struct graph* reseau, fonction_ordre_t generer_ordre) {
	flotant epsilon = 0.0;
	int nb_s = reseau->nb_sommet;

	struct sommet** pile = malloc((reseau->nb_arcs + 1) * sizeof(struct sommet*));
	struct arc* parent_arc[nb_s];
	int is_inverse[nb_s];
	flotant path_flow[nb_s];

	int top = 0;

	struct sommet* source = reseau->sommet_source;
	int source_idx = source - reseau->sommets;

	pile[top++] = source;
	path_flow[source_idx] = DBL_MAX;

	int dest_idx = -1;

	while (top > 0) {
		struct sommet* u = pile[--top];
		int u_idx = u - reseau->sommets;

		if (u->marque) continue;
		u->marque = 1;

		if (u->type == DESTINATION) {
			dest_idx = u_idx;
			break;
		}

		/* Déterminer si u est un TANK atteint directement depuis la super-source (chaîne de taille 1) */
		int u_direct_from_source = (u->type == TANK && u_idx != source_idx &&
			((!is_inverse[u_idx] && parent_arc[u_idx]->source == source) ||
			 (is_inverse[u_idx] && parent_arc[u_idx]->destination == source)));

		int indices[u->degree];
		generer_ordre(u, indices, u->degree);

		for (int k = 0; k < u->degree; k++) {
			int i = indices[k];
			flotant flow_ajoutable;

			/* Skip : interdire chaîne supersource -> tank -> superdestination (2 arcs) */
			if (u_direct_from_source && u->arcs[i].arc_sortant->destination->type == DESTINATION) {
				continue;
			}

			struct arc* arc_out = u->arcs[i].arc_sortant;
			struct sommet* v_out = arc_out->destination;
			flow_ajoutable = arc_out->capacite - arc_out->flow;

			if (flow_ajoutable > epsilon && !v_out->marque) {
				int v_idx = v_out - reseau->sommets;
				parent_arc[v_idx] = arc_out;
				is_inverse[v_idx] = 0;
				path_flow[v_idx] = fmin(path_flow[u_idx], flow_ajoutable);
				pile[top++] = v_out;
			}

			struct arc* arc_in = u->arcs[i].arc_entrant;
			struct sommet* v_in = arc_in->source;
			flow_ajoutable = arc_in->flow;

			if (flow_ajoutable > epsilon && !v_in->marque) {
				int v_idx = v_in - reseau->sommets;
				parent_arc[v_idx] = arc_in;
				is_inverse[v_idx] = 1;
				path_flow[v_idx] = fmin(path_flow[u_idx], flow_ajoutable);
				pile[top++] = v_in;
			}
		}
	}

	if (dest_idx != -1) {
		flotant new_flot = path_flow[dest_idx];
		int curr_idx = dest_idx;

		while (curr_idx != source_idx) {
			struct arc* arc = parent_arc[curr_idx];
			
			if (is_inverse[curr_idx]) {
				arc->flow -= new_flot;
				curr_idx = arc->destination - reseau->sommets;
			} else {
				arc->flow += new_flot;
				curr_idx = arc->source - reseau->sommets;
			}
		}
		free(pile);
		return new_flot;
	}

	free(pile);
	return -1.0;
}

void marque_zero_sommets(struct graph* reseau) {
	for (int i=0; i<reseau->nb_sommet; i++) {
		reseau->sommets[i].marque = 0;
	}
}

void start_flow_ford_fukerson(struct graph* reseau, fonction_ordre_t generer_ordre) {
	marque_zero_sommets(reseau);
	flotant result = 1.0;
	
	while (result != -1.0) {
		marque_zero_sommets(reseau);
		result = parcours_ff_iteratif(reseau, generer_ordre); 
	};
	
	compute_satisfaction_rate(reseau);
}


void marque_zero_arcs(struct graph* reseau) {
	for (int i=0; i<reseau->nb_sommet; i++) {
		reseau->arcs[i].marque = 0;
	}
}

flotant parcours_ek(struct file* file, struct file** end_file, fonction_ordre_t generer_ordre) {
	flotant flow_ajoutable;
	flotant epsilon = 0.0;
	struct sommet* sommet = file->sommet;
	flotant flow = file->flow_ajoutable;
	if (sommet->type == DESTINATION) {return flow;}

	/* Déterminer si le sommet courant est un TANK atteint directement depuis la super-source (chaîne de taille 1) */
	int direct_from_source = (sommet->type == TANK && file->precedent != NULL &&
		file->precedent->sommet->type == SOURCE);

	int indices[sommet->degree];
	generer_ordre(sommet, indices, sommet->degree);

	for (int k = 0; k < sommet->degree; k++) {
		int i = indices[k];

		/* Skip : interdire chaîne supersource -> tank -> superdestination (2 arcs) */
		if (direct_from_source && sommet->arcs[i].arc_sortant->destination->type == DESTINATION) {
			continue;
		}

		int is_u_source = (sommet->type == SOURCE);

		flow_ajoutable = sommet->arcs[i].arc_sortant->capacite - sommet->arcs[i].arc_sortant->flow;
		struct sommet* v_out = sommet->arcs[i].arc_sortant->destination;
		int can_visit_out = 0;
		if (v_out->marque == 0) {
			can_visit_out = 1;
		} else if (v_out->marque == 1 && !is_u_source) {
			can_visit_out = 1;
		}

		if (flow_ajoutable > epsilon && can_visit_out) {
			flow_ajoutable = fmin(flow, flow_ajoutable);
			v_out->marque = is_u_source ? 1 : 2;
			struct file* sommet_suivant = malloc(sizeof(struct file));
			sommet_suivant->sommet = v_out;
			sommet_suivant->flow_ajoutable = flow_ajoutable;
			sommet_suivant->arc = sommet->arcs[i].arc_sortant;
			sommet_suivant->inverse = 1;
			sommet_suivant->precedent = file;
			sommet_suivant->suivant = NULL;
			(*end_file)->suivant = sommet_suivant;
			*end_file = sommet_suivant;
		}

		flow_ajoutable = sommet->arcs[i].arc_entrant->flow;
		struct sommet* v_in = sommet->arcs[i].arc_entrant->source;
		int can_visit_in = 0;
		if (v_in->marque == 0) {
			can_visit_in = 1;
		} else if (v_in->marque == 1 && !is_u_source) {
			can_visit_in = 1;
		}

		if (flow_ajoutable > epsilon && can_visit_in) {
			flow_ajoutable = fmin(flow, flow_ajoutable);
			v_in->marque = is_u_source ? 1 : 2;
			struct file* sommet_suivant = malloc(sizeof(struct file));
			sommet_suivant->sommet = v_in;
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

void start_flow_edmonds_karp(struct graph* reseau, fonction_ordre_t generer_ordre) {
	marque_zero_sommets(reseau);
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
		new_flot = parcours_ek(file, end_file, generer_ordre);
		struct file* current = file;
		struct file* final = file;
		struct file* tmp;
		while (current->suivant != NULL && new_flot == -1.0) {
			current = current->suivant;
			new_flot = parcours_ek(current, end_file, generer_ordre);
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
		marque_zero_sommets(reseau);
	} while (new_flot != -1.0);
	compute_satisfaction_rate(reseau);
}

void compute_flow_ford_fukerson(struct graph* reseau) {
	start_flow_ford_fukerson(reseau, generer_ordre_aleatoire);
}

void compute_flow_edmonds_karp(struct graph* reseau) {
	start_flow_edmonds_karp(reseau, generer_ordre_aleatoire);
}

void compute_flow_elevation_prioritaire_ff(struct graph* reseau) {
	start_flow_ford_fukerson(reseau, generer_ordre_elevation);
}

void compute_flow_edmonds_karp_elevation(struct graph* reseau) {
	start_flow_edmonds_karp(reseau, generer_ordre_elevation);
}

void compute_pression_statique(struct graph* reseau, int mode) {
    if (reseau == NULL || reseau->sommets == NULL || reseau->nb_sommet == 0) return;

    flotant max_charge = -DBL_MAX;
    flotant min_charge = DBL_MAX;
    flotant sum_charge = 0.0;
    int count_sources = 0;

    for (int i = 0; i < reseau->nb_sommet; i++) {
        if (reseau->sommets[i].type == RESERVOIR || reseau->sommets[i].type == TANK) {
            
            flotant charge_source = reseau->sommets[i].elevation;
            if (reseau->sommets[i].type == TANK) {
                charge_source += reseau->sommets[i].pression; 
            }

            if (charge_source > max_charge) max_charge = charge_source;
            if (charge_source < min_charge) min_charge = charge_source;
            sum_charge += charge_source;
            count_sources++;
        }
    }

    if (count_sources == 0) return;

    flotant reference_charge = 0.0;
    switch (mode) {
        case 0:
            reference_charge = max_charge;
            break;
        case 1: 
            reference_charge = min_charge;
            break;
        case 2: 
            reference_charge = sum_charge / (flotant)count_sources;
            break;
        default:
            reference_charge = max_charge;
            break;
    }

    for (int i = 0; i < reseau->nb_sommet; i++) {
        if (reseau->sommets[i].type != SOURCE && reseau->sommets[i].type != DESTINATION) {
            
            reseau->sommets[i].charge = reference_charge;
            
            if (reseau->sommets[i].type == TANK) {
                continue;
            } else if (reseau->sommets[i].type == RESERVOIR) {
                reseau->sommets[i].pression = reference_charge;
            } else {
                reseau->sommets[i].pression = reference_charge - reseau->sommets[i].elevation;
            }
        }
    }
}

void orienter_arcs_par_pression(struct graph* reseau) {
    if (reseau == NULL || reseau->arcs == NULL) return;

    for (int i = 0; i < reseau->nb_arcs; i += 2) {
        struct arc* arc_aller = &reseau->arcs[i];
        struct arc* arc_retour = &reseau->arcs[i+1];
        
        struct sommet* s1 = arc_aller->source;
        struct sommet* s2 = arc_aller->destination;

        if (s1->type == SOURCE || s2->type == DESTINATION || 
            s1->type == DESTINATION || s2->type == SOURCE) {
            continue;
        }

        flotant diff = s1->pression - s2->pression; 

        if (diff > 0.0) {
            arc_retour->capacite = 0.0;
        } else if (diff < 0.0) {
            arc_aller->capacite = 0.0;
        } else {
            arc_aller->capacite = 0.0;
            arc_retour->capacite = 0.0;
        }
    }
    
    fermeture_arc_ferme(reseau);
}

void tester_orientation_flow(struct graph* reseau) {
    if (reseau == NULL || reseau->arcs == NULL) return;

    for (int i = 0; i < reseau->nb_arcs; i++) {
        if (reseau->arcs[i].capacite > 0.0) {
            reseau->arcs[i].flow = 1.0;
        } else {
            reseau->arcs[i].flow = 0.0;
        }
    }
}

flotant compute_min_cut(struct graph* reseau) {
    if (reseau == NULL) return -1.0;

    fix_capacite_flow_un(reseau);

    ajout_source_destination(reseau);

    for (int i = 0; i < reseau->sommet_source->degree; i++) {
        struct sommet* dest = reseau->sommet_source->arcs[i].arc_sortant->destination;
        
        if (dest->type == TANK && dest->emmission <= 0.0) {
            reseau->sommet_source->arcs[i].arc_sortant->capacite = 0.0;
        } else {
            reseau->sommet_source->arcs[i].arc_sortant->capacite = DBL_MAX;
        }
        reseau->sommet_source->arcs[i].arc_entrant->capacite = 0.0;
    }

    for (int i = 0; i < reseau->sommet_destination->degree; i++) {
        struct sommet* src = reseau->sommet_destination->arcs[i].arc_entrant->source;
        
        if (src->type == TANK) {
            reseau->sommet_destination->arcs[i].arc_entrant->capacite = 0.0;
        } else {
            reseau->sommet_destination->arcs[i].arc_entrant->capacite = DBL_MAX;
        }
        reseau->sommet_destination->arcs[i].arc_sortant->capacite = 0.0;
    }
    nullifier_flow(reseau);

    start_flow_ford_fukerson(reseau, generer_ordre_aleatoire);
    flotant min_cut_value = 0.0;
    for (int i = 0; i < reseau->sommet_destination->degree; i++) {
        min_cut_value += reseau->sommet_destination->arcs[i].arc_entrant->flow;
    }

    delete_source_destination(reseau);

    return min_cut_value;
}

void orienter_st_harmonique(struct graph* reseau) {
    if (reseau == NULL || reseau->sommets == NULL) {
        return;
    }

    int n = reseau->nb_sommet;
    flotant* potentiel = malloc(n * sizeof(flotant));
    flotant* nouveau_potentiel = malloc(n * sizeof(flotant));
    int* est_ancrage = calloc(n, sizeof(int));
    for (int i = 0; i < n; i++) {
        struct sommet* u = &reseau->sommets[i];
        potentiel[i] = u->elevation;
        
        if (u->type == RESERVOIR || u->type == TANK || u->demande != 0.0) {
            est_ancrage[i] = 1;
        }
    }

    int iterations = 20000;
    for (int iter = 0; iter < iterations; iter++) {
        for (int i = 0; i < n; i++) {
            if (est_ancrage[i]) {
                nouveau_potentiel[i] = reseau->sommets[i].elevation;
                continue;
            }

            struct sommet* u = &reseau->sommets[i];
            if (u->degree == 0) {
                nouveau_potentiel[i] = potentiel[i];
                continue;
            }

            flotant somme = 0.0;
            for (int j = 0; j < u->degree; j++) {
                struct sommet* voisin = u->arcs[j].arc_sortant->destination;
                int v_idx = voisin - reseau->sommets;
                somme += potentiel[v_idx];
            }
            nouveau_potentiel[i] = somme / (flotant)u->degree;
        }

        for (int i = 0; i < n; i++) {
            potentiel[i] = nouveau_potentiel[i];
        }
    }

    for (int i = 0; i < reseau->nb_arcs; i += 2) {
        struct arc* arc_aller = &reseau->arcs[i];
        struct arc* arc_retour = &reseau->arcs[i+1];
        
        int src_idx = arc_aller->source - reseau->sommets;
        int dest_idx = arc_aller->destination - reseau->sommets;

        flotant diff = potentiel[src_idx] - potentiel[dest_idx];

        if (diff > 0.0) {
            arc_retour->capacite = 0.0;
            arc_retour->ouvert = 0;
        } else if (diff < 0.0) {
            arc_aller->capacite = 0.0;
            arc_aller->ouvert = 0;
        } else {
            if (src_idx > dest_idx) {
                arc_retour->capacite = 0.0;
                arc_retour->ouvert = 0;
            } else {
                arc_aller->capacite = 0.0;
                arc_aller->ouvert = 0;
            }
        }
    }

    fermeture_arc_ferme(reseau);

    free(est_ancrage);
    free(potentiel);
    free(nouveau_potentiel);
}

int dfs_detect_and_cancel_cycle(struct graph* reseau, struct sommet* u, int* marque, struct arc** parent_arc) {
    int u_idx = u - reseau->sommets;
    marque[u_idx] = 1;

    for (int i = 0; i < u->degree; i++) {
        struct arc* arc_out = u->arcs[i].arc_sortant;
        struct sommet* v = arc_out->destination;
        int v_idx = v - reseau->sommets;

        if (arc_out->flow > 0.0) {
            if (marque[v_idx] == 1) {
                flotant min_flow = arc_out->flow;
                struct sommet* curr = u;
                while (curr != v) {
                    int curr_idx = curr - reseau->sommets;
                    struct arc* prev_arc = parent_arc[curr_idx];
                    if (prev_arc->flow < min_flow) {
                        min_flow = prev_arc->flow;
                    }
                    curr = prev_arc->source;
                }
                
                arc_out->flow -= min_flow;
                curr = u;
                while (curr != v) {
                    int curr_idx = curr - reseau->sommets;
                    struct arc* prev_arc = parent_arc[curr_idx];
                    prev_arc->flow -= min_flow;
                    curr = prev_arc->source;
                }
                return 1;
            } else if (marque[v_idx] == 0) {
                parent_arc[v_idx] = arc_out;
                if (dfs_detect_and_cancel_cycle(reseau, v, marque, parent_arc)) {
                    return 1;
                }
            }
        }
    }
    
    marque[u_idx] = 2;
    return 0;
}

void annuler_circuits_flot(struct graph* reseau) {
    if (reseau == NULL || reseau->sommets == NULL) return;
    int n = reseau->nb_sommet;
    int* marque = malloc(n * sizeof(int));
    struct arc** parent_arc = malloc(n * sizeof(struct arc*));
    
    int cycle_found;
    do {
        cycle_found = 0;
        for (int i = 0; i < n; i++) marque[i] = 0;
        for (int i = 0; i < n; i++) parent_arc[i] = NULL;
        
        for (int i = 0; i < n; i++) {
            if (marque[i] == 0) {
                if (dfs_detect_and_cancel_cycle(reseau, &reseau->sommets[i], marque, parent_arc)) {
                    cycle_found = 1;
                    break;
                }
            }
        }
    } while (cycle_found);
    
    free(marque);
    free(parent_arc);
}

