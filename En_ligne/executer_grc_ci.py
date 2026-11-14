"""Exécution réelle des quatre graphes GNU Radio (sans écran) et enregistrement des résultats.
Utilisé par le workflow GitHub Actions ; fonctionne aussi sur tout Linux où GNU Radio 3.10 est installé :
    python3 En_ligne/executer_grc_ci.py"""
import os, sys, json, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.signal import hilbert
ICI = os.path.dirname(os.path.abspath(__file__)); RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI); import colab_tools as C
G = os.path.join(RACINE, 'GNU_Radio'); OUT = os.path.join(RACINE, 'resultats_gnuradio'); os.makedirs(OUT, exist_ok=True)
R = {}
def mesures(nom, d):
    a, b = [np.asarray(v) for v in d['scope'][1]]; n = min(len(a), len(b)); a, b = a[n // 2:n], b[n // 2:n]
    r = {'ecart_efficace': float(np.sqrt(np.mean((a - b) ** 2))), 'correlation': float(np.corrcoef(a, b)[0, 1])}
    s = np.asarray(d['scope_emis'][1][0]); s = s[len(s) // 2:]; z = hilbert(s)[500:-500]
    r['enveloppe_min'], r['enveloppe_max'] = float(np.abs(z).min()), float(np.abs(z).max())
    fi = np.convolve(np.diff(np.unwrap(np.angle(z))) * 480e3 / (2 * np.pi), np.ones(15) / 15, 'valid')
    r['frequence_inst_min'], r['frequence_inst_max'] = float(fi.min()), float(fi.max())
    return r
def figure(nom, d):
    fig, ax = plt.subplots(3, 1, figsize=(10, 8))
    xs = d['scope_emis'][1]
    for k, x in enumerate(xs): ax[0].plot(np.asarray(x)[-2048:], lw=0.8, ls='-' if k == 0 else '--')
    ax[0].set_title(f'{nom} : scope_emis (signal modulé émis)')
    x = np.asarray(d['spectre_emis'][1][0]); N = 8192; w = np.hanning(N)
    P = np.mean([np.abs(np.fft.rfft(x[i:i + N] * w)) ** 2 for i in range(len(x) // 2, len(x) - N, N // 2)], 0)
    f = np.fft.rfftfreq(N, 1 / 480e3); k = f < 25e3
    ax[1].plot(f[k] / 1e3, 10 * np.log10(P[k] / P.max() + 1e-16)); ax[1].set_ylim(-100, 5); ax[1].set_title('spectre_emis (kHz)')
    for v in d['scope'][1]: ax[2].plot(np.asarray(v)[-480:], lw=0.9)
    ax[2].set_title('scope : message émis retardé et message démodulé')
    for a in ax: a.grid(ls=':')
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f'{nom}.png'), dpi=120); plt.close(fig)
for nom, val in (('am_tx_rx_sim', {}), ('ssb_tx_rx_sim', {'lo_phase': 0.0}), ('fm_tx_rx_sim', {}), ('pm_tx_rx_sim', {})):
    tb, d = C.executer(os.path.join(G, nom + '.grc'), duree=2.0, out_dir=os.path.join(OUT, 'hl'), **val)
    R[nom] = mesures(nom, d); figure(nom, d)
    for ph in (2.0, -2.5):
        tb, d2 = C.executer(os.path.join(G, nom + '.grc'), duree=1.0, out_dir=os.path.join(OUT, 'hl'), lo_phase=ph)
        R[nom][f'correlation_lo_phase_{ph}'] = mesures(nom, d2)['correlation']
    print(nom, json.dumps(R[nom], indent=1), flush=True)
json.dump(R, open(os.path.join(OUT, 'mesures.json'), 'w'), indent=1)
