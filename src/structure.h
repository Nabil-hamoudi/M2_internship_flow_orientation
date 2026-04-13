#define ALLOCATION_FAIL_GRAPH 20
#define ALLOCATION_FAIL_SOMMETS 21
#define ALLOCATION_FAIL_ARCS 22

typedef float flotant;
typedef int nbr;

enum type_sommet {
	SOURCE,
	DESTINATION,
	RESERVOIR
};

enum type_arcs {
	TUYAU,
	POMPE,
	VALVE
};

struct sommet {
	enum type_sommet type;
	nbr degree_sortant;
	flotant elevation;
	struct arc *arcs;
};

struct arc {
	enum type_arcs type;
	flotant diametre;
	flotant longueur;
	struct sommet *destination;
};

struct graph {
	nbr nb_sommet;
	nbr nb_arcs;
	struct sommet *sommets;
};

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs);

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree_sortant, flotant elevation);

struct arc assignation_arc(enum type_arcs type_a, flotant diametre, flotant longueur, struct sommet *destination);

