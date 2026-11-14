"""Implémentation de référence (NumPy/SciPy) des simulations, utilisée pour établir et vérifier
tous les résultats chiffrés du guide. Exécution : python3 run_all.py, puis python3 figures.py."""
import numpy as np, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
from scipy.special import jv
from common import *
rng = np.random.default_rng(1)
R = {}
fs, fc, fm, T = 400e3, 50e3, 1e3, 0.05
t = np.arange(int(T*fs)) / fs
keep = slice(4000, 16000)            # régime établi (transitoires des filtres exclus)
Ac = 1.0
lo = np.exp(-2j*np.pi*fc*t)          # oscillateur local complexe

def chk(name, val, ref, tol):
    ok = abs(val-ref) <= tol
    print(f"{'OK ' if ok else 'ECHEC'} {name}: {val:.3f} (attendu {ref:.3f} ± {tol})")
    R[name] = dict(val=float(val), ref=float(ref), ok=bool(ok)); return ok

# ---------------- 1. AM : spectre
for m in (0.5, 1.0):
    s = Ac*(1+m*np.cos(2*np.pi*fm*t))*np.cos(2*np.pi*fc*t)
    f, S = spectrum_db(s, fs)
    k = lambda fr: np.argmin(abs(f-fr))
    chk(f"AM m={m} bande laterale / porteuse (dB)", S[k(fc+fm)]-S[k(fc)], 20*np.log10(m/2), 0.05)
    chk(f"AM m={m} rendement de modulation (%)", 100*np.mean((Ac*m*np.cos(2*np.pi*fm*t)*np.cos(2*np.pi*fc*t))**2)/np.mean(s**2), 100*m**2/(2+m**2), 0.1)

# ---------------- 2. AM / DBL / BLU : démodulation et bruit
W = 3e3; hpre = fir_lowpass(W, fs, 401); Wn = fs*np.sum(hpre**2)/2     # bande équivalente de bruit
def add_noise(s, snrc_db, Wref):
    P = np.mean(s**2); N0 = P/(Wref*10**(snrc_db/10))
    return s + np.sqrt(N0/2*fs)*rng.standard_normal(len(s)), N0
m = 0.5; phi = 0.7                                                      # déphasage inconnu de l'émetteur
s_am  = Ac*(1+m*np.cos(2*np.pi*fm*t))*np.cos(2*np.pi*fc*t+phi)
s_dsb = Ac*np.cos(2*np.pi*fm*t)*np.cos(2*np.pi*fc*t+phi)
xa = analytic(np.cos(2*np.pi*fm*t))
s_usb = Ac*np.real(xa*np.exp(1j*(2*np.pi*fc*t+phi)))                    # BLU supérieure (Hartley)
hbp = fir_lowpass(W/2, fs, 401)*np.exp(2j*np.pi*(W/2)*np.arange(401)/fs)  # filtre complexe 0..W
Wbp = fs*np.sum(np.abs(hbp)**2)
# sans bruit
y_env = np.abs(filt(hpre, s_am*lo)); y_env -= y_env[keep].mean()
y_coh = np.real(filt(hpre, s_dsb*lo)*np.exp(-1j*phi))
y_ssb = np.real(filt(hbp, s_usb*lo)*np.exp(-1j*phi))
for nm, y in (("AM enveloppe", y_env), ("DBL coherente", y_coh), ("BLU coherente", y_ssb)):
    snr, amp = tone_snr(y, fm, fs, keep); chk(f"{nm} sans bruit RSB sortie (dB)>", min(snr, 60), 60, 15)
# avec bruit : courbes RSB_sortie(RSB_canal)
curves = {}
grid = np.arange(0, 41, 4)
for nm in ("AM", "DBL", "BLU"):
    meas = []
    for snrc in grid:
        if nm == "AM":
            r, _ = add_noise(s_am, snrc, Wn); y = np.abs(filt(hpre, r*lo)); y -= y[keep].mean()
        elif nm == "DBL":
            r, _ = add_noise(s_dsb, snrc, Wn); y = np.real(filt(hpre, r*lo)*np.exp(-1j*phi))
        else:
            r, _ = add_noise(s_usb, snrc, Wbp); y = np.real(filt(hbp, r*lo)*np.exp(-1j*phi))
        meas.append(tone_snr(y, fm, fs, keep)[0])
    curves[nm] = meas
th = {"AM": grid+10*np.log10(m**2/(2+m**2)), "DBL": grid, "BLU": grid}
for nm in curves:
    d = np.array(curves[nm])[grid >= 20] - th[nm][grid >= 20]
    chk(f"{nm} ecart moyen mesure/theorie au-dessus du seuil (dB)", d.mean(), 0, 0.6)

# ---------------- 3. FM
df, beta = 5e3, 5.0
s_fm = Ac*np.cos(2*np.pi*fc*t + 2*np.pi*df*np.cumsum(np.cos(2*np.pi*fm*t))/fs + phi)
f, S = spectrum_db(s_fm, fs)
P = np.abs(np.fft.rfft(s_fm)/len(s_fm))**2*2; Pt = P.sum()
inband = P[(f >= fc-6e3) & (f <= fc+6e3)].sum()/Pt
chk("FM puissance dans la bande de Carson (%)", 100*inband, 100*sum(jv(n, beta)**2 for n in range(-6, 7)), 0.5)
k = lambda fr: np.argmin(abs(f-fr))
chk("FM raie porteuse (dB, rel. Ac)", S[k(fc)], 20*np.log10(abs(jv(0, beta))), 0.3)
chk("FM raie fc+fm (dB, rel. Ac)", S[k(fc+fm)], 20*np.log10(abs(jv(1, beta))), 0.3)
hpre_fm = fir_lowpass(8e3, fs, 201); Wpost = 2e3; hpost = fir_lowpass(Wpost, fs, 801)
def fm_demod(r):
    z = filt(hpre_fm, r*lo)
    d = np.angle(z[1:]*np.conj(z[:-1]))*fs/(2*np.pi)
    return filt(hpost, np.concatenate([[0], d]))
y = fm_demod(s_fm); snr, amp = tone_snr(y, fm, fs, keep)
chk("FM demod sans bruit : amplitude restituee (Hz)", amp, df, 50)
# théorie bruit FM : densité N0 f^2/Ac^2 filtrée par Hpost
Hf = np.fft.rfft(hpost, 2**18); ff = np.fft.rfftfreq(2**18, 1/fs)
I2 = 2*np.trapezoid(ff**2*np.abs(Hf)**2, ff); I0 = 2*np.trapezoid(np.abs(Hf)**2, ff)
fm_meas, fm_th, pm_meas, pm_th, cnr = [], [], [], [], []
Bpre = fs*np.sum(hpre_fm**2)
for snrc in grid:
    r, N0 = add_noise(s_fm, snrc, Wn)       # même référence de bande que l'AM pour comparer
    y = fm_demod(r); fm_meas.append(tone_snr(y, fm, fs, keep)[0])
    fm_th.append(10*np.log10((df**2/2)/(N0/Ac**2*I2)))
    cnr.append(10*np.log10((Ac**2/2)/(N0*Bpre)))
fm_meas, fm_th = np.array(fm_meas), np.array(fm_th)
sel = np.array(cnr) > 13
chk("FM ecart mesure/theorie au-dessus du seuil (dB)", (fm_meas-fm_th)[sel].mean(), 0, 0.8)
W3 = 1.5*I2                                               # bande « cubique » équivalente du filtre de sortie
chk("FM gain theorique 3 df^2 Wn / (2 W^3) (dB)", (fm_th-grid).mean(), 10*np.log10(3*df**2*Wn/(2*W3)), 0.01)
print(f"     FM : gain par rapport au RSB canal = {(fm_th-grid).mean():.1f} dB ; seuil vers RSB canal ~ {grid[np.argmax(sel)]} dB")

# ---------------- 4. PM
bp = 1.5
s_pm = Ac*np.cos(2*np.pi*fc*t + bp*np.cos(2*np.pi*fm*t) + phi)
def pm_demod(r):
    z = filt(hpre_fm, r*lo)
    th_ = np.unwrap(np.angle(z)); th_ = filt(hpost, th_)
    return th_ - th_[keep].mean()
y = pm_demod(s_pm); snr, amp = tone_snr(y, fm, fs, keep)
chk("PM demod sans bruit : amplitude restituee (rad)", amp, bp, 0.02)
for snrc in grid:
    r, N0 = add_noise(s_pm, snrc, Wn)
    pm_meas.append(tone_snr(pm_demod(r), fm, fs, keep)[0])
    pm_th.append(10*np.log10((bp**2/2)/(N0/Ac**2*I0)))
pm_meas, pm_th = np.array(pm_meas), np.array(pm_th)
chk("PM ecart mesure/theorie au-dessus du seuil (dB)", (pm_meas-pm_th)[sel].mean(), 0, 0.8)
# équivalence PM / FM : PM d'un message = FM de sa dérivée
dphi_pm = np.diff(bp*np.cos(2*np.pi*fm*t))*fs/(2*np.pi)
chk("PM : excursion de frequence equivalente (Hz)", np.max(np.abs(dphi_pm)), bp*fm, 5)

# ---------------- 5. Interpolation : bloc Repeat contre rééchantillonneur rationnel
fa, L = 48e3, 10; fsi = fa*L; ta = np.arange(int(0.1*fa))/fa
xa_ = np.cos(2*np.pi*1e3*ta)
x_rep = np.repeat(xa_, L)
hint = fir_lowpass(20e3, fsi, 241)*L
xz = np.zeros(len(xa_)*L); xz[::L] = xa_
x_rs = filt(hint, xz)
fi, Srep = spectrum_db(x_rep, fsi); _, Srs = spectrum_db(x_rs[2400:2400+len(x_rep)-4800], fsi)
fi2 = np.fft.rfftfreq(len(x_rep)-4800, 1/fsi)
img_rep = Srep[np.argmin(abs(fi-47e3))] - Srep[np.argmin(abs(fi-1e3))]
img_rs  = Srs[np.argmin(abs(fi2-47e3))] - Srs[np.argmin(abs(fi2-1e3))]
chk("Repeat : image a 47 kHz (dB) = 20log|sinc(47/48)/sinc(1/48)|", img_rep, 20*np.log10(abs(np.sinc(47/48)/np.sinc(1/48))), 0.3)
print(("OK " if img_rs < -60 else "ECHEC"), f"Reechantillonneur : image a 47 kHz = {img_rs:.1f} dB (< -60 dB attendu)")
R["interp"] = dict(rep=float(img_rep), rs=float(img_rs))

R["curves"] = dict(grid=grid.tolist(), AM=curves["AM"], DBL=curves["DBL"], BLU=curves["BLU"],
                   AM_th=th["AM"].tolist(), FM=fm_meas.tolist(), FM_th=fm_th.tolist(), PM=pm_meas.tolist(), PM_th=pm_th.tolist(), cnr=cnr)
json.dump(R, open(os.path.join(HERE, 'results.json'), 'w'), indent=1, default=float)
