function [f, S] = spectre_db(x, fs)
%SPECTRE_DB Spectre d'amplitude unilatéral en dB (fenêtre rectangulaire).
%   La durée du signal doit contenir un nombre entier de périodes des
%   composantes étudiées pour que chaque raie tombe exactement sur une case.
N = numel(x); X = fft(x(:)).'/N;
X = X(1:floor(N/2)+1); X(2:end) = 2*X(2:end);
f = (0:floor(N/2))*fs/N;
S = 20*log10(abs(X) + 1e-15);
end
