#define ALLOCATION_FAIL_GRAPH 20
#define ALLOCATION_FAIL_SOMMETS 21
#define ALLOCATION_FAIL_ARCS 22
#define GRAPHE_NON_INIT 51
#define ERREUR_FICHIER_OUTPUT_MATRICE_FLOW 52
#define ERREUR_MATRICE_FLOW_ALLOC 53


typedef double flotant;
typedef int nbr;

enum type_sommet {
	SOURCE,
	JONCTION,
	DESTINATION,
	RESERVOIR,
	TANK
};

enum type_arcs {
	TUYAU,
	POMPE,
	VALVE
};

struct sommet {
	enum type_sommet type;
	nbr degree;
	flotant elevation;
	flotant demande;
	flotant pression;
	int marque;
	struct arc_symmetrique *arcs;
};

struct arc_symmetrique {
	struct arc *arc_entrant;
	struct arc *arc_sortant;
};

struct arc {
	enum type_arcs type;
	flotant diametre;
	flotant longueur;
	flotant capacite;
	flotant flow;
	struct sommet *source;
	struct sommet *destination;
};

struct graph {
	nbr nb_sommet;
	nbr nb_arcs;
	flotant pression_requise;
	flotant exposant_pression;
	flotant demande_global;
	flotant demande_multiplier;
	flotant satifaisabilite;
	long temp;
	struct sommet *sommet_source;
	struct sommet *sommet_destination;
	struct sommet *sommets;
	struct arc *arcs;
};

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs, nbr sommet_supplementaire, nbr arcs_supplementaire, flotant pression_requise, flotant exposant_pression, flotant demande_global, flotant demande_multiplier, flotant satifaisabilite, long temp);

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree, nbr degree_ajouter, flotant elevation, flotant pression, flotant demande);

struct arc assignation_arc(enum type_arcs type_a, flotant diametre, flotant longueur, flotant capacite, flotant flow, struct sommet *source, struct sommet *destination);

struct arc assignation_arc_oppose(struct arc* B);

struct arc_symmetrique assignation_arc_symmetrique(struct arc* A, struct arc* B, struct sommet* source);

int free_graph(struct graph *G);

void compute_satisfaction_rate(struct graph* reseau);

flotant compute_velocity(struct graph* reseau, nbr arc_index);

void export_flow_matrix(struct graph *G, const char *filename, int source_destination);

