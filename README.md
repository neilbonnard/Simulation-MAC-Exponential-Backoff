# Simulation MAC — Exponential Backoff

Simulation par événements discrets d'un protocole MAC avec algorithme d'Exponential Backoff.

**Auteur :** Neil Bonnard — 22505907 x Amine Ben Elmahdi - 22503866

---

## Structure du projet

```
.
├── main/
│   ├── mac_simulateur.py    # Simulateur principal
│   ├── experiments.py       # Génération des courbes et données
│   ├── generate_report.py   # Génération du rapport PDF
│   └── Experiments.ipynb    # Notebook Jupyter interactif
├── figures/                 # Courbes PNG et données numériques (générés)
├── rapport_MAC_Exponential_Backoff.pdf  # Rapport (généré)
└── README.md
```

---

## Utilisation

### 1. Générer les courbes

```bash
python3 main/experiments.py
```

Génère 8 figures dans `figures/` et les données numériques associées (`.npy`, `.json`).
Durée : ~3-5 minutes (15 runs × 13 valeurs de λ + 13 valeurs de N).

### 2. Générer le rapport PDF

```bash
python3 main/generate_report.py
```

Produit `rapport_MAC_Exponential_Backoff.pdf` à la racine du projet.
Nécessite que `experiments.py` ait été exécuté au préalable.

### 3. Utiliser le simulateur directement

```python
from main.mac_simulateur import simulate
import numpy as np

np.random.seed(42)
result = simulate(N=5, lam=0.5, K=10, tau=1.0, T_max=5000)

print(len(result['successes']))   # nombre de transmissions réussies
print(result['drops'])            # paquets perdus (file pleine)
print(result['collisions'])       # nombre de collisions
```

---

## Paramètres de `simulate()`

| Paramètre           | Type  | Description                                      |
|---------------------|-------|--------------------------------------------------|
| `N`                 | int   | Nombre de stations                               |
| `lam`               | float | Taux d'arrivée par station (loi exponentielle)   |
| `K`                 | int   | Capacité de la file d'attente par station        |
| `tau`               | float | Paramètre de base du backoff                     |
| `T_max`             | float | Durée de la simulation                           |
| `snapshot_interval` | float | Intervalle entre snapshots du nb de clients (défaut: 1.0) |

### Valeur de retour

```python
{
    "successes":       [(t, station), ...],  # transmissions réussies avec timestamp
    "drops":           int,                  # paquets perdus (file pleine)
    "collisions":      int,                  # nombre de collisions
    "queue_snapshots": [(t, total_queue), ...],  # évolution du nb de clients
    "T_max":           float
}
```

---

## Dépendances

```
numpy
matplotlib
scipy
seaborn
reportlab
```

Installation :
```bash
pip install numpy matplotlib scipy seaborn reportlab
```

---

## Modèle

- **N** stations partagent un canal unique
- Arrivées selon un processus de Poisson de taux **λ** par station
- File d'attente de capacité **K** par station
- Durée d'émission = **1 unité de temps** (déterministe)
- En cas de collision, backoff ~ **Exp(2^i × τ)** où i est l'état de la station
- État de backoff borné à **MAX_STATE = 10** (standard 802.11)
- Succès → retour à l'état 1
