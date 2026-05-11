"""
Expériences et génération des courbes pour le rapport MAC Exponential Backoff.
Génère tous les graphiques dans le dossier figures/.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from mac_simulateur import simulate

# ── Répertoire de sortie ──────────────────────────────────────────────────────
FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

def fig_path(name):
    return os.path.join(FIGURES_DIR, name)

# ── Style global ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "lines.linewidth": 1.8,
    "grid.alpha": 0.35,
})

SEED = 2025

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def throughput_curve(successes, T_max, dt=1.0):
    """Retourne (times, throughput) où throughput[i] = n(t_i) / t_i."""
    times = np.arange(dt, T_max + dt, dt)
    n = np.array([sum(1 for s, _ in successes if s <= t) for t in times])
    return times, n / times


def mean_queue_curve(queue_snapshots):
    """Retourne (times, mean_queue) depuis les snapshots."""
    if not queue_snapshots:
        return np.array([]), np.array([])
    ts, qs = zip(*queue_snapshots)
    return np.array(ts), np.array(qs, dtype=float)


def steady_state_throughput(successes, T_max, warmup=0.2):
    """Débit moyen en régime permanent (ignore les warmup% premiers instants)."""
    t_start = warmup * T_max
    count = sum(1 for t, _ in successes if t >= t_start)
    return count / (T_max * (1 - warmup))


def run_multiple(N, lam, K, tau, T_max, n_runs=10, seed=SEED):
    """Lance n_runs simulations indépendantes, retourne liste de résultats."""
    results = []
    for i in range(n_runs):
        np.random.seed(seed + i)
        results.append(simulate(N, lam, K, tau, T_max))
    return results


def confidence_interval_95(values):
    """Retourne (mean, half_width_95) pour un IC à 95%."""
    from scipy import stats
    arr = np.array(values)
    n = len(arr)
    mean = arr.mean()
    se = stats.sem(arr)
    h = se * stats.t.ppf(0.975, df=n - 1)
    return mean, h


# ─────────────────────────────────────────────────────────────────────────────
# Paramètres de référence
# ─────────────────────────────────────────────────────────────────────────────
N_REF   = 5
LAM_REF = 0.5
K_REF   = 10
TAU_REF = 1.0
T_MAX   = 5000
N_RUNS  = 15   # runs pour les courbes statistiques


# ═════════════════════════════════════════════════════════════════════════════
# Figure 1 : Débit n(t)/t en fonction du temps
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 1 : débit n(t)/t ...")

np.random.seed(SEED)
res_ref = simulate(N_REF, LAM_REF, K_REF, TAU_REF, T_MAX, snapshot_interval=1.0)

times_th, th_curve = throughput_curve(res_ref["successes"], T_MAX, dt=5.0)
d_steady = steady_state_throughput(res_ref["successes"], T_MAX)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(times_th, th_curve, color="#2563eb", lw=1.5, label="n(t)/t")
ax.axhline(d_steady, color="#dc2626", ls="--", lw=1.4,
           label=f"d(N,K,λ,τ) ≈ {d_steady:.4f}")
ax.set_xlabel("Temps t")
ax.set_ylabel("Débit n(t)/t")
ax.set_title(f"Débit instantané n(t)/t  —  N={N_REF}, λ={LAM_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig1_throughput_vs_time.png"))
plt.close(fig)
print(f"  d_steady = {d_steady:.4f}")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 2 : Nombre moyen de clients dans le système
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 2 : nombre moyen de clients ...")

snap_t, snap_q = mean_queue_curve(res_ref["queue_snapshots"])

# Moyenne glissante sur 50 points pour lisser
window = 50
if len(snap_q) >= window:
    kernel = np.ones(window) / window
    snap_q_smooth = np.convolve(snap_q, kernel, mode="same")
else:
    snap_q_smooth = snap_q

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(snap_t, snap_q, color="#94a3b8", lw=0.8, alpha=0.5, label="Brut")
ax.plot(snap_t, snap_q_smooth, color="#7c3aed", lw=1.8, label=f"Moyenne glissante ({window} pts)")
mean_q = snap_q[int(0.2 * len(snap_q)):].mean()
ax.axhline(mean_q, color="#dc2626", ls="--", lw=1.4,
           label=f"Moyenne régime permanent ≈ {mean_q:.2f}")
ax.set_xlabel("Temps t")
ax.set_ylabel("Nombre total de paquets en file")
ax.set_title(f"Évolution du nombre de clients  —  N={N_REF}, λ={LAM_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig2_queue_vs_time.png"))
plt.close(fig)
print(f"  mean_queue (régime permanent) = {mean_q:.2f}")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 3 : Taux de paquets perdus (file pleine) en fonction du temps
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 3 : taux de paquets perdus ...")

# On relance avec comptage des arrivées totales
np.random.seed(SEED)

def simulate_with_arrivals(N, lam, K, tau, T_max, snapshot_interval=1.0):
    """Variante qui compte aussi les arrivées totales par intervalle."""
    from heapq import heappush, heappop
    from mac_simulateur import exp_lambda, backoff, MAX_STATE

    echeancier = []
    t = 0.0
    stations = [
        {"queue_len": 0, "state": 1, "attempt_scheduled": False,
         "is_attempting": False, "end_valid": False}
        for _ in range(N)
    ]
    canal_libre = True
    successes = []
    drops_timeline = []   # (t) pour chaque drop
    arrivals_timeline = []

    for i in range(N):
        heappush(echeancier, (exp_lambda(lam), "ARRIVAL", i))

    while echeancier:
        evt = heappop(echeancier)
        t = evt[0]
        if t > T_max:
            break
        evtype, station = evt[1], evt[2]

        if evtype == "ARRIVAL":
            heappush(echeancier, (t + exp_lambda(lam), "ARRIVAL", station))
            arrivals_timeline.append(t)
            if stations[station]["queue_len"] < K:
                stations[station]["queue_len"] += 1
            else:
                drops_timeline.append(t)
            if (stations[station]["queue_len"] == 1
                    and not stations[station]["attempt_scheduled"]
                    and not stations[station]["is_attempting"]):
                heappush(echeancier, (t, "ATTEMPT", station))
                stations[station]["attempt_scheduled"] = True

        elif evtype == "ATTEMPT":
            stations[station]["attempt_scheduled"] = False
            if canal_libre:
                heappush(echeancier, (t + 1.0, "END_TX", station))
                canal_libre = False
                stations[station]["is_attempting"] = True
                stations[station]["end_valid"] = True
            else:
                stations[station]["is_attempting"] = False
                stations[station]["state"] = min(stations[station]["state"] + 1, MAX_STATE)
                heappush(echeancier, (t + backoff(stations[station]["state"], tau), "ATTEMPT", station))
                stations[station]["attempt_scheduled"] = True
                for i in range(N):
                    if i != station and stations[i]["is_attempting"]:
                        stations[i]["is_attempting"] = False
                        stations[i]["end_valid"] = False
                        stations[i]["state"] = min(stations[i]["state"] + 1, MAX_STATE)
                        heappush(echeancier, (t + backoff(stations[i]["state"], tau), "ATTEMPT", i))
                        stations[i]["attempt_scheduled"] = True
                canal_libre = True

        elif evtype == "END_TX":
            if stations[station]["end_valid"]:
                successes.append((t, station))
                stations[station]["state"] = 1
                stations[station]["queue_len"] -= 1
                canal_libre = True
                stations[station]["is_attempting"] = False
                stations[station]["attempt_scheduled"] = False
                if stations[station]["queue_len"] > 0:
                    heappush(echeancier, (t, "ATTEMPT", station))
                    stations[station]["attempt_scheduled"] = True
            else:
                stations[station]["is_attempting"] = False

    return arrivals_timeline, drops_timeline

arrivals_tl, drops_tl = simulate_with_arrivals(N_REF, LAM_REF, K_REF, TAU_REF, T_MAX)

# Taux de perte cumulé
dt = 20.0
bins = np.arange(0, T_MAX + dt, dt)
arr_hist, _ = np.histogram(arrivals_tl, bins=bins)
drop_hist, _ = np.histogram(drops_tl, bins=bins)
loss_rate = np.where(arr_hist > 0, drop_hist / arr_hist, 0.0)
bin_centers = (bins[:-1] + bins[1:]) / 2

# Lissage
if len(loss_rate) >= 20:
    k = np.ones(20) / 20
    loss_smooth = np.convolve(loss_rate, k, mode="same")
else:
    loss_smooth = loss_rate

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(bin_centers, loss_rate, color="#94a3b8", lw=0.8, alpha=0.5, label="Brut")
ax.plot(bin_centers, loss_smooth, color="#ea580c", lw=1.8, label="Moyenne glissante")
mean_loss = loss_rate[int(0.2 * len(loss_rate)):].mean()
ax.axhline(mean_loss, color="#dc2626", ls="--", lw=1.4,
           label=f"Taux moyen ≈ {mean_loss:.3f}")
ax.set_xlabel("Temps t")
ax.set_ylabel("Taux de perte (paquets perdus / arrivées)")
ax.set_title(f"Taux de paquets perdus (file pleine)  —  N={N_REF}, λ={LAM_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig3_loss_rate_vs_time.png"))
plt.close(fig)
print(f"  taux de perte moyen = {mean_loss:.4f}")


# ═════════════════════════════════════════════════════════════════════════════
# Figure 4 : d(N,K,λ,τ) en fonction de λ
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 4 : débit vs λ ...")

lam_values = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0]
d_lam_mean = []
d_lam_ci   = []

for lam in lam_values:
    runs = run_multiple(N_REF, lam, K_REF, TAU_REF, T_MAX, n_runs=N_RUNS)
    ds = [steady_state_throughput(r["successes"], T_MAX) for r in runs]
    m, h = confidence_interval_95(ds)
    d_lam_mean.append(m)
    d_lam_ci.append(h)
    print(f"  λ={lam:.2f}  d={m:.4f} ± {h:.4f}")

d_lam_mean = np.array(d_lam_mean)
d_lam_ci   = np.array(d_lam_ci)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(lam_values, d_lam_mean, "o-", color="#2563eb", label="d(N,K,λ,τ)")
ax.fill_between(lam_values,
                d_lam_mean - d_lam_ci,
                d_lam_mean + d_lam_ci,
                alpha=0.2, color="#2563eb", label="IC 95%")
ax.set_xlabel("λ (taux d'arrivée par station)")
ax.set_ylabel("Débit d(N,K,λ,τ)")
ax.set_title(f"Débit en régime permanent vs λ  —  N={N_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig4_throughput_vs_lambda.png"))
plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# Figure 5 : d(N,K,λ,τ) en fonction de N
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 5 : débit vs N ...")

N_values = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30]
d_N_mean = []
d_N_ci   = []

for N in N_values:
    runs = run_multiple(N, LAM_REF, K_REF, TAU_REF, T_MAX, n_runs=N_RUNS)
    ds = [steady_state_throughput(r["successes"], T_MAX) for r in runs]
    m, h = confidence_interval_95(ds)
    d_N_mean.append(m)
    d_N_ci.append(h)
    print(f"  N={N:2d}  d={m:.4f} ± {h:.4f}")

d_N_mean = np.array(d_N_mean)
d_N_ci   = np.array(d_N_ci)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(N_values, d_N_mean, "s-", color="#7c3aed", label="d(N,K,λ,τ)")
ax.fill_between(N_values,
                d_N_mean - d_N_ci,
                d_N_mean + d_N_ci,
                alpha=0.2, color="#7c3aed", label="IC 95%")
ax.set_xlabel("N (nombre de stations)")
ax.set_ylabel("Débit d(N,K,λ,τ)")
ax.set_title(f"Débit en régime permanent vs N  —  λ={LAM_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig5_throughput_vs_N.png"))
plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# Figure 6 : N optimal avec IC 95%
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 6 : N optimal ...")

# Zoom sur la zone intéressante
N_zoom = list(range(1, 21))
d_zoom_mean = []
d_zoom_ci   = []

for N in N_zoom:
    runs = run_multiple(N, LAM_REF, K_REF, TAU_REF, T_MAX, n_runs=N_RUNS)
    ds = [steady_state_throughput(r["successes"], T_MAX) for r in runs]
    m, h = confidence_interval_95(ds)
    d_zoom_mean.append(m)
    d_zoom_ci.append(h)

d_zoom_mean = np.array(d_zoom_mean)
d_zoom_ci   = np.array(d_zoom_ci)

# N optimal = argmax du débit moyen
N_opt_idx = int(np.argmax(d_zoom_mean))
N_opt = N_zoom[N_opt_idx]
d_opt = d_zoom_mean[N_opt_idx]
ci_opt = d_zoom_ci[N_opt_idx]
print(f"  N optimal = {N_opt}  d = {d_opt:.4f} ± {ci_opt:.4f}  (IC 95%)")

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(N_zoom, d_zoom_mean, color="#94a3b8", alpha=0.6, label="Débit moyen")
ax.errorbar(N_zoom, d_zoom_mean, yerr=d_zoom_ci,
            fmt="none", color="#1e293b", capsize=4, lw=1.2, label="IC 95%")
ax.bar(N_opt, d_opt, color="#2563eb", alpha=0.9, label=f"N optimal = {N_opt}")
ax.set_xlabel("N (nombre de stations)")
ax.set_ylabel("Débit d(N,K,λ,τ)")
ax.set_title(f"N optimal maximisant le débit  —  λ={LAM_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True, axis="y")
fig.tight_layout()
fig.savefig(fig_path("fig6_N_optimal.png"))
plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# Figure 7 : Validation théorique — cas N=1 (pas de collision)
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 7 : validation théorique N=1 ...")

# Avec N=1, K=∞ (grand K), pas de collision possible.
# Le système est une file M/D/1 : arrivées Poisson(λ), service déterministe = 1.
# Débit théorique = min(λ, 1) car le canal a capacité 1 paquet/unité de temps.
# Pour λ < 1 : débit = λ (tout passe, pas de saturation)
# Pour λ >= 1 : débit → 1 (canal saturé)

lam_val_th = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0, 1.2, 1.5, 2.0, 3.0]
d_th = [min(l, 1.0) for l in lam_val_th]

d_sim_n1 = []
d_sim_n1_ci = []
for lam in lam_val_th:
    runs = run_multiple(1, lam, 1000, TAU_REF, T_MAX, n_runs=N_RUNS)
    ds = [steady_state_throughput(r["successes"], T_MAX) for r in runs]
    m, h = confidence_interval_95(ds)
    d_sim_n1.append(m)
    d_sim_n1_ci.append(h)
    print(f"  N=1 λ={lam:.1f}  sim={m:.4f}±{h:.4f}  théo={min(lam,1):.4f}")

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(lam_val_th, d_th, "k--", lw=2, label="Théorique min(λ, 1)")
ax.errorbar(lam_val_th, d_sim_n1, yerr=d_sim_n1_ci,
            fmt="o-", color="#16a34a", capsize=4, label="Simulation (N=1)")
ax.set_xlabel("λ")
ax.set_ylabel("Débit")
ax.set_title("Validation : N=1, K=1000 — comparaison simulation vs théorie")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig7_validation_N1.png"))
plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# Figure 8 : Taux de collision vs λ
# ═════════════════════════════════════════════════════════════════════════════
print("Figure 8 : taux de collision vs λ ...")

col_rates = []
col_ci    = []
for lam in lam_values:
    runs = run_multiple(N_REF, lam, K_REF, TAU_REF, T_MAX, n_runs=N_RUNS)
    # taux = collisions / (successes + collisions)
    rates = []
    for r in runs:
        total = len(r["successes"]) + r["collisions"]
        rates.append(r["collisions"] / total if total > 0 else 0)
    m, h = confidence_interval_95(rates)
    col_rates.append(m)
    col_ci.append(h)

col_rates = np.array(col_rates)
col_ci    = np.array(col_ci)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(lam_values, col_rates, "^-", color="#dc2626", label="Taux de collision")
ax.fill_between(lam_values,
                col_rates - col_ci,
                col_rates + col_ci,
                alpha=0.2, color="#dc2626", label="IC 95%")
ax.set_xlabel("λ (taux d'arrivée par station)")
ax.set_ylabel("Taux de collision")
ax.set_title(f"Taux de collision vs λ  —  N={N_REF}, K={K_REF}, τ={TAU_REF}")
ax.legend()
ax.grid(True)
fig.tight_layout()
fig.savefig(fig_path("fig8_collision_rate_vs_lambda.png"))
plt.close(fig)


# ═════════════════════════════════════════════════════════════════════════════
# Résumé des résultats pour le rapport
# ═════════════════════════════════════════════════════════════════════════════
print("\n=== RÉSUMÉ ===")
print(f"Paramètres de référence : N={N_REF}, λ={LAM_REF}, K={K_REF}, τ={TAU_REF}, T_max={T_MAX}")
print(f"Débit régime permanent  : {d_steady:.4f} paquets/unité de temps")
print(f"Nombre moyen de clients : {mean_q:.2f}")
print(f"Taux de perte moyen     : {mean_loss:.4f}")
print(f"N optimal               : {N_opt}  (d={d_opt:.4f} ± {ci_opt:.4f}, IC 95%)")
print(f"\nFigures sauvegardées dans : {os.path.abspath(FIGURES_DIR)}")

# Sauvegarder les données numériques pour le rapport
np.save(fig_path("data_lam_values.npy"), np.array(lam_values))
np.save(fig_path("data_d_lam_mean.npy"), d_lam_mean)
np.save(fig_path("data_d_lam_ci.npy"), d_lam_ci)
np.save(fig_path("data_N_values.npy"), np.array(N_values))
np.save(fig_path("data_d_N_mean.npy"), d_N_mean)
np.save(fig_path("data_d_N_ci.npy"), d_N_ci)
np.save(fig_path("data_N_zoom.npy"), np.array(N_zoom))
np.save(fig_path("data_d_zoom_mean.npy"), d_zoom_mean)
np.save(fig_path("data_d_zoom_ci.npy"), d_zoom_ci)

# Sauvegarder les scalaires
scalars = {
    "d_steady": d_steady,
    "mean_q": mean_q,
    "mean_loss": mean_loss,
    "N_opt": N_opt,
    "d_opt": d_opt,
    "ci_opt": ci_opt,
    "N_REF": N_REF,
    "LAM_REF": LAM_REF,
    "K_REF": K_REF,
    "TAU_REF": TAU_REF,
    "T_MAX": T_MAX,
    "N_RUNS": N_RUNS,
}
import json
with open(fig_path("scalars.json"), "w") as f:
    json.dump(scalars, f, indent=2)

print("Données sauvegardées.")
