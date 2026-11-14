function xa = signal_analytique(x)
%SIGNAL_ANALYTIQUE Signal analytique x + j*H{x} calculé par FFT
%   (équivalent de hilbert.m, sans Signal Processing Toolbox).
N = numel(x); X = fft(x); H = zeros(size(X));
H(1) = 1;
if mod(N,2) == 0
    H(N/2+1) = 1; H(2:N/2) = 2;
else
    H(2:(N+1)/2) = 2;
end
xa = ifft(X.*H);
end
