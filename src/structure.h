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
	nbr degree;
	flotant elevation;
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
	flotant flow;
	struct sommet *source;
	struct sommet *destination;
};

struct graph {
	nbr nb_sommet;
	nbr nb_arcs;
	struct sommet *sommets;
	struct arc *arcs;
};

struct graph assignation_graph(nbr nb_sommet, nbr nb_arcs);

struct sommet assignation_sommet(enum type_sommet type_s, nbr degree, flotant elevation);

struct arc assignation_arc(enum type_arcs type_a, flotant diametre, flotant longueur, flotant flow, struct sommet *source, struct sommet *destination);

struct arc assignation_arc_oppose(struct arc* B);

struct arc_symmetrique assignation_arc_symmetrique(struct arc* A, struct arc* B, struct sommet* source);

