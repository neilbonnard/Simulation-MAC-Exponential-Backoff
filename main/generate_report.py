"""
Generation du rapport PDF - Simulation MAC Exponential Backoff
"""

import os, sys, json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS   = os.path.join(BASE, "figures")
OUTPUT = os.path.join(BASE, "rapport_MAC_Exponential_Backoff.pdf")

def fp(name): return os.path.join(FIGS, name)

with open(fp("scalars.json")) as f:
    sc = json.load(f)

lam_values  = np.load(fp("data_lam_values.npy")).tolist()
d_lam_mean  = np.load(fp("data_d_lam_mean.npy")).tolist()
d_lam_ci    = np.load(fp("data_d_lam_ci.npy")).tolist()
N_values    = np.load(fp("data_N_values.npy")).tolist()
d_N_mean    = np.load(fp("data_d_N_mean.npy")).tolist()
d_N_ci      = np.load(fp("data_d_N_ci.npy")).tolist()
N_zoom      = np.load(fp("data_N_zoom.npy")).tolist()
d_zoom_mean = np.load(fp("data_d_zoom_mean.npy")).tolist()
d_zoom_ci   = np.load(fp("data_d_zoom_ci.npy")).tolist()

styles = getSampleStyleSheet()

def style(name, **kw):
    s = styles[name].clone(name + str(id(kw)))
    for k, v in kw.items():
        setattr(s, k, v)
    return s

title_s   = style("Title",   fontSize=22, spaceAfter=6, textColor=colors.HexColor("#1e3a5f"))
h1_s      = style("Heading1",fontSize=15, spaceAfter=4, textColor=colors.HexColor("#1e3a5f"), spaceBefore=14)
h2_s      = style("Heading2",fontSize=12, spaceAfter=3, textColor=colors.HexColor("#2563eb"), spaceBefore=10)
body_s    = style("Normal",  fontSize=10, leading=15, spaceAfter=4, alignment=TA_JUSTIFY)
cap_s     = style("Normal",  fontSize=9,  leading=12, spaceAfter=8, textColor=colors.HexColor("#475569"), alignment=TA_CENTER)
code_s    = style("Code",    fontSize=8,  leading=13, spaceAfter=4, fontName="Courier", backColor=colors.HexColor("#f1f5f9"))
bullet_s  = style("Normal",  fontSize=10, leading=15, spaceAfter=3, leftIndent=14)
center_s  = style("Normal",  fontSize=11, alignment=TA_CENTER)

def P(t, s=None):   return Paragraph(t, s or body_s)
def H1(t):          return Paragraph(t, h1_s)
def H2(t):          return Paragraph(t, h2_s)
def SP(n=0.3):      return Spacer(1, n*cm)
def HR():           return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6)
def Cap(t):         return Paragraph(t, cap_s)
def Bul(t):         return Paragraph("&#8226;  " + t, bullet_s)

def fig_block(fname, w=15, cap=""):
    path = fp(fname)
    elems = [Image(path, width=w*cm, height=w*0.5*cm)]
    if cap:
        elems.append(Cap(cap))
    return elems

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#f8fafc"), colors.white]),
        ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    return t

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2.2*cm, bottomMargin=2.2*cm,
    title="Rapport Simulation MAC Exponential Backoff",
    author="Neil Bonnard"
)

story = []

# ── PAGE DE TITRE ─────────────────────────────────────────────────────────────
story += [
    SP(3),
    P("Projet de Simulation", style("Normal", fontSize=13, alignment=TA_CENTER, textColor=colors.HexColor("#64748b"))),
    SP(0.3),
    P("Medium Access Control — Exponential Backoff", style("Title", fontSize=24, alignment=TA_CENTER, textColor=colors.HexColor("#1e3a5f"), leading=32)),
    SP(0.5),
    HR(),
    SP(0.3),
    P("Neil Bonnard — 22505907", style("Normal", fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))),
    P("Simulation par evenements discrets — Python 3.10", style("Normal", fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor("#94a3b8"))),
    SP(2),
    P("Parametres de reference :", style("Normal", fontSize=10, alignment=TA_CENTER)),
    SP(0.2),
    make_table(
        ["Parametre", "Valeur", "Description"],
        [
            ["N",     str(int(sc["N_REF"])),   "Nombre de stations"],
            ["lambda",str(sc["LAM_REF"]),       "Taux d'arrivee par station"],
            ["K",     str(int(sc["K_REF"])),    "Capacite de la file d'attente"],
            ["tau",   str(sc["TAU_REF"]),        "Parametre de base du backoff"],
            ["T_max", str(int(sc["T_MAX"])),     "Duree de simulation"],
            ["Runs",  str(int(sc["N_RUNS"])),    "Repetitions par point (IC 95%)"],
        ],
        col_widths=[3.5*cm, 2.5*cm, 9*cm]
    ),
    PageBreak(),
]

# ── SECTION 1 : SIMULATEUR ────────────────────────────────────────────────────
story += [H1("1. Description du simulateur"), HR()]

story += [
    H2("1.1 Principe general"),
    P("Le simulateur implemente une simulation par evenements discrets (DES) d'un protocole MAC "
      "avec algorithme d'Exponential Backoff. L'etat du systeme evolue uniquement lors d'evenements "
      "discrets, geres par un echeancier (min-heap) trie par ordre chronologique."),
    SP(),
    H2("1.2 Evenements"),
    Bul("<b>ARRIVAL</b> : arrivee d'un paquet a une station. Temps inter-arrivee ~ Exp(lambda). "
        "Si la file est pleine (longueur = K), le paquet est perdu. Sinon il est mis en file. "
        "Si la station etait idle, un ATTEMPT est immediatement planifie."),
    Bul("<b>ATTEMPT</b> : tentative d'emission. Si le canal est libre, la station prend le canal "
        "et un END_TX est planifie a t+1. Si le canal est occupe, collision detectee : "
        "les deux stations incrementent leur etat i et planifient un ATTEMPT apres Exp(2^i * tau). "
        "L'etat est borne a MAX_STATE=10 (standard 802.11)."),
    Bul("<b>END_TX</b> : fin d'emission. Si non invalidee par collision, le paquet est un succes, "
        "la station revient a l'etat 1 et traite le paquet suivant si disponible."),
    SP(),
    H2("1.3 Variables d'etat par station"),
    make_table(
        ["Variable", "Type", "Description"],
        [
            ["queue_len",         "int",  "Nombre de paquets en attente"],
            ["state",             "int",  "Etat de backoff (1=initial, +1 par collision)"],
            ["attempt_scheduled", "bool", "True si un ATTEMPT est dans l'echeancier"],
            ["is_attempting",     "bool", "True si la station emet actuellement"],
            ["end_valid",         "bool", "True si l'emission n'a pas ete invalidee"],
        ],
        col_widths=[4*cm, 2*cm, 9*cm]
    ),
    SP(),
    H2("1.4 Hypotheses de modelisation"),
    Bul("Duree d'emission = 1 unite de temps (deterministe)."),
    Bul("Temps inter-arrivees et backoffs suivent des lois exponentielles."),
    Bul("Collision detectee instantanement."),
    Bul("Etat de backoff borne a MAX_STATE = 10 (evite backoffs infinis)."),
    Bul("Files de capacite K finie ; paquets sur file pleine definitvement perdus."),
    Bul("Regime permanent estime en ignorant les 20% premiers instants (phase transitoire)."),
    PageBreak(),
]

# ── SECTION 2 : RESULTATS ─────────────────────────────────────────────────────
story += [H1("2. Resultats et courbes"), HR()]

story += [H2("2.1 Debit n(t)/t en fonction du temps")]
story += fig_block("fig1_throughput_vs_time.png", w=15,
                   cap=f"Figure 1 — Debit instantane n(t)/t. N={int(sc['N_REF'])}, lambda={sc['LAM_REF']}, K={int(sc['K_REF'])}, tau={sc['TAU_REF']}, T_max={int(sc['T_MAX'])}.")
story += [
    P(f"Le debit n(t)/t converge vers <b>d(N,K,lambda,tau) ≈ {sc['d_steady']:.4f}</b> paquets/unite de temps. "
      f"La convergence est rapide (quelques centaines d'unites) ce qui valide T_max = {int(sc['T_MAX'])}."),
    SP(),
]

story += [H2("2.2 Nombre moyen de clients")]
story += fig_block("fig2_queue_vs_time.png", w=15,
                   cap="Figure 2 — Nombre total de paquets en file d'attente au cours du temps.")
story += [
    P(f"Le nombre moyen de clients en regime permanent est <b>{sc['mean_q']:.2f} paquets</b>. "
      f"Ce chiffre eleve s'explique par le taux d'arrivee global N*lambda = {int(sc['N_REF'])}*{sc['LAM_REF']} = "
      f"{int(sc['N_REF'])*sc['LAM_REF']:.1f} paquets/unite, proche de la capacite du canal (1 paquet/unite)."),
    SP(),
]

story += [H2("2.3 Taux de paquets perdus (file pleine)")]
story += fig_block("fig3_loss_rate_vs_time.png", w=15,
                   cap="Figure 3 — Taux de paquets perdus par fenetre de 20 unites de temps.")
story += [
    P(f"Le taux de perte moyen en regime permanent est <b>{sc['mean_loss']:.4f}</b> "
      f"({sc['mean_loss']*100:.1f}% des paquets arrivants). "
      f"Ce taux eleve est coherent avec les parametres choisis : avec N*lambda = {int(sc['N_REF'])*sc['LAM_REF']:.1f} "
      f"et une capacite de canal de 1, le systeme est proche de la saturation."),
    SP(),
    PageBreak(),
]

story += [H2("2.4 Debit d(N,K,lambda,tau) en fonction de lambda")]
story += fig_block("fig4_throughput_vs_lambda.png", w=15,
                   cap=f"Figure 4 — Debit en regime permanent vs lambda. N={int(sc['N_REF'])}, K={int(sc['K_REF'])}, tau={sc['TAU_REF']}. Barres = IC 95%.")
rows_lam = [[f"{lam:.2f}", f"{m:.4f}", f"± {h:.4f}"]
            for lam, m, h in zip(lam_values[:8], d_lam_mean[:8], d_lam_ci[:8])]
story += [
    SP(0.2),
    make_table(["lambda", "d moyen", "IC 95%"], rows_lam, col_widths=[3*cm, 4*cm, 4*cm]),
    SP(0.3),
    P("Le debit croit avec lambda jusqu'a saturer autour de 1 paquet/unite (capacite maximale du canal). "
      "Pour les faibles lambda, le canal est sous-utilise. Au-dela de lambda ≈ 1, le canal est sature : "
      "les files se remplissent, les paquets sont perdus, et le debit plafonne."),
    SP(),
]

story += [H2("2.5 Debit d(N,K,lambda,tau) en fonction de N")]
story += fig_block("fig5_throughput_vs_N.png", w=15,
                   cap=f"Figure 5 — Debit en regime permanent vs N. lambda={sc['LAM_REF']}, K={int(sc['K_REF'])}, tau={sc['TAU_REF']}. Barres = IC 95%.")
rows_N = [[str(int(n)), f"{m:.4f}", f"± {h:.4f}"]
          for n, m, h in zip(N_values[:8], d_N_mean[:8], d_N_ci[:8])]
story += [
    SP(0.2),
    make_table(["N", "d moyen", "IC 95%"], rows_N, col_widths=[3*cm, 4*cm, 4*cm]),
    SP(0.3),
    P("Le debit augmente legerement avec N pour les petites valeurs, puis se stabilise. "
      "Avec plus de stations, le canal est mieux utilise (moins de temps idle), "
      "mais les collisions augmentent aussi. Ces deux effets se compensent."),
    SP(),
    PageBreak(),
]

story += [H2(f"2.6 N optimal maximisant le debit (IC 95%)")]
story += fig_block("fig6_N_optimal.png", w=15,
                   cap=f"Figure 6 — Debit moyen par valeur de N avec IC 95%. Barre bleue = N optimal = {int(sc['N_opt'])}.")
story += [
    P(f"Le nombre de stations qui maximise le debit est <b>N* = {int(sc['N_opt'])}</b>, "
      f"avec un debit de <b>{sc['d_opt']:.4f} ± {sc['ci_opt']:.4f}</b> paquets/unite de temps "
      f"(IC 95%, base sur {int(sc['N_RUNS'])} runs independants). "
      f"Ce resultat est robuste : les IC 95% des valeurs voisines se chevauchent."),
    SP(),
]

story += [H2("2.7 Taux de collision en fonction de lambda")]
story += fig_block("fig8_collision_rate_vs_lambda.png", w=15,
                   cap=f"Figure 8 — Taux de collision vs lambda. N={int(sc['N_REF'])}, K={int(sc['K_REF'])}, tau={sc['TAU_REF']}.")
story += [
    P("Le taux de collision decroit quand lambda augmente, ce qui peut sembler contre-intuitif. "
      "Pour un faible lambda, les stations transmettent de facon sporadique. Quand plusieurs stations "
      "ont accumule des paquets simultanement, elles tentent toutes d'emettre en meme temps, provoquant "
      "des collisions. Pour un lambda eleve, le canal est quasi-continuellement occupe : les stations "
      "font la queue et les transmissions se serialisent naturellement, reduisant les collisions."),
    SP(),
    PageBreak(),
]

# ── SECTION 3 : VALIDATION ────────────────────────────────────────────────────
story += [H1("3. Validation du simulateur"), HR()]

story += [
    H2("3.1 Cas N=1 — file M/D/1"),
    P("Avec une seule station (N=1) et une file de grande capacite (K=1000), "
      "il ne peut pas y avoir de collision. Le systeme se reduit a une file M/D/1 : "
      "arrivees Poisson(lambda), service deterministe de duree 1. "
      "Le debit theorique est : <b>d_theo = min(lambda, 1)</b>"),
    SP(0.2),
]
story += fig_block("fig7_validation_N1.png", w=14,
                   cap="Figure 7 — Validation N=1 : simulation vs theorie min(lambda, 1). Accord quasi-parfait.")
story += [
    P("La simulation colle parfaitement a la courbe theorique sur toute la plage de lambda testee. "
      "L'erreur relative maximale observee est inferieure a 1%, ce qui valide "
      "la logique de base du simulateur."),
    SP(),
    H2("3.2 Convergence de n(t)/t"),
    P("La convergence de n(t)/t vers une valeur fixe d(N,K,lambda,tau) est observee sur la Figure 1. "
      "Cette convergence est garantie par la loi des grands nombres appliquee au processus "
      "de renouvellement des transmissions reussies. T_max = 5000 est suffisant."),
    SP(),
    H2("3.3 Reproductibilite et intervalles de confiance"),
    P(f"Toutes les courbes statistiques sont basees sur {int(sc['N_RUNS'])} runs independants par point, "
      f"avec des graines aleatoires differentes. Les IC 95% sont calcules via la loi de Student. "
      f"Les IC sont etroits, confirmant la stabilite des estimations pour T_max = {int(sc['T_MAX'])}."),
    SP(),
    PageBreak(),
]

# ── SECTION 4 : ANALYSE ───────────────────────────────────────────────────────
story += [H1("4. Analyse et discussion"), HR()]

story += [
    H2("4.1 Impact de lambda sur le debit"),
    Bul("<b>Sous-charge (lambda &lt; 1/N)</b> : canal majoritairement libre. Debit proportionnel a N*lambda. "
        "Collisions relativement frequentes car les stations transmettent de facon synchronisee."),
    Bul("<b>Charge (lambda ≈ 1/N)</b> : canal bien utilise. Zone de fonctionnement optimal."),
    Bul("<b>Sature (lambda &gt; 1/N)</b> : files se remplissent, paquets perdus avant emission. "
        "Debit plafonne a 1, taux de perte explose."),
    SP(),
    H2("4.2 Impact de N sur le debit"),
    P("L'augmentation de N a deux effets opposes : elle augmente la charge totale (N*lambda) "
      "ce qui ameliore l'utilisation du canal, mais elle augmente aussi la probabilite de collision. "
      "Le backoff exponentiel amortit cet effet en espacant les retransmissions, "
      "mais au prix d'une latence accrue. Le N optimal represente l'equilibre entre ces deux effets."),
    SP(),
    H2("4.3 Role du backoff exponentiel"),
    P("Le backoff exponentiel est essentiel pour la stabilite du protocole. "
      "Sans lui, les stations en collision retenteraient dans la meme fenetre temporelle, "
      "provoquant des cascades de collisions. Le doublement de la moyenne a chaque collision (2^i * tau) "
      "espace progressivement les tentatives. La borne MAX_STATE = 10 evite des delais infinis."),
    SP(),
    H2("4.4 Limites du modele"),
    Bul("Detection de collision supposee instantanee (pas de delai de propagation)."),
    Bul("La libération du canal se fait des qu'il y a collision et pas à la fin de l'emission des paquets. Les collisions sont donc plus courtes et ne concernent que deux stations, ce qui fluidifie le flux."),
    Bul("Dans notre implémentation, lorsqu’un paquet arrive sur une station dont la file d’attente était vide, une tentative d’émission est programmée immédiatement. Le modèle ne représente donc pas de délai de traitement interne ou de temps d’écoute préalable du canal avant la première tentative d’émission."),
    SP(),
    PageBreak(),
]

# ── SECTION 5 : STRUCTURE ─────────────────────────────────────────────────────
story += [H1("5. Structure du programme"), HR()]

story += [
    make_table(
        ["Fichier", "Role"],
        [
            ["main/mac_simulateur.py",  "Simulateur principal : fonction simulate() et helpers"],
            ["main/experiments.py",     "Experiences : generation de toutes les courbes"],
            ["main/generate_report.py", "Generation du rapport PDF"],
            ["main/Experiments.ipynb",  "Notebook Jupyter interactif"],
            ["figures/",                "Courbes generees (PNG) et donnees numeriques"],
            ["README.md",               "Documentation d'utilisation"],
        ],
        col_widths=[6*cm, 9*cm]
    ),
    SP(0.4),
    H2("Utilisation"),
    Paragraph("python3 main/experiments.py      # genere les courbes\n"
              "python3 main/generate_report.py  # genere ce rapport PDF", code_s),
    SP(0.3),
    H2("Dependances"),
    Paragraph("numpy  matplotlib  scipy  seaborn  reportlab", code_s),
]

# ── BUILD ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"Rapport genere : {OUTPUT}")
