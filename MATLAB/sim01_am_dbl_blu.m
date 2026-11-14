%% SIM01_AM_DBL_BLU  Émetteur et récepteur AM, DBL et BLU en simulation pure
% Chaîne étudiée : message -> modulateur -> canal à bruit blanc additif
% gaussien -> oscillateur local complexe -> filtre passe-bas -> démodulateur.
% Contrôles : niveaux des bandes latérales, rendement de modulation,
% démodulation sans bruit, puis rapport signal sur bruit en sortie comparé à
% la théorie (AM : m^2/(2+m^2) ; DBL et BLU cohérentes : 1).
% Aucune boîte à outils n'est nécessaire.
clear; clc; addpath(fullfile(fileparts(mfilename('fullpath')), 'outils'));
rng(1); nok = 0; ntot = 0;

fs = 400e3; fc = 50e3; fm = 1e3; T = 0.05; Ac = 1;
t = (0:round(T*fs)-1)/fs;
keep = 4001:16000;                       % régime établi (transitoires exclus)
lo = exp(-1j*2*pi*fc*t);                 % oscillateur local complexe

%% 1. Spectre AM et rendement de modulation
figure('Name','AM : temps et spectre');
for j = 1:2
    m = 0.5*j;
    s = Ac*(1 + m*cos(2*pi*fm*t)).*cos(2*pi*fc*t);
    [f, S] = spectre_db(s, fs);
    [~, kc] = min(abs(f-fc)); [~, ku] = min(abs(f-(fc+fm)));
    ntot = ntot+1; nok = nok + verifier(sprintf('AM m=%.1f bande laterale/porteuse (dB)', m), S(ku)-S(kc), 20*log10(m/2), 0.05);
    sb = Ac*m*cos(2*pi*fm*t).*cos(2*pi*fc*t);
    ntot = ntot+1; nok = nok + verifier(sprintf('AM m=%.1f rendement de modulation (%%)', m), 100*mean(sb.^2)/mean(s.^2), 100*m^2/(2+m^2), 0.1);
    subplot(2,2,j); plot(t(1:1200)*1e3, s(1:1200), t(1:1200)*1e3, 1+m*cos(2*pi*fm*t(1:1200)), 'LineWidth', 1.2);
    title(sprintf('AM, m = %.1f', m)); xlabel('temps (ms)'); grid on;
    subplot(2,2,j+2); sel = f > 45e3 & f < 55e3; plot(f(sel)/1e3, S(sel)-max(S)); ylim([-60 5]);
    xlabel('fréquence (kHz)'); ylabel('dB'); grid on;
end

%% 2. Démodulation AM (enveloppe), DBL et BLU (cohérentes)
W = 3e3; hpre = lpf_hamming(W, fs, 401); Wn = fs*sum(hpre.^2)/2;   % bande équivalente de bruit
m = 0.5; phi = 0.7;                                                 % déphasage de l'émetteur
s_am  = Ac*(1 + m*cos(2*pi*fm*t)).*cos(2*pi*fc*t + phi);
s_dbl = Ac*cos(2*pi*fm*t).*cos(2*pi*fc*t + phi);
s_blu = Ac*real(signal_analytique(cos(2*pi*fm*t)).*exp(1j*(2*pi*fc*t + phi)));   % Hartley
hbp = lpf_hamming(W/2, fs, 401).*exp(1j*2*pi*(W/2)*(0:400)/fs);                  % filtre complexe 0..W
Wbp = fs*sum(abs(hbp).^2);

y = abs(filter(hpre, 1, s_am.*lo)); y = y - mean(y(keep));
ntot = ntot+1; nok = nok + (rsb_tonalite(y(keep), fm, fs) > 45); fprintf('     AM enveloppe sans bruit : RSB = %.1f dB\n', rsb_tonalite(y(keep), fm, fs));
y = real(filter(hpre, 1, s_dbl.*lo)*exp(-1j*phi));
ntot = ntot+1; nok = nok + (rsb_tonalite(y(keep), fm, fs) > 45); fprintf('     DBL coherente sans bruit : RSB = %.1f dB\n', rsb_tonalite(y(keep), fm, fs));
y = real(filter(hbp, 1, s_blu.*lo)*exp(-1j*phi));
ntot = ntot+1; nok = nok + (rsb_tonalite(y(keep), fm, fs) > 45); fprintf('     BLU coherente sans bruit : RSB = %.1f dB\n', rsb_tonalite(y(keep), fm, fs));

%% 3. Bruit : RSB en sortie en fonction du RSB canal P/(N0*W)
grille = 0:4:40; mes = zeros(3, numel(grille));
for i = 1:numel(grille)
    [r, ~] = ajout_bruit(s_am, grille(i), Wn, fs);
    y = abs(filter(hpre, 1, r.*lo)); y = y - mean(y(keep)); mes(1,i) = rsb_tonalite(y(keep), fm, fs);
    [r, ~] = ajout_bruit(s_dbl, grille(i), Wn, fs);
    y = real(filter(hpre, 1, r.*lo)*exp(-1j*phi)); mes(2,i) = rsb_tonalite(y(keep), fm, fs);
    [r, ~] = ajout_bruit(s_blu, grille(i), Wbp, fs);
    y = real(filter(hbp, 1, r.*lo)*exp(-1j*phi)); mes(3,i) = rsb_tonalite(y(keep), fm, fs);
end
theo = [grille + 10*log10(m^2/(2+m^2)); grille; grille];
noms = {'AM enveloppe', 'DBL coherente', 'BLU coherente'};
for k = 1:3
    d = mes(k, grille >= 20) - theo(k, grille >= 20);
    ntot = ntot+1; nok = nok + verifier([noms{k} ' ecart mesure/theorie (dB)'], mean(d), 0, 0.6);
end
figure('Name','RSB en sortie'); plot(grille, mes, 'o', grille, theo, '-'); grid on;
xlabel('RSB canal (dB)'); ylabel('RSB en sortie (dB)'); legend([noms, strcat(noms, ' (théorie)')], 'Location', 'northwest');
fprintf('\nBilan : %d contrôles réussis sur %d\n', nok, ntot);

function [r, N0] = ajout_bruit(s, rsb_db, Wref, fs)
% Canal à bruit blanc additif gaussien : densité N0/2 (bilatérale).
P = mean(s.^2); N0 = P/(Wref*10^(rsb_db/10));
r = s + sqrt(N0/2*fs)*randn(size(s));
end
