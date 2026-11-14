%% SIM02_FM_PM  Émetteur et récepteur FM et PM en simulation pure
% FM : phase = 2*pi*df*intégrale du message ; PM : phase = bp*message.
% Récepteur : oscillateur local complexe, filtre de prédétection, puis
% discriminateur (FM : angle de z[n]*conj(z[n-1])) ou mesure de phase (PM).
% Contrôles : raies de Bessel, puissance dans la bande de Carson, amplitude
% restituée, RSB en sortie comparé à la théorie au-dessus du seuil.
clear; clc; addpath(fullfile(fileparts(mfilename('fullpath')), 'outils'));
rng(1); nok = 0; ntot = 0;

fs = 400e3; fc = 50e3; fm = 1e3; T = 0.05; Ac = 1; phi = 0.7;
t = (0:round(T*fs)-1)/fs; keep = 4001:16000; lo = exp(-1j*2*pi*fc*t);
df = 5e3; beta = df/fm; bp = 1.5;

%% 1. Spectre FM : fonctions de Bessel et règle de Carson
s_fm = Ac*cos(2*pi*fc*t + 2*pi*df*cumsum(cos(2*pi*fm*t))/fs + phi);
[f, S] = spectre_db(s_fm, fs);
P = abs(fft(s_fm)/numel(s_fm)).^2; P = P(1:numel(f)); P(2:end) = 2*P(2:end);
dans = sum(P(f >= fc-6e3 & f <= fc+6e3))/sum(P);
ntot = ntot+1; nok = nok + verifier('FM puissance dans la bande de Carson (%)', 100*dans, 100*sum(besselj(-6:6, beta).^2), 0.5);
[~, kc] = min(abs(f-fc)); [~, k1] = min(abs(f-fc-fm));
ntot = ntot+1; nok = nok + verifier('FM raie porteuse (dB)', S(kc), 20*log10(abs(besselj(0, beta))), 0.3);
ntot = ntot+1; nok = nok + verifier('FM raie fc+fm (dB)', S(k1), 20*log10(abs(besselj(1, beta))), 0.3);
figure('Name','Spectre FM'); sel = f > 38e3 & f < 62e3; plot(f(sel)/1e3, S(sel)); hold on;
n = -11:11; plot((fc+n*fm)/1e3, 20*log10(abs(besselj(n, beta))+1e-12), 'o'); ylim([-80 0]); grid on;
xlabel('fréquence (kHz)'); ylabel('dB'); legend('simulation', '|J_n(5)|');

%% 2. Démodulation sans bruit
hpre = lpf_hamming(8e3, fs, 201); hpost = lpf_hamming(2e3, fs, 801);
y = fm_demod(s_fm, lo, hpre, hpost, fs);
[~, a] = rsb_tonalite(y(keep), fm, fs);
ntot = ntot+1; nok = nok + verifier('FM amplitude restituee (Hz)', a, df, 50);
s_pm = Ac*cos(2*pi*fc*t + bp*cos(2*pi*fm*t) + phi);
y = pm_demod(s_pm, lo, hpre, hpost, keep);
[~, a] = rsb_tonalite(y(keep), fm, fs);
ntot = ntot+1; nok = nok + verifier('PM amplitude restituee (rad)', a, bp, 0.02);

%% 3. Bruit : comparaison avec la théorie
hp = lpf_hamming(3e3, fs, 401); Wn = fs*sum(hp.^2)/2;      % même référence de bande que l'AM
Hf = fft(hpost, 2^18); Hf = Hf(1:2^17+1); ff = (0:2^17)*fs/2^18;
I2 = 2*trapz(ff, ff.^2.*abs(Hf).^2); I0 = 2*trapz(ff, abs(Hf).^2);
Bpre = fs*sum(hpre.^2);
grille = 0:4:40; mfm = zeros(size(grille)); tfm = mfm; mpm = mfm; tpm = mfm; cnr = mfm;
for i = 1:numel(grille)
    N0 = mean(s_fm.^2)/(Wn*10^(grille(i)/10));
    r = s_fm + sqrt(N0/2*fs)*randn(size(s_fm));
    y = fm_demod(r, lo, hpre, hpost, fs); mfm(i) = rsb_tonalite(y(keep), fm, fs);
    tfm(i) = 10*log10((df^2/2)/(N0/Ac^2*I2));
    r = s_pm + sqrt(N0/2*fs)*randn(size(s_pm));
    y = pm_demod(r, lo, hpre, hpost, keep); mpm(i) = rsb_tonalite(y(keep), fm, fs);
    tpm(i) = 10*log10((bp^2/2)/(N0/Ac^2*I0));
    cnr(i) = 10*log10((Ac^2/2)/(N0*Bpre));
end
sel = cnr > 13;                                            % au-dessus du seuil FM
ntot = ntot+1; nok = nok + verifier('FM ecart mesure/theorie (dB)', mean(mfm(sel)-tfm(sel)), 0, 0.8);
ntot = ntot+1; nok = nok + verifier('PM ecart mesure/theorie (dB)', mean(mpm(sel)-tpm(sel)), 0, 0.8);
fprintf('     Gain FM par rapport au RSB canal : %.1f dB\n', mean(tfm - grille));
figure('Name','RSB FM et PM'); plot(grille, mfm, 'o', grille, tfm, '-', grille, mpm, 's', grille, tpm, '-'); grid on;
xlabel('RSB canal (dB)'); ylabel('RSB en sortie (dB)'); legend('FM mesure', 'FM théorie', 'PM mesure', 'PM théorie', 'Location', 'northwest');
fprintf('\nBilan : %d contrôles réussis sur %d\n', nok, ntot);

function y = fm_demod(r, lo, hpre, hpost, fs)
z = filter(hpre, 1, r.*lo);
d = angle(z(2:end).*conj(z(1:end-1)))*fs/(2*pi);          % fréquence instantanée (Hz)
y = filter(hpost, 1, [0 d]);
end
function y = pm_demod(r, lo, hpre, hpost, keep)
z = filter(hpre, 1, r.*lo);
y = filter(hpost, 1, unwrap(angle(z)));                    % phase instantanée (rad)
y = y - mean(y(keep));
end
