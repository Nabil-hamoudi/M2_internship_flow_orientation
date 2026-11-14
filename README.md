# Approches algorithmiques pour l'estimation de l'orientation des débits dans les réseaux de distribution d'eau

*Nabil HAMOUDI*

Stage de fin d'études du Master 2 AMIS, réalisé du 1er avril au 31 août 2026 au **laboratoire DAVID** (Université de Versailles Saint-Quentin / Paris-Saclay), sous l'encadrement de **Dominique BARTH**.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Présentation

Ce dépôt contient le code développé dans le cadre du mémoire [*Approches algorithmiques pour l'estimation de l'orientation des débits dans les réseaux de distribution d'eau*](docs/memoire.pdf).

Les logiciels de simulation hydraulique comme [EPANET](https://www.epa.gov/water-research/epanet) calculent les pressions et les débits d'un réseau en résolvant numériquement les équations physiques (algorithme du gradient global de Todini et Pilati). Ces calculs sont précis mais coûteux lorsqu'ils doivent être répétés un grand nombre de fois, par exemple dans une boucle d'optimisation.

Ce projet s'intéresse à une information précise issue de ces simulations : **le sens d'écoulement de l'eau dans chaque conduite**. La question étudiée est la suivante :

> Dans quelle mesure peut-on retrouver l'orientation des débits d'un réseau d'eau avec des algorithmes de théorie des graphes, sans résoudre les équations hydrauliques de pression et de débit ?

Le programme permet de :

* charger et préparer des réseaux au format EPANET (`.inp`)
* modéliser un réseau sous forme de **graphe orienté symétrique** muni de capacités
* calculer une orientation par **flot maximum** (Ford-Fulkerson, Edmonds-Karp et leurs variantes)
* construire directement une **orientation s-t** (orientation bipolaire, algorithme d'Even et Tarjan)
* comparer chaque orientation à celle obtenue par une simulation EPANET de référence
* lancer des **analyses paramétriques** sur des centaines de réseaux en parallèle et visualiser les résultats

Le cœur algorithmique est écrit en **C** pour la performance. Il est exposé à **Python** via **CFFI**, qui porte l'interface graphique (Tkinter + Matplotlib) et le pipeline d'analyse.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Installation

### Prérequis

* **Linux x86_64** (ou **WSL** sous Windows). Le `Makefile` télécharge la bibliothèque EPANET précompilée pour Linux.
* **Python 3.10+** avec **Tkinter** (`sudo apt install python3-tk` sur Debian/Ubuntu)
* **GCC**, **make**, **curl**, **unzip**
* **Bibliothèques Python** : numpy, matplotlib, cffi, wntr, epyt, jupyter

```bash
pip install -r requirements.txt
```

### Compilation

```bash
make
```

Cette commande :
1. télécharge et décompresse [EPANET 2.3.5](https://github.com/OpenWaterAnalytics/EPANET/releases/tag/v2.3.5) dans `librairie/` s'il n'est pas déjà présent
2. compile les sources C (`structure.c`, `algorithm_flow.c`, `epanet_parser.c`) en bibliothèque partagée `librairie/libreseau.so`
3. génère le module Python `librairie/_reseau_C` via CFFI (`src/build_ffi.py`)

Autres cibles disponibles :

```bash
make clean   # supprime le dossier librairie/ (EPANET compris)
make build   # clean puis recompilation complète
make zip     # archive les sources dans projet_eau.zip
```

> Note : le `Makefile` appelle `python`. Si votre système n'expose que `python3`, utilisez `make PYTHON=python3`.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Utilisation

Le code utilise des imports absolus à partir de la racine du dépôt (`from src.interface.app import ...`). Il faut donc toujours lancer les scripts **depuis la racine**, et **en tant que modules** avec `python -m`, plutôt qu'en appelant directement le chemin du fichier. Lancer un fichier situé dans `src/` par son chemin (`python src/.../fichier.py`) provoque une erreur `ModuleNotFoundError: No module named 'src'`.

Lancement de l'application :

```bash
python -m main
```

Le même principe s'applique à tout autre script du projet. Le chemin du fichier s'écrit avec des points et sans l'extension `.py` :

```bash
python -m src.interface.app                    # au lieu de python src/interface/app.py
python -m src.creation_dataset.prepare_dataset # au lieu de python src/creation_dataset/prepare_dataset.py
```

L'application ouvre un espace de travail dans lequel plusieurs fenêtres internes peuvent coexister. Trois types de fenêtres sont disponibles depuis la barre de menu.

### 1. Visualiser et simuler un réseau

**Fichier → Ouvrir un réseau (.inp)...**

La fenêtre de visualisation affiche le réseau et permet de lancer une simulation sur un seul fichier. Les options du panneau latéral sont :

| Option | Rôle |
|---|---|
| **Algo Principal** | Algorithme de calcul du flot (EPANET, Ford-Fulkerson, Edmonds-Karp et variantes) |
| **Capacité** | Méthode de calcul des capacités des conduites (`Vitesse Max` par défaut) |
| **Orientation** | Orientation imposée au graphe avant le calcul (s-t, DAG, aléatoire, EPANET...) |
| **Demande** | Traitement des demandes (inchangées, aléatoires uniformes, normales, exponentielles, toutes à 1) |
| **Mult. Demande** | Multiplicateur global appliqué aux demandes EPANET |
| **Vit. Rés / Vit. Arcs (m/s)** | Vitesse maximale pour les conduites issues d'un réservoir et pour les autres conduites |
| **Prop. Source / Prop. Demande** | Proportion appliquée aux capacités des arcs reliés à la super source et à la super destination |
| **Portion** | Part des capacités fixées à partir d'EPANET (mode `EPANET Partiel`) |
| **Ecart-Type** | Paramètre des lois de tirage aléatoire des demandes |
| **Seed** | Graine aléatoire pour rendre une exécution reproductible |
| **Tanks comme Réservoirs** | Traite les cuves comme des sources infinies |

Le bouton **SIMULER** lance le calcul. Les arcs et les sommets peuvent être colorés par débit, vitesse, rugosité, différence d'élévation, pression, demande ou satisfaction, avec une classification par intervalles égaux, quantiles ou seuils personnalisés.

### 2. Lancer une analyse paramétrique

**Analyse → Nouvelle fenêtre d'Analyse (Grid Search)...**

C'est l'outil utilisé pour produire les résultats du mémoire. Le principe est de comparer un **modèle de référence** (en général EPANET) à une ou plusieurs **cibles** (les algorithmes évalués), sur un ensemble de réseaux.

1. **Ajouter des réseaux** avec *Ajouter & Préparer Fichier(s)* ou *Ajouter & Préparer Dossier*. Chaque fichier est converti (unités homogènes, mode de simulation PDA ou DDA et paramètres de pression) puis copié dans `prepared_datasets/` sous le nom `prep_<i>_<nom>.inp`. Les fichiers d'origine ne sont jamais modifiés.
2. **Filtrer** si besoin les réseaux contenant des cuves, des pompes, des vannes, ou selon leur nombre de réservoirs.
3. **Configurer la référence** : algorithme, demande, capacité, orientation.
4. **Ajouter des cibles** avec *Cible* (balayage par grille) ou *Cible Itérative*. Chaque paramètre numérique peut être balayé entre un minimum et un maximum avec un nombre de pas donné. Le programme exécute le produit cartésien de toutes les combinaisons.
5. **Choisir le nombre de processus** puis cliquer sur *Lancer l'Analyse*. Les simulations sont réparties entre plusieurs processus (`ProcessPoolExecutor`).
6. **Explorer les résultats** sous forme de nuage de points, histogramme, boîte à moustaches ou carte de chaleur, avec moyennes et médianes en option. Un clic sur un point permet de rouvrir la simulation correspondante dans une fenêtre de visualisation.
7. **Sauvegarder** l'analyse en `.json` pour la rouvrir plus tard via *Analyse → Ouvrir une analyse existante (.json)...*

> Note : une analyse sur un grand nombre de réseaux et de répétitions peut prendre plusieurs heures.

### 3. Profil statistique d'un réseau

**Analyse → Profil Statistique du Réseau actif** (ou bouton *Profil Statistique*)

Affiche les statistiques descriptives du réseau ouvert dans la fenêtre active : répartition des types de sommets et d'arcs, élévations, diamètres, longueurs, demandes, débits, taux de satisfaction des demandes.

### Reproduire les expériences du mémoire

| Expérience | Référence | Cible |
|---|---|---|
| Orientations s-t et témoins | Algo `EPANET` | Algo `Test Orientation` + Orientation `Orientation s-t aleatoire`, `Orientation s-t elevation`, `Orientation DAG aleatoire` ou `Orientation completement aleatoire` |
| Chaînes augmentantes | Algo `EPANET` | Algo `Ford-Fulkerson`, `Ford-Fulkerson_annulation`, `Ford-Fulkerson_elevation`, `Ford-Fulkerson_elevation_annulation`, `Edmonds-Karp` ou `Edmonds-Karp_elevation`, avec Capacité `Vitesse Max` et Vitesse = 3,0 |

Les fichiers sont préparés en mode **PDA**. Les métriques du mémoire correspondent aux colonnes *Mal orientés* (`ratio_inter_ref`) et *Non orientés* (`ratio_nul_tgt_ref`) des résultats d'analyse.

### Préparer un dossier de réseaux en ligne de commande

Le module `src.creation_dataset.prepare_dataset` permet aussi de convertir un dossier complet hors interface. Depuis la racine du dépôt :

```python
from src.creation_dataset.prepare_dataset import convertir_unites_dossier

convertir_unites_dossier("dataset/brut", "dataset/prepare", unite_cible="LPS", mode_simu="PDA", p_min=0.0, p_req=10.0, p_exp=0.5)
```

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Fonctionnement du pipeline

```
 fichier .inp
      │
      ▼
 1. Préparation (wntr)          conversion d'unités, mode PDA/DDA
      │
      ▼
 2. Simulation EPANET (C)       flots de référence
      │
      ▼
 3. Chargement du graphe (C)    graphe orienté symétrique + capacités
      │
      ▼
 4. Algorithme évalué (C)       flot maximum ou orientation s-t
      │
      ▼
 5. Comparaison (Python)        métriques par rapport à EPANET
      │
      ▼
 6. Visualisation / export      graphiques Matplotlib, fichier .json
```

### Modélisation du réseau

**Graphe orienté symétrique.** Chaque conduite `{u, v}` du réseau EPANET devient deux arcs `(u, v)` et `(v, u)`. Les flots sont ainsi toujours positifs, et orienter une conduite revient à désigner lequel des deux arcs porte le flot.

**Capacités.** Un fichier EPANET ne fournit aucune capacité. Elle est déduite du diamètre de la conduite et d'une vitesse maximale d'écoulement $v_{max}$ :

$$c_{ij} = v_{max} \cdot \frac{\pi D_{ij}^2}{4}$$

Les pompes et les vannes reçoivent une capacité infinie, leur débit résultant de l'équilibre hydraulique global et non d'une limite propre.

**Super source et super destination.** Les algorithmes de flot maximum exigent une source et un puits uniques. Deux sommets virtuels sont ajoutés :

* chaque **réservoir** est relié à la super source $s^*$ par un arc de capacité infinie
* chaque **jonction** est reliée à la super destination $t^*$ par un arc de capacité égale à sa demande
* chaque **cuve** est reliée aux deux, avec des capacités déduites de son niveau de remplissage (volume encore stockable et volume restituable sur un pas de temps)

### Algorithmes

| Famille | Option dans l'interface | Principe |
|---|---|---|
| Flot maximum | `Ford-Fulkerson` | Chaînes augmentantes par parcours en profondeur, ordre des voisins aléatoire, réduction des circuits de longueur 2 |
| | `Ford-Fulkerson_annulation` | Idem, avec suppression de tous les circuits du flot par décomposition chemins/circuits |
| | `Edmonds-Karp` | Chaînes augmentantes par parcours en largeur (plus courts chemins). Le flot obtenu est sans circuit |
| | `*_elevation` | Voisins examinés par élévation décroissante au lieu d'un ordre aléatoire |
| Orientation s-t | `Orientation s-t aleatoire` | Numérotation s-t (Even et Tarjan) de pôles $s^*$ et $t^*$, ordre de parcours aléatoire |
| | `Orientation s-t elevation` | Numérotation s-t avec parcours par élévation décroissante |
| Témoins | `Orientation DAG aleatoire` | Permutation aléatoire des sommets, arêtes orientées du plus petit au plus grand rang |
| | `Orientation completement aleatoire` | Chaque arête orientée au hasard, indépendamment |

L'interface propose également des options exploratoires non retenues dans le mémoire : `Pression Statique`, `Orientation Laplace`, `Orientation Elevation Descendante`, `EPANET Partiel`.

### Métriques d'évaluation

Soit $A_{ref}$ l'ensemble des arcs portant le flot dans EPANET, $A_{alg}$ celui de l'algorithme et $N_{alg}$ les arcs des conduites laissées sans flot par l'algorithme.

**Proportion d'arcs mal orientés**

$$p_{err} = \frac{|A_{ref}| - |A_{ref} \cap A_{alg}| - |A_{ref} \cap N_{alg}|}{|A_{ref}|} \times 100$$

**Proportion de conduites sans orientation**

$$p_{nul} = \frac{|E_{nul}|}{|E|} \times 100$$

Les deux métriques doivent être lues ensemble : laisser une conduite sans flot fait mécaniquement baisser $p_{err}$. L'outil calcule aussi d'autres indicateurs (distance de Jaccard, erreurs pondérées sur les débits et les pressions, taux de satisfaction des demandes, coupe minimale).

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Jeux de données

Les réseaux ne sont pas inclus dans ce dépôt.

* **Données réelles** : 28 réseaux issus de la [Water Distribution System Research Database](https://www.uky.edu/WDST/database.html) du Kentucky Water Resources Research Institute (New York Tunnels, Hanoi, Balerma, Net2, réseaux KY...).
* **Données synthétiques** : 198 réseaux générés par **HydroGen** (De Corte et Sörensen, 2014). L'outil n'est plus téléchargeable, mais des jeux générés restent disponibles dans certains dépôts académiques.

Tout fichier au format EPANET `.inp` peut être utilisé.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Structure du projet

```
M2_internship_flow_orientation/
├── main.py                          Point d'entrée de l'application
├── Makefile                         Téléchargement d'EPANET, compilation C, génération CFFI
├── requirements.txt                 Dépendances Python
├── docs/
│   └── memoire.pdf                  Mémoire de stage complet
└── src/
    ├── structure.c / .h             Structures du graphe (sommets, arcs symétriques, réseau)
    ├── epanet_parser.c / .h         Lecture des .inp, simulation EPANET, gestion des demandes
    ├── algorithm_flow.c / .h        Capacités, super source/destination, flots max, orientations
    ├── build_ffi.py                 Génération du module Python _reseau_C
    ├── compile_flags.txt            Flags pour l'analyse statique (clangd)
    ├── backend/
    │   ├── run.py                   Orchestration des simulations et des analyses parallèles
    │   ├── extract_data.py          Extraction des données et calcul des métriques
    │   └── network_profile.py       Statistiques descriptives d'un réseau
    ├── creation_dataset/
    │   └── prepare_dataset.py       Conversion d'unités et de mode de simulation (wntr)
    ├── interface/
    │   ├── app.py                   Fenêtre principale et menus
    │   ├── visualisation.py         Fenêtre de visualisation et de simulation d'un réseau
    │   ├── analyse.py               Fenêtre d'analyse paramétrique (grid search)
    │   └── network_profile_window.py  Fenêtre de profil statistique
    └── wrapper_tools/
        ├── ffi_wrapper.py           Appels aux fonctions C via CFFI
        └── analyse_tools.py         Accès aux données du graphe et métriques de comparaison
```

Dossiers générés à l'exécution :
* `librairie/` : EPANET, `libreseau.so` et le module `_reseau_C` (créé par `make`)
* `prepared_datasets/` : réseaux préparés par la fenêtre d'analyse

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

## Références

Le détail de la modélisation, des preuves et de l'analyse des résultats est dans le [mémoire complet](docs/memoire.pdf).

1. R. K. Ahuja, T. L. Magnanti, J. B. Orlin. *Network Flows: Theory, Algorithms, and Applications*. Prentice Hall, 1993.
2. ASCE Task Committee on Research Databases for Water Distribution Systems. *Water Distribution System Research Database*. Kentucky Water Resources Research Institute, 2016.
3. A. De Corte, K. Sörensen. « HydroGen: an Artificial Water Distribution Network Generator ». *Water Resources Management* 28.2, 2014.
4. J. Edmonds, R. M. Karp. « Theoretical improvements in algorithmic efficiency for network flow problems ». *Journal of the ACM* 19.2, 1972.
5. S. Even, R. E. Tarjan. « Computing an st-numbering ». *Theoretical Computer Science* 2.3, 1976.
6. L. R. Ford, D. R. Fulkerson. « Maximal flow through a network ». *Canadian Journal of Mathematics* 8, 1956.
7. L. A. Rossman et al. *EPANET 2.2 User Manual*. U.S. EPA, 2020.
8. E. Todini, S. Pilati. « A gradient algorithm for the analysis of pipe networks ». *Computer applications in water supply*, 1988.
