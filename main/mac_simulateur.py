"""
Simulateur MAC - Exponential Backoff
Simulation par événements discrets d'un protocole MAC avec backoff exponentiel.

Paramètres:
    N    : nombre de stations
    lam  : taux d'arrivée des paquets par station (loi exponentielle de paramètre λ)
    K    : capacité de la file d'attente de chaque station
    tau  : paramètre de base du backoff (moyenne du backoff au 1er retry = 2*tau)
    T_max: durée de la simulation

Événements:
    ARRIVAL  : arrivée d'un paquet à une station
    ATTEMPT  : tentative d'émission d'un paquet sur le canal
    END_TX   : fin d'une émission (succès ou collision détectée)

Variables d'état:
    stations : liste de dicts décrivant l'état de chaque station
               - queue_len       : nombre de paquets en attente
               - state           : état de backoff (commence à 1, +1 à chaque collision)
               - attempt_scheduled: True si un ATTEMPT est déjà dans l'écheancier
               - is_attempting   : True si la station est en train d'émettre
               - end_valid       : True si l'émission en cours n'a pas été invalidée
    canal_libre: booléen indiquant si le canal est disponible

Retour de simulate():
    dict avec:
        - successes     : liste de (t, station) pour chaque paquet transmis avec succès
        - drops         : nombre de paquets perdus (file pleine)
        - collisions    : nombre de collisions détectées
        - queue_snapshots: liste de (t, queue_total) pour suivre le nb moyen de clients
"""

import numpy as np
from heapq import heappush, heappop

MAX_STATE = 10  # borne max sur l'état de backoff (standard 802.11)


def exp_lambda(lam):
    """Génère un temps aléatoire selon la loi exponentielle de paramètre λ."""
    return np.random.exponential(1.0 / lam)


def backoff(state, tau):
    """
    Génère un temps de backoff aléatoire selon la loi exponentielle
    de paramètre 1 / (2^state * tau), donc de moyenne 2^state * tau.
    """
    return np.random.exponential((2 ** state) * tau)


def simulate(N, lam, K, tau, T_max, snapshot_interval=1.0):
    """
    Lance la simulation par événements discrets.

    Args:
        N                : nombre de stations
        lam              : taux d'arrivée par station
        K                : capacité de la file d'attente
        tau              : paramètre de base du backoff
        T_max            : durée de la simulation
        snapshot_interval: intervalle de temps entre deux snapshots du nb de clients

    Returns:
        dict avec successes, drops, collisions, queue_snapshots, T_max
    """
    echeancier = []
    t = 0.0

    # État de chaque station
    stations = [
        {
            "queue_len": 0,
            "state": 1,
            "attempt_scheduled": False,
            "is_attempting": False,
            "end_valid": False,
        }
        for _ in range(N)
    ]

    canal_libre = True

    # Résultats
    successes = []          # (t, station) à chaque transmission réussie
    drops = 0               # paquets perdus (file pleine)
    collision_count = 0     # nombre de collisions
    queue_snapshots = []    # (t, queue_total) pour le nb moyen de clients

    # Initialisation : premier ARRIVAL pour chaque station
    for i in range(N):
        heappush(echeancier, (exp_lambda(lam), "ARRIVAL", i))

    # Prochain snapshot
    next_snapshot = snapshot_interval

    while echeancier:
        evt = heappop(echeancier)
        t = evt[0]

        if t > T_max:
            break

        # Snapshots du nombre total de clients dans le système
        while next_snapshot <= t:
            total_q = sum(s["queue_len"] for s in stations)
            queue_snapshots.append((next_snapshot, total_q))
            next_snapshot += snapshot_interval

        evtype = evt[1]
        station = evt[2]

        # ------------------------------------------------------------------ #
        #  ARRIVAL : arrivée d'un paquet à la station                         #
        # ------------------------------------------------------------------ #
        if evtype == "ARRIVAL":
            # Planifier la prochaine arrivée
            heappush(echeancier, (t + exp_lambda(lam), "ARRIVAL", station))

            if stations[station]["queue_len"] < K:
                stations[station]["queue_len"] += 1
            else:
                drops += 1  # file pleine → paquet perdu

            # Si la station vient de recevoir son 1er paquet et n'est pas
            # déjà en train d'émettre ou d'attendre un ATTEMPT
            if (
                stations[station]["queue_len"] == 1
                and not stations[station]["attempt_scheduled"]
                and not stations[station]["is_attempting"]
            ):
                heappush(echeancier, (t, "ATTEMPT", station))
                stations[station]["attempt_scheduled"] = True

        # ------------------------------------------------------------------ #
        #  ATTEMPT : la station tente d'émettre                               #
        # ------------------------------------------------------------------ #
        elif evtype == "ATTEMPT":
            stations[station]["attempt_scheduled"] = False  # l'ATTEMPT est consommé

            if canal_libre:
                # Canal libre → début de transmission
                heappush(echeancier, (t + 1.0, "END_TX", station))
                canal_libre = False
                stations[station]["is_attempting"] = True
                stations[station]["end_valid"] = True

            else:
                # Canal occupé → collision
                collision_count += 1

                # Backoff pour la station qui vient d'arriver
                stations[station]["is_attempting"] = False
                stations[station]["state"] = min(stations[station]["state"] + 1, MAX_STATE)
                t_bo = t + backoff(stations[station]["state"], tau)
                heappush(echeancier, (t_bo, "ATTEMPT", station))
                stations[station]["attempt_scheduled"] = True

                # Backoff pour la station qui était déjà en train d'émettre
                for i in range(N):
                    if i != station and stations[i]["is_attempting"]:
                        stations[i]["is_attempting"] = False
                        stations[i]["end_valid"] = False
                        stations[i]["state"] = min(stations[i]["state"] + 1, MAX_STATE)
                        t_bo_i = t + backoff(stations[i]["state"], tau)
                        heappush(echeancier, (t_bo_i, "ATTEMPT", i))
                        stations[i]["attempt_scheduled"] = True

                canal_libre = True  # canal libéré après collision

        # ------------------------------------------------------------------ #
        #  END_TX : fin d'une émission                                         #
        # ------------------------------------------------------------------ #
        elif evtype == "END_TX":
            if stations[station]["end_valid"]:
                # Transmission réussie
                successes.append((t, station))
                stations[station]["state"] = 1
                stations[station]["queue_len"] -= 1
                canal_libre = True
                stations[station]["is_attempting"] = False
                stations[station]["attempt_scheduled"] = False

                # S'il reste des paquets, planifier le prochain ATTEMPT
                if stations[station]["queue_len"] > 0:
                    heappush(echeancier, (t, "ATTEMPT", station))
                    stations[station]["attempt_scheduled"] = True
            else:
                # Transmission invalidée par une collision détectée pendant l'émission
                # Le canal a déjà été libéré dans le handler ATTEMPT/collision
                stations[station]["is_attempting"] = False

    return {
        "successes": successes,
        "drops": drops,
        "collisions": collision_count,
        "queue_snapshots": queue_snapshots,
        "T_max": T_max,
    }
