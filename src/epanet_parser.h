#include "epanet2_2.h"
#include "structure.h"

#define OPEN_EPANET_INP_ERROR 31

enum type_sommet parser_type_sommet(int type_epanet);

enum type_arcs parser_type_arc(int type_epanet);

EN_Project init_inp_file(char* input, char* log, char* binairy);

void comput_flow(EN_Project* ph);

void fermeture_free_project(EN_Project* ph);

void get_epanet_fulldemande(EN_Project* ph, struct graph* reseau);

void get_epanet_demande(EN_Project* ph, struct graph* reseau);

void modif_multiplicateur(EN_Project* ph, double multiplicateur);

void randomise_demande(EN_Project* ph);

void set_random_seed(unsigned int seed);

void reget_epanet_flow(EN_Project* ph, struct graph* reseau);

struct graph chargement_graph(EN_Project* ph);

