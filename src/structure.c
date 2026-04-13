# include <stdio.h>

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

struct donnee_sommet {
	flotant elevation;
};

struct sommet {
	enum type_sommet type;
	struct arc *arcs;
};

struct arc {
	enum type_arcs type;
	flotant diametre;
	flotant longueur;
	struct sommet *destination;
};

struct graphe {
	nbr nb_sommet;
	nbr nb_arcs;
	struct sommet *sommets;
};

int main() {



return 0;
}
