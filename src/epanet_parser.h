#include "epanet2.h"
#include "epanet2_2.h"
#include "epanet2_enums.h"

#define OPEN_EPANET_INP_ERROR 31

enum type_sommet parser_type_sommet(int type_epanet);

enum type_arcs parser_type_arc(int type_epanet);

EN_Project init_inp_file(char* input, char* log, char* binairy);

struct graph chargement_graph(EN_Project* ph);

