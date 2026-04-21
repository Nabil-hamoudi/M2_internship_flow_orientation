#include "structure.h"

#define MALOC_RANDOM_SOURCE_FAIL 41
#define MALOC_RANDOM_DESTINATION_FAIL 42
#define EPSILON 0.0

struct stack {
	struct stack *prev;
	struct sommet *sommet;
};

void fix_capacite_flow(struct graph* reseau);

void ajout_source_destination(struct graph* reseau);

void ajout_capacite_random(struct graph* reseau, float proportion_demande, float proportion_source);

void ajout_capacite_demande(struct graph* reseau, float proportion_demande);

void ajout_capacite_source(struct graph* reseau, float proportion_source);

void nullifier_flow(struct graph* reseau);

void marque_zero(struct graph* reseau);

void compute_flow_ford_fukerson(struct graph* reseau);

flotant compute_satisfaction_rate(struct graph* reseau);
