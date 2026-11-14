import numpy as np, json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.special import jv
from common import *
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#dddddd', 'grid.linewidth': 0.6, 'lines.linewidth': 1.4})
C = ['#2563a8', '#d9772b', '#2f9466', '#8a55c4', '#c2413b']
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'figures') + os.sep
os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(HERE, 'results.json')))
fs, fc, fm = 400e3, 50e3, 1e3; t = np.arange(20000)/fs

# 1. AM temps + spectre
fig, ax = plt.subplots(2, 2, figsize=(7.2, 4.6))
for j, m in enumerate((0.5, 1.0)):
    s = (1+m*np.cos(2*np.pi*fm*t))*np.cos(2*np.pi*fc*t)
    n = slice(0, 1200)
    ax[0, j].plot(t[n]*1e3, s[n], color=C[0], lw=0.7); ax[0, j].plot(t[n]*1e3, 1+m*np.cos(2*np.pi*fm*t[n]), color=C[1], lw=1.4)
    ax[0, j].set_title(f"Signal AM, m = {m}"); ax[0, j].set_xlabel("temps (ms)")
    f, S = spectrum_db(s, fs); S -= S.max()
    sel = (f > 45e3) & (f < 55e3)
    ax[1, j].plot(f[sel]/1e3, S[sel], color=C[0]); ax[1, j].set_ylim(-60, 5)
    ax[1, j].set_xlabel("fréquence (kHz)"); ax[1, j].set_ylabel("dB (réf. porteuse)")
    ax[1, j].annotate(f"{20*np.log10(m/2):.1f} dB", (51, 20*np.log10(m/2)), xytext=(52.2, 20*np.log10(m/2)+3), fontsize=8)
fig.tight_layout(); fig.savefig(OUT+'am_temps_spectre.png', dpi=200); plt.close()

# 2. Repeat vs rééchantillonneur
fa, L = 48e3, 10; fsi = fa*L; ta = np.arange(int(0.1*fa))/fa; xa = np.cos(2*np.pi*1e3*ta)
x_rep = np.repeat(xa, L); xz = np.zeros(len(xa)*L); xz[::L] = xa; x_rs = filt(fir_lowpass(20e3, fsi, 241)*L, xz)
fig, ax = plt.subplots(figsize=(7.2, 2.8))
for x, lab, c in ((x_rep, "Bloc Repeat (maintien d'ordre zéro)", C[4]), (x_rs[2400:-2400], "Rééchantillonneur rationnel (filtre d'interpolation)", C[0])):
    f, S = spectrum_db(x, fsi); S -= S.max(); ax.plot(f/1e3, S, color=c, label=lab, lw=1.0)
ax.set_xlim(0, 240); ax.set_ylim(-120, 5); ax.set_xlabel("fréquence (kHz)"); ax.set_ylabel("dB")
ax.legend(loc='upper right', frameon=False, fontsize=8)
ax.set_title("Tonalité de 1 kHz suréchantillonnée de 48 kHz à 480 kHz")
fig.tight_layout(); fig.savefig(OUT+'interpolation_images.png', dpi=200); plt.close()

# 3. DBL et BLU
xa_ = analytic(np.cos(2*np.pi*fm*t))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
for a, (s, ti) in zip(ax, ((np.cos(2*np.pi*fm*t)*np.cos(2*np.pi*fc*t), "DBL à porteuse supprimée"),
                          (np.real(xa_*np.exp(2j*np.pi*fc*t)), "BLU supérieure (méthode de Hartley)"))):
    f, S = spectrum_db(s, fs); S -= S.max(); sel = (f > 45e3) & (f < 55e3)
    a.plot(f[sel]/1e3, S[sel], color=C[2]); a.set_title(ti); a.set_xlabel("fréquence (kHz)"); a.set_ylim(-120, 5)
ax[0].set_ylabel("dB")
fig.tight_layout(); fig.savefig(OUT+'dbl_blu_spectres.png', dpi=200); plt.close()

# 4. FM spectre et Bessel
beta, df = 5.0, 5e3
s = np.cos(2*np.pi*fc*t + 2*np.pi*df*np.cumsum(np.cos(2*np.pi*fm*t))/fs)
f, S = spectrum_db(s, fs); sel = (f > 38e3) & (f < 62e3)
fig, ax = plt.subplots(figsize=(7.2, 3.2))
ax.plot(f[sel]/1e3, S[sel], color=C[0], label="spectre simulé")
n = np.arange(-11, 12); ax.plot((fc+n*fm)/1e3, 20*np.log10(np.abs(jv(n, beta))+1e-12), 'o', ms=3.5, color=C[1], label="théorie : |Jn(5)|")
ax.axvspan((fc-6e3)/1e3, (fc+6e3)/1e3, color=C[2], alpha=0.08, label="bande de Carson (12 kHz)")
ax.set_ylim(-80, 0); ax.set_xlabel("fréquence (kHz)"); ax.set_ylabel("dB (réf. Ac)"); ax.legend(frameon=False, fontsize=8, loc='upper center', bbox_to_anchor=(0.5,-0.22), ncol=3)
ax.set_title("Signal FM, Δf = 5 kHz, fm = 1 kHz (β = 5)")
fig.tight_layout(); fig.savefig(OUT+'fm_spectre_bessel.png', dpi=200); plt.close()

# 5. Courbes RSB
cv = R['curves']; g = np.array(cv['grid'])
fig, ax = plt.subplots(figsize=(7.2, 3.6))
for k, c, lab in (("DBL", C[2], "DBL cohérente"), ("BLU", C[3], "BLU cohérente"), ("AM", C[1], "AM, détection d'enveloppe (m = 0,5)"), ("FM", C[0], "FM, β = 5"), ("PM", C[4], "PM, βp = 1,5 rad")):
    ax.plot(g, cv[k], 'o', ms=4, color=c, label=lab + " (mesure)")
ax.plot(g, g, '-', color=C[2], lw=1); ax.plot(g, cv['AM_th'], '-', color=C[1], lw=1)
ax.plot(g, cv['FM_th'], '-', color=C[0], lw=1); ax.plot(g, cv['PM_th'], '-', color=C[4], lw=1)
ax.set_xlabel("RSB canal (dB), puissance reçue / (N0·W)"); ax.set_ylabel("RSB en sortie (dB)")
ax.set_title("Traits : théorie au-dessus du seuil ; points : simulation")
ax.legend(frameon=False, fontsize=7.5, loc='upper left'); ax.set_ylim(-15, 60)
fig.tight_layout(); fig.savefig(OUT+'rsb_sortie_canal.png', dpi=200); plt.close()


print('figures ok')
