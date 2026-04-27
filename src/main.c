#include "stdio.h"
#include "stdlib.h"
#include "epanet_parser.h"
#include "algorithm_flow.h"

int analyse_comparative_FF_EPA_random(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_random(&reseau_epanet, proportion_demande, proportion_source);
	// ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int analyse_comparative_FF_EPA(char *fichier_inp, char *fichier_output_epa, char *fichier_output_algo, flotant proportion_source, flotant proportion_demande, flotant proportion_demande_epa) {
	EN_Project projet = init_inp_file(fichier_inp, "epanet_file.log", "resultat.res");
	comput_flow(&projet);
	struct graph reseau_epanet = chargement_graph(&projet);

	export_flow_matrix(&reseau_epanet, fichier_output_epa, 0);
	fix_capacite_flow(&reseau_epanet);
	ajout_source_destination(&reseau_epanet);
	ajout_capacite_demande(&reseau_epanet, proportion_demande);
	ajout_capacite_source(&reseau_epanet, proportion_source);
	nullifier_flow(&reseau_epanet);

	compute_flow_ford_fukerson(&reseau_epanet);

	export_flow_matrix(&reseau_epanet, fichier_output_algo, 1);
	free_graph(&reseau_epanet);

	EN_close(projet);
	EN_deleteproject(projet);
	return 0;
}

int main(int argc, char *argv[]) {
	if (argc != 8) {
		printf("Usage: %s <fichier.inp> <output_epanet.txt> <output_algo.txt> <proportion_source> <proportion_demande> <proportion_demande_epa> <type_analyse>\n", argv[0]);
		return 1;
	}
	char *fichier_inp = argv[1];
	char *fichier_output_epa = argv[2];
	char *fichier_output_algo = argv[3];
	flotant proportion_source = atof(argv[4]);
	flotant proportion_demande = atof(argv[5]);
	flotant proportion_demande_epa = atof(argv[6]);
	int type = atoi(argv[7]);

	switch (type) {
		case 1:
			return analyse_comparative_FF_EPA_random(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa);
		default:
			return analyse_comparative_FF_EPA(fichier_inp, fichier_output_epa, fichier_output_algo, proportion_source, proportion_demande, proportion_demande_epa);
	}


}
