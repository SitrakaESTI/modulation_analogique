%% SIM04_INTERPOLATION  Bloc « Repeat » contre rééchantillonneur rationnel
% Suréchantillonner un message audio de 48 kHz à 480 kHz par simple
% répétition (maintien d'ordre zéro) laisse des images spectrales autour de
% 48, 96, 144... kHz : après modulation, le signal se « répète » dans toute
% la bande. Le rééchantillonneur rationnel insère des zéros puis applique un
% filtre d'interpolation qui supprime ces images.
clear; clc; addpath(fullfile(fileparts(mfilename('fullpath')), 'outils'));
nok = 0; ntot = 0;
fa = 48e3; L = 10; fsi = fa*L; ta = (0:round(0.1*fa)-1)/fa; x = cos(2*pi*1e3*ta);
x_rep = repelem(x, L);                                     % équivalent du bloc Repeat
xz = zeros(1, numel(x)*L); xz(1:L:end) = x;
x_rs = filter(L*lpf_hamming(20e3, fsi, 241), 1, xz);       % rééchantillonneur rationnel L/1
x_rs = x_rs(2401:end-2400);
[f1, S1] = spectre_db(x_rep, fsi); [f2, S2] = spectre_db(x_rs, fsi);
[~, a] = min(abs(f1-47e3)); [~, b] = min(abs(f1-1e3)); img_rep = S1(a) - S1(b);
[~, a] = min(abs(f2-47e3)); [~, b] = min(abs(f2-1e3)); img_rs = S2(a) - S2(b);
sincx = @(u) sin(pi*u)./(pi*u);
ntot = ntot+1; nok = nok + verifier('Repeat : image a 47 kHz (dB)', img_rep, 20*log10(abs(sincx(47/48)/sincx(1/48))), 0.3);
ntot = ntot+1; nok = nok + (img_rs < -60); fprintf('     Reechantillonneur : image a 47 kHz = %.1f dB (< -60 dB attendu)\n', img_rs);
figure('Name','Images d''interpolation'); plot(f1/1e3, S1-max(S1), f2/1e3, S2-max(S2)); xlim([0 240]); ylim([-120 5]); grid on;
xlabel('fréquence (kHz)'); ylabel('dB'); legend('Repeat', 'Rééchantillonneur rationnel');
fprintf('\nBilan : %d contrôles réussis sur %d\n', nok, ntot);
