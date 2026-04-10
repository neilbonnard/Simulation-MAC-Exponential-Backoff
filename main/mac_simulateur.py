import random as rd
import seaborn as sns
import numpy as np
from heapq import heappush, heappop

def exp_lambda(λ):      #Fonction pour generer temps random selon la loi exponentielle de paramètre λ
    return np.random.exponential(1 / λ)   

def backoff(i, tau):    #Fonction pour generer temps random selon la loi exponentielle de paramètre (2^i)*tau
    return np.random.exponential((2**i) * tau)  
  

def simulate(N, lam, K, tau, T_max):

    echeancier = []
    t = 0
    stations = []
    reussis = []
    canal_libre = True
    log = []

    for i in range(N):      #Initialisation des stations a l'état 1 et pas de paquets dans la file d'attente
        stations.append({"queue_len": 0,
            "state" : 1,
            "attempt_scheduled" : False,
            "is_attempting" : False,
            "end_valid": False})
    
    for i in range(N):      #Initialisation de l'echeancier avec les evenements d'arrivee des paquets a chaque station
        t_arrival = exp_lambda(lam)
        heappush(echeancier, (t_arrival, "ARRIVAL", i))


    while t < T_max: 

        evt = heappop(echeancier)     #Recuperation de l'evenement le plus proche
        t = evt[0]
        station = evt[2]
        match evt[1]:
            case "ARRIVAL":   #Si c'est un evenement d'arrivee de paquet
                t_arrival = t + exp_lambda(lam)
                heappush(echeancier, (t_arrival, "ARRIVAL", station))

                if stations[station]["queue_len"] < K:
                    stations[station]["queue_len"] += 1

                if stations[station]["queue_len"] == 1 and not stations[station]["attempt_scheduled"] and not stations[station]["is_attempting"]:
                    heappush(echeancier, (t, "ATTEMPT", station))
                    stations[station]["attempt_scheduled"] = True
                

            case "ATTEMPT":   #Si c'est un la station essaye d'envoyer un paquet

                if canal_libre:
                    heappush(echeancier, (t+1, "END_TX", station))
                    canal_libre = False
                    stations[station]["is_attempting"] = True
                    stations[station]["end_valid"] = True
                    heappush(log, (t, station, "ATTEMPT"))

                else: 
                    stations[station]["is_attempting"] = False
                    stations[station]["attempt_scheduled"] = True
                    stations[station]["state"] += 1
                    t_backoff = t + backoff(stations[station]["state"], tau)
                    heappush(echeancier, (t_backoff, "ATTEMPT", station))
                    for i in range(N):
                        if i != station and stations[i]["is_attempting"]:
                            r = i
                            stations[i]["is_attempting"] = False
                            stations[i]["attempt_scheduled"] = True
                            stations[i]["state"] += 1
                            t_backoff_i = t + backoff(stations[i]["state"], tau)
                            heappush(echeancier, (t_backoff_i, "ATTEMPT", i))
                            stations[i]["end_valid"] = False

                    heappush(log, (t, station, "COLLISION", r))   #On ajoute l'evenement de collision au log
                    canal_libre = True


            case "END_TX":    #Si un envoi de paquet est terminer
                if stations[station]["end_valid"]:   
                    stations[station]["state"] = 1  #On remet la station a l'etat de base
                    stations[station]["queue_len"] -= 1
                    reussis.append((station, t))   #On ajoute le paquet a la liste des paquets reussis avec le temps d'arrivee du paquet
                    canal_libre = True
                    stations[station]["is_attempting"] = False
                    stations[station]["attempt_scheduled"] = False
                    if stations[station]["queue_len"] > 0:   #Si il y a encore des paquets dans la file d'attente de la station, on programme un nouvel attempt
                        heappush(echeancier, (t, "ATTEMPT", station))
                        stations[station]["attempt_scheduled"] = True
                    heappush(log, (t, station, "END_TX"))

    return log