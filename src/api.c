#include "stdio.h"
#include "stdlib.h"
#include "epanet_parser.h"
#include "algorithm_flow.h"
#include "time.h"

int analyse_comparative_FF_EPA_random(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs, int affichage) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	randomise_demande(&projet);
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_FF_EPA(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs, int affichage) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_FF_EPA_OR(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs, int affichage) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow_oriente(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_EK_EPA_random(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs, int affichage) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	randomise_demande(&projet);
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_edmonds_karp(&reseau_epanet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_EK_EPA(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs, int affichage) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_edmonds_karp(&reseau_epanet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_EK_EPA_OR(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa, flotant vitesse_reservoir, flotant vitesse_arcs, int affichage) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	modif_multiplicateur(&projet, proportion_demande_epa);
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow_oriente(&reseau_epanet, vitesse_reservoir, vitesse_arcs);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_edmonds_karp(&reseau_epanet);
	if (affichage) print_graph_details(&reseau_epanet, vitesse_reservoir, vitesse_arcs);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int main(int argc, char *argv[]) {
	if (argc != 12) {
		printf("Usage: %s <fichier.inp> <output_epanet.txt> <output_algo.txt> <proportion_source> <proportion_demande> <proportion_demande_epa> <vitesse_reservoir_m/s> <vitesse_arcs_m/s> <type_analyse> <seed> <affichage>\n", argv[0]);
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
	unsigned int seed = atoi(argv[10]);
	int affichage = atoi(argv[11]);

	if (seed != 0){
		srand(seed);
	} else {srand(time(NULL));}

	switch (type) {
		case 1:
			return analyse_comparative_FF_EPA(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs, affichage);
		case 2:
			return analyse_comparative_FF_EPA_random(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs, affichage);
		case 3:
			return analyse_comparative_FF_EPA_OR(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs, affichage);
		case 4:
			return analyse_comparative_EK_EPA(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs, affichage);
		case 5:
			return analyse_comparative_EK_EPA_random(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs, affichage);
		case 6:
			return analyse_comparative_EK_EPA_OR(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa, vitesse_reservoir, vitesse_arcs, affichage);
	}

	return 0;
}
