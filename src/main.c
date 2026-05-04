#include "stdio.h"
#include "stdlib.h"
#include "epanet_parser.h"
#include "algorithm_flow.h"
#include "time.h"

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


int analyse_comparative_FF_EPA_random(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);


	print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	fix_capacite_flow(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_random(&reseau_epanet, proportion_demande, proportion_source);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	
	print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_FF_EPA(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);
	print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}


int main(int argc, char *argv[]) {
	if (argc != 10) {
		printf("Usage: %s <fichier.inp> <output_epanet.txt> <output_algo.txt> <proportion_source> <proportion_demande> <proportion_demande_epa> <vitesse_reservoir_m/s> <vitesse_arcs_m/s> <type_analyse>\n", argv[0]);
		return 1;
	}
	char *fichier_inp = argv[1];
	char *fichier_output_epa = argv[2];
	char *fichier_output_algo = argv[3];
	flotant proportion_source = atof(argv[4]);
	flotant proportion_demande = atof(argv[5]);
	flotant proportion_demande_epa = atof(argv[6]);
	flotant vitesse_reservoir = atof(argv[7]);
	flotant vitesse_arcs = atof(argv[8]);
	int type = atoi(argv[9]);

	srand(time(NULL));

	switch (type) {
		case 1:
			return analyse_comparative_FF_EPA(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs);
		case 2:
			return analyse_comparative_FF_EPA_random(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs);
	}

	return 0;
}
