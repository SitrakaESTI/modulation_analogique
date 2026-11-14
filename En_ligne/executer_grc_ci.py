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
def phase(x, f, fs=48000.0):
    x = np.asarray(x, float); t = np.arange(len(x)) / fs
    A = np.column_stack([np.cos(2 * np.pi * f * t), np.sin(2 * np.pi * f * t), np.ones_like(t)])
    c = np.linalg.lstsq(A, x, rcond=None)[0]; return np.arctan2(-c[1], c[0]), np.hypot(c[0], c[1])
def retard_reel(nom, val):
    """retard (en échantillons à 48 kHz) du message démodulé par rapport au message affiché,
    mesuré sur les vrais blocs avec cinq fréquences de message pour lever l'ambiguïté de période"""
    L = {}
    for f in (1000.0, 300.0, 700.0, 1100.0, 470.0):
        tb, d = C.executer(os.path.join(G, nom + '.grc'), duree=1.5, out_dir=os.path.join(OUT, 'hl'), fm=f, **val)
        a, b = [np.asarray(v) for v in d['scope'][1]]; n = min(len(a), len(b)); a, b = a[n // 2:n], b[n // 2:n]
        pa, _ = phase(a, f); pb, amp = phase(b, f); L[f] = ((pa - pb) / (2 * np.pi * f / 48000.0), 48000.0 / f, amp)
    cand = np.arange(-4000, 4001)
    err = sum(np.abs(((cand - l) + p / 2) % p - p / 2) for l, p, _ in L.values())
    return int(cand[np.argmin(err)]), float(err.min()), {str(int(f)): round(v[2], 4) for f, v in L.items()}
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
    m = min(len(x) for x in xs)
    for k, x in enumerate(xs): ax[0].plot(np.arange(1440) / 480.0, np.asarray(x)[m - 1440:m], lw=0.9 if k == 0 else 1.2, ls='-' if k == 0 else '--')
    ax[0].set_xlabel('temps (ms)')
    ax[0].set_title(f'{nom} : scope_emis (signal modulé émis)')
    x = np.asarray(d['spectre_emis'][1][0]); N = 8192; w = np.hanning(N)
    P = np.mean([np.abs(np.fft.rfft(x[i:i + N] * w)) ** 2 for i in range(len(x) // 2, len(x) - N, N // 2)], 0)
    f = np.fft.rfftfreq(N, 1 / 480e3); k = f < 25e3
    ax[1].plot(f[k] / 1e3, 10 * np.log10(P[k] / P.max() + 1e-16)); ax[1].set_ylim(-100, 5); ax[1].set_title('spectre_emis (kHz)')
    a, b = [np.asarray(v) for v in d['scope'][1]]; n = min(len(a), len(b))   # mêmes indices : même instant
    ax[2].plot(np.arange(480) / 48.0, a[n - 480:n], lw=1.6, label='message émis retardé')
    ax[2].plot(np.arange(480) / 48.0, b[n - 480:n], lw=0.9, ls='--', label='message démodulé'); ax[2].legend(loc='upper right')
    ax[2].set_xlabel('temps (ms)')
    ax[2].set_title('scope : message émis retardé et message démodulé')
    for a in ax: a.grid(ls=':')
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f'{nom}.png'), dpi=120); plt.close(fig)
for nom, val in (('am_tx_rx_sim', {}), ('ssb_tx_rx_sim', {'lo_phase': 0.0}), ('fm_tx_rx_sim', {}), ('pm_tx_rx_sim', {})):
    tb, d = C.executer(os.path.join(G, nom + '.grc'), duree=2.0, out_dir=os.path.join(OUT, 'hl'), **val)
    R[nom] = mesures(nom, d); figure(nom, d)
    dl, e, amps = retard_reel(nom, val)
    R[nom]['decalage_supplementaire_echantillons'] = dl; R[nom]['residu_mesure_decalage'] = e; R[nom]['amplitude_demodulee'] = amps
    for ph in (2.0, -2.5):
        tb, d2 = C.executer(os.path.join(G, nom + '.grc'), duree=1.0, out_dir=os.path.join(OUT, 'hl'), lo_phase=ph)
        R[nom][f'correlation_lo_phase_{ph}'] = mesures(nom, d2)['correlation']
    print(nom, json.dumps(R[nom], indent=1), flush=True)
json.dump(R, open(os.path.join(OUT, 'mesures.json'), 'w'), indent=1)
