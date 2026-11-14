"""Outils communs aux simulations de référence (miroir exact des scripts MATLAB)."""
import numpy as np
from scipy.signal import lfilter

def fir_lowpass(fcut, fs, N):
    """Filtre RIF passe-bas, sinus cardinal fenêtré (Hamming), gain unité en continu.
    Même construction que lpf_hamming.m (sans boîte à outils)."""
    n = np.arange(N); M = (N - 1) / 2
    x = 2 * fcut / fs * (n - M)
    h = 2 * fcut / fs * np.sinc(x) * (0.54 - 0.46 * np.cos(2 * np.pi * n / (N - 1)))
    return h / h.sum()

def filt(h, x):
    return lfilter(h, 1.0, x)

def tone_snr(y, f, fs, keep):
    """Rapport signal sur bruit d'une sortie censée contenir une sinusoïde de fréquence f :
    ajustement par moindres carrés de a cos + b sin + c, puis puissance du résidu."""
    y = y[keep]; t = np.arange(len(y)) / fs
    A = np.column_stack([np.cos(2*np.pi*f*t), np.sin(2*np.pi*f*t), np.ones_like(t)])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ coef
    ps = (coef[0]**2 + coef[1]**2) / 2
    return 10*np.log10(ps / np.mean(res**2)), np.hypot(coef[0], coef[1])

def spectrum_db(x, fs):
    """Spectre d'amplitude unilatéral en dB (fenêtre rectangulaire, durée multiple des périodes)."""
    N = len(x); X = np.fft.rfft(x) / N; X[1:] *= 2
    f = np.fft.rfftfreq(N, 1/fs)
    return f, 20*np.log10(np.abs(X) + 1e-15)

def analytic(x):
    """Signal analytique par FFT (équivalent à hilbert.m, sans boîte à outils)."""
    N = len(x); X = np.fft.fft(x); H = np.zeros(N)
    H[0] = 1
    if N % 2 == 0: H[N//2] = 1; H[1:N//2] = 2
    else: H[1:(N+1)//2] = 2
    return np.fft.ifft(X * H)
