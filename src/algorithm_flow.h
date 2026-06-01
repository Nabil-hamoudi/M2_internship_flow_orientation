#include "structure.h"

#define MALOC_RANDOM_SOURCE_FAIL 41
#define MALOC_RANDOM_DESTINATION_FAIL 42

void print_graph_details(struct graph *G, flotant v_res, flotant v_arc);

flotant get_flow_non_oriente(struct graph* reseau, nbr index_aller, nbr index_retour);

flotant get_velocity_non_oriente(struct graph* reseau, nbr index_aller, nbr index_retour);

void fix_capacite_flow(struct graph* reseau, float vitesse_reservoir, float vitesse_arcs);

void fix_capacite_flow_calcule(struct graph* reseau);

void fix_capacite_flow_oriente(struct graph* reseau);

void delete_source_destination(struct graph* reseau);

void ajout_source_destination(struct graph* reseau);

void ajout_capacite_demande(struct graph* reseau, float proportion_demande);

void ajout_capacite_source(struct graph* reseau, float proportion_source);

void nullifier_flow(struct graph* reseau);

void compute_flow_ford_fukerson(struct graph* reseau);

void compute_flow_edmonds_karp(struct graph* reseau);
