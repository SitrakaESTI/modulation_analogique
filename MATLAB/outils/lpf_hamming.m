function h = lpf_hamming(fcut, fs, N)
%LPF_HAMMING Filtre RIF passe-bas à N coefficients (N impair), sinus cardinal
%   fenêtré par Hamming, gain unité en continu. Aucune boîte à outils requise.
%   fcut : fréquence de coupure (Hz) ; fs : fréquence d'échantillonnage (Hz).
n = 0:N-1; M = (N-1)/2;
x = 2*fcut/fs*(n-M);
s = ones(size(x)); k = (x ~= 0); s(k) = sin(pi*x(k))./(pi*x(k));
h = 2*fcut/fs * s .* (0.54 - 0.46*cos(2*pi*n/(N-1)));
h = h/sum(h);
end
